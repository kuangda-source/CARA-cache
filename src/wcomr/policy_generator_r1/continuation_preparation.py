"""CPU-only handoff contracts. No model loading, dispatch, or outcome selection."""
import copy
import hashlib
import json
import math
import statistics

from .interval_grammar import Edge, Profile, compile_policy, digest
from .proposal_tables import Costs, QuadraticStats, make_proxy_graph

HISTORY_BINS = ((2, 4), (5, 8), (9, None))
TIME_BOUNDARY = 'COMPLETE_VIDEO_REQUEST_GUARDRAILS_SAMPLER_DECODE_WRITE_NO_DIAGNOSTICS'


def require(test, message):
    if not test:
        raise ValueError(message)


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def history_points(profile, policy):
    """First skipped target in each older-to-latest true-D gap bin, before outcomes."""
    edges = tuple(Edge(e['start'], e['end'], tuple(e['A_window']), e['alpha']) for e in policy['intervals'])
    rebuilt = compile_policy(profile, edges)
    for key in ('fingerprint', 'actions', 'shared_alpha', 'source_before', 'grammar_sha256'):
        require(policy[key] == rebuilt[key], 'Frozen policy differs from its legal interval compilation')
    anchors, found = [], {}
    for t, action in enumerate(policy['actions'], 1):
        if action == 'D':
            anchors.append(t)
            continue
        if len(anchors) < 2:
            continue
        p, s = anchors[-2:]
        for low, high in HISTORY_BINS:
            key = str(low) + '-' + (str(high) if high else 'plus')
            if s - p >= low and (high is None or s - p <= high) and key not in found:
                found[key] = dict(bin=key, previous=p, source=s, target=t,
                    actual_window=[p, s], adjacent_shadow_window=[s - 1, s],
                    adjacent_anchor_shadow_step=s - 1, target_shadow_step=t,
                    source_age=t - s, history_gap=s - p)
    expected = [str(a) + '-' + (str(b) if b else 'plus') for a, b in HISTORY_BINS]
    points = [found[k] for k in expected if k in found]
    shadows = sorted({x[k] for x in points for k in ('adjacent_anchor_shadow_step', 'target_shadow_step')})
    return dict(policy_fingerprint=policy['fingerprint'], points=points,
        empty_bins=[k for k in expected if k not in found], shadow_pair_steps=shadows,
        shadow_D_pairs=len(shadows), paired_readouts=6 * len(points),
        shadow_writes_parent=False, clean_deployment_timing=False)


def history_matrix(profile, roles, members):
    require(set(roles) == {'CARA', 'SIMPLE'}, 'Freeze final CARA and the SELECT-chosen feasible simple control')
    require(len(members) == len(set(members)) == 2, 'Use the first two registered CAL_FIT members')
    unique = {}
    for role, policy in roles.items():
        if policy['fingerprint'] not in unique:
            unique[policy['fingerprint']] = dict(roles=[], plan=history_points(profile, policy))
        unique[policy['fingerprint']]['roles'].append(role)
    rows = []
    for fingerprint, value in sorted(unique.items()):
        for section, scene in [('WARM', members[0])] + [('FORMAL', m) for m in members]:
            rows.append(dict(section=section, member=scene, seed=0, roles=value['roles'],
                policy_fingerprint=fingerprint, **{'diagnostic': value['plan']}))
    shadow = sum(r['diagnostic']['shadow_D_pairs'] for r in rows)
    return dict(rows=rows, physical_paths=len(rows), formal_paths=sum(r['section']=='FORMAL' for r in rows),
        ordinary_guided_pairs=len(rows) * profile.horizon, shadow_guided_pairs=shadow,
        total_CFG_calls=2 * (len(rows) * profile.horizon + shadow),
        paired_readouts=sum(r['diagnostic']['paired_readouts'] for r in rows),
        role_aliases_preserved=True, production_CPU_accepted=False, GPU_dispatch_ready=False)


def native_candidate_counts(schedule_rows, target_seconds, clean_native35_seconds):
    """Four nearest update-ratio predictions; screening is not a runtime result."""
    require(positive(target_seconds) and positive(clean_native35_seconds), 'Positive clean CAL times required')
    grid = {r['requested_steps']: r['actual_updates'] for r in schedule_rows}
    require(len(grid) == len(schedule_rows) and set(grid) == set(range(18, 36)), 'Complete CPU 18..35 schedule grid required')
    require(all(type(n) is int and n > 0 for n in grid.values()), 'Actual scheduler update counts required')
    predicted = {n: clean_native35_seconds * grid[n] / grid[35] for n in range(18, 35)}
    chosen = sorted(sorted(predicted, key=lambda n: (abs(predicted[n]-target_seconds), n))[:4])
    return dict(requested_steps=chosen, predicted_seconds={str(n): predicted[n] for n in chosen},
        selection_basis='CAL_TIME_ONLY_UPDATE_RATIO_SCREEN_NOT_MEASURED_LATENCY',
        target_seconds=target_seconds, max_candidates=4, formal_repeats=3,
        formal_CAL_members=4, warm_per_candidate=2, maximum_timing_paths=56,
        expand_after_quality_seen=False)


