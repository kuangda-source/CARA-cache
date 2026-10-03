"""Reject changed comparison scope, unpayable cost and inflight budget."""
from copy import deepcopy
from wcomr.light_output_scope import validate_scope, cost_gate, budget_gate


def run(config):
    validate_scope(config)
    cost_gate(config)
    checks = ['ten_output_scope_and_full_cost']
    for key, value in [('planned_output_files', 8), ('fresh_prepare_per_phase', False),
                       ('measurement_sequences', [['official', 'candidate']] * 2),
                       ('reuse_current_or_future_shadow_truth', True)]:
        changed = deepcopy(config)
        changed[key] = value
        try:
            validate_scope(changed)
        except ValueError:
            checks.append('refuse_' + key)
        else:
            raise AssertionError('Changed light scope accepted: ' + key)
    for value in (float('nan'), 5990):
        changed = deepcopy(config)
        changed['cost_admission']['planning_envelope_seconds'] = value
        try:
            cost_gate(changed)
        except ValueError:
            checks.append('refuse_nonfinite_or_unpayable_full_cost')
        else:
            raise AssertionError('Invalid full cost accepted')
    base = {'cap_gpu_hours':12, 'used_gpu_hours':6.733473505896205,
            'budget_authorization_ref':'existing12h'}
    budget_gate(base, 6000)
    for changed, seconds in [(dict(base, used_gpu_hours=11), 6000),
                             (dict(base, other_inflight={}), 6000),
                             (base, 1800), (dict(base, cap_gpu_hours=4), 6000)]:
        try:
            budget_gate(changed, seconds)
        except ValueError:
            checks.append('refuse_changed_budget_or_window')
        else:
            raise AssertionError('Invalid budget accepted')
    return {'status':'LIGHT_TEN_OUTPUT_SCOPE_COST_BUDGET_CONTROLS_PASS', 'checks':checks}
