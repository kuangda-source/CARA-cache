"""Whole P2 cost envelope: all comparisons and preparation, no split dispatch."""
import math
from .continuation_preparation import TIME_BOUNDARY,require

ROLES=('CARA','FRONT_C','FRONT_A','REFRESH_C','REFRESH_A','PURE_PROXY','SAME_Q_SIMPLE','NATIVE35','SHORT_NATIVE_LOW','SHORT_NATIVE_HIGH')
COUNTS=dict(Native_timing_paths=84,history_paths=6,history_extra_D_pairs=36,history_paired_readouts=108,
 same_Q_complete_calibration_paths=64,fixed_control_CAL_paths=24,new_DEV_prompts=16,new_DEV_seeds=2,
 new_DEV_role_upper=10,new_DEV_formal_paths=320,new_DEV_warm_paths=20,
 maximum_paths=518,maximum_ordinary_guided_pairs=18648,maximum_guided_pairs_with_shadow=18684,maximum_CFG_calls=37368,
 LPIPS_pairs_upper=346,quality_positions_upper=1600,generation_loads=1,quality_model_loads_upper=5)


def complete_quote(bank,metrics):
    rows=bank['runner']['runs'];require(len(rows)==24 and all(r['status']=='COMPLETE' for r in rows),'Accepted whole BANK24 planning evidence required')
    duration=max(r['ended_unix']-r['started_unix'] for r in rows);load=bank['runner']['load_seconds']
    require(0<duration<3600 and 0<load<3600,'Finite full request planning clock required')
    dimensions=('subject_consistency','motion_smoothness','overall_consistency','dynamic_degree','MUSIQ_LONGER512')
    require(metrics['full_protocol_accepted'] is True,'Accepted quality planning evidence required')
    costs={d:max(r['metric_wall_seconds'] for r in metrics['rows'] if r['dimension']==d and r['status']=='SCORED') for d in dimensions}
    terms=dict(generation_model_load=load,all518_guarded_complete_requests=518*duration,
        shadow36_full_D_pairs=36*duration/36,history108_paired_readouts=108*duration/36,
        history_state_hash_copy_and_branch_export_allowance=1800.,
        complete346_93frame_CPU_LPIPS_allowance=346*60.,
        five_dimensions_all320_videos=320*sum(costs.values()),
        five_metric_load_and_warm_allowance=1800.,CPU_proposals_and_simple_search=1200.,
        artifact_decode_hash_raw_copy=3600.,exclusive_admission_monitor_shutdown=1200.)
    forecast=math.ceil(sum(terms.values())*1.25)/3600;limit=math.ceil(forecast*1.15*2)/2
    aux=dict(model_load=load,all90_requests=90*duration,shadow36_D=duration,readouts108=3*duration,
             state_hash_copy_export=1800.,artifact_validation=1200.,exclusive_shutdown=900.)
    auxiliary=math.ceil(sum(aux.values())*1.25)/3600
    return dict(status='WHOLE_P2_NO_DEDUP_PLANNING_ENVELOPE_PENDING_ACCEPTED_P1_BINDINGS',version='CARA_PG_P2_WHOLE518_R1',
        scope_counts=COUNTS,roles=list(ROLES),terms_seconds=terms,metric_per_video_planning_max_seconds=costs,
        forecast_complete_GPUh=forecast,billed_limit_GPUh=limit,planning_margin=1.25,limit_margin=1.15,
        auxiliary90_included_not_separate_authorization=dict(terms_seconds=aux,forecast_GPUh=auxiliary,billed_limit_GPUh=math.ceil(auxiliary*1.15*2)/2),
        clean_action_price_used_for_forecast=False,planning_clocks_not_latency_results=True,
        timing_boundary=TIME_BOUNDARY,physical_dedup_credit_seconds=0,old_P1_budget_reused=False,
        same_Q_calibration_count_basis='8_NATIVE_REFERENCE_WARM+8_QUERIES*(2_WARM+4_FIT)+4_SELECT_FINALISTS*2_SELECT',
        fixed_control_count_basis='3_FIXED_PLANS*(2_WARM+4_FIT+2_SELECT)',
        LPIPS_count_basis='40_SIMPLE_CAL+18_FIXED_CAL+9_NONREFERENCE_ROLES*32_NEW_INPUTS',
        new_DEV_count_is_design_target=True,new_DEV_identity_selected=False,
        no_extra_quality_search=True,query_limit_simple=8,training=False,
        pending_bindings=['P1_independent_terminal_and_final_policy','legal_compiled_control_fingerprints_and_aliases',
          'all_registered_input_source_groups_and_seeds','Native_timing_choice_before_new_DEV_quality',
          'P2_whole_lifecycle_metric_CPU_and_resource_acceptance','fresh_ledger_and_complete_card_approval'],
        specific_whole_card_approval_required=limit>=12,cumulative_cap_GPUh=226,
        GPU_submissions=0,GPU_dispatch_ready=False)
