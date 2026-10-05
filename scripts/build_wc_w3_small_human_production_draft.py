#!/usr/bin/env python3
"""Bind the proven Human-only core to new production CLIs, without GPU authority."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def build(root):
    read = lambda p: json.loads((root/p).read_text())
    sha = lambda p: hashlib.sha256((root/p).read_bytes()).hexdigest()
    base_manifest = read('manifests/wc_w3_small_cd_approved_r1_20261005.json')
    base = read('configs/wc_w3_small_cd_approved_r1_20261005.json')
    core_manifest = read('manifests/wc_w3_small_human_core_cpu_r1_20261005.json')
    actual = read('reports/wc_w3_small_human_core_actual_cpu_20261005.json')
    config = read('configs/wc_w3_small_human_complement_r1_draft.json')
    payload = copy.deepcopy(actual['payload_sha256'])
    extra = [
        'src/wcomr/rv0_small_human_execution.py', 'src/wcomr/rv0_small_human_evaluation.py',
        'src/wcomr/rv0_small_partial.py', 'scripts/run_wc_w3_small_human.py',
        'scripts/supervise_wc_w3_small_human.py', 'scripts/audit_wc_w3_small_human_terminal.py',
        'scripts/analyze_wc_w3_small_human_lpips_cpu.py', 'tests/check_rv0_small_human_production_cpu.py',
        'scripts/build_wc_w3_small_human_production_draft.py',
        'reports/wc_w3_small_human_core_actual_cpu_20261005.json',
        'reports/wc_w3_small_human_core_actual_cpu_audit_20261005.json',
        'reports/wc_w3_small_human_core_raw_cpu_20261005.json.gz']
    assert set(payload).isdisjoint(extra)
    payload.update({name: sha(name) for name in extra})
    aliases = ['card', 'run_id', 'sample_names', 'sample_indices', 'target_calls',
               'maximum_age_solver_steps', 'logical_copy_cap_bytes', 'workspace_reserve_bytes']
    config.update({name: copy.deepcopy(config['scope'][name]) for name in aliases})
    config.update(production_entry_ready=True, actual_singleton_core_CPU_verified=True,
        payload_sha256=payload, base_config_sha256=sha('configs/wc_w3_small_cd_approved_r1_20261005.json'),
        human_core_payload_sha256=actual['payload_sha256'], human_core_stage=core_manifest['stage'],
        human_core_receipt_sha256=actual['server_receipt_sha256'],
        lpips_resource_stage=base['lpips_resource_stage'], lpips_resource_receipt_sha256=base['lpips_resource_receipt_sha256'],
        preparation_audits={'human_core': {'path': 'reports/wc_w3_small_human_core_actual_cpu_audit_20261005.json',
            'sha256': sha('reports/wc_w3_small_human_core_actual_cpu_audit_20261005.json')},
            'lpips_resource': base['preparation_audits']['lpips_resource']},
        execution_scope_authority=None, production_CPU_validation='NOT_YET_EXECUTED',
        note='Complete new production entry, prior actual Human core CPU, no new single-card authorization/GPU selection.')
    path = 'configs/wc_w3_small_human_production_r1_draft.json'
    (root/path).write_text(json.dumps(config, indent=2)+'\n')
    mappings = {**base_manifest['source_path_by_stage_path'],
                **{name: name for name in core_manifest['new_payload_sha256']}, **{name: name for name in extra}}
    assert set(mappings) == set(payload)
    manifest = {'identity': 'WC_W3_SMALL_HUMAN_PRODUCTION_CPU_R1_20261005',
        'stage': '.sync/wc-w3-small-human-production-cpu-r1-20261005',
        'base_stage': core_manifest['stage'], 'base_payload_sha256': actual['payload_sha256'],
        'payload_sha256': {**payload, 'human-config.json': sha(path)},
        'source_path_by_stage_path': {**mappings, 'human-config.json': path},
        'upstream_sha256': base['upstream_source_sha256'], 'budget_sha256': sha('reports/budget.json'),
        'new_science_counts': [1, 6, 4, 1], 'original_failed_science_counts': [2, 12, 8, 2],
        'GPU_execution_selected': False, 'new_GPU_approval': False, 'GPU_submissions': 0}
    (root/'manifests/wc_w3_small_human_production_cpu_r1_20261005.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return {'payload_files': len(manifest['payload_sha256']), 'config': path,
            'new_GPU_approval': False, 'GPU_execution_selected': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    print(json.dumps(build(parser.parse_args().root)))
