"""Independent S original-byte financial and technical acceptance.

Full artifacts and risk analysis are separate post-release CPU work. A failed
technical outcome never makes the original host allocation free.
"""
from .gpu_budget_pool_v2 import finite
from .policy_asset_price_review_r1 import exclusive_gate
from .policy_price_terminal_r1 import record
from .sq_s_data_terminal_r2 import require,digest,check_result
from .sq_s_execution_r2 import check_host_bill,settle_central,Pool
from .sq_s_spec_r2 import (RUN,COUNTS,LIMITS,SCOPE,PROFILE,QUOTES,IDENTITY,RESOURCE,ASSETS,MODE,
    PHYSICAL,IDENTITY_SHA,RESOURCE_SHA,UPPER_SHA,OTHER_A6000,EXECUTION_CRITICAL)

IMAGE='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
HANDLES=('guardian','container_cli','supervisor','runner')
TERMINAL_SOURCE='src/wcomr/sq_s_terminal_r2.py'
CAPTURE_SOURCE='src/wcomr/sq_s_capture_r2.py'
MONITOR_SOURCE='src/wcomr/sq_s_monitor_terminal_r2.py'


def original_identity(capture,scope):
    launch=record(capture,'launch');reg=record(capture,'registration');auth=record(capture,'authorization')
    envelope=record(capture,'central_reservation');binding=record(capture,'launch_binding');proof=record(capture,'CPU_acceptance')
    host=launch['host'];physical=record(capture,'physical');identity=record(capture,'identity')
    require(launch['run_id']==RUN and host in LIMITS and launch['whole_GPUh']==LIMITS[host]
        and launch['scope_counts']==physical['counts']==COUNTS and record(capture,'scope')==scope
        and scope['scope_sha256']==UPPER_SHA==digest({k:v for k,v in scope.items() if k!='scope_sha256'})
        and physical['upper_scope_sha256']==UPPER_SHA and physical['host']==host
        and physical['physical_scope_sha256']==launch['physical_scope_sha256']
        and physical['physical_scope_sha256']==digest({k:v for k,v in physical.items() if k!='physical_scope_sha256'})
        and physical['execution_identity_sha256']==IDENTITY_SHA and not physical['CPU_fixture_only'],
        'Original full real S launch and physical cohort required')
    require(reg['namespace']=='SQ_S_COMPLETE_EXECUTION_R2' and reg['stage']==launch['stage']
        and reg['host']==host and reg['source_revision']==launch['source_revision']
        and capture['files']['registration']['sha256']==launch['registration_sha256']
        and capture['files']['authorization']['sha256']==launch['authorization_sha256']
        and capture['files']['scope']['sha256']==launch['scope_sha256'],'Original S stage/source/launch bytes differ')
    require(capture['payload_actual_sha256']==reg['payload_sha256']
        and capture['runtime_actual_sha256']==reg['runtime_source_sha256']
        and set(EXECUTION_CRITICAL)<=set(reg['payload_sha256'])
        and identity['identity_sha256']==IDENTITY_SHA==digest({k:v for k,v in identity.items() if k!='identity_sha256'})
        and all(reg['payload_sha256'].get(name)==value for name,value in identity['numerical_source_sha256'].items())
        and all(reg['runtime_source_sha256'].get(name)==value for name,value in identity['runtime_source_sha256'].items()),
        'Original complete S numerical/runtime source differs')
    for key,path in (('scope',SCOPE),('profile',PROFILE),('quote',QUOTES[host]),('physical',PHYSICAL[host]),
        ('identity',IDENTITY),('resource',RESOURCE),('assets',ASSETS),('mode',MODE)):
        require(capture['files'][key]['sha256']==reg['payload_sha256'].get(path),'Original registered S bytes differ: '+key)
    require(capture['terminal_validator_sha256']==reg['payload_sha256'][TERMINAL_SOURCE]
        and capture['capture_worker_sha256']==reg['payload_sha256'][CAPTURE_SOURCE],
        'Independent S capture/terminal source is unbound')
    contract=record(capture,'resource')
    require(contract['contract_sha256']==RESOURCE_SHA==digest({k:v for k,v in contract.items() if k!='contract_sha256'})
        and auth['execution_identity_sha256']==IDENTITY_SHA and auth['S_resource_contract_sha256']==RESOURCE_SHA,
        'Original S resource/model identity differs')
    require(auth['direct_user_authorization'] is True and bool(auth['user_quote'])
        and auth['authorizes_S_collection'] is True and auth['authorizes_Q1_collection'] is False
        and auth['authorizes_retry'] is False and auth['whole_quote_frozen_by_this_approval'] is True
        and auth['engineering_allowances_accepted_for_this_card'] is True
        and (host!='two_card' or auth['gpu_uuid']==OTHER_A6000),'Exact original S-only approval required')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256','physical_scope_sha256',
        'scope_counts','whole_GPUh','registration_sha256'):
        require(auth[key]==launch[key],'Original S authority/launch differs: '+key)
    quote=record(capture,'quote')
    require(auth['quote_sha256']==capture['files']['quote']['sha256'] and quote['host']==host
        and quote['physical_counts']==COUNTS and quote['physical_scope_sha256']==launch['physical_scope_sha256']
        and quote['proposed_hard_limit_GPUh']==LIMITS[host]
        and auth['CPU_proof_sha256']==capture['files']['CPU_acceptance']['sha256']
        and auth['storage_contract_sha256']==capture['files']['storage']['sha256']
        and auth['asset_proof_sha256']==capture['files']['asset_acceptance']['sha256'],
        'Original S complete quote/CPU/assets/storage binding differs')
    require(proof['passed'] is True and proof['GPU_submissions']==0 and proof['host']==host
        and proof['source_revision']==reg['source_revision'] and proof['actual_platform']['system']=='Linux'
        and proof['skipped']==0 and proof['full_S_entry_CPU_accepted'] is True and proof['native_parser_accepted'] is True
        and proof['payload_sha256']==reg['payload_sha256'] and set(EXECUTION_CRITICAL)<=set(proof['critical_source_sha256'])
        and all(reg['payload_sha256'].get(name)==value for name,value in proof['critical_source_sha256'].items()),
        'Original complete same-host S CPU proof differs')
    job=envelope['job']
    require(envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
        and job['job_id']==RUN and job['status']=='RESERVED_OR_RUNNING'
        and job['billed_limit_GPUh']==LIMITS[host] and job['forecast_GPUh']==quote['forecast_complete_GPUh'],
        'Original single complete S central envelope required')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256','physical_scope_sha256',
        'scope_counts','registration_sha256','authorization_sha256'):
        require(job[key]==launch[key],'Original S envelope/launch differs: '+key)
    require(binding['authorization_sha256']==capture['files']['authorization']['sha256']
        and binding['central_reservation_sha256']==capture['files']['central_reservation']['sha256'],
        'Original S launch/envelope binding differs')
    return launch


