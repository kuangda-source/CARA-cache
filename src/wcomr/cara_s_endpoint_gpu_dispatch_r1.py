"""Once-only endpoint dispatch after separate authority and fresh admission.

Reuse the unchanged budget controller's central/resource/recovery boundaries.
This module never creates authority or reserves funds; unknown means recover.
"""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .cara_s_endpoint_lifecycle_r1 import IDENTITY,JOB_IDENTITY
from .cara_s_endpoint_runner_binding_r1 import validate_inputs,validate,RUNNER,PROFILE
from .cara_budget_dispatch_r1 import central_binding,fresh_resources,recover,ASSETS
from .cara_budget_guardian_journal_r1 import encoded_sha
from .cara_budget_original_handles_r1 import bind_original_process
from .cara_budget_search_journal_r1 import create_record,read_record
from .cara_fast_b36_dispatch_r2 import create
from .gpu_budget_pool_v2 import sha
from .history104_storage_r2 import storage_for
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_gpu_dispatch_r1.py'
GUARDIAN='scripts/cara_s_endpoint_host_entry_r1.py'
CLI='scripts/cara_s_endpoint_gpu_dispatch_r1.py'
ENDPOINT_IDENTITY=('physical_paths','endpoint_binding_sha256','original_budget_freeze_sha256')
REQUIRED=(SOURCE,GUARDIAN,CLI,ASSETS,
    'src/wcomr/cara_budget_dispatch_r1.py','src/wcomr/cara_budget_runner_binding_r1.py',
    'src/wcomr/cara_budget_lifecycle_capture_r1.py','src/wcomr/cara_budget_guardian_journal_r1.py',
    'src/wcomr/cara_s_endpoint_host_guardian_r1.py','src/wcomr/cara_s_endpoint_guardian_journal_r1.py',
    'src/wcomr/cara_s_endpoint_supervisor_r1.py','src/wcomr/cara_s_endpoint_lifecycle_capture_r1.py',
    'scripts/cara_budget_process_bootstrap_r1.py','scripts/cara_s_endpoint_container_r1.py',
    'scripts/cara_s_endpoint_supervisor_worker_r1.py','src/wcomr/cara_s_endpoint_release_r1.py',
    'src/wcomr/cara_s_endpoint_artifacts_r1.py','src/wcomr/cara_fast_b36_dispatch_r2.py',
    'scripts/cara_fast_host_guardian_r2.py','scripts/four_card_bank24_execution_tools_r1.py',
    'scripts/four_card_policy_assets_port_r1.py','src/wcomr/wc73_execution_r1.py')


def ready_inputs(project,stage):
    result=validate_inputs(project,stage)
    registration=result[3];payload=registration['payload_sha256']
    require(set(REQUIRED)<=set(payload) and payload[SOURCE]==sha(__file__),
            'Whole endpoint dispatch, guardian and reader sources must be CPU bound')
    require(encoded_sha(registration)==sha(Path(stage)/'registration.json'),
            'Registration serialization must match original guardian bytes')
    return result


def frozen_commands(project,stage,registration,authority,profile,storage):
    from cara_s_endpoint_container_r1 import container_arguments
    container=container_arguments(project=project,stage=stage,storage=storage,
        registration_sha=sha(Path(stage)/'registration.json'),profile=profile,host=authority['host'],
        run_id=authority['run_id'],uuid=authority['gpu_uuid'],uid=os.getuid(),gid=os.getgid())
    python=container[container.index('--entrypoint')+1]
    runner=[python,str(Path(stage)/RUNNER),'--project',str(project),'--stage',str(stage),
            '--source-revision',registration['source_revision'],'--gpu-uuid',authority['gpu_uuid']]
    return dict(container_cli=container,runner=runner)


def dispatch(project,stage,snapshot,password):
    project,stage=Path(project),Path(stage)
    require(stage.parent==project/'.sync' and stage.name.startswith('cara-S-endpoint-GPU-'),
            'Original endpoint stage required')
    with (stage/'dispatch-control.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        original=recover(stage)
        if original is not None:return original
        _,_,_,registration,authority,profile=ready_inputs(project,stage)
        central_binding(stage,authority,snapshot)
        storage,resources=fresh_resources(project,stage,authority,profile)
        commands=frozen_commands(project,stage,registration,authority,profile,storage)
        require(isinstance(password,str) and bool(password),'Private credential delivery required')
        intent={k:authority[k] for k in IDENTITY+ENDPOINT_IDENTITY}
        intent.update(dispatcher_identity=bind_original_process(os.getpid()),
            registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'GPU-authorization.json'),
            central_reservation_sha256=sha(stage/'central-reservation.json'),commands=commands,
            resources=resources,central_snapshot=snapshot,CPU_fixture_only=False,no_replay=True,observed_unix=time.time())
        create_record(stage/'GPU-intent.json',intent)
        command=[sys.executable,str(stage/GUARDIAN),'--project',str(project),'--stage',str(stage)]
        with (stage/'host-guardian.log').open('x') as log:
            child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
            try:
                result=dict(status='ORIGINAL_GUARDIAN_DISPATCHED_AWAIT_LAUNCH',
                    guardian_identity=bind_original_process(child.pid),intent_sha256=sha(stage/'GPU-intent.json'),
                    launch_id=authority['launch_id'],command=command)
                create_record(stage/'GPU-dispatch.json',result)
                child.stdin.write(json.dumps(dict(sudo_password=password)).encode());child.stdin.flush()
            finally:child.stdin.close()
        return result


def publish_launch(project,stage):
    """Only the original spawned guardian can publish before allocation begins."""
    project,stage=Path(project),Path(stage)
    _,_,_,registration,authority,profile=ready_inputs(project,stage)
    intent=read_record(stage/'GPU-intent.json');dispatched=read_record(stage/'GPU-dispatch.json')
    identity=bind_original_process(os.getpid())
    require(dispatched['guardian_identity']==identity and dispatched['intent_sha256']==sha(stage/'GPU-intent.json')
            and dispatched['launch_id']==authority['launch_id'] and intent['no_replay'] is True
            and intent['CPU_fixture_only'] is False and all(intent[k]==authority[k] for k in IDENTITY+ENDPOINT_IDENTITY)
            and intent['registration_sha256']==sha(stage/'registration.json')
            and intent['authorization_sha256']==sha(stage/'GPU-authorization.json')
            and intent['central_reservation_sha256']==sha(stage/'central-reservation.json'),
            'Only the original registered guardian may publish this launch')
    central_binding(stage,authority,intent['central_snapshot'])
    storage=storage_for(stage)
    commands=frozen_commands(project,stage,registration,authority,profile,storage)
    require(commands==intent['commands'],'Original frozen commands changed after dispatch')
    launch={k:intent[k] for k in JOB_IDENTITY+ENDPOINT_IDENTITY}
    launch.update(CPU_fixture_only=False,guardian_identity=identity,
        central_reservation_sha256=intent['central_reservation_sha256'],commands=commands,
        container=stage.name+'-gpu',project=str(project),dispatched_unix=time.time())
    create(stage/'GPU-launch.json',launch)
    validate(project,stage)
    return launch,storage
