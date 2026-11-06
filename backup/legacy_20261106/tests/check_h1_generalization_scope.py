"""CPU guards for full72 scope, selection-only baseline data, cost and budget."""
import copy

from wcomr.h1_generalization import REGIONS, select_sources
from wcomr.h1_generalization_scope import validate_generalization_scope, cost_gate, budget_gate


def reject(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Invalid scope or selection accepted')


def run(config):
    assert len(validate_generalization_scope(config)) == 72
    cost_gate(config)
    budget = {'cap_gpu_hours': 12, 'used_gpu_hours': 5.300050075675308,
              'budget_authorization_ref': 'manifests/budget_authorization_20261003.json'}
    budget_gate(budget, 6000)
    mutations = [('sample_names', config['sample_names'][:1]), ('sample_indices', [1, 3]),
                 ('reuse_ages', [1, 2]), ('planned_lifetime_cells', 36),
                 ('source_replacement_on_failure', True), ('candidate_error_used_for_selection', True),
                 ('gpu_execution_selected', False),
                 ('deployment_sparse', True), ('approximate_sources_are_true_dense_anchors', True),
                 ('source_regions', [{'name': 'early', 'source_step_bounds': [9, 13]},
                                     {'name': 'late', 'source_step_bounds': [25, 29]}]),
                 ('max_gpu_wall_seconds', 7200), ('seed', False), ('state_steps', [13, 33])]
    for key, value in mutations:
        c = copy.deepcopy(config); c[key] = value
        reject(lambda: validate_generalization_scope(c))
    for value in (float('nan'), -1, 6000):
        c = copy.deepcopy(config); c['cost_admission']['planning_envelope_seconds'] = value
        reject(lambda: cost_gate(c))
    for key, value in [('cap_gpu_hours', 4), ('used_gpu_hours', 11),
                       ('used_gpu_hours', float('nan')), ('used_gpu_hours', -1),
                       ('wc_h1_lifetime_inflight', {}), ('budget_authorization_ref', '')]:
        b = dict(budget); b[key] = value
        reject(lambda: budget_gate(b, 6000))
    trace = [{'call': i + 1, 'cache_counter_before': i,
              'deep_executed': i < 14 or i // 2 + 1 in (10, 12, 27, 29)} for i in range(66)]
    selected = select_sources(trace, REGIONS)
    assert [row['source_solver_step'] for row in selected['selected']] == [10, 27]
    # One CFG becoming full earlier must not change the paired source choice.
    trace[16]['deep_executed'] = True
    assert [row['source_solver_step'] for row in select_sources(trace, REGIONS)['selected']] == [10, 27]
    failures = []
    for mode in ('missing_late', 'counter', 'bool_counter', 'incomplete', 'regions'):
        t, regions = copy.deepcopy(trace), copy.deepcopy(REGIONS)
        if mode == 'missing_late':
            for i in range(48, 58): t[i]['deep_executed'] = False
        elif mode == 'counter': t[4]['cache_counter_before'] = 3
        elif mode == 'bool_counter': t[0]['cache_counter_before'] = False
        elif mode == 'incomplete': t.pop()
        else: regions[0]['source_step_bounds'] = [7, 12]
        reject(lambda: select_sources(t, regions)); failures.append(mode)
    return {'status': 'H1_GENERALIZATION_SCOPE_SELECTION_COST_BUDGET_CPU_PASS',
            'scope_mutations_rejected': len(mutations), 'cost_failures_rejected': 3,
            'budget_failures_rejected': 6, 'selector_failures_rejected': failures,
            'one_branch_full_does_not_select_unpaired_source': True,
            'full_planned_lifetime_cells': 72, 'GPU_execution_authorized_by_this_CPU_test': False}
