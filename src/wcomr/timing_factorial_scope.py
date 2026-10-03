"""Independent early/late missing-arm scope and immutable historical bindings."""
import hashlib
import json

import wcomr.forecast_placement_scope as previous
from wcomr.forecast_placement import replay
from wcomr.selective_refresh_policy import SparsePlacementPolicy, SparseRefreshPolicy
from wcomr.selective_output_scope import budget_gate as previous_budget_gate
from wcomr.timing_factorial_policy import validate_timing_factorial

CARD = 'WC-TIMING-FACTORIAL-HUMAN-R1-20261004-A'
RUN = 'wc-timing-factorial-human-r1'
FORECAST_SHA = 'f6fb44d6b9f6133c23d7b7b291e22e53d60f55db14beb9117132b0e901d3d11c'
DRAFT_SHA = 'c40e20d7b4155def39e801772de3e75c47dc1f78b4e2405e1c5a56120b64ebbc'
CONFIG_SHA = 'e1114baaf9600dfb246af17d2ac69de548183316761b22fcc3d407acb69f79ed'
FIRST_SHA = '52c106096b1d8aba76bc75351132f44c509dae1c008969d8f15e5865280b1dad'
FREE_SHA = '0eea0e004e127947784a197a88dadc0cdd346b34e740008f1ddc06be7204455d'
VARIANTS = [previous.VARIANTS[0],
    {'name': 'E0L0', 'sparse_layers': previous.FULL, 'every': 1,
     'per_cfg_eligible_ordinals': [[4, 5, 6, 7, 8], [4, 5, 6, 7]]},
    {'name': 'E1L1', 'sparse_layers': previous.FULL, 'every': 1,
     'per_cfg_eligible_ordinals': [[1, 4, 5, 6, 7, 8, 9], [1, 4, 5, 6, 7, 8]]}]
COST = {'planning_envelope_seconds': 2304.4287959468365,
    'shutdown_settlement_margin_seconds': 30, 'unbuffered_seconds': 1920.3573299556972,
    'buffer_factor': 1.2, 'control_per_output_seconds': 381.7508979411796,
    'measurement_per_output_seconds': 235.7682573137805, 'load_seconds': 95.91554894298315,
    'bookkeeping_seconds': 75,
    'scope': 'TWO_DD_PLUS_D_LEGACY_NEITHER_BOTH_LIGHT_LOADING_SOURCE_KERNEL_FIRST_USE_AND_SETTLEMENT',
    'both_measurement_proxy_seconds': 278.6352131890133,
    'both_proxy_basis': 'Conservatively multiply the entire candidate pipeline proxy by13/11; same fixed38 full/deep calls, do not assert linear kernel runtime.'}


def policies():
    return (SparseRefreshPolicy(tuple(previous.FULL), 2),) + tuple(
        SparsePlacementPolicy(tuple(v['sparse_layers']), v['every'],
            tuple(tuple(s) for s in v['per_cfg_eligible_ordinals'])) for v in VARIANTS[1:])


def validate_scope(c):
    changed = {
        'card': CARD, 'run_id': RUN, 'comparison': 'timing_factorial', 'variants': VARIANTS,
        'scope': 'OFFLINE_EARLY_LATE_FACTORIAL_SIX_OUTPUT_DIFFERENT_S_COUNTS_NOT_MATCHED_COST',
        'selection_cadence': 'EXPOSED_FUTURE_TRACE_EARLY_LATE_FACTORIAL_MISSING_ARMS',
        'S_per_variant_CFG': [[6, 5], [5, 4], [7, 6]],
        'S_operators_per_variant': [253, 207, 299],
        'varying_S_counts_are_not_matched_cost': True,
        'existing_factorial_arms': ['E1L0', 'E0L1'],
        'existing_arm_output_binding_before_new_variants': True,
        'factorial_manifest': 'manifests/wc_timing_factorial_draft_20261004.json',
        'factorial_manifest_sha256': DRAFT_SHA,
        'historical_forecast_config': 'configs/wc_forecast_placement_human_r1.json',
        'historical_forecast_config_sha256': CONFIG_SHA,
        'previous_forecast_receipt_sha256': FORECAST_SHA,
        'previous_first_S_matched_sha256': FIRST_SHA,
        'previous_minimum_footprint_sha256': FREE_SHA,
    }
    if (any(json.dumps(c.get(k), sort_keys=True) != json.dumps(v, sort_keys=True)
            for k, v in changed.items()) or 'same_S_per_CFG' in c
            or 'same_S_operators_per_candidate' in c):
        raise ValueError('Frozen early/late scope or non-matched-cost role changed')
    # Validate all unchanged scientific gates using the original frozen contract.
    legacy = dict(c)
    legacy.update(card=previous.CARD, run_id=previous.RUN, comparison='forecast_placement',
        variants=previous.VARIANTS,
        scope='OFFLINE_ORACLE_FORECAST_PLACEMENT_SIX_OUTPUT_SAME_NOMINAL_COMPUTE',
        selection_cadence='EXPOSED_FUTURE_TRACE_SAME_PER_CFG_S_BUDGET_ORACLE_PLACEMENT',
        same_S_per_CFG=[6, 5], same_S_operators_per_candidate=253)
    previous.validate_scope(legacy)
    expected, _ = validate_timing_factorial(policies(), tuple(previous.FULL), [12, 10])
    if expected != c['S_per_variant_CFG']:
        raise ValueError('Timing scope and controller policies disagree')


