"""No-Torch identity, complete-scope, time and cumulative-budget gates for H1."""
import json
import math

CARD = 'WC-H1-LOCAL-LIFETIME-R1-20261003-A'
RUN = 'wc-h1-local-lifetime-r1'


def validate_h1_scope(config):
    fixed = {
        'card': CARD, 'run_id': RUN, 'max_gpu_wall_seconds': 1800,
        'stop_after_solver_steps': 21, 'state_steps': [13, 21],
        'phases': ['baseline_prefix', 'observed_prefix'],
        'source_solver_step': 17, 'source_cfg_calls': [33, 34],
        'reuse_ages': [1, 2, 4], 'future_cfg_calls': [35, 36, 37, 38, 41, 42],
        'sample_name': 'common_sense_6487f37f-ef57-49ca-afdc-d898922b5191',
        'dense_fallback_layers': [6, 23, 27], 'policy': {'sim': .1, 'cdf': .98},
        'warmups': 1, 'repeats': 3, 'future_true_D_replays': 2,
        'planned_source_arms': 6, 'planned_lifetime_cells': 18, 'planned_raw_files': 30,
        'source_kinds': ['dense', 'matched_full', 'sparse'],
        'pv_skipping': False, 'deployment_sparse': False,
        'mode_policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope': 'FIXED_OFFICIAL_TRAJECTORY_LOCAL_SOURCE_AGE_NOT_FORKED_ROLLOUT_OR_VIDEO',
        'minimum_disk_free_bytes': 15000000000,
        'approximate_sources_are_true_dense_anchors': False,
        'reuse_current_or_future_shadow_truth': False,
    }
    # JSON canonicalization also rejects float/bool substitutions for integer
    # ages/counters; ordinary Python equality alone would accept those.
    if any(json.dumps(config.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
           for k, v in fixed.items()):
        raise ValueError('Frozen H1 complete18-cell local card altered')
    return {(branch, age, kind) for branch in (0, 1) for age in (1, 2, 4)
            for kind in ('dense', 'matched_full', 'sparse')}


def cost_gate(config):
    admission = config['cost_admission']
    values = [admission['planning_envelope_seconds'], admission['shutdown_settlement_margin_seconds']]
    if (any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in values)
            or sum(values) > config['max_gpu_wall_seconds']):
        raise ValueError('H1 full-scope cost admission failed')


def scope_gate(budget, seconds):
    if (type(seconds) is not int or seconds != 1800 or budget['cap_gpu_hours'] != 12
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Independent1800s H1 card/current12h ledger/no inflight required')
    used = budget['used_gpu_hours']
    if (type(used) not in (int, float) or not math.isfinite(used) or used < 0
            or not budget.get('budget_authorization_ref') or (12 - used) * 3600 < seconds + 15):
        raise ValueError('H1 authorization/balance/settlement margin missing')
