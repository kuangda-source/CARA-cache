"""Read-only full180 audit and grouped final-test evaluation.

No input, workpoint or GPU card is selected here. Original generation statuses
are retained even when a container, tensor or metric fails its CPU audit.
"""
import copy
import hashlib
from pathlib import Path

from .frozen_shared_execution_r1 import point
from .frozen_shared_production_r1 import audit_row, full_rows, sha
from .frozen_shared_statistics_r1 import analyze

GPU_TERMINAL_STATUS = 'N07_SHARED180_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
COMPLETE_STATUS = 'N07_SHARED180_COMPLETE160_AUDITED_93FRAME_SCORED'


def comparisons(methods):
    """Freeze all candidate contrasts by identity, never by a test outcome."""
    return [(candidate, baseline) for candidate in ('A_NO_P', 'TABLE_PHASE_H1')
            for baseline in methods if candidate != baseline]


def stable_history(value):
    # Object addresses are request-local; all numerical/source fields remain.
    if isinstance(value, dict):
        return {k: stable_history(v) for k, v in value.items() if k != 'owner'}
    if isinstance(value, (list, tuple)):
        return [stable_history(v) for v in value]
    return value


def artifact_path(root, info):
    root, path = Path(root).resolve(), Path(info['path']).resolve()
    if (not path.is_relative_to(root) or not path.is_file()
            or type(info['bytes']) is not int or info['bytes'] <= 0
            or path.stat().st_size != info['bytes'] or sha(path) != info['sha256']):
        raise ValueError('Original artifact path, byte count or SHA differs')
    return path


def read_tensor(root, info, key):
    import torch
    value = torch.load(artifact_path(root, info), map_location='cpu', weights_only=True)
    if not isinstance(value, dict) or set(value) != {key}:
        raise ValueError('Original CPU tensor container schema differs')
    return value[key]


def audit_payload(row, planned, bound, root, *, expected_shape=(1, 16, 24, 54, 96)):
    import torch
    from .mid_coverage import tree_digest
    audit_row(row, planned, bound)
    final = read_tensor(root, row['final_artifact'], 'final_latent')
    if (not isinstance(final, torch.Tensor) or final.device.type != 'cpu'
            or tuple(final.shape) != tuple(expected_shape) or not bool(torch.isfinite(final).all())
            or tree_digest(final) != row['final_latent_sha256']):
        raise ValueError('Original final latent differs from the generation receipt')
    del final
    if planned['section'] == 'WARMUP':
        guided = read_tensor(root, row['warm_guided_artifact'], 'guided')
        n = point(planned['method'])['actual_updates']
        if (not isinstance(guided, list) or len(guided) != n
                or tree_digest(guided) != row['warm_guided_tree_sha256']
                or any(not isinstance(t, torch.Tensor) or t.device.type != 'cpu'
                       or tuple(t.shape) != tuple(expected_shape) or not bool(torch.isfinite(t).all())
                       for t in guided)):
            raise ValueError('All actual warm guided vectors and their original SHA required')


def inspect_video(root, row):
    from .rv0_video_reader import decoded_video, probe_video
    root, path = Path(root).resolve(), Path(row['video_path']).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Original video must belong to this immutable output root')
    meta = probe_video(path)
    digest, frames, timestamps = hashlib.sha256(), [], []
    with decoded_video(path) as source:
        for rgb, pts, base in source:
            raw = rgb.tobytes(); digest.update(raw)
            frames.append(hashlib.sha256(raw).hexdigest()); timestamps.append([pts, str(base)])
    if (len(frames) != 93 or meta['frames'] != 93 or meta['HWC'] != [432, 768, 3]
            or meta['fps'] != 16 or timestamps != [[pts, meta['time_base']] for pts in meta['pts']]):
        raise ValueError('All93 original RGB frames, timestamps and geometry required')
    return dict(video_artifact=dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size,
                    frames=93, fps=16, width=768, height=432, decoded_rgb_sha256=frames),
                decoded_video=dict(frames=93, probe=meta, RGB_sha256=digest.hexdigest()))


def failure(kind, row, error):
    return dict(kind=kind, id=row.get('id'), error_type=type(error).__name__, error=str(error))


