"""Pure-Python complete scope and budget gate for the proposed early/late card."""
import json
import math

CARD = 'WC-H1-GENERALIZATION-R1-20261003-A'
RUN = 'wc-h1-generalization-r1'
SAMPLES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191', 'human_199']


def validate_generalization_scope(config):
    fixed = {
        'card': CARD, 'run_id': RUN, 'max_gpu_wall_seconds': 6000,
        'sample_names': SAMPLES, 'sample_indices': [1, 2], 'seed': 0,
        'stop_after_solver_steps': 33, 'state_steps': [13, 21, 33],
        'phases': ['baseline_prefix', 'observed_prefix'],
        'source_regions': [{'name': 'early', 'source_step_bounds': [8, 12]},
                           {'name': 'late', 'source_step_bounds': [25, 29]}],
        'source_selection_rule': 'EARLIEST_PAIRED_TRUE_FULL_WITH_PAID_PROBE_AND_TWO_PAST_SAME_CFG_ANCHORS',
        'selection_inputs': ['call', 'cache_counter_before', 'deep_executed'],
        'reuse_ages': [1, 2, 4], 'source_kinds': ['dense', 'matched_full', 'sparse'],
        'dense_fallback_layers': [6, 23, 27], 'policy': {'sim': .1, 'cdf': .98},
        'warmups': 1, 'repeats': 3, 'future_true_D_replays': 2,
        'planned_source_arms': 24, 'planned_lifetime_cells': 72, 'planned_raw_files': 120,
        'planned_source_arms_per_request': 12, 'planned_lifetime_cells_per_request': 36,
        'pv_skipping': False, 'deployment_sparse': False,
        'mode_policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope': 'FIXED_OFFICIAL_TRAJECTORY_TWO_EXPOSED_CAL_EARLY_LATE_NOT_CONF_OR_VIDEO',
        'minimum_disk_free_bytes': 60000000000,
        'approximate_sources_are_true_dense_anchors': False,
        'reuse_current_or_future_shadow_truth': False,
        'source_replacement_on_failure': False, 'candidate_error_used_for_selection': False,
        'gpu_execution_selected': True,
    }
    if any(json.dumps(config.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
           for k, v in fixed.items()):
        raise ValueError('Frozen generalization24-source/72-cell scope changed')
    return {(name, region, branch, age, kind) for name in SAMPLES
            for region in ('early', 'late') for branch in (0, 1)
            for age in (1, 2, 4) for kind in ('dense', 'matched_full', 'sparse')}


def cost_gate(config):
    admission = config['cost_admission']
    values = [admission['planning_envelope_seconds'], admission['shutdown_settlement_margin_seconds']]
    if (any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in values)
            or sum(values) > config['max_gpu_wall_seconds']):
        raise ValueError('Complete early/late two-scene cost does not fit proposed window')


def budget_gate(budget, seconds):
    if (type(seconds) is not int or seconds != 6000 or budget['cap_gpu_hours'] != 12
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('New generalization6000 scope/current12h/no inflight required')
    used = budget['used_gpu_hours']
    if (type(used) not in (int, float) or not math.isfinite(used) or used < 0
            or not budget.get('budget_authorization_ref') or (12 - used) * 3600 < seconds + 15):
        raise ValueError('Generalization balance or cumulative authorization missing')
