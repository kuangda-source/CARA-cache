"""Independent stdlib reconstruction of complete64 records and all93 statistics.

Does not import the production summary, verifier, Torch, or LPIPS. It never
generates, scores, dispatches, or writes records. Original source receipts and
actual file hashes are verified by the two read-only capture entrypoints.
"""
from fractions import Fraction
import math

STRATEGIES = ('WORKING_P_AGE_KEEP_INTERVAL', 'WORKING_P_AGE_NONZERO_REBASE')
NAMES = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199',
         'misc_13398218_3840_2160_60fps', 'av_51b45829-502e-4143-9c32-c026bd6ab191')
METHODS = ('SOURCE_RA', 'DYNAMIC_NO_P', 'CPD', 'REF_CPD', 'A_CPD_OFF',
           'A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE', 'DENSE_CONTROL')
LEGACY_METHODS = ('WC', 'JOINT_NATIVE', 'RA', 'W1_GLOBAL_1', 'BETA1_GLOBAL_1',
                  'W1_ONE_PHASE', 'BETA1_ONE_PHASE')
WITHIN = (('DYNAMIC_NO_P', 'SOURCE_RA'), ('CPD', 'DYNAMIC_NO_P'),
          ('REF_CPD', 'CPD'), ('A_CPD_OFF', 'CPD'),
          ('A_CPD_W1_ONE_PHASE', 'CPD'), ('A_CPD_BETA1_ONE_PHASE', 'CPD'),
          ('A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE'), ('DENSE_CONTROL', 'SOURCE_RA'))
