#!/usr/bin/env python3
"""Freeze the independent MF-00 four-path CPU invocation and all failures."""
import ast
import hashlib
import json
from pathlib import Path
import time


def main():
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    old_ref = 'manifests/wc_cfg_complete_native_policy_sampling_cpu_r2_preregistration_20261009.json'
    old = json.loads(Path(old_ref).read_text())
    # Preserve and reuse unchanged scientific sources. Entry documents may
    # have legitimately acquired budget/policy prefixes since the old stage.
    for name, digest in old['payload_sha256'].items():
        if name.startswith(('src/', 'tests/')):
            assert sha(name) == digest, name
    files = set(old['payload_sha256']) | {
        old_ref, 'plans/WORLD_CACHE_MF00_INTERFACE_R1_20261010.md',
        'plans/WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md',
        'src/wcomr/cfg_mf00_interface_sampling.py',
        'tests/check_cfg_mf00_interface_sampling_cpu.py',
        'scripts/check_wc_mf00_interface_sampling_cpu.py',
        'scripts/supervise_wc_mf00_interface_sampling_cpu.py',
        'scripts/deploy_wc_mf00_interface_sampling_cpu.py',
        'scripts/prepare_wc_mf00_interface_sampling_cpu.py',
        'reports/wc_mf00_interface_source_derivation_20261010.json',
        'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json',
        'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json',
    }
    for name in files:
        if name.endswith('.py'):
            ast.parse(Path(name).read_bytes())
            compile(Path(name).read_bytes(), name, 'exec')
    result = {
        'identity': 'MF00_I_R1_INDEPENDENT_COMPLETE_FOUR_PATH_BATCH_CPU',
        'registered_unix': time.time(),
        'plan_ref': 'plans/WORLD_CACHE_MF00_INTERFACE_R1_20261010.md',
        'CPU_scope': {'flow_configurations': ['OFF', 'ON'], 'threshold': .06,
            'observer_configurations': ['OFF'], 'strict_repetitions': 1,
            'orders': ['ORIGINAL', 'PAIRED'], 'complete_requests_per_batch': 2,
            'scenarios': ['complete', 'last_vector_writer_failure'], 'complete_rows': 4,
            'successful_full_paths': 8, 'executed_full_paths_including_last_writer_failures': 16,
            'solver_updates': 576, 'net_calls': 1152,
            'actual_guided_tensors_reloaded': 288, 'actual_final_latents_reloaded': 8,
            'last_path_writer_failures': 2, 'semantic_mutation_refusals': 24,
            'actual_truncation_refusals': 2, 'GPU_submissions': 0},
        'payload_sha256': {n: sha(n) for n in sorted(files)},
        'runtime_source_sha256': old['runtime_source_sha256'],
        'prior_complete_CPU_audit_ref': old['prior_complete_CPU_audit_ref'],
        'prior_boundary_CPU_audit_ref': old['prior_boundary_CPU_audit_ref'],
        'prior_native_policy_CPU_audit_ref': old['prior_native_policy_CPU_audit_ref'],
        'old_full16_card_not_executed_or_accepted': True,
        'new_GPU_card_selected': False, 'GPU_submissions': 0,
        'budget_written': False, 'real_model_or_endpoint_or_latency_claim': False,
    }
    target = Path('manifests/wc_mf00_interface_sampling_cpu_r1_preregistration_20261010.json')
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'payload_files': len(files), 'scope': result['CPU_scope']}))


if __name__ == '__main__':
    main()
