"""Source, scope and original-allocation binding for the full14 M1 runner."""
from pathlib import Path
import re

from .cara_budget_host_policy_r1 import bound_policy, POLICY, POLICY_SHA256
from .cara_budget_search_journal_r1 import read_record
from .cara_read_write_plan_r1 import build, validate as validate_card
from .cara_s_endpoint_lifecycle_r1 import IDENTITY, JOB_IDENTITY
from .gpu_budget_pool_v2 import finite, sha
from .policy_price_terminal_r1 import require

SOURCE = 'src/wcomr/cara_read_write_runner_binding_r1.py'
RUNNER = 'scripts/run_cara_read_write_m1_r1.py'
LOADED = 'src/wcomr/cara_read_write_runner_r1.py'
CARD = 'plans/cara_next_stage_20261101/read_write/M1_FULL14_MANIFEST_R2.json'
PARENT = 'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'
PROFILE = 'plans/cara_next_stage_20261101/read_write/M1_FULL14_CONTAINER_PROFILE_R1.json'
PRECISION = 'configs/cara_endpoint_proposal.json'
MODE = 'manifests/wc_h0_eval_mode_contract_20261003.json'
SETUP = 'configs/f1_setup.json'
GEOMETRY = 'configs/wc_ra_comparison_production_r2_20261010.json'
IMAGE = 'sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
GPU = 'GPU-cebf7119-cf03-23b9-e192-cd196332b704'
REQUIRED = (SOURCE, RUNNER, LOADED, CARD, PARENT, PROFILE, PRECISION, MODE, SETUP, GEOMETRY, POLICY,
    'src/wcomr/cara_read_write_plan_r1.py', 'src/wcomr/cara_read_write_collection_r1.py',
    'src/wcomr/cara_read_write_point_r1.py', 'src/wcomr/cara_read_write_suffix_r1.py',
    'src/wcomr/cpu_owned_state_snapshot.py', 'src/wcomr/cara_s_endpoint_runner_r1.py',
    'src/wcomr/cara_budget_host_policy_r1.py', 'src/wcomr/cara_s_endpoint_lifecycle_r1.py',
    'src/wcomr/full_sampling.py', 'src/wcomr/h0_mode.py', 'src/wcomr/runtime_config.py',
    'scripts/run_cara_budget_calibration_r1.py', 'src/wcomr/cara_fast_spec_r1.py',
    'src/wcomr/clean_speed20_r1.py', 'src/wcomr/paper_latency_r1.py', 'src/wcomr/prepared_input.py',
    'src/wcomr/policy_generator_r1/production_sampling.py',
    'src/wcomr/policy_generator_r1/p2_native_sampling.py',
    'src/wcomr/policy_generator_r1/interval_grammar.py',
    'src/wcomr/policy_generator_r1/frozen_request_arguments.py',
    'src/wcomr/wc_time_collection_r1.py', 'src/wcomr/history104_storage_r2.py',
    'src/wcomr/wc73_exclusive_r1.py', 'src/wcomr/cara_budget_original_handles_r1.py',
    'src/wcomr/cara_budget_search_journal_r1.py', 'src/wcomr/cara_read_write_dispatch_r1.py',
    'src/wcomr/cara_read_write_central_r1.py', 'src/wcomr/cara_read_write_capture_r1.py',
    'src/wcomr/cara_read_write_artifacts_r1.py', 'src/wcomr/cara_read_write_scores_r1.py',
    'src/wcomr/cara_read_write_score_capture_r1.py', 'src/wcomr/cara_read_write_score_dispatch_r1.py',
    'scripts/cara_read_write_dispatch_r1.py', 'scripts/cara_read_write_host_entry_r1.py',
    'scripts/cara_read_write_container_r1.py', 'scripts/cara_read_write_supervisor_worker_r1.py',
    'scripts/score_cara_read_write_fidelity_r1.py', 'scripts/cara_read_write_score_bootstrap_r1.py',
    'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json')


def validate_profile(profile, scope_sha256):
    require(profile['schema'] == 'CARA_READ_WRITE_M1_CONTAINER_PROFILE_R1'
        and profile['scope_sha256'] == scope_sha256
        and (profile['physical_paths'], profile['physical_model_pairs'], profile['new_scoring_pairs']) == (14, 512, 8)
        and profile['hard_GPUh'] == 1.95 and profile['stop_release_reserve_seconds'] == 600
        and profile['temperature_stop_C'] == 90
        and profile['GPU_container'] == dict(image=IMAGE, cpus=2, memory_GiB=40, memory_swap_GiB=40,
            pid_namespace='host', network='none', readonly_rootfs=True,
            supervisor_CUDA_visible=False, only_exact_runner_CUDA_visible=True)
        and profile['hosts'] == {'two_card':dict(capability=[8, 6], cpuset_cpus='24,25', minimum_MemAvailable_GiB=44)}
        and profile['snapshot_limits'] == dict(logical_copy_bytes=48*2**30, total_CPU_images_bytes=16*2**30),
        'Exact complete M1 container, host, snapshot and hard limits required')
    limits = profile['storage']
    require(limits['output_image_bytes'] == 16*2**30 and limits['independent_journal_bytes'] == 48*2**20
        and limits['minimum_output_free_bytes'] == 4*2**30
        and limits['minimum_host_free_bytes'] == 16*2**30
        and limits['minimum_host_free_before_provision_bytes'] == 32*2**30
        and limits['minimum_free_inodes'] == 1024,
        'Exact16GiB private M1 output and independent48MiB journal required')


