"""Read-only N09 full40 tensor, RGB, scalar-profile and request-memory audit.

Diagnostic modes remain separate. No clean-speed estimate or action unit price
is derived from inclusive component intervals or from an unselected action.
"""
import copy
import json
import math

from .frozen_shared_post_r1 import artifact_path, failure, stable_history
from .frozen_shared_production_r1 import number
from .runtime_profile40_execution_r1 import COUNTS, audit_row, full_rows

GPU_TERMINAL_STATUS = 'N09_FULL40_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
COMPLETE_STATUS = 'N09_FULL40_RAW_RGB_PROFILE_MEMORY_AUDITED_NOT_CLEAN_LATENCY'
SEMANTICS = 'INCLUSIVE_CURRENT_STREAM_INTERVALS_NOT_ADDITIVE_PURE_KERNEL_COSTS'
MEMORY_FIELDS = ('allocated_bytes', 'reserved_bytes', 'peak_allocated_bytes', 'peak_reserved_bytes')
COMPONENTS = frozenset(('complete_request_inclusive', 'shallow_block', 'deep_block', 'output_head',
    'solver_update', 'VAE_decode', 'input_preparation_inclusive', 'method_install_inclusive',
    'policy_decide', 'policy_commit', 'policy_commit_protected_dense', 'correction_warp',
    'correction_to_velocity', 'request_boundary_GC', 'video_write'))


def metadata_audit(row, planned, bound):
    timers = audit_row(row, planned, bound)
    from .frozen_shared_acceptance_r1 import digest
    state = row['pre_request_state_identity']
    if (not digest(state['original_state_sha256'])
            or state['original_state_sha256'] != state['restored_state_sha256']
            or state['shared_eval_verified'] is not True
            or row['profile_control_mode'] != planned['mode']
            or row['clean_repeated_latency_claim'] is not False
            or row.get('timing_intervals') != timers):
        raise ValueError('Original restored state, eval and diagnostic mode required')


def audit_payload(row, planned, bound, root, *, expected_shape=(1, 16, 24, 54, 96)):
    """Reuse the original finite tensor audit through an explicit local mapping."""
    from .frozen_shared_post_r1 import audit_payload as original
    metadata_audit(row, planned, bound)
    mapped_plan = {**planned, 'case_id': planned['scene'],
                   'section': 'WARMUP' if planned['audit_guided'] else 'TIMED'}
    mapped_row = {**row, **mapped_plan}
    if planned['audit_guided']:
        if row['guided_outputs'] != 36 or row['warm_guided_outputs'] != 36:
            raise ValueError('Each original audit mode needs all36 real guided tensors')
        mapped_row.update(warm_guided_artifact=row['guided_artifact'],
                          warm_guided_tree_sha256=row['guided_tree_sha256'])
    elif any(k in row for k in ('guided_artifact', 'guided_tree_sha256', 'guided_outputs')):
        raise ValueError('Lean requests cannot acquire research guided artifacts')
    original(mapped_row, mapped_plan,
        {'cases': [dict(id=r['name'], seed=r['seed']) for r in bound['requests']]},
        root, expected_shape=expected_shape)


def audit_memory(row, *, expected_device='cuda:0'):
    value = row['request_memory_observation']
    if (set(value) != {'device', 'memory_before', 'memory_after',
                      'peak_reset_before_request', 'request_profile_wall_seconds'}
            or value['device'] != expected_device
            or not number(value['request_profile_wall_seconds'])
            or value['request_profile_wall_seconds'] <= 0):
        raise ValueError('Explicit original request memory boundary and finite wall interval required')
    cuda = expected_device.startswith('cuda:')
    if expected_device != 'cpu' and not cuda:
        raise ValueError('Only explicit visible CUDA device or a CPU control is permitted')
    if value['peak_reset_before_request'] is not cuda:
        raise ValueError('Reset peaks after model residency and before each CUDA request')
    for which in ('memory_before', 'memory_after'):
        cell = value[which]
        if set(cell) != set(MEMORY_FIELDS) | {'available'} or cell['available'] is not cuda:
            raise ValueError('All four original allocator observations required')
        if not cuda:
            if any(cell[k] is not None for k in MEMORY_FIELDS):
                raise ValueError('Unavailable CPU memory is null, never a zero GPU measurement')
            continue
        if (any(type(cell[k]) is not int or cell[k] < 0 for k in MEMORY_FIELDS)
                or cell['reserved_bytes'] < cell['allocated_bytes']
                or cell['peak_reserved_bytes'] < cell['peak_allocated_bytes']
                or cell['peak_allocated_bytes'] < cell['allocated_bytes']
                or cell['peak_reserved_bytes'] < cell['reserved_bytes']):
            raise ValueError('Original nonnegative allocator values or peak bounds differ')
    if cuda and any(value['memory_after'][k] < value['memory_before'][k]
                    for k in ('peak_allocated_bytes', 'peak_reserved_bytes')):
        raise ValueError('One request peak cannot decrease without another reset')
    return copy.deepcopy(value)


