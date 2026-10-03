"""Frozen source, placement, cost and budget gates for one oracle diagnostic."""
import hashlib
import json

from wcomr.selective_output_scope import budget_gate, FULL, TEACHER_SHA, D_SHA

CARD = 'WC-FORECAST-PLACEMENT-HUMAN-R1-20261004-A'
RUN = 'wc-forecast-placement-human-r1'
PREVIOUS_SHA = 'a752a19587552ca4842a3dec0683bbf42891a3a774c4987ca104c58cc0364265'
S_SHA = '7caed197cce35067d62baab668c8b992275fdfb50939f7a5549813e1ac9a119b'
PLACEMENT_SHA = 'a47d9c4167468b4e6e35a7c567aa2108108b8d3f280bf04cfcdbec650fe42ad9'
VARIANTS = [
    {'name': 'legacy_SD', 'sparse_layers': FULL, 'every': 2},
    {'name': 'first_S_matched', 'sparse_layers': FULL, 'every': 1,
     'per_cfg_eligible_ordinals': [[1, 4, 5, 6, 7, 8], [1, 4, 5, 6, 7]]},
    {'name': 'minimum_footprint', 'sparse_layers': FULL, 'every': 1,
     'per_cfg_eligible_ordinals': [[4, 5, 6, 7, 8, 9], [4, 5, 6, 7, 8]]},
]


