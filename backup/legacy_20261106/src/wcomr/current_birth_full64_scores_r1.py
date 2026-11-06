"""Complete64 fidelity/cost summaries; incompatible slots remain explicit."""
import math
from statistics import mean

from .current_birth_real_production_r1 import COUNTS, METHODS, STRATEGIES
from .cfg_guided_w1_deployment_production import NAMES
from .cfg_ra_plus_a_scores import METHODS as LEGACY_METHODS, quantile

WITHIN_CONTRASTS = (
    ('DYNAMIC_NO_P', 'SOURCE_RA'), ('CPD', 'DYNAMIC_NO_P'),
    ('REF_CPD', 'CPD'), ('A_CPD_OFF', 'CPD'),
    ('A_CPD_W1_ONE_PHASE', 'CPD'), ('A_CPD_BETA1_ONE_PHASE', 'CPD'),
    ('A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE'),
    ('DENSE_CONTROL', 'SOURCE_RA'))
LEGACY_BASELINES = ('WC', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE')


def ordered_keys():
    return [(s, n, m) for s in STRATEGIES for n in NAMES for m in METHODS]


def pairing_slots(pairing):
    if list(pairing) != list(STRATEGIES):
        raise ValueError('Both original strategies in registered order required')
    slots = []
    for strategy in STRATEGIES:
        group = pairing[strategy]
        pairs = group['pairs']
        if ([(p['sample_name'], p['method']) for p in pairs]
                != [(n, m) for n in NAMES for m in METHODS]
                or group['complete_pairing_slots'] != 32
                or any(type(p['compatible']) is not bool for p in pairs)
                or group['compatible_pairs'] != sum(p['compatible'] for p in pairs)
                or group['incompatible_pairs'] != sum(not p['compatible'] for p in pairs)):
            raise ValueError('Complete32 compatibility denominator per strategy required')
        for p in pairs:
            if (not p['no_replacement_or_other_seed']
                    or not p['checks'] or any(type(v) is not bool for v in p['checks'].values())
                    or p['compatible'] != all(p['checks'].values())
                    or p['incompatible_fields'] != [k for k, v in p['checks'].items() if not v]):
                raise ValueError('Actual compatibility verdict and fields differ')
            slots.append({'strategy': strategy, **p})
    native = {}
    for p in slots:
        n = p['sample_name']; art = p['Native_artifact']
        if n in native and native[n] != art:
            raise ValueError('Same original Native artifact per scene required')
        native[n] = art
    return slots


def actual_costs(runner):
    if runner['planned_scope'] != COUNTS or runner['completed_strategies'] != list(STRATEGIES):
        raise ValueError('Original complete64 scope and completed strategies required')
    result = []
    for strategy in STRATEGIES:
        requests = runner['batches'][strategy]['requests']
        if [r['sample_name'] for r in requests] != NAMES:
            raise ValueError('All original four requests required')
        for request in requests:
            if [r['collect'] for r in request['paths']] != list(METHODS):
                raise ValueError('All eight methods required for costs')
            for row in request['paths']:
                actions = row['actions']; c = row['collection_complete']
                wall = row['instrumented_parent_pipeline_wall_seconds']
                if (len(actions) != 36 or any(a not in ('DD', 'CC', 'PP') for a in actions)
                        or type(wall) not in (int, float) or not math.isfinite(wall) or wall < 0
                        or row['status'] != 'COMPLETE_PARENT_PATH' or c['complete_pairs'] != 36
                        or row['collect'] == 'DENSE_CONTROL' and actions != ['DD'] * 36):
                    raise ValueError('Actual complete path cost and action sequence required')
                d = c.get('deployment'); a = d['A_readout'] if d is not None else None
                extra = a['extra_candidate_heads'] if a else 0
                if (type(extra) is not int or extra < 0
                        or len(c['actual_original_plus_candidate_heads']) != 72 + extra
                        or a and (a['teacher_calls'] or a['extra_candidate_deep_blocks'])):
                    raise ValueError('Actual head count or forbidden teacher/deep work differs')
                result.append({'strategy': strategy, 'sample_name': request['sample_name'],
                    'method': row['collect'], 'actions': actions,
                    'dense_pair_steps': [i+1 for i, v in enumerate(actions) if v == 'DD'],
                    'partial_pair_steps': [i+1 for i, v in enumerate(actions) if v == 'PP'],
                    'reuse_pair_steps': [i+1 for i, v in enumerate(actions) if v == 'CC'],
                    'complete_branch_calls': 2 * actions.count('DD'),
                    'partial_branch_calls': 2 * actions.count('PP'),
                    'reuse_branch_calls': 2 * actions.count('CC'),
                    'extra_candidate_heads': extra, 'teacher_calls': 0, 'extra_candidate_deep_blocks': 0,
                    'instrumented_pipeline_wall_seconds': wall,
                    'clean_speed_claim': False, 'fixed_order_single_run': True})
    return result


def checked_score(p):
    s = p['score']; values = s['frame_distances']
    digests = [p['reference']['sha256'], p['candidate']['sha256']]
    if (any(type(h) is not str or len(h) != 64 or any(c not in '0123456789abcdef' for c in h) for h in digests)
            or s['reference_sha256'] != digests[0] or s['candidate_sha256'] != digests[1]
            or s['frames'] != 93 or len(values) != 93 or len(s['pts']) != 93
            or len({tuple(t) for t in s['pts']}) != 93
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
            or type(s['mean_LPIPS']) not in (int, float) or not math.isfinite(s['mean_LPIPS'])
            or not math.isclose(sum(values)/93, s['mean_LPIPS'], rel_tol=1e-12, abs_tol=1e-12)):
        raise ValueError('All93 finite distances, PTS, identity and mean required')
    return s


def contrast(candidate, baseline, scored, costs=None):
    rows = []; gaps = []
    for name in NAMES:
        ck, bk = (*candidate[:1], name, candidate[1]), (*baseline[:1], name, baseline[1])
        a, b = scored.get(ck), scored.get(bk)
        if a is None or b is None:
            gaps.append({'sample_name': name, 'candidate_available': a is not None,
                'baseline_available': b is not None}); continue
        if a['reference']['sha256'] != b['reference']['sha256'] or a['score']['pts'] != b['score']['pts']:
            raise ValueError('Contrast requires the same actual Native and paired93 timestamps')
        delta = [x-y for x, y in zip(b['score']['frame_distances'], a['score']['frame_distances'])]
        item = {'sample_name': name, 'baseline_LPIPS': b['score']['mean_LPIPS'],
            'candidate_LPIPS': a['score']['mean_LPIPS'], 'baseline_minus_candidate_LPIPS': mean(delta),
            'improved_frames': sum(v > 0 for v in delta), 'degraded_frames': sum(v < 0 for v in delta),
            'tied_frames': sum(v == 0 for v in delta), 'frame_count': 93,
            'quantiles_type7': {str(q): quantile(delta, q) for q in (0, .1, .25, .5, .75, .9, 1)},
            'contiguous_frame_bin_means': [mean(delta[i:i+31]) for i in (0, 31, 62)],
            'frames_are_independent_samples': False}
        if costs is not None:
            item.update(baseline_minus_candidate_instrumented_seconds=
                costs[bk]['instrumented_pipeline_wall_seconds']-costs[ck]['instrumented_pipeline_wall_seconds'],
                baseline_minus_candidate_complete_branch_calls=
                costs[bk]['complete_branch_calls']-costs[ck]['complete_branch_calls'], clean_speed_claim=False)
        rows.append(item)
    bmean = mean(r['baseline_LPIPS'] for r in rows) if rows else None
    amean = mean(r['candidate_LPIPS'] for r in rows) if rows else None
    return {'candidate': list(candidate), 'baseline': list(baseline), 'registered_scenes': 4,
        'matched_scenes': len(rows), 'gaps': gaps, 'per_scene': rows,
        'scene_equal_mean_baseline_minus_candidate': mean(r['baseline_minus_candidate_LPIPS'] for r in rows) if rows else None,
        'relative_fidelity_improvement_ratio_of_paired_means_percent': 100*(bmean-amean)/bmean if bmean is not None and bmean > 0 else None,
        'improved_scenes': sum(r['baseline_minus_candidate_LPIPS'] > 0 for r in rows),
        'degraded_scenes': sum(r['baseline_minus_candidate_LPIPS'] < 0 for r in rows),
        'tied_scenes': sum(r['baseline_minus_candidate_LPIPS'] == 0 for r in rows),
        'same_card_instrumented_cost_comparison': costs is not None, 'clean_speed_claim': False,
        'matched_time_or_call_budget': False, 'development_not_independent_confirmation': True}


def summarize(pairs, pairing, costs, legacy=None):
    slots = pairing_slots(pairing); expected = [(p['strategy'], p['sample_name'], p['method']) for p in slots if p['compatible']]
    if ([(p['strategy'], p['sample_name'], p['method']) for p in pairs] != expected
            or [(c['strategy'], c['sample_name'], c['method']) for c in costs] != ordered_keys()):
        raise ValueError('Every compatible pair and all64 actual cost slots required')
    bykey = {}; bycost = {}; reference_pts = {}; rows = []
    for c in costs:
        if (len(c['actions']) != 36 or any(a not in ('DD', 'CC', 'PP') for a in c['actions'])
                or sum(c[k] for k in ('complete_branch_calls', 'partial_branch_calls', 'reuse_branch_calls')) != 72
                or c['complete_branch_calls'] != 2*c['actions'].count('DD')
                or c['partial_branch_calls'] != 2*c['actions'].count('PP')
                or c['reuse_branch_calls'] != 2*c['actions'].count('CC')
                or not math.isfinite(c['instrumented_pipeline_wall_seconds']) or c['instrumented_pipeline_wall_seconds'] < 0
                or c['teacher_calls'] or c['extra_candidate_deep_blocks']):
            raise ValueError('All64 actual cost/action slots must be finite and internally consistent')
        bycost[(c['strategy'], c['sample_name'], c['method'])] = c
    for p in pairs:
        key = (p['strategy'], p['sample_name'], p['method']); s = checked_score(p)
        slot = next(v for v in slots if (v['strategy'], v['sample_name'], v['method']) == key)
        if p['reference'] != slot['Native_artifact'] or p['candidate'] != slot['video_artifact']:
            raise ValueError('Scored video must be the original actual compatible slot')
        if key[1] in reference_pts and reference_pts[key[1]] != s['pts']:
            raise ValueError('All methods must use the same Native timestamps')
        reference_pts[key[1]] = s['pts']; bykey[key] = p
    for slot in slots:
        key = (slot['strategy'], slot['sample_name'], slot['method']); p = bykey.get(key)
        rows.append({'strategy': key[0], 'sample_name': key[1], 'method': key[2],
            'compatible': slot['compatible'], 'incompatible_fields': slot['incompatible_fields'],
            'scored': p is not None, 'mean_LPIPS': p['score']['mean_LPIPS'] if p else None,
            'recorded_cost': bycost[key], 'missing_score_filled_with_zero': False})
    aggregates = []
    for strategy in STRATEGIES:
        for method in METHODS:
            own = [r for r in rows if r['strategy'] == strategy and r['method'] == method and r['scored']]
            aggregates.append({'strategy': strategy, 'method': method, 'registered_scenes': 4,
                'matched_scenes': len(own), 'scene_equal_mean_LPIPS': mean(r['mean_LPIPS'] for r in own) if own else None})
    comparisons = [contrast((s, a), (s, b), bykey, bycost) for s in STRATEGIES for a, b in WITHIN_CONTRASTS]
    comparisons += [contrast((STRATEGIES[1], m), (STRATEGIES[0], m), bykey, bycost) for m in METHODS]
    legacy_contrasts = []
    if legacy is not None:
        if [(p['sample_name'], p['method']) for p in legacy['pairs']] != [(n, m) for n in NAMES for m in LEGACY_METHODS]:
            raise ValueError('Retain the complete original28 legacy scores')
        for p in legacy['pairs']:
            checked_score(p); key = ('LEGACY32', p['sample_name'], p['method'])
            bykey[key] = p
        legacy_contrasts = [contrast((s, m), ('LEGACY32', b), bykey)
            for s in STRATEGIES for m in METHODS for b in LEGACY_BASELINES]
    return {'registered_method_paths': 64, 'registered_reference_slots': 4,
        'scored_pairs': len(pairs), 'actual_frame_distances': 93*len(pairs),
        'incompatible_pairs_retained': len(slots)-len(pairs), 'per_slot': rows,
        'scene_equal_aggregates': aggregates, 'registered_same_card_contrasts': comparisons,
        'legacy_quality_only_contrasts': legacy_contrasts,
        'clean_speed_claim': False, 'frames_are_independent_samples': False,
        'fidelity_not_semantic_or_physics_quality': True, 'development_not_independent_confirmation': True,
        'single_threshold_direction_rejection': False, 'missing_scores_filled_with_zero': False}
