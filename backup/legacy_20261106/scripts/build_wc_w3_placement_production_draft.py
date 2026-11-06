#!/usr/bin/env python3
"""Bind the complete proven placement core to production, without GPU authority."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def build(root, revision='r2'):
    if revision not in ['r1', 'r2']:
        raise ValueError('Explicit production revision required')
    read = lambda p: json.loads((root/p).read_text())
    sha = lambda p: hashlib.sha256((root/p).read_bytes()).hexdigest()
    human = read('manifests/wc_w3_small_human_production_cpu_r2_20261005.json')
    base = read('configs/wc_w3_small_cd_approved_r1_20261005.json')
    core_manifest = read('manifests/wc_w3_placement_core_cpu_r4_20261005.json')
    actual = read('reports/wc_w3_placement_core_actual_cpu_r4_20261005.json')
    frozen = 'configs/wc_w3_placement_scope_r1_draft.json'
    config = copy.deepcopy(read(frozen)); payload = copy.deepcopy(actual['payload_sha256'])
    cost_sources = read('reports/wc_w3_placement_cost_from_real_cd_r2_20261005.json')['source_sha256']
    budget_archive = 'reports/wc_w3_placement_budget_at_preparation_20261005.json'
    if (root/budget_archive).exists():
        assert sha(budget_archive) == cost_sources['reports/budget.json']
    else:
        assert sha('reports/budget.json') == cost_sources['reports/budget.json']
        (root/budget_archive).write_bytes((root/'reports/budget.json').read_bytes())
    extra = [
        'src/wcomr/rv0_placement_execution.py', 'src/wcomr/rv0_placement_scores.py',
        'scripts/run_wc_w3_placement.py', 'scripts/supervise_wc_w3_placement.py',
        'scripts/audit_wc_w3_placement_terminal.py', 'scripts/analyze_wc_w3_placement_lpips_cpu.py',
        'scripts/build_wc_w3_placement_production_draft.py', 'tests/check_rv0_placement_production_cpu.py',
        'tests/check_rv0_placement_scores_cpu.py',
        'reports/wc_w3_placement_core_actual_cpu_r4_20261005.json',
        'reports/wc_w3_placement_core_actual_cpu_audit_r4_20261005.json',
        'reports/wc_w3_placement_core_raw_cpu_r4_20261005.json.gz',
        'reports/wc_w3_placement_cost_from_real_cd_r2_20261005.json',
        'manifests/wc_exploratory_hypotheses_r1_20261005.json', budget_archive]
    extra += [n for n in cost_sources if n not in payload and n != 'reports/budget.json']
    extra = list(dict.fromkeys(extra))
    assert len(payload) == 117 and set(payload).isdisjoint(extra)
    payload.update({name: sha(name) for name in extra})
    config.update(card=config['scope']['card'], run_id=config['scope']['run_id'],
        sample_names=[r['scene'] for r in config['scope']['scenes']], sample_indices=config['scope']['sample_indices'],
        maximum_age_solver_steps=33, logical_copy_cap_bytes=6*1024**3, workspace_reserve_bytes=4*1024**3,
        expected_project_root='/home/gaokuangda/data/gkd/worldcache_omr',
        execution_limits={'timeout_seconds': 9600, 'child_timeout_seconds': 9570, 'kill_grace_seconds': 5,
                          'admission_allowance_seconds': 15, 'minimum_disk_free_bytes': 12*1024**3},
        production_entry_ready=True, payload_sha256=payload,
        base_config_sha256=sha('configs/wc_w3_small_cd_approved_r1_20261005.json'),
        placement_core_payload_sha256=actual['payload_sha256'], placement_core_stage=core_manifest['stage'],
        placement_core_receipt_sha256=actual['server_receipt_sha256'], preregistered_scope_sha256=sha(frozen),
        cost=read('reports/wc_w3_placement_cost_from_real_cd_r2_20261005.json'),
        cost_report_ref='reports/wc_w3_placement_cost_from_real_cd_r2_20261005.json',
        cost_budget_archive=budget_archive,
        cost_report_sha256=sha('reports/wc_w3_placement_cost_from_real_cd_r2_20261005.json'),
        lpips_resource_stage=base['lpips_resource_stage'], lpips_resource_receipt_sha256=base['lpips_resource_receipt_sha256'],
        preparation_audits={'placement_core': {'path': 'reports/wc_w3_placement_core_actual_cpu_audit_r4_20261005.json',
            'sha256': sha('reports/wc_w3_placement_core_actual_cpu_audit_r4_20261005.json')},
            'lpips_resource': base['preparation_audits']['lpips_resource']},
        execution_scope_authority=None, GPU_execution_selected=False, gpu_uuid=None,
        production_CPU_validation='NOT_YET_EXECUTED',
        note='Frozen preregistered scope unchanged. Separate concrete production limits; no new single-card GPU authority.')
    path = 'configs/wc_w3_placement_production_'+revision+'_draft.json'
    manifest_path = root/('manifests/wc_w3_placement_production_cpu_'+revision+'_20261005.json')
    if (root/path).exists() or manifest_path.exists():
        raise ValueError('Preserve earlier production revisions')
    (root/path).write_text(json.dumps(config, indent=2)+'\n')
    mappings = copy.deepcopy(human['source_path_by_stage_path'])
    mappings.update({name: name for name in payload if name not in mappings})
    assert set(mappings) == set(payload)
    manifest = {'identity': 'WC_W3_PLACEMENT_PRODUCTION_CPU_'+revision.upper()+'_20261005',
        'stage': '.sync/wc-w3-placement-production-cpu-'+revision+'-20261005', 'base_stage': core_manifest['stage'],
        'base_payload_sha256': actual['payload_sha256'],
        'payload_sha256': {**payload, 'placement-config.json': sha(path)},
        'source_path_by_stage_path': {**mappings, 'placement-config.json': path},
        'upstream_sha256': config['upstream_source_sha256'], 'budget_sha256': sha('reports/budget.json'),
        'new_science_counts': [2, 16, 10, 4], 'GPU_execution_selected': False, 'new_GPU_approval': False, 'GPU_submissions': 0}
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    return {'payload_files': len(manifest['payload_sha256']), 'config': path,
            'new_GPU_approval': False, 'GPU_execution_selected': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--revision', choices=['r1', 'r2'], default='r2'); args = parser.parse_args()
    print(json.dumps(build(args.root, args.revision)))
