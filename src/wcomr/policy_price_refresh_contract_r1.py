"""Separate full-domain price refresh; reuse accepted labels and Native truth.

This is a scope/quote contract, not a production collector or dispatch permit.
"""
import math

from .policy_interval_assets_r1 import ACTIONS, ROUNDS, SCENES, cells

VERSION = 'CARA_PRICE_REFRESH_FULL1624_R1'
COUNTS = dict(requests=4, total_paths=10, formal_paths=8, warm_paths=2,
    new_Native_paths=0, reused_accepted_Native_paths=4,
    CONTROL_paths=5, PRICE_paths=5, ordinary_pairs=360, ordinary_CFG_calls=720,
    loads=1, formal_cells=1624, warm_cells=406, total_cells=2030,
    warmup_round_readout_trials=6090, formal_round_readout_trials=18270,
    formal_path_readout_trials=19488, warm_path_readout_trials=4872, total_readout_trials=24360,
    formal_repetitions_per_cell_action=3, new_error_labels=0)


def matrix():
    rows = [dict(id='warm_' + str(i) + '_' + mode, scene=SCENES[0],
                 section='WARMUP', mode=mode) for i, mode in enumerate(('CONTROL', 'PRICE'), 1)]
    rows += [dict(id='formal_' + str(i) + '_' + mode, scene=scene, section='FORMAL', mode=mode)
             for i, scene in enumerate(SCENES) for mode in ('CONTROL', 'PRICE')]
    return rows


def quote_from_complete_assets(capture, accepted):
    if (accepted.get('full_protocol_accepted') is not True
            or accepted.get('finance', {}).get('finance_accepted') is not True
            or accepted.get('formal_source_time_cells') != 1624):
        raise ValueError('Accepted complete original assets and finance required')
    runs = capture['runner']['runs']
    if len(runs) != 14 or any(r['status'] != 'COMPLETE' for r in runs):
        raise ValueError('This quote requires the actual complete fourteen-path reference')
    missing, extra = 0, 0.
    for row in runs:
        if row['mode'] != 'COLLECT': continue
        if [(p['source'], p['target']) for p in row['interval_cells']] != cells():
            raise ValueError('Do not quote from a favorable source subset')
        for point in row['interval_cells']:
            if point['source'] == point['target'] - 1: continue
            for action in ACTIONS:
                observed = [p['seconds'] for p in point['price_trials'] if p['action'] == action]
                if len(observed) != 2 or any(not math.isfinite(x) or x <= 0 for x in observed):
                    raise ValueError('Warm/formal original timing observations required')
                extra += 2 * max(observed); missing += 2
    if missing != 11340:
        raise ValueError('Every non-nearest cell receives both additional formal rounds')
    native = [r for r in runs if r['mode'] == 'NATIVE']
    if len(native) != 4: raise ValueError('Bind all four reused Native references')
    native_wall = sum(r['ended_unix'] - r['started_unix'] for r in native)
    base = capture['billing']['wall_seconds'] - native_wall
    if not math.isfinite(base) or base <= 0:
        raise ValueError('Invalid whole-card time basis')
    terms = dict(original_GPU_wall_minus_only_reused_Native=base,
        additional_repeats_at_max_same_cell_observed_seconds=extra,
        exclusive_admission_monitor_and_shutdown_reserve=900.)
    forecast = math.ceil(sum(terms.values()) * 1.25) / 3600
    limit = math.ceil(forecast * 1.2 * 4) / 4
    return dict(status='FULL_DOMAIN_PRICE_REFRESH_COMPLETE_PLANNING_QUOTE_NOT_DISPATCH',
        version=VERSION, scope_counts=COUNTS, matrix=matrix(),
        all_cell_rounds=[dict(name=r, actions=list(a)) for r, a in ROUNDS],
        terms_seconds=terms, planning_margin=1.25, limit_margin=1.2,
        forecast_complete_GPUh=forecast, billed_limit_GPUh=limit,
        specific_whole_card_approval_required=limit >= 12,
        cumulative_cap_GPUh=226, extra_readout_trials=missing,
        original_tensor_IO_reduction_credited_seconds=0,
        contention_timings_used_only_for_planning_not_clean_prices=True,
        raw_labels_reused_not_recollected=True, old_max_source_cost_reduction_unchanged=True,
        new_original_parent_and_Native_parity_required=True,
        actual_exclusive_GPU_required=True, production_CPU_accepted=False,
        production_collector_and_lifecycle_integration_pending=True,
        source_frozen_for_dispatch=False, GPU_dispatch_ready=False,
        GPU_submissions=0, ledger_written=False)
