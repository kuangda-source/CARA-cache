"""Descriptive CAL distributions, with no new candidate selection criterion."""
from math import isclose, isfinite, prod
from statistics import mean
from .w1d_summary import METRICS, summarize

MODES = ['official', 'scalar', 'shrink']


def ratio(numerator, denominator):
    return numerator / denominator if denominator > 0 else None


def checked_partition(score, family):
    shape = score['layout']['shape']
    total = prod(shape)
    groups = score['partitions'][family]
    rectangles = []
    for group in groups:
        bounds = [(0, size) for size in shape]
        for axis, interval in group['bounds'].items():
            axis = int(axis)
            if not 0 <= axis < len(shape):
                raise ValueError('Partition axis outside shape')
            start, end = interval
            if not 0 <= start < end <= shape[axis]:
                raise ValueError('Invalid partition bounds')
            bounds[axis] = (start, end)
        if prod(end-start for start, end in bounds) != group['elements']:
            raise ValueError('Partition element count differs from bounds')
        if group['metrics']['status'] != 'OK' or any(
            not isfinite(group['metrics'][key]) or group['metrics'][key] < 0
            for key in ['mse', 'reference_mean_square']
        ):
            raise ValueError('Invalid partition score')
        if any(all(max(a, c) < min(b, d) for (a, b), (c, d) in zip(bounds, old))
               for old in rectangles):
            raise ValueError('Overlapping partition groups')
        rectangles.append(bounds)
    if sum(group['elements'] for group in groups) != total:
        raise ValueError('Partition does not cover tensor')
    for key in ['mse', 'reference_mean_square']:
        weighted = sum(group['elements'] * group['metrics'][key] for group in groups) / total
        if not isclose(weighted, score[key], rel_tol=2e-5, abs_tol=1e-10):
            raise ValueError('Partition reductions do not reconstruct global '+key)
    return groups


def analyze(receipt, partial=False):
    screen = summarize(receipt, partial=partial)
    samples = []
    points = []
    for case in receipt['cases']:
        if case['status'] != 'PAIR_PARITY_PASS':
            continue
        records = case['on']['shadow_records']
        sample = {'name': case['name'], 'outcome': case['on']['outcome'], 'partitions': {}}
        for kind in METRICS:
            sample['partitions'][kind] = {}
            for family in ['time', 'spatial', 'channel']:
                reference = None
                sums = None
                counts = None
                for record in records:
                    scores = record['candidates']
                    groups = {mode: checked_partition(scores[mode][kind], family) for mode in MODES}
                    signature = {'layout': scores['official'][kind]['layout'],
                                 'groups': [{key: g[key] for key in ['bounds', 'elements']}
                                            for g in groups['official']]}
                    for mode in MODES:
                        if scores[mode][kind]['layout'] != signature['layout'] or [
                            {key: g[key] for key in ['bounds', 'elements']} for g in groups[mode]
                        ] != signature['groups']:
                            raise ValueError('Candidate partition geometry differs')
                    if reference is None:
                        reference = signature
                        sums = {mode: [0.0]*len(groups[mode]) for mode in MODES}
                        counts = {mode: [0]*len(groups[mode]) for mode in MODES[1:]}
                    elif signature != reference:
                        raise ValueError('Partition geometry changed within sample')
                    for mode in MODES:
                        for i, group in enumerate(groups[mode]):
                            sums[mode][i] += group['elements'] * group['metrics']['mse']
                            if mode != 'official':
                                counts[mode][i] += group['metrics']['mse'] < groups['official'][i]['metrics']['mse']
                rows = []
                if reference is not None:
                    for i, group in enumerate(reference['groups']):
                        rows.append(dict(group, official_error_share=ratio(sums['official'][i], sum(sums['official'])),
                            candidates={mode: {'sse_ratio_to_official': ratio(sums[mode][i], sums['official'][i]),
                                               'error_share': ratio(sums[mode][i], sum(sums[mode])),
                                               'improved_points': counts[mode][i], 'observed_points': len(records)}
                                        for mode in MODES[1:]}))
                sample['partitions'][kind][family] = {'layout': reference['layout'] if reference else None, 'groups': rows}
        samples.append(sample)
        for record in records:
            scores = record['candidates']
            points.append({'sample': case['name'], 'outcome': case['on']['outcome'],
                'call': record['call'], 'cfg_branch': record['cfg_branch'],
                'cache_age': record.get('cache_age_from_last_true_full'),
                'candidates': {mode: {'reason': scores[mode]['reason'], 'beta': scores[mode].get('beta'),
                    'metrics': {kind: {'mse': scores[mode][kind]['mse'],
                        'relative_mse': scores[mode][kind]['relative_mse'],
                        'direction_cosine': scores[mode][kind]['direction_cosine'],
                        'mse_ratio_to_official': ratio(scores[mode][kind]['mse'], scores['official'][kind]['mse'])}
                        for kind in METRICS}} for mode in MODES}})
    aggregate = {}
    for kind in METRICS:
        aggregate[kind] = {}
        for family in ['time', 'spatial', 'channel']:
            observed = [s['partitions'][kind][family] for s in samples if s['partitions'][kind][family]['groups']]
            rows = []
            if observed:
                reference = observed[0]
                for item in observed:
                    if item['layout'] != reference['layout'] or [g['bounds'] for g in item['groups']] != [g['bounds'] for g in reference['groups']]:
                        raise ValueError('Cross-sample group coordinates differ; do not silently pool')
                for i, group in enumerate(reference['groups']):
                    candidates = {}
                    for mode in MODES[1:]:
                        values = [s['groups'][i]['candidates'][mode]['sse_ratio_to_official'] for s in observed]
                        candidates[mode] = {'mean_sample_sse_ratio_to_official': mean(values) if all(v is not None for v in values) else None,
                            'improved_samples': sum(v is not None and v < 1 for v in values),
                            'defined_ratio_samples': sum(v is not None for v in values), 'observed_samples': len(values)}
                    shares = [s['groups'][i]['official_error_share'] for s in observed]
                    rows.append({'bounds': group['bounds'], 'mean_sample_official_error_share': mean(shares) if all(v is not None for v in shares) else None,
                                 'candidates': candidates})
            aggregate[kind][family] = rows
    return {'status': 'LIVE_PARTIAL_DESCRIPTIVE_NO_DECISION' if partial else 'DESCRIPTIVE_CAL8_TERMINAL',
            'frozen_screen_status': screen['status'], 'completed_pair_samples': screen['completed_pair_samples'],
            'planned_samples': 8, 'group_aggregate': aggregate, 'samples': samples, 'points': points,
            'ranking_reversals': [{'sample': s['name'], **r} for s in screen['samples'] for r in s['ranking_reversals']],
            'limitation': 'Descriptive distributions only; no extra selection thresholds. Each axis is a separate overlapping view, not independent evidence. Equal sample weighting. Latent time/space and hidden-feature channels are not decoded pixels or physical scores. CAL is reusable development; no causal, quality, deployed-candidate or speed claim.'}
