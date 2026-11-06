"""Source-coverage candidate generation and complete-cohort endpoint selection.

Coverage is geometry, not a fitted local-error or LPIPS predictor. A finite
family is generated before endpoint evaluation, without masks from old winners.
"""
from functools import lru_cache
import math

from .cara_fast_spec_r1 import digest, policy_from_mask


TILTS = (0., -2., 2., 4.)
DISTANCE_SCALE = 10**12


def normalized_sigmas(profile, sigmas):
    values = tuple(sigmas)
    if (len(values) != profile.horizon+1
            or any(type(s) not in (int, float) or not math.isfinite(s) for s in values)
            or values[-1] != 0 or any(a <= b for a, b in zip(values, values[1:]))):
        raise ValueError('Complete strictly decreasing sigma grid including terminal zero required')
    return tuple(s/values[0] for s in values[:-1])


def coverage_distance(sigmas, t, a, b, tilt, mode):
    """Equal update-clock / noise-clock distance; high sigma is phase1.

Each C updates working state even in a nearly flat noise segment. Counting
both clocks avoids assigning almost zero lifetime to many such executions.
"""
    age = ((t-b)/len(sigmas)+sigmas[b-1]-sigmas[t-1])/2
    previous = ((t-a)/len(sigmas)+sigmas[a-1]-sigmas[t-1])/2
    distance = age if mode == 'single' else (age+previous)/2
    return math.exp(tilt*(sigmas[t-1]-.5))*distance


def source_trace(profile, dense_steps, sigmas):
    """Direct residual-source consumers; full WC work state is not compressed here."""
    policy = policy_from_mask(profile, list(dense_steps))
    scales = normalized_sigmas(profile, sigmas)
    sources, rows = [], []
    consumers = {s: [] for s in dense_steps}
    for t, action in enumerate(policy['actions'], 1):
        if action == 'D':
            sources.append(t)
        else:
            a, b = sources[-2:]
            rows.append(dict(t=t, a=a, b=b, sigma=scales[t-1],
                current_age=scales[b-1]-scales[t-1], previous_gap=scales[a-1]-scales[b-1],
                current_update_age=t-b, previous_update_gap=b-a))
            consumers[a].append(t)
            consumers[b].append(t)
    lifetimes = [dict(source=s, C_consumers=consumers[s],
        replaced_by_D=dense_steps[i+2] if i+2 < len(dense_steps) else None)
        for i, s in enumerate(dense_steps)]
    return dict(C_states=rows, lifetimes=lifetimes,
        source_reads_per_CFG_branch=sum(len(v) for v in consumers.values()),
        expected_source_reads_per_CFG_branch=2*policy['counts']['C'],
        full_working_state_influence_measured=False)


