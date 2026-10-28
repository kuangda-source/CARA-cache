"""Original B36 terminal evidence, one central bill, and post-release gating.

These functions consume captured bytes. They neither dispatch a process nor
change device mode. Failed technical runs still settle their original cost.
"""
import math

from .cara_fast_b36_execution_r1 import RUN,LIMITS,Pool,require
from .cara_fast_b36_r1 import bind_handoff,check_complete_B
from .cara_fast_spec_r1 import digest
from pathlib import Path
from .gpu_budget_pool_v2 import finite
from .policy_asset_price_review_r1 import exclusive_gate
from .policy_price_terminal_r1 import record

IMAGE='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
MAX_MONITOR_GAP_SECONDS=45
HANDLES=('guardian','container_cli','supervisor','runner')


def bound_A(capture,card):
    package=capture['A32_handoff']
    launch=record(capture,'launch')
    profile=record(capture,'profile')
    require(all(package['files'][name]['sha256']==descriptor['sha256']
                for name,descriptor in profile['A32_handoff_files'].items()), 'Wrong captured A originals')
    bound=bind_handoff(card,package,host=launch['host'],gpu_uuid=launch['gpu_uuid'],
                       source_root=Path(__file__).resolve().parents[2])
    original=record(record(package,'capture'),'launch')
    require(bound['CPU_fixture_only'] is False and bound['A_launch_id']==profile['A_launch_id']
            and bound['frozen_file_sha256']==profile['A_frozen_sha256']
            and launch['launch_id']!=bound['A_launch_id'], 'Real separately bound A/B identity required')
    core=record(capture,'core_CPU_acceptance')
    registration=record(capture,'registration')
    authority=record(capture,'authorization')
    require(core['passed'] is True and capture['files']['core_CPU_acceptance']['sha256']==authority['core_CPU_proof_sha256']
            and all(registration['payload_sha256'].get(name)==expected
                    for name,expected in core['critical_source_sha256'].items()), 'Original B core CPU/source differs')
    require(registration['runtime_source_sha256']==record(record(package,'capture'),'registration')['runtime_source_sha256'],
            'B original pinned runtime differs from A')
    bound.update(A_model_sha256=original['model_sha256'],
                 A_precision=record(record(package,'capture'),'precision'))
    return bound


def original_identity(capture,card):
    launch=record(capture,'launch')
    registration=record(capture,'registration')
    authority=record(capture,'authorization')
    envelope=record(capture,'central_reservation')
    binding=record(capture,'launch_binding')
    require(launch['run_id']==RUN and launch['phase']=='B' and launch['physical_paths']==36
            and launch['whole_GPUh']==LIMITS[launch['host']] and launch['scope_sha256']==card['scope_sha256'],
            'Not the original registered B36 launch')
    require(launch['host'] in ('four_card','two_card') and registration['host']==launch['host']
            and registration['stage']==launch['stage']
            and registration['source_revision']==launch['source_revision'], 'Original host/source/stage differs')
    require(capture['files']['registration']['sha256']==launch['registration_sha256']
            and capture['files']['authorization']['sha256']==launch['authorization_sha256'],
            'Original launch byte identity differs')
    require(capture['payload_actual_sha256']==registration['payload_sha256']
            and capture['runtime_actual_sha256']==registration['runtime_source_sha256'],
            'Execution source or pinned runtime changed')
    require(capture['terminal_validator_sha256']==registration['payload_sha256'].get('src/wcomr/cara_fast_b36_terminal_r1.py'),
            'Terminal validator is not bound to the original stage')
    require(capture['capture_worker_sha256']==registration['payload_sha256'].get('src/wcomr/cara_fast_b36_capture_r1.py'),
            'Terminal capture worker is not bound to the original stage')
    require(authority['direct_user_authorization'] is True and bool(authority['user_quote'])
            and authority.get('new_B36_authorization') is True and authority.get('authorizes_replay') is False, 'Direct B36-only authority is absent')
    for key in ('run_id','phase','host','gpu_uuid','launch_id','source_revision','scope_sha256',
                'physical_paths','whole_GPUh','registration_sha256'):
        require(authority[key]==launch[key], 'Authority/launch differs: '+key)
    cpu=record(capture,'CPU_acceptance')
    require(cpu['passed'] is True and capture['files']['CPU_acceptance']['sha256']==authority['CPU_proof_sha256']
            and all(registration['payload_sha256'].get(name)==expected
                    for name,expected in cpu['critical_source_sha256'].items()), 'Bound affected CPU acceptance differs')
    require(envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True,
            'Original single central envelope required')
    job=envelope['job']
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256','stage',
                'registration_sha256','authorization_sha256'):
        require(job[key]==launch[key], 'Central envelope/launch differs: '+key)
    require(job['job_id']==RUN and job['physical_paths']==36 and job['phase']=='B' and job['billed_limit_GPUh']==LIMITS[launch['host']]
            and job['status']=='RESERVED_OR_RUNNING', 'Original B36 reservation differs')
    require(binding['authorization_sha256']==capture['files']['authorization']['sha256']
            and binding['central_reservation_sha256']==capture['files']['central_reservation']['sha256'],
            'Launch/envelope binding differs')
    bound=bound_A(capture,card)
    require(launch['model_sha256']==bound['A_model_sha256'], 'Original A/B checkpoint differs')
    for name in ('A_launch_id','frozen_file_sha256'):
        require(launch[name]==authority[name]==job[name], 'Original B handoff identity differs: '+name)
    require(binding['A_handoff_package_sha256']==bound['package_sha256'], 'B bound A package differs')
    return launch