def select_native_by_time(rows, *, candidates, members, target_seconds, profile_identity):
    """Complete three-round timing design only. Refusals/missing slots cannot disappear."""
    require(positive(target_seconds), 'Positive frozen CARA CAL target time required')
    require(len(candidates) == len(set(candidates)) == 4 and len(members) == len(set(members)) == 4,
            'Frozen four Native counts and four CAL members required')
    keys = {'requested_steps','member','repeat','seconds','profile_identity','accepted',
            'exclusive_acceptance_sha256','timing_boundary'}
    by_key = {}
    for row in rows:
        require(set(row) == keys, 'Time-only input schema: no quality, LPIPS, or undeclared selection fields')
        require(row['accepted'] is True and row['profile_identity'] == profile_identity
                and row['timing_boundary'] == TIME_BOUNDARY, 'Same-profile accepted clean complete-request timings required')
        proof = row['exclusive_acceptance_sha256']
        require(isinstance(proof, str) and len(proof)==64 and all(c in '0123456789abcdef' for c in proof),
                'Bound independent exclusive timing acceptance required')
        key = (row['requested_steps'], row['member'], row['repeat'])
        require(key not in by_key and positive(row['seconds']), 'Unique positive timing slots required')
        by_key[key] = row['seconds']
    expected = {(n,m,r) for n in candidates for m in members for r in (1,2,3)}
    require(set(by_key) == expected, 'Full timing denominator required; rejected or missing slots block selection')
    means = {n: statistics.mean(statistics.mean(by_key[n,m,r] for r in (1,2,3)) for m in members) for n in candidates}
    matched = [n for n in candidates if abs(means[n]/target_seconds-1) <= .02]
    best = min(matched, key=lambda n: (abs(means[n]/target_seconds-1), means[n], n)) if matched else None
    # If no match, preserve two actually measured adjacent step counts, never interpolate quality.
    brackets = [(a,b) for a in sorted(candidates) for b in candidates if b == a+1
                and min(means[a],means[b]) <= target_seconds <= max(means[a],means[b])]
    pair = min(brackets, key=lambda ab: (abs(means[ab[0]]-target_seconds)+abs(means[ab[1]]-target_seconds), ab)) if brackets else None
    return dict(status='MATCHED_CAL_TIME' if best else ('MEASURED_BRACKET_ONLY' if pair else 'NO_CAL_TIME_MATCH'),
        selected_steps=[best] if best else list(pair or ()), mean_seconds={str(n):means[n] for n in sorted(means)},
        target_seconds=target_seconds, relative_tolerance=.02,
        nonmonotone_clock=any(means[a]>means[b] for a,b in zip(sorted(candidates), sorted(candidates)[1:])),
        heldout_time_match_guaranteed=False, quality_values_used=False, artificial_delay_allowed=False)


