"""Full72 CPU parent paths / 288 origins / 864 CAD trials, both flows and sources.

Uses pinned WC/RF/UniPC/inference with declared Toy weights/attention/decode.
Real eight development request names are retained; no real teachers or video.
"""
import copy
import inspect
import json
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
from wcomr.w3_label64_h1_owner_r1 import install_w3_labels,STEPS
from wcomr.mid_coverage import tree_digest

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    requests=[json.loads(l) for l in (ROOT/'configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl').read_text().splitlines()]
    samples=[]
    for r in requests:
        s=type(selected[0])(r['name']);s.prompt=r['prompt'];s.seed=r['seed'];samples.append(s)
    assert len(samples)==8 and all(s.num_steps==35 and s.seed==0 for s in samples)
    model=inference.pipe.model;net=model.net;sch=model.sample_scheduler
    cal=Calibration('SYNTHETIC_W3_H1_AGE6',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},
        {n:1. for n in range(1,37)})
    original=CompleteStateRoundtrip(net,sch,torch.zeros(1));oldforward=net.forward;initial=original.fingerprint()
    checks=[];origins=extra_pairs=ordinary_pairs=0;source_kinds=set()
    old={'fingerprint':'SYNTHETIC_W3_OLD_MATH','gamma':.5}
    try:
        for regime in ('P_WORKING_SOURCES','D_WORKING_SOURCES'):
            spec={'threshold':2.,'costs':Costs('SYNTHETIC_W3',1.,4.,3.5),
                'partial_prior':CreationPhasePrior('SYNTHETIC_W3',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
                'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
            cells={key:{'status':'FIT','C_scale':1e9,'A_ratios':{'FUSION_A':.02},
                'actual_NEW_P_birth_mean':.0001 if regime=='P_WORKING_SOURCES' else 1e6}
                for key in ('D_EARLY','D_LATE','P_EARLY','P_LATE')}
            table={'version':VERSION,'gamma':.5,'table_model':{'grouping':'SOURCE_PHASE','target':'absolute_guided_MSE',
                'current_teacher_energy_is_online_feature':False,'cells':cells},
                'cost_seconds':{'C':1.,'A':1.3,'P':3.5,'D':4.},'source_A_cost_seconds':{'D':1.1,'P':1.3},
                'lambda_seconds_per_weighted_absolute_MSE':100.}
            table['fingerprint']=fingerprint(table)
            common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,
                specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec},inference_module=inference_module,
                expected_shape=config['expected_shape'],table_parameters={'SOURCE_PHASE':table},previous_parameters=old)
            # Full production matrix: one complete baseline/diagnostic warm pair
            # plus all eight distinct development baseline/diagnostic pairs.
            for i,sample in enumerate([samples[0]]+samples):
                section='WARMUP' if i==0 else 'FORMAL'
                root=Path(artifact_root)/str(flow)/regime/(str(i)+'_'+section)
                original.restore()
                ordinary,_=batch.execute(inference,sample,'TABLE_PHASE_H1',output=root/'BASE',audit=True,**common)
                assert ordinary['status']=='COMPLETE' and len(ordinary['guided'])==36
                recorded=[];holder={}
                def writer(step,payload):
                    assert set(payload)=={'C','A','D','actual_latent','timestep'}
                    assert sum(len(v) if isinstance(v,tuple) else 1 for v in payload.values())==8
                    recorded.append({'step':step,'payload':payload,'sha256':tree_digest(payload)})
                    return {'CPU_only_in_memory':True,'tensor_sha256':tree_digest(payload),'not_actual_GPU_artifact':True}
                original.restore()
                with install_w3_labels(clean,batch,sch,config=config,writer=writer,holder=holder,label_provenance='SYNTHETIC_CPU_INTERFACE'):
                    diagnosed,_=batch.execute(inference,sample,'TABLE_PHASE_H1',output=root/'DIAG',audit=True,**common)
                owner=holder['owner']
                assert diagnosed['status']=='COMPLETE' and len(owner.feature_rows)==36
                assert [r['step'] for r in owner.records]==list(STEPS)
                assert all(r['status']=='COMPLETE_SAME_STATE_CAD_LABEL_NOT_ONLINE_VALUE' for r in owner.records),owner.records
                assert len(recorded)==8 and owner.actual_pair_computations==60
                assert all(torch.equal(a,b) for a,b in zip(ordinary['guided'],diagnosed['guided']))
                assert torch.equal(ordinary['final_latent'],diagnosed['final_latent'])
                assert ordinary['actions']==diagnosed['actions'] and ordinary['A_history']==diagnosed['A_history']
                assert Path(ordinary['video_path']).read_bytes()==Path(diagnosed['video_path']).read_bytes()
                for record in owner.records:
                    assert len(record['trials'])==len(record['serial_restores'])==3
                    assert [r['kind'] for r in record['trials']]==['C','A','D']
                    assert record['extra_pairs']==3 and not record['candidate_or_teacher_committed_to_parent']
                    assert record['same_state_snapshot_and_parent_restore_verified']
                    assert record['label']['provenance']=='SYNTHETIC_CPU_INTERFACE'
                    feature=owner.feature_rows[record['step']-1]
                    gain=feature['observation']['gain'];q=record['label']
                    assert record['gain_squared_targets']==[gain*gain*q['q_A'],gain*gain*(q['q_C']-q['q_A'])]
                    source_kinds.add(record['pre_action_state'][1]);origins+=1;extra_pairs+=3
                assert len(owner.causal.rows)==36  # Extra trials never push history.
                for f in owner.feature_rows:
                    assert f['ordinary_parent_only'] and not f['teacher_or_candidate_history_used']
                    assert all(s<=f['step'] for s in f['features']['T2']['prefix_steps'])
                    assert len(f['features']['T1']['values'])==13 and len(f['features']['T2']['values'])==27
                ordinary_pairs+=72
                checks.append({'scene':sample.name,'section':section,'source_regime':regime,'origins':8,
                    'all36_guided_actions_Ahistory_final_mock_video_equal':True,'ordinary_history_rows':36,
                    'all24_diagnostic_pairs_serially_restored':True,'source_kinds':sorted({r['pre_action_state'][1] for r in owner.records})})
                print('W3_FULL_CPU_PARENT_ACCEPTED',{'flow':flow,'regime':regime,'section':section,'scene':sample.name},flush=True)
        assert len(checks)==18 and origins==144 and extra_pairs==432 and ordinary_pairs==1296 and source_kinds=={'D','P'}
        original.restore();assert original.fingerprint()==initial and net.forward==oldforward
        return [{'flow':flow,'status':'PASS','checks':checks,'complete_CPU_paths':36,'origins':origins,
            'extra_pairs':extra_pairs,'ordinary_pairs':ordinary_pairs,'total_pairs':ordinary_pairs+extra_pairs,
            'sources_exercised':sorted(source_kinds),'all36_original_parent_equal':True,
            'ordinary_initial_state_restored':True,'all36_clean_outputs_actions_video_equal':True,
            'Toy_weights_attention_decode_writer':True,'real_teacher_labels':0}]
    finally:original.restore();net.forward=oldforward


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    namespace={**vars(original),'_body':body};exec(compile(changed,__file__+'#unchanged-Toy-model-setup','exec'),namespace)
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:namespace['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {r['flow'] for r in result['checks']}=={False,True}
    assert sum(r['complete_CPU_paths'] for r in result['checks'])==72
    assert sum(r['origins'] for r in result['checks'])==288 and sum(r['extra_pairs'] for r in result['checks'])==864
    result.update(status='W3_FULL_H1_72_CPU_PATHS288_ORIGINS864_CAD_TRIALS_NONCOMMITTING_CPU_PASS_NOT_GPU',
        actual_CPU_paths=72,actual_CPU_total_pairs=3456,actual_GPU_or_real_video_claim=False,GPU_submissions=0)
    return result
