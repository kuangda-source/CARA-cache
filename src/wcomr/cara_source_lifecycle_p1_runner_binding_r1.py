"""Prospective P1 production entry binding; no dispatch, reservation or authority."""
import math
from pathlib import Path
import re

from .cara_budget_host_policy_r1 import POLICY, POLICY_SHA256, bound_policy
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_p1_plan_r1 import validate as validate_card, build
from .cara_source_lifecycle_p1_service_r1 import CARD, PRECISION, KIND
from .cara_source_lifecycle_fit_broker_r1 import verify_source as verify_broker_source, paths
from .cara_s_endpoint_lifecycle_r1 import IDENTITY, JOB_IDENTITY

SOURCE = 'src/wcomr/cara_source_lifecycle_p1_runner_binding_r1.py'
RUNNER = 'scripts/run_cara_source_lifecycle_p1_r1.py'
PROFILE = 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_CONTAINER_PROFILE_R1.json'
PARENT = 'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'
DESIGN = 'plans/cara_next_stage_20261101/source_lifecycle/V1_CALIBRATION64_DESIGN_R1.json'
WEIGHTS = 'reports/cara_v1_frozen_UniPC_current_input_scale_r1_20261102.json'
MODE = 'manifests/wc_h0_eval_mode_contract_20261003.json'
SETUP = 'configs/f1_setup.json'
GEOMETRY = 'configs/wc_ra_comparison_production_r2_20261010.json'
RUNTIME_ENTRY = 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_RUNTIME_ENTRY_R1.json'
IMAGE = 'sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
GPU = 'GPU-cebf7119-cf03-23b9-e192-cd196332b704'
RUN_ID = 'cara-source-lifecycle-V1-P1-full146-r1-20261102'
STAGE_NAME = 'cara-source-lifecycle-V1-P1-GPU-a6000-full146-r1-20261102'
REQUIRED = (SOURCE, RUNNER, PROFILE, CARD, PARENT, DESIGN, WEIGHTS, MODE, SETUP, GEOMETRY, PRECISION, POLICY,RUNTIME_ENTRY,
    'src/wcomr/cara_source_lifecycle_p1_artifacts_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_inventory_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_scores_r1.py',
    'scripts/score_cara_source_lifecycle_p1_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_runner_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_requests_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_collection_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_plan_r1.py',
    'src/wcomr/cara_source_lifecycle_scalar_collection_r1.py',
    'src/wcomr/cara_source_lifecycle_design_r1.py',
    'src/wcomr/cara_source_lifecycle_estimation_r1.py',
    'src/wcomr/cara_source_lifecycle_planner_r1.py',
    'src/wcomr/cara_source_lifecycle_search_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_clock_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_service_r1.py',
    'src/wcomr/cara_source_lifecycle_fit_broker_r1.py',
    'src/wcomr/cara_source_lifecycle_fit_scores_r1.py',
    'scripts/cara_source_lifecycle_fit_broker_r1.py',
    'scripts/score_cara_source_lifecycle_fit_r1.py',
    'scripts/run_cara_budget_calibration_r1.py',
    'src/wcomr/cara_budget_host_policy_r1.py',
    'src/wcomr/cara_s_endpoint_host_guardian_r1.py',
    'src/wcomr/cara_s_endpoint_supervisor_r1.py',
    'src/wcomr/cara_s_endpoint_guardian_journal_r1.py',
    'src/wcomr/cara_s_endpoint_lifecycle_r1.py',
    'src/wcomr/cara_s_endpoint_lifecycle_capture_r1.py',
    'scripts/cara_budget_process_bootstrap_r1.py',
    'src/wcomr/cara_fast_fidelity_r1.py',
    'src/wcomr/cpu_owned_state_snapshot.py', 'src/wcomr/cara_read_write_suffix_r1.py',
    'src/wcomr/full_sampling.py', 'src/wcomr/h0_mode.py', 'src/wcomr/runtime_config.py',
    'src/wcomr/paper_latency_r1.py', 'src/wcomr/prepared_input.py',
    'src/wcomr/clean_speed20_r1.py', 'src/wcomr/policy_generator_r1/production_sampling.py',
    'src/wcomr/policy_generator_r1/p2_native_sampling.py')