def generator_input(replacement_raw, price_acceptance, old_raw, old_acceptance, native_clock):
    """Explicit accepted-asset schema -> existing proposal CLI. Never consume old prices."""
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    new, old = json.loads(replacement_raw), json.loads(old_raw)
    require(price_acceptance.get('status') == 'FULL_PRICE_ORIGINALS_EXCLUSIVITY_AND_FINANCE_ACCEPTED'
            and price_acceptance.get('full_protocol_accepted') is True
            and price_acceptance.get('clean_action_prices_accepted') is True
            and price_acceptance.get('exclusive_monitoring',{}).get('accepted') is True,
            'Independent full clean-price acceptance required')
    require(price_acceptance['replacement_bundle_sha256']==sha(replacement_raw)
            and price_acceptance['original_label_bundle_sha256']==sha(old_raw), 'Accepted bundle bytes changed')
    require(old_acceptance.get('full_protocol_accepted') is True and old_acceptance.get('formal_source_time_cells')==1624,
            'Original complete four-CAL labels must be accepted')
    require(new.get('status')=='COMPLETE_OLD_LABELS_WITH_NEW_EXCLUSIVE_PRICES'
            and new.get('clean_action_prices_accepted') is True
            and new.get('exclusive_monitoring_accepted') is True
            and new.get('original_label_bundle_sha256')==sha(old_raw), 'Old contaminated bundle cannot pass through')
    require(new['statistics']==old['statistics'] and new['profile']==old['profile']
            and new['fit_members']==old['fit_members'], 'Repricing must not change labels, grammar, or split')
    members = new['fit_members']; identity = new['profile_identity']
    require(len(members)==len(set(members))==4 and len(new['statistics'])==1624, 'Complete original four CAL required')
    require(native_clock.get('status')=='CLEAN_NATIVE_CAL_COMPLETE_REQUEST_CLOCK_ACCEPTED'
            and native_clock.get('full_protocol_accepted') is True
            and native_clock.get('exclusive_monitoring_accepted') is True
            and native_clock.get('profile_identity')==identity
            and native_clock.get('timing_boundary')==TIME_BOUNDARY
            and native_clock.get('before_candidate_endpoints') is True,
            'B=.80 needs independent clean Native full-request CAL clock before candidates')
    rows = native_clock['rows']
    require(len(rows)==4 and {r['member'] for r in rows}==set(members)
            and all(r['seed']==0 and r['requested_steps']==35 and r['actual_updates']==36
                    and r['accepted'] is True and positive(r['seconds']) and positive(r['core_seconds'])
                    and r['core_seconds'] <= r['seconds'] for r in rows),
            'Keep all four registered Native CAL slots; no rejection substitution')
    pfields = ('horizon','protected_dense','max_source_age','min_C_anchors','min_A_anchors','alpha_candidates')
    p = {k:copy.deepcopy(new['profile'][k]) for k in pfields};p['identity']=identity
    cfields = ('dense_seconds','C_seconds','A_seconds_by_alpha','shared_seconds','profile_identity',
               'measurement_protocol','evidence_kind')
    costs = {k:copy.deepcopy(new['costs'][k]) for k in cfields}
    # Asset clocks cover generate_vid2world, while the new declared decision
    # clock includes guardrails and ordinary output writing. Add the measured
    # Native outside-core request overhead once, without changing asset bytes.
    outside_core = statistics.mean(r['seconds']-r['core_seconds'] for r in rows)
    costs['shared_seconds'] += outside_core
    costs['measurement_protocol'] += '_PLUS_CLEAN_NATIVE_OUTSIDE_CORE_REQUEST_OVERHEAD_ONCE'
    stats = [{**{k:v for k,v in r.items() if k!='target'}, 'update':r['target']} for r in new['statistics']]
    require(len({(r['member'],r['source'],r['update']) for r in stats})==1624, 'Duplicate proposal cells')
    require(new['label_basis']=='TEACHER_CONDITIONED_PROPOSAL', 'Preserve teacher-conditioned meaning')
    out = dict(profile=p, costs=costs, statistics=stats, CAL_FIT_members=members,
        weights=[1.]*p['horizon'], statistic_profile_identity=identity, label_basis=new['label_basis'],
        budget_seconds=.8*statistics.mean(r['seconds'] for r in rows), quantum_seconds=.25,
        paths_per_state=4, maximum_final_paths=32, Q=8,
        provenance=dict(original_label_bundle_sha256=sha(old_raw), replacement_bundle_sha256=sha(replacement_raw),
            price_acceptance_sha256=digest(price_acceptance), native_clock_acceptance_sha256=digest(native_clock),
            added_request_overhead_seconds=outside_core,
            overhead_is_proposal_estimate_not_exact_method_latency=True),
        production_CPU_accepted=False, GPU_dispatch_ready=False)
    pp = Profile(**{**p,'protected_dense':tuple(p['protected_dense']),'alpha_candidates':tuple(p['alpha_candidates'])})
    cc = Costs(**{**costs,'dense_seconds':tuple(costs['dense_seconds']),'C_seconds':tuple(costs['C_seconds']),
        'A_seconds_by_alpha':{float(a):tuple(v) for a,v in costs['A_seconds_by_alpha'].items()}})
    table = {(r['member'],r['source'],r['update']):QuadraticStats(r['e2'],r['ed'],r['d2'],r['fusion_contract']) for r in stats}
    graph = make_proxy_graph(pp, statistics=table, fit_members=tuple(members), costs=cc,
        weights=tuple(out['weights']), label_basis=out['label_basis'], statistic_profile_identity=identity)
    require(not graph['missing_cells'], 'Full legal graph coverage required before CPU proposals')
    return out
