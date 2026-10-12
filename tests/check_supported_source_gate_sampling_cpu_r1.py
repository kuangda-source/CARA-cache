"""Nine full36 methods, real native/RF/UniPC hooks, age6 and clean parity."""
import copy,functools,inspect
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.supported_source_gate_batch_r1 import execute,matrix,METHODS
from wcomr.supported_source_gate_control_r1 import SupportedGateController
from wcomr.math_n2_batch_r1 import execute as prior_execute
from wcomr.supported_source_gate_owner_r1 import SupportedGateOwner
from wcomr import clean_speed20_r1 as clean

def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    p=Path(__file__).with_name(name+'.py');s=spec_from_file_location(name,p)
    m=module_from_spec(s);s.loader.exec_module(m);return m

def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    cal=Calibration('SYNTHETIC_SG_ACTUAL_AGE6',{(a,n):.99 for a in range(1,36)
        for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec={'threshold':2.,'costs':Costs('SYNTHETIC_SG',1.,4.,.8),
        'partial_prior':CreationPhasePrior('SYNTHETIC_SG',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
        'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
    specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec}
    old={'fingerprint':'SYNTHETIC_N2_UNCHANGED','gamma':.5,'lambda_seconds_per_normalized_error':100.,
        'A_pair_cost_seconds':1.1,'source':{'D':{'C_scale':1.,'A_over_C':.25},'P':{'C_scale':2.,'A_over_C':.3}}}
    new={**old,'fingerprint':'SYNTHETIC_SG_NOT_CAL_FIT','source_A_cost_seconds':{'D':1.1,'P':1.3}}
    def native(self,*a,**kw):
        threshold=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=threshold
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint()
    net0,pipe0=net.forward,inference.pipe.worldcache_enabled;checks=[];sources=set();A_sources=set()
    try:
        for index,sample in enumerate(selected):
            for method in METHODS:
                common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                    inference_module=inference_module,expected_shape=config['expected_shape'],CPU_native=native)
                initial.restore()
                audit,_=execute(inference,sample,method,parameters=new,previous_parameters=old,
                    output=Path(artifact_root)/str(flow)/str(index)/(method+'_AUDIT'),audit=True,**common)
                initial.restore()
                # Baselines independently invoke the previous untouched batch;
                # new paths use the same physical owner through the lean bridge.
                if method in METHODS[:6]:
                    lean,_=prior_execute(inference,sample,method,parameters=old,
                        output=Path(artifact_root)/str(flow)/str(index)/(method+'_LEAN'),audit=False,**common)
                else:
                    lean,_=execute(inference,sample,method,parameters=new,previous_parameters=old,
                        output=Path(artifact_root)/str(flow)/str(index)/(method+'_LEAN'),audit=False,**common)
                assert audit['status']==lean['status']=='COMPLETE'
                assert audit['solver_steps']==audit['guided_pairs']==36 and len(audit['guided'])==36
                assert audit['actions']==lean['actions'] and audit['A_history']==lean['A_history']
                assert torch.equal(audit['final_latent'],lean['final_latent'])
                assert Path(audit['video_path']).read_bytes()==Path(lean['video_path']).read_bytes()
                assert lean['in_timing_hashes']==lean['in_timing_guided_copies']==lean['research_checkpoints']==0
                assert all(r['teacher_calls']==r['extra_deep_blocks']==0 for r in (audit.get('A_history') or []))
                if method in METHODS[6:]:
                    hist=audit['source_history'];assert len(hist)==36
                    c=SupportedGateController(cal,2.,spec['costs'],spec['partial_prior'],
                        strategy=spec['working_epoch_strategy'],math_parameters=new,
                        horizon=1 if method.endswith('H1') else 2,sigma_at=lambda n:float(scheduler.sigmas[n-1]),
                        allow_P_A=method=='PLUS_P_A_H2')
                    for row in hist:
                        sp=row['source_policy'];event=sp['event_math'];h=row['A_readout']
                        assert event['risk_unit']=='AMPLITUDE_GAIN_SQUARED_NORMALIZED_GUIDED_MSE_PROXY'
                        assert event['future_support_grid_same_as_execution'] and not event['D_A_rule_is_learned']
                        assert not row['P_updates_true_D_or_zero_risk_RA_anchor']
                        if row['action']!='DD':assert row['true_D_before']==row['true_D_after']
                        if row['action']=='PP':assert sp['creation_floor_proxy_after']>0
                        if row['action']=='CC':
                            kind=row['working_sources'][0]['kind'];sources.add(kind)
                            if kind=='D':assert h['readout_action']=='A' and h['extra_heads']==2
                            elif method!='PLUS_P_A_H2':assert h['readout_action']=='C' and h['extra_heads']==0
                            if h['readout_action']=='A':A_sources.add(kind)
                        # Reconstruct every choice from the original paid scalar fields.
                        choice=row['joint_decision'];values=tuple(tuple(p) for p in choice['packets'])
                        decision=c._choice(choice['step'],values,choice['both_sources_ready'],choice['partial_ready'],
                            protected=choice['reason']=='actual_protected_dense')
                        assert decision.reason==choice['reason'] and decision.action*2==row['action']
                        c.commit(decision,actual_action=decision.action,pair_completed=True)
                    snapshot=c.state_dict();c.accumulated=999.;c.restore(snapshot);assert c.state_dict()==snapshot
                checks.append({'scene':sample.name,'method':method,'full36':True,'clean_parity':True,'actions':audit['actions']})
        initial.restore();assert initial.fingerprint()==fp and net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        assert len(checks)==36 and 'D' in A_sources
        return [{'flow':flow,'status':'PASS','checks':checks,'complete_CPU_paths':72,
            'all36_clean_outputs_actions_video_equal':True,'actual_rho_age_max':6,
            'reuse_sources_exercised':sorted(sources),'A_sources_exercised':sorted(A_sources),
            'ordinary_initial_state_restored':True}]
    finally:initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0

def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise));start=source.index('    results=[]\n    try:')
    end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    ns={**vars(original),'_body':body};exec(compile(changed,__file__+'#declared-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='SUPPORTED_GATE_ALL72_AUDIT72_CLEAN_CPU_PASS_NOT_GPU',actual_CPU_paths=144,
        complete_method_paths=72,clean_control_paths=72,actual_GPU_or_real_video_claim=False)
    assert len(matrix(['a','b','c','d']))==54
    return value
