"""Pure scope/cost admission for the independent ten-output light card."""
import json
import math

CARD = 'WC-LIGHT-OUTPUT-R1-20261003-A'
RUN = 'wc-light-output-r1'
SAMPLES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191', 'human_199']
SEQUENCES = [['official', 'candidate', 'candidate', 'official'],
             ['candidate', 'official', 'official', 'candidate']]


def validate_scope(config):
    fixed = {'card': CARD, 'run_id': RUN, 'max_gpu_wall_seconds': 6000,
        'sample_names': SAMPLES, 'sample_indices': [1, 2], 'seed': 0,
        'dense_fallback_layers': [6, 23, 27], 'policy': {'sim': .1, 'cdf': .98},
        'pv_skipping': False, 'deployment_sparse': True,
        'planned_total_phases': 10, 'planned_output_files': 10,
        'measurement_sequences': SEQUENCES, 'fresh_prepare_per_phase': True,
        'state_steps': [13, 21, 33, 35, 36],
        'mode_policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope': 'FRESH_PREPARE_LIGHT_DD_THEN_TWO_EXPOSED_CAL_BALANCED_WC_S_REPEATS',
        'minimum_disk_free_bytes': 15000000000,
        'approximate_sources_are_true_dense_anchors': False,
        'reuse_current_or_future_shadow_truth': False, 'source_replacement_on_failure': False,
        'pipeline_timing': 'CUDA_BOUNDARY_SYNCHRONIZED_COMPLETE_GENERATE',
        'substage_timing': 'UNSYNCHRONIZED_HOST_WALL_NOT_ISOLATED_CUDA_LATENCY',
        'quality_evaluation': 'AUTOMATIC_VIDEO_FIDELITY_MOTION_TEMPORAL_DIAGNOSTICS_AFTER_ARTIFACT_AUDIT'}
    if any(json.dumps(config.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
           for k, v in fixed.items()):
        raise ValueError('Frozen ten-output light scope changed')
    if type(config.get('gpu_execution_selected')) is not bool:
        raise ValueError('Explicit independent execution selection required')


def cost_gate(config):
    validate_scope(config)
    a = config['cost_admission']
    values = [a['planning_envelope_seconds'], a['shutdown_settlement_margin_seconds']]
    if (any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values)
            or sum(values) > config['max_gpu_wall_seconds']):
        raise ValueError('Full ten-output cost does not fit independent6000 cap')


def budget_gate(budget, seconds):
    used = budget['used_gpu_hours']
    if (seconds != 6000 or type(seconds) is not int or budget['cap_gpu_hours'] != 12
            or any(k.endswith('_inflight') for k in budget)
            or type(used) not in (int, float) or not math.isfinite(used) or used < 0
            or not budget.get('budget_authorization_ref') or (12 - used) * 3600 < seconds + 15):
        raise ValueError('Independent light6000/current12h/no-inflight/balance gate failed')
