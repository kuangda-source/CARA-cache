"""Independent full40 receipt, all-frame statistics and original-cost checks."""
import copy
import math

from .balanced_repeat_cpu_acceptance_r1 import validate_bundle, validate_proof
from .balanced_repeat_execution_r1 import COUNTS, full_rows, observed_timers
from .balanced_repeat_production_r1 import RUN, validate_contract, validate_launch_authority
from .balanced_repeat_post_r1 import (
    COMPLETE_STATUS, GPU_TERMINAL_STATUS, metadata_audit, repeat_controls,
    registered_interval_overlaps, summarize,
)
from .frozen_shared_acceptance_r1 import digest, original_alive, original_asset
from .frozen_shared_production_r1 import fingerprint
from .gpu_budget_pool_v2 import BudgetPool


def resource_controls(runner, plan, pool, start, end):
    """Recorded boundaries plus complete registered GPU intervals, not all OS activity."""
    expected = [('BEFORE_LOAD', None)]
    for row in plan: expected.extend([('BEFORE_PATH', row['id']), ('AFTER_PATH', row['id'])])
    expected.append(('AFTER_ALL', None))
    observations = runner.get('resource_observations', [])
    identity = [(r.get('section'), r.get('id')) for r in observations]
    fields_ok = identity == expected and all(
        isinstance(r.get('unix'), (int, float)) and math.isfinite(r['unix']) and start <= r['unix'] <= end
        and r.get('other_registered_GPU_jobs_active') == []
        and r.get('project_CPU_metric_entrypoints') == []
        and r.get('observation_only_not_entire_interval_cleanliness') is True for r in observations)
    interval = registered_interval_overlaps(pool, RUN, start, end)
    return dict(registered_boundary_observations=82, observed_boundary_observations=len(observations),
        recorded_boundaries_all_clear=fields_ok, **interval,
        recorded_clean_resource_controls_accepted=fields_ok and interval['no_recorded_GPU_overlap'])


