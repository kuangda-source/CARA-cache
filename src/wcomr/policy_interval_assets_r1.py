"""Complete, teacher-conditioned interval statistics and separate action prices.

The Cosmos adapter supports all source ages admitted by its physical paired
executor. Native teacher history conditions the proposal table; it is not the
history or endpoint truth of a subsequently generated policy.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

VERSION = 'WC_POLICY_INTERVAL_ASSETS_FULL1624_R1'
CONFIG = 'configs/wc_policy_interval_assets_full1624_r1_20261020.json'
RUN = 'wc-policy-interval-assets-cal4-full1624-r1'
CPU_PROOF = 'policy-assets-production-CPU-proof.json'
CPU_BUNDLE = 'policy-assets-production-CPU-bundle.json'
PROFILE = dict(horizon=36, protected_dense=list(range(1, 8)) + [36],
    max_source_age=28, min_C_anchors=2, min_A_anchors=1,
    alpha_candidates=[0.5, 1.0], CFG_coefficients=[8, -7],
    basis='PINNED_NATIVE_POLICY_EXECUTOR_INITIAL7_AND_CYCLE_RESET',
    source_history='CANONICAL_ACTUAL_D_TEACHER_LAST_TWO_ANCHORS_NOT_FREE_POLICY_HISTORY')
ACTIONS = ('C', 'A_HALF', 'A_ONE')
ROUNDS = (('WARMUP', ACTIONS), ('FORMAL_1', ACTIONS[::-1]),
          ('FORMAL_2', ACTIONS), ('FORMAL_3', ('A_HALF', 'A_ONE', 'C')))
SCENES = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199',
          'misc_13398218_3840_2160_60fps', 'av_51b45829-502e-4143-9c32-c026bd6ab191')
COUNTS = dict(requests=4, total_paths=14, formal_paths=12, full_warmup_paths=2,
    native_reference_paths=4, observer_OFF_control_paths=4, observer_ON_formal_paths=4,
    ordinary_pairs=504, ordinary_CFG_calls=1008, loads=1,
    legal_source_time_cells_per_prompt=406, formal_source_time_cells=1624,
    warm_source_time_cells=406, total_collected_source_time_cells=2030,
    minimum_price_trials_per_cell=6, warm_action_trials_per_cell=3,
    minimum_formal_action_trials_per_cell=3, canonical_price_cells_per_prompt=28,
    canonical_price_trials_per_cell=12, total_readout_pair_trials=13020,
    formal_cell_price_trials=10416, additional_deep_teacher_pairs=0)


def rounds_for(source, target):
    # Every legal cell has its own warm and formal execution for all alphas.
    # Replication of the stationary primitive clock is balanced at every time
    # and every CAL on the same nearest-D state, rather than mixing sources.
    return ROUNDS if source == target-1 else ROUNDS[:2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    import gzip
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def cells(profile=PROFILE):
    n = profile['horizon']; protected = set(profile['protected_dense'])
    return [(s, t) for t in range(1, n + 1) if t not in protected
        for s in range(1, t) if t-s <= profile['max_source_age']
        and not any(s < p < t for p in protected)]


def matrix(scenes=SCENES):
    if tuple(scenes) != SCENES:
        raise ValueError('Preserve the four exposed CAL identities and seed0')
    result = [dict(id='warm_'+str(i)+'_'+mode, scene=scenes[0], section='WARMUP',
                   mode=mode, observer=mode=='COLLECT', round=i)
              for i, mode in enumerate(('CONTROL', 'COLLECT'), 1)]
    for i, scene in enumerate(scenes):
        for mode in ('NATIVE', 'CONTROL', 'COLLECT'):
            result.append(dict(id='formal_'+str(i)+'_'+mode, scene=scene,
                section='FORMAL', mode=mode, observer=mode=='COLLECT', round=1))
    return result


def validate_contract(c):
    if (c.get('version') != VERSION or c.get('run_id') != RUN or c.get('profile') != PROFILE
        or c.get('scope_counts') != COUNTS or c.get('matrix') != matrix()
        or [r['name'] for r in c.get('requests', [])] != list(SCENES)
        or any(r['seed'] != 0 or r['num_steps'] != 35 or r['guidance'] != 7
               or r['num_output_frames'] != 93 or r['resolution'] != '432,768'
               for r in c['requests'])
        or c.get('cumulative_cap_GPUh') != 226
        or c.get('budget_origin_used_GPUh') != 79.99637737158223
        or c.get('autonomy_exclusive_upper_GPUh') != 12
        or c.get('label_basis') != 'TEACHER_CONDITIONED_PROPOSAL'
        or any(c.get(k) is not False for k in ('training', 'F_B_enabled', 'P_enabled',
                'endpoint_selection', 'new_generated_policy', 'clean_speed_claim'))
        or not 0 < c.get('forecast_complete_GPUh', 0) <= c.get('billed_limit_GPUh', 0)
        or c.get('guardrails_enabled') is not True):
        raise ValueError('Full four-CAL/1624-cell scope, ordinary guards and full quote required')
    if len(cells()) != 406 or len(matrix()) != 14:
        raise ValueError('Complete physical source/time domain changed')
    return c


def full_rows(rows):
    plan = matrix()
    if len(rows) > len(plan):
        raise ValueError('Extra unregistered paths')
    for r, p in zip(rows, plan):
        if any(r.get(k) != v for k, v in p.items()):
            raise ValueError('Registered position changed')
    return copy.deepcopy(rows) + [{**p, 'status':'NOT_REACHED'} for p in plan[len(rows):]]


def complete_quote(*, max_whole_request_seconds, load_seconds,
                   readout_inclusive_planning_seconds, latent_elements,
                   hidden_elements, prior_unattributed_seconds=0):
    """Observed inclusive intervals are conservative planning inputs, not prices.

    Include warm-cell collection, all balanced trials, all raw outputs, native
    controls, host/device transfers, SHA, CPU audit and occupied shutdown.
    """
    values = (max_whole_request_seconds, load_seconds, readout_inclusive_planning_seconds,
              latent_elements, hidden_elements, prior_unattributed_seconds)
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Finite nonnegative observed planning inputs required')
    if min(max_whole_request_seconds, readout_inclusive_planning_seconds,
           latent_elements, hidden_elements) <= 0:
        raise ValueError('No zero placeholder for unknown work')
    # Three actual guided outputs per cell, plus one D output per teacher step.
    raw = COUNTS['total_collected_source_time_cells'] * 3 * latent_elements * 4
    raw += 14 * 37 * latent_elements * 4
    # For each target, each source needs its last two actual-D probe/residuals,
    # conditional and unconditional, plus the returned C and Phi outputs.
    transfer = COUNTS['total_collected_source_time_cells'] * 8 * hidden_elements * 2
    # Explicit planning floors, not a claim about measured PCIe/disk bandwidth.
    terms = dict(load=load_seconds, full14_requests=14*max_whole_request_seconds,
        all_readout_trials=COUNTS['total_readout_pair_trials']*readout_inclusive_planning_seconds,
        source_transfer_planning=transfer/(0.5*1024**3),
        raw_write_and_read_and_SHA=raw*4/(0.15*1024**3),
        moments_and_full_output_equality=COUNTS['total_collected_source_time_cells']*0.5,
        setup_and_CPU_post=900., shutdown_reserve=180.,
        previous_unattributed=max(0., prior_unattributed_seconds))
    forecast = math.ceil(math.fsum(terms.values())*1.25)/3600
    limit = math.ceil(forecast*1.2*4)/4
    return dict(status='COMPLETE1624_PLANNING_QUOTE_NOT_ACTUAL_ACTION_PRICES',
        scope_counts=COUNTS, terms_seconds=terms, planning_margin=1.25,
        forecast_complete_GPUh=forecast, billed_limit_GPUh=limit,
        raw_tensor_planning_bytes=raw, source_transfer_planning_bytes=transfer,
        minimum_free_disk_bytes=math.ceil(raw*1.5+20*1024**3),
        peak_CPU_anchor_bank_planning_bytes=36*4*hidden_elements*2,
        observed_planning_inputs=dict(max_whole_request_seconds=max_whole_request_seconds,
            load_seconds=load_seconds, readout_inclusive_planning_seconds=readout_inclusive_planning_seconds,
            latent_elements=latent_elements, hidden_elements=hidden_elements),
        action_unit_prices_measured=False, actual_GPUh=None,
        specific_whole_card_confirmation_required=limit>=12,
        exact_runtime_upper_bound_guarantee=False)
