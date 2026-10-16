"""Bind the full40 timing protocol to already frozen shared executor points.

Primary core timing and the original balanced order remain unchanged. Extra
observed timer fields are reported separately, never subtracted or estimated
to manufacture a clean latency. This module chooses no final workpoints.
"""
import copy
import time

from .balanced_repeat_timing_r1 import SCENES, SLOTS, matrix
from .frozen_shared_execution_r1 import execute, point
from .frozen_shared_production_r1 import audit_row as execution_audit, number

COUNTS = dict(requests=2, methods=5, scientific_paths=30, full_warmup_paths=10,
              total_paths=40, ordinary_pairs=1440, CFG_calls=2880, loads=1, teacher_pairs=0)


def bind(protocol, bindings, final_shared_methods):
    if (protocol['scope_counts'] != COUNTS or protocol['method_slots'] != list(SLOTS)
            or protocol['complete_matrix'] != matrix()
            or protocol['main_clock'] != 'SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING'
            or protocol['extra_profile_paths_selected'] != 0
            or not protocol['scenes_are_old_exposed_CAL_not_new_input_test']
            or set(bindings) != set(SLOTS) or len(final_shared_methods) != 10
            or len(set(final_shared_methods)) != 10 or not set(bindings.values()).issubset(final_shared_methods)):
        raise ValueError('Original40 protocol and the same final frozen five method roles required')
    for method in final_shared_methods: point(method)
    if (bindings['FULL_NATIVE'] != 'NATIVE35'
            or point(bindings['WORLD_CACHE'])['family'] != 'WC'
            or point(bindings['RA_CFG_CACHE'])['family'] != 'RA'
            or bindings['GCR_EFFICIENT'] != 'A_NO_P'
            or bindings['CPA_HIGH_FIDELITY'] != 'TABLE_PHASE_H1'):
        raise ValueError('Bind declared Native/WC/RA/efficient/high-fidelity roles without substitution')
    requests = copy.deepcopy(protocol['requests'])
    if (len(requests) != 2 or [r['name'] for r in requests] != list(SCENES)
            or any(r['seed'] != 0 or r['num_steps'] != 35 or r['guidance'] != 7
                   or r['num_output_frames'] != 93 or r['resolution'] != '432,768'
                   or r['inference_type'] != 'text2world' or not r['prompt']
                   or not isinstance(r['negative_prompt'], str) for r in requests)):
        raise ValueError('The two original full36 timing inputs cannot be renamed or resampled')
    plan = [{**row, 'method': bindings[row['slot']]} for row in matrix()]
    if any(point(row['method'])['actual_updates'] != 36 for row in plan):
        raise ValueError('This full40 timing protocol has exactly1440 actual update pairs')
    return dict(status='N08_FULL40_BOUND_TO_GIVEN_METHOD_IDS_NOT_PRODUCTION',
        scope_counts=COUNTS.copy(), bindings=dict(bindings), final_shared_method_ids=list(final_shared_methods),
        requests=requests, execution_plan=plan, workpoints_selected_by_this_function=False,
        actual_production_CPU_accepted=False, whole_GPU_card_selected=False)


def prepare_samples(bound, inference_arguments):
    samples = {}
    for request in bound['requests']:
        for slot in SLOTS:
            value = inference_arguments(**copy.deepcopy(request))
            actual = value.model_dump(mode='json')
            if any(actual[k] != v for k, v in request.items()):
                raise ValueError('Typed timing input changed the frozen conditioning or seed')
            samples[(request['name'], slot)] = value
    if len(samples) != 10: raise ValueError('All ten original input/role typed variants required')
    return samples


def observed_timers(row):
    fields = dict(core_text_denoise_VAE_seconds='core_seconds',
        method_install_seconds='method_install_seconds',
        guarded_pipeline_without_write_seconds='guarded_pipeline_without_write_seconds',
        method_cleanup_seconds='method_cleanup_seconds', video_write_seconds='video_write_seconds')
    values = {name: row[field] for name, field in fields.items()}
    gc = [row['request_memory_lifecycle'][which]['seconds'] for which in ('before', 'after')]
    gc.append(row['frozen_request_cleanup']['collection']['seconds'])
    if any(not number(v) or v < 0 for v in list(values.values()) + gc):
        raise ValueError('All recorded timer intervals must be finite actual nonnegative observations')
    if values['core_text_denoise_VAE_seconds'] <= 0 or (
            values['guarded_pipeline_without_write_seconds'] < values['core_text_denoise_VAE_seconds']):
        raise ValueError('The guarded request contains its positive synchronized core interval')
    return dict(**values, request_boundary_GC_intervals_seconds=gc,
        original_main_clock_unchanged=True, timings_subtracted_to_create_core=False,
        overlapping_or_nested_intervals_not_a_new_end_to_end_sum=True,
        full_card_billing_required_for_loading_warmup_output_and_maintenance=True,
        actual_GPU_billing_verified_by_this_function=False)


