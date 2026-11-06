"""CAL35 binding to unchanged original guardian/supervisor/storage primitives."""
import copy
import os
from pathlib import Path
import time

from .cara_f19_speed190_identity_r1 import RUN,STAGE,MANIFEST,GPU,IMAGE
from .cara_f19_speed190_card_r1 import validate as validate_card
from .cara_fast_spec_r1 import digest
from .cara_fast_b36_dispatch_r2 import assets_unchanged,selected_gpu,create
from .cara_budget_lifecycle_r1 import IDENTITY,JOB_IDENTITY,financial_terminal,audit_settlement
from .cara_budget_lifecycle_capture_r1 import capture_lifecycle,inspect_container
from .cara_budget_original_handles_r1 import bind_original_process
from .cara_budget_host_guardian_r1 import allocate
from .gpu_budget_pool_v2 import sha,atomic_json
from .history104_storage_r2 import storage_for
from .policy_price_terminal_r1 import require
from .wc73_execution_r1 import Pool,admit_host,hold

HOST_ENTRY='scripts/cara_f19_speed190_host_r1.py'
RUNNER='scripts/run_cara_f19_speed190_r1.py'
ASSETS='plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'
read=lambda p:__import__('json').loads(Path(p).read_bytes())


def validate_stage(project,stage,*,require_proof=True):
    project,stage=Path(project),Path(stage)
    reg,auth=read(stage/'registration.json'),read(stage/'GPU-authorization.json')
    require(reg["payload_sha256"]["src/wcomr/cara_f19_speed190_execution_r1.py"]==sha(__file__),"Exact execution binding source required")
    card=validate_card(read(stage/MANIFEST))
    require(stage==project/'.sync'/STAGE and auth['stage']==str(stage)
        and auth['run_id']==RUN and auth['host']=='two_card' and auth['gpu_uuid']==GPU
        and auth['scope_sha256']==card['scope_sha256'] and auth['billed_limit_GPUh']==3.
        and auth['execution_authorized'] and auth['direct_user_authorization'] and not auth['authorizes_replay']
        and auth['user_quote']==card['authority']['user_quote'] and auth['CPU_fixture_only'] is False,
        'Single user-approved complete CAL35/3GPUh authority required')
    require(all(reg[k]==auth[k] for k in ('stage','host','source_revision'))
        and reg['container_image']==IMAGE and reg['payload_sha256'][MANIFEST]==sha(stage/MANIFEST)
        and all(not Path(n).is_absolute() and '..' not in Path(n).parts and sha(stage/n)==h for n,h in reg['payload_sha256'].items())
        and all(sha(project/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()),'CAL source/runtime bytes differ')
    if require_proof:
        proof=read(stage/'CPU-proof.json')
        require(proof['passed'] and proof['scope_sha256']==card['scope_sha256']
            and proof['source_sha256']==reg['payload_sha256']
            and proof['runtime_source_sha256']==reg['runtime_source_sha256']
            and proof['actual_production_entry_imported'] and proof['complete35_tiny_pipeline_accepted']
            and proof['new_sampling_tests_passed'] and proof['unchanged_lifecycle_components_reused']
            and not proof['CUDA_initialized'],'Complete affected-path Linux CPU acceptance required')
    return card,reg,auth


def fresh(project,stage):
    project,stage=Path(project),Path(stage)
    card,reg,auth=validate_stage(project,stage)
    require(not any((stage/n).exists() for n in ('GPU-intent.json','GPU-launch.json','guardian-intent.json'))
        and inspect_container(stage.name+'-gpu') is None,'Existing or unknown original allocation; recover only')
    storage=storage_for(stage);checked=storage.check()
    require(not list(storage.output.iterdir()),'New CAL output must be empty')
    admission=read(stage/'asset-admission.json')
    assets_unchanged(project,read(stage/ASSETS),admission['assets'])
    gpu=selected_gpu(GPU)
    mem=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
    require(not gpu['pids'] and gpu['memory_used_mib']<=1024 and gpu['compute_mode']=='Default'
        and gpu['temperature_C']<90 and mem>=50*2**30,'Fresh idle/temperature/50GiB host-memory admission required')
    return dict(status='F19_CAL35_FRESH_ADMISSION',authorization=auth,
        authorization_sha256=sha(stage/'GPU-authorization.json'),registration_sha256=sha(stage/'registration.json'),
        GPU_submissions=0,gpu=gpu,MemAvailable_bytes=mem,storage=checked,
        forecast_GPUh=card['quote']['forecast_GPUh'],observed_unix=time.time())


def reserve(project,admission):
    pool=Pool(project);auth=admission['authorization'];path=Path(project)/'reports'/(RUN+'.central-reservation.json')
    require(auth['run_id']==RUN and auth['billed_limit_GPUh']==3. and auth['execution_authorized']
        and auth['direct_user_authorization'] and auth['central_transaction_authorized'] and not auth['authorizes_replay'],
        'This exact newly approved CAL card and necessary central bookkeeping only')
    with pool.transaction() as value:
        require(value['cap_gpu_hours']==250 and all(value[k]==v for k,v in pool.accounting(value).items())
            and sorted(j['billed_limit_GPUh'] for j in value['jobs'].values() if hold(j) and j['status']=='RESERVED_OR_RUNNING')==[4.5,12.],
            'Original250 cap, totals and old16.5 liabilities must remain')
        if path.exists():
            saved=read(path)
            require(saved['job']['launch_id']==auth['launch_id'],'Different original CAL reservation')
            if value==saved['central_before']:atomic_json(pool.path,saved['central_after'])
            else:require(value['jobs'].get(RUN)==saved['job'],'Original transaction unknown')
            return saved
        require(RUN not in value['jobs'] and not value.get('budget_overrun_recorded'),'Recover original job or resolve overrun')
        require(0<=time.time()-admission['observed_unix']<=60,'Fresh selected-host admission required')
        admit_host(value,'two_card')
        require(value['available_gpu_hours']>=13.,'Full3GPUh and separate10GPUh confirmation planning margin required')
        gpu=admission['gpu']
        require(gpu['uuid']==GPU and not gpu['pids'] and gpu['memory_used_mib']<=1024,'Fresh actual selected idle device required')
        before=copy.deepcopy(value);after=copy.deepcopy(value)
        job={k:auth[k] for k in IDENTITY}
        job.update(job_id=RUN,registration_sha256=admission['registration_sha256'],authorization_sha256=admission['authorization_sha256'],
            forecast_GPUh=admission['forecast_GPUh'],status='RESERVED_OR_RUNNING',kind='V2',reserved_unix=time.time(),physical_paths=35)
        after['jobs'][RUN]=job;after.update(pool.accounting(after))
        after['events'].append(dict(sequence=len(after['events'])+1,unix=time.time(),type='F19_CAL35_WHOLE3_RESERVE',job_id=RUN))
        receipt=dict(central_ledger_host='four_card',new_reservation=True,job=job,
            central_before=before,central_after=after,observed_unix=time.time())
        create(path,receipt);atomic_json(pool.path,after)
        return receipt


def publish_and_allocate(project,stage,password):
    project,stage=Path(project),Path(stage)
    card,reg,auth=validate_stage(project,stage)
    require(not (stage/'GPU-launch.json').exists(),'Original launch already published; recover only')
    dispatch=read(stage/'GPU-dispatch.json');identity=bind_original_process(os.getpid())
    require(dispatch['guardian_identity']==identity and dispatch['launch_id']==auth['launch_id'],'Exact original dispatcher child required')
    snapshot=read(stage/'central-snapshot.json');envelope=read(stage/'central-reservation.json')
    require(0<=time.time()-snapshot['observed_unix']<=60 and snapshot['ledger']['jobs'][RUN]==envelope['job']
        and envelope['job']['authorization_sha256']==sha(stage/'GPU-authorization.json'),'Fresh original central reservation required')
    # Recheck mutable selected-host resources immediately before its mode owner.
    assets_unchanged(project,read(stage/ASSETS),read(stage/'asset-admission.json')['assets'])
    gpu=selected_gpu(GPU);require(not gpu['pids'] and gpu['memory_used_mib']<=1024 and gpu['temperature_C']<90,'Actual dispatch GPU changed')
    mem=int(next(l.split()[1] for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemAvailable:")))*1024
    require(mem>=50*2**30 and gpu["compute_mode"]=="Default","Fresh dispatch50GiB/mode admission required")
    storage=storage_for(stage);storage.check()
    from cara_fast_host_guardian_r2 import container_arguments
    command=container_arguments(project,stage,storage,sha(stage/'registration.json'),'24,25',os.getuid(),os.getgid(),GPU,40)
    i=command.index(str(stage/'scripts/cara_fast_worker_r2.py'))
    command[i:i+2]=[str(stage/HOST_ENTRY),'supervise']
    j=command.index('--entrypoint')
    command[j:j]=['--cidfile',str(stage/'container.cid'),'-v',str(stage/'src')+':'+str(stage/'src')+':ro',
        '-v',str(stage/'scripts')+':'+str(stage/'scripts')+':ro']
    runtime_python=str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python')
    launch={k:auth[k] for k in IDENTITY}
    launch.update(CPU_fixture_only=False,container=stage.name+'-gpu',guardian_identity=identity,
        registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'GPU-authorization.json'),
        central_reservation_sha256=sha(stage/'central-reservation.json'),admission_sha256=sha(stage/'fresh-admission.json'),
        commands=dict(container_cli=command,runner=[runtime_python,str(stage/RUNNER),'--project',str(project),
            '--stage',str(stage),'--source-revision',auth['source_revision'],'--gpu-uuid',GPU]))
    create(stage/'GPU-launch.json',launch)
    return allocate(project,stage,storage,password)


def capture(project,stage):
    stage=Path(stage)
    if not (stage/'GPU-launch.json').exists():
        return dict(status='NO_PUBLISHED_ORIGINAL_GPU_LAUNCH',intent=(stage/'GPU-intent.json').exists(),GPU_submissions=0)
    result=capture_lifecycle(project,stage,sha(stage/'GPU-launch.json'))
    if result['status']=='ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE':
        result['financial_terminal']=financial_terminal(result,sha(stage/'GPU-launch.json'))
    return result


def settle(project,capture,expected_launch_sha256):
    launch,billing=financial_terminal(capture,expected_launch_sha256)
    require(launch['run_id']==RUN and launch['billed_limit_GPUh']==3.
        and capture['payload_actual_sha256']['src/wcomr/cara_f19_speed190_execution_r1.py']==sha(__file__),
        'Only this original CAL35 actual charge may settle')
    from .policy_price_terminal_r1 import record
    require(record(capture,'authorization')['central_transaction_authorized'],'Necessary original settlement authority required')
    pool=Pool(project);path=Path(project)/'reports'/(RUN+'.central-settlement.json')
    with pool.transaction() as current:
        require(all(abs(current[k]-v)<1e-9 for k,v in Pool.accounting(current).items()),'Central totals differ')
        job=current['jobs'][RUN]
        require(all(job[k]==launch[k] for k in JOB_IDENTITY),'Original central source/job differs')
        if path.exists():
            saved=read(path);audit_settlement(capture,expected_launch_sha256,saved)
            if current==saved['central_before']:atomic_json(pool.path,saved['central_after'])
            else:require(job==saved['central_after']['jobs'][RUN],'Original settlement transaction unknown')
            return saved
        before=copy.deepcopy(current);after=copy.deepcopy(current)
        bill_sha=capture['files']['billing']['sha256']
        if job['status']=='SETTLED':
            require(job['actual_GPUh']==billing['actual_GPUh'] and job['billing_sha256']==bill_sha,'Different settled original bill')
        else:
            require(job['status']=='RESERVED_OR_RUNNING','Unknown original central job state')
            now=time.time();after['jobs'][RUN].update(status='SETTLED',actual_GPUh=billing['actual_GPUh'],billing_sha256=bill_sha,settled_unix=now)
            if billing['actual_GPUh']>3.:after['budget_overrun_recorded']=True
            after.update(Pool.accounting(after))
            after['events'].append(dict(sequence=len(after['events'])+1,unix=now,type='SETTLE_ACTUAL_ADDITIVELY',job_id=RUN))
        value=dict(central_ledger_host='four_card',launch_id=launch['launch_id'],billing_sha256=bill_sha,central_before=before,central_after=after)
        audit_settlement(capture,expected_launch_sha256,value)
        create(path,value)
        if before!=after:atomic_json(pool.path,after)
        return value
