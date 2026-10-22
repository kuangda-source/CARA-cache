"""One-dispatch, settled-only post and host-bound CPU collection for BANK24.

All expensive work stays behind the real CPU/upstream/unique-v2 gates. The
small orchestration functions are also exercised with explicit CPU fixtures;
there is no fixture or GPU-permission bypass in the production CLI.
"""
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

from four_card_bank24_container_transport_r1 import atomic,identity,alive,LeaseBroker,socket_path
from four_card_bank24_execution_adapter_r1 import CONFIG,LIFECYCLE_SOURCE,ENTRY_SOURCE
from four_card_bank24_gpu_port_r1 import ROOT,SCIENCE_RUN,FULL_CPU_STATUS,read,sha,require,generate,full_quote,require_full_CPU,validate_handoff

TARGET_STAGE='wc-bank24-fourcard-full-execution-r3-20261022'
GPU_LAUNCH='scout-GPU-launch.json'
GPU_INTENT='scout-GPU-dispatch-fence.json'
NLTK_RESOURCE_REL='runtime-resources/nltk-guardrail-d6d4bfa8-r1'
NLTK_MANIFEST_SHA='d43349c4e6b5e31d4f34d600f21c8d49d94cf35b63bd9bb50b05341a37a07571'
PRODUCTION_SCRIPTS=[
    'four_card_bank24_execution_tools_r1.py','four_card_bank24_gpu_port_r1.py',
    'four_card_bank24_execution_adapter_r1.py','four_card_bank24_container_transport_r1.py',
    'supervise_wc_four_card_bank24_gpu_r1.py','run_wc_four_card_bank24_inner_r1.py',
    'watch_wc_four_card_bank24_post_r1.py','run_wc_four_card_bank24_collector_cpu_r1.py',
    'wc_four_card_bank24_execution_r2.py','wc_four_card_resource_cpu_r4.py']


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def verify_registration(stage):
    stage=Path(stage).resolve();reg=read(stage/'registration.json')
    require(reg['namespace']=='BANK24_FOURCARD_GPU_PORT_R1','Wrong registered host scope')
    for name,expected in reg['payload_sha256'].items():
        path=stage/name
        require(not path.is_symlink() and stage in path.resolve().parents and sha(path)==expected,
                'Registered immutable production payload differs: '+name)
    return reg


