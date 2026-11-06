"""Pure admission for one exposed-human fixed-refresh diagnostic card."""
import hashlib
import json
import math

CARD = 'WC-FIXED-HUMAN-R1-20261004-A'
RUN = 'wc-fixed-human-r1'
RAW_SHA = '29ec9b86ca70d7241349f9808057a1e5f47491b0f8b1ba689167f9f8890701ae'


def validate_scope(config):
    fixed = {'card': CARD, 'run_id': RUN, 'max_gpu_wall_seconds': 1800,
        'sample_names': ['human_199'], 'sample_indices': [2], 'seed': 0,
        'dense_fallback_layers': [6, 23, 27], 'policy': {'sim': .1, 'cdf': .98},
        'pv_skipping': False, 'deployment_sparse': True,
        'planned_total_phases': 4, 'planned_output_files': 4,
        'measurement_sequence': ['official', 'candidate'], 'fresh_prepare_per_phase': True,
        'state_steps': [13, 21, 33, 35, 36],
        'mode_policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope': 'OFFLINE_EXPOSED_HUMAN_FIXED_MASK_DD_THEN_LIGHT_D_S',
        'minimum_disk_free_bytes': 15000000000,
        'approximate_sources_are_true_dense_anchors': False,
        'reuse_current_or_future_shadow_truth': False, 'source_replacement_on_failure': False,
        'teacher_trace_used_offline': True, 'online_policy': False,
        'shared_entry_RNG_across_control_and_measurement': True,
        'official_fixed_DD_gate_required': True, 'three_dense_artifacts_must_match': True,
        'fixed_deep_CFG_calls': 38, 'mask_manifest': 'manifests/wc_fixed_exposed_masks_draft_20261004.json',
        'mask_source_receipt_sha256': RAW_SHA,
        'pipeline_timing': 'CUDA_BOUNDARY_SYNCHRONIZED_COMPLETE_GENERATE',
        'substage_timing': 'UNSYNCHRONIZED_HOST_WALL_NOT_ISOLATED_CUDA_LATENCY',
        'quality_evaluation': 'AUTOMATIC_VIDEO_FIDELITY_MOTION_TEMPORAL_DIAGNOSTICS_AFTER_ARTIFACT_AUDIT'}
    if any(json.dumps(config.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
           for k, v in fixed.items()):
        raise ValueError('Frozen fixed-human four-output scope changed')
    if type(config.get('gpu_execution_selected')) is not bool:
        raise ValueError('Explicit independent execution selection required')


def validate_mask(config, stage, project):
    """Bind the frozen exposed mask to the actual original terminal receipt."""
    validate_scope(config)
    manifest = json.loads((stage / config['mask_manifest']).read_text())
    path = project / 'outputs/wc-light-output-r1/diagnostic/receipt.json'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RAW_SHA:
        raise ValueError('Original exposed teacher receipt changed')
    original = json.loads(raw)
    if manifest['source_receipt_sha256'] != RAW_SHA or manifest['execution_selected']:
        raise ValueError('Exposed mask identity or role changed')
    row, = [r for r in manifest['masks'] if r['sample_name'] == 'human_199']
    request, = [r for r in original['measurements']['requests'] if r['sample_name'] == 'human_199']
    official = [r for r in request['phases'] if r['kind'] == 'official']
    if len(official) != 2 or official[0]['trace'] != official[1]['trace']:
        raise ValueError('Two original official traces must agree')
    mask = row['dense_calls']
    context = original['reference_contexts'][original['scope']['sample_names'].index('human_199')]
    if (len(mask) != 72 or any(type(v) is not bool for v in mask)
            or mask != [r['deep_executed'] for r in official[0]['trace']]
            or sum(mask) != 38 or not all(mask[:14] + mask[70:])
            or row['model_id'] != 'Cosmos-Predict2.5-2B:' + config['f1_setup_sha256']
            or [row['model_id'], row['condition_id']] != context[1:]
            or row['source_receipt_sha256'] != RAW_SHA
            or row['horizon'] != 70 or row['warm_calls'] != 14
            or row['role'] != 'OFFLINE_FIXED_EXPOSED_TRACE_DIAGNOSTIC_NOT_DEPLOYMENT_ROUTING'):
        raise ValueError('Actual exposed mask/model/condition/phase protection differs')
    return row


def cost_gate(config):
    validate_scope(config)
    a = config['cost_admission']
    values = [a['planning_envelope_seconds'], a['shutdown_settlement_margin_seconds']]
    if (any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values)
            or sum(values) > config['max_gpu_wall_seconds']):
        raise ValueError('Full four-output cost does not fit independent1800 cap')


def budget_gate(budget, seconds):
    used = budget['used_gpu_hours']
    if (seconds != 1800 or type(seconds) is not int or budget['cap_gpu_hours'] != 12
            or any(k.endswith('_inflight') for k in budget)
            or type(used) not in (int, float) or not math.isfinite(used) or used < 0
            or not budget.get('budget_authorization_ref') or (12 - used) * 3600 < seconds + 15):
        raise ValueError('Independent fixed1800/current12h/no-inflight/balance gate failed')
