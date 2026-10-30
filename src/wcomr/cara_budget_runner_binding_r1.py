"""Read-only runner boundary for one approved, reserved calibration allocation."""
from pathlib import Path

from .cara_budget_calibration_r1 import PRODUCTION_CONFIG, validate_production_context
from .cara_budget_lifecycle_r1 import IDENTITY, JOB_IDENTITY
from .cara_budget_search_journal_r1 import read_record
from .cara_budget_storage_r1 import StorageLimits
from .cara_fast_spec_r1 import digest
from .gpu_budget_pool_v2 import sha
from .policy_price_terminal_r1 import require

BASE='plans/cara_next_stage_20261028/mainline/r2/'
SPEC=BASE+'BUDGET_RUN_SPEC_R1.json'
PROFILE=BASE+'BUDGET_CONTAINER_PROFILE_R1.json'
LIMITS=BASE+'BUDGET_STORAGE_LIMITS_R1.json'
RUNNER='scripts/run_cara_budget_calibration_r1.py'
SOURCE='src/wcomr/cara_budget_runner_binding_r1.py'
REQUIRED=(SOURCE,RUNNER,SPEC,PROFILE,LIMITS,'src/wcomr/cara_budget_calibration_r1.py',
    'src/wcomr/cara_budget_search_r1.py','src/wcomr/cara_budget_search_journal_r1.py',
    'src/wcomr/cara_budget_rgb_objective_r1.py','src/wcomr/cara_budget_storage_r1.py',
    'src/wcomr/cara_fast_requests_r2.py','src/wcomr/cara_fast_requests_r1.py',
    'src/wcomr/prepared_input.py','src/wcomr/full_sampling.py')


def validate(project,stage):
    project,stage=Path(project),Path(stage)
    launch=read_record(stage/'GPU-launch.json');registration=read_record(stage/'registration.json')
    authority=read_record(stage/'GPU-authorization.json')
    require(stage.parent==project/'.sync' and stage.name.startswith('cara-budget-calibration-GPU-')
            and launch['stage']==str(stage) and launch['run_id'].startswith('cara-budget-calibration-'),
            'Original calibration stage/run required')
    require(launch['CPU_fixture_only'] is False and authority['CPU_fixture_only'] is False
            and authority['execution_authorized'] is True and authority['authorizes_replay'] is False
            and authority.get('direct_user_authorization') is True and bool(authority.get('user_quote'))
            and all(authority[k]==launch[k] for k in IDENTITY)
            and all(registration[k]==launch[k] for k in ('host','stage','source_revision')),
            'One direct human-approved original calibration required')
    require(launch['authorization_sha256']==sha(stage/'GPU-authorization.json')
            and launch['registration_sha256']==sha(stage/'registration.json'),
            'Original authority/registration bytes differ')
    payload=registration['payload_sha256']
    require(set(REQUIRED)<=set(payload) and all(not Path(n).is_absolute() and '..' not in Path(n).parts
                and sha(stage/n)==expected for n,expected in payload.items())
            and payload[SOURCE]==sha(__file__) and payload[RUNNER]==sha(stage/RUNNER),
            'Original staged producer/runner source differs')
    runtime=registration['runtime_source_sha256']
    require(bool(runtime) and all(not Path(n).is_absolute() and '..' not in Path(n).parts
                and sha(project/'runtime'/n)==expected for n,expected in runtime.items()),
            'Pinned runtime source differs')
    card=read_record(stage/SPEC);profile=read_record(stage/PROFILE)
    limits=StorageLimits(**read_record(stage/LIMITS)['limits'])
    require(all(payload[n]==sha(stage/n) for n in (SPEC,PROFILE,LIMITS))
            and digest({k:v for k,v in card.items() if k!='scope_sha256'})==card['scope_sha256']==launch['scope_sha256']
            and card['schema']=='CARA_BUDGET_CALIBRATION_RUN_SPEC_R1'
            and card['calibration']['search_config']==vars(PRODUCTION_CONFIG)
            and card['calibration']['physical_paths']==profile['physical_paths']==112
            and card['calibration']['candidate_queries']==profile['candidate_queries']==51
            and card['calibration']['hard_GPUh']==profile['hard_GPUh']==launch['billed_limit_GPUh']==14,
            'Complete prospective calibration manifest/profile required')
    proof=read_record(stage/'execution-CPU-proof.json')
    require(proof.get('passed') is True and proof.get('whole_card_CPU_accepted') is True
            and proof.get('host')==launch['host'] and proof.get('scope_sha256')==card['scope_sha256']
            and authority['CPU_proof_sha256']==sha(stage/'execution-CPU-proof.json')
            and proof['payload_sha256']==payload and proof['runtime_source_sha256']==runtime,
            'Affected full source/host CPU acceptance required')
    quote=read_record(stage/'whole-quote.json')
    host_quote=quote['host_quotes'][launch['host']]
    require(authority['quote_sha256']==sha(stage/'whole-quote.json')
            and quote['scope_sha256']==card['scope_sha256'] and quote['whole_quote_accepted'] is True
            and host_quote['hard_GPUh']==14 and 0<host_quote['forecast_GPUh']<=14
            and host_quote['physical_paths']==112 and host_quote['candidate_queries']==51,
            'Complete admitted host quote required')
    envelope=read_record(stage/'central-reservation.json');job=envelope['job']
    require(launch['central_reservation_sha256']==sha(stage/'central-reservation.json')
            and envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
            and job['job_id']==launch['run_id'] and job['status']=='RESERVED_OR_RUNNING'
            and all(job[k]==launch[k] for k in JOB_IDENTITY),
            'Original unique central reservation required')
    context={k:launch[k] for k in IDENTITY}
    context.update(CPU_fixture_only=False,launch_sha256=sha(stage/'GPU-launch.json'),
        registration_sha256=launch['registration_sha256'],runner_profile_sha256=sha(stage/PROFILE),
        candidate_queries=51,physical_paths=112)
    validate_production_context(context,card,PRODUCTION_CONFIG,card['calibration']['RGB_shape'],limits)
    return card,launch,profile,limits,context