def financial_terminal(capture,scope):
    launch=original_identity(capture,scope)
    require(capture['status']=='SQ_S_TERMINAL_CAPTURE_R2'
            and set(capture['original_live_handles'])==set(HANDLES)
            and all(value is False for value in capture['original_live_handles'].values())
            and capture['own_UUID_lock_free'] is True and capture['mode_owner_lock_free'] is True,
            'Recover original S handles and locks before settlement')
    billing=record(capture,'billing');pending=record(capture,'pending_release')
    guardian=record(capture,'guardian');allocation=record(capture,'allocation_release')
    check_host_bill(launch,billing,pending,guardian,billing_sha256=capture['files']['billing']['sha256'])
    require(pending['allocation_release_sha256']==capture['files']['allocation_release']['sha256']
            and all(pending[key]==value for key,value in allocation.items()),
            'Original host allocation release bytes differ')
    require(all(guardian['identity'][key]==launch['guardian_identity'][key]
                    for key in ('pid','start_ticks')),'Original S guardian identity differs')
    witness=guardian['container_terminal_witness'];con=capture['container']
    if witness['kind']=='BOUND_CONTAINER_TERMINAL':
        require(con is not None and con['state']['Status'] in ('created','exited')
                and not con['state']['Running'] and con['state']['Pid']==0 and con['image']==IMAGE
                and con['id']==witness['container_id']
                and all(con[key]==value for key,value in witness['container'].items())
                and con['manifest_sha256']==launch['registration_sha256']
                and len(con['device_requests'])==1
                and con['device_requests'][0]['DeviceIDs']==[launch['gpu_uuid']],
                'Original S container is not terminal or changed identity')
    else:
        require(con is None and capture['container_observation']=='DEFINITE_NO_SUCH_CONTAINER'
                and ((witness['kind']=='NO_CONTAINER_DISPATCH'
                      and witness['dispatch_state']==guardian['container_dispatch_state']
                      and witness['dispatch_state'] in ('NOT_ATTEMPTED','SPAWN_FAILED_NO_EXEC'))
                     or (witness['kind']=='ORIGINAL_CONTAINER_NEVER_CREATED'
                         and guardian['container_dispatch_state']=='STARTED')),
                'No-container S terminal is not proven; recover only')
    return launch,billing


