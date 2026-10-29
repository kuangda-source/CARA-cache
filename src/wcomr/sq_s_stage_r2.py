"""S source installation, exact inherited lease and consumed once-only handoff."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from .gpu_budget_pool_v2 import sha,process_identity
from .sq_s_execution_r2 import read,require,validate,validate_source,validate_authority
from .sq_s_spec_r2 import RUN,COUNTS,EXECUTION_CRITICAL,stage_path


def create(path,value):
    path=Path(path)
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    descriptor=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def verify_lease_fd(project,gpu_uuid,descriptor):
    expected=(Path(project)/'.sync/gpu-locks'/(gpu_uuid+'.lock')).resolve()
    require(expected.is_file(),'Original S lease file is missing')
    actual=Path('/proc/self/fd/'+str(descriptor)).resolve()
    held=os.fstat(int(descriptor));source=expected.stat()
    require(actual==expected and (held.st_dev,held.st_ino)==(source.st_dev,source.st_ino),
        'Inherited original S lease inode differs')


def install(project,host,base,proof,proof_raw,base_registration_sha256):
    project,base=Path(project),Path(base);stage=stage_path(project,host)
    if stage.exists():return dict(status='S_EXISTING_STAGE_RECOVER_ONLY',stage=str(stage),GPU_submissions=0)
    require(base.parent==project/'.sync' and not base.is_symlink()
        and sha(base/'registration.json')==base_registration_sha256,'Original accepted S CPU stage differs')
    reg=read(base/'registration.json')
    require(reg['GPU_submissions']==0 and reg['resource_limits']['GPU']=='hidden'
        and proof['passed'] is True and proof['host']==host and proof['GPU_submissions']==0
        and proof['source_revision']==reg['source_revision'] and proof['full_S_entry_CPU_accepted'] is True
        and proof['payload_sha256']==reg['payload_sha256']
        and set(EXECUTION_CRITICAL)<=set(proof['critical_source_sha256'])
        and all(reg['payload_sha256'].get(name)==value for name,value in proof['critical_source_sha256'].items())
        and json.loads(proof_raw)==proof,'Exact complete affected S CPU proof required')
    require(all(sha(project/'runtime'/name)==value for name,value in reg['runtime_source_sha256'].items()),
        'Original pinned S runtime changed before installation')
    for name,value in reg['payload_sha256'].items():
        relative=Path(name);source=base/relative
        require(not relative.is_absolute() and '..' not in relative.parts and not source.is_symlink()
            and base.resolve() in source.resolve().parents and sha(source)==value,'Accepted S source path or bytes differ')
    stage.mkdir(mode=0o700)
    for name in reg['payload_sha256']:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,target)
    (stage/'cache').mkdir(exist_ok=True);(stage/'cache/runtime').symlink_to(project/'runtime',target_is_directory=True)
    registration=dict(namespace='SQ_S_COMPLETE_EXECUTION_R2',host=host,stage=str(stage),
        source_revision=reg['source_revision'],payload_sha256=reg['payload_sha256'],
        runtime_source_sha256=reg['runtime_source_sha256'],base_stage=str(base),
        base_registration_sha256=base_registration_sha256,native_hostname=socket.gethostname(),GPU_submissions=0)
    create(stage/'registration.json',registration)
    with (stage/'execution-CPU-proof.json').open('x') as stream:
        stream.write(proof_raw);stream.flush();os.fsync(stream.fileno())
    validate_source(project,stage)
    return dict(status='S_SOURCE_STAGED_NO_GPU_AUTHORITY',stage=str(stage),host=host,
        source_revision=registration['source_revision'],registration_sha256=sha(stage/'registration.json'),
        CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),GPU_submissions=0,ledger_writes=0)


def prepare_intent(project,host,authority):
    stage=stage_path(project,host)
    require(not any((stage/name).exists() for name in ('GPU-intent.json','GPU-launch.json',
        'GPU-dispatch-consumed.json','pg-GPU-authorization.json','central-reservation.json',
        'launch-binding.json','pg-host-guardian.json')),'Original S intent exists; recover only')
    bundle,reg=validate_source(project,stage)
    validate_authority(project,stage,bundle,reg,authority=authority)
    intent=dict(status='SQ_S_PRE_GPU_INTENT_NO_DISPATCH_YET',run_id=RUN,host=host,
        launch_id=authority['launch_id'],source_revision=reg['source_revision'],
        registration_sha256=authority['registration_sha256'],gpu_uuid=authority['gpu_uuid'],
        created_unix=time.time(),authorizes_retry=False)
    create(stage/'GPU-intent.json',intent);create(stage/'pg-GPU-authorization.json',authority)
    return dict(intent=intent,intent_sha256=sha(stage/'GPU-intent.json'),
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'))


def dispatch(project,host,envelope,intent_sha256,password,*,host_python=sys.executable):
    stage=stage_path(project,host)
    require(sha(stage/'GPU-intent.json')==intent_sha256
        and not any((stage/name).exists() for name in ('GPU-launch.json','GPU-dispatch-consumed.json',
            'central-reservation.json','launch-binding.json')),'Original S handoff exists or differs; recover only')
    create(stage/'central-reservation.json',envelope)
    create(stage/'launch-binding.json',dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        central_reservation_sha256=sha(stage/'central-reservation.json')))
    _,_,auth=validate(project,stage)
    create(stage/'GPU-dispatch-consumed.json',dict(intent_sha256=intent_sha256,launch_id=auth['launch_id'],
        consumed_unix=time.time(),authorizes_retry=False))
    command=[host_python,'-u',str(stage/'scripts/cara_sq_s_guardian_r2.py'),
        '--project',str(project),'--stage',str(stage)]
    delivery_error=None
    with (stage/'GPU-guardian.log').open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,
            start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
        try:child.stdin.write(json.dumps(dict(sudo_password=password)).encode());child.stdin.close()
        except (BrokenPipeError,OSError) as error:
            delivery_error=type(error).__name__
            try:child.stdin.close()
            except OSError:pass
    if delivery_error:
        create(stage/'GPU-credential-delivery-diagnostic.json',dict(launch_id=auth['launch_id'],
            error_type=delivery_error,observed_unix=time.time(),authorizes_retry=False))
    until=time.monotonic()+5
    while time.monotonic()<until:
        if (stage/'GPU-launch.json').exists():
            launch=read(stage/'GPU-launch.json')
            require(launch['launch_id']==auth['launch_id'],'Original S child launch differs')
            return launch
        if child.poll() is not None:break
        time.sleep(.02)
    return dict(status='S_CONSUMED_HANDOFF_NO_PUBLISHED_LAUNCH_RECOVER_ONLY',
        launch_id=auth['launch_id'],guardian_identity=process_identity(child.pid),
        credential_delivery_error=delivery_error,actual_GPU_started=False,authorizes_retry=False)


def publish_launch(project,stage):
    stage=Path(stage);auth=read(stage/'pg-GPU-authorization.json')
    require(stage==stage_path(project,auth['host']) and (stage/'GPU-dispatch-consumed.json').exists(),
        'Original consumed S handoff required')
    launch=dict(status='SQ_S_SINGLE_DISPATCHED_HARDWARE_ADMISSION_PENDING',
        **{key:auth[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256',
            'physical_scope_sha256','scope_counts','whole_GPUh','registration_sha256')},
        stage=str(stage),container=stage.name+'-gpu',guardian_identity=process_identity(os.getpid()),
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'),started_unix=time.time(),
        actual_GPU_started=False,automatic_retry_authorized=False)
    require(launch['run_id']==RUN and launch['scope_counts']==COUNTS,'Original complete S launch required')
    create(stage/'GPU-launch.json',launch);return launch
