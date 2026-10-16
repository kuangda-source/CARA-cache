"""Failure-preserving full40 raw/RGB audit and same-round93-frame scoring."""
import copy

from .balanced_repeat_execution_r1 import COUNTS, audit_row, full_rows
from .balanced_repeat_timing_r1 import summaries
from .frozen_shared_post_r1 import failure, stable_history
from .frozen_shared_statistics_r1 import number

GPU_TERMINAL_STATUS = 'N08_FULL40_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
COMPLETE_STATUS = 'N08_FULL40_COMPLETE30_AUDITED_93FRAME_SCORED_REQUIRES_INDEPENDENT_SPEED_ACCEPTANCE'


def metadata_audit(row, planned, bound):
    audit_row(row, planned, bound)
    state = row['pre_request_state_identity']
    from .frozen_shared_acceptance_r1 import digest
    if (not digest(state['original_state_sha256'])
            or state['original_state_sha256'] != state['restored_state_sha256']
            or state['shared_eval_verified'] is not True):
        raise ValueError('Original request state/RNG and shared eval restoration required')


def audit_payload(row, planned, bound, root, *, expected_shape=(1, 16, 24, 54, 96)):
    from .frozen_shared_post_r1 import audit_payload as shared_payload
    metadata_audit(row, planned, bound)
    mapped_row = {**row, 'case_id': row['scene']}
    mapped_plan = {**planned, 'case_id': planned['scene']}
    cases = [dict(id=r['name'], seed=r['seed']) for r in bound['requests']]
    shared_payload(mapped_row, mapped_plan, {'cases': cases}, root, expected_shape=expected_shape)


def audit_rows(runs, bound, payload_auditor, video_inspector, *, save=lambda result: None):
    rows = copy.deepcopy(full_rows(runs, bound))
    result = dict(rows=rows, audit_failures=[])
    for row, planned in zip(rows, bound['execution_plan']):
        if row['status'] == 'TEXT_REJECTED':
            try:
                metadata_audit(row, planned, bound)
                row.update(raw_model_audit='NOT_APPLICABLE_TEXT_REJECTION_RETAINED',
                           endpoint_audit='NOT_APPLICABLE_TEXT_REJECTION_RETAINED')
            except Exception as error:
                row['raw_model_audit'] = 'AUDIT_FAILURE_RETAINED'
                result['audit_failures'].append(failure('TEXT_REJECTION_IDENTITY', row, error))
        elif row['status'] in ('COMPLETE', 'VIDEO_REJECTED'):
            try:
                payload_auditor(row, planned, bound); row['raw_model_audit'] = 'PASS'
            except Exception as error:
                row.update(raw_model_audit='AUDIT_FAILURE_RETAINED', endpoint_audit='AUDIT_FAILURE_RETAINED')
                result['audit_failures'].append(failure('RAW_MODEL', row, error))
                save(result); continue
            if row['status'] == 'VIDEO_REJECTED':
                row['endpoint_audit'] = 'NOT_APPLICABLE_VIDEO_REJECTION_RETAINED'
            else:
                try:
                    row.update(video_inspector(row)); row['endpoint_audit'] = 'PASS'
                except Exception as error:
                    row['endpoint_audit'] = 'AUDIT_FAILURE_RETAINED'
                    result['audit_failures'].append(failure('VIDEO_CONTAINER_OR_RGB', row, error))
        elif row['status'] not in ('TECH_FAILED', 'NOT_REACHED'):
            raise ValueError('Explicit original full40 terminal generation status required')
        save(result)
    return result


def score_rows(rows, scorer, *, save=lambda: None):
    """A reference from another round or the warmup cannot fill a missing one."""
    references = {(r['scene'], r['round']): r for r in rows
                  if r['section'] == 'TIMED' and r['slot'] == 'FULL_NATIVE'
                  and r.get('endpoint_audit') == 'PASS'}
    failed = []
    for row in rows:
        if row['section'] != 'TIMED': continue
        reference = references.get((row['scene'], row['round']))
        if row.get('endpoint_audit') != 'PASS':
            row['LPIPS_missing_reason'] = 'ORIGINAL_CANDIDATE_UNAVAILABLE_OR_AUDIT_FAILED'
        elif reference is None:
            row['LPIPS_missing_reason'] = 'SAME_SCENE_SAME_ROUND_FRESH_NATIVE_NOT_ACCEPTED'
        else:
            try:
                value = scorer(reference, row); dist = value['frame_distances']
                if (value['frames'] != 93 or len(dist) != 93
                        or not number(value['mean_LPIPS']) or any(not number(v) or v < 0 for v in dist)
                        or abs(sum(dist) / 93 - value['mean_LPIPS']) > 1e-12
                        or value['reference_sha256'] != reference['video_artifact']['sha256']
                        or value['candidate_sha256'] != row['video_artifact']['sha256']):
                    raise ValueError('Original same-round identities or complete93-frame score differs')
                row['LPIPS'] = value
            except Exception as error:
                row['LPIPS_missing_reason'] = 'METRIC_AUDIT_FAILURE_RETAINED'
                failed.append(failure('LPIPS', row, error))
        save()
    return failed


