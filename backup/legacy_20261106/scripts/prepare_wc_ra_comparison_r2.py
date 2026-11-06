#!/usr/bin/env python3
"""Freeze actual real prior, complete eight paths and a whole-card cost forecast."""
import ast
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import hashlib
import time


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-incomplete',action='store_true');args=parser.parse_args()
    if args.resume_incomplete:
        assert not Path('configs/wc_ra_comparison_production_r2_20261010.json').exists()
        assert not Path('.sync/ra-comparison-inputs-r2').exists()
    design_ref='manifests/wc_ra_conservative_half_threshold_r2_design_preregistration_20261010.json'
    design=json.loads(Path(design_ref).read_text())
    basis_ref=design['basis_ref'];basis=json.loads(Path(basis_ref).read_text())
    assert sha(basis_ref)==design['basis_sha256'] and basis['exit_code']==0 and basis['independent_checks']['success']
    assert design['parent_tau']==0.141488470197544 and design['threshold_scale']==.5 and design['next_tau']==0.070744235098772
    prior_ref='manifests/wc_ra_baseline_references_cpu_r2_preregistration_20261010.json'
    prior=json.loads(Path(prior_ref).read_text())
    audit_ref='reports/wc_ra_baseline_references_cpu_r2_terminal_20261010_capture_and_independent_audit.json'
    audit=json.loads(Path(audit_ref).read_text())
    assert audit['exit_code']==0 and audit['full_guarded_three_method_scope_reconstructed']
    assert audit['complete_executed_paths']==32 and audit['actual_guided_reloaded']==576 and audit['actual_latents_reloaded']==16
    assert {n:sha(n) for n in prior['payload_sha256']}==prior['payload_sha256']
    cal_ref='reports/wc_ra_calibration_r1_terminal_20261010_capture_and_independent_audit.json'
    cal=json.loads(Path(cal_ref).read_text());assert cal['independent_checks']['success']
    runner_ref=cal['files']['runner']['local_path'];table_ref=cal['files']['calibration_table']['local_path']
    runner=json.loads(gzip.decompress(Path(runner_ref).read_bytes()))
    old=json.loads(gzip.decompress(Path(cal['files']['config']['local_path']).read_bytes()))
    requests=old['preregistration']['requests']
    threshold_ref='reports/wc_ra_real_first_threshold_reconstruction_20261010.json'
    threshold=json.loads(Path(threshold_ref).read_text())
    assert threshold['threshold']==0.141488470197544
    historic_ref='reports/wc_ra_calibration_r1_complete_cost_forecast_20261010.json'
    historic=json.loads(Path(historic_ref).read_text())
    source_refs=[]
    for x in historic['prior_complete_sources']+[historic['additional_slow_load_source']]:
        assert sha(x['source'])==x['compressed_sha256'];source_refs.append(x['source'])
    observed=[{'sample_name':r['sample_name'],'label':r['paths'][0]['label'],
        'instrumented_pipeline_seconds':r['paths'][0]['instrumented_parent_pipeline_wall_seconds']}
        for r in runner['batch']['requests']]
    full=max(historic['max_full_parent_seconds'],*(x['instrumented_pipeline_seconds'] for x in observed))
    load=max(historic['additional_slow_load_source']['load_seconds'],runner['load_seconds'])
    subtotal=load+8*full+900+480+120
    forecast={'status':'FULL_RA_COMPARISON_EIGHT_PATH_COST_FORECAST_NOT_SUBMITTED',
        'complete_scope':{'method_paths':6,'native_reference_slots':2,'complete_paths':8,
                         'solver_updates':288,'net_calls':576},
        'actual_current_calibration_runner_ref':runner_ref,'actual_current_calibration_runner_sha256':sha(runner_ref),
        'actual_current_collection_OFF_parent_costs':observed,
        'historic_complete_cost_ref':historic_ref,'historic_complete_cost_sha256':sha(historic_ref),
        'historic_complete_source_refs':source_refs,'conservative_per_complete_path_seconds':full,
        'slow_loading_seconds':load,'state_roundtrip_and_new_method_bookkeeping_allowance_seconds':900,
        'whole_card_vector_write_allowance_seconds':480,'cleanup_allowance_seconds':120,
        'subtotal_seconds':subtotal,'whole_scope_margin_factor':1.2,
        'forecast_complete_seconds':subtotal*1.2,'forecast_complete_GPUh':subtotal*1.2/3600,
        'empirical_forecast_not_strict_time_upper_bound':True,'ordinary_Native_cost_not_assumed_zero':True,
        'no_legacy_seconds_deadline_created':True,'automatic_single_job_GPUh':4,'GPU_submissions':0}
    assert 0<forecast['forecast_complete_GPUh']<=4
    cost_ref='reports/wc_ra_comparison_r2_complete_cost_forecast_20261010.json'
    if args.resume_incomplete:
        assert json.loads(Path(cost_ref).read_text())==forecast
    else:
        assert not Path(cost_ref).exists();Path(cost_ref).write_text(json.dumps(forecast,indent=2)+'\n')
    budget_raw=Path('reports/budget.json').read_bytes();budget=json.loads(budget_raw)
    assert not any('inflight' in k for k in budget)
    assert budget['automatic_single_job_gpu_hours']==4 and budget['cap_gpu_hours']==77.89524658965853
    assert budget['used_gpu_hours']+forecast['forecast_complete_GPUh']<=budget['cap_gpu_hours']
    spec=importlib.util.spec_from_file_location('cal_contract','src/wcomr/cfg_ra_calibration_production.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    reg={'card':'WC-RA-FULL-VIDEO-COMPARISON-R2-20261010-A','run_id':'wc-ra-full-video-comparison-r2',
        'registered_unix':time.time(),'hypothesis':design['hypothesis'],
        'scope_counts':{'requests':2,'complete_method_paths':6,'native_reference_slots':2,'complete_paths':8,
                        'maximum_videos':8,'solver_updates':288,'net_calls':576,'maximum_guided_outputs':288,
                        'maximum_final_latents':8,'maximum_fidelity_pairs':6},
        'requests':requests,'methods':['WC','JOINT_NATIVE','RA'],'repetitions':['first'],
        'branch_order':['conditional','negative_prompt'],'guided_weights':[8,-7],
        'state_steps':[13,21,33,35,36],'timesteps':old['sampling_protocol']['timesteps'],
        'threshold_rule':'PREREGISTERED_SINGLE_HALF_OF_ORIGINAL_D6_MEDIAN_AFTER_R1_DEVELOPMENT',
        'RA_threshold':design['next_tau'],'parent_RA_threshold':threshold['threshold'],'threshold_scale':.5,
        'development_design_ref':design_ref,'development_design_sha256':sha(design_ref),
        'development_basis_ref':basis_ref,'development_basis_sha256':sha(basis_ref),
        'quality_informed_development_refinement':True,'parameter_choice':design['parameter_choice'],
        'calibration_fingerprint':threshold['calibration_fingerprint'],
        'reference_policy':'ORDINARY_NATIVE_MATCHED_INPUT_NO_REPLACEMENT',
        'first_working_point_not_equal_actual_time_or_dense_count':True,
        'clean_latency_claim':False,'independent_confirmation_claim':False,
        'identity_selection':'Already exposed Common/Human seed3, development only',
        'fidelity_protocol':'Uniform offline CPU FP32 full native-size RGB93 LPIPS; report complete frame distributions; rejection slots retained, no replacement or zero-fill.',
        'negative_result_policy':'Distinguish this configuration, metric alignment and direction; preserve all positives/negatives, then preregister a low-cost distinguishing revision if supported.',
        'does_not_accept_or_shrink_old_sixteen_path_card':True,'forecast':forecast,
        'execution_policy_ref':'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json',
        'budget_window_authorization_ref':'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json'}
    reg_ref='manifests/wc_ra_comparison_r2_preregistration_20261010.json'
    if args.resume_incomplete:
        saved=json.loads(Path(reg_ref).read_text());reg['registered_unix']=saved['registered_unix'];assert reg==saved
    else:
        assert not Path(reg_ref).exists();Path(reg_ref).write_text(json.dumps(reg,indent=2,allow_nan=False)+'\n')
    profile=Path('.sync/ra-calibration-inputs-r1/profile-config.json').read_bytes()
    generated={'profile-config.json':profile,'ra-comparison-requests.jsonl':(''.join(json.dumps(r)+'\n' for r in requests)).encode(),
               'budget-at-preparation.json':budget_raw}
    files=set(prior['payload_sha256'])|{prior_ref,audit_ref,cal_ref,runner_ref,table_ref,
        cal['files']['config']['local_path'],cal['files']['CPU_result']['local_path'],
        threshold_ref,historic_ref,cost_ref,reg_ref,'src/wcomr/cfg_ra_comparison_production_r2.py',
        'src/wcomr/cfg_ra_calibration_production.py','src/wcomr/runtime_config.py',
        'manifests/wc_h0_eval_mode_contract_20261003.json','scripts/run_wc_s0_profile.py',
        'plans/WORLD_CACHE_RA_FULL_VIDEO_COMPARISON_R2_20261010.md',design_ref,basis_ref,
        'reports/wc_ra_comparison_r2_source_derivation_20261010.json'}
    files.update(str(p) for p in Path('scripts').glob('*wc_ra_comparison*r2*.py'))
    files.update(x['local_path'] for x in audit['files'].values());files.update(source_refs)
    payload={n:sha(n) for n in sorted(files)}
    payload.update({n:hashlib.sha256(v).hexdigest() for n,v in generated.items()})
    for n in files:
        if n.endswith('.py'):ast.parse(Path(n).read_bytes());compile(Path(n).read_bytes(),n,'exec')
    config={'identity':'RA_COMPARISON_PREPARATION_NOT_SELECTED','execution_run_id':reg['run_id'],
        'preregistration':reg,'preregistration_ref':reg_ref,'preregistration_sha256':sha(reg_ref),
        'payload_sha256':payload,'project_input_sha256':old['project_input_sha256'],
        'runtime_source_sha256':{**old['runtime_source_sha256'],**prior['runtime_source_sha256']},
        'historical_wc_settings':old['historical_wc_settings'],'sampling_protocol':old['sampling_protocol'],
        'expected_real_components':1216,'expected_real_shape':[1,16,24,54,96],
        'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'cumulative_cap_GPUh':budget['cap_gpu_hours'],'automatic_single_job_GPUh':4,
        'GPU_execution_selected':False,'gpu_uuid':None,'single_job_exception_authority':None,
        'production_cpu_receipt_sha256':None,'production_cpu_stage':'.sync/wc-ra-comparison-production-cpu-r2-20261010',
        'batch_cpu_registration_ref':prior_ref,'batch_cpu_audit_ref':audit_ref,
        'calibration_complete_audit_ref':cal_ref,'calibration_table_ref':table_ref,
        'calibration_runner_ref':runner_ref,'independent_threshold_ref':threshold_ref,
        'legacy_profile_validator_role':'READ_ONLY_SOURCE_CHECKPOINT_GUARDRAIL_ASSET_CHECK_NO_OLD_EXECUTION_CAP'}
    inputs=Path('.sync/ra-comparison-inputs-r2');inputs.mkdir(exist_ok=False)
    for n,raw in generated.items():(inputs/n).write_bytes(raw)
    reg_copy=inputs/reg_ref;reg_copy.parent.mkdir(parents=True,exist_ok=True)
    reg_copy.write_bytes(Path(reg_ref).read_bytes())
    target=Path('configs/wc_ra_comparison_production_r2_20261010.json');assert not target.exists()
    target.write_text(json.dumps(config,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'RA_COMPARISON_COMPLETE_EIGHT_PATH_PREPARATION_NOT_GPU',
        'scope':reg['scope_counts'],'payload_files':len(payload),'threshold':design['next_tau'],
        'forecast_complete_GPUh':forecast['forecast_complete_GPUh'],'GPU_submissions':0}))


if __name__=='__main__':main()
