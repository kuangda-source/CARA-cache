"""Once-only host dispatch for an already approved, prepared, reserved card.

Preparation, whole-card CPU acceptance and central reservation are prerequisites.
This module never creates authority, reserves funds, or retries an original child.
"""
import fcntl
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from .cara_budget_lifecycle_r1 import IDENTITY, JOB_IDENTITY
from .cara_budget_guardian_journal_r1 import encoded_sha
from .cara_budget_original_handles_r1 import bind_original_process, observe_original_process
from .cara_budget_runner_binding_r1 import validate_inputs, validate, RUNNER, PROFILE
from .cara_budget_search_journal_r1 import create_record, read_record
from .cara_fast_b36_dispatch_r2 import assets_unchanged, english_resources, selected_gpu, create
from .gpu_budget_pool_v2 import DeviceLease, finite, sha
from .history104_storage_r2 import storage_for
from .policy_price_terminal_r1 import require
from .wc73_exclusive_r1 import observe
from .wc73_execution_r1 import Pool, hold, admit_host

SOURCE='src/wcomr/cara_budget_dispatch_r1.py'
GUARDIAN='scripts/cara_budget_host_entry_r1.py'
CLI='scripts/cara_budget_dispatch_r1.py'
ASSETS='plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'
REQUIRED=(SOURCE,GUARDIAN,CLI,ASSETS,
    'src/wcomr/cara_budget_host_guardian_r1.py','src/wcomr/cara_budget_guardian_journal_r1.py',
    'src/wcomr/cara_budget_supervisor_r1.py','scripts/cara_budget_process_bootstrap_r1.py',
    'scripts/cara_budget_container_r1.py','scripts/cara_budget_supervisor_worker_r1.py',
    'src/wcomr/cara_budget_complete_r1.py','scripts/accept_cara_budget_complete_r1.py',
    'src/wcomr/cara_fast_b36_dispatch_r2.py','scripts/cara_fast_host_guardian_r2.py',
    'scripts/four_card_bank24_execution_tools_r1.py','scripts/four_card_policy_assets_port_r1.py',
    'src/wcomr/cara_budget_lifecycle_r1.py','src/wcomr/wc73_execution_r1.py',
    'src/wcomr/cara_budget_central_r1.py','src/wcomr/cara_budget_prepare_r1.py',
    'scripts/cara_budget_central_r1.py','scripts/cara_budget_prepare_r1.py',
    'src/wcomr/immutable_stage_payload_r1.py')


def ready_inputs(project,stage):
    card,registration,authority,profile,limits=validate_inputs(project,stage)
    payload=registration['payload_sha256']
    require(set(REQUIRED)<=set(payload) and payload[SOURCE]==sha(__file__),
            'Whole dispatch, guardian and result-reader sources must be CPU bound')
    require(encoded_sha(registration)==sha(Path(stage)/'registration.json'),
            'Registration serialization must match the original guardian byte binding')
    require(re.fullmatch('[0-9a-f]{40}',authority['source_revision'])
            and re.fullmatch('[0-9a-f-]{32,36}',authority['launch_id'])
            and registration['container_image']==profile['GPU_container']['image'],
            'Published source, unique launch and pinned image required')
    proof=read_record(Path(stage)/'execution-CPU-proof.json')
    require(proof.get('dual_host_whole_card_CPU_accepted') is True
            and set(proof['host_receipts'])=={'four_card','two_card'}
            and all(row['whole_card_CPU_accepted'] is True and row['scope_sha256']==card['scope_sha256']
                    and row['payload_sha256']==payload for row in proof['host_receipts'].values()),
            'Both hosts need full affected execution CPU acceptance')
    quote=read_record(Path(stage)/'whole-quote.json')
    require(set(quote['host_quotes'])=={'four_card','two_card'},'Both complete host quotes required')
    components={'generation','path_artifacts_and_objectives','producer_final_full_readback',
                'admission_and_model_load','stop_and_release'}
    for row in quote['host_quotes'].values():
        costs=row['components_seconds']
        require(set(costs)==components and all(finite(v) and v>0 for v in costs.values())
                and row['physical_paths']==112 and row['candidate_queries']==51 and row['hard_GPUh']==14
                and finite(row['forecast_GPUh']) and 0<row['forecast_GPUh']<=14
                and abs(sum(costs.values())/3600-row['forecast_GPUh'])<1e-9
                and costs['stop_and_release']>=600 and bool(row['evidence_refs']),
                'Whole quote must include every path, objective, final readback and release')
    return card,registration,authority,profile,limits


