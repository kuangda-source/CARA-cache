#!/usr/bin/env python3
"""Build an unselected full-causal draft from current source and CPU receipts."""
import argparse
import json
from pathlib import Path
import sys


def build(project):
    sys.path.insert(0, str(project/'src'))
    from wcomr.rv0_execution import sha, validate_config, RUN, CARD
    from wcomr.rv0_causal_scope import proposal
    cpu = json.loads((project/'reports/wc_rv0_causal_cpu_r3_20261004.json').read_text())
    resource = json.loads((project/'reports/wc_rv0_lpips_resource_cpu_v2_20261004.json').read_text())
    if cpu['exit_code'] != 0 or resource['exit_code'] != 0:
        raise ValueError('Actual prior full-core/LPIPS CPU checks required')
    additional = ['src/wcomr/rv0_execution.py', 'src/wcomr/rv0_causal_scope.py',
        'src/wcomr/rv0_lpips.py', 'src/wcomr/rv0_video_reader.py', 'src/wcomr/rv0_evaluation_plan.py',
        'scripts/run_wc_rv0_causal.py', 'scripts/supervise_wc_rv0_causal.py',
        'scripts/analyze_wc_rv0_causal_lpips_cpu.py', 'scripts/audit_wc_rv0_causal_cpu.py',
        'scripts/audit_wc_rv0_causal_terminal.py',
        'scripts/audit_wc_rv0_returned_native_hashes.py',
        'scripts/audit_wc_rv0_lpips_resource.py', 'scripts/check_wc_full_native_cpu.py',
        'scripts/run_wc_s0_profile.py', 'scripts/build_wc_rv0_causal_draft.py',
        'manifests/wc_h0_eval_mode_contract_20261003.json',
        'manifests/budget_authorization_20261004_wc_13gpuh.json',
        'reports/wc_rv0_causal_scope_cost_r3_20261004.json',
        'reports/wc_rv0_native_readonly_hash_audit_20261004.json',
        'reports/wc_rv0_causal_cpu_native_audit_r3_20261004.json',
        'reports/wc_rv0_lpips_resource_native_audit_v2_20261004.json']
    payload = {name: sha(project/name) for name in sorted(set(cpu['payload_sha256']) | set(additional))}
    payload['profile-config.json'] = sha(project/'configs/wc_s0_profile.json')
    config = {'run_id': RUN, 'card': CARD, 'scope': proposal(), 'gpu_execution_selected': False,
        'gpu_uuid': None, 'sample_names': proposal()['sample_names'], 'sample_indices': [1, 2],
        'logical_copy_cap_bytes': 6*(1 << 30), 'workspace_reserve_bytes': 4*(1 << 30),
        'minimum_disk_free_bytes': 15000000000, 'timeout_seconds': 6900,
        'child_timeout_seconds': 6870, 'kill_grace_seconds': 5, 'release_allowance_seconds': 30,
        'admission_allowance_seconds': 15, 'GPU_submitted': False, 'budget_reserved_seconds': 0,
        'RV_labels': 0, 'full_RV0_acceptance': False, 'clean_speed_measurement': False,
        'CPU_scoring_after_GPU_release': True, 'cal_config_sha256': sha(project/'configs/cal_w1d8.jsonl'),
        'f1_setup_sha256': sha(project/'configs/f1_setup.json'),
        'cost_report_ref': 'reports/wc_rv0_causal_scope_cost_r3_20261004.json',
        'cost_report_sha256': sha(project/'reports/wc_rv0_causal_scope_cost_r3_20261004.json'),
        'payload_sha256': payload, 'upstream_source_sha256': cpu['upstream_sha256'],
        'cpu_control_payload_sha256': cpu['payload_sha256'],
        'cpu_control_stage': '.sync/wc-rv0-causal-cpu-r3',
        'cpu_control_receipt_sha256': cpu['server_receipt_sha256'],
        'lpips_resource_stage': '.sync/wc-rv0-lpips-resource-v2',
        'lpips_resource_receipt_sha256': resource['server_receipt_sha256'],
        'preparation_audits': {
            'causal_cpu_original': {'path': 'reports/wc_rv0_causal_cpu_native_audit_r3_20261004.json',
                'sha256': sha(project/'reports/wc_rv0_causal_cpu_native_audit_r3_20261004.json')},
            'lpips_resource_original': {'path': 'reports/wc_rv0_lpips_resource_native_audit_v2_20261004.json',
                'sha256': sha(project/'reports/wc_rv0_lpips_resource_native_audit_v2_20261004.json')}},
        'execution_status': 'UNSELECTED_DRAFT_CPU_CONTRACT_ONLY_NOT_DEPLOYED',
        'limits': ['Full18 output scope retained; no GPU choice, reservation or submission.',
                   'Old CPU originals/resources rechecked via native remote hashes and local judgment.',
                   'New production/decoder actual-host CPU checks and deployment are still pending.',
                   'Real causal terminal audit, formal budget-matched labels and quality confirmation are still required.']}
    validate_config(config)
    return config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise ValueError('Do not overwrite a draft receipt/config identity')
    config = build(args.project)
    args.output.write_text(json.dumps(config, indent=2)+'\n')
    print(json.dumps({'status': config['execution_status'], 'source_files': len(config['payload_sha256']),
                      'parents': 8, 'suffixes': 24, 'outputs': 18, 'GPU_selected': False}))