def settle_original(pool,capture,scope):
    _,billing=financial_terminal(capture,scope)
    return settle_central(pool,record(capture,'authorization'),billing,
        record(capture,'pending_release'),record(capture,'guardian'),
        billing_sha256=capture['files']['billing']['sha256'])


def audit_settlement(capture,scope,settlement):
    launch,billing=financial_terminal(capture,scope)
    require(settlement['central_ledger_host']=='four_card' and settlement['run_id']==RUN
            and settlement['launch_id']==launch['launch_id'] and settlement['cost_settled'] is True
            and settlement['scientific_acceptance_implied'] is False
            and settlement['billing_sha256']==capture['files']['billing']['sha256'],
            'Original S central settlement identity differs')
    before,after=settlement['central_before'],settlement['central_after']
    require(all(before[k]==after[k] for k in ('cap_gpu_hours','origin_used_gpu_hours','origin_gpu_jobs_launched'))
            and before['cap_gpu_hours']==226 and set(before['jobs'])==set(after['jobs'])
            and all(after['jobs'][key]==value for key,value in before['jobs'].items() if key!=RUN)
            and all(ledger[key]==value for ledger in (before,after)
                    for key,value in Pool.accounting(ledger).items()),
            'Central S settlement changed another job, cap or uncertainty reserve')
    job=after['jobs'][RUN]
    require(job==settlement['job'] and job['status']=='SETTLED'
            and job['actual_GPUh']==billing['actual_GPUh']
            and job['billing_sha256']==capture['files']['billing']['sha256'],
            'Original S central bill not settled')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256'):
        require(job[key]==launch[key],'Settled original S job differs: '+key)
    return billing



