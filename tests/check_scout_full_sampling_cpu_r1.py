"""Complete registered scout scopes through pinned RF/UniPC with declared Toy weights."""
import inspect
from pathlib import Path
from textwrap import dedent

import torch
from wcomr.scout_sampling_r1 import execute, plans
from wcomr.drop1_full18_r1 import execute as old_execute
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.source_phase_absolute_h1_control_r1 import VERSION, fingerprint


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,kind):
    net=inference.pipe.model.net; scheduler=inference.pipe.model.sample_scheduler
    cal=Calibration('SYNTHETIC_SCOUT_AGE6',{(a,n):.99 for a in range(1,36)
        for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec=dict(threshold=2.,costs=Costs('SYNTHETIC',1.,4.,3.5),partial_prior=CreationPhasePrior(
        'SYNTHETIC',.005,.3,early_creation_floor=.005,late_creation_floor=.02),working_epoch_strategy='WORKING_P_AGE_NONZERO_REBASE')
    specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec};old={'fingerprint':'SYNTHETIC_PRIOR_UNCHANGED','gamma':.5}
    p=dict(version=VERSION,gamma=.5,table_model=dict(grouping='SOURCE_PHASE',target='absolute_guided_MSE',
        current_teacher_energy_is_online_feature=False,cells={s+'_'+phase:dict(status='FIT',C_scale=100.,
        A_ratios={'FUSION_A':.02},actual_NEW_P_birth_mean=.0001) for s in ('D','P') for phase in ('EARLY','LATE')}),
        cost_seconds={'C':1.,'A':1.3,'P':3.5,'D':4.},source_A_cost_seconds={'D':1.1,'P':1.3},lambda_seconds_per_weighted_absolute_MSE=100.)
    p['fingerprint']=fingerprint(p); tables={'SOURCE_PHASE':p}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    n=4 if kind=='CAL12' else 6
    samples=[type(selected[0])(f'SCOUT_{kind}_CPU_{i}') for i in range(n)]
    def native(self,*args,**kw):
        thresh=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*args,**kw)
        finally:self.worldcache_rel_l1_thresh=thresh
    def run(sample,method,audit,observe,out,executor=execute):
        initial.restore();assert initial.fingerprint()==origin
        kwargs=dict(table_parameters=tables,previous_parameters=old,runtime=runtime,wc=wc,rf=rf,settings=settings,
            calibration=cal,specs=specs,inference_module=inference_module,expected_shape=config['expected_shape'],output=out,audit=audit)
        if executor is execute:kwargs.update(kind=kind,observer=observe,CPU_native=native)
        return executor(inference,sample,method,**kwargs)
    checks=[];count=0
    try:
        for i,sample in enumerate(samples):
            all_audit={}
            for method,plan in plans(kind).items():
                group=[]
                for audit in (True,False):
                    for observe in (False,True):
                        row=run(sample,method,audit,observe,Path(artifact_root)/str(flow)/str(i)/f'{method}_{audit}_{observe}')
                        count+=1
                        assert row['status']=='COMPLETE' and row['solver_steps']==row['guided_pairs']==36
                        assert row['request_memory_lifecycle']['owners_alive_after']==0
                        if method!='NATIVE35':
                            assert row['semantic_plan']==list(plan) and row['actions']==['DD' if a=='D' else 'CC' for a in plan]
                            for a,h in zip(plan,row['source_history']):
                                assert h['A_readout']['readout_action']==a and h['teacher_calls']==0
                                if a!='D':assert h['true_D_before']==h['true_D_after']
                            if observe:
                                assert set(row['scout_vectors'])=={'p20_c','p20_u','p21_c','p21_u','v_actual21','v_returned21'}
                                assert row['scout_observation']['probe_copies']==4 and row['scout_observation']['velocity_copies']==2
                        group.append(row)
                ref=group[0]
                for row in group[1:]:
                    assert torch.equal(ref['final_latent'],row['final_latent'])
                    assert ref['actions']==row['actions'] and ref['A_history']==row['A_history']
                    assert Path(ref['video_path']).read_bytes()==Path(row['video_path']).read_bytes()
                    if row['audit']:assert all(torch.equal(a,b) for a,b in zip(ref['guided'],row['guided']))
                all_audit[method]=group[1]
                # The control has the exact registered original mask, with the
                # same restored Toy input and unchanged production executor.
                old_method=('S25-C' if method=='G01_LATE_A' else 'S26-C') if kind=='CAL12' else {'D21':'S26-C','A21':'S25-A','NATIVE35':None}[method]
                if old_method:
                    legacy=run(sample,old_method,True,False,Path(artifact_root)/str(flow)/str(i)/('legacy_'+method),old_execute);count+=1
                    prefix=21 if kind=='CAL12' else 36
                    assert all(torch.equal(a,b) for a,b in zip(legacy['guided'][:prefix],ref['guided'][:prefix]))
                checks.append(dict(scene=sample.name,method=method,all36_observer_OFF_ON_audit_equal=True,
                    all4_modes_final_actions_history_CPU_video_equal=True,old_full_or_common_prefix_verified=bool(old_method),
                    owners_released=True))
            if kind=='BANK24':
                d,a=(all_audit[k] for k in ('D21','A21'))
                assert d['scout_observation']['pre_action_input_sha256']==a['scout_observation']['pre_action_input_sha256']
                assert all(torch.equal(x,y) for x,y in zip(d['guided'][:20],a['guided'][:20]))
                for key in ('p20_c','p20_u','p21_c','p21_u'):
                    assert torch.equal(d['scout_vectors'][key],a['scout_vectors'][key])
            else:
                c,d=(all_audit[k] for k in ('G01_LATE_A','VARIATION26_C'))
                assert c['scout_observation']['pre_action_input_sha256']==d['scout_observation']['pre_action_input_sha256']
        expected=40 if kind=='CAL12' else 84
        assert count==expected and len(checks)==n*len(plans(kind))
        return [dict(flow=flow,status='PASS',complete_CPU_paths=count,checks=checks,
            full36_output_and_owner_controls=True,ordinary_initial_state_restored=True,
            CPU_video_payload_is_not_real_93frame_video=True)]
    finally:
        initial.restore();assert initial.fingerprint()==origin


def run(runtime,tensor_loader,artifact_root,*,kind):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,_kind)\n'+source[end:]
    ns={**vars(original),'_body':body,'_kind':kind};exec(compile(changed,__file__+'#unchanged-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='SCOUT_'+kind+'_COMPLETE_SAMPLING_CPU_PASS_NOT_GPU',kind=kind,
        actual_CPU_paths=sum(c['complete_CPU_paths'] for c in value['checks']),
        actual_GPU_or_real_video_claim=False)
    return value