def financial_terminal(capture,card):
    launch=original_identity(capture,card)
    require(capture['status']=='FAST_B36_TERMINAL_CAPTURE'
            and set(capture['original_live_handles'])==set(HANDLES)
            and all(value is False for value in capture['original_live_handles'].values())
            and capture['own_UUID_lock_free'] is True and capture['mode_owner_lock_free'] is True,
            'Recover original handles/locks before settling; unknown is not terminal')
    container=capture['container']
    require(container['state']['Status']=='exited' and not container['state']['Running']
            and container['image']==IMAGE and container['manifest_sha256']==launch['registration_sha256']
            and container['device_requests'][0]['DeviceIDs']==[launch['gpu_uuid']]
            and len(container['device_requests'])==1, 'Original container identity/terminal state differs')
    supervisor=record(capture,'supervisor')
    billing=record(capture,'billing')
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256','phase'):
        require(billing[key]==launch[key] and supervisor[key]==launch[key], 'Original bill/supervisor differs: '+key)
    require(billing['billed_limit_GPUh']==LIMITS[launch['host']] and finite(billing['wall_seconds'])
            and billing['wall_seconds']>0 and billing['actual_GPUh']==billing['wall_seconds']/3600,
            'Exact original measured wall bill required; no estimates or zero assumptions')
    return launch,billing


def settle_original(pool,capture,card):
    """Run only against the four-card central ledger, once original handles end."""
    launch,billing=financial_terminal(capture,card)
    before=pool.read()
    job=before['jobs'][RUN]
    for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256','stage',
                'registration_sha256','authorization_sha256'):
        require(job[key]==launch[key], 'Wrong central original job: '+key)
    require(job['billed_limit_GPUh']==LIMITS[launch['host']], 'Original card hard limit differs')
    bill_sha=capture['files']['billing']['sha256']
    after=pool.settle(RUN,billing['actual_GPUh'],bill_sha)
    require(before['cap_gpu_hours']==after['cap_gpu_hours']
            and set(before['jobs'])==set(after['jobs'])
            and all(after['jobs'][key]==value for key,value in before['jobs'].items() if key!=RUN),
            'Another job or the old uncertainty liability changed')
    return dict(central_ledger_host='four_card',job_id=RUN,launch_id=launch['launch_id'],
                billing_sha256=bill_sha,central_before=before,central_after=after,
                science_accepted=False,second_host_charge_created=False)


