"""Price the complete frozen N09 diagnostic from original successful requests.

Trace/profile headroom is a declared planning allowance, not measured operator
overhead. This pure metadata module imports no model and admits no GPU work.
"""
from collections import Counter
import copy
import math

from .balanced_repeat_timing_r1 import matrix, SLOTS, SCENES
from .frozen_card_cost_r1 import (
    ADDITIONAL_CARD_SETUP_HEADROOM_SECONDS, FULL_WARM_TRACE_HEADROOM_SECONDS,
    MARGIN, ORIGIN, positive,
)

PROFILE_HEADROOM_SECONDS=30.
BINDINGS=dict(FULL_NATIVE='NATIVE35',WORLD_CACHE='WC_HALF',RA_CFG_CACHE='RA_DEFAULT',
              GCR_EFFICIENT='A_NO_P',CPA_HIGH_FIDELITY='TABLE_PHASE_H1')
MODES=('ORIGINAL_AUDIT_WARMUP','ORIGINAL_AUDIT','PROFILE_AUDIT','PROFILE_LEAN')


def registered_plan(scope,protocol,freeze):
    expected=[]
    for row in matrix():
        expected.append(dict(row,id='n09_runtime_'+row['id'],method=BINDINGS[row['slot']],
            section='WARMUP' if row['round']==0 else 'PROFILE_CONTROL',mode=MODES[row['round']],
            audit_guided=row['round']!=3,component_profile=row['round'] in (2,3),actual_solver_updates=36))
    if (scope['status']!='N09_RUNTIME_FULL40_SCOPE_PREREGISTERED_NOT_PRODUCTION_OR_GPU_CARD'
            or scope['complete_matrix']!=expected or scope['method_bindings']!=BINDINGS
            or scope['requests']!=protocol['requests'] or len(scope['requests'])!=2
            or [r['name'] for r in scope['requests']]!=list(SCENES)
            or freeze['repeat_timing_bindings']!=BINDINGS or set(BINDINGS)!=set(SLOTS)
            or freeze['parameters_frozen_from']!='DEVELOPMENT_ONLY' or freeze['final_test_outputs_seen']
            or not set(BINDINGS.values()).issubset(freeze['method_ids'])
            or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
                or r['resolution']!='432,768' or r['guidance']!=7 for r in scope['requests'])):
        raise ValueError('Price exactly the old frozen five roles, full40 modes and original requests')
    counts=scope['scope_counts']
    required=dict(total_paths=40,full_warmup_paths=10,formal_profile_control_paths=30,
        ordinary_pairs=1440,ordinary_CFG_calls=2880,profiled_paths=20,loads=1,online_teacher_pairs=0)
    if any(counts.get(k)!=v for k,v in required.items()):
        raise ValueError('Complete diagnostic, full warmups and all1440 update pairs required')
    return expected


def estimate(scope,protocol,freeze,sources):
    plan=registered_plan(scope,protocol,freeze);records={}
    if not sources:raise ValueError('Accepted original source cost records required')
    for source in sources:
        if (not positive(source['load_seconds']) or source['residual_per_path_seconds']<0
                or not math.isfinite(source['residual_per_path_seconds'])):
            raise ValueError('Actual original model load and whole-bill remainder required')
        for method,record in source['methods'].items():
            if method in records:raise ValueError('Do not splice duplicate method cost sources')
            records[method]=record
    native=records.get('NATIVE35',{}).get('max_complete_request_seconds')
    if not positive(native):
        return dict(status='N09_COMPLETE40_COST_UNKNOWN_NO_SUCCESSFUL_NATIVE_REQUEST',
            scope_counts=copy.deepcopy(scope['scope_counts']),complete_plan_positions=40,
            forecast_complete_GPUh=None,billed_limit_GPUh=None,whole_card_selected=False,GPU_submissions=0)
    rows=[];fallback=set()
    for planned in plan:
        method=planned['method'];record=records.get(method,{})
        preferred='max_warm_request_seconds' if planned['audit_guided'] else 'max_formal_request_seconds'
        observed=record.get(preferred);field=preferred
        if observed is None:observed=record.get('max_complete_request_seconds');field='max_complete_request_seconds'
        proxy=observed is None
        if proxy:
            observed=native+60.;fallback.add(method);field=None
        if not positive(observed):raise ValueError('Successful complete request prices cannot be zero or nonfinite')
        trace=FULL_WARM_TRACE_HEADROOM_SECONDS if planned['audit_guided'] else 0.
        profile=PROFILE_HEADROOM_SECONDS if planned['component_profile'] else 0.
        rows.append(dict(planned,observed_successful_request_max_seconds=None if proxy else observed,
            observed_source_field=field,
            source_or_proxy='NATIVE35_MAX_PLUS60_EXPLICIT_PLANNING_PROXY' if proxy else 'OBSERVED_SUCCESSFUL_WHOLE_REQUEST',
            trace_planning_headroom_seconds=trace,component_profile_planning_headroom_seconds=profile,
            planned_complete_request_seconds=observed+trace+profile))
    request_seconds=sum(r['planned_complete_request_seconds'] for r in rows)
    load=max(s['load_seconds'] for s in sources)
    residual=max(s['residual_per_path_seconds'] for s in sources)*len(rows)
    before=load+request_seconds+residual+ADDITIONAL_CARD_SETUP_HEADROOM_SECONDS
    forecast=math.ceil(before*(1+MARGIN))/3600
    return dict(status='N09_FULL40_OBSERVED_WHOLE_REQUEST_COST_PREVIEW_NOT_SELECTED_OR_ADMITTED',
        scope_counts=copy.deepcopy(scope['scope_counts']),complete_plan_positions=len(rows),positions=rows,
        actual_mode_counts=dict(Counter(r['mode'] for r in rows)),one_resident_load_seconds=load,
        projected_complete_requests_seconds=request_seconds,projected_uncategorized_seconds=residual,
        trace_planning_headroom_total_seconds=sum(r['trace_planning_headroom_seconds'] for r in rows),
        component_profile_planning_headroom_total_seconds=sum(r['component_profile_planning_headroom_seconds'] for r in rows),
        additional_card_setup_headroom_seconds=ADDITIONAL_CARD_SETUP_HEADROOM_SECONDS,
        planning_margin_fraction=MARGIN,projected_seconds_before_margin=before,
        forecast_complete_GPUh=forecast,billed_limit_GPUh=forecast,explicit_proxy_methods=sorted(fallback),
        component_observer_cost_measured=False,trace_headroom_is_measured_overhead=False,
        runtime_upper_bound_guarantee=False,specific_card_confirmation_required_by_forecast=forecast>=12,
        budget_origin_used_GPUh=ORIGIN,current_pool_cap_or_balance_queried=False,
        fresh_v2_budget_CPU_and_UUID_admission_still_required=True,active_job_reservation_written=False,
        whole_card_selected=False,generation_latency_or_action_price_claim=False,
        minimal_calibration_collection_cost_measured=False,sources=copy.deepcopy(sources),GPU_submissions=0,
        SSH_queries=0,server_ledger_written=False)