def validate_mask(c, stage, project):
    validate_scope(c)
    raw_config = (stage / c['historical_forecast_config']).read_bytes()
    if hashlib.sha256(raw_config).hexdigest() != CONFIG_SHA:
        raise ValueError('Historical forecast configuration changed')
    row = previous.validate_mask(json.loads(raw_config), stage, project)
    raw = (project / 'outputs/wc-forecast-placement-human-r1/diagnostic/receipt.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != FORECAST_SHA:
        raise ValueError('Original complete forecast receipt changed')
    original = json.loads(raw)
    if (original['status'] != 'SIX_FORECAST_PLACEMENT_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
            or original['comparison'] != 'forecast_placement' or original['fixed_mask'] != row
            or original['reference_context'][1:] != [row['model_id'], row['condition_id']]
            or original['measurement']['variant_names'] != ['fixed_D', 'legacy_SD', 'first_S_matched', 'minimum_footprint']):
        raise ValueError('Historical forecast comparison identity changed')
    for i, digest in enumerate((previous.D_SHA, previous.S_SHA, FIRST_SHA, FREE_SHA)):
        phase = original['measurement']['phases'][i]
        artifact, = phase['artifacts']
        path = project / 'outputs/wc-forecast-placement-human-r1/diagnostic/measurement/human_199' / (str(i).zfill(3) + '_' + phase['kind']) / 'human_199.mp4'
        if artifact['sha256'] != digest or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Historical D/legacy/first/free physical video changed')
    draft_raw = (stage / c['factorial_manifest']).read_bytes()
    if hashlib.sha256(draft_raw).hexdigest() != DRAFT_SHA:
        raise ValueError('Immutable factorial draft changed')
    draft = json.loads(draft_raw)
    if (draft['source_raw_sha256'] != FORECAST_SHA or draft['fixed_mask'] != row
            or draft['GPU_card_selected'] or draft['GPU_submitted'] or draft['reserved_seconds']
            or draft['online_policy'] or draft['causal_refresh_value_labels']):
        raise ValueError('Factorial historical source or draft role differs')
    arms = {v['name']: v for v in draft['arms']}
    for name, index, digest in (('E1L0', 2, FIRST_SHA), ('E0L1', 3, FREE_SHA)):
        arm = arms[name]; phase = original['measurement']['phases'][index]
        p = SparsePlacementPolicy(tuple(previous.FULL), per_cfg_eligible_ordinals=tuple(
            tuple(v) for v in arm['policy']['per_cfg_eligible_ordinals']))
        if (arm['existing_GPU_phase_index'] != index or arm['existing_video_sha256'] != digest
                or arm['policy'] != phase['refresh_provenance']['selection_policy']
                or replay(phase['refresh_provenance']['events'], p, verify_actual=True) != arm['source_replay']):
            raise ValueError('Existing factorial arm does not match original actual source graph')
    events = original['measurement']['phases'][1]['refresh_provenance']['events']
    for p, name in zip(policies()[1:], ('E0L0', 'E1L1')):
        if p.to_dict() != arms[name]['policy'] or replay(events, p) != arms[name]['source_replay']:
            raise ValueError('Missing arm policy/source graph differs from immutable draft')
    return row


def cost_gate(c):
    validate_scope(c)
    if (c.get('cost_admission') != COST
            or COST['planning_envelope_seconds'] + COST['shutdown_settlement_margin_seconds'] > 2400):
        raise ValueError('Full factorial cost differs or does not fit independent2400 cap')


def budget_gate(b, seconds):
    previous_budget_gate(b, seconds)
    if b['budget_authorization_ref'] != 'manifests/budget_authorization_20261003.json':
        raise ValueError('Cumulative budget authority differs')