def audit_profile(row, planned, root, *, expected_device='cuda:0', probe_depth=2):
    value = (json.loads(artifact_path(root, row['component_profile_artifact']).read_text())
             if planned['component_profile'] else None)
    return audit_profile_value(row, planned, value, expected_device=expected_device, probe_depth=probe_depth)


def audit_profile_value(row, planned, value, *, expected_device='cuda:0', probe_depth=2):
    """Recompute every component count/sum from the original scalar intervals."""
    if not planned['component_profile']:
        if any(k in row for k in ('component_profile_artifact', 'profile_components')):
            raise ValueError('Original audit controls must not contain component observations')
        return None
    memory = audit_memory(row, expected_device=expected_device)
    if (set(value) != {'status', 'device', 'request_profile_wall_seconds', 'memory_before',
            'memory_after', 'peak_reset_before_request', 'components', 'intervals',
            'interval_semantics', 'multi_stream_work_not_attributed', 'no_inner_profiler_synchronize',
            'scalar_records_only', 'timing_claim', 'no_direct_post_probe_action_price_claim'}
            or value['status'] != 'PROFILE_COMPLETE'
            or value['interval_semantics'] != SEMANTICS
            or value['timing_claim'] != 'INSTRUMENTED_PROFILE_NOT_CLEAN_LATENCY'
            or any(value[k] is not True for k in ('multi_stream_work_not_attributed',
                'no_inner_profiler_synchronize', 'scalar_records_only', 'no_direct_post_probe_action_price_claim'))
            or any(value[k] != memory[k] for k in memory)
            or value['components'] != row['profile_components']
            or not isinstance(value['intervals'], list) or not value['intervals']):
        raise ValueError('Original profile schema, device, memory, mode or interval semantics differs')
    cuda = expected_device.startswith('cuda:')
    components = {}
    for index, span in enumerate(value['intervals']):
        parent = span['parent']
        if (set(span) != {'id', 'parent', 'component', 'outcome', 'CPU_seconds', 'CUDA_elapsed_ms'}
                or type(span['id']) is not int or span['id'] != index
                or (parent is not None and (type(parent) is not int or not 0 <= parent < index))
                or span['component'] not in COMPONENTS
                or not isinstance(span['outcome'], str) or not span['outcome']
                or span['outcome'] == 'RUNNING'
                or not number(span['CPU_seconds']) or span['CPU_seconds'] < 0
                or (cuda and (not number(span['CUDA_elapsed_ms']) or span['CUDA_elapsed_ms'] < 0))
                or (not cuda and span['CUDA_elapsed_ms'] is not None)):
            raise ValueError('Original ordered finite scalar interval and existing component required')
        if (index == 0 and (parent is not None or span['component'] != 'complete_request_inclusive')):
            raise ValueError('The original complete-request span must be the root')
        if index and (parent is None or span['component'] == 'complete_request_inclusive'):
            raise ValueError('Every component belongs to the single original request root')
        cell = components.setdefault(span['component'], dict(calls=0, inclusive_CPU_seconds=0.,
            inclusive_CUDA_ms=0. if cuda else None, exceptions=0))
        cell['calls'] += 1
        cell['inclusive_CPU_seconds'] += span['CPU_seconds']
        if cuda: cell['inclusive_CUDA_ms'] += span['CUDA_elapsed_ms']
        cell['exceptions'] += span['outcome'] != 'RETURNED'
    if set(components) != set(value['components']):
        raise ValueError('No absent or invented component sums are permitted')
    for name, computed in components.items():
        recorded = value['components'][name]
        if (set(recorded) != set(computed)
                or type(recorded['calls']) is not int or recorded['calls'] != computed['calls']
                or type(recorded['exceptions']) is not int or recorded['exceptions'] != computed['exceptions']):
            raise ValueError('Recompute component and exception counts from original intervals')
        for field in ('inclusive_CPU_seconds', 'inclusive_CUDA_ms'):
            a, b = recorded[field], computed[field]
            if b is None:
                if a is not None: raise ValueError('CPU controls have no CUDA interval')
            elif not number(a) or not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10):
                raise ValueError('Recomputed inclusive component interval differs')
    counts = {name: cell['calls'] for name, cell in components.items()}
    if row['status'] in ('COMPLETE', 'VIDEO_REJECTED'):
        required = dict(shallow_block=2 * 36 * probe_depth, solver_update=36,
                        VAE_decode=1, method_install_inclusive=1)
        if (type(probe_depth) is not int or not 0 < probe_depth < 28
                or any(counts.get(k, 0) != n for k, n in required.items())
                or counts.get('output_head', 0) < 72
                or counts.get('video_write', 0) != (1 if row['status'] == 'COMPLETE' else 0)):
            raise ValueError('Actual full36 CFG/probe/solver/decode/write observations required')
    return dict(interval_count=len(value['intervals']), components=components,
        interval_semantics=SEMANTICS, timing_claim=value['timing_claim'],
        request_memory_observation=memory, no_direct_post_probe_action_price_claim=True)


