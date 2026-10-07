#!/usr/bin/env python3
"""Version the changed execution policy while retaining the proven scientific closure."""
import copy
import hashlib
import json
from pathlib import Path


def build(root):
    read = lambda name: json.loads((root/name).read_text())
    digest = lambda name: hashlib.sha256((root/name).read_bytes()).hexdigest()
    old = read('manifests/wc_w3_placement_production_cpu_r2_20261005.json')
    config = copy.deepcopy(read('configs/wc_w3_placement_production_r2_draft.json'))
    policy_name = 'manifests/wc_execution_autonomy_authorization_20261007.json'
    policy = read(policy_name)
    from wcomr.rv0_placement_execution import LIMITS, validate_config
    changed = ['src/wcomr/rv0_placement_execution.py', 'scripts/run_wc_w3_placement.py',
        'scripts/supervise_wc_w3_placement.py', 'tests/check_rv0_placement_production_cpu.py',
        'tests/check_wc_execution_policy_cpu.py', 'scripts/build_wc_w3_placement_policy_draft.py', policy_name]
    payload = copy.deepcopy(config['payload_sha256'])
    payload.update({name: digest(name) for name in changed})
    config.update(payload_sha256=payload, execution_limits=LIMITS,
        execution_policy_authority={
            'approval_ref': policy_name, 'approval_sha256': digest(policy_name),
            **{name: policy[name] for name in ['source_user_text', 'automatic_single_job_gpu_hours',
                'legacy_per_card_seconds_caps_revoked', 'cumulative_cap_gpu_hours', 'usage_reset']}},
        execution_scope_authority=None, GPU_execution_selected=False, gpu_uuid=None,
        production_CPU_validation='POLICY_CHANGE_ACTUAL_CPU_PENDING',
        note='Only execution policy/accounting changed. No legacy per-job GPU seconds deadline. '
             'Complete unchanged W3-B exceeds the new 2 GPUh approval threshold.')
    validate_config(config)
    config_name = 'configs/wc_w3_placement_policy_r1_draft_20261007.json'
    manifest_name = 'manifests/wc_w3_placement_policy_cpu_r1_20261007.json'
    if any((root/name).exists() for name in [config_name, manifest_name]):
        raise ValueError('Preserve prior policy drafts and CPU attempts')
    (root/config_name).write_text(json.dumps(config, indent=2)+'\n')
    mappings = copy.deepcopy(old['source_path_by_stage_path'])
    mappings.update({name: name for name in changed})
    mappings['placement-config.json'] = config_name
    manifest = {'identity': 'WC_W3_PLACEMENT_POLICY_CPU_R1_20261007',
        'stage': '.sync/wc-w3-placement-policy-cpu-r1-20261007', 'base_stage': old['stage'],
        'base_payload_sha256': old['payload_sha256'],
        'payload_sha256': {**payload, 'placement-config.json': digest(config_name)},
        'source_path_by_stage_path': mappings, 'upstream_sha256': config['upstream_source_sha256'],
        'budget_sha256': digest('reports/budget.json'), 'new_science_counts': [2, 16, 10, 4],
        'GPU_execution_selected': False, 'above_2h_approval': False, 'GPU_submissions': 0,
        'unchanged_scientific_core_files': 117, 'legacy_GPU_deadlines_removed': True}
    assert set(mappings) == set(manifest['payload_sha256'])
    (root/manifest_name).write_text(json.dumps(manifest, indent=2)+'\n')
    return {'config': config_name, 'payload_files': len(manifest['payload_sha256']),
        'nominal_gpu_hours': config['cost']['complete_nominal_proxy_seconds']/3600,
        'planning_gpu_hours': config['cost']['complete_planning_proxy_seconds']/3600,
        'requires_above_2h_answer': True, 'GPU_submissions': 0}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    print(json.dumps(build(parser.parse_args().root)))