COUNTS = {'requests': 4, 'working_epoch_strategies': 2, 'methods_per_request': 8,
          'complete_paths': 64, 'maximum_videos': 64, 'solver_updates': 2304, 'net_calls': 4608,
          'maximum_guided_outputs': 2304, 'maximum_final_latents': 64,
          'reused_native_reference_slots': 4, 'maximum_fidelity_pairs': 64}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected):
    """Exact structure, finite numeric tolerance, no extra or missing fields."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), 'Dictionary fields differ')
        for k in expected:
            same(actual[k], expected[k])
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), 'List denominator differs')
        for a, b in zip(actual, expected):
            same(a, b)
    elif isinstance(expected, float):
        require(type(actual) in (int, float) and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), 'Numeric value differs')
    else:
        require(type(actual) is type(expected) and actual == expected, 'Scalar value or type differs')


def keys():
    return [(s, n, m) for s in STRATEGIES for n in NAMES for m in METHODS]


def slots_from_pairing(pairing):
    require(list(pairing) == list(STRATEGIES), 'Both original ordered strategy groups required')
    slots = []
    native = {}
    for strategy in STRATEGIES:
        g = pairing[strategy]
        require([(p['sample_name'], p['method']) for p in g['pairs']]
                == [(n, m) for n in NAMES for m in METHODS], 'Complete ordered32 slots per strategy required')
        require(g['complete_pairing_slots'] == 32
                and g['compatible_pairs'] == sum(p['compatible'] for p in g['pairs'])
                and g['incompatible_pairs'] == sum(not p['compatible'] for p in g['pairs']),
                'Pairing counts differ')
        for p in g['pairs']:
            require(type(p['compatible']) is bool and p['checks']
                    and all(type(v) is bool for v in p['checks'].values())
                    and p['compatible'] == all(p['checks'].values())
                    and p['incompatible_fields'] == [k for k, v in p['checks'].items() if not v]
                    and p['no_replacement_or_other_seed'] is True, 'Pairing verdict or missing fields differ')
            name = p['sample_name']
            require(name not in native or native[name] == p['Native_artifact'], 'Original Native differs across methods')
            native[name] = p['Native_artifact']
            slots.append({'strategy': strategy, **p})
    return slots


def costs_from_runner(runner):
    require(runner['planned_scope'] == COUNTS and runner['completed_strategies'] == list(STRATEGIES),
            'Complete original scope and strategy completion required')
    costs = []
    for strategy in STRATEGIES:
        requests = runner['batches'][strategy]['requests']
        require([r['sample_name'] for r in requests] == list(NAMES), 'Original four requests required')
        for request in requests:
            require([r['collect'] for r in request['paths']] == list(METHODS), 'Original eight methods required')
            for row in request['paths']:
                actions = row['actions']; c = row['collection_complete']
                wall = row['instrumented_parent_pipeline_wall_seconds']
                require(row['status'] == 'COMPLETE_PARENT_PATH' and c['complete_pairs'] == 36
                        and len(actions) == 36 and all(a in ('CC', 'PP', 'DD') for a in actions)
                        and type(wall) in (int, float) and math.isfinite(wall) and wall >= 0,
                        'Incomplete actions or nonfinite/negative actual cost')
                require(row['collect'] != 'DENSE_CONTROL' or actions == ['DD'] * 36, 'Dense control was not full')
                d = c.get('deployment'); a = d['A_readout'] if d is not None else None
                extra = a['extra_candidate_heads'] if a else 0
                require(type(extra) is int and extra >= 0
                        and len(c['actual_original_plus_candidate_heads']) == 72 + extra
                        and (not a or a['teacher_calls'] == a['extra_candidate_deep_blocks'] == 0),
                        'Head cost or forbidden teacher/deep work differs')
                costs.append({'strategy': strategy, 'sample_name': request['sample_name'], 'method': row['collect'],
                    'actions': actions, 'dense_pair_steps': [i + 1 for i, a in enumerate(actions) if a == 'DD'],
                    'partial_pair_steps': [i + 1 for i, a in enumerate(actions) if a == 'PP'],
                    'reuse_pair_steps': [i + 1 for i, a in enumerate(actions) if a == 'CC'],
                    'complete_branch_calls': 2 * actions.count('DD'), 'partial_branch_calls': 2 * actions.count('PP'),
                    'reuse_branch_calls': 2 * actions.count('CC'), 'extra_candidate_heads': extra,
                    'teacher_calls': 0, 'extra_candidate_deep_blocks': 0,
                    'instrumented_pipeline_wall_seconds': wall, 'clean_speed_claim': False,
                    'fixed_order_single_run': True})
    return costs


def verify_pair(p):
    s = p['score']; values = s['frame_distances']
    require(s['frames'] == len(values) == len(s['pts']) == 93, 'Original all93 score required')
    require(all(type(v) in (int, float) and math.isfinite(v) for v in values), 'Nonfinite score')
    pts = [Fraction(v) * Fraction(t) for v, t in s['pts']]
    require(all(b > a for a, b in zip(pts, pts[1:])), 'Actual timestamps must strictly increase')
    for kind in ('reference', 'candidate'):
        h = p[kind]['sha256']
        require(type(h) is str and len(h) == 64 and all(c in '0123456789abcdef' for c in h)
                and s[kind + '_sha256'] == h, 'Actual original score/video identity differs')
    require(type(s['mean_LPIPS']) in (int, float) and math.isfinite(s['mean_LPIPS']), 'Nonfinite score mean')
    same(s['mean_LPIPS'], math.fsum(values) / 93)
    return s


def average(values):
    return math.fsum(values) / len(values) if values else None


def comparison(candidate, baseline, scored, costs=None):
    rows = []; gaps = []
    for name in NAMES:
        ck = (candidate[0], name, candidate[1]); bk = (baseline[0], name, baseline[1])
        a = scored.get(ck); b = scored.get(bk)
        if a is None or b is None:
            gaps.append({'sample_name': name, 'candidate_available': a is not None, 'baseline_available': b is not None})
            continue
        require(a['reference']['sha256'] == b['reference']['sha256'] and a['score']['pts'] == b['score']['pts'],
                'Comparison Native or paired timestamps differ')
        delta = [x - y for x, y in zip(b['score']['frame_distances'], a['score']['frame_distances'])]
        ordered = sorted(delta); quantiles = {}
        for q in (0, .1, .25, .5, .75, .9, 1):
            p = 92 * q; lo = math.floor(p); hi = math.ceil(p)
            quantiles[str(q)] = ordered[lo] + (ordered[hi] - ordered[lo]) * (p - lo)
        row = {'sample_name': name, 'baseline_LPIPS': b['score']['mean_LPIPS'],
            'candidate_LPIPS': a['score']['mean_LPIPS'], 'baseline_minus_candidate_LPIPS': average(delta),
            'improved_frames': sum(v > 0 for v in delta), 'degraded_frames': sum(v < 0 for v in delta),
            'tied_frames': sum(v == 0 for v in delta), 'frame_count': 93,
            'quantiles_type7': quantiles, 'contiguous_frame_bin_means': [average(delta[i:i + 31]) for i in (0, 31, 62)],
            'frames_are_independent_samples': False}
        if costs is not None:
            row.update(baseline_minus_candidate_instrumented_seconds=
                costs[bk]['instrumented_pipeline_wall_seconds'] - costs[ck]['instrumented_pipeline_wall_seconds'],
                baseline_minus_candidate_complete_branch_calls=
                costs[bk]['complete_branch_calls'] - costs[ck]['complete_branch_calls'], clean_speed_claim=False)
        rows.append(row)
    bmean = average([r['baseline_LPIPS'] for r in rows]); amean = average([r['candidate_LPIPS'] for r in rows])
    return {'candidate': list(candidate), 'baseline': list(baseline), 'registered_scenes': 4,
        'matched_scenes': len(rows), 'gaps': gaps, 'per_scene': rows,
        'scene_equal_mean_baseline_minus_candidate': average([r['baseline_minus_candidate_LPIPS'] for r in rows]),
        'relative_fidelity_improvement_ratio_of_paired_means_percent':
            100 * (bmean - amean) / bmean if bmean is not None and bmean > 0 else None,
        'improved_scenes': sum(r['baseline_minus_candidate_LPIPS'] > 0 for r in rows),
        'degraded_scenes': sum(r['baseline_minus_candidate_LPIPS'] < 0 for r in rows),
        'tied_scenes': sum(r['baseline_minus_candidate_LPIPS'] == 0 for r in rows),
        'same_card_instrumented_cost_comparison': costs is not None, 'clean_speed_claim': False,
        'matched_time_or_call_budget': False, 'development_not_independent_confirmation': True}


def reconstruct_summary(pairs, pairing, costs, legacy):
    slots = slots_from_pairing(pairing)
    expected = [(s['strategy'], s['sample_name'], s['method']) for s in slots if s['compatible']]
    require([(p['strategy'], p['sample_name'], p['method']) for p in pairs] == expected, 'Score subset, duplication, or order differs')
    require([(c['strategy'], c['sample_name'], c['method']) for c in costs] == keys(), 'All original64 costs required')
    bycost = {}; scored = {}; pts = {}; rows = []
    for c in costs:
        actions = c['actions']
        require(len(actions) == 36 and all(a in ('CC', 'PP', 'DD') for a in actions), 'Incomplete cost action sequence')
        require(all(c[k] == 2 * actions.count(a) for k, a in
                    [('complete_branch_calls', 'DD'), ('partial_branch_calls', 'PP'), ('reuse_branch_calls', 'CC')])
                and sum(c[k] for k in ('complete_branch_calls', 'partial_branch_calls', 'reuse_branch_calls')) == 72
                and math.isfinite(c['instrumented_pipeline_wall_seconds']) and c['instrumented_pipeline_wall_seconds'] >= 0
                and c['teacher_calls'] == c['extra_candidate_deep_blocks'] == 0, 'Cost reconstruction differs')
        bycost[(c['strategy'], c['sample_name'], c['method'])] = c
    slotmap = {(s['strategy'], s['sample_name'], s['method']): s for s in slots}
    for p in pairs:
        key = (p['strategy'], p['sample_name'], p['method']); s = verify_pair(p); slot = slotmap[key]
        require(p['reference'] == slot['Native_artifact'] and p['candidate'] == slot['video_artifact'], 'Scored actual slot differs')
        require(key[1] not in pts or pts[key[1]] == s['pts'], 'Same Native timestamps across methods required')
        pts[key[1]] = s['pts']; scored[key] = p
    for slot in slots:
        key = (slot['strategy'], slot['sample_name'], slot['method']); p = scored.get(key)
        rows.append({'strategy': key[0], 'sample_name': key[1], 'method': key[2],
            'compatible': slot['compatible'], 'incompatible_fields': slot['incompatible_fields'],
            'scored': p is not None, 'mean_LPIPS': p['score']['mean_LPIPS'] if p else None,
            'recorded_cost': bycost[key], 'missing_score_filled_with_zero': False})
    aggregates = []
    for strategy in STRATEGIES:
        for method in METHODS:
            own = [r for r in rows if r['strategy'] == strategy and r['method'] == method and r['scored']]
            aggregates.append({'strategy': strategy, 'method': method, 'registered_scenes': 4,
                'matched_scenes': len(own), 'scene_equal_mean_LPIPS': average([r['mean_LPIPS'] for r in own])})
    comparisons = [comparison((s, a), (s, b), scored, bycost) for s in STRATEGIES for a, b in WITHIN]
    comparisons += [comparison((STRATEGIES[1], m), (STRATEGIES[0], m), scored, bycost) for m in METHODS]
    require([(p['sample_name'], p['method']) for p in legacy['pairs']]
            == [(n, m) for n in NAMES for m in LEGACY_METHODS], 'Original28 legacy score denominator required')
    for p in legacy['pairs']:
        verify_pair(p); scored[('LEGACY32', p['sample_name'], p['method'])] = p
    old = [comparison((s, m), ('LEGACY32', b), scored)
           for s in STRATEGIES for m in METHODS for b in ('WC', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE')]
    return {'registered_method_paths': 64, 'registered_reference_slots': 4,
        'scored_pairs': len(pairs), 'actual_frame_distances': 93 * len(pairs),
        'incompatible_pairs_retained': 64 - len(pairs), 'per_slot': rows, 'scene_equal_aggregates': aggregates,
        'registered_same_card_contrasts': comparisons, 'legacy_quality_only_contrasts': old,
        'clean_speed_claim': False, 'frames_are_independent_samples': False,
        'fidelity_not_semantic_or_physics_quality': True, 'development_not_independent_confirmation': True,
        'single_threshold_direction_rejection': False, 'missing_scores_filled_with_zero': False}
