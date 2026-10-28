"""Q1 original-byte acceptance and CPU analysis after release and settlement.

Reuse the established byte-record and hardware-exclusive predicates. A failed
numeric control is an accepted diagnostic terminal, never codec evidence.
"""
import hashlib
import json
import math

from .gpu_budget_pool_v2 import finite
from .policy_asset_price_review_r1 import exclusive_gate
from .policy_price_terminal_r1 import record
from .sq_q1_execution_r1 import require,check_collection,settle_central,Pool
from .sq_q1_spec_r1 import (RUN,COUNTS,LIMITS,SCOPE,PROFILE,QUOTES,EXECUTION_CRITICAL,
                            RUNTIME_REQUIRED)

IMAGE='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
HANDLES=('guardian','container_cli','supervisor','runner')


def original_identity(capture,scope):
    launch=record(capture,'launch');reg=record(capture,'registration')
    auth=record(capture,'authorization');envelope=record(capture,'central_reservation')
    binding=record(capture,'launch_binding');proof=record(capture,'CPU_acceptance')
    host=launch['host']
    require(launch['run_id']==RUN and host in LIMITS and launch['whole_GPUh']==LIMITS[host]
            and launch['scope_counts']==COUNTS and record(capture,'scope')==scope
            and scope['scope_counts']==COUNTS,'Original complete Q1 launch required')
    require(reg['namespace']=='SQ_Q1_EXECUTION_R1' and reg['stage']==launch['stage']
            and reg['source_revision']==launch['source_revision'] and reg['host']==host,
            'Original Q1 host/stage/source differs')
    require(capture['files']['registration']['sha256']==launch['registration_sha256']
            and capture['files']['authorization']['sha256']==launch['authorization_sha256']
            and capture['files']['scope']['sha256']==launch['scope_sha256'],
            'Original Q1 launch byte binding differs')
    require(capture['payload_actual_sha256']==reg['payload_sha256']
            and capture['runtime_actual_sha256']==reg['runtime_source_sha256']
            and set(EXECUTION_CRITICAL)<=set(reg['payload_sha256'])
            and set(RUNTIME_REQUIRED)<=set(reg['runtime_source_sha256']),
            'Original Q1 source/runtime incomplete or changed')
    for key,path in (('scope',SCOPE),('profile',PROFILE),('quote',QUOTES[host])):
        require(capture['files'][key]['sha256']==reg['payload_sha256'].get(path),
                'Original registered Q1 file differs: '+key)
    require(capture['terminal_validator_sha256']==reg['payload_sha256'][
        'src/wcomr/sq_q1_terminal_r1.py'],'Unbound independent Q1 terminal validator')
    require(auth['direct_user_authorization'] is True and bool(auth['user_quote'])
            and auth['authorizes_retry'] is False and auth['authorizes_S_collection'] is False,
            'Q1-only direct authority required')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256',
                'scope_counts','whole_GPUh','registration_sha256'):
        require(auth[key]==launch[key],'Q1 authority/launch differs: '+key)
    quote=record(capture,'quote')
    require(auth['quote_sha256']==capture['files']['quote']['sha256'] and quote['host']==host
            and quote['scope_counts']==COUNTS and quote['input_source_sha256'][SCOPE]==launch['scope_sha256']
            and quote['proposed_hard_limit_GPUh']==LIMITS[host], 'Original whole Q1 quote differs')
    require(proof['passed'] is True and proof['GPU_submissions']==0
            and auth['CPU_proof_sha256']==capture['files']['CPU_acceptance']['sha256']
            and set(EXECUTION_CRITICAL)<=set(proof['critical_source_sha256'])
            and all(reg['payload_sha256'].get(name)==digest
                    for name,digest in proof['critical_source_sha256'].items()),
            'Original affected Q1 execution CPU proof differs')
    job=envelope['job']
    require(envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
            and job['job_id']==RUN and job['status']=='RESERVED_OR_RUNNING'
            and job['billed_limit_GPUh']==LIMITS[host], 'Original single Q1 envelope required')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256',
                'scope_counts','registration_sha256','authorization_sha256'):
        require(job[key]==launch[key],'Original Q1 envelope/launch differs: '+key)
    require(binding['authorization_sha256']==capture['files']['authorization']['sha256']
            and binding['central_reservation_sha256']==capture['files']['central_reservation']['sha256'],
            'Original Q1 launch/envelope binding differs')
    return launch