def repeat_controls(rows, bound):
    """All warm vectors were audited; compare each lean endpoint to its warm."""
    lookup = {(r['scene'], r['slot'], r['round']): r for r in rows}
    warm_controls, repeated, failed = [], [], []
    for planned in bound['execution_plan']:
        row = lookup[(planned['scene'], planned['slot'], planned['round'])]
        if row['section'] == 'WARMUP':
            valid = row.get('raw_model_audit') == 'PASS' and row.get('warm_guided_outputs') == 36
            warm_controls.append(dict(id=row['id'], scene=row['scene'], slot=row['slot'],
                status='PASS_ALL36_WARM_GUIDED_AUDITED' if valid else 'ORIGINAL_WARM_TRACE_UNAVAILABLE_RETAINED',
                guided_outputs_audited=36 if valid else None,
                no_formal_guided_copy_or_cross_scene_guided_equality_claim=True))
            continue
        warm = lookup[(row['scene'], row['slot'], 0)]
        control = dict(id=row['id'], warm_id=warm['id'], scene=row['scene'], slot=row['slot'],
                       round=row['round'], raw_endpoint_actions_history_equal=False, all93_RGB_equal=False)
        repeated.append(control)
        if row['status'] in ('TECH_FAILED', 'NOT_REACHED') or warm['status'] in ('TECH_FAILED', 'NOT_REACHED'):
            control['status'] = 'TECHNICAL_OR_WARM_CONTROL_UNAVAILABLE_RETAINED'; continue
        if row['status'] == 'TEXT_REJECTED' or warm['status'] == 'TEXT_REJECTED':
            control['status'] = ('TEXT_REJECTION_REPEATED_NO_MODEL_OR_VIDEO_CONTROL' if
                row['status'] == warm['status'] else 'GUARDRAIL_OUTCOMES_DIFFER_NO_REPEAT_CONTROL_RETAINED')
            continue
        if any(r.get('raw_model_audit') != 'PASS' for r in (row, warm)):
            control['status'] = 'RAW_AUDIT_UNAVAILABLE_RETAINED'; continue
        try:
            if any(row.get(k) != warm.get(k) for k in (
                    'final_latent_sha256', 'actions', 'A_history', 'scheduler_timesteps', 'pre_request_state_identity')):
                raise ValueError('Warm/lean original endpoint, state, actions or history differs')
            if stable_history(row.get('source_history')) != stable_history(warm.get('source_history')):
                raise ValueError('Warm/lean physical source history differs')
            control['raw_endpoint_actions_history_equal'] = True
            rgb = all(r.get('endpoint_audit') == 'PASS' for r in (row, warm))
            if rgb:
                if (row['decoded_video']['RGB_sha256'] != warm['decoded_video']['RGB_sha256']
                        or row['video_artifact']['decoded_rgb_sha256'] != warm['video_artifact']['decoded_rgb_sha256']):
                    raise ValueError('Warm/lean complete93 RGB outputs differ')
                control.update(status='PASS', all93_RGB_equal=True)
            elif row['status'] == warm['status'] == 'VIDEO_REJECTED':
                control['status'] = 'PASS_RAW_VIDEO_REJECTION_RETAINED'
            else:
                control['status'] = 'RAW_EQUAL_RGB_CONTROL_UNAVAILABLE_RETAINED'
        except Exception as error:
            control['status'] = 'REPEAT_CONTROL_FAILURE_RETAINED'
            failed.append(failure('WARM_LEAN_ENDPOINT_ACTION_HISTORY_RGB', row, error))
    if len(warm_controls) != 10 or len(repeated) != 30:
        raise ValueError('All original ten warm traces and thirty formal repeat controls required')
    return warm_controls, repeated, failed


