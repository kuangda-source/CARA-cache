"""Scope/cost/authority rejection controls for the independent missing arms."""
from copy import deepcopy
from pathlib import Path
import importlib.util


def run(c):
    spec = importlib.util.spec_from_file_location('timing_scope', Path(__file__).parents[1] / 'src/wcomr/timing_factorial_scope.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.validate_scope(c); m.cost_gate(c)
    b = {'used_gpu_hours': 8.67188491753794, 'cap_gpu_hours': 12,
        'budget_authorization_ref': 'manifests/budget_authorization_20261003.json'}
    m.budget_gate(b, 2400)
    checks = ['exact_six_output_different_S_counts_complete_cost_current_budget']
    changes = [('planned_output_files', 4), ('planned_total_phases', 4),
        ('max_gpu_wall_seconds', 1800), ('online_policy', True),
        ('three_dense_artifacts_must_match', False), ('official_fixed_DD_gate_required', False),
        ('legacy_SD_output_gate_before_new_variants', False),
        ('shared_entry_RNG_across_control_and_measurement', False),
        ('previous_legacy_SD_sha256', '0'*64), ('mask_source_receipt_sha256', '0'*64),
        ('deployment_sparse', False), ('gpu_execution_selected', 'yes'),
        ('S_per_variant_CFG', [[6, 5], [6, 5], [6, 5]]),
        ('S_operators_per_variant', [253, 253, 253]),
        ('varying_S_counts_are_not_matched_cost', False), ('comparison', 'forecast_placement'),
        ('causal_refresh_value_labels', True), ('factorial_manifest_sha256', '0'*64),
        ('historical_forecast_config_sha256', '0'*64), ('previous_forecast_receipt_sha256', '0'*64),
        ('previous_first_S_matched_sha256', '0'*64), ('previous_minimum_footprint_sha256', '0'*64),
        ('existing_arm_output_binding_before_new_variants', False),
        ('existing_factorial_arms', ['E0L0', 'E1L1']), ('same_S_per_CFG', [6, 5]),
        ('same_S_operators_per_candidate', 253)]
    for key, value in changes:
        q = deepcopy(c); q[key] = value
        try: m.validate_scope(q)
        except ValueError: checks.append('reject_' + key)
        else: raise AssertionError('Scope change accepted: ' + key)
    for key, value in [('sparse_layers', [2, 3, 6]), ('every', True), ('name', 'picked_after_video')]:
        q = deepcopy(c); q['variants'][1][key] = value
        try: m.validate_scope(q)
        except ValueError: checks.append('reject_variant_' + key)
        else: raise AssertionError('Variant change accepted')
    for slots in ([[1, 4, 5, 6, 7], [4, 5, 6, 7]], [[4, 5, 6, 7], [4, 5, 6, 7]],
                  [[True, 5, 6, 7, 8], [4, 5, 6, 7]], [[4, 5, 6, 7, 99], [4, 5, 6, 7]]):
        q = deepcopy(c); q['variants'][1]['per_cfg_eligible_ordinals'] = slots
        try: m.validate_scope(q)
        except ValueError: checks.append('reject_variant_slots_' + repr(slots))
        else: raise AssertionError('Changed intervention accepted')
    for key in ('planning_envelope_seconds', 'both_measurement_proxy_seconds', 'bookkeeping_seconds'):
        for value in (2400, float('nan'), -1, 1):
            q = deepcopy(c); q['cost_admission'][key] = value
            try: m.cost_gate(q)
            except ValueError: checks.append('reject_full_cost_' + key + '_' + repr(value))
            else: raise AssertionError('Invalid cost accepted')
    for key, value in [('cap_gpu_hours', 16), ('used_gpu_hours', 11.9),
        ('used_gpu_hours', float('nan')), ('some_inflight', {}),
        ('budget_authorization_ref', None), ('budget_authorization_ref', 'unverified-authority')]:
        q = deepcopy(b); q[key] = value
        try: m.budget_gate(q, 2400)
        except ValueError: checks.append('reject_budget_' + key + '_' + repr(value))
        else: raise AssertionError('Invalid budget accepted')
    return {'status': 'TIMING_FACTORIAL_SIX_OUTPUT_SCOPE_COST_BUDGET_CPU_PASS_NOT_GPU',
        'CPU_only': True, 'checks': checks, 'actual_mask_asset_import_gate': False}
