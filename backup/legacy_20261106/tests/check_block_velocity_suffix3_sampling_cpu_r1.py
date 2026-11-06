"""CPU implementation proof for three saved velocities; L2 fixture is synthetic.

No B accuracy claim: real D/L2 artifacts are separately bound for production.
This test isolates exact-prefix refusal, single injection, solver/state/RNG
restore, unchanged parent and full endpoint equality under reverse order.
"""
import copy
import inspect
from pathlib import Path
from textwrap import dedent
import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.math_n2_sampling_owner_r1 import MathSamplingOwner
from wcomr.block_velocity_suffix3_r1 import block_velocity_suffix_install,LABELS
from wcomr.pi0_readout_suffix8_r1 import pi0_readout_suffix_install
from wcomr.partial_mlp_deployment_state import plain
from wcomr.mid_coverage import tree_digest
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.rv0_causal import original_decode_tails


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m


class PrefixFixtureOwner(MathSamplingOwner):
    def __init__(self,*a,scene,**kw):
        super().__init__(*a,**kw);self.references={};self.scene=scene

    def pair(self,noise,latent,timestep,conditions,choose):
        n=len(self.history)+1
        ref=dict(scene=self.scene,step=n,input_sha256=tree_digest((noise,latent,timestep)),
            source_state_sha256=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache)),
            true_D_state_sha256=tree_digest(plain([vars(d) for d in self.deployment.dense])))
        v=super().pair(noise,latent,timestep,conditions,choose)
        ref['vectors']={label:tuple((t.detach().cpu().clone()*scale) for t in v)
            for label,scale in [('DENSE_VELOCITY',1.01),('L2_VELOCITY',.99)]}
        ref['synthetic_vectors_not_true_D_or_L2']=True
        self.references[n]=ref;return v


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    gains={n:1. for n in range(1,37)}
    for n in (8,9,10,25,27,28,29,30,31,32,33,34,35):gains[n]=0.
    gains[26]=1000.
    cal=Calibration('SYNTHETIC_SUFFIX3_CELLS',
        {(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},gains)
    spec=dict(threshold=.04,costs=Costs('SYNTHETIC_SUFFIX3',1.,4.,3.),
        partial_prior=CreationPhasePrior('SYNTHETIC_SUFFIX3',.0001,.3,
            early_creation_floor=.0001,late_creation_floor=10.),
        working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs={'A_CPD_BETA1_ONE_PHASE':spec};params={'gamma':.5,'fingerprint':'SYNTHETIC_ONLY'}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint()
    net0=net.forward;pipe0=inference.pipe.worldcache_enabled
    decoder,writer,tails=original_decode_tails(runtime,inference_module);ordinary_writer=inference_module.save_img_or_video
    cells=(('D','EARLY',3),('D','LATE',2),('P','EARLY',2),('P','LATE',1))
    select=load('check_pi0_readout_suffix8_sampling_cpu_r1').select;checks=[]
    try:
        for index,(sample,(source,phase,target)) in enumerate(zip(selected,cells)):
            directory=Path(artifact_root)/str(flow)/str(index);initial.restore();holder={}
            common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                inference_module=inference_module,expected_shape=config['expected_shape'],audit=True)
            def parent(*a,**kw):
                o=PrefixFixtureOwner(*a,scene=sample.name,math_parameters=params,source_mode='P_OFF',**kw)
                holder['parent']=o;return o
            with clean.patched(clean,'CurrentBirthSamplingOwner',parent):
                ordinary=clean.execute(inference,sample,'KEEP_A_P',output=directory/'ordinary',**common)
            parent=holder['parent'];point=select(sample.name,parent.history,source,phase,target)
            n=point['chosen']['step'];reference=parent.references[n]
            def endpoint_writer(root):
                def save(step,label,tensors):
                    d=directory/root/label;d.mkdir(parents=True);raw=d/'vectors.pt';torch.save(tensors,raw)
                    with clean.patched(inference_module,'save_img_or_video',ordinary_writer):
                        video=decoder(inference.pipe,tensors['final_latent'].to(model.tensor_kwargs['device']))
                        path=writer(inference,video,d/sample.name)
                    assert path is not None and Path(path).exists()
                    return dict(path=str(raw),tensor_sha256=tree_digest(tensors),video_path=str(path),original_tails=tails)
                return save
            initial.restore();old={}
            with pi0_readout_suffix_install(clean,scheduler,point,config,endpoint_writer('old'),params,old,runtime=runtime):
                old_parent=clean.execute(inference,sample,'KEEP_A_P',output=directory/'old_parent',**common)
            old_C=next(b for b in old['owner'].event_records[0]['branches'] if b['first_readout']=='C')
            old_raw=tensor_loader(Path(old_C['artifact']['path']),map_location='cpu',weights_only=True)
            new_by_order=[]
            for reverse in (False,True):
                initial.restore();new={}
                with block_velocity_suffix_install(clean,scheduler,point,reference,config,
                        endpoint_writer('new_'+str(reverse)),params,new,runtime=runtime,reverse_order=reverse):
                    value=clean.execute(inference,sample,'KEEP_A_P',output=directory/('parent_'+str(reverse)),**common)
                owner=new['owner'];event=owner.event_records[0];by={b['label']:b for b in event['branches']}
                assert len(owner.event_records)==1 and set(by)==set(LABELS)
                assert len(event['serial_restores'])==6 and owner.actual_pair_computations==36+3*(37-n)
                assert event['actual_teacher_calls']==event['actual_B_executor_calls']==0
                assert owner.injections==dict(C_REPLAY=0,DENSE_VELOCITY=1,L2_VELOCITY=1)
                for v in (old_parent,value):
                    assert v['status']==ordinary['status']=='COMPLETE' and v['solver_steps']==v['guided_pairs']==36
                    assert v['actions']==ordinary['actions'] and torch.equal(v['final_latent'],ordinary['final_latent'])
                    assert all(torch.equal(a,b) for a,b in zip(v['guided'],ordinary['guided']))
                    assert Path(v['video_path']).read_bytes()==Path(ordinary['video_path']).read_bytes()
                data={}
                for label,b in by.items():
                    raw=tensor_loader(Path(b['artifact']['path']),map_location='cpu',weights_only=True);data[label]=raw
                    assert tree_digest(raw)==b['artifact']['tensor_sha256']
                    assert len(raw['guided'])==len(b['actions'])==37-n
                    assert b['actions'][0]=='CC' and b['readout_actions'][0]=='C'
                    first=b['source_policy_tail'][0];assert first['true_D_before']==first['true_D_after']
                    assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in b['source_policy_tail'][1:])
                    if label=='C_REPLAY':
                        assert torch.equal(raw['final_latent'],old_raw['final_latent'])
                        assert all(torch.equal(a,b) for a,b in zip(raw['guided'],old_raw['guided']))
                        assert b['actions']==old_C['actions']
                    else:
                        c,u=reference['vectors'][label]
                        assert torch.equal(raw['guided'][0],c+7*(c-u))
                        assert b['first_returned_velocity_sha256']==tree_digest((c,u))
                assert len({b['first_C_cache_state_sha256'] for b in by.values()})==1
                new_by_order.append((by,data))
            for label in LABELS:
                a,b=(v[1][label] for v in new_by_order)
                assert torch.equal(a['final_latent'],b['final_latent'])
                assert all(torch.equal(x,y) for x,y in zip(a['guided'],b['guided']))
                assert new_by_order[0][0][label]['actions']==new_by_order[1][0][label]['actions']
                assert Path(new_by_order[0][0][label]['artifact']['video_path']).read_bytes()==Path(new_by_order[1][0][label]['artifact']['video_path']).read_bytes()
            checks.append(dict(scene=sample.name,source=source,phase=phase,registered_step=n,
                both_three_arm_orders_and_complete_parent_equal=True,first_C_caches_equal=True,
                injected_two_saved_vectors_exact=True,synthetic_only_not_B_quality=True))
        initial.restore();assert initial.fingerprint()==fp and net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        return [dict(flow=flow,status='PASS',checks=checks,full_CPU_parents=16,endpoint_suffixes=32,
                     initial_state_restored=True,all_four_source_phase_cells=True)]
    finally:initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    ns={**vars(original),'_body':body}
    replacement='    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader)\n'
    exec(compile(source[:start]+replacement+source[end:],__file__+'#declared-Toy-setup','exec'),ns)
    r=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {v['flow'] for v in r['checks']}=={False,True}
    r.update(status='B_SAVED_VELOCITY_SUFFIX3_TWO_FLOW32_PARENTS64_SUFFIXES_CPU_PASS_NOT_GPU',
             actual_CPU_parents=32,endpoint_suffixes=64,synthetic_vectors_not_true_D_or_L2=True,
             actual_GPU_or_real_video_claim=False)
    return r
