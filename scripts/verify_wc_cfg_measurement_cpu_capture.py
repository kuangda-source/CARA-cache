#!/usr/bin/env python3
"""Verify all captured native CPU receipts without claiming a second tensor load."""
import gzip
import hashlib
import json
from pathlib import Path

PREFIX = 'reports/wc_cfg_measurement_cpu_r1_terminal_20261009_'


def main():
    capture = json.loads(Path(PREFIX + 'capture.json').read_text())
    assert capture['status'] == 'MEASUREMENT_ORIGINAL_CPU_TERMINAL_SUCCESS_NATIVE_CAPTURE'
    native = {}
    for name, item in capture['files'].items():
        compressed = Path(item['local_path']).read_bytes()
        raw = gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        if name.endswith('.json'):
            native[name] = json.loads(raw)
    result, audit, receipt, reg = [native[n] for n in ('result.json', 'audit.json', 'receipt.json', 'collector-preregistration.json')]
    assert receipt['core_exit_code'] == receipt['audit_exit_code'] == receipt['exit_code'] == 0
    assert receipt['budget_before_sha256'] == receipt['budget_after_sha256'] == capture['budget_sha256_unchanged']
    assert receipt['payload_after_sha256'] == result['payload_sha256'] == reg['payload_sha256'] and len(reg['payload_sha256']) == 44
    assert receipt['runtime_after_sha256'] == reg['runtime_source_sha256'] and len(reg['runtime_source_sha256']) == 5
    assert result['successful_full_parents'] == 4 and result['successful_origins'] == 10 and result['successful_mock_videos'] == 4
    assert result['successful_CFG_pairs'] == audit['successful_CFG_pairs'] == 80
    assert result['strict_repeat_groups'] == audit['strict_repeat_groups'] == 40
    assert audit['raw_tensors_reconstructed'] == 240 and audit['separate_net_input_condition_witnesses_verified'] == 448
    assert audit['separate_solver_space_witnesses_verified'] == 152 and audit['full_parent_pairs'] == 2
    complete = [c for c in result['checks'] if c['scenario'] == 'complete']
    assert [c['flow'] for c in complete] == [False, True]
    controls = ['missing_origin', 'missing_repeat', 'wrong_pair_output', 'wrong_condition', 'wrong_action',
                'missing_net_measurement', 'wrong_active_condition_measurement', 'wrong_sampler_measurement']
    for c in complete:
        assert c['semantic_mutation_rejections'] == controls
        assert c['complete_pair_rows'] == 40 and c['complete_mock_videos'] == 2
    failures = [c for c in result['checks'] if c['scenario'] != 'complete']
    expected = ['second_CFG', 'nested_writer', 'condition_mutation', 'solver_mutation', 'nonfinite', 'mode_mutation']
    assert [c['scenario'] for c in failures] == [c['scenario'] for c in audit['failed_attempts_retained']] == expected
    assert all(c['complete_scope_retained'] and c['all_failed_forks_restored'] for c in failures)
    assert all(c['five_origins_retained'] and c['planned_CFG_pairs'] == 40 for c in audit['failed_attempts_retained'])
    measurements = result['measurement_checks']
    assert all(measurements[k] for k in ('same_active_different_full_values_distinguished', 'changed_active_values_distinguished',
              'zero_active_explicit', 'same_numeric_values_different_dtype_distinguished',
              'raw_solver_return_and_extracted_latent_distinguished', 'inputs_unmodified', 'RNG_unmodified'))
    assert measurements['invalid_masks_rejected'] == ['nonbinary', 'nonfinite', 'not_broadcastable', 'wrong_rank']
    assert not any(v['CUDA_initialized'] or v['GPU_submissions'] for v in (result, audit, measurements))
    proof = {'status': 'MEASUREMENT_NATIVE_CPU_TERMINAL_SCOPE_BINDING_VERIFIED_NOT_SECOND_TENSOR_LOAD',
             'source_revision': capture['source_revision'], 'original_PIDs_absent': capture['original_PIDs_absent'],
             'CPU_wall_seconds': receipt['CPU_wall_seconds'], 'successful_CFG_pairs': 80, 'strict_repeat_groups': 40,
             'server_independent_raw_tensors_reconstructed': 240, 'net_condition_witnesses_verified': 448,
             'solver_space_witnesses_verified': 152, 'evidence_mutation_refusals': 16, 'failed_attempts_retained': 6,
             'measurement_controls': measurements, 'native_files_verified': len(capture['files']),
             'budget_sha256_unchanged': receipt['budget_after_sha256'], 'GPU_submissions': 0,
             'local_second_tensor_load': False, 'real_model_or_quality_claim': False}
    dest = Path(PREFIX + 'verification.json'); assert not dest.exists()
    dest.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
