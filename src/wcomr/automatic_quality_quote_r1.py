"""Whole N10 engineering budget; assumptions are not measured GPU throughput."""
import math

from .automatic_quality_r1 import DIMENSIONS, fingerprint

VERSION='N10_FULL960_STATIC_WORKLOAD_ENGINEERING_ALLOWANCES_R1'
ALLOWANCE_SECONDS=dict(subject_consistency=15., motion_smoothness=30.,
    overall_consistency=15., dynamic_degree=30., MUSIQ_LONGER512=15.)


def quote(scope):
    if (scope['status']!='N10_UNPRICED_COMPLETE160_FULL960_SOURCE_PREPARATION_NOT_PRODUCTION'
            or scope['original_input_status_counts']!={'READY_TO_SCORE':645,'VIDEO_UNAVAILABLE':155,'NOT_APPLICABLE_STATIC_SCOPE':160}
            or scope['actual_whole_card_quote_GPUh'] is not None or scope['real_quality_scores']!=0
            or scope['actual_production_CPU_accepted'] or scope['production_config_generated']):
        raise ValueError('The unchanged complete unpriced actual160/960 input preparation is required')
    rows=scope['dimension_workload']
    if [r['dimension'] for r in rows]!=list(DIMENSIONS):
        raise ValueError('All original six dimensions, including inapplicable static scope, must remain')
    positions=[]
    for row in rows:
        dim=row['dimension'];ready=row['ready_video_invocations'];active=dim in ALLOWANCE_SECONDS
        if ready!=(129 if active else 0) or row['registered_positions']!=160 or row['original_model_entries']!=int(active):
            raise ValueError('Price every original valid video and all five model contexts')
        per_video=ALLOWANCE_SECONDS.get(dim,0.)
        positions.append(dict(dimension=dim,model_role=row['role'],registered_positions=160,
            ready_video_metric_invocations=ready,model_contexts=int(active),
            planned_model_load_and_validation_seconds=120. if active else 0.,
            planned_per_video_allowance_seconds=per_video,
            planned_video_scoring_seconds=ready*per_video,
            observed_GPU_seconds=None))
    before=sum(p['planned_model_load_and_validation_seconds']+p['planned_video_scoring_seconds'] for p in positions)+600.
    seconds=math.ceil(before*1.2);forecast=seconds/3600
    return dict(status='N10_WHOLE960_ENGINEERING_GPU_BUDGET_NOT_MEASURED_MODEL_PRICE',pricing_version=VERSION,
        input_bundle_fingerprint=scope['unpriced_config_template']['input_bundle_fingerprint'],
        scorer_fingerprint=scope['unpriced_config_template']['scorer_fingerprint'],
        scope_counts=scope['unpriced_config_template']['scope_counts'],positions=positions,
        total_ready_video_metric_invocations=645,total_registered_metric_positions=960,
        full_model_contexts=5,extra_warmup_paths=0,first_video_cold_start_in_scoring=True,
        aggregate_failure_recording_and_release_allowance_seconds=600.,whole_card_margin=1.2,
        before_margin_seconds=before,forecast_GPUh=forecast,
        billed_limit_GPUh=math.ceil(forecast*1.25*4)/4,
        assumption_scope='All source verification, official decoding/preprocessing, inference, observation and per-row journal inside each allowance; fixed context load and final whole-card work added.',
        engineering_allowances_not_empirical_throughput=True,CPU_wall_used_as_GPU_rate=False,
        measured_GPU_model_rates=None,runtime_upper_bound_guarantee=False,
        generation_latency_claim=False,new_quality_scores=0,
        complete_card_selection_requires_actual_production_CPU=True)


def validate_selected(config, scope, cost):
    expected=quote(scope)
    if (cost!=expected or any(config[k]!=cost[k] for k in ('forecast_GPUh','billed_limit_GPUh'))
            or config['input_bundle_fingerprint']!=cost['input_bundle_fingerprint']
            or config['scope_counts']!=cost['scope_counts'] or config['scorer_fingerprint']!=cost['scorer_fingerprint']
            or config.get('engineering_cost_policy')!=VERSION
            or config['cumulative_cap_GPUh']!=226 or config['budget_origin_used_GPUh']!=79.99637737158223):
        raise ValueError('The entire original960 engineering quote and cumulative window must recompute exactly')
    return fingerprint(cost)
