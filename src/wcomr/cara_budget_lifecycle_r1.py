"""Read-only prospective calibration closure; no dispatch or ledger mutation.

The caller supplies the launch SHA retained at dispatch. Financial closure and
resource release remain separate from complete-search scientific acceptance.
"""
from .cara_budget_original_handles_r1 import ROLES
from .gpu_budget_pool_v2 import BudgetPool, finite, sha
from .policy_asset_price_review_r1 import exclusive_gate
from .policy_price_terminal_r1 import record, require

SOURCE = 'src/wcomr/cara_budget_lifecycle_r1.py'
IDENTITY = ('run_id', 'launch_id', 'host', 'gpu_uuid', 'stage',
            'source_revision', 'scope_sha256', 'billed_limit_GPUh')
JOB_IDENTITY = IDENTITY + ('registration_sha256', 'authorization_sha256')


def financial_terminal(capture, expected_launch_sha256, *, cpu_validation=False):
    """Validate captured original bytes, including failed allocations."""
    require(capture['files']['launch']['sha256'] == expected_launch_sha256,
            'Recover the dispatch-bound original launch')
    launch = record(capture, 'launch')
    require(launch['CPU_fixture_only'] is cpu_validation,
            'CPU fixtures cannot certify a production allocation')
    require(launch['host'] in ('four_card', 'two_card')
            and finite(launch['billed_limit_GPUh']) and launch['billed_limit_GPUh'] > 0,
            'Original registered host and whole limit required')
    registration = record(capture, 'registration')
    authority = record(capture, 'authorization')
    for key in ('registration', 'authorization'):
        require(capture['files'][key]['sha256'] == launch[key + '_sha256'],
                'Original registration or authorization bytes differ')
    require(all(authority[k] == launch[k] for k in IDENTITY)
            and authority['execution_authorized'] is True
            and authority['authorizes_replay'] is False
            and authority['CPU_fixture_only'] is cpu_validation,
            'Original execution scope or authority differs')
    require(all(registration[k] == launch[k] for k in ('host', 'stage', 'source_revision'))
            and registration['payload_sha256'] == capture['payload_actual_sha256']
            and registration['runtime_source_sha256'] == capture['runtime_actual_sha256']
            and registration['payload_sha256'][SOURCE] == sha(__file__),
            'Original execution/runtime/validator source differs')
    envelope = record(capture, 'central_reservation')
    job = envelope['job']
    require(envelope['central_ledger_host'] == 'four_card'
            and capture['files']['central_reservation']['sha256'] == launch['central_reservation_sha256']
            and job['job_id'] == launch['run_id'] and job['status'] == 'RESERVED_OR_RUNNING'
            and all(job[k] == launch[k] for k in JOB_IDENTITY),
            'Original single central reservation differs')
    guardian = record(capture, 'guardian')
    require(guardian['status'] == 'BUDGET_CALIBRATION_GUARDIAN_TERMINAL'
            and all(guardian[k] == launch[k] for k in IDENTITY)
            and guardian['original_handles']['guardian'] == launch['guardian_identity'],
            'Original guardian identity or terminal is absent')
    witness = guardian['container_terminal_witness']
    require(witness['complete'] is True, 'Original container closure remains unknown')
    kind = witness['kind']
    require(kind in ('NO_CONTAINER_DISPATCH', 'ORIGINAL_CONTAINER_NEVER_CREATED', 'BOUND_CONTAINER_TERMINAL'),
            'Unknown container closure kind')
    container = capture['container']
    no_container = kind != 'BOUND_CONTAINER_TERMINAL'
    if no_container:
        require(container is None and not any(capture['files'][k]['exists'] for k in
                ('supervisor_start', 'runner_intent', 'runner_start')),
                'No-container closure conflicts with worker evidence')
        if kind == 'NO_CONTAINER_DISPATCH':
            require(guardian['container_dispatch_state'] in ('NOT_ATTEMPTED', 'SPAWN_FAILED_NO_EXEC'),
                    'A dispatch attempt cannot be silently erased')
        else:
            require(guardian['container_dispatch_state'] == 'STARTED',
                    'Missing container requires the original ended CLI')
    else:
        require(container == witness['container'] and container['id'] == witness['container_id']
                and container['name'] == launch['container']
                and container['image'] == registration['container_image']
                and container['manifest_sha256'] == launch['registration_sha256']
                and container['device_ids'] == [launch['gpu_uuid']]
                and container['state']['Status'] in ('created', 'exited')
                and container['state']['Running'] is False and container['state']['Pid'] == 0,
                'Original container identity or terminal state differs')
    observations = capture['process_observations']
    handles = guardian['original_handles']
    require(set(handles) == set(observations) == set(ROLES), 'All original process roles required')
    present = [h for h in handles.values() if h is not None]
    require(len({(h['pid'], h['start_ticks']) for h in present}) == len(present),
            'Distinct original process roles required')
    for role in ROLES:
        handle, observation = handles[role], observations[role]
        if handle is None:
            never_dispatched = (no_container and role in ('supervisor', 'runner')) or (
                kind == 'NO_CONTAINER_DISPATCH' and role == 'container_cli')
            # Bound container init may fail before either worker starts.
            init_failed = (not no_container and role in ('supervisor', 'runner')
                and not capture['files']['runner_intent']['exists']
                and not capture['files'][role + '_start']['exists'])
            require((never_dispatched or init_failed) and observation is None,
                    'Missing original identity is not evidence of exit')
            continue
        require(handle['host_view'] == launch['guardian_identity']['host_view']
                and type(handle['pid']) is int and handle['pid'] > 0
                and type(handle['start_ticks']) is int and handle['start_ticks'] > 0
                and observation['original_pid'] == handle['pid']
                and observation['original_start_ticks'] == handle['start_ticks']
                and observation['observed_host_view'] == handle['host_view']
                and observation['original_live'] is False
                and observation['status'] == 'ORIGINAL_NOT_LIVE',
                'Original process live, unknown or observed in another host view')
        if role in ('supervisor', 'runner'):
            require(record(capture, role + '_start')['identity'] == handle,
                    'Guardian and original worker-start identities differ')
        current = observation['observed_process']
        reason = observation['reason']
        require(current['pid'] == handle['pid'] and (
            (reason == 'ORIGINAL_PROC_ABSENT' and current['state'] is None and current['start_ticks'] is None)
            or (reason == 'PID_REUSED_ORIGINAL_PROCESS_EXITED' and type(current['start_ticks']) is int
                and current['start_ticks'] > 0 and current['start_ticks'] != handle['start_ticks'])
            or (reason == 'ORIGINAL_PROCESS_ZOMBIE_OR_DEAD' and current['state'] in ('Z', 'X')
                and current['start_ticks'] == handle['start_ticks'])), 'Unsubstantiated original exit')
    # A guardian that failed before any allocation cannot own either lock.
    # Missing files alone never prove this: require the terminal source-bound
    # event history and absence of every child/dispatch instead.
    never_acquired=guardian.get('allocation_never_attempted_witness')
    if never_acquired is not None:
        require(isinstance(never_acquired,dict)
                and set(never_acquired)=={'mode_lock_attempted','device_lease_attempted',
                                         'mode_change_attempted','container_dispatch_attempted'}
                and all(value is False for value in never_acquired.values())
                and kind=='NO_CONTAINER_DISPATCH' and guardian['container_dispatch_state']=='NOT_ATTEMPTED'
                and guardian['GPU_mode_change_attempted'] is False
                and guardian.get('mode_owner_fenced') is False and bool(guardian.get('error_type'))
                and all(handles[role] is None for role in ('container_cli','supervisor','runner')),
                'A never-acquired witness cannot erase attempted allocation or execution')
    else:
        require(capture['own_UUID_lock_free'] is True and capture['mode_owner_lock_free'] is True,
                'Original resource lock closure unknown')
    billing = record(capture, 'billing')
    require(all(billing[k] == launch[k] for k in IDENTITY)
            and guardian['billing_sha256'] == capture['files']['billing']['sha256']
            and billing['billing_clock_owner'] == 'HOST_GUARDIAN'
            and billing['wall_interval_complete'] is True
            and all(finite(billing[k]) for k in ('started_monotonic', 'ended_monotonic', 'wall_seconds', 'actual_GPUh'))
            and 0 <= billing['started_monotonic'] < billing['ended_monotonic']
            and billing['started_monotonic'] == guardian['started_monotonic']
            and billing['ended_monotonic'] == guardian['ended_monotonic']
            and billing['wall_seconds'] == billing['ended_monotonic'] - billing['started_monotonic']
            and billing['actual_GPUh'] == billing['wall_seconds'] / 3600,
            'Exact complete original guardian bill required')
    return launch, billing


