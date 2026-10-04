#!/usr/bin/env python3
"""Read-only source/receipt audit of current CPU suffix controls; no Torch."""
import argparse
import hashlib
import json
from pathlib import Path


UPSTREAM = {
    'cosmos_predict2/inference.py': '0db96c49f0b3f18a971bc989e0727132dafc27ef621145a2d25a3da62a7a1975',
    'cosmos_predict2/_src/predict2/inference/video2world.py': '59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95',
    'cosmos_predict2/_src/predict2/inference/worldcache_utils.py': 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903',
    'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py': 'c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87',
    'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py': 'f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(project, stage, runtime, expected):
    raw = (stage / 'receipt.json').read_bytes()
    receipt = json.loads(raw)
    assert receipt['status'] == 'RV0_PINNED_SUFFIX_CPU_CONTROLS_PASS_NOT_REAL_CAUSAL_ACCEPTANCE'
    assert receipt['exit_code'] == 0 and receipt['payload_sha256'] == expected
    assert len(expected) == 31
    for name, digest in expected.items():
        assert sha(stage / name) == digest, name
    for name, digest in UPSTREAM.items():
        assert sha(runtime / name) == digest, name
    current_budget = json.loads((project / 'reports/budget.json').read_text())
    assert receipt['original_GPU_budget_unchanged_during_CPU']
    assert current_budget == receipt['budget_before']
    assert current_budget['cap_gpu_hours'] == 12 and current_budget['gpu_jobs_launched'] == 44
    assert not any(k.endswith('_inflight') for k in current_budget)
    assert receipt['GPU_submissions'] == receipt['RV_labels'] == 0
    controls = receipt['controls']; result = controls['controls']
    assert controls['torch_version'] == '2.7.1+cu128'
    assert not controls['cuda_initialized'] and not result['CUDA_initialized']
    assert result['GPU_submissions'] == result['RV_labels'] == 0
    assert result['upstream_sha256'] == UPSTREAM
    rows = result['checks']
    assert [(r['flow'], r['control']) for r in rows] == [
        (False, 'full'), (False, 'cache'), (True, 'full'), (True, 'cache')]
    for row in rows:
        assert all(row[key] for key in (
            'parent36_CFG72_matches_unobserved_full_pipeline',
            'four_suffixes22_to36_CFG28_match_every_input_output_deep_and_final_latent',
            'all_suffix_final_state_components_equal',
            'AB_BA_order_invariant_parent_restored',
            'missing_identity_changed_code_half_CFG_condition_drift_nonfinite_child_duplicate_refused',
            'live_parent_latent_and_shortened_grid_drift_refused'))
        assert row['official_loop_AST_sha256'] == 'b0b85fe9b0aefad24d4cf958cdac01c16a521e438581d9750c7bcc1e6f8f9971'
        assert row['real_model_GPU_actions_or_RV_labels'] is False
    return {
        'status': 'CURRENT_CPU_SUFFIX_ORIGINAL_RECEIPT_SOURCE_AUDIT_PASS_NOT_REAL_RV0',
        'server_receipt_sha256': hashlib.sha256(raw).hexdigest(),
        'current_payload_sha256': expected, 'upstream_sha256': UPSTREAM,
        'integration_groups': 4, 'complete_parent_solver_updates_per_phase': 36,
        'suffix_solver_updates_per_control': 14, 'suffix_CFG_calls_per_control': 28,
        'suffix_controls_per_group': 4, 'budget': current_budget,
        'CPU_wall_seconds': receipt['CPU_wall_seconds'],
        'GPU_submissions': 0, 'RV_labels': 0, 'real_model_causal_acceptance': False,
        'no_Torch_import_in_auditor': True,
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage', 'runtime', 'expected'): p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.project, a.stage, a.runtime, json.loads(a.expected.read_text()))))
