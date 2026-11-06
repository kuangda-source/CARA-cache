#!/usr/bin/env python3
"""Read-only audit of pinned CPU one-action controls; no Torch or rerun."""
import argparse
import hashlib
import json
import math
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
    assert receipt['status'] == 'RV0_ONE_ACTION_CPU_CONTROLS_PASS_NOT_REAL_LABELS'
    assert receipt['exit_code'] == 0 and receipt['payload_sha256'] == expected
    assert len(expected) == 33
    assert {'src/wcomr/rv0_actions.py', 'src/wcomr/rv0_fork.py',
            'tests/check_rv0_actions_cpu.py', 'tests/check_rv0_fork_cpu.py'} <= set(expected)
    for name, digest in expected.items():
        assert sha(stage / name) == digest, name
    for name, digest in UPSTREAM.items():
        assert sha(runtime / name) == digest, name
    budget = json.loads((project / 'reports/budget.json').read_text())
    assert receipt['original_GPU_budget_unchanged_during_CPU'] is True
    assert budget == receipt['budget_before']
    assert budget['cap_gpu_hours'] == 12 and budget['gpu_jobs_launched'] == 44
    assert not any(k.endswith('_inflight') for k in budget)
    assert receipt['GPU_submissions'] == receipt['RV_labels'] == 0
    wall = receipt['CPU_wall_seconds']
    assert math.isfinite(wall) and 0 < wall <= 600
    controls = receipt['controls']; result = controls['controls']
    assert controls['torch_version'] == '2.7.1+cu128'
    assert controls['cuda_initialized'] is False and result['CUDA_initialized'] is False
    assert result['status'] == 'CPU_ONE_ACTION_C_D_INTERFACE_PASS_NOT_REAL_RV_LABELS'
    assert result['GPU_submissions'] == result['RV_labels'] == 0
    groups = [(False, 'full'), (False, 'cache'), (True, 'full'), (True, 'cache')]
    regression = result['unchanged_suffix_regression']
    assert regression['upstream_sha256'] == UPSTREAM
    assert regression['CUDA_initialized'] is False
    assert regression['GPU_submissions'] == regression['RV_labels'] == 0
    assert [(r['flow'], r['control']) for r in regression['checks']] == groups
    for row in regression['checks']:
        for key in (
            'parent36_CFG72_matches_unobserved_full_pipeline',
            'four_suffixes22_to36_CFG28_match_every_input_output_deep_and_final_latent',
            'all_suffix_final_state_components_equal',
            'AB_BA_order_invariant_parent_restored',
            'missing_identity_changed_code_half_CFG_condition_drift_nonfinite_child_duplicate_refused',
            'live_parent_latent_and_shortened_grid_drift_refused'):
            assert row[key] is True, key
        assert row['official_loop_AST_sha256'] == 'b0b85fe9b0aefad24d4cf958cdac01c16a521e438581d9750c7bcc1e6f8f9971'
        assert row['real_model_GPU_actions_or_RV_labels'] is False
    current = result['current']
    assert current['status'] == 'PINNED_PIPELINE_CPU_FIXTURE_EXTERNAL_EXERCISE_COMPLETE'
    assert current['upstream_sha256'] == UPSTREAM and current['cuda_initialized'] is False
    assert [(r['flow'], r['native_control']) for r in current['checks']] == groups
    storage = []
    for row in current['checks']:
        for key in (
            'original_vs_OFF_all72_inputs_outputs_cache_banks_latent_state_RNG_artifact_equal',
            'CFG0_and_CFG1_same_input_current_CD_deep0_vs_full',
            'CC_DD_swapped_CD_full_suffix_and_state_equal',
            'native_matching_action_equals_OFF',
            'current_CD_uses_paid_probe_past_own_CFG_true_full_only',
            'cache_full_side_effects_left_to_pinned_body',
            'six_invalid_plans_and_missing_history_refused',
            'changed_eval_mode_refused_and_restored',
            'TECH_BLOCKED_attempts_and_parent_restore_verified'):
            assert row[key] is True, key
        # Stale-age rejection is exercised on the forced-cache pair only.
        assert row['stale_age_refused_when_infeasible'] is (row['native_control'] == 'cache')
        assert (row['suffix_controls'], row['suffix_updates'], row['suffix_CFG_calls']) == (12, 14, 28)
        assert row['budget_matched_or_real_GPU_labels'] is False
        copied = row['snapshot_storage_CPU_Toy_only']
        assert copied['snapshot_copies_only_not_live_weights_or_peak'] is True
        logical = copied['logical_tensor_bytes_by_device']
        physical = copied['unique_owned_tensor_storage_bytes_by_device']
        assert set(logical) == {'cpu', 'numpy'} and set(physical) == {'cpu'}
        assert all(type(v) is int and v > 0 for v in [*logical.values(), *physical.values()])
        assert physical['cpu'] <= logical['cpu']
        storage.append(copied)
    return {
        'status': 'CURRENT_CPU_ONE_ACTION_ORIGINAL_RECEIPT_SOURCE_AUDIT_PASS_NOT_REAL_LABELS',
        'server_receipt_sha256': hashlib.sha256(raw).hexdigest(),
        'current_payload_sha256': expected, 'upstream_sha256': UPSTREAM,
        'unchanged_suffix_regression_groups': 4, 'one_action_integration_groups': 4,
        'one_action_complete_suffix_controls': 48,
        'complete_parent_solver_updates': 36, 'complete_parent_CFG_calls': 72,
        'one_action_suffix_solver_updates': 14, 'one_action_suffix_CFG_calls': 28,
        'snapshot_owned_storage_CPU_Toy_only': storage,
        'same_remaining_policy_function_not_same_future_mask': True,
        'budget_matched': False, 'real_model_causal_acceptance': False,
        'complete_GPU_cost_or_peak_VRAM_bound_validated': False,
        'budget': budget, 'CPU_wall_seconds': wall,
        'GPU_submissions': 0, 'RV_labels': 0, 'no_Torch_import_in_auditor': True,
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage', 'runtime', 'expected'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.project, args.stage, args.runtime,
                           json.loads(args.expected.read_text()))))