def audit_rows(runs, bound, payload_auditor, video_inspector, profile_auditor, *,
               expected_device='cuda:0', save=lambda result: None):
    rows = copy.deepcopy(full_rows(runs, bound))
    result = dict(rows=rows, audit_failures=[])
    for row, planned in zip(rows, bound['execution_plan']):
        if row['status'] in ('TECH_FAILED', 'NOT_REACHED'):
            save(result); continue
        if row['status'] not in ('COMPLETE', 'VIDEO_REJECTED', 'TEXT_REJECTED'):
            raise ValueError('Original full40 terminal generation outcomes required')
        try:
            if row['status'] == 'TEXT_REJECTED':
                metadata_audit(row, planned, bound)
                if any(k in row for k in ('guided_artifact', 'final_artifact', 'video_path')):
                    raise ValueError('Text rejection cannot contain generated artifacts')
                row['raw_model_audit'] = 'NOT_APPLICABLE_TEXT_REJECTION_RETAINED'
            else:
                payload_auditor(row, planned, bound); row['raw_model_audit'] = 'PASS'
        except Exception as error:
            row['raw_model_audit'] = 'AUDIT_FAILURE_RETAINED'
            result['audit_failures'].append(failure('RAW_MODEL_OR_IDENTITY', row, error))
        for kind, field, observe in (
                ('REQUEST_MEMORY', 'request_memory_audit', lambda: audit_memory(row, expected_device=expected_device)),
                ('COMPONENT_PROFILE', 'component_profile_audit', lambda: profile_auditor(row, planned))):
            try:
                checked = observe(); row[field] = 'PASS'
                if field == 'component_profile_audit' and checked is not None:
                    row['audited_component_profile'] = checked
            except Exception as error:
                row[field] = 'AUDIT_FAILURE_RETAINED'
                result['audit_failures'].append(failure(kind, row, error))
        if row['status'] != 'COMPLETE':
            row['endpoint_audit'] = 'NOT_APPLICABLE_' + row['status'] + '_RETAINED'
        elif row.get('raw_model_audit') != 'PASS':
            row['endpoint_audit'] = 'RAW_MODEL_AUDIT_FAILED_RETAINED'
        else:
            try:
                row.update(video_inspector(row)); row['endpoint_audit'] = 'PASS'
            except Exception as error:
                row['endpoint_audit'] = 'AUDIT_FAILURE_RETAINED'
                result['audit_failures'].append(failure('VIDEO_CONTAINER_OR_RGB', row, error))
        save(result)
    return result


def parity_controls(rows, bound):
    """Compare all10 original/profile traces and all10 profile/lean endpoints."""
    lookup = {(r['scene'], r['slot'], r['round']): r for r in rows}
    controls = {name: [] for name in ('warm_to_original_controls',
        'original_to_profile_all36_controls', 'profile_to_lean_controls')}
    failed = []
    for request in bound['requests']:
        for slot in bound['bindings']:
            for name, first, second in (('warm_to_original_controls', 0, 1),
                    ('original_to_profile_all36_controls', 1, 2), ('profile_to_lean_controls', 2, 3)):
                left, right = (lookup[(request['name'], slot, n)] for n in (first, second))
                control = dict(scene=request['name'], slot=slot, left_id=left['id'], right_id=right['id'],
                    raw_endpoint_actions_history_equal=False, all93_RGB_equal=False,
                    all36_guided_tree_equal=False, status='ORIGINAL_CONTROL_UNAVAILABLE_RETAINED')
                controls[name].append(control)
                if any(r.get('raw_model_audit') != 'PASS' for r in (left, right)):
                    continue
                try:
                    for key in ('final_latent_sha256', 'actions', 'A_history', 'scheduler_timesteps',
                                'pre_request_state_identity'):
                        if left.get(key) != right.get(key):
                            raise ValueError('Original same-method state, endpoint, actions or A history differs: ' + key)
                    if stable_history(left.get('source_history')) != stable_history(right.get('source_history')):
                        raise ValueError('Original physical source history differs')
                    control['raw_endpoint_actions_history_equal'] = True
                    if first in (0, 1):
                        if (left.get('guided_outputs') != 36 or right.get('guided_outputs') != 36
                                or left.get('guided_tree_sha256') != right.get('guided_tree_sha256')):
                            raise ValueError('All36 original guided tensors must match between audit modes')
                        control['all36_guided_tree_equal'] = True
                    if all(r.get('endpoint_audit') == 'PASS' for r in (left, right)):
                        if (left['decoded_video']['RGB_sha256'] != right['decoded_video']['RGB_sha256']
                                or left['video_artifact']['decoded_rgb_sha256'] != right['video_artifact']['decoded_rgb_sha256']):
                            raise ValueError('All93 decoded RGB frames differ between original diagnostic modes')
                        control.update(status='PASS', all93_RGB_equal=True)
                    else:
                        control['status'] = 'RAW_EQUAL_RGB_CONTROL_UNAVAILABLE_RETAINED'
                except Exception as error:
                    control['status'] = 'PARITY_FAILURE_RETAINED'
                    failed.append(failure(name, right, error))
    if any(len(group) != 10 for group in controls.values()):
        raise ValueError('All ten original scene/method groups required for every control')
    return controls, failed


