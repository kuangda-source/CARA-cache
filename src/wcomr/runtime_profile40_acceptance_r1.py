"""Offline independent full40 profile acceptance from original saved receipts.

The pinned CPU post checks tensor contents and all decoded RGB. This layer
binds those receipts, rebuilds mode controls, raw scalar aggregates and costs.
"""
import copy
import math

from .frozen_shared_acceptance_r1 import digest, original_alive, original_asset
from .frozen_shared_production_r1 import fingerprint, number
from .gpu_budget_pool_v2 import BudgetPool
from .runtime_profile40_cpu_acceptance_r1 import validate_bundle, validate_proof, ACCEPTED_STATUS, PATTERNS
from .runtime_profile40_execution_r1 import full_rows
from .runtime_profile40_post_r1 import (
    COMPLETE_STATUS, GPU_TERMINAL_STATUS, metadata_audit, audit_memory, audit_profile_value,
    parity_controls, summarize,
)
from .runtime_profile40_production_r1 import RUN, COUNTS, validate_contract, validate_authority


def financial_receipt(value, launch, config):
    supervisor = value.get('supervisor') or value.get('supervisor_fallback')
    bill = value.get('billing') or value.get('billing_fallback')
    if not supervisor or not bill or 'pool' not in value:
        return dict(own_GPU_finance_released=False, original_finance_status='MISSING_ORIGINAL_FINANCE_RETAINED')
    keys = ('source_revision','launch_id','run_id','gpu_uuid','scope_counts','config_sha256')
    bill_sha = value.get('billing_sha256') if value.get('billing') else value.get('billing_fallback_sha256')
    if (supervisor['status'] != GPU_TERMINAL_STATUS
            or any(supervisor[k] != launch[k] for k in keys)
            or any(bill[k] != launch[k] for k in keys)
            or any(supervisor[k] != launch['supervisor_identity'][k] for k in ('pid','start_ticks'))
            or supervisor['registration_sha256'] != launch['registration_sha256']
            or supervisor['bound_profile_fingerprint'] != launch['bound_profile_fingerprint']
            or bill['status'] != 'N09_FULL40_ACTUAL_GPU_BILL'
            or bill['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or not number(bill['actual_GPUh']) or not number(bill['wall_seconds'])
            or bill['actual_GPUh'] <= 0 or not math.isclose(bill['wall_seconds']/3600,bill['actual_GPUh'],rel_tol=1e-12)
            or supervisor['billing_sha256'] != bill_sha or supervisor['actual_GPUh'] != bill['actual_GPUh']):
        raise ValueError('Original exact supervisor, entire actual wall and bill identity required')
    pool = value['pool']; job = pool['jobs'][RUN]
    if (pool['cap_gpu_hours'] != config['cumulative_cap_GPUh']
            or pool['origin_used_gpu_hours'] != config['budget_origin_used_GPUh']
            or any(pool[k] != v for k,v in BudgetPool.accounting(pool).items())
            or job['status'] != 'SETTLED' or job['actual_GPUh'] != bill['actual_GPUh']
            or job['billing_sha256'] != bill_sha or job['scope_counts'] != COUNTS
            or job['forecast_GPUh'] != config['forecast_complete_GPUh']
            or job['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or job['production_CPU_sha256'] != launch['production_CPU_sha256']
            or job['bound_profile_fingerprint'] != launch['bound_profile_fingerprint']
            or job['bound_input_fingerprint'] != launch['bound_input_fingerprint']
            or job['authorization_sha256'] != launch['authorization_sha256']
            or any(job[k] != launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256'))):
        raise ValueError('Original v2 origin/cap, additive totals and own job settlement required')
    if config['billed_limit_GPUh'] >= 12 and job['kind'] != 'V2_SPECIFIC_WHOLE_CARD_APPROVAL':
        raise ValueError('Original specific complete-card approval must survive settlement')
    respected = bill['actual_GPUh'] <= config['billed_limit_GPUh']
    if not respected and pool.get('budget_overrun_recorded') is not True:
        raise ValueError('Actual fee overrun cannot be silently erased')
    released = (value.get('own_UUID_lock_exists') is True and value.get('own_UUID_lock_free') is True
        and value.get('own_GPU','').split(',')[0].strip() == launch['gpu_uuid']
        and not value.get('GPU_telemetry_error')
        and not any(line.split(',')[0].strip() == launch['gpu_uuid']
                    for line in value.get('compute_apps','').splitlines() if line.strip()))
    return dict(own_GPU_finance_released=released, actual_GPUh=bill['actual_GPUh'],
        original_billed_limit_respected=respected, original_output_root_available=bill['original_output_root_available'],
        original_finance_status='ORIGINAL_ACTUAL_BILL_AND_ADDITIVE_SETTLEMENT_MATCH',
        other_UUID_activity_not_own_release_failure=True)


def accept(value, launch):
    if (value.get('status') != 'N09_FULL40_ORIGINAL_ONCE_CAPTURE' or value.get('mode') != 'terminal'
            or value['launch'] != launch or launch['run_id'] != RUN
            or value['observed_unix'] < launch['next_check_not_before_unix']
            or value['registration_sha256'] != launch['registration_sha256']
            or value['registration']['source_revision'] != launch['source_revision']
            or value['payload_actual_sha256'] != value['registration']['payload_sha256']
            or set(value['payload_verified']) != set(value['registration']['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())):
        raise ValueError('Original full source and post-ETA terminal snapshot required; health is not acceptance')
    processes = value['original_processes']; supervisor = value.get('supervisor') or value.get('supervisor_fallback') or {}
    live = dict(supervisor=original_alive(launch['supervisor_identity'],processes.get('supervisor_pid')),
        child=original_alive(supervisor.get('child_identity'),processes.get('child_pid')),
        CPU_post=original_alive(launch.get('post_watcher_identity'),processes.get('post_watcher_pid')))
    if any(live.values()):
        return dict(status='N09_ORIGINAL_TASK_STILL_RUNNING_REESTIMATE_ONCE_NO_RESTART',original_live_handles=live,
            full_runtime_profile_scope_accepted=False,GPU_submissions=0,SSH_queries=0)
    if not value.get('config'):
        return dict(status='N09_ORIGINAL_TERMINAL_MISSING_CONFIG_RETAINED',full_runtime_profile_scope_accepted=False,
                    no_GPU_relaunch_authorized=True,GPU_submissions=0)
    config = value['config']; data = {k:value[k] for k in ('runtime_scope','timing_protocol','method_freeze','shared_config')}
    bound = validate_contract(config,data['runtime_scope'],data['timing_protocol'],data['method_freeze'],data['shared_config'])
    if value['config_sha256'] != launch['config_sha256'] or fingerprint(bound) != launch['bound_profile_fingerprint']:
        raise ValueError('Original complete diagnostic matrix and config identity differ')
    for name,ref in config['references'].items():
        if value[name+'_sha256'] != ref['sha256']:
            raise ValueError('Original bound production reference differs: '+name)
    if config['references']['method_freeze'] != data['shared_config']['references']['method_freeze']:
        raise ValueError('Original common frozen role binding required')
    proof,registration,authority = (value[k] for k in ('production_CPU','registration','authorization'))
    validate_bundle(value['production_CPU_bundle'],launch['source_revision'],
        registration_sha256=value['registration_sha256'],config_sha256=value['config_sha256'],
        proof_sha256=value['production_CPU_sha256'],payload_sha256=registration['payload_sha256'])
    validate_proof(proof,config,bound,registration,registration_sha256=value['registration_sha256'],config_sha256=value['config_sha256'])
    validate_authority(config,bound,registration,proof,authority,revision=launch['source_revision'],gpu_uuid=launch['gpu_uuid'],
        config_sha256=value['config_sha256'],proof_sha256=value['production_CPU_sha256'],registration_sha256=value['registration_sha256'])
    accepted = value['independent_CPU_acceptance']
    if (value['authorization_sha256'] != launch['authorization_sha256']
            or value['independent_CPU_acceptance_sha256'] != launch['independent_CPU_acceptance_sha256']
            or authority['independent_CPU_acceptance_sha256'] != value['independent_CPU_acceptance_sha256']
            or accepted['status'] != ACCEPTED_STATUS or accepted['CPU_accepted'] is not True):
        raise ValueError('Original authorization and independent CPU acceptance bytes differ')
    expected_cpu = dict(status=ACCEPTED_STATUS,CPU_accepted=True,source_revision=launch['source_revision'],
        registration_sha256=launch['registration_sha256'],config_sha256=launch['config_sha256'],
        production_CPU_sha256=launch['production_CPU_sha256'],production_CPU_bundle_sha256=value['production_CPU_bundle_sha256'],
        bound_profile_fingerprint=launch['bound_profile_fingerprint'],scope_counts=COUNTS,CPU_commands=len(PATTERNS)+1)
    if any(accepted.get(k) != v for k,v in expected_cpu.items()):
        raise ValueError('The independent CPU acceptance belongs to another source, scope or proof')
    cpu_launch, cpu_exit = value['production_CPU_launch'], value['production_CPU_exit']
    if (cpu_exit['exit_code'] != 0 or cpu_exit['source_revision'] != launch['source_revision']
            or cpu_exit['registration_sha256'] != launch['registration_sha256']
            or cpu_exit['production_CPU_sha256'] != launch['production_CPU_sha256']
            or cpu_exit['bundle_result_sha256'] != value['production_CPU_bundle_sha256']
            or any(cpu_exit['original_CPU_identity'].get(k) != cpu_launch['identity'].get(k)
                   or accepted['original_CPU_identity'].get(k) != cpu_launch['identity'].get(k)
                   for k in ('pid','start_ticks'))
            or cpu_launch['source_revision'] != launch['source_revision']
            or cpu_launch['registration_sha256'] != launch['registration_sha256']
            or any(proof['unchanged_profile_and_numeric_CPU_reuse']['source_sha256'][n]
                   != data['runtime_scope']['source_bindings'][n]['sha256']
                   for n in proof['unchanged_profile_and_numeric_CPU_reuse']['source_sha256'])):
        raise ValueError('Original CPU exit/identity and frozen four-source reuse must agree')
    finance = financial_receipt(value,launch,config)
    if (not finance['own_GPU_finance_released'] or not finance.get('original_output_root_available')
            or 'post_exit' not in value or 'final' not in value):
        return dict(status='N09_ORIGINAL_TERMINAL_FINANCE_OR_CPU_RECEIPT_INCOMPLETE_RETAINED',
            full_runtime_profile_scope_accepted=False,no_GPU_relaunch_authorized=True,**finance,GPU_submissions=0)
    post,final = value['post_exit'],value['final']; supervisor=value['supervisor']
    if (post['status'] != 'N09_FULL40_POST_CPU_TERMINAL'
            or post['original_supervisor'] != {k:launch['supervisor_identity'][k] for k in ('pid','start_ticks')}
            or post['source_revision'] != launch['source_revision'] or post['config_sha256'] != launch['config_sha256']
            or post['final_result_sha256'] != value['final_sha256']
            or final['source_revision'] != launch['source_revision'] or final['config_sha256'] != launch['config_sha256']
            or final['bound_profile_fingerprint'] != launch['bound_profile_fingerprint'] or final['scope_counts'] != COUNTS
            or final['GPU_supervisor'] != supervisor
            or any(final[k] for k in ('GPU_submissions','ledger_written','CUDA_initialized'))):
        raise ValueError('Original CPU post/final identities or its no-GPU boundary differ')
    if final['status'] == 'N09_FULL40_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED':
        return dict(status='N09_CPU_TECHNICAL_FAILURE_READONLY_REPAIR_REQUIRED',full_runtime_profile_scope_accepted=False,
            original_CPU_error=final.get('CPU_terminal_error'),**finance,GPU_submissions=0)
    runner = value.get('runner',{'runs':[]})
    if value.get('runner') and (value['runner_sha256'] != supervisor['runner_sha256']
            or runner['source_revision'] != launch['source_revision'] or runner['config_sha256'] != launch['config_sha256']
            or runner['bound_profile_fingerprint'] != fingerprint(bound) or runner['scope_counts'] != COUNTS
            or runner['matrix'] != bound['execution_plan'] or runner['bindings'] != bound['bindings']):
        raise ValueError('Original resident worker, methods, order or observed scope differs')
    if supervisor['child_exit_code'] == 0 and (runner['model_load_calls'] != 1 or runner['model_loads_completed'] != 1):
        raise ValueError('A complete full40 card must load one resident model')
    rows = final['rows']; original = full_rows(runner['runs'],bound)
    if len(rows) != 40 or [r['id'] for r in rows] != [r['id'] for r in original]:
        raise ValueError('All original40 positions must survive postprocessing')
    inventory = {r['path']:r for r in final['artifact_inventory']}
    if len(inventory) != len(final['artifact_inventory']):raise ValueError('Duplicate original artifact path')
    scalar_count = 0
    for row,before,planned in zip(rows,original,bound['execution_plan']):
        if not set(before).issubset(row) or any(row[k] != v for k,v in before.items()):
            raise ValueError('CPU post changed an original outcome or timer')
        if row.get('raw_model_audit') == 'PASS':
            metadata_audit(row,planned,bound);original_asset(row['final_artifact'],inventory,value['output_root'])
            if not digest(row['final_latent_sha256']):raise ValueError('Original finite latent tree identity required')
            if planned['audit_guided']:
                original_asset(row['guided_artifact'],inventory,value['output_root'])
                if row['guided_outputs'] != 36 or not digest(row['guided_tree_sha256']):
                    raise ValueError('All36 original guided outputs required')
            elif any(k in row for k in ('guided_artifact','guided_outputs','guided_tree_sha256')):
                raise ValueError('Lean diagnostic cannot contain guided research artifacts')
        if row.get('request_memory_audit') == 'PASS':audit_memory(row,expected_device='cuda:0')
        if row.get('component_profile_audit') == 'PASS':
            raw = None
            if planned['component_profile']:
                asset=row['component_profile_artifact'];original_asset(asset,inventory,value['output_root'])
                info=value['profile_scalar_originals'][asset['path']]
                if (info['path'] != asset['path'] or info['sha256'] != asset['sha256'] or info['bytes'] != asset['bytes']
                        or info['matches_original_row_identity'] is not True or info['data'] is None):
                    raise ValueError('Original scalar file bytes and source row identity required')
                raw=info['data'];scalar_count+=1
            expected=audit_profile_value(row,planned,raw,expected_device='cuda:0',probe_depth=2)
            if row.get('audited_component_profile') != expected:
                raise ValueError('Independent original interval aggregation differs')
        if row.get('endpoint_audit') == 'PASS':
            asset=row['video_artifact'];original_asset(asset,inventory,value['output_root'])
            if (row['status'] != 'COMPLETE' or row.get('raw_model_audit') != 'PASS'
                    or [asset['frames'],asset['fps'],asset['width'],asset['height']] != [93,16,768,432]
                    or len(asset['decoded_rgb_sha256']) != 93 or not all(digest(h) for h in asset['decoded_rgb_sha256'])
                    or row['decoded_video']['frames'] != 93 or not digest(row['decoded_video']['RGB_sha256'])):
                raise ValueError('All original93 RGB observations required')
    controls,failures=parity_controls(rows,bound)
    if any(final.get(k) != v for k,v in controls.items()) or any(f not in final['audit_failures'] for f in failures):
        raise ValueError('Independent all36/endpoint/history/RGB control reconstruction differs')
    expected=summarize(copy.deepcopy(final),bound,observed_paths=len(runner['runs']),child_exit_code=supervisor['child_exit_code'])
    if any(fingerprint(final.get(k)) != fingerprint(v) for k,v in expected.items()):
        raise ValueError('Independent full40 mode/cohort reconstruction differs')
    if final['resource_boundary_observations'] != runner.get('resource_observations',[]):
        raise ValueError('CPU post changed original resource observations')
    full = final['status'] == COMPLETE_STATUS and post['exit_code'] == 0
    if final['status'] == COMPLETE_STATUS and not full:raise ValueError('Nonzero CPU post cannot be full acceptance')
    return dict(status='N09_FULL40_PROFILE_INDEPENDENTLY_ACCEPTED_NOT_CLEAN_SPEED' if full else
        'N09_FULL40_TERMINAL_ISSUES_OR_REJECTIONS_RETAINED',terminal_receipt_audit_accepted=True,
        full_runtime_profile_scope_accepted=full,full_protocol_including_billed_limit_accepted=full and finance['original_billed_limit_respected'],
        original_runner_paths=len(runner['runs']),registered_total_paths=40,registered_formal_profile_paths=30,
        original_CPU_post_exit_code=post['exit_code'],accepted_93frame_videos=expected['accepted_93frame_videos'],
        accepted_complete_mode_groups=expected['accepted_complete_scene_method_mode_groups'],
        independently_reconstructed_scalar_files=scalar_count,all_mode_observations=expected['all_mode_observations'],
        clean_repeated_latency_claim=False,action_unit_prices_measured=False,minimal_calibration_collection_cost_measured=False,
        **finance,GPU_submissions=0,SSH_queries=0)
