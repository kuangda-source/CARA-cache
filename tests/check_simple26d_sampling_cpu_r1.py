"""Two flows x four Toy CAL inputs x six actual executors x audit/lean."""
import inspect
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.simple26d_r1 import METHODS,plans,execute,CPU_STATUS
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.source_phase_absolute_h1_control_r1 import VERSION,fingerprint

def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m

def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    net=inference.pipe.model.net;scheduler=inference.pipe.model.sample_scheduler
    cal=Calibration('SYNTHETIC_AGE6',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec=dict(threshold=2.,costs=Costs('SYNTHETIC',1.,4.,3.5),partial_prior=CreationPhasePrior('SYNTHETIC',.005,.3,early_creation_floor=.005,late_creation_floor=.02),working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec};old={'fingerprint':'SYNTHETIC_PRIOR_UNCHANGED','gamma':.5}
    p=dict(version=VERSION,gamma=.5,table_model=dict(grouping='SOURCE_PHASE',target='absolute_guided_MSE',current_teacher_energy_is_online_feature=False,
        cells={s+'_'+phase:dict(status='FIT',C_scale=100.,A_ratios={'FUSION_A':.02},actual_NEW_P_birth_mean=.0001) for s in ('D','P') for phase in ('EARLY','LATE')}),
        cost_seconds={'C':1.,'A':1.3,'P':3.5,'D':4.},source_A_cost_seconds={'D':1.1,'P':1.3},lambda_seconds_per_weighted_absolute_MSE=100.)
    p['fingerprint']=fingerprint(p);tables={'SOURCE_PHASE':p}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint();checks=[]
    try:
        for i,sample in enumerate(selected):
            for method in METHODS:
                outcomes=[]
                for audit in (True,False):
                    initial.restore();assert initial.fingerprint()==origin
                    v=execute(inference,sample,method,table_parameters=tables,previous_parameters=old,
                        runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,inference_module=inference_module,
                        expected_shape=config['expected_shape'],output=Path(artifact_root)/str(flow)/str(i)/(method+str(audit)),audit=audit)
                    plan=plans()[method]
                    assert v['status']=='COMPLETE' and v['solver_steps']==v['guided_pairs']==36
                    assert v['semantic_plan']==list(plan) and v['actions'].count('DD')==26 and v['online_teacher_calls']==0
                    assert [h['A_readout']['readout_action'] for h in v['source_history']]==list(plan)
                    for a,h in zip(plan,v['source_history']):
                        assert h['teacher_calls']==h['A_readout']['teacher_calls']==h['A_readout']['extra_deep_blocks']==0
                        if a!='D':assert h['true_D_before']==h['true_D_after']
                        if a=='C':assert h['A_readout']['extra_heads']==0 and h['A_readout']['shared_alpha']==0
                    if not audit:assert v['in_timing_guided_copies']==v['in_timing_hashes']==v['research_checkpoints']==0
                    outcomes.append(v)
                x,y=outcomes
                assert torch.equal(x['final_latent'],y['final_latent']) and x['actions']==y['actions'] and x['A_history']==y['A_history']
                assert Path(x['video_path']).read_bytes()==Path(y['video_path']).read_bytes()
                checks.append(dict(scene=sample.name,method=method,DD=26,A=plan.count('A'),C=plan.count('C'),audit_lean_final_actions_RGB_equal=True))
        assert len(checks)==24
        return [dict(flow=flow,status='PASS',checks=checks,complete_CPU_paths=48,all36_clean_outputs_actions_video_equal=True,ordinary_initial_state_restored=True)]
    finally:initial.restore();assert initial.fingerprint()==origin

def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    ns={**vars(original),'_body':body};exec(compile(changed,__file__+'#declared-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status=CPU_STATUS,actual_CPU_paths=96,complete_method_paths=48,clean_control_paths=48,actual_GPU_or_real_video_claim=False)
    return value
