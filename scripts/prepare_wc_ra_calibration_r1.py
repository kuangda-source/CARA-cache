#!/usr/bin/env python3
"""Freeze the complete six-origin real calibration card after actual batch CPU."""
import ast
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    prior_ref='manifests/wc_ra_calibration_sampling_cpu_r1_preregistration_20261010.json'
    prior=json.loads(Path(prior_ref).read_text())
    prefix='reports/wc_ra_calibration_sampling_cpu_r1_terminal_20261010_'
    audit_ref=prefix+'capture_and_independent_audit.json'
    receipt_ref=prefix+'receipt.json.native.gz'
    audit=json.loads(Path(audit_ref).read_text())
    receipt=json.loads(gzip.decompress(Path(receipt_ref).read_bytes()))
    assert audit['exit_code']==receipt['exit_code']==receipt['child_exit_code']==0
    assert audit['full_guarded_batch_complete_scope_reconstructed']
    expected={'actual_parent_guided_reloaded':288,'actual_parent_latents_reloaded':8,
        'actual_child_tensors_reloaded':96,'semantic_mutation_refusals':16,
        'actual_child_truncation_refusals':2,'last_writer_failure_controls':2,
        'complete_executed_parent_paths':16,'complete_child_arms_including_last_writer_failure':48,
        'actual_retained_Toy_tensor_file_size_and_hash_bindings':62}
    assert all(audit[k]==v for k,v in expected.items())
    assert receipt['source_revision']==audit['source_revision']
    assert receipt['payload_after_sha256']==prior['payload_sha256']
    assert {n:sha(n) for n in prior['payload_sha256']}==prior['payload_sha256']
    assert receipt['budget_before_sha256']==receipt['budget_after_sha256']==sha('reports/budget.json')
    common=json.loads(gzip.decompress(Path('reports/wc_other_scene_cfg_confirmation_r1_terminal_20261009_config_native.gz').read_bytes()))
    human=json.loads(gzip.decompress(Path('reports/wc_cfg_mechanism_confirmation_r1_terminal_20261009_config_native.gz').read_bytes()))
    requests=[common['preregistration']['confirmation_request'],human['preregistration']['confirmation_request']]
    cost_ref='reports/wc_ra_calibration_r1_complete_cost_forecast_20261010.json'
    forecast=json.loads(Path(cost_ref).read_text())
    source_refs=[]
    for item in forecast['prior_complete_sources']+[forecast['additional_slow_load_source']]:
        assert sha(item['source'])==item['compressed_sha256']
        source_refs.append(item['source'])
    assert forecast['complete_scope']=={'parent_paths':4,'parent_solver_updates':144,
        'current_pair_measurements_reused':12,'additional_dense_future_pairs':156,
        'child_solver_updates':168,'total_solver_updates':312,'total_net_calls':624}
    subtotal=(forecast['additional_slow_load_source']['load_seconds']
        +4*forecast['max_full_parent_seconds']+12*forecast['max_nonnested_pair_seconds']
        +156*forecast['future_dense_pair_estimate_seconds']
        +forecast['new_origin_restore_and_bookkeeping_allowance_seconds']
        +forecast['full_parent_vector_write_allowance_seconds']+forecast['cleanup_allowance_seconds'])
    assert math.isclose(subtotal,forecast['subtotal_seconds'],abs_tol=1e-9)
    assert math.isclose(subtotal*forecast['whole_scope_margin_factor']/3600,
        forecast['forecast_complete_GPUh'],abs_tol=1e-12)
    assert 0<forecast['forecast_complete_GPUh']<=4 and not forecast['GPU_submissions']
    budget_raw=Path('reports/budget.json').read_bytes()
    budget=json.loads(budget_raw)
    assert budget['automatic_single_job_gpu_hours']==4 and budget['cap_gpu_hours']==77.89524658965853
    assert not any('inflight' in k for k in budget)
    assert budget['used_gpu_hours']+forecast['forecast_complete_GPUh']<=budget['cap_gpu_hours']
    spec=importlib.util.spec_from_file_location('calibration_contract','src/wcomr/cfg_ra_calibration_production.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reg={'card':module.CARD,'run_id':module.RUN,'registered_unix':time.time(),
        'hypothesis':'Collection preserves the complete shared-D6 parent trajectory while providing actual paired branch-error correlations and full dense-suffix latent propagation measurements for a coarse local RA prior.',
        'scope_counts':module.COUNTS,'requests':requests,'collection_switches':['OFF','ON'],
        'repetitions':['first'],'state_steps':[12,22,32,36],'target_steps':[13,23,33],
        'shared_anchors':[7,19,31],'reuse_ages':[6,4,2],
        'dense_steps':list(range(1,8))+[13,19,25,31,36],
        'selector':'UNIFORM_SHARED_D6_COLLECTION',
        'suffix_selector':'CURRENT_CC_OR_DD_THEN_COMPLETE_DENSE_DD',
        'measurement_space':'POST_RF_DENOISE_AND_FINAL_LATENT',
        'estimator':'SIX_ORIGIN_MEDIAN_RHO_THREE_STAGE_MEDIAN_GAIN_LINEAR_TIME_MAX_AGE6',
        'timesteps':common['sampling_protocol']['timesteps'],
        'identity_selection':'Already exposed Common/Human seed3; calibration development, not independent CONF.',
        'new_policy_or_clean_latency_claim':False,'forecast':forecast,
        'independent_scope_reason':'Integrated plan requires a local coarse RA calibration before full-video RA and coupled approximation/partial-refresh development; old native-policy sixteen-path card remains unchanged.',
        'does_not_accept_old_full16_card':True,
        'undefined_labels_policy':'Retain undefined rho/gain; refuse a deployable table if all rho or any stage gain is unobserved.',
        'estimated_cells_policy':'Global observed-median rho and time-interpolated median gain; age<=6 grid is an estimated prior, older/missing cells DD.',
        'age_and_stage_confounded':True,
        'paid_proxy_not_identical_to_absolute_latent_error':True,
        'not_video_quality_or_future_cost_supervision':True,
        'first_window_allocation_revision':'Complete forecast 3.552744294 GPUh supersedes the unregistered 2.5 GPUh MF-R calibration suggestion; use unregistered first-window allowance without reducing any paths or controls.',
        'batch_CPU_registration_ref':prior_ref,'batch_CPU_registration_sha256':sha(prior_ref),
        'batch_CPU_complete_audit_ref':audit_ref,'batch_CPU_complete_audit_sha256':sha(audit_ref),
        'execution_policy_ref':'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json',
        'budget_window_authorization_ref':'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json'}
    reg_ref='manifests/wc_ra_calibration_r1_preregistration_20261010.json'
    target=Path(reg_ref)
    assert not target.exists()
    target.write_text(json.dumps(reg,indent=2,allow_nan=False)+'\n')
    profile=Path('.sync/real-paired-interface-inputs-r1/profile-config.json').read_bytes()
    old=json.loads(Path('configs/wc_real_paired_interface_production_r1_20261009.json').read_text())
    assert hashlib.sha256(profile).hexdigest()==old['payload_sha256']['profile-config.json']
    generated={'profile-config.json':profile,
        'ra-calibration-requests.jsonl':(''.join(json.dumps(r)+'\n' for r in requests)).encode(),
        'budget-at-preparation.json':budget_raw}
    files=set(prior['payload_sha256'])|{prior_ref,audit_ref,receipt_ref,reg_ref,cost_ref,
        'src/wcomr/cfg_ra_calibration_production.py','src/wcomr/runtime_config.py',
        'manifests/wc_h0_eval_mode_contract_20261003.json','scripts/run_wc_s0_profile.py'}
    files.update(str(p) for p in Path('scripts').glob('*wc_ra_calibration*r1.py'))
    files.update(str(p) for p in Path('reports').glob('wc_ra_calibration_sampling_cpu_r1_terminal_20261010_*.native.gz'))
    files.update(source_refs)
    payload={n:sha(n) for n in sorted(files)}
    payload.update({n:hashlib.sha256(v).hexdigest() for n,v in generated.items()})
    for name in files:
        if name.endswith('.py'):
            ast.parse(Path(name).read_bytes())
            compile(Path(name).read_bytes(),name,'exec')
    runtime={**old['runtime_source_sha256'],**prior['runtime_source_sha256']}
    config={'identity':'RA_CALIBRATION_PREPARATION_NOT_SELECTED','execution_run_id':module.RUN,
        'preregistration':reg,'preregistration_ref':reg_ref,'preregistration_sha256':sha(reg_ref),
        'payload_sha256':payload,'project_input_sha256':old['project_input_sha256'],
        'runtime_source_sha256':runtime,'historical_wc_settings':old['historical_wc_settings'],
        'sampling_protocol':old['sampling_protocol'],'expected_real_components':1216,
        'expected_real_shape':[1,16,24,54,96],'logical_copy_cap_bytes':6*(1<<30),
        'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'cumulative_cap_GPUh':budget['cap_gpu_hours'],'automatic_single_job_GPUh':4,
        'GPU_execution_selected':False,'gpu_uuid':None,'single_job_exception_authority':None,
        'production_cpu_receipt_sha256':None,
        'production_cpu_stage':'.sync/wc-ra-calibration-production-cpu-r1-20261010',
        'batch_cpu_registration_ref':prior_ref,'batch_cpu_receipt_ref':receipt_ref,
        'batch_cpu_audit_ref':audit_ref,
        'legacy_profile_validator_role':'READ_ONLY_SOURCE_CHECKPOINT_GUARDRAIL_ASSET_CHECK_NO_OLD_EXECUTION_CAP'}
    inputs=Path('.sync/ra-calibration-inputs-r1')
    inputs.mkdir(exist_ok=False)
    for name,raw in generated.items():
        (inputs/name).write_bytes(raw)
    p=inputs/reg_ref
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(target.read_bytes())
    module.validate_contract(config,inputs)
    dest=Path('configs/wc_ra_calibration_production_r1_20261010.json')
    assert not dest.exists()
    dest.write_text(json.dumps(config,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'RA_CALIBRATION_LOCAL_PREPARATION_NOT_PRODUCTION_CPU',
        'payload_files':len(payload),'scope':module.COUNTS,
        'forecast_complete_GPUh':forecast['forecast_complete_GPUh'],
        'GPU_submissions':0,'GPU_selected':False}))


if __name__=='__main__':
    main()