def audit_row(row, planned, bound):
    if any(row.get(k) != v for k, v in planned.items()):
        raise ValueError('Original timing input, slot, method or balanced position changed')
    if row['method'] != bound['bindings'][row['slot']]:
        raise ValueError('Timing cannot silently substitute a workpoint after freeze')
    mapped = {**planned, 'case_id': planned['scene']}
    execution_audit({**row, 'case_id': row['scene']}, mapped,
        {'cases': [dict(id=r['name'], seed=r['seed']) for r in bound['requests']]})
    if row['status'] in ('COMPLETE', 'VIDEO_REJECTED'):
        return observed_timers(row)
    return None


def execute_one(inference, sample, planned, bound, *, restore_request_state, **kwargs):
    if (sample.name != planned['scene'] or sample.seed != 0 or sample.num_steps != 35
            or planned['method'] != bound['bindings'][planned['slot']] or 'audit' in kwargs):
        raise ValueError('Original request and registered warm/formal mode required')
    restored = restore_request_state()
    original = restored['original_state_sha256']
    if (not isinstance(original, str) or len(original) != 64
            or any(c not in '0123456789abcdef' for c in original)
            or restored['restored_state_sha256'] != original or restored['shared_eval_verified'] is not True):
        raise ValueError('Restore the original model/scheduler/RNG state and shared eval before every request')
    result = execute(inference, sample, planned['method'], audit=planned['section'] == 'WARMUP', **kwargs)
    if result['status'] in ('COMPLETE', 'VIDEO_REJECTED'):
        guided = result.get('guided')
        if planned['section'] == 'WARMUP':
            expected = point(planned['method'])['actual_updates']
            if (not isinstance(guided, list) or len(guided) != expected
                    or result.get('warm_guided_outputs', expected) != expected):
                raise ValueError('Count every actual warm guided tensor before the metadata audit')
            # Sampling returns actual tensors; the later archive adds file
            # hashes. Count them here, outside the already-ended core clock.
            result['warm_guided_outputs'] = len(guided)
        elif guided is not None:
            raise ValueError('Formal timing cannot retain research guided copies')
    row = {**planned, **result}
    timers = audit_row(row, planned, bound)
    return dict(result, timing_intervals=timers, pre_request_state_identity=restored,
        clean_resource_state_accepted_by_this_function=False,
        timing_scope='N08_REGISTERED_CORE_AND_SEPARATE_OBSERVED_INTERVALS_NOT_YET_FINAL_ACCEPTANCE')


def run_registered_batch(bound, samples, run_one, *, save=lambda state: None):
    plan = bound['execution_plan']
    if plan != [{**r, 'method': bound['bindings'][r['slot']]} for r in matrix()] or bound['scope_counts'] != COUNTS:
        raise ValueError('Keep every original40 timing position')
    if set(samples) != {(r['scene'], r['slot']) for r in plan}:
        raise ValueError('All ten typed input/slot variants required')
    state = dict(status='N08_FULL40_RUNNING', scope_counts=COUNTS.copy(), runs=[])
    save(state)
    for planned in plan:
        row = {**planned, 'status': 'RUNNING', 'started_unix': time.time()}
        state['runs'].append(row); save(state)
        try:
            row.update(run_one(planned, samples[(planned['scene'], planned['slot'])]), ended_unix=time.time())
            row['timing_intervals'] = audit_row(row, planned, bound)
            save(state)
        except BaseException as error:
            row.update(original_returned_status=row['status'], status='TECH_FAILED',
                       error_type=type(error).__name__, error=str(error), ended_unix=time.time())
            state.update(status='N08_FULL40_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED', error=str(error))
            save(state); raise
    state['status'] = 'N08_FULL40_GPU_COMPLETE_CPU_AUDIT_PENDING'; save(state)
    return state


def full_rows(runs, bound):
    from .frozen_shared_production_r1 import full_rows as original_prefix
    return original_prefix(runs, bound['execution_plan'])
