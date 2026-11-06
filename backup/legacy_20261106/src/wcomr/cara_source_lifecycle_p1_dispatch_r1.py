"""Once-only full146 P1 dispatch under the original generic guardian."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .cara_source_lifecycle_p1_runner_binding_r1 import validate_inputs, RUNNER, PROFILE, RUN_ID, STAGE_NAME
from .cara_source_lifecycle_p1_central_r1 import validate_authority,ledger_valid
from .wc73_execution_r1 import Pool,hold,admit_host
from .gpu_budget_pool_v2 import finite
import math
import copy
from .cara_s_endpoint_lifecycle_r1 import IDENTITY, JOB_IDENTITY
from .cara_budget_dispatch_r1 import recover, ASSETS
from .cara_budget_guardian_journal_r1 import encoded_sha
from .cara_budget_original_handles_r1 import bind_original_process
from .cara_budget_search_journal_r1 import create_record, read_record
from .cara_fast_b36_dispatch_r2 import assets_unchanged, english_resources, selected_gpu, create
from .gpu_budget_pool_v2 import DeviceLease, sha
from .history104_storage_r2 import storage_for
from .policy_price_terminal_r1 import require
from .wc73_exclusive_r1 import observe

SOURCE = 'src/wcomr/cara_source_lifecycle_p1_dispatch_r1.py'
GUARDIAN = 'scripts/cara_source_lifecycle_p1_host_entry_r1.py'
CLI = 'scripts/cara_source_lifecycle_p1_dispatch_r1.py'
P1_IDENTITY = ('semantic_positions','physical_generation_upper','admission_sha256')
ENVIRONMENT='internal-score-environment.json'
REQUIRED = (SOURCE, GUARDIAN, CLI, ASSETS,
    'src/wcomr/cara_source_lifecycle_p1_identity_r1.py',
    'src/wcomr/cara_budget_dispatch_r1.py', 'src/wcomr/cara_budget_guardian_journal_r1.py',
    'src/wcomr/cara_budget_lifecycle_capture_r1.py', 'src/wcomr/cara_s_endpoint_host_guardian_r1.py',
    'src/wcomr/cara_s_endpoint_guardian_journal_r1.py', 'src/wcomr/cara_s_endpoint_supervisor_r1.py',
    'src/wcomr/cara_s_endpoint_lifecycle_capture_r1.py', 'scripts/cara_budget_process_bootstrap_r1.py',
    'scripts/cara_source_lifecycle_p1_container_r1.py', 'scripts/cara_source_lifecycle_p1_supervisor_worker_r1.py',
    'src/wcomr/cara_fast_b36_dispatch_r2.py', 'scripts/cara_fast_host_guardian_r2.py',
    'scripts/four_card_bank24_execution_tools_r1.py', 'scripts/four_card_policy_assets_port_r1.py',
    'src/wcomr/wc73_execution_r1.py','src/wcomr/cara_source_lifecycle_p1_central_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_capture_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_score_capture_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_score_dispatch_r1.py',
    'scripts/cara_source_lifecycle_p1_score_bootstrap_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_analysis_r1.py')


def ready_inputs(project, stage):
    result = validate_inputs(project, stage)
    payload = result[1]['payload_sha256']
    require(set(REQUIRED) <= set(payload) and payload[SOURCE] == sha(__file__),
        'Whole P1 dispatch/guardian sources must be CPU bound')
    require(encoded_sha(result[1]) == sha(Path(stage)/'registration.json'),
        'Registration serialization must match original guardian bytes')
    validate_authority(result[2],project)
    require(result[2]['FIT_environment_sha256']==sha(Path(stage)/ENVIRONMENT),'Frozen original FIT environment differs')
    return result


def central_binding(stage,authority,snapshot):
    """Fresh original reservation, including separately recorded24GPUh steps."""
    stage=Path(stage);validate_authority(authority,stage.parents[1])
    envelope=read_record(stage/'central-reservation.json');current=snapshot['ledger'];job=envelope['job']
    before,base,after=(envelope[k] for k in ('central_before','reservation_base','central_after'))
    for value in (before,base,after,current):ledger_valid(value)
    require(snapshot['central_ledger_host']=='four_card' and finite(snapshot['observed_unix'])
        and 0<=time.time()-snapshot['observed_unix']<=60 and current['available_gpu_hours']>=0
        and not current.get('budget_overrun_recorded')
        and envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
        and job['job_id']==RUN_ID and job['status']=='RESERVED_OR_RUNNING' and current['jobs'].get(RUN_ID)==job
        and all(job[k]==authority[k] for k in IDENTITY)
        and job['registration_sha256']==sha(stage/'registration.json')
        and job['authorization_sha256']==sha(stage/'GPU-authorization.json'),
        'Fresh original P1 central reservation and unchanged whole job required')
    steps=envelope['cap_increments24']
    require(type(steps) is int and steps>=0 and (not steps or authority.get('standing_cap_increment24_authorized') is True)
        and steps==max(0,math.ceil((authority['billed_limit_GPUh']-before['available_gpu_hours'])/24))
        and base['cap_gpu_hours']==before['cap_gpu_hours']+steps*24
        and base['cap_gpu_hours']==after['cap_gpu_hours']==current['cap_gpu_hours']
        and all(before[k]==base[k]==after[k]==current[k] for k in ('origin_used_gpu_hours','origin_gpu_jobs_launched')),
        'Only the minimum necessary standing24GPUh cap steps may precede this reservation')
    expected=copy.deepcopy(before)
    events=base['events'][len(before['events']):]
    require(base['events'][:len(before['events'])]==before['events'] and len(events)==steps,
        'Original cap-adjustment event prefix differs')
    for event in events:
        require(event['type']=='P1_STANDING_CAP_INCREMENT24' and event['job_id']==RUN_ID
            and event['sequence']==len(expected['events'])+1 and event['increment_GPUh']==24
            and event['previous_cap_GPUh']==expected['cap_gpu_hours']
            and event['cap_GPUh']==expected['cap_gpu_hours']+24 and finite(event['unix']),
            'Exact original24GPUh cap event required')
        expected['cap_gpu_hours']+=24;expected['events'].append(event)
    totals=set(Pool.accounting(base))
    require(set(expected)==set(base) and all(expected[k]==base[k] for k in expected if k not in totals)
        and RUN_ID not in before['jobs'] and set(after['jobs'])==set(base['jobs'])|{RUN_ID}
        and all(after['jobs'][k]==v for k,v in base['jobs'].items()) and after['jobs'][RUN_ID]==job
        and after['events'][:-1]==base['events'] and after['events'][-1]['type']=='P1_COMPLETE146_RESERVE'
        and after['events'][-1]['job_id']==RUN_ID,
        'Cap adjustment must preserve every old record, then add exactly the complete original P1 job')
    old={k:v for k,v in before['jobs'].items() if hold(v) and v['status']=='RESERVED_OR_RUNNING'}
    require(len(old)==2 and sorted(v['billed_limit_GPUh'] for v in old.values())==[4.5,12.]
        and all(after['jobs'][k]==v==current['jobs'][k] for k,v in old.items()),
        'Original two unknown liabilities must remain byte-identical')
    admit_host(current,authority['host'],exclude=RUN_ID)
    return envelope


def fresh_resources(project, stage, authority, profile):
    """Fresh real16GiB admission; retain the accepted64GiB gate unchanged."""
    project, stage = Path(project), Path(stage)
    storage = storage_for(stage)
    storage.check()
    limits = profile['storage']
    require(storage.output == project/'outputs'/authority['run_id']
        and storage.config['image_bytes'] == limits['output_image_bytes'] == 64*2**30
        and storage.config['journal_bytes'] == limits['independent_journal_bytes'] == 48*2**20
        and all(storage.config[k] >= limits[k] for k in
            ('minimum_output_free_bytes', 'minimum_host_free_bytes', 'minimum_free_inodes')),
        'Original64GiB P1 allocation and independent journal required')
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
        and (set(map(int,host['cpuset_cpus'].split(',')))|{26,27}) <= os.sched_getaffinity(0),
        'Host CPU/memory margin unavailable')
    environment=read_record(stage/ENVIRONMENT)
    require(sha(stage/ENVIRONMENT)==authority['FIT_environment_sha256']
        and len(environment['weights_sha256'])==2
        and set(environment['weights_sha256'].values())=={
            '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02',
            'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'}
        and all(Path(p).is_absolute() and Path(p).is_relative_to(project) and sha(Path(p))==h for p,h in environment['weights_sha256'].items())
        and (Path(environment['piq_site'])/'piq/__init__.py').is_file(),
        'Fresh original offline Alex/PIQ2-weight environment required')
    with DeviceLease(project, authority['gpu_uuid']):
        pass
    with (project/'.sync/gpu-locks'/(authority['gpu_uuid']+'.mode-owner.lock')).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return storage, dict(gpu=gpu, exclusive_observation=hardware,
        MemAvailable_bytes=memory, observed_unix=time.time())


def frozen_commands(project, stage, registration, authority, profile, storage):
    from cara_source_lifecycle_p1_container_r1 import container_arguments
    container = container_arguments(project=project, stage=stage, storage=storage,
        registration_sha=sha(Path(stage)/'registration.json'), profile=profile, host=authority['host'],
        run_id=authority['run_id'], uuid=authority['gpu_uuid'], uid=os.getuid(), gid=os.getgid())
    python = container[container.index('--entrypoint')+1]
    runner = [python, str(Path(stage)/RUNNER), '--project', str(project), '--stage', str(stage),
        '--source-revision', registration['source_revision'], '--gpu-uuid', authority['gpu_uuid']]
    return dict(container_cli=container, runner=runner)


def dispatch(project, stage, snapshot, password):
    project, stage = Path(project), Path(stage)
    require(stage.parent==project/'.sync' and stage.name==STAGE_NAME,'Original complete P1 stage required')
    with (stage/'dispatch-control.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original = recover(stage)
        if original is not None:
            return original
        _, registration, authority, profile, quote = ready_inputs(project, stage)
        central_binding(stage, authority, snapshot)
        storage, resources = fresh_resources(project, stage, authority, profile)
        commands = frozen_commands(project, stage, registration, authority, profile, storage)
        require(isinstance(password, str) and bool(password), 'Private credential delivery required')
        intent = {k:authority[k] for k in IDENTITY}
        intent.update(semantic_positions=146, physical_generation_upper=142, admission_sha256=sha(stage/'fresh-admission.json'),
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
    _, registration, authority, profile, quote = ready_inputs(project, stage)
    intent = read_record(stage/'GPU-intent.json')
    dispatched = read_record(stage/'GPU-dispatch.json')
    identity = bind_original_process(os.getpid())
    require(dispatched['guardian_identity'] == identity and dispatched['intent_sha256'] == sha(stage/'GPU-intent.json')
        and dispatched['launch_id'] == authority['launch_id'] and intent['no_replay'] is True
        and intent['CPU_fixture_only'] is False and all(intent[k] == authority[k] for k in IDENTITY)
        and intent['semantic_positions']==146 and intent['physical_generation_upper']==142 and intent['admission_sha256'] == sha(stage/'fresh-admission.json')
        and intent['registration_sha256'] == sha(stage/'registration.json')
        and intent['authorization_sha256'] == sha(stage/'GPU-authorization.json')
        and intent['central_reservation_sha256'] == sha(stage/'central-reservation.json'),
        'Only the original registered guardian may publish this P1 launch')
    central_binding(stage, authority, intent['central_snapshot'])
    storage = storage_for(stage)
    commands = frozen_commands(project, stage, registration, authority, profile, storage)
    require(commands == intent['commands'], 'Original frozen P1 commands changed after dispatch')
    launch = {k:intent[k] for k in JOB_IDENTITY+P1_IDENTITY}
    launch.update(CPU_fixture_only=False, guardian_identity=identity,
        central_reservation_sha256=intent['central_reservation_sha256'], commands=commands,
        container=stage.name+'-gpu', project=str(project), dispatched_unix=time.time())
    require(launch['run_id']==RUN_ID and launch['billed_limit_GPUh']==profile['hard_GPUh'],
        'Original complete P1 launch identity differs')
    create(stage/'GPU-launch.json', launch)
    return launch, storage
