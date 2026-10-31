"""Read-only binding for a separately approved complete endpoint runner."""
from pathlib import Path
import re

from .cara_budget_host_policy_r1 import bound_policy,POLICY,SOURCE as HOST_POLICY_SOURCE,POLICY_SHA256
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_binding_r2 import load_card
from .cara_fast_spec_r1 import digest,policy_from_mask,profile_from
from .cara_s_endpoint_artifacts_r1 import PROPOSAL
from .cara_s_endpoint_lifecycle_r1 import IDENTITY,JOB_IDENTITY
from .cara_s_endpoint_release_r1 import CARD,BINDING
from .cara_s_uniform_endpoint_execution_r1 import request_card
from .gpu_budget_pool_v2 import finite,sha
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_runner_binding_r1.py'
RUNNER='scripts/run_cara_s_endpoint_r1.py'
LOADED='src/wcomr/cara_s_endpoint_runner_r1.py'
PROFILE='configs/cara_endpoint_container_profile.json'
BASE='plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json'
MODE='manifests/wc_h0_eval_mode_contract_20261003.json'
RA='plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json'
SETUP='configs/f1_setup.json'
GEOMETRY='configs/wc_ra_comparison_production_r2_20261010.json'
IMAGE='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
REQUIRED=('plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json',SOURCE,RUNNER,LOADED,PROFILE,CARD,BINDING,PROPOSAL,BASE,MODE,RA,SETUP,GEOMETRY,POLICY,HOST_POLICY_SOURCE,
    'src/wcomr/cara_s_endpoint_pipeline_r1.py','src/wcomr/cara_s_uniform_endpoint_execution_r1.py',
    'src/wcomr/cara_s_uniform_endpoint_binding_r1.py','src/wcomr/cara_s_uniform_endpoint_plan_r1.py',
    'src/wcomr/cara_fast_requests_r2.py','src/wcomr/cara_fast_requests_r1.py',
    'src/wcomr/full_sampling.py','src/wcomr/h0_mode.py','src/wcomr/runtime_config.py',
    'scripts/run_cara_budget_calibration_r1.py','src/wcomr/cara_s_endpoint_lifecycle_r1.py',
    'src/wcomr/clean_speed20_r1.py','src/wcomr/paper_latency_r1.py','src/wcomr/prepared_input.py',
    'src/wcomr/policy_generator_r1/production_sampling.py','src/wcomr/policy_generator_r1/p2_native_sampling.py',
    'src/wcomr/policy_generator_r1/interval_grammar.py','src/wcomr/policy_generator_r1/frozen_request_arguments.py',
    'src/wcomr/wc_time_collection_r1.py','src/wcomr/cara_fast_binding_r2.py','src/wcomr/cara_fast_spec_r1.py',
    'src/wcomr/history104_storage_r2.py','src/wcomr/wc73_exclusive_r1.py',
    'src/wcomr/cara_budget_original_handles_r1.py','src/wcomr/cara_budget_search_journal_r1.py')


