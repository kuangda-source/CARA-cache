"""Offline Fast-card specifications. No transport, model loading or GPU dispatch."""
import hashlib
import json
import math
from fractions import Fraction

from .policy_generator_r1.interval_grammar import Edge, Profile, compile_policy


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def profile_from(value):
    return Profile(**{k: tuple(v) if k in ('protected_dense', 'alpha_candidates') else v
                      for k, v in value.items()})


def uniform_mask(schedule, profile, count):
    """Farthest-point coverage on actual linear sigma, exact rational tie breaks.

    Normalize by the full scheduler sigma range, including the terminal zero.
    Terminal sigma has no model call. Protection/age are engineering constraints.
    """
    n = schedule['actual_updates']
    sigmas = schedule['sigmas']
    if (n != profile.horizon or len(schedule['timesteps']) != n or len(sigmas) != n+1
            or any(type(v) not in (float, int) or not math.isfinite(v) for v in sigmas)
            or any(a <= b for a, b in zip(sigmas, sigmas[1:]))
            or sigmas[-1] != 0 or not len(profile.protected_dense) <= count <= n):
        raise ValueError('Actual strictly decreasing sigma/update grid required')
    raw = [Fraction(v) for v in sigmas]
    coordinates = [(raw[0]-v)/(raw[0]-raw[-1]) for v in raw[:-1]]
    selected = set(profile.protected_dense)
    while len(selected) < count:
        candidates = [t for t in range(1, n+1) if t not in selected]
        selected.add(min(candidates, key=lambda t: (
            -min(abs(coordinates[t-1]-coordinates[s-1]) for s in selected), t)))
    mask = sorted(selected)
    if max(b-a-1 for a, b in zip(mask, mask[1:]+[n+1])) > profile.max_source_age:
        raise ValueError('Uniform mask exceeds the inherited production age support')
    return mask, [float(v) for v in coordinates]


def policy_from_mask(profile, dense, corrections=()):
    if (dense != sorted(set(dense)) or not set(profile.protected_dense) <= set(dense)
            or set(dense) & set(corrections)):
        raise ValueError('Distinct ordered protected D and disjoint A required')
    edges = []
    for start, end in zip(dense, dense[1:]+[profile.horizon+1]):
        active = sorted(t for t in corrections if start < t < end)
        if active and (active != list(range(active[0], active[-1]+1))
                       or any(t-start != 1 for t in active)):
            raise ValueError('Fast A1 supports only one age-one correction per interval')
        edges.append(Edge(start, end, (active[0], active[-1]) if active else (),
                          (0.5 if active[0] >= 25 else 1.0) if active else 0.0))
    policy = compile_policy(profile, edges)
    actual_a = [i for i, a in enumerate(policy['actions'], 1) if a == 'A']
    if actual_a != sorted(corrections):
        raise ValueError('Correction outside the actual horizon')
    return policy


def audit_actions(policy):
    anchors, rows = [], []
    for t, action in enumerate(policy['actions'], 1):
        rows.append(dict(step=t, action=action, CFG_pair='DD' if action == 'D' else 'CC',
                         true_D_before=anchors[-1] if anchors else None,
                         source_age=t-anchors[-1] if anchors else None,
                         true_D_anchors_before=len(anchors), alpha=policy['shared_alpha'][t-1]))
        if action == 'D':
            anchors.append(t)
    return rows


def select_baselines(rows, native_rows, fit_members, grids, scope_sha256):
    """Complete two-FIT grid, same-device T_DD first, Alex as frozen tie-break.

    All configurations within 5% worst-prompt mismatch are eligible; choose
    their prompt-equal Alex mean. Otherwise choose nearest and label unmatched.
    """
    expected = {(m, family, candidate) for m in fit_members
                for family, candidates in grids.items() for candidate in candidates}
    identities = [(r['member'], r['family'], r['candidate']) for r in rows]
    if len(identities) != len(set(identities)) or set(identities) != expected:
        raise ValueError('Complete distinct FIT-only candidate denominator required')
    if len(native_rows) != len(fit_members) or {r['member'] for r in native_rows} != set(fit_members):
        raise ValueError('One matched Native reference for each FIT input required')
    all_rows = rows+native_rows
    contexts = {(r['host'], r['gpu_uuid'], r['scope_sha256']) for r in all_rows}
    if len(contexts) != 1 or next(iter(contexts))[2] != scope_sha256:
        raise ValueError('One host/device/scope required for finite selection')
    for row in all_rows:
        if (row['status'] != 'COMPLETE' or row.get('thermal_interrupted', False)
                or row.get('eligible_clean_time') is not True
                or type(row['T_DD']) not in (int, float)
                or not math.isfinite(row['T_DD']) or row['T_DD'] <= 0):
            raise ValueError('Clean complete selection paths required; no partial fallback')
    targets = {r['member']: r['T_DD']/1.5 for r in native_rows}
    selected = {}
    for family, candidates in grids.items():
        options = []
        for candidate in candidates:
            pair = [r for r in rows if r['family'] == family and r['candidate'] == candidate]
            if any(type(r['Alex']) not in (int, float) or not math.isfinite(r['Alex'])
                   or r['Alex'] < 0 for r in pair):
                raise ValueError('Complete finite Alex scores required after GPU release')
            options.append(dict(candidate=candidate,
                mismatch=max(abs(r['T_DD']/targets[r['member']]-1) for r in pair),
                Alex_mean=sum(r['Alex'] for r in pair)/len(pair)))
        eligible = [v for v in options if v['mismatch'] <= 0.05]
        choice = min(eligible, key=lambda v: (v['Alex_mean'], candidates.index(v['candidate']))) if eligible else min(
            options, key=lambda v: (v['mismatch'], v['Alex_mean'], candidates.index(v['candidate'])))
        selected[family] = dict(choice, time_match='MATCHED' if eligible else 'UNMATCHED', options=options)
    return dict(scope_sha256=scope_sha256, selection_rows_sha256=digest(all_rows), selected=selected,
                target='matched FIT Native T_DD / 1.5', CHECK_accessed=False)