def financial_terminal(capture,scope):
    launch=original_identity(capture,scope)
    require(capture['status']=='SQ_Q1_TERMINAL_CAPTURE_R1'
            and set(capture['original_live_handles'])==set(HANDLES)
            and all(value is False for value in capture['original_live_handles'].values())
            and capture['own_UUID_lock_free'] is True and capture['mode_owner_lock_free'] is True,
            'Recover original Q1 handles and locks before settlement')
    con=capture['container'];state=con['state']
    require(state['Status']=='exited' and not state['Running'] and con['image']==IMAGE
            and con['manifest_sha256']==launch['registration_sha256']
            and len(con['device_requests'])==1
            and con['device_requests'][0]['DeviceIDs']==[launch['gpu_uuid']],
            'Original Q1 container is not terminal or changed identity')
    billing=record(capture,'billing');pending=record(capture,'pending_release')
    supervisor=record(capture,'supervisor');guardian=record(capture,'guardian')
    for value in (billing,pending,supervisor):
        for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256'):
            require(value[key]==launch[key],'Original Q1 terminal identity differs: '+key)
    require(billing['billed_limit_GPUh']==launch['whole_GPUh'] and finite(billing['wall_seconds'])
            and billing['wall_seconds']>0 and billing['actual_GPUh']==billing['wall_seconds']/3600
            and pending['billing_sha256']==capture['files']['billing']['sha256'],
            'Original exact Q1 wall bill differs')
    require(guardian['status']=='SQ_Q1_HOST_GUARDIAN_TERMINAL'
            and all(guardian[key]==launch[key] for key in ('run_id','gpu_uuid','launch_id','source_revision'))
            and all(guardian['identity'][key]==launch['guardian_identity'][key]
                    for key in ('pid','start_ticks')),'Original Q1 guardian identity differs')
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
            'Original Q1 central settlement identity differs')
    before,after=settlement['central_before'],settlement['central_after']
    require(all(before[k]==after[k] for k in ('cap_gpu_hours','origin_used_gpu_hours','origin_gpu_jobs_launched'))
            and before['cap_gpu_hours']==226 and set(before['jobs'])==set(after['jobs'])
            and all(after['jobs'][key]==value for key,value in before['jobs'].items() if key!=RUN)
            and all(ledger[key]==value for ledger in (before,after)
                    for key,value in Pool.accounting(ledger).items()),
            'Central Q1 settlement changed another job, cap or uncertainty reserve')
    job=after['jobs'][RUN]
    require(job==settlement['job'] and job['status']=='SETTLED'
            and job['actual_GPUh']==billing['actual_GPUh']
            and job['billing_sha256']==capture['files']['billing']['sha256'],
            'Original Q1 central bill not settled')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256'):
        require(job[key]==launch[key],'Settled original Q1 job differs: '+key)
    return billing


