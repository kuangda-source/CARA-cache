#!/usr/bin/env python3
"""Freeze the complete affected eight-path composition CPU fixture."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--attempt', choices=('r1', 'r2'), default='r1')
    args = p.parse_args()
    prior_ref = 'manifests/wc_ra_baseline_sampling_cpu_r1_preregistration_20261010.json'
    prior = json.loads(Path(prior_ref).read_bytes())
    assert {n: sha(n) for n in prior['payload_sha256']} == prior['payload_sha256']
    base_audit_ref = 'reports/wc_ra_baseline_sampling_cpu_r1_terminal_20261010_retained_independent_audit.json'
    base_audit = json.loads(Path(base_audit_ref).read_bytes())
    assert base_audit['status'] == 'RA_BASELINE_R1_RETAINED_COMPLETE_CPU_NATIVE_AUDIT_PASSED'
    assert base_audit['complete_executed_paths'] == 24 and base_audit['actual_guided_reloaded'] == 432
    assert base_audit['GPU_submissions'] == base_audit['CPU_or_GPU_experiment_reruns'] == 0
    native_ref = 'reports/wc_w1_native_reference_core_actual_cpu_r2_20261006.json'
    native = json.loads(Path(native_ref).read_bytes())
    old_source = native['payload_sha256']
    for n in ('src/wcomr/w1_native_reference_sampling.py', 'src/wcomr/protocol.py', 'src/wcomr/guardrail_observation.py'):
        assert sha(n) == old_source[n]
    files = set(prior['payload_sha256']) | {prior_ref, base_audit_ref, native_ref,
        prior['calibration_batch_CPU_audit_ref'], prior['calibration_batch_CPU_result_ref'],
        'src/wcomr/cfg_ra_baseline_with_references.py', 'tests/check_cfg_ra_baseline_references_cpu.py',
        'src/wcomr/w1_native_reference_sampling.py', 'src/wcomr/protocol.py', 'src/wcomr/guardrail_observation.py'}
    files.update(str(p) for p in Path('scripts').glob('*wc_ra_baseline_references_cpu.py'))
    for n in files:
        if n.endswith('.py'):
            ast.parse(Path(n).read_bytes())
            compile(Path(n).read_bytes(), n, 'exec')
    scope = {'flows': [False, True], 'methods': ['WC', 'JOINT_NATIVE', 'RA'],
        'references_per_complete_card': 2, 'method_paths_per_complete_card': 6,
        'scenarios': ['complete', 'last_vector_writer_failure'],
        'complete_executed_paths': 32, 'successful_paths': 16,
        'solver_updates': 1152, 'net_calls': 2304,
        'guided_tensors_reloaded': 576, 'final_latents_reloaded': 16,
        'semantic_mutation_refusals': 16, 'actual_last_method_truncation_refusals': 2,
        'last_method_writer_failure_controls': 2, 'retained_Toy_tensor_files': 30,
        'GPU_submissions': 0}
    reg = {'card': 'WC-RA-BASELINE-REFERENCES-CPU-'+args.attempt.upper()+'-20261010-A',
        'registered_unix': time.time(), 'CPU_scope': scope,
        'hypothesis': 'Six existing policy trajectories plus two ordinary matching Native references preserve real prepared-input and initial noise/latent/time/condition identity; no reference substitutes another seed, and late reference failures retain every executed path.',
        'threshold_rule': 'MEDIAN_EIGHT_COMPLETE_SHARED_D6_INTERVAL_PAID_RISKS',
        'calibration_batch_CPU_audit_ref': prior['calibration_batch_CPU_audit_ref'],
        'calibration_batch_CPU_result_ref': prior['calibration_batch_CPU_result_ref'],
        'three_method_complete_CPU_audit_ref': base_audit_ref,
        'unchanged_native_request_CPU_proof_ref': native_ref,
        'CPU_Native_numerical_body': 'Explicit dense-only WC numerical stand-in; real Native class source origin independently checked, real class body not executed in this Toy fixture.',
        'real_reference_rejections': 'Retain TEXT_REJECTED/VIDEO_REJECTED slots, no replacements or zero-filled quality values.',
        'payload_sha256': {n: sha(n) for n in sorted(files)},
        'runtime_source_sha256': {**prior['runtime_source_sha256'],
            'cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py': '2d3ddcf94158c61223bc610f31ede475f7e4e27cc3b604ff3557b73d891e665f'},
        'GPU_submissions': 0, 'ledger_written': False,
        'real_GPU_calibration_remains_required_for_real_policy': True,
        'reuse_unchanged_prior_CPU_proofs_not_rerun': True}
    ref = Path('manifests/wc_ra_baseline_references_cpu_'+args.attempt+'_preregistration_20261010.json')
    assert not ref.exists()
    ref.write_text(json.dumps(reg, indent=2)+'\n')
    print(json.dumps({'status': 'RA_COMPLETE_COMPARISON_CPU_REGISTERED_NOT_EXECUTED',
                      'payload_files': len(reg['payload_sha256']), 'scope': scope, 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