def audit_settlement(capture, expected_launch_sha256, settlement, *, cpu_validation=False):
    """Read the one central before/after receipt, never write a ledger."""
    launch, billing = financial_terminal(capture, expected_launch_sha256, cpu_validation=cpu_validation)
    before, after = settlement['central_before'], settlement['central_after']
    require(settlement['central_ledger_host'] == 'four_card'
            and settlement['launch_id'] == launch['launch_id']
            and settlement['billing_sha256'] == capture['files']['billing']['sha256'],
            'Original central settlement identity differs')
    require(all(before[k] == after[k] for k in ('cap_gpu_hours', 'origin_used_gpu_hours', 'origin_gpu_jobs_launched'))
            and set(before['jobs']) == set(after['jobs'])
            and all(after['jobs'][k] == v for k, v in before['jobs'].items() if k != launch['run_id']),
            'Unrelated jobs, old liability or central origin changed')
    for ledger in (before, after):
        require(all(ledger[k] == v for k, v in BudgetPool.accounting(ledger).items()), 'Incorrect central totals')
        job = ledger['jobs'][launch['run_id']]
        require(job['job_id'] == launch['run_id'] and all(job[k] == launch[k] for k in JOB_IDENTITY),
                'Central job differs from original launch')
    job = after['jobs'][launch['run_id']]
    require(job['status'] == 'SETTLED' and job['actual_GPUh'] == billing['actual_GPUh']
            and job['billing_sha256'] == capture['files']['billing']['sha256'],
            'Original guardian charge is not settled')
    require(billing['actual_GPUh'] <= launch['billed_limit_GPUh']
            or after.get('budget_overrun_recorded') is True, 'Actual budget overrun must remain recorded')
    original_job = before['jobs'][launch['run_id']]
    settlement_fields = {'status', 'actual_GPUh', 'billing_sha256', 'settled_unix'}
    require(all(job.get(k) == v for k, v in original_job.items() if k not in settlement_fields),
            'Settlement changed original job metadata')
    if original_job['status'] == 'SETTLED':
        require(before == after, 'Repeated acceptance must not create another settlement')
    else:
        require(after['events'][:-1] == before['events']
                and after['events'][-1]['type'] == 'SETTLE_ACTUAL_ADDITIVELY'
                and after['events'][-1]['job_id'] == launch['run_id'], 'Exactly one original settlement event required')
    return billing