def process_environment(project,cache_root,gpu_uuid=None):
    project=Path(project);cache_root=Path(cache_root);site=project/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages'
    caches=dict(TORCHINDUCTOR_CACHE_DIR='torchinductor',TRITON_CACHE_DIR='triton',
        TORCH_EXTENSIONS_DIR='extensions',CUDA_CACHE_PATH='cuda',XDG_CACHE_HOME='xdg')
    for name in caches.values():(cache_root/name).mkdir(parents=True,exist_ok=True)
    value=dict(USER='gaokuangda',LOGNAME='gaokuangda',PYTHONDONTWRITEBYTECODE='1',
        WC_SCOUT_KIND='BANK24',
        CUDA_VISIBLE_DEVICES=gpu_uuid or '',NVIDIA_VISIBLE_DEVICES=gpu_uuid or 'void',
        HF_HOME=str(project/'cache/huggingface'),HF_HUB_CACHE=str(project/'cache/huggingface/hub'),
        NLTK_DATA=str(project/NLTK_RESOURCE_REL),
        TORCH_HOME=str(project/'cache/torch'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',
        CUDA_HOME=str(site/'nvidia/cuda_nvrtc'),CUDA_PATH=str(site/'nvidia/cuda_nvrtc'),
        PATH=str(project/'system-libs-r1/usr/bin')+':/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin')
    libraries=[project/'system-libs-r1/usr/lib/x86_64-linux-gnu',project/'system-libs-r1/lib/x86_64-linux-gnu']
    libraries += [site/'nvidia'/n/'lib' for n in ['cuda_nvrtc','cuda_runtime','cudnn','nvjitlink','cublas']]+[site/'torch/lib']
    value['LD_LIBRARY_PATH']=':'.join(map(str,libraries))
    value.update({k:str(cache_root/v) for k,v in caches.items()});return value


def verify_nltk_resources(project):
    """Check the actual files before any GPU observation, reservation or spawn."""
    root=Path(project)/NLTK_RESOURCE_REL;receipt=root.with_suffix('.manifest.json')
    require(root.is_dir() and not root.is_symlink() and root.resolve()==root.absolute(),
            'Physical Guardrail NLTK resources required')
    require(receipt.is_file() and not receipt.is_symlink() and sha(receipt)==NLTK_MANIFEST_SHA,
            'Pinned NLTK manifest required')
    manifest=read(receipt);paths=list(root.rglob('*'))
    require(not any(p.is_symlink() for p in paths),'NLTK resources must not contain symbolic links')
    require({p.relative_to(root).as_posix() for p in paths if p.is_file()}==set(manifest['files']),
            'NLTK file inventory differs')
    for name,expected in manifest['files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,'Unsafe NLTK path')
        p=root/name
        require(p.stat().st_size==expected['bytes'] and sha(p)==expected['sha256'],
                'Pinned NLTK bytes differ: '+name)
    return dict(root=str(root),manifest_sha256=NLTK_MANIFEST_SHA,files=len(manifest['files']))


def build_template(inputs,destination,source,recipe,script_directory):
    """Copy frozen science bytes, then make a distinct host registration."""
    import shutil
    inputs=Path(inputs);destination=Path(destination);destination.mkdir()
    metadata=recipe['execution_metadata']
    bindings=dict(metadata['original_payload_sha256'],**metadata['additional_metadata_sha256'])
    require(len(metadata['original_payload_sha256'])==1789 and len(metadata['additional_metadata_sha256'])==29,
            'Unchanged 1789 plus separately listed29 files required')
    payload={}
    for name,expected in bindings.items():
        src=inputs/name;require(not src.is_symlink() and sha(src)==expected,'Original input changed: '+name)
        target=destination/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
        payload['inputs/'+name]=expected
    sources,binding=generate(destination/'inputs')
    for name,body in sources.items():
        (destination/name).write_text(body);payload[name]=sha(destination/name)
    for name in PRODUCTION_SCRIPTS:
        shutil.copyfile(Path(script_directory)/name,destination/name);payload[name]=sha(destination/name)
    c=read(destination/'inputs'/CONFIG);q=full_quote(read(inputs/'reports/wc_scout_BANK24_whole_quote_R1_20261018.json'),c['scope_counts'])
    atomic(destination/'whole24-planning-quote.json',q);payload['whole24-planning-quote.json']=sha(destination/'whole24-planning-quote.json')
    target=Path(recipe['workspace'])/'.sync'/TARGET_STAGE
    meta=dict(namespace='BANK24_FOURCARD_GPU_PORT_R1',host_source_revision=source,entry_stage=str(target),
        config_ref='inputs/'+CONFIG,config_sha256=sha(destination/'inputs'/CONFIG),scope_counts=c['scope_counts'],
        scientific_lifecycle_source=LIFECYCLE_SOURCE,scientific_entry_source=ENTRY_SOURCE,
        container_image_id=recipe['container_image_id'],scientific_source_modifications=0,
        scientific_run_id=c['run_id'],execution_run_id=SCIENCE_RUN)
    atomic(destination/'host-lifecycle-dependency.json',meta);payload['host-lifecycle-dependency.json']=sha(destination/'host-lifecycle-dependency.json')
    reg=dict(namespace='BANK24_FOURCARD_GPU_PORT_R1',source_revision=source,payload_sha256=payload,
        runtime_source_sha256=recipe['runtime_source_sha256'],original_payload_count=1789,extra_metadata_count=29,
        original_scientific_lifecycle_source=LIFECYCLE_SOURCE,original_scientific_entry_source=ENTRY_SOURCE)
    atomic(destination/'registration.json',reg)
    return dict(target_stage=str(target),registration_sha256=sha(destination/'registration.json'),
        generated_sha256={n:sha(destination/n) for n in sources},port_binding=binding,
        scope_counts=c['scope_counts'],planning_quote=q,planning_quote_sha256=sha(destination/'whole24-planning-quote.json'),source_revision=source)


def validate_authorization(project,stage,auth):
    project=Path(project).resolve();stage=Path(stage).resolve()
    require(project==Path(ROOT).resolve() and stage==project/'.sync'/TARGET_STAGE,'Only the independent four-card production namespace is allowed')
    require(not (stage/'CPU-TEST-ONLY.json').exists(),'A CPU fixture cannot be a production GPU stage')
    reg=verify_registration(stage);accepted=require_full_CPU(stage,reg['source_revision']);meta=read(stage/'host-lifecycle-dependency.json')
    require(auth.get('direct_user_authorization') is True and auth.get('autonomy_exclusive_upper_GPUh')==12,
            'Existing direct whole-under12 authority required')
    require(auth['source_revision']==reg['source_revision'] and auth['registration_sha256']==sha(stage/'registration.json')
        and auth['scope_counts']==meta['scope_counts'] and auth['config_sha256']==meta['config_sha256'],'Actual complete scope/source differs')
    require(auth['production_CPU_sha256']==sha(stage/'scout-lifecycle-CPU-proof.json')
        and auth['independent_CPU_acceptance_sha256']==sha(stage/'scout-lifecycle-CPU-independent-acceptance.json'), 'Actual full CPU bytes differ')
    require(auth['unique_handoff_sha256']==sha(stage/'unique-v2-handoff.json'),'External unique writer proof differs')
    handoff=validate_handoff(project,read(stage/'unique-v2-handoff.json'))
    quote=read(stage/'whole24-planning-quote.json')
    require(auth['planning_quote_sha256']==sha(stage/'whole24-planning-quote.json')
        and auth['forecast_GPUh']==quote['forecast_complete_GPUh'] and auth['billed_limit_GPUh']==quote['billed_limit_GPUh']
        and math.isfinite(auth['forecast_GPUh']) and 0<auth['forecast_GPUh']<=auth['billed_limit_GPUh']<12,
        'Complete finite strictly-under12 planning quote required')
    require(auth['gpu_uuid'].startswith('GPU-') and auth['launch_id'] and len(auth['launch_id'])<=64,'Fresh single launch/UUID required')
    require(auth['launch_id'].replace('-','').isalnum(),'Unsafe container launch identity')
    for name,key in [('scout-upstream-capture.json.gz','upstream_capture_sha256'),('scout-upstream-acceptance.json','upstream_acceptance_sha256'),
                     ('scout-frozen-CAL-gate.json','frozen_gate_sha256')]:
        require(sha(stage/name)==auth[key],'Original accepted upstream bytes differ')
    sys.path.insert(0,str(stage/'inputs/src'))
    os.environ['WC_SCOUT_KIND']='BANK24'
    from wcomr.scout_gpu_lifecycle_r1 import verify_upstream
    upstream=read(stage/'scout-upstream-capture.json.gz');upaccepted=read(stage/'scout-upstream-acceptance.json')
    require(upaccepted['capture_sha256']==sha(stage/'scout-upstream-capture.json.gz'),'Actual upstream acceptance binding differs')
    verify_upstream('BANK24',upstream,upaccepted,read(stage/'scout-frozen-CAL-gate.json'))
    return reg,meta,quote,handoff


def restore_only(stage):
    stage=Path(stage)
    if (stage/GPU_LAUNCH).is_file():return read(stage/GPU_LAUNCH)
    if (stage/GPU_INTENT).exists():
        return dict(status='DISPATCH_FENCE_PRESENT_UNKNOWN_RESTORE_ONLY',stage=str(stage),
            intent=read(stage/GPU_INTENT),no_GPU_relaunch_authority=True)
    return None


def spawn_once(stage,launch_fields,supervisor_command,watcher_command):
    """One durable Popen boundary, shared by production and explicit CPU tests.

    No gates live in this small primitive. Only validated production caller
    builds real GPU commands; tests use CPU commands in job/TEST_ONLY.
    """
    stage=Path(stage)
    with (stage/'dispatch-control.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        old=restore_only(stage)
        if old:return old
        fence=dict(source_revision=launch_fields['source_revision'],launch_id=launch_fields['launch_id'],
            created_unix=time.time(),no_replay=True)
        with (stage/GPU_INTENT).open('x') as f:json.dump(fence,f);f.flush();os.fsync(f.fileno())
        value=dict(launch_fields,started_unix=time.time(),post_watcher_identity=None,post_watcher_pid=None)
        try:
            with (stage/'supervisor.log').open('x') as log:
                child=subprocess.Popen(supervisor_command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                    start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
            who=identity(child.pid);require(who is not None,'Started original supervisor identity unknown; restore only')
            value.update(supervisor_identity=who,supervisor_pid=child.pid,command=supervisor_command,
                halfway_check_not_before_unix=value['started_unix']+math.ceil(value['forecast_GPUh']*1800),
                next_check_not_before_unix=value['started_unix']+math.ceil(value['forecast_GPUh']*3600+900))
            atomic(stage/GPU_LAUNCH,value)
            with (stage/'post-watcher-intent.json').open('x') as f:json.dump(dict(launch_id=value['launch_id'],created_unix=time.time()),f)
            with (stage/'post-watcher.log').open('x') as log:
                post=subprocess.Popen(watcher_command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                    start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
            value.update(post_watcher_identity=identity(post.pid),post_watcher_pid=post.pid,post_command=watcher_command)
        except BaseException as error:
            value.update(status='DISPATCH_BOUNDARY_UNKNOWN_RESTORE_ONLY',error_type=type(error).__name__,error=str(error),no_GPU_relaunch_authority=True)
            atomic(stage/GPU_LAUNCH,value);raise
        atomic(stage/GPU_LAUNCH,value);return value


def dispatch(project,stage,auth):
    with (Path(stage)/'GPU-admission-control.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _dispatch_locked(project,stage,auth)


def _dispatch_locked(project,stage,auth):
    old=restore_only(stage)
    if old:return old
    project=Path(project);stage=Path(stage)
    reg,meta,quote,handoff=validate_authorization(project,stage,auth)
    verify_nltk_resources(project)
    controller=module('bound_GPU_controller',stage/'supervise_wc_four_card_bank24_gpu_r1.py')
    gpu=controller.observe(auth['gpu_uuid']);poolmod=module('bound_SM89_pool',stage/'bank24_sm89_budget_pool.py');pool=poolmod.BudgetPool(project).read()
    from four_card_bank24_execution_adapter_r1 import device_gate
    if not device_gate(gpu) or any(j['status']=='RESERVED_OR_RUNNING' and j['gpu_uuid']==auth['gpu_uuid'] for j in pool['jobs'].values()):
        return dict(status='SCOUT_RESOURCE_BUSY_NOT_DISPATCHED_NO_FENCE',GPU_submissions=0,ledger_written=False,gpu=gpu)
    require(pool['available_gpu_hours']>=quote['billed_limit_GPUh'],'Insufficient balance for the complete whole card')
    require(not (project/'outputs'/SCIENCE_RUN).exists(),'Original output exists; restore only')
    atomic(stage/'GPU-process-environment.json',process_environment(project,stage/'GPU-process-caches',auth['gpu_uuid']))
    atomic(stage/'scout-GPU-authorization.json',auth)
    fields=dict(status='SCOUT_COMPLETE_CARD_DISPATCHED_ADMISSION_PENDING',kind='BANK24',project=str(project),stage=str(stage),
        run_id=SCIENCE_RUN,source_revision=reg['source_revision'],entry_source_revision=reg['source_revision'],
        entry_stage=str(stage),entry_registration_sha256=sha(stage/'registration.json'),registration_sha256=sha(stage/'registration.json'),
        config_sha256=meta['config_sha256'],production_CPU_sha256=auth['production_CPU_sha256'],
        independent_CPU_acceptance_sha256=auth['independent_CPU_acceptance_sha256'],dependency_sha256=sha(stage/'host-lifecycle-dependency.json'),
        authorization_sha256=sha(stage/'scout-GPU-authorization.json'),launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],
        scope_counts=meta['scope_counts'],matrix=quote['positions'],forecast_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'],
        actual_admission_accepted=False,new_quality_or_speed_result=False)
    supervisor=['python3',str(stage/'supervise_wc_four_card_bank24_gpu_r1.py'),'--stage',str(stage),'--authorization',str(stage/'scout-GPU-authorization.json')]
    watcher=['python3',str(stage/'watch_wc_four_card_bank24_post_r1.py'),'--stage',str(stage)]
    return spawn_once(stage,fields,supervisor,watcher)


def post_conditions(project,stage,launch,container_state):
    """Read-only preconditions; an unknown container never counts as exited."""
    project=Path(project);stage=Path(stage);out=project/'outputs'/launch['run_id']
    sup=read(out/'supervisor.json') if (out/'supervisor.json').is_file() else {}
    inner=read(stage/'inner-supervisor.json') if (stage/'inner-supervisor.json').is_file() else {}
    handles=[launch.get('supervisor_identity'),sup.get('supervisor_identity'),sup.get('child_identity'),inner.get('identity'),inner.get('child_identity')]
    require(not any(alive(x) for x in handles),'Original host/inner/runner still live; post must wait')
    require(sup.get('status')=='SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
        and sup.get('owned_container_exit_verified') is True,'GPU container exit and settlement are not verified')
    require(container_state in ('ABSENT','EXITED'),'GPU container is running or unknown')
    bill=read(out/'billing.json');pool=read(project/'reports/gpu-budget-v2.json');job=pool['jobs'][launch['run_id']]
    require(job['status']=='SETTLED' and job['billing_sha256']==sha(out/'billing.json')==sup['billing_sha256']
        and job['actual_GPUh']==bill['actual_GPUh'],'Original whole wall not settled')
    require(all(bill[k]==launch[k] for k in ['launch_id','run_id','source_revision','gpu_uuid','scope_counts']), 'Settled foreign job')
    require(math.isfinite(bill['wall_seconds']) and bill['wall_seconds']>0
        and math.isclose(bill['wall_seconds']/3600,bill['actual_GPUh'],rel_tol=1e-12),'Invalid additive actual wall')
    path=project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.lock')
    with path.open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    return sup


def cpu_container(project,stage,observation,mode,image,timeout=150):
    """Real GPU-hidden CPU container, bound by actual Docker peer and FD.

    The descriptor is an observation lock, never a released GPU UUID lease.
    """
    project=Path(project);stage=Path(stage);observation=Path(observation)
    require(observation.is_dir() and stage in observation.resolve().parents,'Own observation directory required')
    lease=observation/'observation.lock';fd=os.open(lease,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    manifest=dict(mode=mode,project=str(project),stage=str(stage),observation=str(observation),
        host_snapshot_sha256=sha(observation/'host-snapshot.json'),
        nonce=secrets.token_hex(24),container='wc-bank24-cpu-'+secrets.token_hex(8),created_unix=time.time())
    atomic(observation/'cpu-manifest.json',manifest);label=sha(observation/'cpu-manifest.json')
    broker=LeaseBroker(observation,fd,lease,manifest['nonce'],label,manifest['container'])
    args=['docker','run','--rm','--read-only','--network','none','--pid','host','--name',manifest['container'],
        '--label','wcomr.manifest='+label,'--user',str(os.getuid())+':'+str(os.getgid()),'--cpus','2','--memory','16g','--pids-limit','256',
        '--tmpfs','/tmp:rw,size=1g','-v',ROOT+':'+ROOT+':ro','-v',str(stage)+':'+str(stage)+':rw',
        '-v',str(observation)+':'+str(observation)+':rw','-v',str(socket_path(observation).parent)+':'+str(socket_path(observation).parent)+':ro',
        '-w',str(stage)]
    if str(project)!=ROOT:args+=['-v',str(project)+':'+str(project)+':ro']
    for k,v in process_environment(ROOT,observation/'process-caches').items():args+=['-e',k+'='+v]
    args+=['--entrypoint',str(Path(ROOT)/'envs/wc-cosmos-py310-cu128-r3/bin/python'),image,
        str(stage/'run_wc_four_card_bank24_collector_cpu_r1.py'),'--manifest',str(observation/'cpu-manifest.json')]
    atomic(observation/'container-command.json',args);broker.start();child=None;verified_exit=False
    try:
        with (observation/'CPU-container.log').open('x') as log:
            child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            try:code=child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Stop only the container carrying this exact manifest label.
                check=subprocess.run(['docker','inspect',manifest['container']],capture_output=True,text=True,timeout=15)
                require(check.returncode==0 and json.loads(check.stdout)[0]['Config']['Labels'].get('wcomr.manifest')==label,
                        'Owned CPU container identity unknown; retain handle')
                subprocess.run(['docker','stop','--time','5',manifest['container']],check=True,capture_output=True,timeout=20)
                child.wait(timeout=10);code=124
        require(broker.failure is None and broker.record is not None,'Actual CPU Docker peer handoff failed')
        require(code==0,'Original CPU post/collector failed; preserve its bounded log')
        controller=module('registered_CPU_container_state',stage/'supervise_wc_four_card_bank24_gpu_r1.py')
        require(controller.owned_container_state(manifest['container'],label) in ('ABSENT','EXITED'),
                'Original CPU container exit unknown; retain handle')
        verified_exit=True
        result=read(observation/'cpu-result.json')
        require(result['actual_CPU_identity']['pid']==broker.record['peer_identity']['pid']
            and result['actual_CPU_identity']['start_ticks']==broker.record['peer_identity']['start_ticks'], 'CPU collector PID differs')
        result['host_verified_Docker_peer']=broker.record
        result['host_verified_CPU_container_exit']=True
        return result
    finally:
        if child is not None and child.poll() is None:
            owned=subprocess.run(['docker','inspect',manifest['container']],capture_output=True,text=True,timeout=15)
            if owned.returncode==0 and json.loads(owned.stdout)[0]['Config']['Labels'].get('wcomr.manifest')==label:
                subprocess.run(['docker','stop','--time','5',manifest['container']],capture_output=True,timeout=20)
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:pass
        broker.close();fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)
        atomic(observation/'host-release.json',dict(original_CPU_container_exit_verified=verified_exit,
            original_observation_FD_closed=True,original_IPC_directory_removed=not socket_path(observation).parent.exists(),
            actual_authoritative_UUID_lock_opened=False))


def capture_host(project,stage,launch,mode,telemetry):
    """One host observation and telemetry pair; no scientific partials."""
    project=Path(project);stage=Path(stage);reg=verify_registration(stage);out=project/'outputs'/launch['run_id']
    sup=read(out/'supervisor.json') if (out/'supervisor.json').is_file() else {}
    inner=read(stage/'inner-supervisor.json') if (stage/'inner-supervisor.json').is_file() else {}
    handles=dict(supervisor=launch.get('supervisor_identity'),post=launch.get('post_watcher_identity'),inner=inner.get('identity'),runner=inner.get('child_identity'))
    if not handles['post'] and (stage/'post-watcher-once.json').is_file():
        watcher=read(stage/'post-watcher-once.json')
        require(watcher.get('launch_id')==launch['launch_id'],'Recovered watcher belongs to another launch')
        handles['post']=watcher['identity']
    processes={k:identity(v['pid']) for k,v in handles.items() if v}
    live={k:alive(v) for k,v in handles.items()}
    container_state='ABSENT'
    container_manifest=read(stage/'gpu-container-manifest.json') if (stage/'gpu-container-manifest.json').is_file() else {}
    if sup.get('container') or container_manifest:
        controller=module('registered_GPU_container_state',stage/'supervise_wc_four_card_bank24_gpu_r1.py')
        container_state=controller.owned_container_state(sup.get('container',container_manifest.get('container')),
            sup.get('container_manifest_sha256') or sha(stage/'gpu-container-manifest.json'))
    live['GPU_container']=container_state not in ('ABSENT','EXITED')
    post_manifest=stage/'post-CPU-observation/cpu-manifest.json'
    if post_manifest.is_file():
        pm=read(post_manifest);controller=module('registered_post_CPU_state',stage/'supervise_wc_four_card_bank24_gpu_r1.py')
        live['post_CPU_container']=controller.owned_container_state(pm['container'],sha(post_manifest)) not in ('ABSENT','EXITED')
    pool=read(project/'reports/gpu-budget-v2.json')
    value=dict(status='BANK24_FOURCARD_ORIGINAL_ONCE_CAPTURE',mode=mode,observed_unix=time.time(),launch=launch,
        registration_sha256=sha(stage/'registration.json'),pool=pool,expected_original_handles=handles,
        original_processes=processes,original_live_handles=live,GPU_container_state=container_state,
        GPU_submissions=0,ledger_written=False,own_UUID_lock_free=False)
    value.update(telemetry(launch['gpu_uuid']))
    path=project/'.sync/gpu-locks'/(launch['gpu_uuid']+'.lock')
    if path.is_file():
        with path.open('r') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);value['own_UUID_lock_free']=True;fcntl.flock(lock,fcntl.LOCK_UN)
            except BlockingIOError:pass
    value['other_reservation_identities']={k:identity(j['supervisor_pid']) for k,j in pool['jobs'].items()
        if k!=launch['run_id'] and j['status']=='RESERVED_OR_RUNNING' and j['gpu_uuid']==launch['gpu_uuid']}
    if mode!='terminal' or any(live.values()):
        value.update(scientific_partial_read=False,technical_progress=dict(supervisor_status=sup.get('status'),
            planned_slots=24,settlement_status=pool['jobs'].get(launch['run_id'],{}).get('status')))
    return value


def gpu_telemetry(uuid):
    try:
        own=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
        return dict(own_GPU=own,compute_apps=apps,GPU_telemetry_calls=1)
    except (OSError,subprocess.SubprocessError) as error:return dict(GPU_telemetry_error=type(error).__name__,GPU_telemetry_calls=1)


def collect_once(project,stage,launch,mode,observation,telemetry=gpu_telemetry):
    """Host telemetry once, then CPU physical-artifact audit after full exit."""
    observation=Path(observation);observation.mkdir()
    value=capture_host(project,stage,launch,mode,telemetry)
    atomic(observation/'host-snapshot.json',value)
    if mode!='terminal' or any(value['original_live_handles'].values()):return value
    meta=read(Path(stage)/'host-lifecycle-dependency.json')
    result=cpu_container(project,stage,observation,'collect',meta['container_image_id'])
    value=result['capture'];value['CPU_collector_binding']={k:v for k,v in result.items() if k!='capture'}
    return value
