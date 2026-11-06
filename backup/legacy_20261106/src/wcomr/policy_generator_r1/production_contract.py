"""Whole PG-P1 scope and conservative planning, independent of partial prices."""
import math
from .continuation_preparation import TIME_BOUNDARY

VERSION='CARA_PG_P1_COMPLETE64_R1'
COUNTS=dict(maximum_paths=64,FIT_endpoint_paths=32,SELECT_endpoint_paths=8,
    Native_reference_paths=6,nonNative_warm_paths=16,Native_warm_paths=2,
    maximum_guided_pairs=2304,maximum_CFG_calls=4608,loads=1,maximum_scored_pairs=40,
    extra_label_collection_paths=0,extra_shadow_pairs=0,information_queries=8)


def matrix():
    rows=[dict(id='native_warm_'+str(i),split='WARM',kind='NATIVE',member_index=0) for i in (1,2)]
    rows += [dict(id='native_fit_'+str(i),split='CAL_FIT',kind='NATIVE',member_index=i) for i in range(4)]
    for q in range(8):
        rows += [dict(id=f'q{q}_warm_{i}',split='WARM',kind='POLICY',query_slot=q,member_index=0) for i in (1,2)]
        rows += [dict(id=f'q{q}_fit_{i}',split='CAL_FIT',kind='POLICY',query_slot=q,member_index=i) for i in range(4)]
    rows += [dict(id='native_select_'+str(i),split='CAL_SELECT',kind='NATIVE',member_index=i) for i in range(2)]
    rows += [dict(id=f'select_{q}_{i}',split='CAL_SELECT',kind='POLICY',selection_slot=q,member_index=i) for q in range(4) for i in range(2)]
    assert len(rows)==64
    return rows


def complete_quote(bank):
    rows=bank['runner']['runs']
    if len(rows)!=24 or any(r['status']!='COMPLETE' for r in rows):raise ValueError('Whole accepted BANK24 required')
    duration=max(r['ended_unix']-r['started_unix'] for r in rows)
    load=bank['runner']['load_seconds']
    if not 0<duration<3600 or not 0<load<3600:raise ValueError('Invalid whole request planning clock')
    # Every possible path is charged at the maximum observed complete Native/
    # policy request; no expected .8 speedup or physical dedup credit is taken.
    terms=dict(model_load=load,all64_full_paths=64*duration,CPU_graph_and_one_refinement=1200.,
        complete40_pairs_93frame_CPU_LPIPS=2400.,raw_copy_hash_reference_validation=1200.,
        exclusive_admission_monitor_shutdown=900.)
    forecast=math.ceil(sum(terms.values())*1.25)/3600
    limit=math.ceil(forecast*1.15*2)/2
    return dict(status='COMPLETE_PG_P1_PLANNING_QUOTE_PENDING_PRICE_AND_CPU_BINDINGS',version=VERSION,
        scope_counts=COUNTS,matrix=matrix(),terms_seconds=terms,planning_margin=1.25,limit_margin=1.15,
        forecast_complete_GPUh=forecast,billed_limit_GPUh=limit,
        specific_whole_card_approval_required=limit>=12,cumulative_cap_GPUh=226,
        complete_request_boundary=TIME_BOUNDARY,old_timings_only_for_conservative_planning=True,
        deployment_B_seconds=None,clean_action_prices_used=False,physical_dedup_credit_seconds=0,
        price_refresh_budget_reused=False,minimum_free_disk_bytes=30*2**30,
        minimum_MemAvailable_bytes=24*2**30,training=False,GPU_dispatch_ready=False)
