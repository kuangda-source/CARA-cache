#!/usr/bin/env python3
"""Compare complete audited R1/R2 controls and working points; local stdlib only.

Use both independent raw and full93 score acceptances, never a live subset.
Vector equality here is equality of fully reloaded, audited tensor digests.
This program does not perform another tensor load, generation or metric run.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time


def load_original(proof, key):
    item=proof['files'][key];raw=gzip.decompress(Path(item['local_path']).read_bytes())
    if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError('Preserved complete native bytes differ: '+key)
    return json.loads(raw)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('reports/wc_ra_r1_r2_complete_working_point_and_control_comparison_20261010.json'));a=p.parse_args()
    assert not a.output.exists()
    runs=[];bindings={}
    for version in ('r1','r2'):
        raw_path=Path('reports/wc_ra_comparison_'+version+'_terminal_20261010_capture_and_independent_audit.json')
        score_path=Path('reports/wc_ra_comparison_score_cpu_'+version+'_terminal_20261010_capture_and_independent_audit.json')
        raw,score=(json.loads(p.read_text()) for p in (raw_path,score_path))
        if not raw['independent_checks']['success'] or not score['independent_checks']['success']:
            raise ValueError('Both complete original raw and all93 acceptances required')
        runner,audit,result=(load_original(proof,key) for proof,key in [(raw,'runner'),(raw,'CPU_result'),(score,'result')])
        if result['original_raw_audit_sha256']!=raw['files']['CPU_result']['sha256'] or result['original_runner_receipt_sha256']!=raw['files']['runner']['sha256']:
            raise ValueError('Score must refer to the same complete raw execution')
        if runner['comparison']['planned_paths']!=8 or len(runner['comparison']['references'])!=2 or result['maximum_pairs']!=6:
            raise ValueError('Do not replace the full eight-path denominator')
        bindings.update({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (raw_path,score_path)})
        runs.append((runner,audit,result,raw))
    old,new=(r[0] for r in runs);c0,c1=(r['config'] for r in (old,new))
    fields=['project_input_sha256','runtime_source_sha256','historical_wc_settings','sampling_protocol','expected_real_components','expected_real_shape']
    config_checks={k:c0[k]==c1[k] for k in fields}
    for k in ('scope_counts','requests','methods','repetitions','branch_order','guided_weights','state_steps','timesteps','calibration_fingerprint','reference_policy'):
        config_checks['registered_'+k]=c0['preregistration'][k]==c1['preregistration'][k]
    assert c0['preregistration']['RA_threshold']==.141488470197544 and c1['preregistration']['RA_threshold']==.070744235098772
    assert c1['preregistration']['threshold_scale']==.5 and c1['preregistration']['quality_informed_development_refinement']
    controls=[]
    for i,(before,after) in enumerate(zip(old['comparison']['batch']['requests'],new['comparison']['batch']['requests'])):
        assert before['sample_name']==after['sample_name']
        for j,method in enumerate(('WC','JOINT_NATIVE')):
            x,y=before['paths'][j],after['paths'][j];assert x['method']==y['method']==method
            keys=['guided_sha256','guided_list_sha256','final_latent_sha256','actions','counters','block_visits','conditions_before','conditions_after','first_velocity_input_sha256','rng_after','flags_before','flags_after']
            checks={k:x[k]==y[k] for k in keys}
            assert len(x['guided_sha256'])==len(y['guided_sha256'])==36
            v0=next(v for v in runs[0][1]['videos'] if v['sample_name']==before['sample_name'] and v['method']==method)
            v1=next(v for v in runs[1][1]['videos'] if v['sample_name']==before['sample_name'] and v['method']==method)
            checks['actual_decoded_RGB_digest']=v0['decoded_RGB_SHA']==v1['decoded_RGB_SHA']
            checks['full_video_shape_and_PTS']=v0['all_frames_shape']==v1['all_frames_shape'] and v0['probe']==v1['probe']
            controls.append({'scene':before['sample_name'],'method':method,'checks':checks,'all_equal':all(checks.values()),'audited_guided_digests_compared':36})
        x,y=(r['comparison']['references'][i] for r in (old,new));checks={'outcome':x['outcome']==y['outcome']}
        if x['outcome']==y['outcome']=='ACCEPTED':
            for k in ('guided_sha256','guided_list_sha256','final_latent_sha256','conditions_before','conditions_after','first_velocity_input_sha256','CFG_calls','solver_steps','sampling'):
                checks[k]=x[k]==y[k]
            assert len(x['guided_sha256'])==len(y['guided_sha256'])==36
            v0=next(v for v in runs[0][1]['videos'] if v['sample_name']==x['sample_name'] and v['method']=='NATIVE')
            v1=next(v for v in runs[1][1]['videos'] if v['sample_name']==y['sample_name'] and v['method']=='NATIVE')
            checks['actual_decoded_RGB_digest']=v0['decoded_RGB_SHA']==v1['decoded_RGB_SHA']
            checks['full_video_shape_and_PTS']=v0['all_frames_shape']==v1['all_frames_shape'] and v0['probe']==v1['probe']
        controls.append({'scene':before['sample_name'],'method':'NATIVE','checks':checks,'all_equal':all(checks.values()),'reference_outcomes':[x['outcome'],y['outcome']]})
    pairs=[]
    s0,s1=(r[2]['summary']['per_scene_method'] for r in runs)
    for row in s1:
        prev=next((r for r in s0 if (r['sample_name'],r['method'])==(row['sample_name'],row['method'])),None)
        if prev is None:continue
        q0,q1=prev['mean_LPIPS'],row['mean_LPIPS'];t0,t1=prev['instrumented_pipeline_wall_seconds'],row['instrumented_pipeline_wall_seconds']
        pairs.append({'scene':row['sample_name'],'method':row['method'],'R1_LPIPS':q0,'R2_LPIPS':q1,
            'relative_LPIPS_decrease_percent':100*(q0-q1)/q0 if q0 else None,
            'R1_full_branch_calls':prev['complete_branch_calls'],'R2_full_branch_calls':row['complete_branch_calls'],
            'R1_instrumented_pipeline_seconds':t0,'R2_instrumented_pipeline_seconds':t1,
            'R2_same_run_WC_relative_fidelity_improvement_percent':row['relative_fidelity_improvement_percent'],
            'R2_same_run_improved_frames':row['improved_frames'],'R2_same_run_degraded_frames':row['degraded_frames'],
            'R2_same_run_tied_frames':row['tied_frames'],'frames_are_independent_samples':False,'clean_latency_claim':False})
    result={'status':'COMPLETE_R1_R2_WORKING_POINT_COMPARISON_WITH_AUDITED_CONTROL_DIGESTS',
        'observed_unix':time.time(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'bound_complete_audit_sha256':bindings,'config_checks':config_checks,'controls':controls,
        'all_unchanged_configuration_and_control_digests_equal':all(config_checks.values()) and all(r['all_equal'] for r in controls),
        'quality_informed_development_not_confirmation':True,'method_rows':pairs,
        'complete_reference_slots_per_run':2,'accepted_reference_slots':[r[1]['verdict']['accepted_reference_slots'] for r in runs],
        'scored_pairs_per_run':[r[2]['summary']['scored_pairs'] for r in runs],
        'no_new_tensor_load_or_metric_or_generation':True,'GPU_submissions':0,'ledger_written':False}
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
