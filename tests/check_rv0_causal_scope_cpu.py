"""Fail closed against reduced causal scope, unit drift or overspending."""
import copy
import importlib.util
import math
from pathlib import Path


def run():
    path = Path(__file__).resolve().parents[1]/'src/wcomr/rv0_causal_scope.py'
    spec = importlib.util.spec_from_file_location('rv0_causal_scope_cpu', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    c = m.proposal(); checks = []
    assert m.validate_scope(c)['complete_suffixes'] == 24
    for key, value in [('sample_names', c['sample_names'][:1]), ('CFG_slots', [0]),
                       ('suffix_labels_per_CFG', ['C_first', 'D_first']), ('parent_phases', 6),
                       ('suffix_controls', 12), ('total_encoded_outputs', 8),
                       ('decoded_OFF_bridge_outputs', 0),
                       ('action_unit', 'PAIRED_CFG_SOLVER_STEP'), ('suffix_solver_updates', 4),
                       ('suffix_policy', 'FIXED_MASK'), ('budget_matched', True),
                       ('GPU_execution_selected', True), ('Head_or_LoRA', True),
                       ('signed_fidelity_diagnostic_is_primary_RV_training_label', True)]:
        candidate = copy.deepcopy(c); candidate[key] = value
        try: m.validate_scope(candidate)
        except ValueError: checks.append('refuse_'+key)
        else: raise AssertionError('Reduced/changed scope accepted: '+key)
    budget = {'cap_gpu_hours': 13, 'used_gpu_hours': 11.022315686839217,
              'budget_authorization_ref': c['budget_authorization_ref']}
    assert m.budget_gate(budget, c)['reserved_seconds'] == 0
    for change in [{'used_gpu_hours': 11.1}, {'cap_gpu_hours': 12},
                   {'budget_authorization_ref': 'manifests/budget_authorization_20261003.json'},
                   {'used_gpu_hours': math.nan}, {'used_gpu_hours': -1},
                   {'used_gpu_hours': 13.01}, {'used_gpu_hours': True}, {'job_inflight': {}}]:
        try: m.budget_gate({**budget, **change}, c)
        except ValueError: checks.append('refuse_budget_'+str(len(checks)))
        else: raise AssertionError('Unsafe/changed budget admitted')
    inputs = dict(loading=76, native_pipeline=325, wc_pipeline=219,
                  diagnostic_parent_without_children=273, unchanged_suffix_inclusive=121)
    cost = m.price(c, **inputs)
    assert cost['complete_scope_time_guaranteed'] is False
    for value in [math.nan, math.inf, 0, -1, True, 10000]:
        try: m.price(c, **{**inputs, 'unchanged_suffix_inclusive': value})
        except ValueError: checks.append('refuse_bad_or_over_cap_cost_'+str(len(checks)))
        else: raise AssertionError('Invalid or over-cap complete cost accepted')
    return {'status': 'FULL_CAUSAL_SCOPE_BUDGET_COST_CPU_CONTROLS_PASS_NO_GPU',
            'refusal_controls': len(checks), 'checks': checks, 'GPU_submissions': 0}


if __name__ == '__main__':
    import json
    print(json.dumps(run()))
