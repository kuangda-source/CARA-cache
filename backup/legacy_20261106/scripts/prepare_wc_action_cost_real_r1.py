#!/usr/bin/env python3
"""Freeze full real C/A/P/D incremental-cost card after the complete R4 CPU proof."""
import ast
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    prior_ref='manifests/wc_source_aware_action_cost_cpu_r4_preregistration_20261010.json'
    prior=json.loads(Path(prior_ref).read_text())
    prefix='reports/wc_source_aware_action_cost_cpu_r4_terminal_20261010_'
    audit_ref=prefix+'capture.json'; receipt_ref=prefix+'receipt.json.native.gz'
    result_ref=prefix+'result.json.native.gz'
    audit=json.loads(Path(audit_ref).read_text())
    receipt=json.loads(gzip.decompress(Path(receipt_ref).read_bytes()))
    result=json.loads(gzip.decompress(Path(result_ref).read_bytes()))
    assert audit['exit_code']==receipt['exit_code']==receipt['child_exit_code']==0
    assert audit['independent_source_complete_results_and_actual_artifact_hashes_verified']
    assert (result['actual_complete_solver_updates'],result['actual_normal_net_calls'],
            result['actual_parent_guided_reloaded'],result['actual_parent_latents_reloaded'],
            result['actual_post_RF_branch_tensors_reloaded'])==(864,1728,576,16,224)
    assert result['mutation_refusals']==10 and result['actual_truncation_refusals']==2
    assert result['last_parent_writer_failure_controls']==1 and not result['CUDA_initialized']
    assert receipt['payload_after_sha256']==prior['payload_sha256']
    assert {n:sha(n) for n in prior['payload_sha256']}==prior['payload_sha256']
    assert receipt['budget_before_sha256']==receipt['budget_after_sha256']
    assert result['new_action_cost_mutation_refusals']==12
    assert audit['independent_tensor_reload']['actual_tensors']==816
    assert audit['independent_tensor_reload']['direct_C_and_dense_and_parent_parity']
    old=json.loads(Path('configs/wc_ra_calibration_production_r1_20261010.json').read_text())
    spec=importlib.util.spec_from_file_location('guided_w1_contract','src/wcomr/source_aware_action_cost_production_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=[json.loads(line) for line in Path('configs/cal_w1d8.jsonl').read_text().splitlines() if line]
    requests=[next(r for r in rows if r['name']==name) for name in module.NAMES]
    cost_ref='reports/wc_action_cost_real_r1_complete_cost_forecast_20261010.json'
    forecast=json.loads(Path(cost_ref).read_text())
    assert forecast['complete_scope']==module.COUNTS
    source_refs=list(forecast['source_refs'])
    for name,digest in forecast['source_refs'].items(): assert sha(name)==digest
    assert abs(sum(forecast['cost_parts'].values())-forecast['subtotal_seconds'])<1e-9
    assert abs(forecast['subtotal_seconds']*forecast['whole_scope_margin_factor']/3600-forecast['forecast_complete_GPUh'])<1e-12
    assert 0<forecast['forecast_complete_GPUh']<=4
    import subprocess
    budget_raw=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','cat /home/gaokuangda/data/gkd/worldcache_omr/reports/budget.json'],timeout=40);budget=json.loads(budget_raw)
    assert budget['automatic_single_job_gpu_hours']==4 and budget['cap_gpu_hours']==77.89524658965853
    # CPU preparation is read-only and may proceed while the approved main card runs.
    # GPU selection/admission separately requires a settled fresh ledger and free GPU.
    inflight={k:v for k,v in budget.items() if 'inflight' in k}
    assert not inflight or (list(inflight)==['wc_ra_plus_a_r1_inflight'] and inflight['wc_ra_plus_a_r1_inflight']['run_id']=='wc-ra-plus-a-full-video-r1')
    reg={'card':module.CARD,'run_id':module.RUN,'registered_unix':time.time(),
        'hypothesis':'Measure same-state post-paid-probe C/shared-A/50percent partial/dense paired costs with actual output heads and full state restore, providing real incremental cost inputs for source-aware multi-precision CFG scheduling; retain all six modes, eight parents, eight origins and all repetitions without standalone-win gates.',
        'scope_counts':module.COUNTS,'requests':requests,'collection_switches':['OFF','ON'],
        'repetitions':['first'],'state_steps':[12,30,35,36],'target_steps':[12,30],
        'strictly_past_anchor_steps':[7,25],'dense_steps':list(range(1,8))+[13,19,25,31,36],
        'selector':'UNIFORM_SHARED_D6_COLLECTION','measurement_space':'POST_RF_DENOISE_FP32_BCTHW',
        'methods':['ORIGINAL']+module.MODES,'layer_indices_zero_based':[4,10,16,22],
        'block_size':128,'fractions':[.5],'warmups':1,'repeats':3,
        'expected_probe_shape':[1,24,27,48,2048],'expected_active_counts':{'0.5':15488},
        'cost_boundary':'POST_ALREADY_PAID_TWO_SHALLOW_PROBES_THROUGH_POST_RF_PAIR',
        'A_methods':['W1_ONE_PHASE','BETA1_ONE_PHASE'],'A_shared_phase_boundary':25,'A_shared_alpha':[1,.5],
        'C_gamma_flow_original_clone_and_two_original_heads_paid':True,
        'A_extra_heads_and_shared_post_RF_fusion_paid':True,'C_or_A_deep_blocks':0,
        'teacher_OR_partial_updates_WC_anchor':False,'group_cost_is_clean_pipeline_latency':False,
        'teacher_updates_deployment_anchor':False,'new_policy_or_clean_latency_claim':False,
        'timesteps':old['sampling_protocol']['timesteps'],'forecast':forecast,
        'identity_selection':'Four already exposed CAL W1D8 scenes, same original seed0; not independent CONF.',
        'source_quality':'Actual own-branch D7/25 projections seed isolated P; A uses only actual parent D calibration. C must equal actual parent C; P is approximate, not a true D or zero-risk source.',
        'prospective_condition_provenance':'Save per-field condition hashes, finite mask/nonzero witnesses and raw/numerical solver configuration; preserve prior R1/R2 aggregate mismatch.',
        'parent_route_is_not_new_controller_benefit':True,'group_error_and_cost_are_not_partial_video_result':True,
        'source_quality_and_age_are_part_of_later_selector':True,'no_missing_scene_or_origin_replacement':True,
        'combination_not_gated_by_standalone_A_win':True,
        'first_window_allocation_revision':'Complete eight-parent/eight-origin/six-mode warmup and three-repetition cost forecast; preserve prior P0 whole envelope plus A costs without deleting any scene, control or repeat to fit4GPUh.',
        'preparation_may_record_original_main_inflight_not_actual_spending':True,
        'new_GPU_waits_original_main_GPU_raw_CPU_and_score_CPU_settled':True,
        'batch_CPU_registration_ref':prior_ref,'batch_CPU_registration_sha256':sha(prior_ref),
        'batch_CPU_complete_audit_ref':audit_ref,'batch_CPU_complete_audit_sha256':sha(audit_ref),
        'execution_policy_ref':'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json',
        'budget_window_authorization_ref':'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json'}
    reg_ref='manifests/wc_action_cost_real_r1_preregistration_20261010.json'
    target=Path(reg_ref);assert not target.exists();target.write_text(json.dumps(reg,indent=2,allow_nan=False)+'\n')
    profile=Path('.sync/wc-mf-a-original-profile-config.json').read_bytes()
    assert hashlib.sha256(profile).hexdigest()==old['payload_sha256']['profile-config.json']
    generated={'profile-config.json':profile,'action-cost-requests.jsonl':''.join(json.dumps(r)+'\n' for r in requests).encode(),
               'budget-at-preparation.json':budget_raw}
    files=set(prior['payload_sha256'])|{prior_ref,audit_ref,receipt_ref,result_ref,reg_ref,cost_ref,
        'src/wcomr/source_aware_action_cost_production_r1.py','src/wcomr/runtime_config.py',
        'manifests/wc_h0_eval_mode_contract_20261003.json','scripts/run_wc_s0_profile.py'}
    files.update(str(p) for p in Path('scripts').glob('*wc_action_cost_real*r1.py'))
    files.update(str(p) for p in Path('reports').glob('wc_source_aware_action_cost_cpu_r4_terminal_20261010_*.native.gz'))
    files.update(source_refs)
    payload={n:sha(n) for n in sorted(files)}
    payload.update({n:hashlib.sha256(raw).hexdigest() for n,raw in generated.items()})
    for name in files:
        if name.endswith('.py'):compile(ast.parse(Path(name).read_bytes()),name,'exec')
    config={'identity':'ACTION_COST_GROUP_PREPARATION_NOT_SELECTED','execution_run_id':module.RUN,
        'preregistration':reg,'preregistration_ref':reg_ref,'preregistration_sha256':sha(reg_ref),
        'payload_sha256':payload,'project_input_sha256':old['project_input_sha256'],
        'runtime_source_sha256':{**old['runtime_source_sha256'],**prior['runtime_source_sha256']},
        'historical_wc_settings':old['historical_wc_settings'],'sampling_protocol':old['sampling_protocol'],
        'expected_real_components':1216,'expected_real_shape':[1,16,24,54,96],
        'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'cumulative_cap_GPUh':budget['cap_gpu_hours'],'automatic_single_job_GPUh':4,
        'GPU_execution_selected':False,'gpu_uuid':None,'single_job_exception_authority':None,
        'production_cpu_receipt_sha256':None,'production_cpu_stage':'.sync/wc-action-cost-real-production-cpu-r1-20261010',
        'batch_cpu_registration_ref':prior_ref,'batch_cpu_receipt_ref':receipt_ref,
        'batch_cpu_audit_ref':audit_ref,'batch_cpu_result_ref':result_ref,
        'legacy_profile_validator_role':'READ_ONLY_SOURCE_CHECKPOINT_GUARDRAIL_ASSET_CHECK_NO_OLD_EXECUTION_CAP'}
    inputs=Path('.sync/action-cost-real-inputs-r1');inputs.mkdir(exist_ok=False)
    for name,raw in generated.items():(inputs/name).write_bytes(raw)
    p=inputs/reg_ref;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(target.read_bytes())
    module.validate_contract(config,inputs)
    dest=Path('configs/wc_action_cost_real_production_r1_20261010.json');assert not dest.exists()
    dest.write_text(json.dumps(config,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'ACTION_COST_GROUP_LOCAL_PREPARATION_NOT_PRODUCTION_CPU',
        'payload_files':len(payload),'scope':module.COUNTS,'forecast_complete_GPUh':forecast['forecast_complete_GPUh'],
        'GPU_submissions':0,'GPU_selected':False}))


if __name__=='__main__':main()