def audit_rows(runs, plan, bound, payload_auditor, video_inspector, *, save=lambda result: None):
    rows = copy.deepcopy(full_rows(runs, plan))
    result = dict(rows=rows, audit_failures=[])
    for row, planned in zip(rows, plan):
        if row['status'] == 'TEXT_REJECTED':
            try:
                audit_row(row, planned, bound)
                row.update(raw_model_audit='NOT_APPLICABLE_TEXT_REJECTION_RETAINED',
                           endpoint_audit='NOT_APPLICABLE_TEXT_REJECTION_RETAINED')
            except Exception as error:
                row['raw_model_audit'] = 'AUDIT_FAILURE_RETAINED'
                result['audit_failures'].append(failure('TEXT_REJECTION_IDENTITY', row, error))
        elif row['status'] in ('COMPLETE', 'VIDEO_REJECTED'):
            try:
                payload_auditor(row, planned, bound)
                row['raw_model_audit'] = 'PASS'
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
            raise ValueError('Explicit original terminal generation status required')
        save(result)
    return result


def score_rows(rows, scorer, *, reference_method='NATIVE35', save=lambda: None):
    """Score every compatible formal row; a broken reference is never replaced."""
    failures = []
    refs = {r['case_id']: r for r in rows if r['section'] == 'TIMED'
            and r['method'] == reference_method and r.get('endpoint_audit') == 'PASS'}
    for row in rows:
        if row['section'] != 'TIMED': continue
        if row.get('endpoint_audit') != 'PASS':
            row['LPIPS_missing_reason'] = 'ORIGINAL_CANDIDATE_UNAVAILABLE_OR_AUDIT_FAILED'
        elif row['case_id'] not in refs:
            row['LPIPS_missing_reason'] = 'MATCHED_FRESH_NATIVE35_SAME_CASE_SEED_NOT_ACCEPTED'
        else:
            try:
                score = scorer(refs[row['case_id']], row)
                # Reject a foreign seed/reference or incomplete metric immediately.
                values = score['frame_distances']
                from .frozen_shared_statistics_r1 import number
                if (score['frames'] != 93 or len(values) != 93 or not number(score['mean_LPIPS'])
                        or any(not number(v) or v < 0 for v in values)
                        or abs(sum(values) / 93 - score['mean_LPIPS']) > 1e-12
                        or score['reference_sha256'] != refs[row['case_id']]['video_artifact']['sha256']
                        or score['candidate_sha256'] != row['video_artifact']['sha256']):
                    raise ValueError('Whole93-frame metric or matched artifact identity differs')
                row['LPIPS'] = score
            except Exception as error:
                row['LPIPS_missing_reason'] = 'METRIC_AUDIT_FAILURE_RETAINED'
                failures.append(failure('LPIPS', row, error))
        save()
    return failures