def central_binding(stage,authority,snapshot):
    """Read a fresh authoritative snapshot; never infer funds from an old receipt."""
    stage=Path(stage);envelope=read_record(stage/'central-reservation.json')
    job=envelope['job'];current=snapshot['ledger']
    require(snapshot['central_ledger_host']=='four_card'
            and finite(snapshot['observed_unix']) and 0<=time.time()-snapshot['observed_unix']<=60
            and current['cap_gpu_hours']==226 and not current.get('budget_overrun_recorded',False)
            and all(finite(current[k]) and math.isclose(current[k],v,rel_tol=0,abs_tol=1e-9)
                    for k,v in Pool.accounting(current).items())
            and current['available_gpu_hours']>=0,'Fresh central cap, totals and funds required')
    require(envelope['central_ledger_host']=='four_card' and envelope['new_reservation'] is True
            and job['job_id']==authority['run_id'] and job['status']=='RESERVED_OR_RUNNING'
            and current['jobs'].get(authority['run_id'])==job
            and all(job[k]==authority[k] for k in IDENTITY)
            and job['registration_sha256']==sha(stage/'registration.json')
            and job['authorization_sha256']==sha(stage/'GPU-authorization.json'),
            'Recover the single central original job; host migration or replay is forbidden')
    # The original unresolved liability is retained byte-for-byte by reservation.
    before=envelope['central_before'];after=envelope['central_after']
    old=[(k,v) for k,v in before['jobs'].items() if v['status']=='RESERVED_OR_RUNNING' and hold(v)]
    require(len(old)==2 and sorted(v['billed_limit_GPUh'] for _,v in old)==[4.5,12.]
            and all(after['jobs'].get(k)==v==current['jobs'].get(k) for k,v in old)
            and all(before[k]==after[k]==current[k] for k in
                    ('cap_gpu_hours','origin_used_gpu_hours','origin_gpu_jobs_launched')),
            'Original cap, origin and old 16.5 GPUh liability must remain unchanged')
    require(set(after['jobs'])==set(before['jobs'])|{authority['run_id']}
            and authority['run_id'] not in before['jobs'] and after['jobs'][authority['run_id']]==job
            and all(after['jobs'][k]==v for k,v in before['jobs'].items()),
            'Reservation must add exactly the original whole job')
    admit_host(current,authority['host'],exclude=authority['run_id'])
    return envelope


def fresh_resources(project,stage,authority,profile):
    project,stage=Path(project),Path(stage)
    storage=storage_for(stage);storage.check()
    require(storage.output==project/'outputs'/authority['run_id']
            and storage.config['image_bytes']==64*2**30,'Original 64 GiB allocation required')
    admission=read_record(stage/'fresh-admission.json')
    require(admission['registration_sha256']==sha(stage/'registration.json')
            and admission['authorization_sha256']==sha(stage/'GPU-authorization.json')
            and admission['asset_spec_sha256']==sha(stage/ASSETS), 'Original admitted asset/source binding differs')
    assets_unchanged(project,read_record(stage/ASSETS),admission['assets']);english_resources(project)
    image=profile['GPU_container']['image']
    require(json.loads(subprocess.check_output(['docker','image','inspect',image],text=True,timeout=20))[0]['Id']==image,
            'Pinned Docker image absent')
    from .cara_budget_lifecycle_capture_r1 import inspect_container
    require(inspect_container(stage.name+'-gpu') is None,'Existing container: recover original handle')
    gpu=selected_gpu(authority['gpu_uuid']);host=profile['hosts'][authority['host']]
    hardware=observe(authority['gpu_uuid'])
    require(gpu['uuid']==authority['gpu_uuid'] and gpu['compute_cap']=='.'.join(map(str,host['capability']))
            and gpu['utilization_percent']==0 and not gpu['pids'] and 0<=gpu['memory_used_mib']<=1024
            and 0<=gpu['temperature_C']<90 and gpu['compute_mode'] in ('Default','Exclusive_Process')
            and hardware['gpu_uuid']==authority['gpu_uuid'] and hardware['compute_apps']==[]
            and hardware['mps_processes']==[], 'Selected device is not idle, cool and exclusively admissible')
    memory=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                    if line.startswith('MemAvailable:')))*1024
    require(memory>=host['minimum_MemAvailable_GiB']*2**30
            and set(map(int,host['cpuset_cpus'].split(',')))<=os.sched_getaffinity(0),
            'Host CPU/memory margin unavailable')
    with DeviceLease(project,authority['gpu_uuid']):pass
    with (project/'.sync/gpu-locks'/(authority['gpu_uuid']+'.mode-owner.lock')).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    return storage,dict(gpu=gpu,exclusive_observation=hardware,MemAvailable_bytes=memory,observed_unix=time.time())


