#!/usr/bin/env python3
"""Describe the observed N05 frontier without interpolation or per-scene selection."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def tradeoff(accepted):
    assert accepted['status'] in (
        'N05_CORE66_INDEPENDENTLY_ACCEPTED',
        'N05_CORE66_ACCEPTED_WITH_REJECTIONS_RETAINED',
    )
    assert accepted['full_denominator'] == 66 and accepted['formal_denominator'] == 44
    points = []
    incomplete = []
    scenes = None
    for row in accepted['independent_methods']:
        cases = row['scene_rows']
        names = tuple(x['scene'] for x in cases)
        assert len(names) == len(set(names)) == 4
        if scenes is None:
            scenes = names
        assert scenes == names
        t, q = row['mean_seconds'], row['mean_LPIPS']
        if t is None or q is None:
            incomplete.append(row['method'])
            continue
        assert math.isfinite(t) and t > 0 and math.isfinite(q) and q >= 0
        assert all(c.get('main_seconds') is not None and c.get('LPIPS') is not None for c in cases)
        assert math.isclose(sum(c['main_seconds'] for c in cases) / 4, t, rel_tol=1e-11)
        assert math.isclose(sum(c['LPIPS'] for c in cases) / 4, q, rel_tol=1e-11, abs_tol=1e-12)
        points.append(dict(method=row['method'], mean_seconds=t, mean_LPIPS=q))
    assert len(points) + len(incomplete) == 11

    def dominates(left, right):
        return (left['mean_seconds'] <= right['mean_seconds']
                and left['mean_LPIPS'] <= right['mean_LPIPS']
                and (left['mean_seconds'] < right['mean_seconds']
                     or left['mean_LPIPS'] < right['mean_LPIPS']))

    for point in points:
        point['dominated_by_observed_methods'] = [p['method'] for p in points if dominates(p, point)]
    comparisons = []
    for ours in (p for p in points if p['method'] in ('A_NO_P', 'TABLE_PHASE_H1')):
        for family in ('NATIVE', 'WC_', 'RA_'):
            baselines = [p for p in points if p['method'].startswith(family)]
            within_cost = [p for p in baselines if p['mean_seconds'] <= ours['mean_seconds']]
            within_loss = [p for p in baselines if p['mean_LPIPS'] <= ours['mean_LPIPS']]
            best_q = min(within_cost, key=lambda p: (p['mean_LPIPS'], p['mean_seconds'], p['method'])) if within_cost else None
            best_t = min(within_loss, key=lambda p: (p['mean_seconds'], p['mean_LPIPS'], p['method'])) if within_loss else None
            comparisons.append(dict(
                ours=ours['method'], baseline_family=family,
                observed_points_no_slower_than_ours=[p['method'] for p in within_cost],
                lowest_loss_baseline_no_slower_than_ours=best_q,
                observed_points_no_higher_loss_than_ours=[p['method'] for p in within_loss],
                fastest_baseline_no_higher_loss_than_ours=best_t,
                baseline_over_ours_seconds=best_t['mean_seconds'] / ours['mean_seconds'] if best_t else None,
            ))
    return dict(
        status='N05_OBSERVED_POINT_TRADEOFF_DESCRIPTION_NOT_REPEATED_LATENCY',
        scenes=list(scenes), scene_count=4, points=points, incomplete_methods=incomplete,
        observed_nondominated_methods=[p['method'] for p in points if not p['dominated_by_observed_methods']],
        operating_point_comparisons=comparisons,
        missing_points_excluded_with_original_denominator_retained=True,
        interpolation_used=False, per_scene_configuration_selection=False,
        statistical_significance_claim=False, stable_speed_claim=False,
        corrected_neighbor_gap_retained=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acceptance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = tradeoff(json.loads(args.acceptance.read_text()))
    result.update(acceptance_ref=str(args.acceptance), acceptance_sha256=hashlib.sha256(args.acceptance.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('points', 'operating_point_comparisons')}))


if __name__ == '__main__':
    main()
