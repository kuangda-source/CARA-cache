import copy
import json

from wcomr.h1_scope import validate_h1_scope, cost_gate, scope_gate


def run(config):
    assert len(validate_h1_scope(config)) == 18
    cost_gate(config)
    for key, value in [('max_gpu_wall_seconds', 1200), ('reuse_ages', [1, 2]),
                       ('source_solver_step', 17.0), ('planned_lifetime_cells', 12),
                       ('future_true_D_replays', 1), ('state_steps', [21]),
                       ('deployment_sparse', True), ('approximate_sources_are_true_dense_anchors', True),
                       ('reuse_current_or_future_shadow_truth', True), ('card', 'old-r4')]:
        changed = copy.deepcopy(config)
        changed[key] = value
        try:
            validate_h1_scope(changed)
        except ValueError:
            pass
        else:
            raise AssertionError('Altered H1 scope accepted: ' + key)
    for admission in ({'planning_envelope_seconds': 1800, 'shutdown_settlement_margin_seconds': 30},
                      {'planning_envelope_seconds': float('nan'), 'shutdown_settlement_margin_seconds': 30}):
        changed = dict(config, cost_admission=admission)
        try:
            cost_gate(changed)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid time envelope accepted')
    budget = {'cap_gpu_hours': 12, 'used_gpu_hours': 5.05310433089345,
              'budget_authorization_ref': 'manifests/budget_authorization_20261003.json'}
    scope_gate(budget, 1800)
    for changed in (dict(budget, cap_gpu_hours=4), dict(budget, used_gpu_hours=11.9),
                    dict(budget, used_gpu_hours=-1), dict(budget, used_gpu_hours=float('nan')),
                    dict(budget, wc_h0_complement_inflight={}), dict(budget, budget_authorization_ref=None)):
        try:
            scope_gate(changed, 1800)
        except ValueError:
            pass
        else:
            raise AssertionError('Unsafe or reset budget accepted')
    return {'status': 'H1_SCOPE_COST_BUDGET_CONTROLS_PASS',
        'altered_scope_cases_rejected': 10, 'invalid_cost_cases_rejected': 2,
        'invalid_budget_cases_rejected': 6}