def audit_settlement(capture,card,settlement):
    launch,billing=financial_terminal(capture,card)
    before,after=settlement['central_before'],settlement['central_after']
    require(settlement['central_ledger_host']=='four_card' and settlement['job_id']==RUN
            and settlement['launch_id']==launch['launch_id']
            and settlement['billing_sha256']==capture['files']['billing']['sha256']
            and settlement['science_accepted'] is False and settlement['second_host_charge_created'] is False,
            'Central settlement identity differs')
    require(all(before[key]==after[key] for key in ('cap_gpu_hours','origin_used_gpu_hours','origin_gpu_jobs_launched'))
            and all(ledger[key]==value for ledger in (before,after)
                    for key,value in Pool.accounting(ledger).items()), 'Central origin/totals/cap differ')
    require(set(before['jobs'])==set(after['jobs'])
            and all(after['jobs'][key]==value for key,value in before['jobs'].items() if key!=RUN),
            'Unrelated original reservations changed')
    for ledger in (before,after):
        job=ledger['jobs'][RUN]
        for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256','stage',
                    'registration_sha256','authorization_sha256'):
            require(job[key]==launch[key], 'Settled job identity differs: '+key)
    job=after['jobs'][RUN]
    require(job['status']=='SETTLED' and job['actual_GPUh']==billing['actual_GPUh']
            and job['billing_sha256']==capture['files']['billing']['sha256'], 'Original central bill is not settled')
    return billing


def audit_monitor(rows,launch,supervisor,billing,ready,grant,pending):
    runner=supervisor['child_identity']
    require(rows and len(rows)==supervisor['observations'] and ready['identity']==grant['runner']==runner
            and ready['GPU_context_held'] is True and grant['gpu_uuid']==launch['gpu_uuid']
            and grant['source_revision']==ready['source_revision']==launch['source_revision'],
            'Complete original monitor/context binding required')
    last=0.
    active=False
    maximum_gap=0.
    maximum_temperature=0.
    for row in rows:
        elapsed=row['monotonic_elapsed']
        require(finite(elapsed) and elapsed>=last and elapsed-last<=MAX_MONITOR_GAP_SECONDS,
                'Invalid or interrupted original exclusive journal')
        maximum_gap=max(maximum_gap,elapsed-last)
        last=elapsed
        require(row['launch_id']==launch['launch_id'] and row['run_id']==RUN and row['runner']==runner,
                'Mixed monitor launch or runner')
        require(not active or row['context_granted'], 'Context grant regressed')
        active=active or row['context_granted']
        snapshot=row['snapshot']
        verdict=exclusive_gate(snapshot,gpu_uuid=launch['gpu_uuid'],
            phase='active' if active or snapshot['compute_apps'] else 'idle',runner=runner,now=snapshot['observed_unix'])
        require(verdict['observation_passed'], 'Foreign/unknown context or nonexclusive original monitor')
        temperature=float(row['thermal']['temperature.gpu'])
        require(math.isfinite(temperature) and temperature<90, 'Original thermal stop or invalid temperature')
        maximum_temperature=max(maximum_temperature,temperature)
    require(active and 0<=billing['wall_seconds']-last<=MAX_MONITOR_GAP_SECONDS,
            'Unmonitored original terminal interval')
    final=pending['final_snapshot']
    require(exclusive_gate(final,gpu_uuid=launch['gpu_uuid'],phase='idle',now=final['observed_unix'])['observation_passed'],
            'Original final CUDA context release was not verified')
    return dict(samples=len(rows),max_gap_seconds=maximum_gap,max_temperature_C=maximum_temperature)


