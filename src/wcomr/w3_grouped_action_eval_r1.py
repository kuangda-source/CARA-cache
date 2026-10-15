"""Frozen-window/ridge prompt-held-out local CAD evaluation, never deployment.

Data quality cohorts are fixed before fitting. Teacher labels live separately
from FeatureRow values. Loss units are quoted post-probe cost + lambda*g^2*MSE,
not elapsed video runtime or final perceptual quality.
"""
from collections import Counter
from dataclasses import replace
import hashlib,json,math,time
from pathlib import Path
import numpy as np

from .gpu_budget_pool_v2 import BudgetPool
from .p_acr_profile528_contract_r1 import H1_FP
from .source_phase_absolute_h1_control_r1 import validate_parameters
from .w3_causal_trend_r1 import SameStateLabel,RidgeRisk,coherent_scores,Observation,CausalHistory
from .w3_label64_post_r1 import full_matrix,audit_features
from .w3_label64_h1_owner_r1 import STEPS

MODELS=('T0_H1_ORIGINAL','T0_CAD','T1','T2')
COHORTS=('PRIMARY_FULL_PARENT_RGB','SENSITIVITY_RAW_MODEL')
ACTION_ORDER={'C':0,'A':1,'D':2}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def close(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
def choose(scores):return min(scores,key=lambda a:(scores[a],ACTION_ORDER[a]))

def replay_saved_features(rows,clock):
    """Linux production values with local eight-epsilon replay verification.

    Server audit already requires exact replay on its native platform. macOS
    libm/reduction last bits can differ; schemas, causal prefixes and clocks
    remain exact. No local recomputed feature substitutes saved online values.
    """
    from .w3_actual_clock_replay_r1 import validate_clock
    validate_clock(clock)
    assert len(rows)==36 and [r['step'] for r in rows]==list(range(1,37))
    first=Observation(**rows[0]['observation']);h=CausalHistory(first.prompt,first.seed,window=4)
    features=[];maximum=0.;different=0
    for row in rows:
        o=Observation(**row['observation'])
        assert o.step==row['step'] and o.sigma==clock['sigmas'][o.step-1]
        assert row['ordinary_parent_only'] is True and row['teacher_or_candidate_history_used'] is False
        if row['scheduler_pre_step_index'] is None:
            assert o.step==1 and row['sigma_from_actual_first_grid_before_init'] is True
        else:assert row['scheduler_pre_step_index']==o.step-1 and not row['sigma_from_actual_first_grid_before_init']
        fs=h.push(o);saved={}
        for model,f in fs.items():
            actual=row['features'][model]
            assert tuple(actual['names'])==f.names and tuple(actual['prefix_steps'])==f.prefix_steps
            x=np.asarray(actual['values'],float);y=np.asarray(f.values,float)
            assert x.shape==y.shape and np.isfinite(x).all()
            delta=np.abs(x-y);bound=8*np.finfo(np.float64).eps*np.maximum(1.,np.maximum(np.abs(x),np.abs(y)))
            assert np.all(delta<=bound),'Saved prefix exceeds cross-platform floating roundoff'
            maximum=max(maximum,float(delta.max()));different+=bool(delta.max()>0)
            saved[model]=replace(f,values=tuple(float(v) for v in x))
        features.append(saved)
    return features,dict(verified_feature_rows=72,nonbitwise_replay_rows=int(different),max_absolute_difference=maximum,
        tolerance='8*float64_epsilon*max(1,abs(saved),abs(replay))',values_used_for_fit='SAVED_PRODUCTION_CAUSAL_FEATURES')

def accept_dataset(root,original_capture,repair_capture):
    root=Path(root);original=original_capture['capture'];c=repair_capture['capture']
    assert original_capture['transport_exit_code']==repair_capture['transport_exit_code']==0
    assert original['source_revision']=='047dcf181a3ab706002b2965e74b626e4648deea'
    assert c['registration']['source_revision']==c['launch']['source_revision']=='5b7ef102f0aac80842904d750326ad83345fbf7e'
    assert all(c['payload_verified'].values()) and len(c['payload_verified'])==4 and c['original_registration_unchanged']
    e,r=c['exit'],c['result'];assert e['exit_code']==0 and e['result_sha256']==c['result_sha256']
    assert c['process']['state'] in (None,'Z','X') and not e['GPU_submissions'] and not e['ledger_written']
    assert e['source_revision']==c['registration']['source_revision']
    assert r['source_revision']==original['source_revision'] and r['reader_repair']==e['derivation_proof']
    assert e['derivation_proof']['reader_source_revision']==e['source_revision'] and e['derivation_proof']['original_GPU_source_revision']==original['source_revision']
    proof=e['derivation_proof'];assert proof['explicit_sites']==3 and proof['inverse_AST_equal'] and not proof['original_CAD_raw_auditor_changed'] and not proof['original_artifact_hash_checks_changed']
    assert r['status']=='W3_FULL_SCOPE_PARTIAL_REJECTIONS_OR_AUDIT_FAILURES_RETAINED'
    assert not r['CUDA_initialized'] and r['GPU_submissions']==0 and r['budget_before_sha256']==r['budget_after_sha256']
    assert (r['planned_parent_denominator'],r['planned_formal_label_denominator'],r['planned_warmup_label_denominator'])==(18,64,8)
    assert (len(r['parents']),len(r['labels']))==(18,72)
    assert r['audit_failed_parent_ids']==['9_FORMAL_DIAGNOSTIC']
    assert (r['raw_files'],r['raw_tensors'],r['actual_pairs'],r['actual_available_labels'])==(80,1104,768,64)
    assert (r['accepted_videos'],r['scored_control_frames'])==(15,1395)
    assert len(r['video_subprocess_failures_retained'])==1 and r['video_subprocess_failures_retained'][0]['parent_id']=='9_FORMAL_DIAGNOSTIC'
    assert r['video_subprocess_failures_retained'][0]['error_type']=='CalledProcessError'
    records=original['receipts']
    receipt=lambda suffix:next(v for k,v in records.items() if k.endswith(suffix))
    runner=receipt('/runner.json')['data'];sup=receipt('/supervisor.json')['data']
    assert r['GPU_supervisor']==sup and sup['runner_sha256']==receipt('/runner.json')['sha256']
    assert sum(x['actual_pair_computations'] for x in runner['runs'])==768
    requests=[json.loads(s) for s in (root/'configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl').read_text().splitlines()]
    plan=full_matrix(requests);rows=runner['runs'];assert len(rows)==18
    for row,want in zip(rows,plan):assert all(row[k]==want[k] for k in ('id','scene','section','kind'))
    parents={p['id']:p for p in r['parents']};labels={(x['parent_id'],x['step']):x for x in r['labels']}
    assert len(parents)==18 and len(labels)==72
    assert all(p['original_status']==row['status'] for p,row in zip(r['parents'],rows))
    assert sum(p.get('all36_guided_actions_Ahistory_final_equal') is True for p in r['parents'])==8
    assert sum(p.get('all93_RGB_equal_to_resident_baseline') is True for p in r['parents'])==7
    for p in r['parents']:
        if p['audit_status']=='AUDITED':assert p['video']['frames']==93
    binding=json.loads((root/'configs/wc_p_acr_local12_profile528_production_r1_20261015.json').read_text())['references']['H1']
    assert sha(root/binding['ref'])==binding['sha256']
    params=json.loads((root/binding['ref']).read_text());validate_parameters(params);assert params['fingerprint']==H1_FP
    lam=params['lambda_seconds_per_weighted_absolute_MSE']
    clock=json.loads((root/'reports/wc_w3_actual_schedule_native_CPU_replay_20261015.json').read_text())['result']
    data=[];unsupported=[];replay_proofs=[]
    for row in rows:
        if row['kind']!='DIAGNOSTIC':continue
        if row['status']=='TEXT_REJECTED':
            assert all(not labels[(row['id'],s)]['labels_available'] for s in STEPS)
            unsupported.extend([dict(parent_id=row['id'],scene=row['scene'],step=s,status='ORIGINAL_TEXT_REJECTED') for s in STEPS]);continue
        assert row['status']=='COMPLETE' and len(row['diagnostic_points'])==8
        fs,replayed=replay_saved_features(row['feature_rows'],clock);replay_proofs.append(dict(parent_id=row['id'],**replayed))
        for record in row['diagnostic_points']:
            step=record['step'];audit=labels[(row['id'],step)];parent=parents[row['id']]
            assert audit['labels_available'] and audit['all8_point_tensors_read'] and audit['status']=='RAW_CAD_AND_ORDINARY_PREFIX_AUDITED'
            assert record['status']=='COMPLETE_SAME_STATE_CAD_LABEL_NOT_ONLINE_VALUE' and record['extra_pairs']==3
            assert record['same_state_snapshot_and_parent_restore_verified'] and record['teacher_never_used_in_feature_inputs'] and not record['candidate_or_teacher_committed_to_parent']
            feature=fs[step-1]['T1'];obs=feature.observation;label=SameStateLabel(**record['label'])
            assert obs.calibration_supported and not obs.protected and obs.source_age in range(1,7)
            assert obs.state_id==record['feature_state_id']==label.state_id and obs.sigma==record['sigma']
            assert obs.prompt.endswith(':'+row['scene']) and obs.seed==0 and label.provenance=='REAL_SAME_STATE_POST_RF'
            for action,field in (('C','q_C'),('A','q_A')):
                loss=audit['losses'][action];assert close(loss['as_executed_guided_MSE'],getattr(label,field))
                mc,mu,cross=loss['independent_CFG_Gram'];gram=64*mc+49*mu-112*cross
                assert close(gram,loss['independent64_guided_MSE'])
                assert abs(loss['FP32_FP64_delta'])<=loss['MSE_roundoff_difference_bound']+1e-10
            assert audit['losses']['D']['as_executed_guided_MSE']==0
            target=label.target(feature);assert np.allclose(target,audit['gain_squared_targets'],rtol=1e-10,atol=1e-12) and np.allclose(target,record['gain_squared_targets'],rtol=1e-10,atol=1e-12)
            full=parent['audit_status']=='AUDITED' and parent.get('all93_RGB_equal_to_resident_baseline') is True
            primary=bool(row['section']=='FORMAL' and full and parent.get('all36_guided_actions_Ahistory_final_equal') is True)
            sensitivity=bool(row['section']=='FORMAL' and parent.get('all36_guided_actions_Ahistory_final_equal') is True)
            assert audit['primary_grouped_fit_admitted']==primary and audit['sensitivity_raw_model_fit_admitted']==sensitivity
            if row['section']=='WARMUP':continue
            assert sensitivity
            hist=row['source_history'][step-1];table=hist['source_policy']['event_math']['candidate_risk_and_price']
            costs={'C':params['cost_seconds']['C'],'A':params['source_A_cost_seconds'][obs.source_kind],'D':params['cost_seconds']['D']}
            for action in costs:
                t=table[action];assert close(t['price'],costs[action]) and close(t['gain_squared_risk'],obs.gain**2*t['absolute_current_MSE']) and close(t['score'],costs[action]+lam*t['gain_squared_risk'])
            predicted=np.array([table['A']['gain_squared_risk'],table['C']['gain_squared_risk']-table['A']['gain_squared_risk']])
            cad=coherent_scores(predicted,obs,costs=costs,lam=lam)
            assert cad['action']==choose({a:table[a]['score'] for a in costs})
            data.append(dict(id=row['id']+':'+str(step),parent_id=row['id'],group=row['scene'],step=step,
                primary=primary,sensitivity=sensitivity,feature=fs[step-1],label=label,target=target,costs=costs,lam=lam,
                frozen_T0_prediction=predicted,original_H1_action=record['parent_readout'],source_kind=obs.source_kind,
                source_age=obs.source_age,phase='EARLY' if step<25 else 'LATE',RGB_complete=bool(full)))
    assert len(data)==56 and sum(x['primary'] for x in data)==48 and len(unsupported)==8
    assert len({x['group'] for x in data})==7 and len({x['group'] for x in data if x['primary']})==6
    assert r['primary_grouped_fit_label_count']==48 and r['sensitivity_raw_model_fit_label_count']==56 and r['warmup_labels_excluded_from_fit']==8
    totals=BudgetPool.accounting(c['pool']);assert all(c['pool'][k]==v for k,v in totals.items())
    acceptance=dict(status='W3_RAW_SUPERVISION_COHORTS_ACCEPTED_WITH_ORIGINAL_VIDEO_FAILURE_AND_TEXT_REJECTIONS',
        original_parent_denominator=18,formal_position_denominator=64,warmup_position_denominator=8,
        raw_files=80,raw_tensors=1104,actual_pairs=768,audited_teacher_labels=64,formal_labels=56,warmup_excluded=8,
        primary_labels=48,primary_prompt_groups=6,sensitivity_labels=56,sensitivity_prompt_groups=7,
        video_failures=['9_FORMAL_DIAGNOSTIC'],text_rejected_formal_positions=8,all72_success_claim=False,
        whole_original_card_without_failures_accepted=False,new_policy_endpoint_or_speed_claim=False,
        causal_saved_feature_cross_platform_replay=replay_proofs,lambda_frozen=lam,H1_fingerprint=H1_FP,GPU_submissions=0,ledger_written=False,pool_totals=totals)
    return data,acceptance

def fit_fold(data,held_group,model):
    train=[x for x in data if x['group']!=held_group];test=[x for x in data if x['group']==held_group]
    assert train and test and not {x['group'] for x in train}&{x['group'] for x in test}
    forbidden={x['feature'][model].observation.prompt for x in test}
    reg=RidgeRisk(model=model,ridge=1.).fit([(x['feature'][model],x['label']) for x in train],forbidden_prompts=forbidden)
    assert set(reg.training_prompts).isdisjoint(forbidden)
    predictions={x['id']:reg.predict(x['feature'][model]) for x in test}
    return reg,predictions,train,test

def evaluate(data,name):
    rows=[x for x in data if x['primary']] if name==COHORTS[0] else list(data)
    groups=sorted({x['group'] for x in rows});assert len(rows)==8*len(groups)
    folds=[];predictions={}
    for model in ('T1','T2'):
        for held in groups:
            start=time.perf_counter();reg,pred,train,test=fit_fold(rows,held,model)
            predictions[model,held]=pred
            folds.append(dict(model=model,held_group=held,training_groups=sorted({x['group'] for x in train}),
                training_prompts=list(reg.training_prompts),held_observation_prompts=sorted({x['feature'][model].observation.prompt for x in test}),
                training_rows=len(train),held_rows=len(test),feature_names=list(reg.names),mean=reg.mean.tolist(),std=reg.std.tolist(),weights=reg.weights.tolist(),ridge=1.,window=4,
                fit_and_prediction_CPU_seconds=time.perf_counter()-start,held_labels_used_for_fit=False))
    details=[]
    for sample in rows:
        o=sample['feature']['T1'].observation;t=sample['target'];costs=sample['costs'];lam=sample['lam']
        risk={'A':float(t[0]),'C':float(sum(t)),'D':0.}
        truth={a:costs[a]+lam*risk[a] for a in ('C','A','D')};oracle=choose(truth)
        for model in MODELS:
            raw=sample['frozen_T0_prediction'] if model.startswith('T0_') else predictions[model,sample['group']][sample['id']]
            decision=coherent_scores(raw,o,costs=costs,lam=lam);assert decision['category']=='COHERENT_CAD_OPTIMIZER'
            action=sample['original_H1_action'] if model=='T0_H1_ORIGINAL' else decision['action']
            regret=None if action not in truth else max(0.,float(truth[action]-truth[oracle]))
            ca=(decision['scores']['C']<=decision['scores']['A'])!=(truth['C']<=truth['A'])
            ad=(decision['scores']['A']<=decision['scores']['D'])!=(truth['A']<=truth['D'])
            details.append(dict(id=sample['id'],group=sample['group'],model=model,step=sample['step'],source=sample['source_kind'],source_age=sample['source_age'],phase=sample['phase'],
                action=action,original_H1_action=sample['original_H1_action'],oracle=oracle,local_regret=regret,
                undefined_regret_reason='ORIGINAL_P_HAS_NO_SAME_STATE_P_LABEL' if regret is None else None,
                oracle_mistake=None if regret is None else action!=oracle,CA_boundary_misrank=ca,AD_boundary_misrank=ad,
                raw_prediction=raw.tolist(),weighted_targets=t.tolist(),raw_target_MSE=float(np.mean((raw-t)**2)),
                repair=decision['repair'],predicted_scores=decision['scores'],true_scores=truth,
                RGB_complete=sample['RGB_complete'],teacher_used_as_online_feature=False))
    summaries=[]
    for model in MODELS:
        per=[]
        for group in groups:
            rr=[x for x in details if x['model']==model and x['group']==group];valid=[x for x in rr if x['local_regret'] is not None]
            mean=lambda k:float(np.mean([x[k] for x in valid])) if valid else None
            per.append(dict(group=group,total_points=len(rr),scorable_points=len(valid),mean_regret=mean('local_regret'),
                oracle_error_rate=mean('oracle_mistake'),CA_boundary_error_rate=mean('CA_boundary_misrank'),AD_boundary_error_rate=mean('AD_boundary_misrank'),
                raw_target_MSE=mean('raw_target_MSE'),repair_rate=mean('repair'),action_counts=dict(Counter(x['action'] for x in rr)),oracle_counts=dict(Counter(x['oracle'] for x in rr))))
        avg=lambda k:float(np.mean([x[k] for x in per])) if all(x[k] is not None for x in per) else None
        summaries.append(dict(model=model,per_prompt=per,prompt_equal_mean_regret=avg('mean_regret'),prompt_equal_oracle_error_rate=avg('oracle_error_rate'),
            prompt_equal_CA_boundary_error_rate=avg('CA_boundary_error_rate'),prompt_equal_AD_boundary_error_rate=avg('AD_boundary_error_rate'),
            prompt_equal_target_MSE=avg('raw_target_MSE'),prompt_equal_repair_rate=avg('repair_rate'),
            action_counts=dict(Counter(x['action'] for x in details if x['model']==model)),undefined_regret_points=sum(x['local_regret'] is None for x in details if x['model']==model)))
    base=next(x for x in summaries if x['model']=='T0_CAD')
    for summary in summaries:
        b,x=base['prompt_equal_mean_regret'],summary['prompt_equal_mean_regret']
        summary['regret_change_percent_vs_T0_CAD']=100*(x/b-1) if b is not None and b>0 and x is not None else None
        compare=[(next(y for y in details if y['model']=='T0_CAD' and y['id']==r['id']),r) for r in details if r['model']==summary['model']]
        summary['actions_changed_vs_T0_CAD']=sum(a['action']!=b['action'] for a,b in compare)
        summary['prompt_regret_wins_vs_T0_CAD']=sum(x['mean_regret']<y['mean_regret'] for x,y in zip(summary['per_prompt'],base['per_prompt']) if x['mean_regret'] is not None and y['mean_regret'] is not None)
    return dict(cohort=name,groups=groups,prompt_groups=len(groups),points=len(rows),ridge=1.,window=4,
        group_split='LEAVE_ONE_WHOLE_PROMPT_OUT_NO_WARMUP',standardization='TRAIN_PROMPTS_ONLY',models=summaries,
        original_H1_to_CAD_bridge_changed_points=sum(x['actions_changed_vs_T0_CAD'] for x in summaries if x['model']=='T0_H1_ORIGINAL'),
        oracle_action_counts=dict(Counter(x['oracle'] for x in details if x['model']=='T0_CAD')),
        folds=folds,point_predictions=details,independent_final_test=False,
        metric_unit='POST_PROBE_QUOTED_SECONDS_PLUS_FIXED_LAMBDA_WEIGHTED_LOCAL_MSE_NOT_RUNTIME',
        policy_closed_loop_or_video_quality_claim=False,GPU_submissions=0)
