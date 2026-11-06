"""Admission controls reject oracle inputs, altered matrices and unpaid cost."""
from copy import deepcopy
from wcomr.stage_output_scope import validate_scope, cost_gate, budget_gate


def run(config):
    validate_scope(config);cost_gate(config)
    checks=['eight_output_scope_and_complete_cost']
    changes=[('planned_output_files',6),('planned_total_phases',6),
        ('fresh_prepare_per_phase',False),('sample_names',['human_199']),
        ('sample_indices',[2]),('seed',1),('dense_fallback_layers',[]),
        ('reuse_current_or_future_shadow_truth',True),('uses_future_trace',True),
        ('official_skip_predicate_replaced',True),('fixed_deep_CFG_count',38),
        ('exact_S_quota',11),('fixed_mask',{}),('dense_calls',[True]*72),
        ('per_cfg_eligible_ordinals',[[1],[1]]),('mask',{}),
        ('max_gpu_wall_seconds',1800),('child_timeout_seconds',3600),
        ('kill_after_seconds',30),('mode_policy','default'),
        ('approximate_sources_are_true_dense_anchors',True),
        ('expected_D_sha256',{}),('gpu_execution_selected','true'),
        ('measurement_sequences',[['official','candidate']]*2)]
    for key,value in changes:
        changed=deepcopy(config);changed[key]=value
        try:validate_scope(changed)
        except ValueError:checks.append('refuse_'+key)
        else:raise AssertionError('Changed online scope accepted: '+key)
    for key,value in [('every',3),('first_solver_step',12),('last_solver_step',35),
                      ('sparse_layers',[6]),('every',True)]:
        changed=deepcopy(config);changed['stage_policies'][0][key]=value
        try:validate_scope(changed)
        except ValueError:checks.append('refuse_policy_'+key)
        else:raise AssertionError('Changed stage policy accepted: '+key)
    for field,value in [('planning_envelope_seconds',float('nan')),
                        ('planning_envelope_seconds',3580),('planning_envelope_seconds',True),
                        ('shutdown_settlement_margin_seconds',29)]:
        changed=deepcopy(config);changed['cost_admission'][field]=value
        try:cost_gate(changed)
        except ValueError:checks.append('refuse_invalid_cost_'+field)
        else:raise AssertionError('Invalid cost accepted')
    base={'cap_gpu_hours':12,'used_gpu_hours':9.136838727254782,
          'budget_authorization_ref':'existing12h'}
    budget_gate(base,3600)
    for changed,seconds in [(dict(base,used_gpu_hours=11),3600),
        (dict(base,other_inflight={}),3600),(base,1800),(base,True),
        (dict(base,cap_gpu_hours=4),3600),(dict(base,used_gpu_hours=float('nan')),3600),
        (dict(base,used_gpu_hours=True),3600),(dict(base,budget_authorization_ref=''),3600)]:
        try:budget_gate(changed,seconds)
        except ValueError:checks.append('refuse_changed_budget_or_window')
        else:raise AssertionError('Invalid budget accepted')
    return {'status':'ONLINE_EIGHT_OUTPUT_SCOPE_COST_BUDGET_CONTROLS_PASS','checks':checks}