def frozen_commands(project,stage,registration,authority,profile,storage):
    from cara_budget_container_r1 import container_arguments
    container=container_arguments(project=project,stage=stage,storage=storage,
        registration_sha=sha(Path(stage)/'registration.json'),profile=profile,host=authority['host'],
        run_id=authority['run_id'],uuid=authority['gpu_uuid'],uid=os.getuid(),gid=os.getgid())
    python=container[container.index('--entrypoint')+1]
    runner=[python,str(Path(stage)/RUNNER),'--project',str(project),'--stage',str(stage),
            '--source-revision',registration['source_revision'],'--gpu-uuid',authority['gpu_uuid']]
    return dict(container_cli=container,runner=runner)


def recover(stage):
    """Operational control bytes only; no scientific outputs or new submission."""
    stage=Path(stage);records={}
    for name in ('GPU-intent','GPU-dispatch','GPU-launch'):
        path=stage/(name+'.json')
        if path.exists():records[name]=read_record(path)
    if not records:return None
    handle=records.get('GPU-launch',records.get('GPU-dispatch',{})).get('guardian_identity')
    observation=observe_original_process(handle) if handle else None
    return dict(status='ORIGINAL_DISPATCH_RECOVER_ONLY',records=records,
        guardian_observation=observation,GPU_submissions=0,authorizes_retry=False)


def dispatch(project,stage,snapshot,password):
    project,stage=Path(project),Path(stage)
    require(stage.parent==project/'.sync' and stage.name.startswith('cara-budget-calibration-GPU-'),
            'Original calibration stage required')
    with (stage/'dispatch-control.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        original=recover(stage)
        if original is not None:return original
        _,registration,authority,profile,_=ready_inputs(project,stage)
        central_binding(stage,authority,snapshot)
        storage,resources=fresh_resources(project,stage,authority,profile)
        commands=frozen_commands(project,stage,registration,authority,profile,storage)
        require(isinstance(password,str) and bool(password),'Private credential delivery required')
        intent={k:authority[k] for k in IDENTITY}
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
    _,registration,authority,profile,_=ready_inputs(project,stage)
    intent=read_record(stage/'GPU-intent.json');dispatched=read_record(stage/'GPU-dispatch.json')
    identity=bind_original_process(os.getpid())
    require(dispatched['guardian_identity']==identity and dispatched['intent_sha256']==sha(stage/'GPU-intent.json')
            and dispatched['launch_id']==authority['launch_id'] and intent['no_replay'] is True
            and intent['CPU_fixture_only'] is False and all(intent[k]==authority[k] for k in IDENTITY)
            and intent['registration_sha256']==sha(stage/'registration.json')
            and intent['authorization_sha256']==sha(stage/'GPU-authorization.json')
            and intent['central_reservation_sha256']==sha(stage/'central-reservation.json'),
            'Only the original registered guardian may publish this launch')
    central_binding(stage,authority,intent['central_snapshot'])
    storage=storage_for(stage)
    commands=frozen_commands(project,stage,registration,authority,profile,storage)
    require(commands==intent['commands'],'Original frozen commands changed after dispatch')
    launch={k:intent[k] for k in JOB_IDENTITY}
    launch.update(CPU_fixture_only=False,guardian_identity=identity,
        central_reservation_sha256=intent['central_reservation_sha256'],commands=commands,
        container=stage.name+'-gpu',project=str(project),dispatched_unix=time.time())
    create(stage/'GPU-launch.json',launch)
    validate(project,stage)
    return launch,storage