def validate_scope(c):
    fixed = {
        'card': CARD, 'run_id': RUN, 'max_gpu_wall_seconds': 2400,
        'sample_names': ['human_199'], 'sample_indices': [2], 'seed': 0,
        'dense_fallback_layers': [6, 23, 27], 'policy': {'sim': .1, 'cdf': .98},
        'pv_skipping': False, 'deployment_sparse': True,
        'planned_total_phases': 6, 'planned_output_files': 6,
        'measurement_sequence': ['official', 'candidate', 'candidate', 'candidate'],
        'measurement_sequence_policy': 'reference_then_candidates',
        'variants': VARIANTS, 'comparison': 'forecast_placement',
        'selection_cadence': 'EXPOSED_FUTURE_TRACE_SAME_PER_CFG_S_BUDGET_ORACLE_PLACEMENT',
        'fresh_prepare_per_phase': True, 'state_steps': [13, 21, 33, 35, 36],
        'mode_policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope': 'OFFLINE_ORACLE_FORECAST_PLACEMENT_SIX_OUTPUT_SAME_NOMINAL_COMPUTE',
        'minimum_disk_free_bytes': 15000000000,
        'teacher_trace_used_offline': True, 'online_policy': False,
        'causal_refresh_value_labels': False,
        'approximate_sources_are_true_dense_anchors': False,
        'reuse_current_or_future_shadow_truth': False,
        'source_replacement_on_failure': False,
        'shared_entry_RNG_across_control_and_measurement': True,
        'official_fixed_DD_gate_required': True, 'three_dense_artifacts_must_match': True,
        'legacy_SD_output_gate_before_new_variants': True, 'fixed_deep_CFG_calls': 38,
        'same_S_per_CFG': [6, 5], 'same_S_operators_per_candidate': 253,
        'mask_manifest': 'manifests/wc_fixed_exposed_masks_draft_20261004.json',
        'mask_source_receipt_sha256': TEACHER_SHA,
        'placement_manifest': 'manifests/wc_forecast_placement_draft_20261004.json',
        'placement_manifest_sha256': PLACEMENT_SHA,
        'previous_selective_receipt_sha256': PREVIOUS_SHA,
        'previous_D_sha256': D_SHA, 'previous_legacy_SD_sha256': S_SHA,
        'pipeline_timing': 'CUDA_BOUNDARY_SYNCHRONIZED_COMPLETE_GENERATE',
        'substage_timing': 'UNSYNCHRONIZED_HOST_WALL_NOT_ISOLATED_CUDA_LATENCY',
        'quality_evaluation': 'AUTOMATIC_VIDEO_FIDELITY_MOTION_TEMPORAL_DIAGNOSTICS_AFTER_ARTIFACT_AUDIT',
    }
    if any(json.dumps(c.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
           for k, v in fixed.items()):
        raise ValueError('Frozen forecast placement six-output scope changed')
    if type(c.get('gpu_execution_selected')) is not bool:
        raise ValueError('Explicit independent GPU execution selection required')


def validate_mask(c, stage, project):
    validate_scope(c)
    manifest = json.loads((stage / c['mask_manifest']).read_text())
    raw = (project / 'outputs/wc-light-output-r1/diagnostic/receipt.json').read_bytes()
    if (hashlib.sha256(raw).hexdigest() != TEACHER_SHA
            or manifest['source_receipt_sha256'] != TEACHER_SHA or manifest['execution_selected']):
        raise ValueError('Original exposed teacher or offline mask identity changed')
    original = json.loads(raw)
    row, = [r for r in manifest['masks'] if r['sample_name'] == 'human_199']
    q, = [q for q in original['measurements']['requests'] if q['sample_name'] == 'human_199']
    official = [p for p in q['phases'] if p['kind'] == 'official']
    context = original['reference_contexts'][original['scope']['sample_names'].index('human_199')]
    calls = row['dense_calls']
    if (len(official) != 2 or official[0]['trace'] != official[1]['trace']
            or len(calls) != 72 or any(type(v) is not bool for v in calls) or sum(calls) != 38
            or calls != [r['deep_executed'] for r in official[0]['trace']]
            or not all(calls[:14] + calls[70:])
            or [row['model_id'], row['condition_id']] != context[1:]
            or row['model_id'] != 'Cosmos-Predict2.5-2B:' + c['f1_setup_sha256']
            or row['source_receipt_sha256'] != TEACHER_SHA
            or row['horizon'] != 70 or row['warm_calls'] != 14
            or row['role'] != 'OFFLINE_FIXED_EXPOSED_TRACE_DIAGNOSTIC_NOT_DEPLOYMENT_ROUTING'):
        raise ValueError('Actual common mask/model/condition binding changed')
    previous_raw = (project / 'outputs/wc-selective-human-r1/diagnostic/receipt.json').read_bytes()
    if hashlib.sha256(previous_raw).hexdigest() != PREVIOUS_SHA:
        raise ValueError('Previous selective six-output receipt changed')
    previous = json.loads(previous_raw)
    if (previous['status'] != 'SIX_SELECTIVE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
            or previous['fixed_mask'] != row or previous['reference_context'][1:] != context[1:]
            or previous['measurement']['variant_names'] != ['fixed_D', 'full_S', 'small_S', 'cadenced_S']):
        raise ValueError('Previous selective comparison identity differs')
    for i, digest in ((0, D_SHA), (3, S_SHA)):
        p = previous['measurement']['phases'][i]
        artifact, = p['artifacts']
        path = (project / 'outputs/wc-selective-human-r1/diagnostic/measurement/human_199'
                / (str(i).zfill(3) + '_' + p['kind']) / 'human_199.mp4')
        if artifact['sha256'] != digest or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Actual previous D or legacy SD artifact changed')
    placement_raw = (stage / c['placement_manifest']).read_bytes()
    if hashlib.sha256(placement_raw).hexdigest() != PLACEMENT_SHA:
        raise ValueError('Frozen offline placement manifest changed')
    placement = json.loads(placement_raw)
    if (placement['source_raw_sha256'] != PREVIOUS_SHA or placement['fixed_mask'] != row
            or placement['same_S_quota_per_CFG'] != [6, 5]
            or placement['GPU_card_selected'] or placement['GPU_submitted']
            or placement['reserved_seconds'] != 0 or placement['online_policy']):
        raise ValueError('Historical placement draft/source role changed')
    from wcomr.selective_refresh_policy import SparseRefreshPolicy, SparsePlacementPolicy
    policies = (SparseRefreshPolicy(tuple(FULL), 2),) + tuple(
        SparsePlacementPolicy(tuple(v['sparse_layers']), v['every'],
                              tuple(tuple(s) for s in v['per_cfg_eligible_ordinals']))
        for v in VARIANTS[1:])
    for policy, key in zip(policies, ('legacy_policy', 'first_S_matched_policy', 'unconstrained_policy')):
        if policy.to_dict() != placement[key]:
            raise ValueError('Runtime policy differs from frozen CPU placement')
    return row


def cost_gate(c):
    import math
    validate_scope(c)
    values = [c['cost_admission']['planning_envelope_seconds'],
              c['cost_admission']['shutdown_settlement_margin_seconds']]
    if (any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values)
            or values != [2252.988448896557, 30] or sum(values) > 2400):
        raise ValueError('Full six-output cost does not fit independent2400 cap')
