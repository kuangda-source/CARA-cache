"""CPU diagnostics for a complete original price table, never clean-price approval.

This sidecar leaves the frozen collector/acceptor unchanged. Repeated nearest
anchors and singly measured other anchors are distinct statistical units.
"""
import math
import statistics as st

from .policy_interval_assets_r1 import ACTIONS, SCENES, cells, matrix, rounds_for


def distribution(values):
    xs = sorted(values)
    if not xs:
        return dict(n=0, median=None, p95=None, maximum=None)
    def quantile(q):
        i = (len(xs) - 1) * q
        lo = int(i)
        return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo)
    return dict(n=len(xs), median=quantile(.5), p95=quantile(.95), maximum=xs[-1])


def analyze_prices(runs):
    if len(runs) != 14:
        raise ValueError('Complete original 14-path denominator required')
    for row, planned in zip(runs, matrix()):
        if any(row.get(k) != v for k, v in planned.items()):
            raise ValueError('Original path position changed')
        if row.get('status') not in ('COMPLETE', 'VIDEO_REJECTED'):
            raise ValueError('Do not analyze partial or refused price domains')
    collected = [r for r in runs if r['section'] == 'FORMAL' and r['mode'] == 'COLLECT']
    repeated = []
    per_cell = []
    for row in collected:
        points = row['interval_cells']
        if [(p['source'], p['target']) for p in points] != cells():
            raise ValueError('Keep all 406 cells per CAL')
        for point in points:
            s, t = point['source'], point['target']
            trials = point['price_trials']
            if [(p['round'], p['action']) for p in trials] != [
                    (r, a) for r, order in rounds_for(s, t) for a in order]:
                raise ValueError('Missing, duplicated or reordered registered trials')
            if any(not math.isfinite(p['seconds']) or p['seconds'] <= 0
                   or p['shared_prefix_included'] or p['restore_copy_hash_write_included']
                   for p in trials):
                raise ValueError('Invalid action interval or timing boundary')
            means = {}
            for action in ACTIONS:
                formal = [p['seconds'] for p in trials
                          if p['action'] == action and p['round'] != 'WARMUP']
                means[action] = st.mean(formal)
                if len(formal) == 3:
                    repeated.append(dict(scene=row['scene'], source=s, target=t, action=action,
                        sample_CV=st.stdev(formal) / st.mean(formal),
                        round2_over_round1=formal[1] / formal[0],
                        round3_over_round1=formal[2] / formal[0]))
            per_cell.append(dict(scene=row['scene'], source=s, target=t, means=means,
                A_HALF_over_C=means['A_HALF'] / means['C'],
                A_ONE_over_C=means['A_ONE'] / means['C']))
    # Retain the frozen max-source aggregator; diagnose rather than replace it.
    amplification = []
    for scene in SCENES:
        for t in range(8, 36):
            group = [p for p in per_cell if p['scene'] == scene and p['target'] == t]
            for action in ACTIONS:
                xs = [p['means'][action] for p in group]
                amplification.append(dict(scene=scene, target=t, action=action,
                    max_source_over_median_source=max(xs) / st.median(xs)))
    # Scene and execution position coincide. This is descriptive drift only.
    sequence = []
    for scene in SCENES:
        item = dict(scene=scene)
        for action in ACTIONS:
            ratios = []
            for s, t in cells():
                matched = [p for p in per_cell if p['source'] == s and p['target'] == t]
                own = next(p['means'][action] for p in matched if p['scene'] == scene)
                ratios.append(own / st.median(p['means'][action] for p in matched))
            item[action] = distribution(ratios)
        sequence.append(item)
    return dict(status='FULL1624_DESCRIPTIVE_PRICE_REVIEW_NOT_CLEAN_ACCEPTANCE',
        formal_cells=len(per_cell), triply_measured_cells=len(repeated) // 3,
        singly_measured_cells=len(per_cell) - len(repeated) // 3,
        formal_readout_trials=5544, warm_trials_excluded=4872,
        repeated_action_summary={a: {key: distribution(p[key] for p in repeated if p['action'] == a)
            for key in ('sample_CV', 'round2_over_round1', 'round3_over_round1')} for a in ACTIONS},
        same_cell_action_ratios={a: distribution(p[a] for p in per_cell)
                                for a in ('A_HALF_over_C', 'A_ONE_over_C')},
        source_max_amplification={a: distribution(p['max_source_over_median_source']
            for p in amplification if p['action'] == a) for a in ACTIONS},
        matched_cell_sequence_ratios=sequence,
        sequence_is_confounded_with_scene=True,
        round_drift_is_confounded_with_action_order=True,
        repeated_cells=repeated, source_max_cells=amplification,
        clean_action_prices_accepted=False, PG_P1_dispatch_ready=False,
        reason='Variation is diagnostic; low variance cannot clear known same-GPU contention. '
               'Clean replacement prices require a separately registered exclusive measurement.',
        endpoint_quality_or_speed_result=False)


def exclusive_gate(snapshot, *, gpu_uuid, phase, runner=None, max_age_seconds=10, now):
    """Read-only admission evidence; never a reservation or an admin operation."""
    reasons = []
    if phase not in ('idle', 'active'):
        raise ValueError('Use idle preflight or active context verification')
    if snapshot.get('gpu_uuid') != gpu_uuid:
        reasons.append('UUID_MISMATCH')
    if not 0 <= now - snapshot.get('observed_unix', -math.inf) <= max_age_seconds:
        reasons.append('STALE_OBSERVATION')
    if snapshot.get('compute_mode') != 'Exclusive_Process':
        reasons.append('HARDWARE_EXCLUSIVE_PROCESS_NOT_ENABLED')
    if snapshot.get('mps_processes') != []:
        reasons.append('MPS_PRESENT_OR_UNKNOWN')
    apps = snapshot.get('compute_apps')
    if not isinstance(apps, list):
        reasons.append('COMPUTE_APPS_UNKNOWN')
    elif phase == 'idle' and apps:
        reasons.append('GPU_ALREADY_OCCUPIED')
    elif phase == 'active':
        if not runner or len(apps) != 1 or any(
                apps[0].get(k) != runner.get(k) or runner.get(k) is None
                for k in ('pid', 'start_ticks', 'uid')):
            reasons.append('EXACT_OWN_RUNNER_NOT_SOLE_CONTEXT')
    return dict(status='EXCLUSIVE_OBSERVATION_PASS' if not reasons else 'EXCLUSIVE_ADMISSION_BLOCKED',
        observation_passed=not reasons, phase=phase, reasons=reasons,
        future_ownership_guaranteed=False, reservation_created=False,
        process_or_compute_mode_modified=False)
