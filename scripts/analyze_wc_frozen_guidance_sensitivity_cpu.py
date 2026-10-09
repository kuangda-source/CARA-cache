#!/usr/bin/env python3
"""H-T51: algebraic sensitivity at fixed, already exposed teacher states."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registration', type=Path, default=Path('manifests/wc_frozen_guidance_sensitivity_cpu_preregistration_20261009.json'))
    p.add_argument('--output', type=Path, default=Path('reports/wc_frozen_guidance_sensitivity_cpu_results_20261009.json'))
    args = p.parse_args()
    reg_raw = args.registration.read_bytes()
    reg = json.loads(reg_raw)
    started = time.perf_counter()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    assert not args.output.exists()
    for n, digest in reg['source_payload_sha256'].items():
        assert sha(Path(n).read_bytes()) == digest, n
    for n, digest in reg['input_sha256'].items():
        assert sha(Path(n).read_bytes()) == digest, n
    capture = json.loads(Path(reg['capture_path']).read_bytes())
    entry = capture['files']['CPU_score']
    compressed = Path(entry['local_path']).read_bytes()
    assert sha(compressed) == entry['compressed_sha256']
    raw = gzip.decompress(compressed)
    assert sha(raw) == entry['sha256'] and len(raw) == entry['bytes']
    score = json.loads(raw)
    assert score['source_revision'] == capture['source_revision'] == reg['teacher_source_revision']
    assert capture['GPU_exit_code'] == capture['CPU_exit_code'] == 0
    assert score['full_parent_parity'] and not score['CUDA_initialized']
    assert (score['local_CFG_pairs'], score['diagnostic_net_calls'], score['raw_tensor_count'],
            score['strict_repeat_groups'], score['complete_real_components']) == (40, 80, 120, 20, 1216)
    assert len(score['videos']) == 2
    assert [o['label'] for o in score['origins']] == reg['origin_labels']
    curves = []
    intervals = []
    current_checks = []
    for origin in score['origins']:
        metrics = origin['metrics']
        assert origin['strict_pair_repeats_and_own_history_verified'] is True
        assert metrics['measurement_space'] == 'POST_DENOISE_BEFORE_SOLVER'
        assert metrics['guidance'] == 7 and metrics['ideal_branch_weights'] == [8, -7]
        assert all(metrics['same_branch_output_factorization'].values())
        assert not metrics['cell_output_factorization_assumed']
        geometry = metrics['CC_error_geometry']
        a = geometry['unweighted_conditional_MSE']
        b = geometry['unweighted_unconditional_MSE']
        d = geometry['signed_branch_error_dot_mean']
        assert all(math.isfinite(v) for v in (a, b, d)) and a >= 0 and b >= 0
        assert d*d <= a*b + 1e-12 * max(a*b, 1e-30)
        curvature = a + b - 2*d
        assert curvature >= -1e-12 * max(a, b, 1e-30)
        dc_slope, cd_slope = a - 2*d, b - 2*d
        dc_root = None if dc_slope == 0 else -a / dc_slope
        cd_root = None if cd_slope == 0 else 2*d / cd_slope
        intervals.append({'label': origin['label'], 'coefficients': {'a': a, 'b': b, 'd': d},
            'branch_error_cosine': geometry['branch_error_cosine'],
            'DC_benefit_factorization': '(1+g) * (a + (a-2*d)*g)',
            'CD_benefit_factorization': 'g * ((b-2*d)*g - 2*d)',
            'DC_nonnegative_guidance_crossing': dc_root if dc_root is not None and dc_root >= 0 else None,
            'CD_nonzero_nonnegative_guidance_crossing': cd_root if cd_root is not None and cd_root > 0 else None,
            'CC_nonnegative_guidance_minimizer': None if curvature <= 0 else max(0., (d-a)/curvature),
            'minimizer_is_not_a_generation_guidance_recommendation': True})
        for guidance in reg['guidance_grid']:
            weighted = (1+guidance)**2*a + guidance**2*b
            cross = -2*guidance*(1+guidance)*d
            cc = weighted + cross
            dc, cd = guidance**2*b, (1+guidance)**2*a
            assert cc >= -1e-12 * max(weighted, 1e-30)
            values = {'CC': cc, 'DC': dc, 'CD': cd, 'DD': 0.}
            row = {'label': origin['label'], 'fixed_vector_algebraic_guidance': guidance,
                'ideal_weights': [1+guidance, -guidance], 'ideal_float64_MSE_to_DD': values,
                'weighted_independent_energy': weighted, 'signed_cross_term': cross,
                'signed_cancellation_fraction': None if weighted == 0 else -cross/weighted,
                'benefit_MSE_vs_CC': {'DC': cc-dc, 'CD': cc-cd},
                'relative_MSE_reduction_vs_CC_percent': {
                    n: None if cc == 0 else 100*(cc-v)/cc for n, v in values.items()},
                'actual_guidance_trajectory_regenerated': False}
            if guidance == 7:
                assert math.isclose(cc, origin['independent_signed_energy'], rel_tol=1e-10, abs_tol=1e-12)
                assert math.isclose(cc, geometry['ideal_float64_guided_MSE'], rel_tol=1e-10, abs_tol=1e-12)
                differences = {}
                for mode in ('CC', 'DC', 'CD'):
                    actual = metrics['cells'][mode]['guided_velocity_MSE_to_DD']
                    # Different arithmetic: these are ideal float64 polynomials,
                    # while the historical metric uses the actual FP32 closure.
                    assert math.isclose(values[mode], actual, rel_tol=1e-6, abs_tol=1e-10)
                    differences[mode] = values[mode] - actual
                current_checks.append({'label': origin['label'],
                    'ideal_minus_historical_actual_FP32_MSE': differences,
                    'same_branch_factorization_measured': True})
            curves.append(row)
    assert len(curves) == 35 and len(intervals) == len(current_checks) == 5
    result = {'status': 'COMPLETE_FIVE_FROZEN_STATE_GUIDANCE_POLYNOMIAL_SENSITIVITY_NOT_GENERATION',
        'source_revision': revision, 'teacher_source_revision': score['source_revision'],
        'registration_sha256': sha(reg_raw), 'input_sha256': reg['input_sha256'],
        'CPU_wall_seconds': time.perf_counter()-started, 'curves': curves,
        'analytic_crossings_and_minima': intervals, 'actual_g7_reconstruction': current_checks,
        'fixed_exposed_states': 5, 'algebraic_weight_rows': 35, 'GPU_submissions': 0,
        'new_independent_states_or_tensor_reads': 0, 'teacher_input_original_120_tensor_audit_verified': True,
        'new_generation_or_quality_or_route_claim': False,
        'limits': 'Fixed existing post-denoise branch errors and historical measured factorization. '
                  'Float64 algebra, no FP32 recomposition at other g, no trajectory or tensor regeneration. '
                  'Five correlated exposed states, not new guidance samples, validation, or a routing policy.'}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'CPU_wall_seconds', 'fixed_exposed_states', 'algebraic_weight_rows', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