def validate_inputs(project,stage):
    project,stage=Path(project),Path(stage)
    authority=read_record(stage/'GPU-authorization.json');registration=read_record(stage/'registration.json')
    require(project.is_absolute() and stage.parent==project/'.sync' and stage.name.startswith('cara-S-endpoint-GPU-')
            and authority['stage']==str(stage) and re.fullmatch('cara-S-endpoint-[a-z0-9-]+',authority['run_id'])
            and re.fullmatch('[0-9a-f]{40}',authority['source_revision'])
            and re.fullmatch('[0-9a-f-]{32,36}',authority['launch_id']), 'Original isolated endpoint identity required')
    require(authority['CPU_fixture_only'] is False and authority['execution_authorized'] is True
            and authority['authorizes_replay'] is False and authority['direct_user_authorization'] is True
            and bool(authority['user_quote']) and authority['new_endpoint_authorization'] is True
            and authority['card_kind']=='CARA_SU19_BUDGET_ENDPOINT'
            and all(registration[k]==authority[k] for k in ('host','stage','source_revision')),
            'Separate direct endpoint authority required')
    payload=registration['payload_sha256'];runtime=registration['runtime_source_sha256']
    require(set(REQUIRED)<=set(payload) and all(not Path(p).is_absolute() and '..' not in Path(p).parts
                and sha(stage/p)==h for p,h in payload.items()) and payload[SOURCE]==sha(__file__)
            and bool(runtime) and all(not Path(p).is_absolute() and '..' not in Path(p).parts
                and sha(project/'runtime'/p)==h for p,h in runtime.items()), 'Registered endpoint source/runtime differs')
    if read_record(stage/PROPOSAL).get('endpoint7'):
        for path in ('src/wcomr/cara_endpoint7_binding_r1.py', 'src/wcomr/cara_endpoint7_plan_r1.py'):
            require(payload.get(path)==sha(Path(__file__).parents[2]/path), 'Seven-role binding source missing or changed')
    bound_policy(stage,registration,authority)
    card,bound,proposal,profile=[read_record(stage/p) for p in (CARD,BINDING,PROPOSAL,PROFILE)]
    require(card['CPU_fixture_only'] is bound['CPU_fixture_only'] is False
            and proposal.get('CPU_fixture_only',False) is False
            and bound['status']=='FROZEN_POLICY_BOUND_WHOLE_CPU_PENDING'
            and card==request_card(proposal,bound,load_card(stage,BASE)), 'Exact production endpoint scope/binding required')
    count=len(card['physical_matrix']);pairs=bound['counts']['unique_new_scoring_pairs']
    freeze=Path(bound['original_freeze_path']);original=bound['original_calibration']
    expected=proposal['budget_comparator']
    require(freeze==project/'outputs'/original['run_id']/'calibration-frozen-mask.json'
            and sha(freeze)==bound['original_freeze_sha256'] and read_record(freeze)==original
            and original['schema']=='CARA_BUDGET_COMPLETE_MASK_FREEZE_R1'
            and original['CPU_fixture_only'] is False and original['new_GPU_authority'] is False
            and original['complete_physical_paths']==112 and original['complete_two_FIT_queries']==51
            and all(original[k]==expected['original_'+k] for k in ('run_id','launch_id','source_revision','scope_sha256'))
            and original['launch_id']!=authority['launch_id']
            and original['policy']==bound['budget_policy']==policy_from_mask(profile_from(proposal['profile']),original['selected']['dense'])
            and original['selected']['policy_fingerprint']==original['policy']['fingerprint'],
            'Original complete112/51 production budget freeze required')
    require(authority['scope_sha256']==profile['scope_sha256']==card['scope_sha256']
            and authority['physical_paths']==profile['physical_paths']==count in ((46,) if card.get('endpoint7') else (25,32))
            and profile['new_scoring_pairs']==pairs in ((16,) if card.get('endpoint7') else (8,12))
            and authority['endpoint_binding_sha256']==profile['endpoint_binding_sha256']==bound['binding_sha256']
            and authority['original_budget_freeze_sha256']==bound['original_freeze_sha256']
            and authority['gpu_uuid']==proposal['gpu_uuid'] and authority['host']==proposal['host']=='two_card'
            and finite(authority['billed_limit_GPUh']) and authority['billed_limit_GPUh']==profile['hard_GPUh']>600/3600,
            'Complete endpoint scope, original GPU and independent whole limit required')
    require(profile['schema']=='CARA_ENDPOINT_CONTAINER_PROFILE_R1'
            and profile['GPU_container']==dict(image=IMAGE,cpus=2,memory_GiB=40,memory_swap_GiB=40,
                pid_namespace='host',network='none',readonly_rootfs=True,supervisor_CUDA_visible=False,
                only_exact_runner_CUDA_visible=True)
            and registration['container_image']==IMAGE
            and profile['hosts']=={'two_card':dict(capability=[8,6],cpuset_cpus='24,25',minimum_MemAvailable_GiB=44)}
            and profile['storage']['output_image_bytes']==64*2**30
            and profile['storage']['independent_journal_bytes']==48*2**20
            and profile['storage']['minimum_output_free_bytes']==4*2**30
            and profile['storage']['minimum_host_free_bytes']==128*2**20
            and profile['storage']['minimum_free_inodes']==1024,
            'Pinned endpoint container/host/private storage required')
    proof=read_record(stage/'execution-CPU-proof.json')
    require(authority['CPU_proof_sha256']==sha(stage/'execution-CPU-proof.json')
            and proof['passed'] is True and proof['whole_card_CPU_accepted'] is True
            and proof['selected_policy_affected_CPU_accepted'] is True
            and proof['host']=='two_card' and proof['scope_sha256']==card['scope_sha256']
            and proof['endpoint_binding_sha256']==bound['binding_sha256']
            and proof['original_budget_freeze_sha256']==bound['original_freeze_sha256']
            and proof['payload_sha256']==payload and proof['runtime_source_sha256']==runtime
            and proof['execution_host_policy_sha256']==POLICY_SHA256,
            'Whole and selected-policy source-bound endpoint CPU acceptance required')
    quote=read_record(stage/'whole-quote.json');host_quote=quote['host_quotes']['two_card']
    require(authority['quote_sha256']==sha(stage/'whole-quote.json') and quote['whole_quote_accepted'] is True
            and quote['scope_sha256']==card['scope_sha256'] and quote['endpoint_binding_sha256']==bound['binding_sha256']
            and quote['execution_host_policy_sha256']==POLICY_SHA256 and set(quote['host_quotes'])=={'two_card'}
            and host_quote['physical_paths']==count and host_quote['new_scoring_pairs']==pairs
            and host_quote['hard_GPUh']==authority['billed_limit_GPUh']
            and finite(host_quote['forecast_GPUh']) and 0<host_quote['forecast_GPUh']<=host_quote['hard_GPUh'],
            'Complete separate endpoint host quote required')
    costs=host_quote['components_seconds']
    require(set(costs)=={'generation','path_artifacts','admission_and_model_load','stop_and_release'}
            and all(finite(value) and value>0 for value in costs.values())
            and costs['stop_and_release']>=600 and bool(host_quote['evidence_refs'])
            and abs(sum(costs.values())/3600-host_quote['forecast_GPUh'])<1e-9,
            'Whole endpoint allocation costs and release margin required')
    return card,bound,proposal,registration,authority,profile


