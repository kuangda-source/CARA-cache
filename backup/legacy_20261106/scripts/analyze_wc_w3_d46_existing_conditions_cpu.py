#!/usr/bin/env python3
"""Describe frozen D46 records without another generation or score run."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import time


def read(path):
    raw=Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quantile(values,p):
    values=sorted(values);rank=p*(len(values)-1);lo=math.floor(rank);hi=math.ceil(rank)
    return values[lo]+(values[hi]-values[lo])*(rank-lo)


def describe(seed,row,base,refresh,left,right):
    assert len(left['frame_distances'])==len(right['frame_distances'])==93 and left['pts']==right['pts']
    be=base['record']['action_report']['suffix_events'];re=refresh['record']['action_report']['suffix_events']
    assert [e['call'] for e in be]==[e['call'] for e in re]==list(range(45,73))
    current=be[1];history=be[0]['true_full_history'];assert current['call']==46 and current['cfg_slot']==1
    assert history[1] and current['paid_probe'] and not current['current_deep_truth_used']
    prefix=[sum(d==26 for d in row['deep'][:44][slot::2]) for slot in (0,1)]
    features={'solver_step':current['solver_step'],'CFG_slot':1,'own_history_before_call46':history,
        'last_own_full_step':history[1][-1],'own_age_before_call46':current['solver_step']-history[1][-1],
        'prefix_full_CFG':prefix,'paid_probe':current['paid_probe'],'native_suggested_C':current['native_skip'],
        'numeric_probe_drift':'NOT_RECORDED_IN_THESE_RECEIPTS'}
    transitions=[]
    for a,b in zip(be[2:],re[2:]):
        if a['actual_action']!=b['actual_action']:
            transitions.append({'call':a['call'],'CFG_slot':a['cfg_slot'],'BASE':a['actual_action'],'REFRESH':b['actual_action']})
    future_saved=sum(x['actual_action']=='D' for x in be[2:])-sum(x['actual_action']=='D' for x in re[2:])
    current_added=int(re[1]['actual_action']=='D')-int(be[1]['actual_action']=='D')
    differences=[a-b for a,b in zip(left['frame_distances'],right['frame_distances'])]
    full_mean=math.fsum(differences)/93
    assert math.isclose(full_mean,left['mean_LPIPS']-right['mean_LPIPS'],abs_tol=1e-12)
    segments=[]
    for lo,hi in [(1,31),(32,62),(63,93)]:
        values=differences[lo-1:hi]
        segments.append({'frames_1_based':[lo,hi],'signed_mean':math.fsum(values)/31,
            'improved':sum(x>0 for x in values),'worse':sum(x<0 for x in values),'tied':sum(x==0 for x in values)})
    return {'seed':seed,'pre_action_features':features,'future_action_changes':transitions,
        'post_action_cost_outcome':{'current_full_added':current_added,'strict_future_full_saved':future_saved,
            'whole_full_saved':future_saved-current_added},'signed_quality':full_mean,'frame_segments':segments,
        'frame_signed_quantiles':{str(p):quantile(differences,p) for p in (.1,.5,.9)},
        'calls_with_different_actual_actions':[a['call'] for a,b in zip(be,re) if a['actual_action']!=b['actual_action']],
        'future_changes_are_not_pre_action_features':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preregistration',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists();p=read(args.preregistration)
    for name,h in p['input_sha256'].items():assert sha(name)==h,name
    assert sha(p['plan'])==p['plan_sha256'] and p['GPUh']==0 and p['registration_after_main_D46_results_exposed']
    old=read('reports/wc_w3_small_human_runner_20261005.json.gz')
    oldscore=read('reports/wc_w3_small_human_lpips_cpu_20261005.json')
    originals=read('reports/wc_w3_small_human_original_receipts_20261005.json')
    raw=gzip.decompress(Path('reports/wc_w3_small_human_runner_20261005.json.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest()==originals['files']['runner']['original_sha256']==oldscore['runner_receipt_sha256']
    new=read('reports/wc_w3_d46_r3_complete_20261008_runner_json_native.gz')
    score=read('reports/wc_w3_d46_r3_complete_20261008_CPU_score_json_native.gz')
    assert [x['seed'] for x in new['cases']]==[x['seed'] for x in score['cases']]==[1,2]
    assert old['reference_contexts'][0][1]==new['model_context']
    for key,value in score['metric_protocol'].items():assert oldscore['protocol'][key]==value,key
    orow=old['requests'][0];oc={x['label']:x for x in orow['children']};op={x['action']:x['score'] for x in oldscore['pairs']}
    assert set(op)=={'C','D'}
    for key in ('inputs','outputs','deep','banks','solver_outputs','final_latent_sha256'):
        assert oc['OFF1'][key]==oc['C_first'][key],key
    cases=[describe(0,orow,oc['C_first'],oc['D_first'],op['C'],op['D'])]
    for case,measurement in zip(new['cases'],score['cases']):
        row=case['WC']['requests'][0];cs={x['label']:x for x in row['children']}
        cases.append(describe(case['seed'],row,cs['BASE_first'],cs['REFRESH_first'],measurement['losses']['BASE'],measurement['losses']['REFRESH']))
    a,b=cases[0]['pre_action_features'],cases[2]['pre_action_features']
    keys=['solver_step','CFG_slot','own_history_before_call46','last_own_full_step','own_age_before_call46','prefix_full_CFG','paid_probe','native_suggested_C']
    result={'status':'EXPOSED_D46_EXISTING_CONDITIONS_CPU_COMPLETE_NOT_PREDICTIVE_RULE_OR_CONF',
        'registered_card':p['card'],'preregistration_sha256':sha(args.preregistration),'script_sha256':sha(__file__),
        'completed_unix':time.time(),'input_sha256':p['input_sha256'],'cases':cases,
        'seed0_vs_seed2_pre_action_equality':{k:a[k]==b[k] for k in keys},
        'same_model_context_fingerprint':True,'same_reported_metric_protocol':True,
        'old_forced_C_equals_native_OFF_actual_traces':True,
        'numeric_probe_drift_available':False,'full_new_runtime_WC_settings_comparison':'NOT_RECORDED_AT_NEW_ROOT; do not infer full equality solely from context fingerprint',
        'GPU_submissions':0,'metric_reruns':0,'gate_fitting':False,'independent_CONF':False,
        'boundary':'Three exposed seeds of one prompt. Future actions are outcomes. Missing numeric shallow/probe features are not inferred from hashes.'}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'pre_action_equality':result['seed0_vs_seed2_pre_action_equality'],'cases':[{'seed':x['seed'],'features':x['pre_action_features'],'future_changes':x['future_action_changes'],'segments':x['frame_segments']} for x in cases]}))


if __name__=='__main__':main()
