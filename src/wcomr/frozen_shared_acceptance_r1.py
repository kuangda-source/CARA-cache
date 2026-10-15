"""Offline independent receipt/statistics acceptance; no artifact downloads.

The pinned original CPU post audits the actual tensors and decoded videos.
This second layer independently binds those receipts, reconstructs the matrix
and paired statistics, and checks original task-specific financial release.
"""
import copy
import math
from pathlib import PurePosixPath
import re

from .frozen_shared_production_r1 import (
    RUN, audit_row, fingerprint, full_rows, validate_contract, validate_launch_authority,
)
from .frozen_shared_post_r1 import COMPLETE_STATUS, GPU_TERMINAL_STATUS, stable_history, summarize
from .frozen_shared_execution_r1 import point
from .gpu_budget_pool_v2 import BudgetPool


def original_alive(expected, observed):
    return bool(expected and observed and expected['pid'] == observed['pid']
                and expected['start_ticks'] == observed['start_ticks']
                and observed['state'] not in (None, 'Z', 'X'))


def digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def original_asset(info, inventory, root):
    path, parent = PurePosixPath(info['path']), PurePosixPath(root)
    if (not path.is_absolute() or not path.is_relative_to(parent) or '..' in path.parts
            or not digest(info['sha256']) or type(info['bytes']) is not int or info['bytes'] <= 0
            or inventory.get(str(path)) != {k: info[k] for k in ('path', 'sha256', 'bytes')}):
        raise ValueError('Original artifact receipt or final inventory identity differs')