def validate(project,stage):
    stage=Path(stage)
    card,bound,proposal,registration,authority,profile=validate_inputs(project,stage)
    launch=read_record(stage/'GPU-launch.json');envelope=read_record(stage/'central-reservation.json');job=envelope['job']
    require(launch['CPU_fixture_only'] is False and all(launch[k]==authority[k] for k in IDENTITY)
            and launch['authorization_sha256']==sha(stage/'GPU-authorization.json')
            and launch['registration_sha256']==sha(stage/'registration.json')
            and launch['central_reservation_sha256']==sha(stage/'central-reservation.json')
            and envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
            and job['job_id']==launch['run_id'] and job['status']=='RESERVED_OR_RUNNING'
            and all(job[k]==launch[k] for k in JOB_IDENTITY), 'Original endpoint launch and central reservation required')
    for key in ('physical_paths','endpoint_binding_sha256','original_budget_freeze_sha256'):
        require(launch[key]==authority[key],'Original endpoint launch field differs: '+key)
    context={k:launch[k] for k in IDENTITY}
    context.update(phase='ENDPOINT',CPU_fixture_only=False,launch_sha256=sha(stage/'GPU-launch.json'),
        registration_sha256=launch['registration_sha256'],physical_paths=len(card['physical_matrix']),
        endpoint_binding_sha256=bound['binding_sha256'],original_budget_freeze_sha256=bound['original_freeze_sha256'],
        new_endpoint_authorization=True,model_precision_sha256=proposal['precision_sha256'])
    return card,bound,proposal,launch,profile,context
