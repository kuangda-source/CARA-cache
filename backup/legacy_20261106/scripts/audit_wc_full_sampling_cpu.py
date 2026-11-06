#!/usr/bin/env python3
"""Audit sealed CPU receipts/source identities; no Torch, network or GPU work."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root):
    paths = [root / f'reports/wc_full_sampling_cpu_r{i}_20261003.json' for i in range(1, 6)]
    receipts = [json.loads(p.read_text()) for p in paths]
    first, _, base, _, latest = receipts
    assert first['status'] == 'FULL_SAMPLING_CPU_GATE_FAILED'
    assert all(r['status'] == 'FULL_SAMPLING_CPU_GATE_PASS' for r in receipts[1:])
    assert all(r['budget_unchanged'] for r in receipts)
    assert not latest['controls']['cuda_initialized']
    for name, digest in latest['payload_sha256'].items():
        assert sha(root / name) == digest, 'Current payload differs: ' + name
    # D/D no-adapter controls were rerun in r3; the final production core and
    # all its dependencies are still those exact bytes, separately from the
    # later adapter/fixture identity tested by r5.
    for name, digest in base['payload_sha256'].items():
        if name.startswith('src/') and name != 'src/wcomr/refresh_deployment.py':
            assert sha(root / name) == digest, 'D/D core changed after r3: ' + name
    controls = base['controls']['complete_sampling']['dense_full_controls']['checks']
    positive = [r for r in controls if 'failure' not in r]
    assert len(controls) == 11 and len(positive) == 6
    for r in positive:
        assert r['full_updates'] == [36, 36] and r['cfg_calls'] == [72, 72]
        assert len(r['nine_gates']) == 9 and all(r['nine_gates'].values())
        assert all(r['pipeline_gates'].values())
        assert r['checkpoints'] == [13, 21, 33, 35, 36]
        assert r['actual_restored_latent_continues_to_final']
    assert {r['failure'] for r in controls if 'failure' in r} == {
        'solver_tail', 'decode', 'writer', 'output_corruption', 'rng_after_decode'}
    refresh = latest['controls']['complete_sampling']['refresh_controls']['checks']
    positive_refresh = [r for r in refresh if 'failure' not in r]
    assert len(refresh) == 19 and len(positive_refresh) == 12
    for r in positive_refresh:
        assert r['full_updates'] == [36, 36] and r['cfg_calls'] == [72, 72]
        assert r['component_counts'] == [51] * 5
        evidence = r['refresh_controls']
        assert evidence['native70_reset_invalidates_both_cfg_histories']
        assert evidence['sparse_never_true_dense'] and evidence['ledger_restored_and_rebound']
        assert evidence['warm_and_final_dense'] and evidence['fallback_layer_2_never_sparse']
        if r['control'] == 'refresh_dense':
            assert all(r['nine_gates'].values()) and all(r['pipeline_gates'].values())
            assert evidence['sparse_refresh_calls'] == 0
        else:
            assert evidence['sparse_refresh_calls'] > 0
            assert evidence['cache_hit_reads_approximate_forecast']
            assert evidence['approximate_closure_changes_actual_final_latent']
            assert not r['nine_gates']['output_hashes']
    failures = [r for r in refresh if 'failure' in r]
    assert {r['failure'] for r in failures} == {'refresh_context', 'refresh_model',
        'refresh_group', 'refresh_condition', 'refresh_window', 'refresh_nonfinite', 'refresh_kernel_nan'}
    for r in failures:
        assert r['planned_phases'] == 4 and r['denominators_preserved']
        assert r['first_request_complete_preserved']
        assert r['all_hooks_and_decode_flags_restored'] and r['second_phase_updates'] == [36, 11]
    assert latest['budget']['used_gpu_hours'] == base['budget']['used_gpu_hours']
    assert latest['budget']['used_gpu_hours'] == 6.055044055960606
    assert latest['budget']['gpu_jobs_launched'] == 36
    return {'status': 'COMPLETE_SAMPLING_REFRESH_CPU_RECEIPT_AND_CURRENT_SOURCE_AUDIT_PASS',
        'receipts': {str(p.relative_to(root)): sha(p) for p in paths},
        'current_payload_sha256': latest['payload_sha256'],
        'DD_no_adapter_control_rows': 11, 'refresh_control_rows': 19,
        'final_cpu_wall_seconds': latest['cpu_wall_seconds'],
        'observed_unix': latest['observed_unix'], 'budget_used_gpu_hours': latest['budget']['used_gpu_hours'],
        'budget_jobs': latest['budget']['gpu_jobs_launched'], 'new_GPU_cost': 0,
        'cuda_initialized': False, 'fresh_gpu': latest['fresh_gpu'], 'fresh_apps': latest['fresh_apps'],
        'original_stride_failure_preserved': True,
        'limits': 'CPU receipt/source audit only. Toy output stand-in and mock writer; '
                  'no actual sparse kernel, weights, VAE, encoded video, clean E2E speed or independent restart.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    result['audit_script_sha256'] = sha(Path(__file__))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['status', 'DD_no_adapter_control_rows',
        'refresh_control_rows', 'budget_used_gpu_hours', 'new_GPU_cost']}))