def statistics_inputs(rows, controls):
    """Keep original observations; mask uncertified paths only in a derived view."""
    view = copy.deepcopy(rows); indexed = {r['id']: r for r in controls}
    safe = {'PASS', 'PASS_RAW_VIDEO_REJECTION_RETAINED', 'RAW_EQUAL_RGB_CONTROL_UNAVAILABLE_RETAINED'}
    for row in view:
        if row['section'] != 'TIMED': continue
        if indexed[row['id']]['status'] not in safe:
            row['raw_model_audit'] = 'REPEAT_CONTROL_UNAVAILABLE_OR_FAILED_FOR_STATISTICS'
            row['endpoint_audit'] = 'REPEAT_CONTROL_UNAVAILABLE_OR_FAILED_FOR_STATISTICS'
            row.pop('LPIPS', None)
    references = {(r['scene'], r['round']): r for r in view
                  if r['section'] == 'TIMED' and r['slot'] == 'FULL_NATIVE'}
    for row in view:
        if row['section'] == 'TIMED' and references[(row['scene'], row['round'])].get('endpoint_audit') != 'PASS':
            # Original pair scores remain on rows/all_formal_observations.
            # A derived primary cohort cannot keep a now-uncertified reference.
            row.pop('LPIPS', None)
    return view


def summarize(result, bound, *, observed_paths, child_exit_code):
    rows = result['rows']; formal = [r for r in rows if r['section'] == 'TIMED']
    if len(rows) != 40 or len(formal) != 30 or bound['scope_counts'] != COUNTS:
        raise ValueError('Original complete40/30/10 timing denominator required')
    statistics = summaries(statistics_inputs(rows, result['formal_to_warm_controls']))
    incomplete = observed_paths != 40 or child_exit_code != 0 or any(
        r['status'] in ('TECH_FAILED', 'NOT_REACHED') for r in rows)
    all_ok = (all(r.get('endpoint_audit') == 'PASS' for r in rows)
        and all('LPIPS' in r for r in formal)
        and len(result['warm_trace_controls']) == 10
        and all(r['status'] == 'PASS_ALL36_WARM_GUIDED_AUDITED' for r in result['warm_trace_controls'])
        and len(result['formal_to_warm_controls']) == 30
        and all(r['status'] == 'PASS' for r in result['formal_to_warm_controls']))
    status = ('N08_FULL40_AUDIT_FAILURE_FULL_SCOPE_RETAINED' if result['audit_failures'] else
              'N08_FULL40_TECHNICAL_INCOMPLETE_FULL_SCOPE_RETAINED' if incomplete else
              COMPLETE_STATUS if all_ok else 'N08_FULL40_REJECTIONS_OR_MISSING_CONTROLS_RETAINED')
    return dict(status=status, original_runner_paths=observed_paths,
        registered_total_paths=40, registered_formal_paths=30, registered_full_warmup_paths=10,
        raw_model_pass_paths=sum(r.get('raw_model_audit') == 'PASS' for r in rows),
        accepted_scientific_videos=sum(r.get('endpoint_audit') == 'PASS' for r in formal),
        scored_scientific_videos=sum('LPIPS' in r for r in formal),
        timing_statistics=statistics,
        all_formal_observations=[dict(id=r['id'], scene=r['scene'], slot=r['slot'], round=r['round'],
            original_status=r['status'], observed_core_seconds=r.get('core_seconds'),
            raw_model_audit=r.get('raw_model_audit'), endpoint_audit=r.get('endpoint_audit'),
            observed_LPIPS=r.get('LPIPS'), repeat_control=next(c for c in result['formal_to_warm_controls'] if c['id'] == r['id']))
            for r in formal],
        stable_repeated_clean_speed_claim=False, clean_interval_resource_state_accepted=False,
        independent_input_generalization_claim=False, GPU_submissions=0, ledger_written=False)


def registered_interval_overlaps(pool, own_run, start, end):
    """Check complete recorded job intervals, including transient boundary gaps."""
    if not number(start) or not number(end) or not start < end:
        raise ValueError('Original finite wall-clock interval required')
    overlaps = []
    for name, job in pool['jobs'].items():
        if name == own_run: continue
        settled, reserved = job.get('settled_unix'), job.get('reserved_unix')
        if job['status'] == 'SETTLED' and number(settled) and settled <= start: continue
        if not number(reserved): raise ValueError('An unknown recorded start cannot establish a clean interval')
        if reserved >= end: continue
        if job['status'] == 'SETTLED':
            if not number(settled) or settled < reserved: raise ValueError('Original settled interval differs')
            if settled <= start: continue
        elif job['status'] != 'RESERVED_OR_RUNNING': raise ValueError('Unknown original v2 job state')
        overlaps.append(dict(job_id=name, reserved_unix=reserved, settled_unix=settled, status=job['status']))
    return dict(recorded_GPU_job_overlaps=overlaps, no_recorded_GPU_overlap=not overlaps,
        interval_basis='ORIGINAL_V2_JOB_RESERVED_AND_SETTLED_UNIX_NOT_BOUNDARY_ONLY',
        external_unrecorded_GPU_or_transient_CPU_interference_excluded=False)
