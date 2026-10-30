"""Read only the original calibration's operational and lifecycle metadata.

No query results, RGB, scores, mode changes, process signals or ledger writes.
Production deployment still requires the source-bound guardian/card integration.
"""
import json
from pathlib import Path
import re
import subprocess
import time

from .cara_budget_original_handles_r1 import ROLES, observe_original_process
from .cara_fast_b36_capture_r1 import captured_file, file_sha, lock_free
from .policy_price_terminal_r1 import record, require

SOURCE='src/wcomr/cara_budget_lifecycle_capture_r1.py'
METADATA={
    'launch':'GPU-launch.json', 'registration':'registration.json',
    'authorization':'GPU-authorization.json', 'central_reservation':'central-reservation.json',
    'guardian':'guardian.json', 'supervisor_start':'supervisor-start.json',
    'runner_intent':'runner-intent.json', 'runner_start':'runner-start.json',
    'billing':'billing.json', 'pending_release':'release-pending-central.json',
}


def inspect_container(name):
    result=subprocess.run(['docker','inspect','--type','container',name],capture_output=True,text=True,timeout=20)
    if result.returncode:
        if result.returncode==1 and result.stderr.strip() in (
                'Error: No such object: '+name,'Error: No such container: '+name,
                'Error response from daemon: No such container: '+name):
            return None
        raise RuntimeError('Original Docker observation unavailable')
    rows=json.loads(result.stdout)
    require(len(rows)==1,'Exactly one original container required')
    actual=rows[0];devices=actual['HostConfig']['DeviceRequests']
    require(isinstance(devices,list) and len(devices)==1,'Original single GPU request required')
    return dict(id=actual['Id'],name=actual['Name'].lstrip('/'),image=actual['Image'],
        manifest_sha256=actual['Config']['Labels'].get('wcomr.manifest'),device_ids=devices[0]['DeviceIDs'],
        state=actual['State'])


def capture_lifecycle(project, stage, expected_launch_sha256):
    project,stage=Path(project).resolve(),Path(stage)
    require(stage.is_absolute() and not stage.is_symlink() and stage.parent==project/'.sync'
            and stage.name.startswith('cara-budget-calibration-GPU-'), 'Original registered GPU stage required')
    launch_file=captured_file(stage/METADATA['launch'])
    require(launch_file.get('sha256')==expected_launch_sha256,'Original dispatch-bound launch SHA required')
    capture=dict(files={'launch':launch_file})
    launch=record(capture,'launch')
    require(launch['stage']==str(stage) and launch['container']==stage.name+'-gpu'
            and re.fullmatch(r'GPU-[A-Za-z0-9-]+',launch['gpu_uuid']),
            'Original stage and container name differ')
    operational=dict(status='ORIGINAL_CALIBRATION_LIVE_OR_UNKNOWN',launch_id=launch['launch_id'],
        observed_unix=time.time(),scientific_rows_returned=False,GPU_submissions=0,ledger_written=False)
    # Read only start/guardian metadata until the original physical lifetime is
    # resolved. A partial query journal or scientific result is never opened.
    capture['files']['guardian']=captured_file(stage/METADATA['guardian'])
    if not capture['files']['guardian']['exists']:
        return dict(operational,reason='ORIGINAL_GUARDIAN_NOT_RECORDED')
    guardian=record(capture,'guardian')
    require(all(guardian[k]==launch[k] for k in ('run_id','launch_id','host','gpu_uuid','stage','source_revision')),
            'Original guardian launch differs')
    handles=guardian['original_handles']
    require(set(handles)==set(ROLES) and handles['guardian']==launch['guardian_identity'],
            'Original guardian process binding differs')
    observations={role:observe_original_process(handle) if handle is not None else None
                  for role,handle in handles.items()}
    operational['process_observations']=observations
    try:
        container=inspect_container(launch['container'])
    except (OSError,subprocess.SubprocessError,RuntimeError,ValueError,KeyError,TypeError) as error:
        return dict(operational,reason='ORIGINAL_CONTAINER_OBSERVATION_UNKNOWN',error_type=type(error).__name__)
    operational['container_state']=container['state'] if container is not None else None
    witness=guardian.get('container_terminal_witness',{})
    if (guardian['status']!='BUDGET_CALIBRATION_GUARDIAN_TERMINAL' or witness.get('complete') is not True
            or any(row is not None and row['original_live'] is not False for row in observations.values())
            or (container is not None and (container['state']['Running'] or container['state']['Pid']!=0))):
        return dict(operational,reason='ORIGINAL_LIFETIME_NOT_TERMINAL')
    for key,name in METADATA.items():
        if key not in capture['files']:capture['files'][key]=captured_file(stage/name)
    registration=record(capture,'registration')
    require(capture['files']['registration']['sha256']==launch['registration_sha256']
            and registration['payload_sha256'][SOURCE]==file_sha(__file__), 'Original capture source differs')
    # Registration-relative source paths stay inside their respective roots.
    for collection in ('payload_sha256','runtime_source_sha256'):
        require(all(not Path(p).is_absolute() and '..' not in Path(p).parts
                    for p in registration[collection]),'Invalid registered source path')
    capture.update(status='ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE',container=container,
        process_observations=observations,
        own_UUID_lock_free=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.lock')),
        mode_owner_lock_free=lock_free(project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.mode-owner.lock')),
        payload_actual_sha256={n:file_sha(stage/n) for n in registration['payload_sha256']},
        runtime_actual_sha256={n:file_sha(project/'runtime'/n) for n in registration['runtime_source_sha256']},
        observed_unix=time.time(),scientific_rows_returned=False,GPU_submissions=0,ledger_written=False)
    return capture
