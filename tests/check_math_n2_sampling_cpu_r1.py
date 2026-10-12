"""All eight method paths x four Toy requests x both actual flow modes."""
import copy
import functools
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.math_n2_sampling_owner_r1 import MathSamplingOwner
from wcomr.p_reference_same_state_owner_r1 import ComparisonReadout
from wcomr.source_aware_current_birth_sampling_r2 import CurrentBirthSamplingOwner

METHODS=('NATIVE','RA','A_NO_P','NONZERO_CPD','P_OFF','SOURCE_H1','SOURCE_H2','H2_P_TO_D')

def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    p=Path(__file__).with_name(name+'.py');s=spec_from_file_location(name,p)
    m=module_from_spec(s);s.loader.exec_module(m);return m


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    cal=Calibration('SYNTHETIC_N2_ALL36',{(a,s):.99 for a in range(1,36) for s in range(a+1,37)},
                    {s:1. for s in range(1,37)})
    spec={'threshold':2.,'costs':Costs('SYNTHETIC_N2',1.,4.,.8),
          'partial_prior':CreationPhasePrior('SYNTHETIC_N2',.005,.3,
               early_creation_floor=.005,late_creation_floor=.02),
          'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
    specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec}
    params={'fingerprint':'SYNTHETIC_ONLY_NOT_N1_FIT','gamma':.5,
        'lambda_seconds_per_normalized_error':100.,'A_pair_cost_seconds':1.1,
        'source':{'D':{'C_scale':1.,'A_over_C':.25},'P':{'C_scale':2.,'A_over_C':.3}}}
    def native(self,*a,**kw):
        threshold=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=threshold
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint()
    net0,pipe0=net.forward,inference.pipe.worldcache_enabled;checks=[];controls=[]
    try:
        for index,sample in enumerate(selected):
            plans={};outputs={}
            def execute(label,factory=None):
                initial.restore();holder={}
                def wrapped(*a,**kw):
                    owner=factory(*a,**kw);holder['owner']=owner;return owner
                method=label if label in ('NATIVE','RA','A_NO_P') else 'KEEP_A_P'
                with clean.patched(clean,'CurrentBirthSamplingOwner',wrapped if factory else CurrentBirthSamplingOwner):
                    result=clean.execute(inference,sample,method,runtime=runtime,wc=wc,rf=rf,
                       settings=settings,calibration=cal,specs=specs,inference_module=inference_module,
                       output=Path(artifact_root)/str(flow)/str(index)/label,
                       expected_shape=config['expected_shape'],audit=True,CPU_native=native)
                assert result['status']=='COMPLETE' and len(result['guided'])==36
                if holder.get('owner'):plans[label]=copy.deepcopy(holder['owner'].controller.history)
                return result
            for method in METHODS:
                factory=None
                if method=='NONZERO_CPD':
                    def factory(*a,**kw):
                        kw['method']='CPD';return CurrentBirthSamplingOwner(*a,**kw)
                elif method not in ('NATIVE','RA','A_NO_P'):
                    options={'math_parameters':params,'source_mode':'P_OFF' if method=='P_OFF' else 'FUSION',
                             'horizon':None if method=='P_OFF' else 1 if method=='SOURCE_H1' else 2}
                    if method=='H2_P_TO_D':
                        mask=[d.reason.rsplit(':',1)[-1] if d.reason.startswith('MATH_EVENT_') else d.action
                              for d in plans['SOURCE_H2']]
                        mask=['D' if a=='P' else a for a in mask]
                        options['fixed_control_plan']=mask
                    factory=functools.partial(MathSamplingOwner,**options)
                result=execute(method,factory);outputs[method]=result
                assert result['solver_steps']==result['guided_pairs']==36
                if method=='H2_P_TO_D':assert 'PP' not in result['actions']
                if method in ('SOURCE_H1','SOURCE_H2'):
                    decision=plans[method];assert len(decision)==36
                    assert [d.action*2 for d in decision]==result['actions']
                    assert all(h['teacher_calls']==h['extra_deep_blocks']==0 for h in result['A_history'])
                    assert all(h['C_or_P_observation_updates_D_anchor'] is False for h in result['A_history'])
                    # Replay full healthy histories after perturbation.
                    c=holder_control_factory(cal,spec,params,1 if method=='SOURCE_H1' else 2,
                                             lambda n:float(scheduler.sigmas[n-1]))
                    for d in decision:
                        new=c._choice(d.step,d.packets,d.both_sources_ready,d.partial_ready,
                                      protected=d.reason=='actual_protected_dense')
                        c.commit(new,actual_action=new.action,pair_completed=True)
                    snapshot=c.state_dict();c.accumulated=999.;c.restore(snapshot)
                    assert c.state_dict()==snapshot
                checks.append({'scene':sample.name,'method':method,'flow':flow,'full36':True,
                               'actions':result['actions'],'teachers':0})
            # Compare the lean production implementation to both original
            # reference endpoints on their own full trajectories, not a Toy
            # copy of the new formula. Four additional full paths per scene.
            for gamma in (0.,1.):
                def reference(*a,**kw):
                    o=CurrentBirthSamplingOwner(*a,**kw);old=o.deployment.readout
                    r=ComparisonReadout(o.deployment,method=old.method)
                    r.warp,r.to_velocity=old.warp,old.to_velocity
                    r.reference_variant='D_REFERENCE_UNIT' if gamma==0 else 'P_REFERENCE_UNIT'
                    o.deployment.readout=r;return o
                old=execute('REFERENCE_'+str(gamma),reference)
                new=execute('LEAN_'+str(gamma),functools.partial(MathSamplingOwner,
                    math_parameters={**params,'gamma':gamma}))
                assert old['actions']==new['actions'] and torch.equal(old['final_latent'],new['final_latent'])
                assert all(torch.equal(x,y) for x,y in zip(old['guided'],new['guided']))
                assert Path(old['video_path']).read_bytes()==Path(new['video_path']).read_bytes()
                controls.append({'scene':sample.name,'gamma':gamma,'all36_outputs_actions_final_video_equal':True})
        initial.restore();assert initial.fingerprint()==fp
        assert net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        assert len(checks)==32 and len(controls)==8
        return [{'flow':flow,'status':'PASS','checks':checks,'endpoint_controls':controls,
                 'complete_CPU_paths':48,'ordinary_initial_state_restored':True}]
    finally:initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0


def holder_control_factory(cal,spec,params,horizon,sigma):
    from wcomr.math_n2_event_control_r1 import EventController
    return EventController(cal,spec['threshold'],spec['costs'],spec['partial_prior'],
        strategy=spec['working_epoch_strategy'],math_parameters=params,horizon=horizon,sigma_at=sigma)


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise));start=source.index('    results=[]\n    try:')
    end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    ns={**vars(original),'_body':body};exec(compile(changed,__file__+'#declared-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='MATH_N2_ALL64_METHOD_PATHS32_ENDPOINT_CONTROLS_CPU_PASS_NOT_GPU',
        actual_CPU_paths=96,complete_method_paths=64,endpoint_control_paths=32,
        actual_GPU_or_real_video_claim=False)
    return value
