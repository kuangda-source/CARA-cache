#!/usr/bin/env python3
"""Describe all accepted replacement prices without changing their aggregator."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics as st
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.policy_asset_price_review_r1 import distribution
from wcomr.policy_price_terminal_r1 import accept, record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('capture', 'accepted', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    raw = a.capture.read_bytes()
    cap, accepted = json.loads(raw), json.loads(a.accepted.read_text())
    old = json.loads((ROOT / 'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json').read_text())
    oldacc = json.loads((ROOT / 'reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json').read_text())
    verified = accept(cap, old, oldacc)
    verified.update(capture_ref=str(a.capture), capture_sha256=hashlib.sha256(raw).hexdigest())
    if accepted != verified:
        raise ValueError('Full independent price acceptance does not reproduce')
    actions = ('C', 'A_HALF', 'A_ONE')
    runs = [r for r in record(cap, 'runner')['runs'] if r['section'] == 'FORMAL' and r['mode'] == 'PRICE']
    points, repeated, amplification, sequence = [], [], [], []
    for run in runs:
        for cell in run['price_cells']:
            point = dict(scene=run['scene'], source=cell['source'], target=cell['target'], means={})
            for action in actions:
                xs = [t['seconds'] for t in cell['price_trials'] if t['action'] == action and t['round'] != 'WARMUP']
                assert len(xs) == 3
                point['means'][action] = st.mean(xs)
                repeated.append(dict(scene=run['scene'], source=cell['source'], target=cell['target'], action=action,
                    sample_CV=st.stdev(xs)/st.mean(xs), round2_over_round1=xs[1]/xs[0], round3_over_round1=xs[2]/xs[0]))
            points.append(point)
    assert len(points) == 1624 and len(repeated) == 4872
    for run in runs:
        scene = run['scene']
        for target in range(8, 36):
            group = [p for p in points if p['scene'] == scene and p['target'] == target]
            for action in actions:
                xs = [p['means'][action] for p in group]
                amplification.append(dict(scene=scene, target=target, action=action, max_source_over_median_source=max(xs)/st.median(xs)))
        row = dict(scene=scene)
        for action in actions:
            ratios = []
            for point in (p for p in points if p['scene'] == scene):
                matched = [p['means'][action] for p in points if (p['source'], p['target']) == (point['source'], point['target'])]
                ratios.append(point['means'][action]/st.median(matched))
            row[action] = distribution(ratios)
        sequence.append(row)
    result = dict(status='ACCEPTED_EXCLUSIVE_FULL1624_DESCRIPTIVE_PRICE_ANALYSIS', capture_ref=str(a.capture),
        capture_sha256=verified['capture_sha256'], acceptance_ref=str(a.accepted), formal_cells=1624,
        triply_measured_cells=1624, formal_readout_trials=14616, formal_cell_warm_trials_excluded=4872,
        full_warm_path_trials_excluded=4872, repeated_action_summary={action: {key: distribution(r[key] for r in repeated if r['action'] == action)
            for key in ('sample_CV', 'round2_over_round1', 'round3_over_round1')} for action in actions},
        source_max_amplification={action: distribution(r['max_source_over_median_source'] for r in amplification if r['action'] == action) for action in actions},
        matched_cell_sequence_ratios=sequence, sequence_is_confounded_with_scene=True,
        round_drift_is_confounded_with_action_order=True, clean_acceptance_basis='Independent original parity, continuous exclusivity and finance acceptance; not low CV',
        original_aggregator_unchanged='MAX_SOURCE_WITHIN_PROMPT_THEN_PROMPT_EQUAL',
        endpoint_quality_or_deployment_speed_result=False, repeated_cells=repeated, source_max_cells=amplification)
    with a.output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','formal_cells','repeated_action_summary','source_max_amplification','matched_cell_sequence_ratios')}))


if __name__ == '__main__':
    main()
