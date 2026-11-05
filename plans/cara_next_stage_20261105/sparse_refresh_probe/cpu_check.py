"""Actual pinned WC/RF/UniPC on tiny CPU tensors plus 28-block P_k controls."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from types import MethodType,SimpleNamespace

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
import torch
from prepare import build
from postprocess import summarize
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cara_f19_speed190_sampling_r1 import light_source
from wcomr.cara_sparse_refresh_probe_r1 import SparseOwner,LayerReuse
from wcomr.cfg_paired_probe_forward import _function,WC_PATH,WC_SHA
from wcomr.policy_interval_readout_r1 import guided
from test_cara_read_write_provenance_r1 import bound,RUNTIME
from test_cara_read_write_transition_r1 import modules


def check_path(card,role,flow):
    step,_=bound(flow);model=step.worldcache.model;wc,rf=modules()
    model.net.forward=MethodType(wc.worldcache_mini_train_dit_forward,model.net)
    model.denoise=MethodType(rf.denoise,model);model.tensor_kwargs['dtype']=torch.float32
    for c in step.conditions:
        for key in ('gt_frames','cross','condition_video_input_mask_B_C_T_H_W'):
            setattr(c,key,getattr(c,key).float())
    owner=SparseOwner(model,policy=role['policy'],profile=profile_from(card['profile']),context=('sparse_CPU',str(flow)),
        runtime=RUNTIME,wc=wc,rf=rf,light_C=True,partial_updates=tuple(role['partial_updates']),sync_residual=role['sync_residual'])
    latent=step.noise.float();noise=latent.clone();scheduler=copy.deepcopy(step.solver._template);writes=[];next_C=[]
    with torch.no_grad():
        for t,timestep in enumerate(step.timesteps,1):
            delta=owner.readout.delta;dr=owner.readout.residual_delta;source=owner.readout.delta_step
            old_cache=list(model.net.residual_cache);old_birth=list(owner.readout.cache_birth_steps)
            old_u=old_cache[1]
            pair=owner.pair(noise,latent,timestep.reshape(1,1),step.conditions,owner.choose)
            assert pair[0].shape==pair[1].shape==noise.shape
            if t in role['partial_updates']:
                assert owner.readout.delta is delta and owner.readout.residual_delta is dr and owner.readout.delta_step==source
                assert torch.allclose(pair[0]-pair[1],delta,atol=1e-6,rtol=1e-5)
                assert owner.executor.last['action']=='DC'
                if role['sync_residual']:
                    assert torch.equal(model.net.residual_cache[1],model.net.residual_cache[0]-dr)
                    assert owner.readout.cache_birth_steps==[t,t]
                else:
                    assert model.net.residual_cache[1] is old_u
                    assert owner.readout.cache_birth_steps==[t,source]
                writes.append(dict(step=t,true_DD_source=source,birth_steps=list(owner.readout.cache_birth_steps)))
            elif t-1 in role['partial_updates'] and role['mask'][t-1]=='C':
                assert all(a is b for a,b in zip(model.net.residual_cache,old_cache))
                assert owner.readout.cache_birth_steps==old_birth
                next_C.append(dict(step=t,read_birth_steps=old_birth,residual_cache_unchanged=True))
            assert torch.isfinite(guided(pair)).all()
            latent=scheduler.step(guided(pair),timestep,latent,return_dict=False)[0]
    assert ''.join(r['actual'] for r in owner.history)==role['mask']
    assert not any(r['fallback_reason'] for r in owner.history)
    proof={k:v for k,v in owner.proof.items() if k.endswith(('sha256','AST_equal'))}
    owner.close()
    return dict(flow=flow,full36=True,shapes_finite=True,writes=writes,next_C=next_C,compiled_proof=proof)


def check_layers(k):
    class Block(torch.nn.Module):
        def __init__(self,index):super().__init__();self.gain=.001*(index+1);self.calls=0
        def forward(self,x):self.calls+=1;return x+self.gain*x.tanh()
    net=SimpleNamespace(blocks=torch.nn.ModuleList([Block(i) for i in range(28)]),cnt=0)
    layers=LayerReuse(net);x=torch.linspace(-1,1,24).reshape(1,2,3,4)
    layers.begin(26,'D')
    for branch in (0,1):
        net.cnt=branch;out=x+branch
        for block in net.blocks:out=block(out)
    anchors=[[r.clone() for r in branch] for branch in layers.residuals]
    before=[b.calls for b in net.blocks];layers.begin(29,'P',k=k)
    for branch in (0,1):
        net.cnt=branch;out=x+branch+.02;expected=out.clone()
        for i,block in enumerate(net.blocks):
            out=block(out)
            expected=expected+block.gain*expected.tanh() if i<k else expected+anchors[branch][i]
        assert out.shape==x.shape and torch.equal(out,expected)
    assert [b.calls-n for b,n in zip(net.blocks,before)]==[2 if i<k else 0 for i in range(28)]
    assert layers.birth_steps==[[26]*28,[26]*28]
    assert all(torch.equal(a,b) for aa,bb in zip(anchors,layers.residuals) for a,b in zip(aa,bb))
    layers.close()
    return dict(k=k,blocks=28,both_branches=True,shapes_equal=True,expected_values_equal=True,anchors_stay_at_D26=True)


if __name__=='__main__':
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('CPU check forbids CUDA')
    torch.cuda._lazy_init=forbidden
    card=build();checks=[]
    original=_function(RUNTIME,WC_PATH,WC_SHA,'worldcache_mini_train_dit_forward')
    transformed,proof=light_source(original)
    assignment='self.residual_cache[current_idx] = residual_x'
    writes=lambda node:[ast.dump(n,include_attributes=False) for n in ast.walk(node) if isinstance(n,ast.Assign) and ast.unparse(n)==assignment]
    assert len(writes(original))==1 and writes(original)==writes(transformed)
    for name,role in card['roles'].items():
        for flow in (False,True):checks.append(dict(role=name,**check_path(card,role,flow)))
    pk=[check_layers(k) for k in (14,20)]
    references={r['slot']['member']:r for r in card['reused_R18C']}
    def rows_for(deltas):
        return [dict(slot=s,Alex=references[s['member']]['Alex']+deltas[s['role']],
            T_DD=references[s['member']]['T_DD']+(1 if s['role']!='c' else 0),
            mask_matches=True,fidelity=dict(frames=93)) for s in card['matrix']]
    good=summarize(card,rows_for(dict(b=-.005,b0=.01,c=-.001)),dict(gate_passed=True))
    bad=summarize(card,rows_for(dict(b=.01,b0=.02,c=.01)),dict(gate_passed=True))
    assert good['go'] and good['b_go'] and good['c_go'] and not good['close_CFG_branch_P']
    assert not bad['go'] and bad['close_CFG_branch_P']
    assert not summarize(card,rows_for(dict(b=-.005,b0=.01,c=-.001)),dict(gate_passed=False))['go']
    value=dict(passed=True,pinned_WC_sha256=hashlib.sha256((RUNTIME/WC_PATH).read_bytes()).hexdigest(),
        full_path_residual_write_preserved=True,light_AST_proof=proof,complete36_paths=checks,Pk=pk,
        analysis_fixture=True,CUDA_initialized=torch.cuda.is_initialized(),model_weights_loaded=False,
        GPU_submissions=0,ledger_transactions=0,scope='Tiny local CPU controls, not real-GPU timing or Linux production acceptance')
    (HERE/'cpu_check.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(passed=True,complete36_paths=len(checks),Pk_variants=len(pk),CUDA_initialized=False)))
