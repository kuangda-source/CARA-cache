"""CPU analysis invariants; synthetic features, never a real F result."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
spec = importlib.util.spec_from_file_location('f_analysis', ROOT / 'scripts/analyze_wc_spectral_probe_r1.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


def run():
    params = json.loads((ROOT / 'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
    points = json.loads((ROOT / 'reports/wc_source_phase16_live_or_terminal_capture_20261012.json').read_text())['final']['points']
    records = []
    for i, p in enumerate(points):
        # Explicit synthetic feature values unrelated to teacher outcomes.
        f = {'raw_sub_guided': .03 * (i + 1), 'raw_sub_cosine': .1 * (i % 3),
             'haar_detail_guided_fraction': .02 * (i % 5), 'haar_detail_cfg_cosine': .2,
             'fft_high_guided_fraction': .05 * (i % 4), 'fft_high_cfg_cosine': .3}
        timings = {mode: {'median_seconds': .001} for mode in ('RAW', 'HAAR', 'FFT')}
        records.append({'point': copy.deepcopy(p), 'observation': {'feature_row': {'features': f}, 'feature_timing': timings},
            'actual': {'C': p['losses']['C']['absolute_guided_MSE'], 'A': p['losses']['FUSION_A']['absolute_guided_MSE']},
            'raw': {'proxy': p['actual_C_paid_proxy']['local_proxy'], 'clock': p['selection']['chosen']['age'],
                    'source': int(p['selection']['source'] == 'P'), 'step': p['selection']['chosen']['step']}})
    result = a.analyze(records, params)
    assert result['scope'] == {'states': 16, 'prompt_groups': 4, 'natural_C_states': 14}
    assert len(result['folds']) == 4 and len(result['summaries']) == 30
    assert all(len(f['training_prompts']) == 3 and f['held_prompt'] not in f['training_prompts'] for f in result['folds'])
    for f in result['folds']:
        assert f['regression']['RAW_CLOCK']['supervised_coefficients_per_output'] == 2
        for m in ('RAW_SUB', 'HAAR', 'FFT'):
            assert f['regression'][m]['supervised_coefficients_per_output'] == 4
        for row in f['held_rows']:
            for score in row['scores']:
                for d in score['decisions']:
                    assert d['regret_seconds_plus_weighted_MSE'] >= 0
                    assert d['chosen'] in ('C', 'A')
                    if score['method'] in ('RAW_SUB', 'HAAR', 'FFT'):
                        assert abs(d['regret_plus_observed_feature_seconds'] - d['regret_seconds_plus_weighted_MSE'] - .001) < 1e-8
    # Held labels may alter reported regret, but no prior, normalization,
    # unsupervised input basis or regression may depend on held labels.
    held = result['folds'][0]['held_prompt']; changed = copy.deepcopy(records)
    for r in changed:
        if r['point']['selection']['scene'] == held:
            for label in ('C', 'D_REFERENCE_A', 'FUSION_A', 'NEW_P'):
                r['point']['losses'][label]['absolute_guided_MSE'] *= 2
            r['actual']['C'] *= 2; r['actual']['A'] *= 2
    altered = a.analyze(changed, params)
    other = next(f for f in altered['folds'] if f['held_prompt'] == held)
    for name in ('train_only_source_phase_prior', 'train_only_preprocessing', 'regression'):
        assert other[name] == result['folds'][0][name]
    # A missing row cannot silently shrink the fixed scope.
    try:
        a.analyze(records[:-1], params)
    except ValueError:
        pass
    else:
        raise AssertionError('Partial F16 accepted')
    json.dumps(result, allow_nan=False)
    return {'status': 'F16_ANALYSIS_SYNTHETIC_FEATURE_CPU_PASS_NOT_REAL_F_RESULT',
            'checks': ['all16_four_prompt_LOPO', 'natural14_denominator', 'fixed_small_coefficients',
                       'all_three_frozen_lambda_points', 'all_observed_feature_costs_charged',
                       'held_target_perturbation_no_fit_leakage', 'partial_scope_refused'],
            'GPU_calls': 0, 'real_F_features': False}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
