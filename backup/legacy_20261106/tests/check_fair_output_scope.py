"""Reject shortened fair matrices, fake Native, future choices and unpaid work."""
from copy import deepcopy
from wcomr.fair_output_scope import validate_scope, cost_gate, budget_gate


def run(config):
    validate_scope(config);cost_gate(config)
    checks = ['fourteen_output_scope_and_complete_cost']
    changes = [('planned_output_files',12),('planned_total_phases',12),
        ('workpoints',config['workpoints'][:5]),('metric_reference','wc006'),
        ('planned_native_relative_pairs',8),('expected_solver_updates',[36]*6),
        ('expected_CFG_calls',[72]*6),('native_mode','WC_FORCED_FULL'),
        ('native_forward_identity','worldcache.forward'),('fresh_prepare_per_phase',False),
        ('sample_names',['human_199']),('sample_indices',[2]),('seed',1),
        ('dense_fallback_layers',[]),('reuse_current_or_future_shadow_truth',True),
        ('uses_future_trace',True),('official_skip_predicate_replaced',True),
        ('fixed_deep_CFG_count',38),('exact_S_quota',9),('fixed_mask',{}),
        ('dense_calls',[True]*72),('per_cfg_eligible_ordinals',[[1],[1]]),('mask',{}),
        ('max_gpu_wall_seconds',1800),('child_timeout_seconds',6300),('kill_after_seconds',30),
        ('mode_policy','default'),('approximate_sources_are_true_dense_anchors',True),
        ('expected_WC_sha256',{}),('gpu_execution_selected','true')]
    for key,value in changes:
        changed=deepcopy(config);changed[key]=value
        try:validate_scope(changed)
        except ValueError:checks.append('refuse_'+key)
        else:raise AssertionError('Changed fair scope accepted: '+key)
    for key,value in [('every',2),('first_solver_step',12),('last_solver_step',35),
                      ('sparse_layers',[6]),('every',True)]:
        changed=deepcopy(config);changed['stage_policy'][key]=value
        try:validate_scope(changed)
        except ValueError:checks.append('refuse_policy_'+key)
        else:raise AssertionError('Changed stage policy accepted: '+key)
    for field,value in [('planning_envelope_seconds',float('nan')),
                        ('planning_envelope_seconds',6271),('planning_envelope_seconds',True),
                        ('shutdown_settlement_margin_seconds',29)]:
        changed=deepcopy(config);changed['cost_admission'][field]=value
        try:cost_gate(changed)
        except ValueError:checks.append('refuse_invalid_cost_'+field)
        else:raise AssertionError('Invalid cost accepted')
    base={'cap_gpu_hours':12,'used_gpu_hours':9.691073425147268,
          'budget_authorization_ref':'existing12h'}
    budget_gate(base,6300)
    for changed,seconds in [(dict(base,used_gpu_hours=11),6300),
        (dict(base,other_inflight={}),6300),(base,1800),(base,True),
        (dict(base,cap_gpu_hours=4),6300),(dict(base,used_gpu_hours=float('nan')),6300),
        (dict(base,used_gpu_hours=True),6300),(dict(base,budget_authorization_ref=''),6300)]:
        try:budget_gate(changed,seconds)
        except ValueError:checks.append('refuse_changed_budget_or_window')
        else:raise AssertionError('Invalid budget accepted')
    return {'status':'FAIR_FOURTEEN_OUTPUT_SCOPE_COST_BUDGET_CONTROLS_PASS','checks':checks}
