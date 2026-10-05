#!/usr/bin/env python3
"""Existing sparse timing and provenance conditions; no weights, kernel or Torch."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def timed_median(case):
    hot=case['wall_ms']
    if (len(hot)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in hot)
            or not math.isclose(statistics.median(hot),case['median_wall_ms'],abs_tol=1e-12)):
        raise ValueError('Preserve three actual hot samples and their median')
    return case['median_wall_ms']


def opportunity_scenarios(sparse_calls, full_calls, local_group_saving, assumptions):
    if (type(sparse_calls) is not int or type(full_calls) is not int or not 0<=sparse_calls<=full_calls
            or full_calls<=0 or not math.isfinite(local_group_saving) or not 0<local_group_saving<1
            or assumptions!=[0,.25,.5,.75,1]):
        raise ValueError('Explicit conditional opportunity inputs required')
    r=sparse_calls/full_calls
    return [{'assumed_all_full_group_share_of_pipeline':p,
             'conditional_pipeline_time_reduction_fraction':r*p*local_group_saving,
             'measured_prediction_bound_or_causal_fit':False} for p in assumptions]


def pipeline_observation(baseline, variant):
    if (baseline['CFG_calls']!=72 or variant['CFG_calls']!=72
            or len(baseline['trace'])!=72 or len(variant['trace'])!=72
            or [r['deep_executed'] for r in baseline['trace']]!=[r['deep_executed'] for r in variant['trace']]
            or baseline['block_counts']!=variant['block_counts']
            or baseline['substage_cuda_isolated'] is not False or variant['substage_cuda_isolated'] is not False):
        raise ValueError('Same full/cache actions and existing host timing scope required')
    named=[]
    for name in ['prepare','sample','decode','video_guardrail','write']:
        a,b=baseline['substage_host_wall'][name],variant['substage_host_wall'][name]
        if (a['calls']!=1 or b['calls']!=1 or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in (a['seconds'],b['seconds']))):
            raise ValueError('Single logged host interval required')
        named.append({'stage':name,'WC_seconds':a['seconds'],'sparse_seconds':b['seconds'],
                      'WC_minus_sparse_seconds':a['seconds']-b['seconds']})
    a,b=baseline['pipeline_wall_seconds'],variant['pipeline_wall_seconds']
    if any(not math.isfinite(t) or t<=0 for t in (a,b)):
        raise ValueError('Actual pipeline wall required')
    return {'WC_pipeline_seconds':a,'sparse_pipeline_seconds':b,'WC_minus_sparse_pipeline_seconds':a-b,
        'pipeline_time_reduction_fraction':1-b/a,'host_substages':named,
        'WC_outside_logged_substages_seconds':a-sum(r['WC_seconds'] for r in named),
        'sparse_outside_logged_substages_seconds':b-sum(r['sparse_seconds'] for r in named),
        'host_brackets_are_CUDA_components':False,'single_fixed_order_no_speed_confidence_interval':True}


def analyze(root, manifest):
    read=lambda n:json.loads((root/n).read_text())
    for name,digest in manifest['input_sha256'].items():
        if sha(root/name)!=digest:raise ValueError('Registered sparse-cost input changed: '+name)
    registration=read('manifests/wc_exploratory_hypotheses_r1_20261005.json')
    hypothesis=next(h for h in registration['hypotheses'] if h['id']==manifest['hypothesis_id'])
    if (hypothesis['estimated_new_GPU_seconds']!=0 or manifest['new_GPU_seconds']!=0
            or manifest['scenarios']['scenario_is_measured_bound_or_fit'] is not False
            or manifest['old_operator_criteria']!={'relative_RMSE_max':.05,'speedup_min':1.1}):
        raise ValueError('Preserve exploratory, CPU-only scope and old criteria')
    raw=read('reports/wc_mid_full_r4_runner_20261003.json');old=read('reports/wc_mid_full_r4_summary_20261003.json')
    if len(raw['snapshots'])!=104 or len(raw['cases'])!=312:
        raise ValueError('All104/312 valid original operator cases required')
    by={(r['call'],r['layer'],r['arm']):r for r in raw['cases']}
    if len(by)!=312:raise ValueError('Repeated sparse operator identity')
    ratios=[];numerics=0;speed=0;both=0
    for call in (25,26,35,36):
        for layer in range(2,28):
            dense,matched,sparse=[by[call,layer,arm] for arm in ('dense','matched_full','sparse')]
            for case in (dense,matched,sparse):
                if case['finite'] is not True:raise ValueError('Original finite operator evidence required')
                timed_median(case)
            ratio=timed_median(dense)/timed_median(sparse);ratios.append(ratio)
            n=sparse['rmse_vs_dense']<=.05;s=ratio>=1.1
            numerics+=n;speed+=s;both+=n and s
    median=statistics.median(ratios)
    if ((numerics,speed,both)!=(92,76,64) or (numerics,speed,both)!=(old['numerics_pass'],old['speed_pass'],old['both_pass'])
            or not math.isclose(median,old['median_dense_over_sparse'],abs_tol=1e-12)):
        raise ValueError('Original operator timing/criteria recompute differs')
    h0=read('reports/wc_h0_eval_complement_r2_runner_20261003.json')
    if len(h0['h0_records'])!=2:raise ValueError('Both H0 original same-state observations required')
    group=[]
    for record in h0['h0_records']:
        arms={a['arm']:a for a in record['arms']};d,f,s=[timed_median(arms[a]) for a in ('dense','matched_full','sparse')]
        group.append({'call':record['call'],'CFG_slot':record['cfg_slot'],
            'dense_group_plus_head_ms':d,'matched_full_group_plus_head_ms':f,'sparse_group_plus_head_ms':s,
            'D_over_S':d/s,'one_minus_S_over_D':1-s/d,'matched_full_over_D_minus1':f/d-1,
            'matched_full_net_difference_is_isolated_router_cost':False,
            'same_deep_group_timing_not_pipeline':True})
    local_saving=statistics.mean(r['one_minus_S_over_D'] for r in group)
    fair=json.loads(gzip.decompress((root/'reports/wc_fair_cal_r1_runner_20261004.json.gz').read_bytes()))
    metric=read('reports/wc_existing_fair_w1_lpips_cpu_r1_20261004.json')['result']
    conditions=[]
    for request in fair['measurements']['requests']:
        base=next(p for p in request['phases'] if p['workpoint']['name']=='wc006')
        stage=next(p for p in request['phases'] if p['workpoint']['name']=='stage_every1')
        observation=pipeline_observation(base,stage);events=stage['refresh_provenance']['events']
        sparse=[e for e in events if e['action']=='sparse'];full=base['block_counts']['full_calls']
        if len(events)!=72 or full!=sum(e['deep_executed'] for e in base['trace']):
            raise ValueError('Full72 calls and original full counts required')
        allowed=fair['stage_policy']['sparse_layers'];fractions=[]
        for event in sparse:
            if (event['official_skipped'] or event['sparse_layers']!=allowed
                    or [o['layer'] for o in event['operator_metadata']]!=allowed):
                raise ValueError('Actual full calls/all23 sparse layer substitutions required')
            fractions.extend(o['executed_fraction'] for o in event['operator_metadata'])
        if any(type(f) not in (int,float) or not math.isfinite(f) or not 0<f<=1 for f in fractions):
            raise ValueError('Actual recorded block-map execution fractions required')
        name=request['sample_name'];lpips={p['variant']:p for p in metric['pairs'] if p['sample']==name}
        for variant,phase in [('wc006',base),('stage_every1',stage)]:
            if (lpips[variant]['candidate']['sha256']!=phase['artifacts'][0]['sha256']
                    or lpips[variant]['score']['frames']!=93):
                raise ValueError('Native LPIPS/source video binding differs')
        conditions.append({'scene':name,**observation,'official_full_calls':full,'sparse_full_calls':len(sparse),
            'sparse_call_ids':[e['call'] for e in sparse],'full_call_count_share':len(sparse)/full,
            'substituted_attention_operators':len(fractions),'possible_deep_attention_operators':full*26,
            'attention_operator_count_share':len(fractions)/(full*26),'count_share_is_measured_time_share':False,
            'recorded_executed_block_fraction':{'min':min(fractions),'mean':statistics.mean(fractions),'max':max(fractions)},
            'executed_block_fraction_is_FLOP_or_speed_ratio':False,
            'Native_LPIPS_WC006':lpips['wc006']['score']['mean_LPIPS'],
            'Native_LPIPS_sparse':lpips['stage_every1']['score']['mean_LPIPS'],
            'conditional_opportunity_scenarios':opportunity_scenarios(len(sparse),full,local_saving,
                manifest['scenarios']['all_full_group_share_of_pipeline']),
            'measured_time_weighted_replaceable_share':'UNKNOWN',
            'separately_timed_routing_quantization_selection_sync_memory_cache':'UNKNOWN'})
    return {'status':'EXPLORATORY_SPARSE_COST_CONDITIONS_FROM_EXISTING_VALID_TIMING_COMPLETE',
        'hypothesis_id':manifest['hypothesis_id'],'operator':{'inputs':104,'cases':312,'median_D_over_S':median,
            'numerics_pass':numerics,'speed_pass':speed,'both_pass':both,'new_criteria':False},
        'same_state_group_observations':group,'group_saving_reference_mean':local_saving,
        'FAIR_conditions':conditions,'FAIR_model_load_seconds':fair['load_seconds'],
        'FAIR_load_is_in_each_video_pipeline_wall':False,
        'unmeasured_remaining_scope':'Outside logged host brackets is a timing residual, not an identified component or CUDA profile.',
        'source_observed_auxiliary_operations':['full block mask allocation','fused selection/quantization',
            'block-map validity/selected fraction scalar host reads','output finite reduction/host decision','cache/provenance updates'],
        'auxiliary_operation_seconds_or_causal_slowdown':'UNKNOWN',
        'scenario_transfers_local_H0_group_cost_to_FAIR_calls':'UNMEASURED_ASSUMPTION_NOT_BOUND_OR_FIT',
        'current_sparse_configuration_end_to_end_advantage':'NOT_ESTABLISHED',
        'entire_sparse_direction_disproved':False,'old_results_or_criteria_changed':False,
        'input_sha256':manifest['input_sha256'],'new_GPU_seconds':0,'kernel_or_layer_search':False,
        'budget_sha256_before':manifest['input_sha256']['reports/budget.json']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ['root','manifest','output']:parser.add_argument('--'+n,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve original analysis identity')
    start=time.perf_counter();result=analyze(args.root,json.loads(args.manifest.read_text()))
    result.update(analysis_code_sha256=sha(__file__),execution_manifest_sha256=sha(args.manifest),
                  CPU_wall_seconds=time.perf_counter()-start)
    if sha(args.root/'reports/budget.json')!=result['budget_sha256_before']:raise ValueError('CPU analysis changed budget')
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'FAIR_scenes':len(result['FAIR_conditions']),'new_GPU_seconds':0}))