def accept(value, launch, *, bootstrap_repetitions=4096):
    if (value['status'] != 'N07_SHARED180_ORIGINAL_ONCE_CAPTURE' or value['launch'] != launch
            or value['registration_sha256'] != launch['registration_sha256']
            or value['registration']['source_revision'] != launch['source_revision']
            or set(value['payload_verified']) != set(value['registration']['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())
            or launch['run_id'] != RUN):
        raise ValueError('Original launch, complete payload and registration identity required')
    if value['mode'] != 'terminal':
        raise ValueError('Admission-only observation contains no scientific acceptance')
    if value['observed_unix'] < launch['next_check_not_before_unix']:
        raise ValueError('An early terminal observation does not satisfy the original ETA')
    processes = value['original_processes']
    supervisor = value.get('supervisor', {})
    live = dict(supervisor=original_alive(launch['supervisor_identity'], processes.get('supervisor_pid')),
                post=original_alive(launch.get('post_watcher_identity'), processes.get('post_watcher_pid')),
                child=original_alive(supervisor.get('child_identity'), processes.get('child_pid')))
    if any(live.values()):
        return dict(status='N07_ORIGINAL_TASK_STILL_RUNNING_REESTIMATE_ONCE_NO_RESTART',
            original_live_handles=live, observed_unix=value['observed_unix'],
            original_runner_paths=len(value.get('runner', {}).get('runs', [])),
            scientific_full_scope_accepted=False, GPU_submissions=0, SSH_queries=0)
    if not supervisor or 'post_exit' not in value or 'final' not in value:
        return dict(status='N07_ORIGINAL_TERMINAL_RECEIPT_MISSING_TECHNICAL_REPAIR_REQUIRED',
            original_live_handles=live, scientific_full_scope_accepted=False,
            original_admission_failure=value.get('admission_failure'),
            original_fallback_supervisor=value.get('supervisor_fallback'),
            no_GPU_relaunch_authorized=True, GPU_submissions=0, SSH_queries=0)
    config, bound, proof, authority = (value[k] for k in ('config', 'bound_inputs', 'production_CPU', 'authorization'))
    plan = validate_contract(config, bound)
    if (value['config_sha256'] != launch['config_sha256']
            or value['bound_inputs_sha256'] != config['references']['bound_inputs']['sha256']
            or fingerprint(bound) != launch['bound_input_fingerprint']
            or value['production_CPU_sha256'] != launch['production_CPU_sha256']
            or value['authorization_sha256'] != launch['authorization_sha256']):
        raise ValueError('Frozen scope, original typed CPU or launch authority differs')
    validate_launch_authority(config, bound, value['registration'], proof, authority,
        revision=launch['source_revision'], gpu_uuid=launch['gpu_uuid'],
        config_sha256=value['config_sha256'], proof_sha256=value['production_CPU_sha256'],
        registration_sha256=value['registration_sha256'])
    if (proof['actual_sample_argument_variants'] != 160 or proof['matrix'] != plan
            or proof['CUDA_initialized'] or proof['model_weights_loaded']
            or proof['runner_source_sha256'] != value['registration']['payload_sha256'][
                'scripts/run_wc_paper_N07_frozen_shared180_r1.py']):
        raise ValueError('All original160 typed requests and a no-weights CPU proof required')
    if (supervisor['status'] != GPU_TERMINAL_STATUS
            or supervisor['pid'] != launch['supervisor_identity']['pid']
            or supervisor['start_ticks'] != launch['supervisor_identity']['start_ticks']
            or any(supervisor[k] != launch[k] for k in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid',
                       'scope_counts', 'config_sha256', 'bound_input_fingerprint', 'registration_sha256'))):
        raise ValueError('Original exact supervisor, scope and terminal status required')
    bill, pool, post, final = (value[k] for k in ('billing', 'pool', 'post_exit', 'final'))
    if (bill['status'] != 'N07_SHARED180_ACTUAL_GPU_BILL' or not bill['original_output_root_available']
            or any(bill[k] != launch[k] for k in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid',
                                                'scope_counts', 'config_sha256'))
            or bill['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or not isinstance(bill['actual_GPUh'], (int, float)) or not math.isfinite(bill['actual_GPUh'])
            or bill['actual_GPUh'] <= 0 or bill['actual_GPUh'] > bill['billed_limit_GPUh']
            or not math.isclose(bill['wall_seconds'] / 3600, bill['actual_GPUh'], rel_tol=1e-12)
            or supervisor['billing_sha256'] != value['billing_sha256']
            or supervisor['actual_GPUh'] != bill['actual_GPUh']):
        raise ValueError('Original complete actual cost and its immutable billing identity required')
    job = pool['jobs'][RUN]
    if (pool['cap_gpu_hours'] != config['cumulative_cap_GPUh']
            or pool['origin_used_gpu_hours'] != config['budget_origin_used_GPUh']
            or any(pool[k] != v for k, v in BudgetPool.accounting(pool).items())
            or job['status'] != 'SETTLED' or job['actual_GPUh'] != bill['actual_GPUh']
            or job['billing_sha256'] != value['billing_sha256']
            or job['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or job['forecast_GPUh'] != config['forecast_complete_GPUh']
            or job['scope_counts'] != config['scope_counts']
            or job['production_CPU_sha256'] != launch['production_CPU_sha256']
            or job['bound_input_fingerprint'] != launch['bound_input_fingerprint']
            or any(job[k] != launch[k] for k in ('source_revision', 'launch_id', 'gpu_uuid', 'config_sha256'))):
        raise ValueError('Unchanged original v2 window and additive one-job settlement required')
    if config['billed_limit_GPUh'] >= 12 and (job['kind'] != 'V2_SPECIFIC_WHOLE_CARD_APPROVAL'
            or job['authorization_sha256'] != launch['authorization_sha256']):
        raise ValueError('The original large-card settlement must retain its exact specific approval')
    if (not value['own_UUID_lock_free'] or value['own_GPU'].split(',')[0].strip() != launch['gpu_uuid']
            or any(line.split(',')[0].strip() == launch['gpu_uuid']
                   for line in value['compute_apps'].splitlines() if line.strip())):
        raise ValueError('Own UUID must be released; other GPUs are independent')
    if (post['status'] != 'N07_SHARED180_POST_CPU_TERMINAL'
            or post['original_supervisor'] != {k: launch['supervisor_identity'][k] for k in ('pid', 'start_ticks')}
            or post['source_revision'] != launch['source_revision']
            or post['config_sha256'] != launch['config_sha256']
            or post['final_result_sha256'] != value['final_sha256']):
        raise ValueError('Original CPU post exit and final result identity required')
    if (final['source_revision'] != launch['source_revision']
            or final['config_sha256'] != launch['config_sha256']
            or final['bound_input_fingerprint'] != launch['bound_input_fingerprint']
            or final['scope_counts'] != config['scope_counts']
            or final['GPU_supervisor'] != supervisor
            or final['GPU_submissions'] or final['ledger_written'] or final['CUDA_initialized']):
        raise ValueError('CPU audit cannot change the original GPU scope or budget')
    if final['status'] == 'N07_SHARED180_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED':
        return dict(status='N07_CPU_TECHNICAL_FAILURE_RETAINED_READONLY_REPAIR_REQUIRED',
            scientific_full_scope_accepted=False, actual_GPUh=bill['actual_GPUh'],
            original_GPU_finance_released=True, original_CPU_error=final.get('CPU_terminal_error'),
            no_GPU_relaunch_authorized=True, GPU_submissions=0, SSH_queries=0)
    runner = value.get('runner', {'runs': []})
    if value.get('runner'):
        if (supervisor['runner_sha256'] != value['runner_sha256']
                or runner['source_revision'] != launch['source_revision']
                or runner['config_sha256'] != launch['config_sha256']
                or runner['bound_input_fingerprint'] != launch['bound_input_fingerprint']
                or runner['scope_counts'] != config['scope_counts'] or runner['matrix'] != plan
                or runner['cases'] != bound['cases'] or runner['methods'] != bound['method_ids']):
            raise ValueError('Original runner receipt differs from its terminal supervisor')
        if supervisor['child_exit_code'] == 0 and (runner['model_load_calls'] != 1 or runner['model_loads_completed'] != 1):
            raise ValueError('A complete card must retain its one resident model construction')
    original_rows = full_rows(runner['runs'], plan)
    rows = final['rows']
    if len(rows) != 180 or [r['id'] for r in rows] != [r['id'] for r in original_rows]:
        raise ValueError('Keep all180 original positions in the original order')
    inventory = {r['path']: r for r in final['artifact_inventory']}
    if len(inventory) != len(final['artifact_inventory']): raise ValueError('Duplicate artifact inventory path')
    for row, original, planned in zip(rows, original_rows, plan):
        if any(row.get(k) != v for k, v in original.items()):
            raise ValueError('CPU post changed an original generation outcome or runtime receipt')
        if row.get('raw_model_audit') == 'PASS':
            audit_row(row, planned, bound)
            original_asset(row['final_artifact'], inventory, value['output_root'])
            if row['section'] == 'WARMUP':
                original_asset(row['warm_guided_artifact'], inventory, value['output_root'])
        if row.get('endpoint_audit') == 'PASS':
            artifact = row['video_artifact']
            if (row['status'] != 'COMPLETE' or row.get('raw_model_audit') != 'PASS'
                    or [artifact['frames'], artifact['fps'], artifact['width'], artifact['height']] != [93, 16, 768, 432]
                    or len(artifact['decoded_rgb_sha256']) != 93
                    or not all(digest(v) for v in artifact['decoded_rgb_sha256'])
                    or not digest(row['decoded_video']['RGB_sha256'])):
                raise ValueError('All93 RGB identities and the original raw result required')
            original_asset(artifact, inventory, value['output_root'])
    controls = final['warm_repeat_controls']
    if len(controls) != 10 or [r['method'] for r in controls] != bound['method_ids']:
        raise ValueError('All ten original warm equivalence controls required')
    for control in controls:
        if control['status'] != 'PASS': continue
        method = control['method']
        arms = [next(r for r in rows if r['id'] == f'warm_{repeat}_{method}') for repeat in (1, 2)]
        arms.append(next(r for r in rows if r['section'] == 'TIMED'
                         and r['case_id'] == arms[0]['case_id'] and r['method'] == method))
        if (control['all_guided_outputs_equal'] != point(method)['actual_updates']
                or arms[0]['warm_guided_tree_sha256'] != arms[1]['warm_guided_tree_sha256']
                or not control['all93_RGB_equal'] or any(r.get('endpoint_audit') != 'PASS' for r in arms)):
            raise ValueError('Original full warm guided/RGB acceptance differs')
        for other in arms[1:]:
            if any(other.get(k) != arms[0].get(k) for k in ('final_latent_sha256', 'actions', 'A_history', 'scheduler_timesteps')):
                raise ValueError('Original warm/formal endpoint actions or history differs')
            if (stable_history(other.get('source_history')) != stable_history(arms[0].get('source_history'))
                    or other['decoded_video']['RGB_sha256'] != arms[0]['decoded_video']['RGB_sha256']
                    or other['video_artifact']['decoded_rgb_sha256'] != arms[0]['video_artifact']['decoded_rgb_sha256']):
                raise ValueError('Original warm/formal physical source or RGB differs')
    recomputed = summarize(copy.deepcopy(final), bound, observed_paths=len(runner['runs']),
        child_exit_code=supervisor['child_exit_code'], bootstrap_repetitions=bootstrap_repetitions)
    if any(fingerprint(final.get(k)) != fingerprint(v) for k, v in recomputed.items()):
        raise ValueError('Independent all-frame, both-seed prompt-grouped statistics or denominator differs')
    accepted = final['status'] == COMPLETE_STATUS and post['exit_code'] == 0
    if final['status'] == COMPLETE_STATUS and not accepted:
        raise ValueError('A failed CPU post cannot be a full scientific acceptance')
    return dict(status='N07_FROZEN_SHARED180_INDEPENDENT_RECEIPT_ACCEPTED' if accepted else
                'N07_FROZEN_SHARED180_TERMINAL_ISSUES_OR_REJECTIONS_RETAINED',
        scientific_full_scope_accepted=accepted, original_terminal_status=final['status'],
        terminal_receipt_audit_accepted=True,
        scientific_available_cohorts_with_registered_missingness=(post['exit_code'] == 0 and final['status'] in (
            COMPLETE_STATUS, 'N07_SHARED180_FULL_SCOPE_REJECTIONS_OR_MISSING_CONTROLS_RETAINED')),
        source_revision=launch['source_revision'], actual_GPUh=bill['actual_GPUh'],
        scope_counts=config['scope_counts'], original_runner_paths=len(runner['runs']),
        original_status_counts={s: sum(r['status'] == s for r in rows)
            for s in ('COMPLETE', 'TEXT_REJECTED', 'VIDEO_REJECTED', 'TECH_FAILED', 'NOT_REACHED')},
        accepted_scientific_videos=recomputed['accepted_scientific_videos'],
        scored_scientific_videos=recomputed['scored_scientific_videos'],
        grouped_statistics=recomputed['grouped_statistics'],
        original_tensor_and_video_audit='PINNED_REMOTE_CPU_POST_RECEIPTS_NO_LOCAL_BULK_ARTIFACT_REDOWNLOAD',
        aggregate_and_original_receipt_independently_recomputed=True, own_GPU_and_finance_released=True,
        original_CPU_post_exit_code=post['exit_code'], audit_failures=copy.deepcopy(final['audit_failures']),
        stable_repeated_clean_speed_claim=False, physics_quality_claim=False,
        no_test_winner_selection=True, GPU_submissions=0, SSH_queries=0, ledger_written=False)