def accept(value, launch):
    if (value['status'] != 'N08_FULL40_ORIGINAL_ONCE_CAPTURE' or value['mode'] != 'terminal'
            or value['launch'] != launch or launch['run_id'] != RUN
            or value['registration_sha256'] != launch['registration_sha256']
            or value['registration']['source_revision'] != launch['source_revision']
            or set(value['payload_verified']) != set(value['registration']['payload_sha256'])
            or not value['payload_verified'] or not all(v is True for v in value['payload_verified'].values())
            or value['observed_unix'] < launch['next_check_not_before_unix']):
        raise ValueError('Original full40 post-ETA launch, payload and source identity required')
    processes = value['original_processes']; supervisor = value.get('supervisor', {})
    live = dict(supervisor=original_alive(launch['supervisor_identity'], processes.get('supervisor_pid')),
        child=original_alive(supervisor.get('child_identity'), processes.get('child_pid')),
        post=original_alive(launch.get('post_watcher_identity'), processes.get('post_watcher_pid')))
    if any(live.values()):
        return dict(status='N08_ORIGINAL_TASK_STILL_RUNNING_REESTIMATE_ONCE_NO_RESTART',
            original_live_handles=live, original_runner_paths=len(value.get('runner', {}).get('runs', [])),
            scientific_full_scope_accepted=False, GPU_submissions=0, SSH_queries=0)
    if not supervisor or 'post_exit' not in value or 'final' not in value:
        return dict(status='N08_ORIGINAL_TERMINAL_RECEIPT_MISSING_TECHNICAL_REPAIR_REQUIRED',
            scientific_full_scope_accepted=False, original_admission_failure=value.get('admission_failure'),
            original_supervisor_fallback=value.get('supervisor_fallback'),
            original_billing_fallback=value.get('billing_fallback'),
            no_GPU_relaunch_authorized=True, GPU_submissions=0, SSH_queries=0)
    config, protocol, shared, freeze = [value[k] for k in ('config', 'timing_protocol', 'shared_config', 'method_freeze')]
    bound = validate_contract(config, protocol, shared, freeze)
    if config['references']['method_freeze'] != shared['references']['method_freeze']:
        raise ValueError('N07 and N08 must retain the same original method-freeze SHA')
    for key in ('timing_protocol', 'shared_config', 'method_freeze'):
        if value[key + '_sha256'] != config['references'][key]['sha256']:
            raise ValueError('Original frozen timing reference differs: ' + key)
    if (value['config_sha256'] != launch['config_sha256']
            or fingerprint(bound) != launch['bound_timing_fingerprint']
            or launch['bound_input_fingerprint'] != launch['bound_timing_fingerprint']
            or value['production_CPU_sha256'] != launch['production_CPU_sha256']
            or value['authorization_sha256'] != launch['authorization_sha256']):
        raise ValueError('Original input/order, CPU or whole-card authority differs')
    proof, authority = value['production_CPU'], value['authorization']
    validate_bundle(value['production_CPU_bundle'], launch['source_revision'])
    validate_proof(proof, config, bound, value['registration'],
        registration_sha256=value['registration_sha256'], config_sha256=value['config_sha256'])
    validate_launch_authority(config, bound, value['registration'], proof, authority,
        revision=launch['source_revision'], gpu_uuid=launch['gpu_uuid'], config_sha256=value['config_sha256'],
        proof_sha256=value['production_CPU_sha256'], registration_sha256=value['registration_sha256'])
    keys = ('source_revision', 'launch_id', 'run_id', 'gpu_uuid', 'scope_counts', 'config_sha256',
            'bound_timing_fingerprint', 'registration_sha256')
    if (supervisor['status'] != GPU_TERMINAL_STATUS or supervisor['pid'] != launch['supervisor_identity']['pid']
            or supervisor['start_ticks'] != launch['supervisor_identity']['start_ticks']
            or any(supervisor[k] != launch[k] for k in keys)):
        raise ValueError('Exact original full40 supervisor and terminal scope required')
    bill, pool, post, final = [value[k] for k in ('billing', 'pool', 'post_exit', 'final')]
    if (bill['status'] != 'N08_FULL40_ACTUAL_GPU_BILL' or not bill['original_output_root_available']
            or any(bill[k] != launch[k] for k in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid', 'scope_counts', 'config_sha256'))
            or bill['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or not isinstance(bill['actual_GPUh'], (int, float)) or not math.isfinite(bill['actual_GPUh'])
            or not 0 < bill['actual_GPUh'] <= bill['billed_limit_GPUh']
            or not math.isclose(bill['wall_seconds'] / 3600, bill['actual_GPUh'], rel_tol=1e-12)
            or supervisor['billing_sha256'] != value['billing_sha256'] or supervisor['actual_GPUh'] != bill['actual_GPUh']):
        raise ValueError('Original entire load/warm/formal/maintenance bill required')
    job = pool['jobs'][RUN]
    if (pool['cap_gpu_hours'] != config['cumulative_cap_GPUh']
            or pool['origin_used_gpu_hours'] != config['budget_origin_used_GPUh']
            or any(pool[k] != v for k, v in BudgetPool.accounting(pool).items())
            or job['status'] != 'SETTLED' or job['actual_GPUh'] != bill['actual_GPUh']
            or job['billing_sha256'] != value['billing_sha256']
            or job['billed_limit_GPUh'] != config['billed_limit_GPUh']
            or job['forecast_GPUh'] != config['forecast_complete_GPUh']
            or job['scope_counts'] != COUNTS or job['production_CPU_sha256'] != launch['production_CPU_sha256']
            or job['bound_input_fingerprint'] != launch['bound_timing_fingerprint']
            or job['bound_timing_fingerprint'] != launch['bound_timing_fingerprint']
            or any(job[k] != launch[k] for k in ('source_revision', 'launch_id', 'gpu_uuid', 'config_sha256'))):
        raise ValueError('Original unchanged v2 window and additive whole-job settlement required')
    if config['billed_limit_GPUh'] >= 12 and (job['kind'] != 'V2_SPECIFIC_WHOLE_CARD_APPROVAL'
            or job['authorization_sha256'] != launch['authorization_sha256']):
        raise ValueError('Original specific large-card approval must survive settlement')
    if (not value['own_UUID_lock_free'] or value['own_GPU'].split(',')[0].strip() != launch['gpu_uuid']
            or any(line.split(',')[0].strip() == launch['gpu_uuid'] for line in value['compute_apps'].splitlines() if line.strip())):
        raise ValueError('Own original UUID lease and compute process must be released')
    if (post['status'] != 'N08_FULL40_POST_CPU_TERMINAL'
            or post['original_supervisor'] != {k: launch['supervisor_identity'][k] for k in ('pid', 'start_ticks')}
            or post['source_revision'] != launch['source_revision'] or post['config_sha256'] != launch['config_sha256']
            or post['final_result_sha256'] != value['final_sha256']):
        raise ValueError('Original post exit and its full40 final identity required')
    if (final['source_revision'] != launch['source_revision'] or final['config_sha256'] != launch['config_sha256']
            or final['bound_timing_fingerprint'] != launch['bound_timing_fingerprint']
            or final['scope_counts'] != COUNTS or final['GPU_supervisor'] != supervisor
            or final['GPU_submissions'] or final['ledger_written'] or final['CUDA_initialized']):
        raise ValueError('CPU post cannot alter GPU outcomes, source, scope or costs')
    if final['status'] == 'N08_FULL40_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED':
        return dict(status='N08_CPU_TECHNICAL_FAILURE_READONLY_REPAIR_REQUIRED',
            scientific_full_scope_accepted=False, original_GPU_finance_released=True,
            actual_GPUh=bill['actual_GPUh'], original_CPU_error=final.get('CPU_terminal_error'),
            no_GPU_relaunch_authorized=True, GPU_submissions=0, SSH_queries=0)
    runner = value.get('runner', {'runs': []})
    if value.get('runner'):
        if (supervisor['runner_sha256'] != value['runner_sha256']
                or runner['source_revision'] != launch['source_revision'] or runner['config_sha256'] != launch['config_sha256']
                or runner['bound_timing_fingerprint'] != launch['bound_timing_fingerprint']
                or runner['scope_counts'] != COUNTS or runner['matrix'] != bound['execution_plan']
                or runner['bindings'] != bound['bindings']):
            raise ValueError('Original resident-model runner differs')
        if supervisor['child_exit_code'] == 0 and (runner['model_load_calls'] != 1 or runner['model_loads_completed'] != 1):
            raise ValueError('A complete full40 must construct exactly one resident model')
    original = full_rows(runner['runs'], bound); rows = final['rows']
    if len(rows) != 40 or [r['id'] for r in rows] != [r['id'] for r in original]:
        raise ValueError('All original40 positions and order must survive CPU post')
    inventory = {a['path']: a for a in final['artifact_inventory']}
    if len(inventory) != len(final['artifact_inventory']): raise ValueError('Duplicate original artifact path')
    for row, before, planned in zip(rows, original, bound['execution_plan']):
        if not set(before).issubset(row) or any(row[k] != v for k, v in before.items()):
            raise ValueError('CPU post changed an original generation or timing observation')
        if row.get('raw_model_audit') == 'PASS':
            metadata_audit(row, planned, bound)
            original_asset(row['final_artifact'], inventory, value['output_root'])
            if not digest(row['final_latent_sha256']): raise ValueError('Original latent tree SHA required')
            if row['timing_intervals'] != observed_timers(row): raise ValueError('Recorded timer interval view differs')
            if row['section'] == 'WARMUP':
                original_asset(row['warm_guided_artifact'], inventory, value['output_root'])
                if not digest(row['warm_guided_tree_sha256']): raise ValueError('Original full36 guided tree SHA required')
        if row.get('endpoint_audit') == 'PASS':
            asset = row['video_artifact']
            if (row['status'] != 'COMPLETE' or row.get('raw_model_audit') != 'PASS'
                    or [asset['frames'], asset['fps'], asset['width'], asset['height']] != [93, 16, 768, 432]
                    or len(asset['decoded_rgb_sha256']) != 93 or not all(digest(h) for h in asset['decoded_rgb_sha256'])
                    or not digest(row['decoded_video']['RGB_sha256'])):
                raise ValueError('Complete93 RGB identities and original raw result required')
            original_asset(asset, inventory, value['output_root'])
    warm, repeated, control_failures = repeat_controls(rows, bound)
    if (final['warm_trace_controls'] != warm or final['formal_to_warm_controls'] != repeated
            or any(f not in final['audit_failures'] for f in control_failures)):
        raise ValueError('Independent all10 warm/all30 formal parity reconstruction differs')
    recomputed = summarize(copy.deepcopy(final), bound, observed_paths=len(runner['runs']), child_exit_code=supervisor['child_exit_code'])
    if any(fingerprint(final.get(k)) != fingerprint(v) for k, v in recomputed.items()):
        raise ValueError('Independent per-frame, per-round or full-cohort statistics differs')
    raw_accepted = final['status'] == COMPLETE_STATUS and post['exit_code'] == 0
    if final['status'] == COMPLETE_STATUS and not raw_accepted: raise ValueError('Failed CPU post cannot be full acceptance')
    if final['resource_boundary_observations'] != runner.get('resource_observations', []):
        raise ValueError('CPU post changed original resource observations')
    resources = resource_controls(runner, bound['execution_plan'], pool, supervisor['started_unix'], bill['ended_unix'])
    speed_accepted = raw_accepted and resources['recorded_clean_resource_controls_accepted']
    return dict(status=('N08_FULL40_RAW_FIDELITY_AND_REPEATED_LATENCY_INDEPENDENTLY_ACCEPTED' if speed_accepted else
        'N08_FULL40_RAW_FIDELITY_ACCEPTED_SPEED_RESOURCES_UNACCEPTED' if raw_accepted else
        'N08_FULL40_TERMINAL_ISSUES_OR_REJECTIONS_RETAINED'),
        scientific_full_scope_accepted=speed_accepted, full_raw_and_fidelity_scope_accepted=raw_accepted,
        stable_repeated_clean_speed_claim=speed_accepted, terminal_receipt_audit_accepted=True,
        timing_interpretation='REGISTERED_REPEATED_LATENCY_WITH_RECORDED_RESOURCE_CONTROLS' if speed_accepted else 'DIAGNOSTIC_NOT_ACCEPTED_CLEAN_LATENCY',
        resource_controls=resources, source_revision=launch['source_revision'], actual_GPUh=bill['actual_GPUh'],
        scope_counts=COUNTS.copy(), original_runner_paths=len(runner['runs']),
        original_status_counts={s: sum(r['status'] == s for r in rows) for s in ('COMPLETE', 'TEXT_REJECTED', 'VIDEO_REJECTED', 'TECH_FAILED', 'NOT_REACHED')},
        accepted_scientific_videos=recomputed['accepted_scientific_videos'], scored_scientific_videos=recomputed['scored_scientific_videos'],
        timing_statistics=recomputed['timing_statistics'], all_formal_observations=recomputed['all_formal_observations'],
        original_CPU_post_exit_code=post['exit_code'], audit_failures=copy.deepcopy(final['audit_failures']),
        aggregate_and_original_observations_independently_recomputed=True,
        tensor_and_RGB_audit='PINNED_ORIGINAL_CPU_POST_NO_LOCAL_BULK_REDOWNLOAD',
        own_GPU_and_finance_released=True, independent_new_input_generalization_claim=False,
        GPU_submissions=0, SSH_queries=0, ledger_written=False)