def coverage_plans(profile, dense_count, sigmas, *, tilt=0., mode='two', top_k=3):
    """Minimize peak coverage, then squared coverage, at an exact D quota.

Two passes are essential: a later bottleneck can equalize different prefix
peaks, reversing their energy ranking. First solve the bottleneck; then keep
k additive paths under that fixed optimum. Distances are rounded to 1e-12
before comparison, making the discrete objective and tie breaks reproducible.
All returned paths attain the minimum peak (fewer than k may exist).
"""
    scales = normalized_sigmas(profile, sigmas)
    n = profile.horizon
    if (type(dense_count) is not int or not len(profile.protected_dense) <= dense_count <= n
            or profile.min_C_anchors != 2 or mode not in ('single', 'two')
            or type(top_k) is not int or not 1 <= top_k <= 3
            or type(tilt) not in (int, float) or not math.isfinite(tilt) or abs(tilt) > 8):
        raise ValueError('Legal exact D quota, two-anchor profile, finite tilt and top1..3 required')
    protected = set(profile.protected_dense)

    def legal(b, c, count):
        return (not any(b < t < c for t in protected)
                and c-b-1 <= profile.max_source_age
                and (c == b+1 or count >= 2))

    @lru_cache(maxsize=None)
    def interval(a, b, c):
        values = [round(DISTANCE_SCALE*coverage_distance(scales, t, a, b, tilt, mode))
                  for t in range(b+1, c)]
        return max(values, default=0), sum(v*v for v in values)

    def transitions(a, b, count):
        for c in range(b+1, n+1):
            if n-c >= dense_count-count-1 and legal(b, c, count):
                yield c, interval(a, b, c)

    layer = {(0, 1): 0}
    for count in range(1, dense_count):
        following = {}
        for (a, b), peak in layer.items():
            for c, (edge_peak, _) in transitions(a, b, count):
                value = max(peak, edge_peak)
                key = (b, c)
                if key not in following or value < following[key]:
                    following[key] = value
        layer = following
    endings = [max(peak, interval(a, b, n+1)[0]) for (a, b), peak in layer.items()
               if legal(b, n+1, dense_count)]
    if not endings:
        raise ValueError('No legal schedule at the exact D quota')
    optimum = min(endings)

    layer = {(0, 1): [(0, (1,))]}
    for count in range(1, dense_count):
        following = {}
        for (a, b), prefixes in layer.items():
            for c, (peak, energy) in transitions(a, b, count):
                if peak > optimum:
                    continue
                options = following.setdefault((b, c), [])
                options.extend((cost+energy, mask+(c,)) for cost, mask in prefixes)
                options.sort()
                del options[top_k:]
        layer = following
    endings = []
    for (a, b), prefixes in layer.items():
        if legal(b, n+1, dense_count):
            peak, energy = interval(a, b, n+1)
            if peak <= optimum:
                endings.extend((cost+energy, mask) for cost, mask in prefixes)
    plans = []
    for energy, mask in sorted(endings)[:top_k]:
        policy = policy_from_mask(profile, list(mask))
        plans.append(dict(dense_steps=list(mask), peak_units=optimum,
            squared_units=energy, peak=optimum/DISTANCE_SCALE,
            squared_sum=energy/DISTANCE_SCALE**2, policy=policy))
    return dict(plans=plans, tilt=tilt, mode=mode, exact_D=dense_count,
        horizon=n, distance_scale=DISTANCE_SCALE, minimum_peak_exact=True,
        energy_top_k_within_minimum_peak=True, terminal_LPIPS_predicted=False)


def candidate_pool(profile, dense_count, sigmas, *, mode='two'):
    """Four fixed phase tilts x up to three plans, deduplicated before scoring."""
    candidates, seen = [], {}
    for tilt in TILTS:
        result = coverage_plans(profile, dense_count, sigmas, tilt=tilt, mode=mode)
        for rank, plan in enumerate(result['plans'], 1):
            mask_id = digest(dict(profile=profile.fingerprint, dense=plan['dense_steps']))
            origin = dict(tilt=tilt, rank=rank, peak=plan['peak'], squared_sum=plan['squared_sum'])
            if mask_id in seen:
                seen[mask_id]['origins'].append(origin)
                continue
            row = dict(candidate_id=mask_id, dense_steps=plan['dense_steps'],
                policy=plan['policy'], origins=[origin],
                trace=source_trace(profile, plan['dense_steps'], sigmas))
            seen[mask_id] = row
            candidates.append(row)
    payload = dict(schema='CARA_SOURCE_COVERAGE_POOL_R1', mode=mode,
        exact_D=dense_count, profile_sha256=profile.fingerprint, sigmas=list(sigmas),
        coverage_coordinate='equal_mean_of_normalized_update_and_sigma_distance',
        tilts=list(TILTS), per_tilt_limit=3, candidate_limit=12, candidates=candidates,
        local_error_labels_used=0, endpoint_evaluated=False, GPU_dispatch_ready=False)
    return dict(payload, pool_sha256=digest(payload))


