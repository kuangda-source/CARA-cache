"""Frozen complete-output card; pure CPU scope, full cost and budget admission."""
import json
import math

CARD = 'WC-FULL-OUTPUT-R1-20261003-A'
RUN = 'wc-full-output-r1'
SAMPLES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191', 'human_199']


def validate_scope(config):
    fixed = {'card': CARD, 'run_id': RUN, 'max_gpu_wall_seconds': 6000,
        'sample_names': SAMPLES, 'sample_indices': [1, 2], 'seed': 0,
        'state_steps': [13, 21, 33, 35, 36], 'phases': ['baseline_full', 'restored_full'],
        'dense_fallback_layers': [6, 23, 27], 'policy': {'sim': .1, 'cdf': .98},
        'pv_skipping': False, 'deployment_sparse': True,
        'planned_total_phases': 6, 'planned_output_files': 6,
        'comparison_kind': 'closed_loop_interface',
        'mode_policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope': 'COMPLETE_OFFICIAL_VS_DENSE_ADAPTER_GATE_THEN_TWO_EXPOSED_CAL_WC_S_OUTPUT_PAIRS',
        'minimum_disk_free_bytes': 15000000000,
        'approximate_sources_are_true_dense_anchors': False,
        'reuse_current_or_future_shadow_truth': False, 'source_replacement_on_failure': False,
        'quality_evaluation': 'AUTOMATIC_VIDEO_FIDELITY_MOTION_TEMPORAL_DIAGNOSTICS_AFTER_ARTIFACT_AUDIT',
        'clean_performance_measurement': False, 'gpu_execution_selected': True}
    if any(json.dumps(config.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
           for k, v in fixed.items()):
        raise ValueError('Frozen complete six-output scope changed')


def cost_gate(config):
    validate_scope(config)
    a = config['cost_admission']
    vals = [a['planning_envelope_seconds'], a['shutdown_settlement_margin_seconds']]
    if (any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in vals)
            or sum(vals) > config['max_gpu_wall_seconds']):
        raise ValueError('Complete output cost does not fit independent6000 window')


def budget_gate(budget, seconds):
    used = budget['used_gpu_hours']
    if (seconds != 6000 or type(seconds) is not int or budget['cap_gpu_hours'] != 12
            or any(k.endswith('_inflight') for k in budget)
            or type(used) not in (int, float) or not math.isfinite(used) or used < 0
            or not budget.get('budget_authorization_ref') or (12 - used) * 3600 < seconds + 15):
        raise ValueError('Independent6000/current12h/no-inflight/balance gate failed')
