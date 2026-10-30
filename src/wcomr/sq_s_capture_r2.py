"""Bounded original-handle S capture; live responses contain counts only."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

from .gpu_budget_pool_v2 import same_live_process,sha
from .policy_price_terminal_r1 import record
from .sq_s_execution_r2 import require,read
from .sq_s_spec_r2 import RUN,SCOPE,PROFILE,QUOTES,IDENTITY,RESOURCE,ASSETS,MODE,PHYSICAL,stage_path
from .sq_gpu_allocation_r1 import SystemOperations,container_record

MAX_METADATA=16*1024**2


def captured_file(path):
    path=Path(path)
    if not path.exists():return dict(path=str(path),exists=False)
    require(not path.is_symlink() and path.stat().st_size<=MAX_METADATA,'S metadata path/size differs')
    raw=path.read_bytes()
    return dict(path=str(path),exists=True,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),raw_utf8=raw.decode())


def lock_free(path):
    if not path.exists():return None
    descriptor=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
    try:
        try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return False
        fcntl.flock(descriptor,fcntl.LOCK_UN);return True
    finally:os.close(descriptor)


def capture(project,stage,launch_sha256):
    project,stage=Path(project),Path(stage)
    require(stage.parent==project/'.sync' and stage.name.startswith('cara-sq-s-complete-')
            and not stage.is_symlink(),'Original independent S stage required')
    output=project/'outputs'/RUN
    files={key:captured_file(stage/name) for key,name in dict(
        launch='GPU-launch.json',registration='registration.json',authorization='pg-GPU-authorization.json',
        CPU_acceptance='execution-CPU-proof.json',central_reservation='central-reservation.json',
        storage='history104-storage.json',asset_acceptance='S-asset-verification.json',
        launch_binding='launch-binding.json',guardian='pg-host-guardian.json',
        ready='pg-runner-context-ready.json',grant='pg-runner-context-granted.json').items()}
    require(files['launch'].get('sha256')==launch_sha256,'Recover exact original S launch bytes')
    value=dict(files=files);launch=record(value,'launch')
    require(stage==stage_path(project,launch['host']) and launch['run_id']==RUN and launch['stage']==str(stage)
            and launch['container']==stage.name+'-gpu','Original S launch/stage differs')
    files['supervisor']=captured_file(output/'S-supervisor.json')
    guardian=record(value,'guardian') if files['guardian']['exists'] else {}
    supervisor=record(value,'supervisor') if files['supervisor']['exists'] else {}
    identities=dict(guardian=launch['guardian_identity'],container_cli=guardian.get('container_cli_identity'),
        supervisor=supervisor.get('supervisor_identity'),runner=supervisor.get('child_identity'))
    live={key:same_live_process(ident) if ident and ident.get('start_ticks') is not None else None
          for key,ident in identities.items()}
    try:
        container=SystemOperations().inspect_container(stage,launch['registration_sha256'],launch['gpu_uuid'])
    except (RuntimeError,ValueError,KeyError,subprocess.SubprocessError):
        return dict(status='SQ_S_ORIGINAL_CONTAINER_UNKNOWN_RECOVER_ONLY',launch_id=launch['launch_id'],
            original_live_handles=live,scientific_rows_returned=False,GPU_submissions=0,ledger_writes=0)
    witness=guardian.get('container_terminal_witness',{})
    closed=(guardian.get('status')=='SQ_S_HOST_GUARDIAN_TERMINAL' and witness.get('complete') is True
            and ((container is None and witness.get('kind') in ('NO_CONTAINER_DISPATCH','ORIGINAL_CONTAINER_NEVER_CREATED'))
                 or (container is not None and witness.get('kind')=='BOUND_CONTAINER_TERMINAL'
                     and container['Id']==witness.get('container_id') and not container['State']['Running']
                     and container['State']['Pid']==0)))
    absence={}
    if closed:
        for key in ('container_cli','supervisor','runner'):
            if identities[key] is None:
                # This proves closure, not that an unrecorded worker never ran.
                live[key]=False;absence[key]='NO_PUBLISHED_HANDLE_IN_VERIFIED_ORIGINAL_TERMINAL'
    if not closed or any(item is not False for item in live.values()):
        health=read(output/'S-health.json') if (output/'S-health.json').exists() else {}
        allow=('status','run_id','launch_id','model_load_attempts','model_loads')
        matrix_health=health.get('matrix_health',{})
        health['attempted_new_paths']=len(matrix_health.get('attempted_new_role_ids',[]))
        allow=allow+('attempted_new_paths',)
        return dict(status='SQ_S_LIVE_OR_HANDLE_UNKNOWN_OPERATIONAL_ONLY',launch_id=launch['launch_id'],
            original_live_handles=live,container_state=container['State'] if container else None,
            health={key:health[key] for key in allow if key in health},
            scientific_rows_returned=False,GPU_submissions=0,ledger_writes=0)
    registration=record(value,'registration');host=launch['host']
    files.update({key:captured_file(stage/name) for key,name in (
        ('scope',SCOPE),('profile',PROFILE),('quote',QUOTES[host]),('identity',IDENTITY),
        ('resource',RESOURCE),('assets',ASSETS),('mode',MODE),('physical',PHYSICAL[host]))})
    files.update({key:captured_file(output/name) for key,name in (
        ('collection','S-collection.json'),('billing','S-billing.json'),
        ('pending_release','S-release-pending-central.json'),('allocation_release','S-allocation-release.json'),
        ('supervisor_billing','S-supervisor-billing-diagnostic.json'),
        ('supervisor_release','S-supervisor-release-diagnostic.json'))})
    no_exec=witness['kind']=='NO_CONTAINER_DISPATCH' and witness['dispatch_state'] in ('NOT_ATTEMPTED','SPAWN_FAILED_NO_EXEC')
    uuid_lock=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.lock'))
    mode_lock=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.mode-owner.lock'))
    if no_exec and uuid_lock is None:uuid_lock=True
    if no_exec and mode_lock is None and not guardian['mode_owner_fenced']:mode_lock=True
    observed_container=None
    if container is not None:
        config=container['HostConfig']
        observed_container=dict(container_record(container),id=container['Id'],
            cpuset_cpus=config['CpusetCpus'],memory_swap_GiB=config['MemorySwap']/2**30)
    value.update(status='SQ_S_TERMINAL_CAPTURE_R2',original_live_handles=live,
        own_UUID_lock_free=uuid_lock,mode_owner_lock_free=mode_lock,original_handle_absence_witness=absence,
        container=observed_container,container_observation='BOUND_ORIGINAL_CONTAINER' if container else 'DEFINITE_NO_SUCH_CONTAINER',
        payload_actual_sha256={name:sha(stage/name) for name in registration['payload_sha256']},
        runtime_actual_sha256={name:sha(project/'runtime'/name) for name in registration['runtime_source_sha256']},
        terminal_validator_sha256=sha(Path(__file__).with_name('sq_s_terminal_r2.py')),
        capture_worker_sha256=sha(__file__),scientific_rows_returned=True,
        GPU_submissions=0,ledger_writes=0)
    monitor=output/'S-exclusive-monitor.jsonl'
    if monitor.exists():
        from .sq_s_monitor_terminal_r2 import check_monitor
        try:
            value['monitor_witness']=check_monitor(monitor,launch,record(value,'supervisor'),
                record(value,'supervisor_billing'),record(value,'ready'),record(value,'grant'),
                maximum_bytes=record(value,'profile')['monitor_file_MiB_max']*2**20)
        except (ValueError,KeyError,TypeError,OSError) as error:
            value['monitor_witness']=dict(accepted=False,error_type=type(error).__name__,error=str(error),
                path=str(monitor),raw_monitor_transferred=False)
    else:value['monitor_witness']=dict(accepted=False,exists=False,raw_monitor_transferred=False)
    return value
