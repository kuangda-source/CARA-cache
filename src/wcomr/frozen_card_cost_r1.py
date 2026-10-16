"""Observed whole-request planning costs; no workpoint choice or GPU admission."""
from collections import Counter
import math

from .balanced_repeat_timing_r1 import SLOTS, matrix as repeat_matrix
from .frozen_input_selection_r1 import KNOWN_METHODS
from .gpu_budget_pool_v2 import BudgetPool

CAP = 104.97136333301378
ORIGIN = 79.99637737158223
MARGIN = .20
FULL_WARM_TRACE_HEADROOM_SECONDS = 60.
ADDITIONAL_CARD_SETUP_HEADROOM_SECONDS = 300.
REPEAT_COUNTS = dict(requests=2,methods=5,scientific_paths=30,full_warmup_paths=10,
    total_paths=40,ordinary_pairs=1440,CFG_calls=2880,loads=1,teacher_pairs=0)


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def source_costs(value, accepted, *, capture_sha256, kind):
    statuses = dict(N05=('N05_CORE66_INDEPENDENTLY_ACCEPTED', 'N05_CORE66_ACCEPTED_WITH_REJECTIONS_RETAINED'),
        N06=('SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED', 'SIMPLE26D_FULL36_TERMINAL_WITH_REJECTIONS_RETAINED'))
    full, formal = (66, 44) if kind == 'N05' else (36, 24)
    if (kind not in statuses or accepted['status'] not in statuses[kind]
            or accepted['capture_sha256'] != capture_sha256
            or [accepted['full_denominator'], accepted['formal_denominator']] != [full, formal]):
        raise ValueError('Original complete independently accepted source card and capture SHA required')
    runner, bill, launch = value['runner'], value['billing'], value['launch']
    rows = runner['runs']; plan = runner['matrix']
    if (len(rows) != full or len(plan) != full or len({r['id'] for r in rows}) != full
            or [r['id'] for r in rows] != [r['id'] for r in plan]
            or sum(r['section'] == 'TIMED' for r in rows) != formal
            or any(r['status'] not in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED') for r in rows)
            or runner['source_revision'] != launch['source_revision']
            or bill['source_revision'] != launch['source_revision']
            or not positive(bill['wall_seconds']) or not positive(runner['load_seconds'])
            or not math.isclose(bill['wall_seconds']/3600, bill['actual_GPUh'], rel_tol=1e-11)
            or not math.isclose(bill['actual_GPUh'], accepted['actual_GPUh'], rel_tol=1e-11)):
        raise ValueError('All original requests, actual resident load and original whole GPU bill required')
    durations = []; groups = {}
    for row in rows:
        seconds = row['ended_unix'] - row['started_unix']
        if not positive(seconds): raise ValueError('Finite positive complete-request wall intervals required')
        durations.append(seconds)
        group = groups.setdefault(row['method'], dict(complete=[], formal=[], warm=[], rejected=0))
        if row['status'] != 'COMPLETE':
            group['rejected'] += 1
            continue  # A fast guard rejection cannot estimate full successful inference.
        if not positive(row['core_seconds']) or seconds + .1 < row['core_seconds']:
            raise ValueError('Whole request must include its measured inference core')
        group['complete'].append(seconds)
        group['formal' if row['section'] == 'TIMED' else 'warm'].append(seconds)
    residual = bill['wall_seconds'] - runner['load_seconds'] - sum(durations)
    if residual < -1.:
        raise ValueError('Load plus request intervals exceed the whole bill; inspect original clocks')
    methods = {m: dict(complete_observations=len(g['complete']), rejected_observations=g['rejected'],
        max_complete_request_seconds=max(g['complete']) if g['complete'] else None,
        max_formal_request_seconds=max(g['formal']) if g['formal'] else None,
        max_warm_request_seconds=max(g['warm']) if g['warm'] else None) for m,g in groups.items()}
    pool = value['pool']
    if (pool['cap_gpu_hours'] != CAP or pool['origin_used_gpu_hours'] != ORIGIN
            or any(not math.isclose(pool[k], v, rel_tol=1e-11, abs_tol=1e-12)
                   for k,v in BudgetPool.accounting(pool).items())):
        raise ValueError('Do not reset the original cumulative budget window')
    return dict(source_kind=kind, source_revision=launch['source_revision'], source_capture_sha256=capture_sha256,
        original_paths=full, actual_GPUh=bill['actual_GPUh'], billed_wall_seconds=bill['wall_seconds'],
        load_seconds=runner['load_seconds'], sum_request_wall_seconds=sum(durations),
        original_unattributed_seconds=residual, planning_residual_seconds=max(0.,residual),
        residual_per_path_seconds=max(0.,residual)/full, methods=methods,
        snapshot_observed_unix=value['observed_unix'], original_v2_available_GPUh=pool['available_gpu_hours'],
        timing_use='HISTORICAL_WHOLE_COST_PLANNING_ONLY_NOT_CLEAN_LATENCY_OR_CAUSAL_COMPONENT_COST')


def estimate(plan, counts, sources):
    if len(plan) != counts['total_paths'] or sum(r['section']=='TIMED' for r in plan) != counts['scientific_paths']:
        raise ValueError('Price the complete original planned matrix, never a smaller prefix')
    requested = Counter((r['method'],r['section']) for r in plan)
    records = {}
    for source in sources:
        for method, record in source['methods'].items():
            if method in records: raise ValueError('Do not silently splice duplicate method cost sources')
            records[method] = record
    native = records.get('NATIVE35',{}).get('max_complete_request_seconds')
    if not positive(native):
        return dict(status='WHOLE_COST_EVIDENCE_MISSING_NATIVE_COMPLETE_REQUEST', scope_counts=counts,
                    forecast_complete_GPUh=None, billed_limit_GPUh=None, GPU_submissions=0)
    components = []; total_requests = 0.; fallback = set()
    for (method,section), number in sorted(requested.items()):
        if method not in KNOWN_METHODS or section not in ('WARMUP','TIMED'):
            raise ValueError('Only the original finite execution points and full warm/formal sections are supported')
        record = records.get(method,{})
        key = 'max_warm_request_seconds' if section=='WARMUP' else 'max_formal_request_seconds'
        observed = record.get(key) or record.get('max_complete_request_seconds')
        proxy = observed is None
        if proxy:
            observed = native + 60.; fallback.add(method)
        warm_allowance = FULL_WARM_TRACE_HEADROOM_SECONDS if section=='WARMUP' else 0.
        subtotal = number * (observed + warm_allowance); total_requests += subtotal
        components.append(dict(method=method,section=section,paths=number,
            observed_max_complete_request_seconds=None if proxy else observed,
            planning_per_request_seconds=observed+warm_allowance,
            full_warm_trace_headroom_seconds=warm_allowance,
            source_or_proxy='NATIVE35_MAX_PLUS60_EXPLICIT_PLANNING_PROXY' if proxy else 'OBSERVED_COMPLETE_REQUEST_MAX',
            projected_seconds=subtotal))
    load = max(s['load_seconds'] for s in sources)
    residual = max(s['residual_per_path_seconds'] for s in sources)*len(plan)
    before_margin = load + total_requests + residual + ADDITIONAL_CARD_SETUP_HEADROOM_SECONDS
    forecast = math.ceil(before_margin*(1+MARGIN))/3600
    return dict(status='COMPLETE_CARD_OBSERVED_REQUEST_COST_FORECAST_NOT_ADMISSION', scope_counts=counts,
        complete_plan_positions=len(plan), components=components, one_resident_load_seconds=load,
        projected_complete_requests_seconds=total_requests, projected_uncategorized_seconds=residual,
        additional_card_setup_headroom_seconds=ADDITIONAL_CARD_SETUP_HEADROOM_SECONDS,
        planning_margin_fraction=MARGIN, projected_seconds_before_margin=before_margin,
        forecast_complete_GPUh=forecast, billed_limit_GPUh=forecast,
        explicit_proxy_methods=sorted(fallback), runtime_upper_bound_guarantee=False,
        active_job_reservation_written=False, specific_card_approval_required_by_estimate=forecast>=12,
        source_CPU_or_resource_acceptance_not_replaced_by_forecast=True, GPU_submissions=0)


def preview(shared_bound, method_freeze, sources):
    methods = shared_bound['method_ids']; counts = shared_bound['planned_scope_counts']
    if (method_freeze['method_ids'] != methods or len(methods)!=len(set(methods)) or len(methods)!=10
            or method_freeze['parameters_frozen_from']!='DEVELOPMENT_ONLY'
            or method_freeze['final_test_outputs_seen'] is not False
            or counts['total_paths']!=180 or counts['scientific_paths']!=160
            or counts['full_warmup_paths']!=20 or counts['loads']!=1 or counts['teacher_pairs']!=0):
        raise ValueError('Keep the original whole180 development-frozen common test')
    expected = {(m,s):n for m in methods for s,n in [('TIMED',16),('WARMUP',2)]}
    if Counter((r['method'],r['section']) for r in shared_bound['execution_plan']) != expected:
        raise ValueError('Every frozen common method retains all16 formal and2 warm paths')
    first = estimate(shared_bound['execution_plan'],counts,sources)
    bindings = method_freeze['repeat_timing_bindings']
    if (set(bindings)!=set(SLOTS) or len(set(bindings.values()))!=5
            or not set(bindings.values()).issubset(methods)
            or bindings['FULL_NATIVE']!='NATIVE35' or not bindings['WORLD_CACHE'].startswith('WC_')
            or not bindings['RA_CFG_CACHE'].startswith('RA_')
            or bindings['GCR_EFFICIENT']!='A_NO_P' or bindings['CPA_HIGH_FIDELITY']!='TABLE_PHASE_H1'):
        raise ValueError('Price the same original five timing roles frozen with the common test')
    repeat = [dict(r,method=bindings[r['slot']]) for r in repeat_matrix()]
    second = estimate(repeat,REPEAT_COUNTS.copy(),sources)
    available = next(s['original_v2_available_GPUh'] for s in sources if s['source_kind']=='N05')
    a,b = first['forecast_complete_GPUh'],second['forecast_complete_GPUh']
    joint = a+b if a is not None and b is not None else None
    return dict(status='N07_N08_COMPLETE_SCOPE_COST_PREVIEW_NOT_SELECTED_OR_ADMITTED',
        N07=first,N08=second,combined_estimate_GPUh=joint,
        N05_capture_budget_snapshot_available_GPUh=available,
        additional_budget_needed_for_both_at_snapshot_GPUh=max(0.,joint-available) if joint is not None else None,
        cumulative_cap_GPUh=CAP,budget_origin_used_GPUh=ORIGIN,sources=sources,
        final_method_or_input_selection_made_by_estimator=False,
        fresh_CPU_scope_authority_and_UUID_budget_checks_still_required=True,
        forecasts_not_core_latency_speedups_or_action_prices=True,
        GPU_submissions=0,SSH_queries=0,server_ledger_written=False)
