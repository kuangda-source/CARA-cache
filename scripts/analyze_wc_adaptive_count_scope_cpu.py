#!/usr/bin/env python3
"""Existing adaptive C/D action outcomes; diagnostic wall is not deployed speed."""
import gzip
import hashlib
import json
from pathlib import Path
import statistics

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'manifests/wc_next_batch_cpu_analysis_r1_20261006.json').read_text())
for name,digest in manifest['input_sha256'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name

def counts(events):
    return [sum(e['actual_action']=='D' and e['cfg_slot']==slot for e in events) for slot in [0,1]]

rows=[]
for runner_name,score_name in [('wc_w3_small_cd_runner_20261005.json.gz','wc_w3_small_cd_failed_card_lpips_cpu_20261005.json'),
                               ('wc_w3_small_human_runner_20261005.json.gz','wc_w3_small_human_lpips_cpu_20261005.json')]:
    raw=gzip.decompress((root/'reports'/runner_name).read_bytes());runner=json.loads(raw)
    score=json.loads((root/'reports'/score_name).read_text())
    for parent in runner['requests']:
        children=parent.get('children',[])
        if len(children)!=6:continue # Original A incomplete Human remains excluded, not zero or replaced.
        target=parent['target_call'];by={c['label']:c for c in children};arms={}
        for action in ['C','D']:
            first,second=[by[action+'_'+repeat] for repeat in ['first','second']]
            assert first['deep']==second['deep'] and first['outputs']==second['outputs']
            report=first['record']['action_report'];events=report['suffix_events']
            assert report['remaining_policy']=='ORIGINAL_WC_ADAPTIVE'
            assert report['same_remaining_policy_function_not_same_future_action_mask'] is True
            assert [e['call'] for e in events]==list(range(45,73))
            assert all(e['cfg_slot']==(e['call']-1)%2 and e['current_deep_truth_used'] is False for e in events)
            assert [26 if e['actual_action']=='D' else 0 for e in events]==first['deep']
            at=[e for e in events if e['call']==target];assert len(at)==1 and at[0]['actual_action']==action
            walls=[by[action+'_'+repeat]['record']['control_wall_seconds'] for repeat in ['first','second']]
            assert all(w>0 for w in walls)
            decoded=next(v for v in parent['decoded_children'] if v['label']==action+'_first')
            arms[action]={'full_calls_by_CFG':counts(events),'before_target_full_by_CFG':counts([e for e in events if e['call']<target]),
                'target_full_by_CFG':counts(at),'after_target_full_by_CFG':counts([e for e in events if e['call']>target]),
                'full_call_ids':[e['call'] for e in events if e['actual_action']=='D'],
                'paid_probe_count':sum(e['paid_probe'] for e in events),'control_wall_seconds':walls,
                'control_wall_median_seconds':statistics.median(walls),
                'single_encoded_tail_seconds':decoded['decode_guardrail_encode_wall_seconds'],
                'one_observed_control_plus_tail_seconds':walls[0]+decoded['decode_guardrail_encode_wall_seconds'],
                'next_full_call_same_CFG_after_target':next(e['call'] for e in events if e['call']>target and e['cfg_slot']==(target-1)%2 and e['actual_action']=='D')}
        a,b=by['C_first']['record']['action_report']['suffix_events'],by['D_first']['record']['action_report']['suffix_events']
        assert arms['C']['before_target_full_by_CFG']==arms['D']['before_target_full_by_CFG']
        lpips={p['action']:p['score']['mean_LPIPS'] for p in score['pairs']}
        rows.append({'scene':parent['sample_name'],'target_call':target,'target_CFG':(target-1)%2,
            'call_window_inclusive':[45,72],'full_count_includes_target_call':True,'arms':arms,
            'changed_future_actions':[{'call':x['call'],'C':x['actual_action'],'D':y['actual_action']} for x,y in zip(a,b) if x['call']>target and x['actual_action']!=y['actual_action']],
            'Y_quality_C_minus_D':lpips['C']-lpips['D'],
            'Y_control_wall_median_C_minus_D_seconds':arms['C']['control_wall_median_seconds']-arms['D']['control_wall_median_seconds'],
            'Y_single_control_plus_encoded_tail_C_minus_D_seconds':arms['C']['one_observed_control_plus_tail_seconds']-arms['D']['one_observed_control_plus_tail_seconds'],
            'future_full_reduction_C_minus_D':sum(arms['C']['after_target_full_by_CFG'])-sum(arms['D']['after_target_full_by_CFG']),
            'window_net_full_reduction_C_minus_D':sum(arms['C']['full_calls_by_CFG'])-sum(arms['D']['full_calls_by_CFG']),
            'original_complete_runner_sha256':hashlib.sha256(raw).hexdigest(),
            'time_scope':'Restored suffix control with hash/state/recording costs; one tail observed per arm. Not clean deployment or a confidence interval.',
            'quantitative_probe_drift_and_separate_routing_sync_memory_seconds':'UNKNOWN',
            'fixed_quota_result':False,'formal_training_label_or_online_policy':False})
assert len(rows)==2
result={'identity':'WC_ADAPTIVE_COUNT_SCOPE_EXISTING_CPU_R1_20261006','status':'ADAPTIVE_COUNT_BOUNDARY_AND_DIAGNOSTIC_COST_COMPLETE',
        'rows':rows,'future_counts_are_post_action_outcomes':True,'B_is_only_acceptance_gate_for_adaptive_route':False,
        'original_A_timeout_and_denominator_preserved':True,'old_scores_modified':False,'new_GPU_seconds':0,
        'input_manifest_sha256':hashlib.sha256((root/'manifests/wc_next_batch_cpu_analysis_r1_20261006.json').read_bytes()).hexdigest(),
        'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
out=root/'reports/wc_adaptive_count_scope_cpu_r1_20261006.json';assert not out.exists()
out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':result['status'],'readouts':[{k:r[k] for k in ['scene','target_call','future_full_reduction_C_minus_D','window_net_full_reduction_C_minus_D','Y_control_wall_median_C_minus_D_seconds']} for r in rows]}))
