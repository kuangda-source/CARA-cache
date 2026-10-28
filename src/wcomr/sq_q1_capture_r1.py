"""Bounded original-handle Q1 capture; live responses contain counts only."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

from .gpu_budget_pool_v2 import same_live_process,sha
from .policy_price_terminal_r1 import record
from .sq_q1_execution_r1 import require,read
from .sq_q1_spec_r1 import RUN,SCOPE,PROFILE,QUOTES

MAX_METADATA=16*1024**2


def captured_file(path):
    path=Path(path)
    if not path.exists():return dict(path=str(path),exists=False)
    require(not path.is_symlink() and path.stat().st_size<=MAX_METADATA,'Q1 metadata path/size differs')
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
    require(stage.parent==project/'.sync' and stage.name.startswith('cara-sq-q1-saved-')
            and not stage.is_symlink(),'Original independent Q1 stage required')
    output=project/'outputs'/RUN
    files={key:captured_file(stage/name) for key,name in dict(
        launch='GPU-launch.json',registration='registration.json',authorization='pg-GPU-authorization.json',
        CPU_acceptance='execution-CPU-proof.json',central_reservation='central-reservation.json',
        storage='history104-storage.json',
        launch_binding='launch-binding.json',guardian='pg-host-guardian.json',
        ready='pg-runner-context-ready.json',grant='pg-runner-context-granted.json').items()}
    require(files['launch'].get('sha256')==launch_sha256,'Recover exact original Q1 launch bytes')
    value=dict(files=files);launch=record(value,'launch')
    require(launch['run_id']==RUN and launch['stage']==str(stage)
            and launch['container']==stage.name+'-gpu','Original Q1 launch/stage differs')
    files['supervisor']=captured_file(output/'Q1-supervisor.json')
    guardian=record(value,'guardian') if files['guardian']['exists'] else {}
    supervisor=record(value,'supervisor') if files['supervisor']['exists'] else {}
    identities=dict(guardian=launch['guardian_identity'],container_cli=guardian.get('container_cli_identity'),
        supervisor=supervisor.get('supervisor_identity'),runner=supervisor.get('child_identity'))
    live={key:same_live_process(ident) if ident and ident.get('start_ticks') is not None else None
          for key,ident in identities.items()}
    inspected=subprocess.run(['docker','inspect',launch['container']],capture_output=True,text=True,timeout=20)
    if inspected.returncode:
        return dict(status='SQ_Q1_ORIGINAL_CONTAINER_UNKNOWN_RECOVER_ONLY',launch_id=launch['launch_id'],
            original_live_handles=live,scientific_rows_returned=False,GPU_submissions=0,ledger_writes=0)
    container=json.loads(inspected.stdout)[0]
    require(container['Config']['Labels'].get('wcomr.manifest')==launch['registration_sha256'],
            'Observed container is not the original Q1 manifest')
    if container['State']['Running'] or any(item is not False for item in live.values()):
        health=read(output/'Q1-health.json') if (output/'Q1-health.json').exists() else {}
        allow=('status','run_id','launch_id','completed_states','expected_states','formal_C_pairs_completed',
               'head_calls','scientific_selection','verified_files','total_files')
        return dict(status='SQ_Q1_LIVE_OR_HANDLE_UNKNOWN_OPERATIONAL_ONLY',launch_id=launch['launch_id'],
            original_live_handles=live,container_state=container['State'],
            health={key:health[key] for key in allow if key in health},
            scientific_rows_returned=False,GPU_submissions=0,ledger_writes=0)
    registration=record(value,'registration');host=launch['host']
    files.update({key:captured_file(stage/name) for key,name in (
        ('scope',SCOPE),('profile',PROFILE),('quote',QUOTES[host]))})
    files.update({key:captured_file(output/name) for key,name in (
        ('collection','Q1-collection.json'),('billing','Q1-billing.json'),
        ('pending_release','Q1-release-pending-central.json'))})
    config=container['HostConfig']
    value.update(status='SQ_Q1_TERMINAL_CAPTURE_R1',original_live_handles=live,
        own_UUID_lock_free=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.lock')),
        mode_owner_lock_free=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.mode-owner.lock')),
        container=dict(state=container['State'],image=container['Image'],
            manifest_sha256=container['Config']['Labels'].get('wcomr.manifest'),
            device_requests=config['DeviceRequests'],readonly_root=config['ReadonlyRootfs'],
            pid_mode=config['PidMode'],network=config['NetworkMode'],cpus=config['NanoCpus']/10**9,
            cpuset_cpus=config['CpusetCpus'],memory_GiB=config['Memory']/2**30,
            memory_swap_GiB=config['MemorySwap']/2**30),
        payload_actual_sha256={name:sha(stage/name) for name in registration['payload_sha256']},
        runtime_actual_sha256={name:sha(project/'runtime'/name) for name in registration['runtime_source_sha256']},
        terminal_validator_sha256=sha(Path(__file__).with_name('sq_q1_terminal_r1.py')),
        capture_worker_sha256=sha(__file__),scientific_rows_returned=True,
        GPU_submissions=0,ledger_writes=0)
    monitor=output/'Q1-exclusive-monitor.jsonl'
    if monitor.exists():
        require(monitor.stat().st_size<=MAX_METADATA and not monitor.is_symlink(),'Q1 monitor size/path differs')
        value.update(monitor_raw_utf8=monitor.read_text(),monitor_sha256=sha(monitor))
    else:value.update(monitor_raw_utf8='',monitor_sha256=hashlib.sha256(b'').hexdigest())
    return value