def validate_profile(profile, scope):
    hard = profile['hard_GPUh']
    if (profile['schema'] != 'CARA_V1_P1_CONTAINER_PROFILE_R1' or profile['scope_sha256'] != scope
            or profile['run_id'] != RUN_ID or profile['semantic_positions'] != 146
            or profile['physical_generation_upper'] != 142 or profile['physical_model_pairs_upper'] != 5176
            or profile['internal_FIT_queries_upper'] != 42 or profile['internal_FIT_metric_pairs_upper'] != 84
            or profile['postrelease_new_metric_pairs_upper'] != 32
            or type(hard) not in (int, float) or not math.isfinite(hard) or hard <= 4
            or profile['stop_release_reserve_seconds'] != 600 or profile['temperature_stop_C'] != 90
            or profile['GPU_container'] != dict(image=IMAGE, cpus=2, memory_GiB=40, memory_swap_GiB=40,
                pid_namespace='host', network='none', readonly_rootfs=True,
                supervisor_CUDA_visible=False, only_exact_runner_CUDA_visible=True)
            or profile['hosts'] != {'two_card':dict(capability=[8,6], cpuset_cpus='24,25', minimum_MemAvailable_GiB=52)}
            or profile['internal_CPU'] != dict(cpus=2, cpuset_cpus='26,27', memory_GiB=8,
                memory_swap_GiB=8, network='none', readonly_rootfs=True, GPU_visible=False, wall_seconds=600)
            or profile['snapshot_limits'] != dict(logical_copy_bytes=48*2**30, total_CPU_images_bytes=16*2**30)):
        raise ValueError('Exact full146/142 P1 two-card resource profile and separately frozen hard limit required')
    limits = profile['storage']
    if (limits['output_image_bytes'] != 64*2**30 or limits['independent_journal_bytes'] != 48*2**20
            or limits['minimum_output_free_bytes'] != 8*2**30 or limits['minimum_host_free_bytes'] != 16*2**30
            or limits['minimum_host_free_before_provision_bytes'] != 80*2**30
            or limits['minimum_free_inodes'] != 8192):
        raise ValueError('Exact private64GiB output, independent48MiB journal and whole-card low-water bounds required')


def validate_inputs(project, stage):
    project, stage = Path(project), Path(stage)
    authority, registration = read_record(stage/'GPU-authorization.json'), read_record(stage/'registration.json')
    if (not project.is_absolute() or stage.parent != project/'.sync' or stage.name != STAGE_NAME
            or authority['stage'] != str(stage) or authority['run_id'] != RUN_ID
            or not re.fullmatch('[0-9a-f]{40}', authority['source_revision'])
            or not re.fullmatch('[0-9a-f]{32}', authority['launch_id'])
            or authority['CPU_fixture_only'] is not False or authority['execution_authorized'] is not True
            or authority['authorizes_replay'] is not False or authority['card_kind'] != KIND
            or authority['authorization_basis'] != 'DIRECT_USER_SINGLE_CARD' or not authority['user_quote']
            or authority['host'] != 'two_card' or authority['gpu_uuid'] != GPU
            or any(registration[k] != authority[k] for k in ('stage','host','source_revision'))):
        raise ValueError('Separate direct-user single P1 authority and original two-card identity required')
    payload, runtime = registration['payload_sha256'], registration['runtime_source_sha256']
    if (not set(REQUIRED) <= set(payload) or payload[SOURCE] != file_sha(__file__)
            or any(Path(n).is_absolute() or '..' in Path(n).parts or file_sha(stage/n) != h for n,h in payload.items())
            or not runtime or any(Path(n).is_absolute() or '..' in Path(n).parts
                                  or file_sha(project/'runtime'/n) != h for n,h in runtime.items())):
        raise ValueError('Complete registered P1 source/runtime closure differs')
    bound_policy(stage, registration, authority)
    extra=read_record(stage/RUNTIME_ENTRY)['files']
    if (extra!={'packages/cosmos-oss/cosmos_oss/init.py':'0328ceaed0b94dbdeeb5ee5d7092657b85c492c9927efcf282630bdd4d303539'}
            or any(file_sha(project/'runtime'/n)!=h for n,h in extra.items())):
        raise ValueError('Original supplemental Cosmos output-initialization source differs')
    card, profile = read_record(stage/CARD), read_record(stage/PROFILE)
    validate_card(card)
    if card != build(read_record(stage/PARENT), read_record(stage/DESIGN)):
        raise ValueError('Original whole146 science and fixed64 design differ')
    validate_profile(profile, card['scope_sha256'])
    if (authority['scope_sha256'] != card['scope_sha256']
            or authority['billed_limit_GPUh'] != profile['hard_GPUh']
            or authority['semantic_positions'] != 146 or authority['physical_generation_upper'] != 142
            or registration['container_image'] != IMAGE):
        raise ValueError('Original whole P1 scope, hard limit or pinned image differs')
    proof = read_record(stage/'execution-CPU-proof.json')
    fields = ('complete_algorithm_reused_source_bound', 'actual_host_FIT_broker_reused_source_bound',
              'guardian_FIT_cleanup_reused_source_bound', 'production_total_entry_CPU_accepted',
              'released_full146_reader_and_new32_scores_CPU_accepted')
    if (authority['CPU_proof_sha256'] != file_sha(stage/'execution-CPU-proof.json')
            or proof['schema'] != 'CARA_V1_P1_WHOLE_CPU_COMPOSED_R1'
            or proof['whole_card_CPU_accepted'] is not True or proof['host'] != 'two_card'
            or proof['scope_sha256'] != card['scope_sha256'] or proof['payload_sha256'] != payload
            or proof['runtime_source_sha256'] != runtime or proof['execution_host_policy_sha256'] != POLICY_SHA256
            or proof['supplemental_runtime_sha256'] != extra
            or any(proof[k] is not True for k in fields)):
        raise ValueError('Complete affected P1 entry/released reader CPU and unchanged reusable sources required')
    quote = read_record(stage/'whole-quote.json')
    costs, bounds = quote['components_seconds'], quote['fair_search_query_bounds']
    expected_costs = {'source_parent_requests','shadow_dense_compute','shadow_state_capture_hash_restore',
        'fresh_baselines','candidate_FIT','selected_candidate_CHECK','search_FIT','selected_search_CHECK',
        'warm_and_controls','internal_FIT_CPU_held_allocation','internal_container_startup',
        'model_load_admission_stop_release','variation_margin'}
    if (authority['quote_sha256'] != file_sha(stage/'whole-quote.json')
            or quote['schema'] != 'CARA_V1_P1_WHOLE_ACCEPTED_QUOTE_R1' or quote['whole_quote_accepted'] is not True
            or quote['scope_sha256'] != card['scope_sha256'] or quote['host'] != 'two_card'
            or any(quote[k] != profile[k] for k in ('hard_GPUh','semantic_positions','physical_generation_upper',
                'physical_model_pairs_upper','internal_FIT_queries_upper','internal_FIT_metric_pairs_upper',
                'postrelease_new_metric_pairs_upper'))
            or set(costs) != expected_costs or any(type(v) not in (int,float) or not math.isfinite(v) or v <= 0 for v in costs.values())
            or costs['model_load_admission_stop_release'] < 600
            or not math.isclose(math.fsum(costs.values())/3600, quote['forecast_GPUh'], rel_tol=0, abs_tol=1e-9)
            or not 0 < quote['forecast_GPUh'] <= profile['hard_GPUh']
            or quote['snapshot_cost_basis_accepted'] is not True or not quote['evidence_refs']
            or set(bounds) != {'path_seconds','FIT_score_seconds','overhead_seconds'}
            or any(type(v) not in (int,float) or not math.isfinite(v) or v <= 0 for v in bounds.values())
            or bounds['FIT_score_seconds'] < 600):
        raise ValueError('Whole P1 requests/snapshots/held CPU/startup/release quote and full-query bounds required')
    return card, registration, authority, profile, quote


