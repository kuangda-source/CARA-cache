"""Complete N10 input/workload preparation without a selected GPU price.

The returned document is deliberately not N10-production-config.json. The
normal production validator must still refuse it until a whole-card quote,
actual production CPU and original GPU admission exist.
"""
from collections import Counter
import copy

from .automatic_quality_models_r1 import ROLE_FOR_DIMENSION, ROLES
from .automatic_quality_production_r1 import PURPOSE, validate, validate_inputs
from .automatic_quality_r1 import DIMENSIONS, sampling_spec


STATUS = 'N10_UNPRICED_COMPLETE160_FULL960_SOURCE_PREPARATION_NOT_PRODUCTION'
RUN = 'wc-paper-n10-accepted160-full960-r1'
SCOPE = dict(generation_positions=160, metric_positions=960, prompt_groups=8,
             seeds=[17, 43], methods=10, new_generation_paths=0)


def build_unpriced(inputs, CPU, CPU_registration, resources, comparisons, *, source_revision, references):
    bundle = inputs['input_bundle']
    config = dict(purpose=PURPOSE, run_id=RUN, input_bundle_fingerprint=bundle['fingerprint'],
        measurement_protocol_sha256=inputs['measurement_protocol_sha256'],
        scorer_fingerprint=bundle['scorer_fingerprint'], methods=copy.deepcopy(bundle['methods']),
        dimensions=list(DIMENSIONS), scope_counts=copy.deepcopy(SCOPE), bootstrap_repetitions=4096,
        comparisons=copy.deepcopy(comparisons), forecast_GPUh=None, billed_limit_GPUh=None,
        cumulative_cap_GPUh=226, budget_origin_used_GPUh=79.99637737158223,
        whole_card_cost_includes_load_warm_scoring_and_release=True,
        generation_latency_claim=False, weighted_quality_total=None, references=copy.deepcopy(references))
    preview = dict(purpose=PURPOSE, source_revision=source_revision)
    validate_inputs(config, preview, inputs, CPU, CPU_registration, resources)
    try:
        validate(config, preview, inputs, CPU, CPU_registration, resources)
    except ValueError as error:
        if 'Whole-card billed scoring price' not in str(error): raise
    else:
        raise ValueError('An unpriced preparation must not pass complete production validation')
    workload = []
    for dimension in DIMENSIONS:
        rows = [r for r in bundle['rows'] if r['dimension'] == dimension]
        counts = dict(Counter(r['input_status'] for r in rows))
        ready = counts.get('READY_TO_SCORE', 0); spec = sampling_spec(dimension)
        workload.append(dict(dimension=dimension, role=ROLE_FOR_DIMENSION[dimension],
            registered_positions=160, original_input_status_counts=counts, ready_video_invocations=ready,
            selected_source_positions_per_ready_video=len(spec['frame_indices']),
            target_positions_per_ready_video=len(spec['target_indices']),
            planned_selected_source_positions=ready*len(spec['frame_indices']),
            planned_target_positions=ready*len(spec['target_indices']),
            sampling_policy=spec['policy'], original_model_entries=1 if ready else 0,
            actual_model_forward_calls=None, actual_GPU_seconds=None))
    if {r['role'] for r in workload if r['ready_video_invocations']} != set(ROLES):
        raise ValueError('Preserve the complete five-role scoring scope, not a cheaper model subset')
    return dict(status=STATUS, unpriced_config_template=config,
        validation_registration_preview=preview, original_input_status_counts=dict(Counter(
            r['input_status'] for r in bundle['rows'])), dimension_workload=workload,
        source_frame_positions_are_not_executed_model_calls=True,
        input_and_complete_model_proof_validated=True, complete_production_validation_refused_for_missing_price=True,
        original_five_model_CPU_runtime_relabelled_as_GPU_price=False,
        extra_warmup_video_paths=0, first_original_video_includes_cold_start=True,
        actual_whole_card_quote_GPUh=None, actual_production_CPU_accepted=False,
        production_config_generated=False, real_quality_scores=0, GPU_submissions=0,
        SSH_queries=0, ledger_written=False)