def validate_inputs(project, stage):
    project, stage = Path(project), Path(stage)
    authority = read_record(stage/'GPU-authorization.json')
    registration = read_record(stage/'registration.json')
    require(project.is_absolute() and stage.parent == project/'.sync'
        and stage.name.startswith('cara-read-write-M1-GPU-')
        and authority['stage'] == str(stage)
        and re.fullmatch('cara-read-write-M1-[a-z0-9-]+', authority['run_id'])
        and re.fullmatch('[0-9a-f]{40}', authority['source_revision'])
        and re.fullmatch('[0-9a-f]{32}', authority['launch_id']), 'Original isolated M1 identity required')
    require(authority['CPU_fixture_only'] is False and authority['execution_authorized'] is True
        and authority['authorizes_replay'] is False and authority['card_kind'] == 'CARA_READ_WRITE_M1_FULL14'
        and authority['authorization_basis'] == 'USER_STANDING_BELOW2_GPUH_MAINLINE'
        and bool(authority['user_quote']) and authority['host'] == 'two_card' and authority['gpu_uuid'] == GPU
        and all(registration[k] == authority[k] for k in ('host', 'stage', 'source_revision')),
        'M1 authority must bind the existing below2GPUh rule and original two-card GPU')
    payload, runtime = registration['payload_sha256'], registration['runtime_source_sha256']
    require(set(REQUIRED) <= set(payload) and all(not Path(p).is_absolute() and '..' not in Path(p).parts
        and sha(stage/p) == h for p, h in payload.items()) and payload[SOURCE] == sha(__file__)
        and bool(runtime) and all(not Path(p).is_absolute() and '..' not in Path(p).parts
        and sha(project/'runtime'/p) == h for p, h in runtime.items()), 'Registered M1 source/runtime differs')
    bound_policy(stage, registration, authority)
    card, profile = read_record(stage/CARD), read_record(stage/PROFILE)
    validate_card(card)
    require(card == build(read_record(stage/PARENT)), 'Exact original two-FIT complete14 M1 scope required')
    validate_profile(profile, card['scope_sha256'])
    require(authority['scope_sha256'] == card['scope_sha256']
        and authority['physical_paths'] == 14 and authority['billed_limit_GPUh'] == profile['hard_GPUh']
        and registration['container_image'] == IMAGE, 'M1 scope, image and whole limit differ')
    proof = read_record(stage/'execution-CPU-proof.json')
    require(authority['CPU_proof_sha256'] == sha(stage/'execution-CPU-proof.json')
        and proof['passed'] is True and proof['whole_card_CPU_accepted'] is True
        and proof['host'] == 'two_card' and proof['scope_sha256'] == card['scope_sha256']
        and proof['payload_sha256'] == payload and proof['runtime_source_sha256'] == runtime
        and proof['execution_host_policy_sha256'] == POLICY_SHA256
        and all(proof[k] is True for k in ('actual_module_full14_accepted', 'loaded_runner_accepted',
            'dispatch_finance_release_accepted', 'postrelease_eight_pair_scorer_accepted')),
        'Complete source-bound affected M1 CPU acceptance required')
    quote = read_record(stage/'whole-quote.json')
    require(authority['quote_sha256'] == sha(stage/'whole-quote.json')
        and quote['whole_quote_accepted'] is True and quote['scope_sha256'] == card['scope_sha256']
        and quote['physical_paths'] == 14 and quote['physical_model_pairs'] == 512
        and quote['scoring_pairs_after_release'] == 8 and quote['hard_GPUh'] == profile['hard_GPUh']
        and finite(quote['forecast_GPUh']) and 0 < quote['forecast_GPUh'] <= quote['hard_GPUh'] < 2
        and quote['stop_release_reserve_seconds'] == 600,
        'Complete below2GPUh whole M1 quote required')
    costs = quote['components_seconds']
    require(set(costs) == {'requests_and_extra_D_seconds', 'request_variation_buffer_seconds',
        'model_load_and_setup_seconds', 'new_snapshot_hash_materialization_allowance_seconds', 'stop_release_reserve_seconds'}
        and all(finite(v) and v > 0 for v in costs.values())
        and costs['stop_release_reserve_seconds'] >= 600
        and abs(sum(costs.values())/3600 - quote['forecast_GPUh']) < 1e-9,
        'M1 quote must include all requests, snapshots, setup and release')
    return card, registration, authority, profile


def validate(project, stage):
    stage = Path(stage)
    card, registration, authority, profile = validate_inputs(project, stage)
    launch = read_record(stage/'GPU-launch.json')
    envelope = read_record(stage/'central-reservation.json')
    job = envelope['job']
    require(launch['CPU_fixture_only'] is False and all(launch[k] == authority[k] for k in IDENTITY)
        and launch['physical_paths'] == 14
        and launch['authorization_sha256'] == sha(stage/'GPU-authorization.json')
        and launch['registration_sha256'] == sha(stage/'registration.json')
        and launch['central_reservation_sha256'] == sha(stage/'central-reservation.json')
        and envelope['central_ledger_host'] == 'four_card' and envelope['new_reservation'] is True
        and job['job_id'] == launch['run_id'] and job['status'] == 'RESERVED_OR_RUNNING'
        and all(job[k] == launch[k] for k in JOB_IDENTITY), 'Original single M1 launch/reservation required')
    admission_sha256 = sha(stage/'fresh-admission.json')
    require(launch['admission_sha256'] == admission_sha256, 'Original M1 asset/resource admission changed')
    context = {k:launch[k] for k in IDENTITY}
    context.update(phase='READ_WRITE_M1', CPU_fixture_only=False, physical_paths=14,
        launch_sha256=sha(stage/'GPU-launch.json'), registration_sha256=launch['registration_sha256'],
        admission_sha256=admission_sha256,
        model_precision_sha256=read_record(stage/PRECISION)['precision_sha256'])
    return card, launch, profile, context