def technical_terminal(capture,card):
    launch,billing=financial_terminal(capture,card)
    require(billing['actual_GPUh']<=LIMITS[launch['host']], 'Original B36 exceeded its whole hard limit')
    guardian=record(capture,'guardian')
    supervisor=record(capture,'supervisor')
    pending=record(capture,'pending_release')
    container=capture['container']
    require(guardian['status']=='FAST_B36_HOST_GUARDIAN_TERMINAL' and guardian['container_exit_code']==0
            and guardian['mode_restoration']['restored'] is True and not guardian.get('error_type')
            and all(guardian['identity'][key]==launch['guardian_identity'][key] for key in ('pid','start_ticks')),
            'Original host guardian did not finish and restore')
    require(all(guardian[key]==launch[key] for key in ('run_id','launch_id','gpu_uuid','source_revision')),
            'Original guardian launch differs')
    admitted=guardian['mode_admission']['verified_snapshot']
    require(exclusive_gate(admitted,gpu_uuid=launch['gpu_uuid'],phase='idle',now=admitted['observed_unix'])['observation_passed'],
            'Original idle hardware admission is not verified')
    require(supervisor['child_exit_code']==0 and supervisor['exclusive_monitor_accepted'] is True
            and not supervisor.get('error_type') and not supervisor.get('release_error')
            and container['state']['ExitCode']==0 and not container['state']['OOMKilled']
            and container['readonly_root'] and container['pid_mode']=='host' and container['network']=='none'
            and container['cpus']==2 and container['memory_GiB']==record(capture,'profile')['GPU_container']['memory_GiB'],
            'Original GPU execution failed')
    require(all(pending.get(key) is True for key in ('GPU_released','original_process_exited','technical_accepted'))
            and pending['cost_settled'] is False and pending['billing_sha256']==capture['files']['billing']['sha256'],
            'Original pending release differs')
    require(all(pending[key]==launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','scope_sha256')),
            'Original pending release launch differs')
    collection=record(capture,'collection')
    bound=bound_A(capture,card)
    require(record(capture,'precision')==bound['A_precision'], 'Actual B precision/backend differs from A')
    phase_sha=check_complete_B(card,collection,bound['frozen'],cpu_validation=False)
    require(phase_sha==pending['phase_state_sha256']==supervisor['phase_state_sha256'], 'Original B36 collection differs')
    schedules={row['requested_steps']:row['actual_updates'] for row in card['schedules']}
    requests={row['name']:row for row in card['inputs']}
    for row in collection['rows']:
        slot,result=row['slot'],row['result']
        concrete=result['concrete_role']
        updates=schedules[card['roles'][concrete]['requested_steps']]
        require(result['role']==slot['role']
                and result['solver_steps']==result['guided_pairs']==updates
                and result['audit_enabled']==slot['audit_enabled']
                and result['eligible_clean_time']==slot['eligible_clean_time'], 'Registered role/update/audit path differs')
        argument_file=capture['artifacts'][slot['id']]['arguments']
        arguments=record(dict(files={'arguments':argument_file}),'arguments')
        expected={key:value for key,value in requests[slot['member']].items() if key!='partition'}
        expected.update(seed=slot['seed'],num_steps=card['roles'][concrete]['requested_steps'])
        require(all(arguments.get(key)==value for key,value in expected.items()),
                'Actual saved inference arguments differ from the registered physical request')
    audit=capture['monitor_audit']
    require(audit['passed'] is True and audit['validator_sha256']==capture['terminal_validator_sha256'],
            'Independent complete monitor audit failed')
    artifacts=capture['artifacts']
    require(set(artifacts)=={row['slot']['id'] for row in collection['rows']}, 'Original B36 artifact denominator differs')
    for row in collection['rows']:
        saved=artifacts[row['slot']['id']]
        require(saved['video']['path']==row['result']['video_path'] and saved['video']['bytes']>0
                and saved['tensor']['path']==row['tensor_artifact']['path']
                and saved['tensor']['sha256']==row['tensor_artifact']['sha256']
                and saved['tensor']['bytes']==row['tensor_artifact']['bytes'], 'Original B36 artifact changed')
    return phase_sha


def released_terminal(capture,card,settlement):
    """A failed run can be financially released, but can never enter scoring."""
    billing=audit_settlement(capture,card,settlement)
    launch=record(capture,'launch')
    pending=record(capture,'pending_release')
    release=dict(phase='B',run_id=RUN,launch_id=launch['launch_id'],host=launch['host'],
        gpu_uuid=launch['gpu_uuid'],scope_sha256=card['scope_sha256'],
        original_process_exited=True,cost_settled=True,GPU_released=pending.get('GPU_released') is True,
        billing_sha256=capture['files']['billing']['sha256'],actual_GPUh=billing['actual_GPUh'],
        terminal_capture_sha256=digest(capture),central_settlement_sha256=digest(settlement),
        technical_accepted=False,authorizes_phase_B=False,authorizes_replay=False)
    try:
        release['phase_state_sha256']=technical_terminal(capture,card)
        release['technical_accepted']=True
    except (ValueError,KeyError,TypeError) as error:
        release['technical_failure']=str(error)
    return release