def warm_controls(rows, plan, read_guides):
    """Both full warm traces and the first formal endpoint must agree."""
    import torch
    methods = [r['method'] for r in plan if r['section'] == 'WARMUP' and r['round'] == 1]
    controls, failures = [], []
    for method in methods:
        arms = [next(r for r in rows if r['id'] == f'warm_{repeat}_{method}') for repeat in (1, 2)]
        first = next(r for r in rows if r['section'] == 'TIMED'
                     and r['case_id'] == arms[0]['case_id'] and r['method'] == method)
        group = arms + [first]
        if any(r['status'] in ('TECH_FAILED', 'NOT_REACHED') for r in group):
            controls.append(dict(method=method, status='MISSING_TECHNICAL_OR_NOT_REACHED_RETAINED')); continue
        try:
            if len({r['status'] for r in group}) != 1:
                raise ValueError('Warm and first formal guardrail outcome differs')
            if group[0]['status'] == 'TEXT_REJECTED':
                if any(r.get('raw_model_audit') != 'NOT_APPLICABLE_TEXT_REJECTION_RETAINED' for r in group):
                    raise ValueError('Invalid text rejection control')
                controls.append(dict(method=method, status='TEXT_REJECTION_REPEATED_NO_MODEL_OR_GUIDED_CONTROL'))
                continue
            if any(r.get('raw_model_audit') != 'PASS' for r in group):
                controls.append(dict(method=method, status='RAW_AUDIT_UNAVAILABLE_RETAINED')); continue
            reference = group[0]
            for other in group[1:]:
                for field in ('final_latent_sha256', 'actions', 'A_history', 'scheduler_timesteps'):
                    if reference.get(field) != other.get(field):
                        raise ValueError('Warm/formal raw endpoint, actions or history differs: ' + field)
                if stable_history(reference.get('source_history')) != stable_history(other.get('source_history')):
                    raise ValueError('Warm/formal physical source history differs')
            n = point(method)['actual_updates']
            left, right = read_guides(arms[0]), read_guides(arms[1])
            if (len(left) != n or len(right) != n
                    or any(a.shape != b.shape or not torch.equal(a, b) for a, b in zip(left, right))):
                raise ValueError('Both warm traces require every actual19/27/36 guided output equal')
            del left, right
            rgb = all(r.get('endpoint_audit') == 'PASS' for r in group)
            if reference['status'] == 'COMPLETE' and not rgb:
                controls.append(dict(method=method, status='VIDEO_AUDIT_UNAVAILABLE_RETAINED',
                    all_guided_outputs_equal=n, raw_endpoint_actions_history_equal=True)); continue
            if rgb and any(r['decoded_video']['RGB_sha256'] != reference['decoded_video']['RGB_sha256']
                    or r['video_artifact']['decoded_rgb_sha256'] != reference['video_artifact']['decoded_rgb_sha256']
                    for r in group[1:]):
                raise ValueError('Warm/formal all93 RGB frames differ')
            controls.append(dict(method=method, status='PASS' if rgb else 'PASS_RAW_VIDEO_REJECTION_RETAINED',
                all_guided_outputs_equal=n, raw_endpoint_actions_history_equal=True,
                all93_RGB_equal=rgb, first_formal_case=first['case_id']))
        except Exception as error:
            controls.append(dict(method=method, status='CONTROL_FAILURE_RETAINED'))
            failures.append(failure('WARM_REPEAT_OR_FIRST_FORMAL', {'id': method}, error))
    return controls, failures


def summarize(result, bound, *, observed_paths, child_exit_code, bootstrap_repetitions=4096):
    rows, failures = result['rows'], result['audit_failures']
    formal = [r for r in rows if r['section'] == 'TIMED']
    if len(rows) != 180 or len(formal) != 160:
        raise ValueError('Original180/160 denominator required')
    statistics = analyze(bound['cases'], bound['method_ids'], formal, comparisons(bound['method_ids']),
        reference_method='NATIVE35', bootstrap_repetitions=bootstrap_repetitions, bootstrap_seed=20261016)
    incomplete = observed_paths != 180 or child_exit_code != 0 or any(
        r['status'] in ('TECH_FAILED', 'NOT_REACHED') for r in rows)
    all_videos = all(r.get('endpoint_audit') == 'PASS' for r in rows)
    all_scored = all('LPIPS' in r for r in formal)
    warm = result['warm_repeat_controls']
    status = ('N07_SHARED180_AUDIT_FAILURE_FULL_SCOPE_RETAINED' if failures else
              'N07_SHARED180_TECHNICAL_INCOMPLETE_FULL_SCOPE_RETAINED' if incomplete else
              COMPLETE_STATUS if all_videos and all_scored and len(warm) == 10
                  and all(r['status'] == 'PASS' for r in warm) else
              'N07_SHARED180_FULL_SCOPE_REJECTIONS_OR_MISSING_CONTROLS_RETAINED')
    return dict(status=status, grouped_statistics=statistics, original_runner_paths=observed_paths,
        registered_total_paths=180, registered_formal_paths=160,
        accepted_scientific_videos=sum(r.get('endpoint_audit') == 'PASS' for r in formal),
        scored_scientific_videos=sum('LPIPS' in r for r in formal),
        raw_model_pass_paths=sum(r.get('raw_model_audit') == 'PASS' for r in rows),
        stable_repeated_clean_speed_claim=False, physics_quality_claim=False,
        no_test_winner_selection=True, GPU_submissions=0, ledger_written=False)