def technical_terminal(capture,scope):
    launch,billing=financial_terminal(capture,scope)
    supervisor=record(capture,'supervisor');pending=record(capture,'pending_release')
    guardian=record(capture,'guardian');con=capture['container'];state=con['state']
    require(billing['actual_GPUh']<=launch['whole_GPUh'] and state['ExitCode']==0 and not state['OOMKilled']
            and con['readonly_root'] and con['pid_mode']=='host' and con['network']=='none'
            and con['cpus']==2 and con['memory_GiB']==con['memory_swap_GiB']==16
            and con['cpuset_cpus']==record(capture,'profile')['hosts'][launch['host']]['cpuset_cpus'],
            'Original Q1 resource boundary or GPU execution failed')
    require(guardian['container_exit_code']==0 and guardian['mode_restoration']['restored'] is True
            and not guardian.get('error_type') and supervisor['child_exit_code']==0
            and supervisor['exclusive_monitor_accepted'] is True and not supervisor.get('error_type')
            and not supervisor.get('release_error') and pending['technical_accepted'] is True
            and pending['GPU_released'] is True and pending['original_process_exited'] is True
            and pending['cost_settled'] is False,'Original Q1 technical release not accepted')
    idle=guardian['mode_admission']['verified_snapshot']
    require(exclusive_gate(idle,gpu_uuid=launch['gpu_uuid'],phase='idle',now=idle['observed_unix'])[
        'observation_passed'],'Original Q1 hardware idle admission failed')
    collection=record(capture,'collection')
    require(capture['files']['collection']['sha256']==pending['collection_sha256']==supervisor['collection_sha256'],
            'Original Q1 collection bytes changed')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256'):
        require(collection[key]==launch[key],'Q1 collection/launch identity differs: '+key)
    classification=check_collection(scope,collection)
    require(classification==pending['collection_classification']==supervisor['collection_classification'],
            'Original Q1 terminal classification changed')
    raw=capture['monitor_raw_utf8']
    require(hashlib.sha256(raw.encode()).hexdigest()==capture['monitor_sha256'],
            'Original Q1 continuous monitor bytes changed')
    rows=[json.loads(line) for line in raw.splitlines()]
    ready,grant=record(capture,'ready'),record(capture,'grant');runner=supervisor['child_identity']
    require(rows and len(rows)==supervisor['observations'] and ready['identity']==grant['runner']==runner
            and ready['GPU_context_held'] is True and grant['gpu_uuid']==launch['gpu_uuid']
            and grant['source_revision']==ready['source_revision']==launch['source_revision'],
            'Original sole-runner context grant missing')
    active=False;last=0.;max_gap=0.;maximum_temperature=0.
    for row in rows:
        elapsed=row['monotonic_elapsed'];gap=elapsed-last
        require(finite(elapsed) and 0<=gap<=45,'Interrupted or reversed Q1 exclusive monitoring')
        last=elapsed;max_gap=max(max_gap,gap)
        require(row['launch_id']==launch['launch_id'] and row['run_id']==RUN and row['runner']==runner
                and (not active or row['context_granted']),'Mixed original Q1 monitor identity or regressed grant')
        active=active or row['context_granted'];snapshot=row['snapshot']
        require(exclusive_gate(snapshot,gpu_uuid=launch['gpu_uuid'],
            phase='active' if active or snapshot['compute_apps'] else 'idle',runner=runner,
            now=snapshot['observed_unix'])['observation_passed'],'Foreign or unknown Q1 GPU context')
        temperature=float(row['thermal']['temperature.gpu'])
        require(math.isfinite(temperature) and temperature<90,'Original Q1 thermal stop or invalid value')
        maximum_temperature=max(maximum_temperature,temperature)
    require(active and 0<=billing['wall_seconds']-last<=45,'Unmonitored original Q1 terminal interval')
    final=pending['final_snapshot']
    require(exclusive_gate(final,gpu_uuid=launch['gpu_uuid'],phase='idle',now=final['observed_unix'])[
        'observation_passed'],'Original Q1 context release not independently verified')
    return dict(classification,monitor_samples=len(rows),max_monitor_gap_seconds=max_gap,
                max_temperature_C=maximum_temperature)


def analyse_released(capture,scope,settlement):
    """All numerical selection is CPU work after original release and settlement."""
    billing=audit_settlement(capture,scope,settlement)
    technical=technical_terminal(capture,scope)
    result=dict(status='Q1_NUMERIC_DIAGNOSTIC_TERMINAL_NO_CODEC_SELECTION',run_id=RUN,
        actual_GPUh=billing['actual_GPUh'],technical_acceptance=technical,codec_selection=None,
        endpoint_benefit_established=False,deployment_memory_or_speed_measured=False)
    if technical['complete']:
        from .sq_q1_readout_r1 import select_shared_codecs
        result.update(status='Q1_COMPLETE_POST_RELEASE_CODEC_SELECTION',
            codec_selection=select_shared_codecs(record(capture,'collection')['states']))
    return result
