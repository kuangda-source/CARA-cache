"""Read one original A32 handle; never return partial scientific rows while live."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from datetime import datetime

from .cara_fast_execution_r2 import RUN,require,PROFILE
from .cara_fast_terminal_r2 import audit_monitor
from .gpu_budget_pool_v2 import atomic_json,process_identity,same_live_process
from .policy_price_terminal_r1 import record
from .wc73_exclusive_r1 import observe

MAX_METADATA_BYTES=16*1024**2
MAX_ARTIFACT_BYTES=32*1024**3


def file_sha(path):
    require(Path(path).is_file(), 'Hash only an original regular file')
    value=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(4*1024**2),b''):
            value.update(chunk)
    return value.hexdigest()


def captured_file(path):
    path=Path(path)
    if not path.exists():
        return dict(path=str(path),exists=False)
    require(path.is_file() and not path.is_symlink(), 'Metadata must be the original regular file')
    require(path.stat().st_size<=MAX_METADATA_BYTES, 'Metadata resource bound exceeded')
    raw=path.read_bytes()
    return dict(path=str(path),exists=True,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),raw_utf8=raw.decode())


def lock_free(path):
    if not path.exists():
        return None
    descriptor=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        fcntl.flock(descriptor,fcntl.LOCK_UN)
        return True
    finally:
        os.close(descriptor)


def recover_reader(stage,expected_launch_sha256):
    intent=json.loads((stage/'A-terminal-capture-intent.json').read_text())
    require(intent['launch_sha256']==expected_launch_sha256
            and intent['capture_worker_sha256']==file_sha(__file__), 'Different original terminal reader')
    complete=stage/'A-terminal-capture.json'
    if complete.exists():
        result=json.loads(complete.read_text())
        require(result['capture_identity']==intent['identity'], 'Original reader result identity differs')
        return result
    running=same_live_process(intent['identity'])
    return dict(status='FAST_A32_TERMINAL_READER_LIVE' if running else 'FAST_A32_TERMINAL_READER_STOPPED_NO_RETRY',
                capture_identity=intent['identity'],scientific_rows_returned=False,
                GPU_submissions=0,ledger_written=False)


def capture_terminal(project,stage,expected_launch_sha256):
    project,stage=Path(project),Path(stage)
    require(stage.parent==project/'.sync' and stage.name.startswith('cara-fast-cal-a32-')
            and not stage.is_symlink(), 'Use the original manifest-bound A32 stage')
    if (stage/'A-terminal-capture-intent.json').exists():
        return recover_reader(stage,expected_launch_sha256)
    output=project/'outputs'/RUN
    files={key:captured_file(stage/name) for key,name in dict(
        launch='GPU-launch.json',registration='registration.json',authorization='pg-GPU-authorization.json',
        CPU_acceptance='execution-CPU-proof.json',central_reservation='central-reservation.json',
        launch_binding='launch-binding.json',profile=PROFILE,guardian='pg-host-guardian.json',
        ready='pg-runner-context-ready.json',grant='pg-runner-context-granted.json').items()}
    require(files['launch'].get('sha256')==expected_launch_sha256, 'Recover the original launch receipt')
    value=dict(files=files)
    launch=record(value,'launch')
    require(launch['stage']==str(stage) and launch['run_id']==RUN
            and launch['container']==stage.name+'-gpu'
            and re.fullmatch(r'GPU-[A-Za-z0-9-]+',launch['gpu_uuid']), 'Original launch path/UUID differs')
    files['supervisor']=captured_file(output/'A-supervisor.json')
    guardian=record(value,'guardian') if files['guardian']['exists'] else {}
    supervisor=record(value,'supervisor') if files['supervisor']['exists'] else {}
    identities=dict(guardian=launch['guardian_identity'],container_cli=guardian.get('container_cli_identity'),
                    supervisor=supervisor.get('supervisor_identity'),runner=supervisor.get('child_identity'))
    live={key:same_live_process(identity) if identity and identity.get('start_ticks') is not None else None
          for key,identity in identities.items()}
    inspected=subprocess.run(['docker','inspect',launch['container']],capture_output=True,text=True,timeout=20)
    if inspected.returncode:
        return dict(status='FAST_A32_HANDLE_UNKNOWN',launch_id=launch['launch_id'],
                    original_live_handles=live,reason='Original container observation unavailable',
                    scientific_rows_returned=False,GPU_submissions=0,ledger_written=False)
    container=json.loads(inspected.stdout)[0]
    if container['State']['Running'] or any(item is not False for item in live.values()):
        return dict(status='FAST_A32_LIVE_OR_HANDLE_UNKNOWN_OPERATIONAL_ONLY',launch_id=launch['launch_id'],
                    original_live_handles=live,container_state=container['State'],
                    scientific_rows_returned=False,GPU_submissions=0,ledger_written=False)
    intent=dict(launch_sha256=expected_launch_sha256,identity=process_identity(os.getpid()),
                capture_worker_sha256=file_sha(__file__),started_unix=time.time(),
                declared_CPU_bound=dict(cpus=1,memory_GiB=1,work_seconds=900))
    try:
        with (stage/'A-terminal-capture-intent.json').open('x') as handle:
            json.dump(intent,handle)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        return recover_reader(stage,expected_launch_sha256)
    try:
        registration=record(value,'registration')
        files.update({key:captured_file(output/name) for key,name in dict(
            collection='A-collection.json',billing='A-billing.json',pending_release='A-release-pending-central.json',
            precision='A-model-precision.json',runner='A-runner.json').items()})
        config=container['HostConfig']
        # Availability after the original job released its context is a separate
        # observation. A later user's job or a transient probe failure cannot
        # invalidate the original final-idle/handle evidence or block its bill.
        try:
            current_gpu=observe(launch['gpu_uuid'])
        except (OSError,subprocess.SubprocessError,ValueError) as error:
            current_gpu=dict(observation_unavailable=True,error_type=type(error).__name__,error=str(error))
        value.update(status='FAST_A32_TERMINAL_CAPTURE',original_live_handles=live,
            own_UUID_lock_free=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.lock')),
            mode_owner_lock_free=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.mode-owner.lock')),
            container=dict(state=container['State'],image=container['Image'],
                manifest_sha256=container['Config']['Labels'].get('wcomr.manifest'),
                device_requests=config['DeviceRequests'],readonly_root=config['ReadonlyRootfs'],
                pid_mode=config['PidMode'],network=config['NetworkMode'],
                cpus=config['NanoCpus']/10**9,memory_GiB=config['Memory']/1024**3),
            payload_actual_sha256={name:file_sha(stage/name) for name in registration['payload_sha256']},
            runtime_actual_sha256={name:file_sha(project/'runtime'/name) for name in registration['runtime_source_sha256']},
            terminal_validator_sha256=file_sha(Path(__file__).with_name('cara_fast_terminal_r2.py')),
            capture_worker_sha256=file_sha(__file__),
            current_GPU_snapshot=current_gpu,
            current_GPU_availability_is_not_a_new_admission=True,
            artifacts={},artifact_errors={},GPU_submissions=0,ledger_written=False)
        monitor=output/'A-exclusive-monitor.jsonl'
        try:
            require(monitor.stat().st_size<=MAX_METADATA_BYTES, 'Monitor resource bound exceeded')
            rows=[json.loads(line) for line in monitor.read_text().splitlines()]
            require(len(rows)<=10000, 'Original monitor row bound exceeded')
            audit=audit_monitor(rows,launch,supervisor,record(value,'billing'),
                                record(value,'ready'),record(value,'grant'),record(value,'pending_release'))
            value['monitor_audit']=dict(audit,passed=True,path=str(monitor),sha256=file_sha(monitor),
                validator_sha256=value['terminal_validator_sha256'])
        except (OSError,ValueError,KeyError,TypeError) as error:
            value['monitor_audit']=dict(passed=False,path=str(monitor),error=str(error),
                validator_sha256=value['terminal_validator_sha256'])
        # A corrupt or partial artifact must not prevent settlement of its real bill.
        checked={}
        scanned_bytes=0
        collection=record(value,'collection') if files['collection']['exists'] else dict(rows=[])
        for row in collection['rows']:
            slot=row['slot']['id']
            if row['status']!='COMPLETE':
                continue
            try:
                video=Path(row['result']['video_path'])
                tensor=Path(row['tensor_artifact']['path'])
                require(video.parent==output/'A'/slot and tensor==output/'A'/(slot+'.pt'),
                        'Artifact is outside its registered physical slot')
                saved={}
                for kind,path in [('video',video),('tensor',tensor)]:
                    require(not path.is_symlink() and output.resolve() in path.resolve().parents,
                            'Artifact path escapes the original output')
                    if path not in checked:
                        size=path.stat().st_size
                        require(scanned_bytes+size<=MAX_ARTIFACT_BYTES, 'Artifact verification resource bound exceeded')
                        checked[path]=dict(path=str(path),bytes=size,sha256=file_sha(path))
                        scanned_bytes+=size
                    saved[kind]=checked[path]
                saved['arguments']=captured_file(video.with_suffix('.json'))
                value['artifacts'][slot]=saved
            except (OSError,ValueError,KeyError,TypeError) as error:
                value['artifact_errors'][slot]=str(error)
        value['artifact_bytes_read']=scanned_bytes
        value['scientific_rows_returned']=True
        value['capture_identity']=intent['identity']
        atomic_json(stage/'A-terminal-capture.json',value)
        return value
    except BaseException as error:
        atomic_json(stage/'A-terminal-capture-failure.json',dict(error_type=type(error).__name__,error=str(error),identity=intent['identity']))
        raise


def capture_scores(project,stage,manifest_path,expected_manifest_sha256):
    """Observe the unique post-release CPU scorer; live receipts expose no scores."""
    from .cara_fast_post_r2 import SCORER_SOURCES
    project,stage,manifest_path=Path(project),Path(stage),Path(manifest_path)
    require(stage.parent==project/'.sync' and stage.name.startswith('cara-fast-cal-a32-')
            and manifest_path.parent==project/'outputs'/RUN/'A-score-CPU', 'Original scoring stage/path required')
    require(file_sha(manifest_path)==expected_manifest_sha256, 'Original scoring manifest changed')
    manifest=json.loads(manifest_path.read_text())
    require(manifest['run_id']==RUN and set(manifest['scorer_source_sha256'])==set(SCORER_SOURCES),
            'Original A32 scoring source scope differs')
    require(Path(manifest['manifest_path'])==manifest_path, 'Original scoring manifest path differs')
    inspected=subprocess.run(['docker','inspect',stage.name+'-A-score-cpu'],capture_output=True,text=True,timeout=20)
    if inspected.returncode:
        return dict(status='FAST_A32_SCORE_HANDLE_UNKNOWN',scientific_rows_returned=False,GPU_submissions=0)
    container=json.loads(inspected.stdout)[0]
    if container['State']['Running']:
        return dict(status='FAST_A32_SCORE_LIVE_OPERATIONAL_ONLY',container_state=container['State'],
                    scientific_rows_returned=False,GPU_submissions=0)
    def stamp(value):
        value=re.sub(r'(\.\d{6})\d+(?=Z|[+-])',r'\1',value)
        return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    state=container['State']
    config=container['HostConfig']
    execution=dict(container_state=state,
        host_config={key:config[key] for key in ('NanoCpus','Memory','DeviceRequests','NetworkMode','ReadonlyRootfs')},
        manifest_sha256=expected_manifest_sha256,
        manifest_label_sha256=container['Config']['Labels'].get('wcomr.manifest'),
        source_actual_sha256={name:file_sha(stage/name) for name in SCORER_SOURCES},
        container_wall_seconds=stamp(state['FinishedAt'])-stamp(state['StartedAt']))
    return dict(status='FAST_A32_SCORE_TERMINAL_CAPTURE',execution=execution,
                files=dict(scores=captured_file(manifest_path.parent/'scores.json')),
                scientific_rows_returned=True,GPU_submissions=0,ledger_written=False)