def select_endpoint(pool, fit_members, rows, *, cost_limit_GPUh, overhead_GPUh=0.):
    """Input-equal complete93-frame LPIPS; failed/missing cohorts stay visible.

Rows explicitly retain failures and their cost. Only candidates complete on
every registered FIT member are eligible. No per-frame or per-input selection.
This function selects data supplied by a caller; it never runs/freeze/scores.
"""
    payload = {k: v for k, v in pool.items() if k != 'pool_sha256'}
    if digest(payload) != pool['pool_sha256']:
        raise ValueError('Frozen candidate pool digest differs')
    ids = [r['candidate_id'] for r in pool['candidates']]
    if (not ids or len(ids) != len(set(ids)) or not fit_members
            or len(fit_members) != len(set(fit_members))):
        raise ValueError('Distinct nonempty candidates and registered FIT members required')
    expected = {(c, m) for c in ids for m in fit_members}
    actual = [(r['candidate_id'], r['member']) for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('Full frozen candidate x FIT denominator required, including failures')
    contexts = {(r['metric_protocol_sha256']) for r in rows}
    member_bindings = {m: {(r['input_sha256'], r['reference_sha256']) for r in rows
                           if r['member'] == m} for m in fit_members}
    if (len(contexts) != 1 or any(len(v) != 1 for v in member_bindings.values())
            or any(not isinstance(r[k], str) or len(r[k]) != 64
                   or any(c not in '0123456789abcdef' for c in r[k])
                   for r in rows for k in ('input_sha256', 'reference_sha256', 'metric_protocol_sha256'))):
        raise ValueError('One metric protocol and fixed input/reference bytes per member required')
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0
           for v in (cost_limit_GPUh, overhead_GPUh)):
        raise ValueError('Finite nonnegative complete calibration cost limit required')
    for row in rows:
        if (row['status'] not in ('COMPLETE', 'FAILED', 'MISSING')
                or type(row['actual_GPUh']) not in (int, float)
                or not math.isfinite(row['actual_GPUh']) or row['actual_GPUh'] < 0):
            raise ValueError('Explicit terminal status and actual cost for every position required')
        if row['status'] == 'COMPLETE':
            if (row['frames'] != 93 or any(type(row[k]) not in (int, float)
                    or not math.isfinite(row[k]) or row[k] < 0
                    for k in ('LPIPS', 'T_DD', 'T_request'))
                    or not 0 < row['T_DD'] <= row['T_request']):
                raise ValueError('Complete93-frame finite LPIPS and both positive clocks required')
    total = math.fsum([overhead_GPUh]+[r['actual_GPUh'] for r in rows])
    if total > cost_limit_GPUh:
        raise ValueError('Complete calibration cost exceeds the fixed limit')
    options = []
    for candidate_id in ids:
        cohort = [r for r in rows if r['candidate_id'] == candidate_id]
        eligible = all(r['status'] == 'COMPLETE' for r in cohort)
        options.append(dict(candidate_id=candidate_id, eligible=eligible,
            statuses={r['member']: r['status'] for r in cohort},
            LPIPS_mean=math.fsum(r['LPIPS'] for r in cohort)/len(cohort) if eligible else None))
    complete = [r for r in options if r['eligible']]
    selected = min(complete, key=lambda r: (r['LPIPS_mean'], ids.index(r['candidate_id']))) if complete else None
    return dict(schema='CARA_SOURCE_COVERAGE_ENDPOINT_SELECTION_R1',
        status='SELECTED' if selected else 'NO_COMPLETE_CANDIDATE',
        selected=selected, candidates=options, candidate_denominator=len(ids),
        input_denominator=len(fit_members), position_denominator=len(expected),
        actual_calibration_GPUh=total, overhead_GPUh=overhead_GPUh,
        cost_limit_GPUh=cost_limit_GPUh, pool_sha256=pool['pool_sha256'],
        rows_sha256=digest(rows), selection_members=list(fit_members),
        metric_protocol_sha256=next(iter(contexts)), frozen=False)
