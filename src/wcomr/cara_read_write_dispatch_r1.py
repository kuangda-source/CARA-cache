"""Once-only full14 M1 dispatch under the original generic guardian."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .cara_read_write_runner_binding_r1 import validate_inputs, validate, RUNNER, PROFILE
from .cara_read_write_identity_r1 import for_run
from .cara_s_endpoint_lifecycle_r1 import IDENTITY, JOB_IDENTITY
from .cara_budget_dispatch_r1 import central_binding, recover, ASSETS
from .cara_budget_guardian_journal_r1 import encoded_sha
from .cara_budget_original_handles_r1 import bind_original_process
from .cara_budget_search_journal_r1 import create_record, read_record
from .cara_fast_b36_dispatch_r2 import assets_unchanged, english_resources, selected_gpu, create
from .gpu_budget_pool_v2 import DeviceLease, sha
from .history104_storage_r2 import storage_for
from .policy_price_terminal_r1 import require
from .wc73_exclusive_r1 import observe

SOURCE = 'src/wcomr/cara_read_write_dispatch_r1.py'
GUARDIAN = 'scripts/cara_read_write_host_entry_r1.py'
CLI = 'scripts/cara_read_write_dispatch_r1.py'
M1_IDENTITY = ('physical_paths', 'admission_sha256')
REQUIRED = (SOURCE, GUARDIAN, CLI, ASSETS,
    'src/wcomr/cara_budget_dispatch_r1.py', 'src/wcomr/cara_budget_guardian_journal_r1.py',
    'src/wcomr/cara_budget_lifecycle_capture_r1.py', 'src/wcomr/cara_s_endpoint_host_guardian_r1.py',
    'src/wcomr/cara_s_endpoint_guardian_journal_r1.py', 'src/wcomr/cara_s_endpoint_supervisor_r1.py',
    'src/wcomr/cara_s_endpoint_lifecycle_capture_r1.py', 'scripts/cara_budget_process_bootstrap_r1.py',
    'scripts/cara_read_write_container_r1.py', 'scripts/cara_read_write_supervisor_worker_r1.py',
    'src/wcomr/cara_fast_b36_dispatch_r2.py', 'scripts/cara_fast_host_guardian_r2.py',
    'scripts/four_card_bank24_execution_tools_r1.py', 'scripts/four_card_policy_assets_port_r1.py',
    'src/wcomr/wc73_execution_r1.py')


def ready_inputs(project, stage):
    result = validate_inputs(project, stage)
    payload = result[1]['payload_sha256']
    require(set(REQUIRED) <= set(payload) and payload[SOURCE] == sha(__file__),
        'Whole M1 dispatch/guardian sources must be CPU bound')
    require(encoded_sha(result[1]) == sha(Path(stage)/'registration.json'),
        'Registration serialization must match original guardian bytes')
    return result


def fresh_resources(project, stage, authority, profile):
    """Fresh real16GiB admission; retain the accepted64GiB gate unchanged."""
    project, stage = Path(project), Path(stage)
    storage = storage_for(stage)
    storage.check()
    limits = profile['storage']
    require(storage.output == project/'outputs'/authority['run_id']
        and storage.config['image_bytes'] == limits['output_image_bytes'] == 16*2**30
        and storage.config['journal_bytes'] == limits['independent_journal_bytes'] == 48*2**20
        and all(storage.config[k] >= limits[k] for k in
            ('minimum_output_free_bytes', 'minimum_host_free_bytes', 'minimum_free_inodes')),
        'Original16GiB M1 allocation and independent journal required')
    admission = read_record(stage/'fresh-admission.json')
    require(admission['registration_sha256'] == sha(stage/'registration.json')
        and admission['authorization_sha256'] == sha(stage/'GPU-authorization.json')
        and admission['asset_spec_sha256'] == sha(stage/ASSETS), 'Original admitted asset/source binding differs')
    assets_unchanged(project, read_record(stage/ASSETS), admission['assets'])
    english_resources(project)
    image = profile['GPU_container']['image']
    require(json.loads(subprocess.check_output(['docker', 'image', 'inspect', image], text=True, timeout=20))[0]['Id'] == image,
        'Pinned Docker image absent')
    from .cara_budget_lifecycle_capture_r1 import inspect_container
    require(inspect_container(stage.name+'-gpu') is None, 'Existing container: recover original handle')
    gpu = selected_gpu(authority['gpu_uuid'])
    host = profile['hosts'][authority['host']]
    hardware = observe(authority['gpu_uuid'])
    require(gpu['uuid'] == authority['gpu_uuid'] and gpu['compute_cap'] == '.'.join(map(str, host['capability']))
        and gpu['utilization_percent'] == 0 and not gpu['pids'] and 0 <= gpu['memory_used_mib'] <= 1024
        and 0 <= gpu['temperature_C'] < 90 and gpu['compute_mode'] in ('Default', 'Exclusive_Process')
        and hardware['gpu_uuid'] == authority['gpu_uuid'] and hardware['compute_apps'] == []
        and hardware['mps_processes'] == [], 'Selected device is not idle, cool and exclusively admissible')
    memory = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
        if line.startswith('MemAvailable:')))*1024
    require(memory >= host['minimum_MemAvailable_GiB']*2**30
        and set(map(int, host['cpuset_cpus'].split(','))) <= os.sched_getaffinity(0),
        'Host CPU/memory margin unavailable')
    with DeviceLease(project, authority['gpu_uuid']):
        pass
    with (project/'.sync/gpu-locks'/(authority['gpu_uuid']+'.mode-owner.lock')).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return storage, dict(gpu=gpu, exclusive_observation=hardware,
        MemAvailable_bytes=memory, observed_unix=time.time())


def frozen_commands(project, stage, registration, authority, profile, storage):
    from cara_read_write_container_r1 import container_arguments
    container = container_arguments(project=project, stage=stage, storage=storage,
        registration_sha=sha(Path(stage)/'registration.json'), profile=profile, host=authority['host'],
        run_id=authority['run_id'], uuid=authority['gpu_uuid'], uid=os.getuid(), gid=os.getgid())
    python = container[container.index('--entrypoint')+1]
    runner = [python, str(Path(stage)/RUNNER), '--project', str(project), '--stage', str(stage),
        '--source-revision', registration['source_revision'], '--gpu-uuid', authority['gpu_uuid']]
    return dict(container_cli=container, runner=runner)


def dispatch(project, stage, snapshot, password):
    project, stage = Path(project), Path(stage)
    require(stage.parent == project/'.sync',
        'Original M1 stage required')
    for_run(read_record(stage/'GPU-authorization.json')['run_id']).check_stage(stage.name)
    with (stage/'dispatch-control.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original = recover(stage)
        if original is not None:
            return original
        _, registration, authority, profile = ready_inputs(project, stage)
        central_binding(stage, authority, snapshot)
        storage, resources = fresh_resources(project, stage, authority, profile)
        commands = frozen_commands(project, stage, registration, authority, profile, storage)
        require(isinstance(password, str) and bool(password), 'Private credential delivery required')
        intent = {k:authority[k] for k in IDENTITY}
        intent.update(physical_paths=14, admission_sha256=sha(stage/'fresh-admission.json'),
            dispatcher_identity=bind_original_process(os.getpid()),
            registration_sha256=sha(stage/'registration.json'), authorization_sha256=sha(stage/'GPU-authorization.json'),
            central_reservation_sha256=sha(stage/'central-reservation.json'), commands=commands,
            resources=resources, central_snapshot=snapshot, CPU_fixture_only=False, no_replay=True, observed_unix=time.time())
        create_record(stage/'GPU-intent.json', intent)
        command = [sys.executable, str(stage/GUARDIAN), '--project', str(project), '--stage', str(stage)]
        with (stage/'host-guardian.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
            try:
                result = dict(status='ORIGINAL_GUARDIAN_DISPATCHED_AWAIT_LAUNCH',
                    guardian_identity=bind_original_process(child.pid), intent_sha256=sha(stage/'GPU-intent.json'),
                    launch_id=authority['launch_id'], command=command)
                create_record(stage/'GPU-dispatch.json', result)
                child.stdin.write(json.dumps(dict(sudo_password=password)).encode())
                child.stdin.flush()
            finally:
                child.stdin.close()
        return result


def publish_launch(project, stage):
    """Only the original spawned guardian may publish the immutable launch."""
    project, stage = Path(project), Path(stage)
    _, registration, authority, profile = ready_inputs(project, stage)
    intent = read_record(stage/'GPU-intent.json')
    dispatched = read_record(stage/'GPU-dispatch.json')
    identity = bind_original_process(os.getpid())
    require(dispatched['guardian_identity'] == identity and dispatched['intent_sha256'] == sha(stage/'GPU-intent.json')
        and dispatched['launch_id'] == authority['launch_id'] and intent['no_replay'] is True
        and intent['CPU_fixture_only'] is False and all(intent[k] == authority[k] for k in IDENTITY)
        and intent['physical_paths'] == 14 and intent['admission_sha256'] == sha(stage/'fresh-admission.json')
        and intent['registration_sha256'] == sha(stage/'registration.json')
        and intent['authorization_sha256'] == sha(stage/'GPU-authorization.json')
        and intent['central_reservation_sha256'] == sha(stage/'central-reservation.json'),
        'Only the original registered guardian may publish this M1 launch')
    central_binding(stage, authority, intent['central_snapshot'])
    storage = storage_for(stage)
    commands = frozen_commands(project, stage, registration, authority, profile, storage)
    require(commands == intent['commands'], 'Original frozen M1 commands changed after dispatch')
    launch = {k:intent[k] for k in JOB_IDENTITY+M1_IDENTITY}
    launch.update(CPU_fixture_only=False, guardian_identity=identity,
        central_reservation_sha256=intent['central_reservation_sha256'], commands=commands,
        container=stage.name+'-gpu', project=str(project), dispatched_unix=time.time())
    create(stage/'GPU-launch.json', launch)
    validate(project, stage)
    return launch, storage