def validate(project, stage):
    project, stage = Path(project), Path(stage)
    card, registration, authority, profile, quote = validate_inputs(project, stage)
    launch, envelope, guardian = (read_record(stage/n) for n in ('GPU-launch.json','central-reservation.json','guardian.json'))
    job = envelope['job']
    if (any(launch[k] != authority[k] for k in IDENTITY) or launch['CPU_fixture_only'] is not False
            or launch['registration_sha256'] != file_sha(stage/'registration.json')
            or launch['authorization_sha256'] != file_sha(stage/'GPU-authorization.json')
            or launch['central_reservation_sha256'] != file_sha(stage/'central-reservation.json')
            or launch['admission_sha256'] != file_sha(stage/'fresh-admission.json')
            or envelope['central_ledger_host'] != 'four_card' or envelope['new_reservation'] is not True
            or job['job_id'] != RUN_ID or job['status'] != 'RESERVED_OR_RUNNING'
            or any(job[k] != launch[k] for k in JOB_IDENTITY)):
        raise ValueError('Original admitted P1 launch and exact central reservation required')
    context = {k:launch[k] for k in IDENTITY}
    context.update(CPU_fixture_only=False, phase='SOURCE_LIFECYCLE_V1_P1', hard_GPUh=launch['billed_limit_GPUh'],
        guardian_started_monotonic=guardian['started_monotonic'], launch_sha256=file_sha(stage/'GPU-launch.json'),
        registration_sha256=launch['registration_sha256'], admission_sha256=launch['admission_sha256'],
        model_precision_sha256=read_record(stage/PRECISION)['precision_sha256'])
    spec = read_record(project/'outputs'/RUN_ID/'internal-FIT-queue/binding.json')
    verify_broker_source(spec, full=True)
    if spec['context'] != context or guardian['original_handles']['guardian'] != launch['guardian_identity']:
        raise ValueError('Original guardian and sealed host FIT queue must share the exact runner context')
    queue, _ = paths(spec)
    start = read_record(queue/'service-start.json')
    if start['binding_sha256'] != digest(spec):
        raise ValueError('Original host FIT service start differs')
    return card, launch, profile, context, spec, quote
