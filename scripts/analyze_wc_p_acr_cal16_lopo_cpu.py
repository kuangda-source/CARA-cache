"""Pre-registered held-prompt scalar experiment; no test-point coefficient fit."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.p_acr_e0_analysis import fixed_direction_error

PREREG = 'manifests/wc_p_acr_cal16_lopo_cpu_prereg_20261014.json'


def fit_and_predict(rows, held, grouping, direction):
    train = [r for r in rows if r['scene'] != held]
    test = [r for r in rows if r['scene'] == held]
    if len(train) != 12 or len(test) != 4:
        raise ValueError('Complete held-prompt folds required')
    out = []
    def cell(r):
        return 'GLOBAL' if grouping == 'GLOBAL_SCALAR' else r['source'] + '_' + r['phase']
    for row in test:
        group = [r for r in train if cell(r) == cell(row)]
        if not group or any(r['scene'] == held for r in group):
            raise ValueError('Held-prompt leakage')
        denom = sum(r['moments']['mc' if direction == 'Pc' else 'mu'] for r in group)
        if denom <= 0:
            raise ValueError('Explicit unsupported coefficient group')
        coefficient = sum(r['moments']['cross'] for r in group) / denom
        m = row['moments']
        loss = fixed_direction_error(m['mc'], m['mu'], m['cross'], direction, coefficient)
        out.append({'held_scene': held, 'step': row['step'], 'source': row['source'], 'phase': row['phase'],
                    'model': grouping, 'direction': direction, 'coefficient_from_train_only': coefficient,
                    'training_scenes': sorted({r['scene'] for r in group}), 'training_points': len(group),
                    'q_A': row['q_base'], 'q_P_frozen_coefficient': loss,
                    'q_P_oracle': row['q_' + direction + '_oracle'],
                    'q_P_fixed0': row['fixed_0'][direction], 'q_P_fixed1': row['fixed_1'][direction],
                    'loss_reduction_fraction': (row['q_base'] - loss) / row['q_base']})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', type=Path, required=True); args = ap.parse_args()
    pre = json.loads((ROOT / PREREG).read_text())
    raw = json.loads((ROOT / pre['input']).read_text())
    rows = [r for r in raw['families'] if r['readout'] == 'FUSION_A']
    scenes = sorted({r['scene'] for r in rows})
    if len(scenes) != 4 or len(rows) != 16:
        raise ValueError('Original all16 paired states required')
    evaluations = [r for model in pre['models'] for direction in ('Pc', 'Pu') for held in scenes
                   for r in fit_and_predict(rows, held, model, direction)]
    summaries = []
    for model in pre['models']:
        for direction in ('Pc', 'Pu'):
            rr = [r for r in evaluations if r['model'] == model and r['direction'] == direction]
            prompts = [{'scene': scene, 'q_A': mean(r['q_A'] for r in rr if r['held_scene'] == scene),
                        'q_P': mean(r['q_P_frozen_coefficient'] for r in rr if r['held_scene'] == scene)} for scene in scenes]
            qa = mean(p['q_A'] for p in prompts); qp = mean(p['q_P'] for p in prompts)
            summaries.append({'model': model, 'direction': direction, 'q_A_prompt_equal_mean': qa,
                              'q_P_prompt_equal_mean': qp, 'loss_reduction_fraction': 1 - qp / qa,
                              'improved_prompts': sum(p['q_P'] < p['q_A'] for p in prompts),
                              'improved_points': sum(r['q_P_frozen_coefficient'] < r['q_A'] for r in rr),
                              'oracle_loss_reduction_fraction': 1 - mean(r['q_P_oracle'] for r in rr) / qa,
                              'fixed1_loss_reduction_fraction': 1 - mean(r['q_P_fixed1'] for r in rr) / qa,
                              'prompts': prompts})
    result = {'status': 'CAL16_P_ACR_4_PROMPT_LOPO_2_MODELS_2_DIRECTIONS64_HELD_POINTS_COMPLETE',
              'preregistration_sha256': hashlib.sha256((ROOT / PREREG).read_bytes()).hexdigest(),
              'input_sha256': hashlib.sha256((ROOT / pre['input']).read_bytes()).hexdigest(),
              'evaluations': evaluations, 'summaries': summaries,
              'GPU_submissions': 0, 'new_teacher_calls': 0, 'deployable_weights_frozen': False,
              'independent_pipeline_generalization': False, 'H1_trajectory_or_endpoint_result': False,
              'baseline_A_was_frozen_using_all_CAL_prior_to_this_conditional_experiment': True}
    with args.output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({'status': result['status'], 'summaries': [{k: v for k, v in r.items() if k != 'prompts'} for r in summaries]}))


if __name__ == '__main__':
    main()