def released_lifecycle(capture, expected_launch_sha256, settlement, *, cpu_validation=False):
    """Financial and release evidence only; complete-search acceptance is separate."""
    billing = audit_settlement(capture, expected_launch_sha256, settlement, cpu_validation=cpu_validation)
    launch = record(capture, 'launch')
    guardian = record(capture, 'guardian')
    container = capture['container']
    no_container = guardian['container_terminal_witness']['kind'] != 'BOUND_CONTAINER_TERMINAL'
    restored = guardian['mode_restoration']['restored'] is True
    if guardian['GPU_mode_change_attempted']:
        snapshot = guardian['mode_restoration'].get('snapshot', {})
        restored = restored and (snapshot.get('gpu_uuid') == launch['gpu_uuid']
            and snapshot.get('compute_mode') == 'Default' and snapshot.get('compute_apps') == []
            and snapshot.get('mps_processes') == [])
    released = no_container
    if not no_container and capture['files']['pending_release']['exists']:
        pending = record(capture, 'pending_release')
        require(all(pending[k] == launch[k] for k in IDENTITY), 'Original final release identity differs')
        final = pending['final_snapshot']
        released = exclusive_gate(final, gpu_uuid=launch['gpu_uuid'], phase='idle',
                                 now=final['observed_unix'])['observation_passed']
    exceeded = billing['actual_GPUh'] > launch['billed_limit_GPUh']
    execution_success = (not no_container and restored and released and not exceeded
        and container['state']['ExitCode'] == 0 and not container['state']['OOMKilled']
        and guardian['container_exit_code'] == 0 and not guardian.get('error_type'))
    return dict(status='ORIGINAL_LIFECYCLE_AUDITED_NOT_SCIENTIFIC_ACCEPTANCE',
        launch_id=launch['launch_id'],actual_GPUh=billing['actual_GPUh'],cost_settled=True,
        original_processes_ended=True,GPU_released=released,mode_restored=restored,
        container_exit_success=execution_success,hard_limit_exceeded=exceeded,
        complete_search_accepted=False,scientific_read_allowed=False,dispatch_allowed=False,
        authorizes_replay=False,CPU_fixture_only=cpu_validation,GPU_submissions=0,ledger_written=False)
