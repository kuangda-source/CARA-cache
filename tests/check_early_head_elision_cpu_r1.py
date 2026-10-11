"""E5 full36 paired CPU controls; pinned native head/MLP, Toy attention/update.

Run OFF/W1/ beta1, both Flow modes, legacy/new versions. Actual return tensors,
all physical fields, D/P state, RNG, head calls, and own-version full snapshots
are tested. These are implementation controls, not real videos or GPU speed.
"""
import argparse
import ast
import copy
from enum import Enum
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace, MethodType


def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    assert not args.output.exists();args.output.mkdir(parents=True)
    import torch
    from einops import rearrange
    from wcomr.early_head_elision_cpu_r1 import (native_final_layer,compile_early_head_collection,
        EarlyHeadPartialDeployment,PureNativeHeadGuard,VERSION)
    from wcomr.cfg_paired_probe_forward import WC_PATH,WC_SHA,RF_PATH,RF_SHA
    from wcomr.cfg_guided_w1_forward import compile_collection
    from wcomr.partial_mlp_guided_readout import GuidedPartialDeployment
    from wcomr.partial_mlp_deployment import PartialDeploymentPair
    from wcomr.partial_mlp_guided_sampling import GuidedSamplingOwner
    from wcomr.partial_mlp_deployment_sampling import P_STEPS,LAYERS
    from wcomr.cfg_paired_probe_native_policy import NativePolicyPairedExecutor
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.cpu_owned_state_snapshot import CPUDeploymentRoundtrip
    from wcomr.partial_mlp_deployment_state import plain
    from wcomr.mid_coverage import tree_digest,WC_FIELDS
    from check_partial_mlp_guided_sampling_cpu_r1 import pinned_blocks
    torch.set_num_threads(2)
    def forbidden(*a,**k):raise RuntimeError('E5 CPU forbids CUDA/download')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    class DataType(str,Enum):VIDEO='video';IMAGE='image'
    quiet=SimpleNamespace(**{n:lambda *a,**k:None for n in ('info','debug','warning')})
    def module(relative,digest,names):
        path=args.runtime/relative;raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
        m=ModuleType('E5_'+path.stem);m.__file__=str(path)
        vars(m).update(torch=torch,rearrange=rearrange,amp=torch.amp,F=torch.nn.functional,DataType=DataType,log=quiet)
        nodes=[n for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef) and n.name in names]
        assert sorted(n.name for n in nodes)==sorted(names)
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future]+nodes,type_ignores=[])),str(path),'exec'),vars(m))
        return m
    wc=module(WC_PATH,WC_SHA,['worldcache_mini_train_dit_forward','apply_worldcache',
        'compute_optimal_gamma','estimate_optical_flow','warp_feature','compute_saliency_map'])
    rf=module(RF_PATH,RF_SHA,['denoise']);rf.Video2WorldModelRectifiedFlow=SimpleNamespace(denoise=rf.denoise)
    NativeHead=native_final_layer(args.runtime)
    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__();self.blocks=pinned_blocks(args.runtime)
            self.final_layer=NativeHead(8,1,1,8)
            self.use_crossattn_projection=self.use_wan_fp32_strategy=False
            self.t_embedder=lambda t:(t.unsqueeze(-1).expand(*t.shape,8),None)
            self.t_embedding_norm=lambda t:t
            self.prepare_embedded_sequence=lambda x,**kw:(x.movedim(1,-1).contiguous(),None,None)
            self.unpatchify=lambda x:x.movedim(-1,1).contiguous()
        def forward(self,**kw):return wc.worldcache_mini_train_dit_forward(self,**kw)
    shape=(1,8,2,16,16);noise=torch.linspace(-.3,.7,4096).reshape(shape);initial=noise+.7
    class Condition:
        def __init__(self,b):
            self.is_video=self.use_video_condition=True;self.gt_frames=torch.full(shape,.2)
            self.condition_video_input_mask_B_C_T_H_W=torch.zeros(1,1,2,16,16)
            self.condition_video_input_mask_B_C_T_H_W[:,:,0]=1
            self.cross=torch.ones(1,3,8)*(b+1)
        def to_dict(self):return {'crossattn_emb':self.cross,'data_type':DataType.VIDEO}
    conditions=tuple(Condition(b) for b in (0,1));condition_sha=tree_digest([vars(c) for c in conditions])
    records=[];restores=0
    def run(flow,method,fast,fault=None):
        nonlocal restores
        saved_gt=[c.gt_frames.clone() for c in conditions]
        torch.manual_seed(92817);net=Net().eval()
        wc.apply_worldcache(net,num_steps=70,ret_ratio=.2,rel_l1_thresh=.08,probe_depth=2,
                            osi_enabled=True,flow_enabled=flow,flow_scale=1)
        model=SimpleNamespace(net=net,tensor_kwargs={'dtype':torch.float32},
            config=SimpleNamespace(conditional_frame_timestep=.2,denoise_replace_gt_frames=True))
        model.denoise=MethodType(rf.denoise,model)
        cls=EarlyHeadPartialDeployment if fast else GuidedPartialDeployment
        d=cls(model,method='ROTATION_050',a_method=method,context=('E5_CPU','FIXED_CPD',str(flow)),
              layers=LAYERS,p_steps=P_STEPS)
        r=d.readout
        # Explicit fallback controls use the same original predictor in both
        # versions except these predeclared unavailable-candidate locations.
        if method=='W1_ONE_PHASE':
            for branch,c in enumerate(d.dense):
                def unavailable(self,*,b=branch,original=type(c).predict,**kw):
                    if r.current['step']==11 or (r.current['step']==8 and b==1):
                        return kw['official'],'E5_DECLARED_UNAVAILABLE'
                    return original(self,**kw)
                missing=type('DeclaredUnavailableCalibrator',(type(c),),{'predict':unavailable})()
                missing.reset(d.context);d.dense[branch]=missing
        if fault:
            original_hidden=d.hidden
            def injected(*values,**kw):
                original_hidden(*values,**kw)
                if r.current['step']==8 and values[2]==0:
                    entry=r.current['branches'][0]
                    assert entry['proposed_head'] is not None
                    if fault=='nonfinite':entry['proposed_head'].reshape(-1)[0]=float('nan')
                    elif fault=='coordinates':entry['proposed_head']=entry['proposed_head'][:,:,:,:-1]
                    elif fault=='conditions':conditions[0].gt_frames.add_(1)
                    elif fault=='parameters':next(net.parameters()).add_(1)
                    else:raise AssertionError(fault)
            d.hidden=injected
        compile_fn=compile_early_head_collection if fast else compile_collection
        _,denoise,proof=compile_fn(args.runtime,wc,rf,d,dense_context=d.dense_context)
        base=NativePolicyPairedExecutor(model,denoise,torch,wc_forward=wc.worldcache_mini_train_dit_forward,
                                       rf_denoise=rf.denoise)
        executor=PartialDeploymentPair(base,d)
        # Reuse accepted complete owned-state methods, with an explicit new
        # binding for the CPU guard and without unsupported observer hooks.
        class FixtureOwner(GuidedSamplingOwner):
            def installation(self):
                return super().installation()+(id(getattr(self.deployment.readout,'e5_guard',None)),VERSION if fast else 'LEGACY')
        owner=FixtureOwner.__new__(FixtureOwner)
        owner.model=model;owner.net=net;owner.method='ROTATION_050';owner.context=d.context;owner.a_method=method
        owner.deployment=d;owner.base=base;owner.executor=executor;owner.cache={};owner.hooks=[]
        owner.linear_rows=[];owner.head_calls=[];owner.step=0
        solver=SimpleNamespace(step=0,history=[]);latent=initial.clone();vectors=[];states=[]
        calls=0
        def profile(frame,event,arg):
            nonlocal calls
            if event=='call' and frame.f_code is NativeHead.forward.__code__:
                calls+=1
        previous=sys.getprofile();assert previous is None
        sys.setprofile(profile)
        failure=None
        try:
            with torch.no_grad():
                for step in range(1,37):
                    owner.step=step
                    values=executor.pair(noise,latent,torch.full((1,1),1-step/50),conditions,executor.choose)
                    guided=values[0]+7*(values[0]-values[1]);vectors.append(guided.detach().clone())
                    latent=latent-.001*guided;solver.step=step;solver.history.append(guided.detach().clone())
                    fields={k:tree_digest(getattr(net,k)) for k in WC_FIELDS if hasattr(net,k)}
                    dense=[c.receipt() for c in d.dense]
                    states.append({'step':step,'action':d.history[-1]['action'],'fields':fields,
                        'dense':dense,'working':tree_digest(plain(d.working)),
                        'projections':tree_digest(plain(d.core.cache)),
                        'rng':tree_digest(torch.get_rng_state()),'buffers':tree_digest(dict(net.named_buffers())),
                        'conditions':tree_digest([vars(c) for c in conditions])})
                    if step in (12,26):
                        physical=CompleteStateRoundtrip(net,solver,latent)
                        own=CPUDeploymentRoundtrip(owner,logical_copy_cap_bytes=64*1024**2,CPU_storage_cap_bytes=64*1024**2)
                        before=physical.fingerprint();owned=owner.fingerprint()
                        net.previous_output[0].add_(17);solver.history.clear();torch.rand(3)
                        d.working=[None,None];r.history.clear();r.completed=-9
                        d.dense[0].anchors.clear()
                        physical.restore();own.restore()
                        assert physical.fingerprint()==before and owner.fingerprint()==owned
                        restores+=1
                summary=d.finish()
        except ValueError as error:
            if fault is None:raise
            failure=str(error)
        finally:sys.setprofile(previous);d.close()
        if fault:
            assert failure and d.poisoned and base.poisoned and len(vectors)==7,(fault,failure,len(vectors))
            if fault=='conditions':
                for c,saved in zip(conditions,saved_gt):c.gt_frames.copy_(saved)
            # An unsupported branch is retained and never repaired/resumed.
            refused=0
            for call in (d.finish,r.finish):
                try:call()
                except ValueError:refused+=1
            assert refused==2
            path=args.output/('fault_'+fault+'.pt')
            torch.save({'guided':vectors,'final_latent':latent},path)
            return {'fault':fault,'error':failure,'planned_pairs':36,'completed_pairs':7,
                'poisoned_no_resume':True,'finish_refusals':refused,'path':str(path),
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        assert len(vectors)==36 and tree_digest([vars(c) for c in conditions])==condition_sha
        history=summary['A_readout']['history']
        expected=sum(x['total_head_calls'] for x in history) if fast else 72+sum(x['extra_heads'] for x in history)
        assert calls==expected,(calls,expected)
        if fast:
            if method=='OFF':assert calls==72 and not any(any(h['original_head_elided']) for h in history)
            else:
                assert any(any(h['original_head_elided']) for h in history)
                assert all(not any(h['original_head_elided']) for h in history if h['action']!='CC' or h['step']>=25)
            if method=='W1_ONE_PHASE':
                assert history[7]['original_head_elided']==[True,False]
                assert history[10]['original_head_elided']==[False,False]
        label='flow'+str(flow)+'_'+method+('_FAST' if fast else '_LEGACY');path=args.output/(label+'.pt')
        torch.save({'guided':vectors,'final_latent':latent},path)
        record={'label':label,'flow':flow,'method':method,'fast':fast,'path':str(path),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'states':states,'actual_native_head_calls':calls,
            'compiler':dict(proof),'summary':summary}
        records.append(record);return record
    pairs=[];comparisons=0;bookkeeping_changes=0
    for flow in (False,True):
        for method in ('OFF','W1_ONE_PHASE','BETA1_ONE_PHASE'):
            old=run(flow,method,False);new=run(flow,method,True)
            a=torch.load(old['path'],weights_only=True,map_location='cpu')
            b=torch.load(new['path'],weights_only=True,map_location='cpu')
            assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
            comparisons+=37
            for x,y in zip(old['states'],new['states']):
                assert {k:v for k,v in x.items() if k!='fields'}=={k:v for k,v in y.items() if k!='fields'}
                assert {k:v for k,v in x['fields'].items() if k!='previous_output'}=={k:v for k,v in y['fields'].items() if k!='previous_output'}
                bookkeeping_changes+=x['fields']['previous_output']!=y['fields']['previous_output']
            saved=old['actual_native_head_calls']-new['actual_native_head_calls']
            assert saved==sum(sum(h['original_head_elided']) for h in new['summary']['A_readout']['history'])
            pairs.append({'flow':flow,'method':method,'actual_old_heads':old['actual_native_head_calls'],
                'actual_new_heads':new['actual_native_head_calls'],'saved_native_heads':saved,'direct_tensor_equalities':37})
    branch_failures=[run(False,'BETA1_ONE_PHASE',True,fault=name)
                     for name in ('nonfinite','coordinates','conditions','parameters')]
    # Dynamic unsupported heads fail before eliding a native call.
    refusals=[]
    def refuse(name,mutate):
        torch.manual_seed(11);net=Net().eval();guard=PureNativeHeadGuard(net,args.runtime)
        remove=mutate(net)
        try:
            guard.validate()
        except (ValueError,AttributeError) as e:refusals.append({'name':name,'error':str(e)})
        else:raise AssertionError('Unsupported head accepted: '+name)
        finally:
            if remove:remove()
    refuse('buffer',lambda n:n.final_layer.register_buffer('unexpected',torch.zeros(1)))
    def hook(n):
        h=n.final_layer.register_forward_hook(lambda *a:None);return h.remove
    refuse('head_hook',hook)
    def childhook(n):
        h=n.final_layer.linear.register_forward_pre_hook(lambda *a:None);return h.remove
    refuse('child_hook',childhook)
    refuse('training',lambda n:setattr(n.final_layer,'training',True))
    def parameter(n):
        with torch.no_grad():next(n.parameters()).add_(1)
    refuse('parameter_version',parameter)
    refuse('head_identity',lambda n:setattr(n,'final_layer',NativeHead(8,1,1,8).eval()))
    refuse('unpatchify_identity',lambda n:setattr(n,'unpatchify',lambda x:x))
    assert len(records)==12 and comparisons==222 and restores==24 and len(refusals)==7
    assert not torch.cuda.is_initialized()
    result={'status':'E5_CPU_FULL36_NATIVE_HEAD_EQUIVALENCE_PASS_NOT_REAL_GPU_ACCEPTANCE',
        'version':VERSION,'paths':records,'paired_comparisons':pairs,'direct_tensor_equalities':comparisons,
        'own_version_full_physical_and_owned_restores':restores,'changed_previous_output_steps':bookkeeping_changes,
        'unsupported_head_refusals':refusals,'actual_paired_branch_failures':branch_failures,
        'GPU_submissions':0,'CUDA_initialized':False,
        'declared_stand_ins':['small native weights','Toy attention','direct Toy latent update','Toy condition/prepare/unpatchify'],
        'no_real_video_or_latency_claim':True}
    (args.output/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('paths','unsupported_head_refusals')}))


if __name__=='__main__':main()
