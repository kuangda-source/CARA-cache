"""Full48 H1 baseline/audited/quiet price20 paths, both flows and D/P sources.

Pinned full RF/condition/UniPC/inference bodies; Toy weights/attention/decode.
All96 origins and1920 complete action trials are retained. No real
teacher, video quality, latency claim, model weights or GPU is involved.
"""
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.source_phase_absolute_h1_control_r1 import VERSION,fingerprint
from wcomr import source_phase_absolute_h1_batch_r1 as batch
from wcomr import clean_speed20_r1 as clean
from wcomr.p_acr_profile20_owner_r1 import install_profile20,trial_plan
from wcomr.mid_coverage import tree_digest


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;sch=model.sample_scheduler
    cal=Calibration('SYNTHETIC_PA_H1_AGE6',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},
        {n:1. for n in range(1,37)})
    original=CompleteStateRoundtrip(net,sch,torch.zeros(1));oldforward=net.forward;initial=original.fingerprint()
    checks=[];source_kinds=set();extra_pairs=0;origins=0
    coeff={'fingerprint':'DECLARED_SYNTHETIC_INTERFACE_NOT_CAL_COEFFICIENTS',
           'cells':{s+'_'+phase:{'Pc_eta':.83,'Pu_zeta':.83} for s in ('D','P') for phase in ('EARLY','LATE')}}
    old={'fingerprint':'SYNTHETIC_PA_OLD_MATH','gamma':.5}
    try:
        for regime in ('P_WORKING_SOURCES','D_WORKING_SOURCES'):
            spec={'threshold':2.,'costs':Costs('SYNTHETIC_PA',1.,4.,3.5),
                'partial_prior':CreationPhasePrior('SYNTHETIC_PA',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
                'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
            specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec}
            # Both fixtures use a declared large synthetic scale, keeping the
            # original age1-6 support at every fixed diagnostic position.
            # Real frozen H1 parameters stay intact. Positive cheap/expensive
            # synthetic P birth costs distinguish the two source regimes.
            cells={key:{'status':'FIT','C_scale':1e9,'A_ratios':{'FUSION_A':.02},
                'actual_NEW_P_birth_mean':.0001 if regime=='P_WORKING_SOURCES' else 1e6} for key in ('D_EARLY','D_LATE','P_EARLY','P_LATE')}
            table={'version':VERSION,'gamma':.5,'table_model':{'grouping':'SOURCE_PHASE','target':'absolute_guided_MSE',
                'current_teacher_energy_is_online_feature':False,'cells':cells},
                'cost_seconds':{'C':1.,'A':1.3,'P':3.5,'D':4.},'source_A_cost_seconds':{'D':1.1,'P':1.3},
                'lambda_seconds_per_weighted_absolute_MSE':100.}
            table['fingerprint']=fingerprint(table)
            common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                inference_module=inference_module,expected_shape=config['expected_shape'],
                table_parameters={'SOURCE_PHASE':table},previous_parameters=old)
            for i,sample in enumerate(selected):
                original.restore()
                ordinary,_=batch.execute(inference,sample,'TABLE_PHASE_H1',output=Path(artifact_root)/str(flow)/regime/(str(i)+'_BASE'),audit=True,**common)
                assert ordinary['status']=='COMPLETE' and len(ordinary['guided'])==36
                # Teacher-free trace selection only; fixed original PA positions.
                positions=(12,23,29 if i in (0,2) else 30)
                points=[]
                for step in positions:
                    h=ordinary['source_history'][step-1];state=h['joint_decision']['state_before']
                    points.append({'step':step,'expected_source':state[1],'expected_source_birth':state[2],
                        'expected_source_age':step-state[2],'expected_H1_readout':h['A_readout']['readout_action']})
                print('PA_FIXED_CPU_PARENT_TRACE',{'flow':flow,'regime':regime,'scene':sample.name,
                    'points':points,'reasons':[ordinary['source_history'][s-1]['joint_decision']['reason'] for s in positions]},flush=True)
                profiles={}
                for quiet in (False,True):
                    recorded=[];holder={}
                    def writer(step,payload):
                        assert len(payload)==21
                        digest=tree_digest(payload)
                        recorded.append({'step':step,'sha256':digest})
                        return {'CPU_only_in_memory':True,'tensor_sha256':digest,'not_actual_GPU_artifact':True}
                    original.restore()
                    with install_profile20(clean,batch,sch,states=points,config=config,writer=writer,
                            coefficients=coeff,holder=holder,quiet_observers=quiet):
                        diagnosed,_=batch.execute(inference,sample,'TABLE_PHASE_H1',
                            output=Path(artifact_root)/str(flow)/regime/(str(i)+('_QUIET' if quiet else '_AUDIT20')),audit=True,**common)
                    owner=holder['owner'];assert diagnosed['status']=='COMPLETE' and len(owner.records)==len(recorded)==3
                    assert all(torch.equal(a,b) for a,b in zip(ordinary['guided'],diagnosed['guided']))
                    assert torch.equal(ordinary['final_latent'],diagnosed['final_latent'])
                    assert ordinary['actions']==diagnosed['actions'] and ordinary['A_history']==diagnosed['A_history']
                    assert Path(ordinary['video_path']).read_bytes()==Path(diagnosed['video_path']).read_bytes()
                    assert owner.actual_pair_computations==96
                    profile=[]
                    for record in owner.records:
                        trials=record['trials'];assert len(trials)==len(record['serial_restores'])==20
                        assert [(t['kind'],t['repetition'],t['section']) for t in trials]==list(trial_plan())
                        assert sum(t['section']=='WARMUP' for t in trials)==5 and sum(t['section']=='TIMED' for t in trials)==15
                        assert record['all20_trials_restored'] and not record['candidate_or_teacher_committed_to_parent']
                        source=record['parent_pre_action'][1]
                        head_expect={'C':2,'A':4 if source=='D' else 6,'D':2,
                            'Pc':5 if source=='D' else 7,'Pu':5 if source=='D' else 7}
                        linear_expect={'C':0,'A':0,'D':16,'Pc':8,'Pu':8}
                        for t in trials:
                            assert t['compiler_installation_outside_timer'] and t['snapshot_hash_restore_IO_outside_timer']
                            assert t['full_pair_seconds']>0 and t['action_preparation_seconds']>=0
                            assert t['per_action_compiler_preparation_is_charged']
                            assert t['charged_action_seconds']==t['full_pair_seconds']+t['action_preparation_seconds']
                            if quiet:
                                assert t['actual_heads'] is None and t['actual_Linear_observers'] is None
                                assert t['observers']['pure_observers_suspended']==9
                            else:
                                assert t['actual_heads']==head_expect[t['kind']],(source,t)
                                assert t['actual_Linear_observers']==linear_expect[t['kind']],(source,t)
                                assert t['observers']['pure_observers_suspended']==0
                        profile.append({'step':record['point']['step'],'source':source,
                            'all20_actual_head_Linear_counts_verified':not quiet,
                            'quiet_observers_exact9_preserved_algorithm_and_payload':quiet,
                            'trials':trials})
                        source_kinds.add(source);origins+=1;extra_pairs+=20
                    profiles[quiet]=recorded
                    checks.append({'scene':sample.name,'regime':regime,'quiet_observers':quiet,
                        'diagnostic_origins':3,'extra_pairs':60,'actual_pairs_diagnostic_parent':96,
                        'full36_parent_guided_actions_A_history_final_and_mock_video_equal':True,
                        'all_snapshot_restores_accepted':True,'complete_price_profiles':profile,
                        'source_kinds':sorted({r['parent_pre_action'][1] for r in owner.records})})
                assert profiles[False]==profiles[True]
        assert len(checks)==16 and origins==48 and extra_pairs==960 and source_kinds=={'D','P'}
        original.restore();assert original.fingerprint()==initial and net.forward==oldforward
        return [{'flow':flow,'status':'PASS','checks':checks,'complete_CPU_paths':24,'origins':origins,
            'extra_pairs':extra_pairs,'sources_exercised':sorted(source_kinds),'ordinary_initial_state_restored':True,
            'all36_clean_outputs_actions_video_equal':True,'all_audit_quiet_candidate_payloads_equal':True,'Toy_weights_attention_decode_writer':True}]
    finally:original.restore();net.forward=oldforward


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    namespace={**vars(original),'_body':body};exec(compile(changed,__file__+'#fixed-Toy-model-setup','exec'),namespace)
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:namespace['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {r['flow'] for r in result['checks']}=={False,True}
    assert sum(r['origins'] for r in result['checks'])==96 and sum(r['extra_pairs'] for r in result['checks'])==1920
    result.update(status='PA_PROFILE20_FULL48_ORIGINS96_TRIALS1920_AUDIT_QUIET_CPU_PASS_NOT_GPU',
        actual_CPU_paths=48,actual_GPU_or_real_video_claim=False,GPU_submissions=0)
    return result