def summarize(result, bound, *, observed_paths, child_exit_code):
    rows = result['rows']
    if len(rows) != 40 or bound['scope_counts'] != COUNTS or type(observed_paths) is not int:
        raise ValueError('Keep every original full40/30formal/10warm position')
    names = ('warm_to_original_controls', 'original_to_profile_all36_controls', 'profile_to_lean_controls')
    all_controls = [c for name in names for c in result[name]]
    if any(len(result[name]) != 10 for name in names):
        raise ValueError('All registered mode controls must be reported')
    incomplete = observed_paths != 40 or child_exit_code != 0 or any(
        r['status'] in ('TECH_FAILED', 'NOT_REACHED') for r in rows)
    all_ok = (all(r.get(k) == 'PASS' for r in rows for k in (
        'raw_model_audit', 'endpoint_audit', 'request_memory_audit', 'component_profile_audit'))
        and all(c['status'] == 'PASS' for c in all_controls))
    status = ('N09_FULL40_AUDIT_FAILURE_FULL_SCOPE_RETAINED' if result['audit_failures'] else
        'N09_FULL40_TECHNICAL_INCOMPLETE_FULL_SCOPE_RETAINED' if incomplete else
        COMPLETE_STATUS if all_ok else 'N09_FULL40_REJECTIONS_OR_MISSING_CONTROLS_RETAINED')
    indexed = {(r['scene'], r['slot'], r['round']): r for r in rows}
    cohorts = []
    for request in bound['requests']:
        for slot in bound['bindings']:
            group = [indexed[(request['name'], slot, n)] for n in range(4)]
            safe = all(r.get(k) == 'PASS' for r in group for k in (
                'raw_model_audit', 'endpoint_audit', 'request_memory_audit', 'component_profile_audit'))
            safe = safe and all(c['status'] == 'PASS' for c in all_controls
                               if c['scene'] == request['name'] and c['slot'] == slot)
            cohorts.append(dict(scene=request['name'], slot=slot, method=bound['bindings'][slot],
                complete_mode_group_accepted=safe, observations=[dict(id=r['id'], mode=r['mode'],
                    original_status=r['status'], observed_timers=r.get('timing_intervals'),
                    request_memory_observation=r.get('request_memory_observation'),
                    audited_component_profile=r.get('audited_component_profile'),
                    raw_model_audit=r.get('raw_model_audit'), endpoint_audit=r.get('endpoint_audit'),
                    component_profile_audit=r.get('component_profile_audit'),
                    request_memory_audit=r.get('request_memory_audit')) for r in group]))
    return dict(status=status, original_runner_paths=observed_paths, registered_total_paths=40,
        registered_formal_profile_control_paths=30, registered_full_warmup_paths=10,
        raw_model_pass_paths=sum(r.get('raw_model_audit') == 'PASS' for r in rows),
        accepted_93frame_videos=sum(r.get('endpoint_audit') == 'PASS' for r in rows),
        audited_component_profile_paths=sum(r.get('component_profile_audit') == 'PASS'
            and r['component_profile'] for r in rows),
        accepted_complete_scene_method_mode_groups=sum(c['complete_mode_group_accepted'] for c in cohorts),
        all_mode_observations=cohorts, inclusive_intervals_not_added_to_total_latency=True,
        separate_diagnostic_modes_not_clean_repeats=True, clean_repeated_latency_claim=False,
        component_calls_not_action_unit_prices=True, minimal_calibration_cost_measured=False,
        GPU_submissions=0, ledger_written=False)
