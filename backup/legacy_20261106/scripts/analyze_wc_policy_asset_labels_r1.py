#!/usr/bin/env python3
"""Describe all accepted CAL cells; no policy selection or threshold fitting."""
import argparse
from itertools import combinations
import json
from pathlib import Path
import statistics as st
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from audit_wc_policy_asset_prices_r1 import review
from wcomr.policy_interval_assets_r1 import read
from wcomr.policy_generator_r1.evaluation_analysis import spearman


def values(point):
    v = point['statistics']
    return dict(C=v['e2'], A_HALF=v['actual_half_MSE'], A_ONE=v['e2'] + 2*v['ed'] + v['d2'])


def summarize(points):
    rows = [values(p) for p in points]
    means = {a: st.mean(r[a] for r in rows) for a in ('C', 'A_HALF', 'A_ONE')}
    return dict(cells=len(rows), mean_MSE=means,
        relative_to_C={a: means[a]/means['C'] - 1 for a in ('A_HALF', 'A_ONE')},
        improved_cell_count={a: sum(r[a] < r['C'] for r in rows) for a in ('A_HALF', 'A_ONE')})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('capture', 'accepted', 'launch-ref', 'contention-ref', 'output'):
        p.add_argument('--' + key, required=True, type=Path)
    a = p.parse_args()
    checked = review(a.capture, a.accepted, a.launch_ref, a.contention_ref)
    capture = read(a.capture)
    rows = [r for r in capture['runner']['runs'] if r['section'] == 'FORMAL' and r['mode'] == 'COLLECT']
    scenes = [dict(scene=r['scene'], **summarize(r['interval_cells'])) for r in rows]
    by_age = []
    for lo, hi in ((1, 4), (5, 8), (9, 16), (17, 28)):
        by_age.append(dict(source_age_min=lo, source_age_max=hi, scenes=[dict(scene=r['scene'],
            **summarize([v for v in r['interval_cells'] if lo <= v['target'] - v['source'] <= hi])) for r in rows]))
    ranks = []
    for t in range(8, 36):
        groups = [[p for p in r['interval_cells'] if p['target'] == t] for r in rows]
        for i, j in combinations(range(4), 2):
            for action in ('C', 'A_HALF', 'A_ONE'):
                ranks.append(dict(target=t, source_count=len(groups[i]), action=action,
                    scene_pair=[rows[i]['scene'], rows[j]['scene']],
                    spearman=spearman([values(v)[action] for v in groups[i]],
                                      [values(v)[action] for v in groups[j]])))
    means = {action: st.mean(s['mean_MSE'][action] for s in scenes) for action in ('C','A_HALF','A_ONE')}
    result = dict(status='ACCEPTED_FULL1624_CAL_TEACHER_LABELS_DESCRIPTIVE_ONLY',
        source_bindings=checked['source_bindings'], formal_cells=1624, CAL_scenes=4, seeds=[0],
        scenes=scenes, prompt_equal_cell_mean_MSE=means,
        relative_to_C={action: means[action]/means['C'] - 1 for action in ('A_HALF','A_ONE')},
        age_groups=by_age, same_target_source_rank_agreement_across_CAL=ranks,
        A_HALF_basis='DIRECT_ACCEPTED_GUIDED_MSE', A_ONE_basis='ACCEPTED_FP64_MOMENT_IDENTITY',
        aggregation='SAME_406_CELLS_EQUAL_WITHIN_EACH_CAL_THEN_CAL_EQUAL',
        independent_sample_unit='PROMPT_NOT_CELL_OR_FRAME',
        new_independent_DEV_or_TEST=False, endpoint_quality_result=False,
        actual_policy_history_result=False, policy_or_threshold_fitted=False, GPU_submissions=0)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({k: result[k] for k in ('status','relative_to_C')}))


if __name__ == '__main__': main()