def technical_terminal(capture,scope):
    launch,billing=financial_terminal(capture,scope)
    supervisor=record(capture,'supervisor');pending=record(capture,'pending_release')
    guardian=record(capture,'guardian');con=capture['container']
    require(con is not None,'No-container terminal has no S technical collection')
    state=con['state']
    inner=record(capture,'supervisor_billing');diagnostic=record(capture,'supervisor_release')
    require(pending['supervisor_billing_sha256']==capture['files']['supervisor_billing']['sha256']
            ==diagnostic['billing_sha256']==supervisor['supervisor_billing_sha256']
            and pending['supervisor_release_sha256']==capture['files']['supervisor_release']['sha256']
            and inner['billing_clock_owner']=='SUPERVISOR_DIAGNOSTIC'
            and inner['diagnostic_only'] is True and inner['chargeable'] is False
            and diagnostic['diagnostic_only'] is True,
            'Original supervisor monitoring diagnostic bytes differ')
    for value in (supervisor,inner,diagnostic):
        require(all(value[key]==launch[key] for key in (
            'run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256')),
            'Original S supervisor diagnostic identity differs')
    require(billing['started_monotonic']<=inner['started_monotonic']<=inner['ended_monotonic']<=billing['ended_monotonic']
            and inner['allocation_started_monotonic']==supervisor['allocation_started_monotonic']==billing['started_monotonic']
            and inner['started_monotonic']==supervisor['started_monotonic']
            and inner['ended_monotonic']==supervisor['ended_monotonic']
            and inner['wall_seconds']==inner['ended_monotonic']-inner['started_monotonic']
            ==supervisor['diagnostic_wall_seconds'],
            'Original continuous-monitor interval is not within the complete host allocation')
    require(billing['actual_GPUh']<=launch['whole_GPUh'] and state['ExitCode']==0 and not state['OOMKilled']
            and con['readonly_root'] and con['pid_mode']=='host' and con['network']=='none'
            and con['cpus']==2 and con['memory_GiB']==con['memory_swap_GiB']==40
            and con['cpuset_cpus']==record(capture,'profile')['hosts'][launch['host']]['cpuset_cpus'],
            'Original S resource boundary or GPU execution failed')
    require(guardian['container_exit_code']==0 and guardian['mode_restoration']['restored'] is True
            and not guardian.get('error_type') and supervisor['child_exit_code']==0
            and supervisor['exclusive_monitor_accepted'] is True and not supervisor.get('error_type')
            and not supervisor.get('release_error') and pending['technical_accepted'] is True
            and pending['GPU_released'] is True and pending['original_process_exited'] is True
            and pending['cost_settled'] is False,'Original S technical release not accepted')
    idle=guardian['mode_admission']['verified_snapshot']
    require(exclusive_gate(idle,gpu_uuid=launch['gpu_uuid'],phase='idle',now=idle['observed_unix'])[
        'observation_passed'],'Original S hardware idle admission failed')
    collection=record(capture,'collection')
    require(capture['files']['collection']['sha256']==pending['collection_sha256']==supervisor['collection_sha256'],
            'Original S collection bytes changed')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256'):
        require(collection[key]==launch[key],'S collection/launch identity differs: '+key)
    physical=record(capture,'physical');identity=record(capture,'identity')
    classification=check_result(collection,scope,physical,identity_sha256=IDENTITY_SHA,
        resource_contract_sha256=RESOURCE_SHA,expected_shape=identity['expected_real_shape'],
        new_output_root=record(capture,'storage')['output_mount']+'/paths')
    require(classification==pending['collection_classification']==supervisor['collection_classification'],
            'Original S terminal classification changed')
    witness=capture['monitor_witness'];ready=record(capture,'ready');grant=record(capture,'grant')
    require(witness['accepted'] is True and witness['status']=='S_ORIGINAL_FULL_MONITOR_PASS'
        and witness['validator_sha256']==record(capture,'registration')['payload_sha256'][MONITOR_SOURCE]
        and witness['input_sha256']=={key:digest(value) for key,value in dict(launch=launch,supervisor=supervisor,
            inner=inner,ready=ready,grant=grant).items()}
        and witness['samples']==supervisor['observations'] and witness['runner']==supervisor['child_identity']
        and witness['launch_id']==launch['launch_id'] and witness['source_revision']==launch['source_revision']
        and witness['raw_monitor_transferred'] is False and witness['max_monitor_gap_seconds']<=45
        and witness['max_temperature_C']<90,'Original streamed S monitor acceptance differs')
    final=pending['final_snapshot']
    require(exclusive_gate(final,gpu_uuid=launch['gpu_uuid'],phase='idle',now=final['observed_unix'])[
        'observation_passed'],'Original S context release not independently verified')
    return dict(classification,monitor_samples=witness['samples'],
        max_monitor_gap_seconds=witness['max_monitor_gap_seconds'],max_temperature_C=witness['max_temperature_C'])
