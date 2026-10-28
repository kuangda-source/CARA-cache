"""Q1 source staging and once-only host handoff; no automatic retry."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from .gpu_budget_pool_v2 import atomic_json,sha,process_identity
from .sq_q1_execution_r1 import read,require,validate
from .sq_q1_spec_r1 import (RUN,COUNTS,SCOPE,PROFILE,QUOTES,LIMITS,ASSETS,WEIGHT,
                            MANIFEST_SHA,CHECKPOINT_SHA,CHECKPOINT_BYTES,EXECUTION_CRITICAL)


def exclusive_json(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    descriptor=os.open(str(Path(path).parent),os.O_RDONLY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def verify_lease_fd(project,gpu_uuid,descriptor):
    expected=(Path(project)/'.sync/gpu-locks'/(gpu_uuid+'.lock')).resolve()
    require(expected.is_file(),'Original Q1 lease file is missing')
    actual=Path('/proc/self/fd/'+str(descriptor)).resolve()
    held=os.fstat(int(descriptor));source=expected.stat()
    require(actual==expected and (held.st_dev,held.st_ino)==(source.st_dev,source.st_ino),
            'Inherited original Q1 lease file identity differs')


def stage_path(project,host):
    require(host in LIMITS,'Registered Q1 host required')
    return Path(project)/'.sync'/('cara-sq-q1-saved-'+host.replace('_','-')+'-r2-20261029')


def install(project,host,base,proof,proof_raw,base_registration_sha256):
    """Copy one already accepted CPU source stage, not any tensor/model data."""
    project,base=Path(project),Path(base);stage=stage_path(project,host)
    if stage.exists():return dict(status='Q1_EXISTING_STAGE_RECOVER_ONLY',stage=str(stage),GPU_submissions=0)
    require(base.parent==project/'.sync' and not base.is_symlink(),'Registered CPU source sibling required')
    require(sha(base/'registration.json')==base_registration_sha256,'Original accepted CPU registration differs')
    reg=read(base/'registration.json')
    require(reg.get('GPU_submissions')==0 and reg.get('resource_limits',{}).get('GPU')=='hidden',
            'Original GPU-hidden CPU stage required')
    require(proof['passed'] is True and proof['GPU_submissions']==0 and proof['source_revision']==reg['source_revision']
            and all(reg['payload_sha256'].get(name)==digest
                    for name,digest in proof['critical_source_sha256'].items())
            and set(EXECUTION_CRITICAL)<=set(proof['critical_source_sha256']),
            'Exact complete affected CPU source proof required')
    require(json.loads(proof_raw)==proof,'CPU proof bytes differ')
    require(all(sha(base/name)==digest for name,digest in reg['payload_sha256'].items())
            and all(sha(project/'runtime'/name)==digest for name,digest in reg['runtime_source_sha256'].items()),
            'Accepted source/runtime changed before Q1 staging')
    stage.mkdir(mode=0o700)
    for name in reg['payload_sha256']:
        source=base/name;require(not source.is_symlink(),'Registered source cannot be a symlink')
        path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,path)
    (stage/'cache').mkdir(exist_ok=True);(stage/'cache/runtime').symlink_to(project/'runtime',target_is_directory=True)
    registration=dict(namespace='SQ_Q1_EXECUTION_R1',host=host,stage=str(stage),
        source_revision=reg['source_revision'],payload_sha256=reg['payload_sha256'],
        runtime_source_sha256=reg['runtime_source_sha256'],base_stage=str(base),
        base_registration_sha256=base_registration_sha256,native_hostname=socket.gethostname(),GPU_submissions=0)
    atomic_json(stage/'registration.json',registration)
    (stage/'execution-CPU-proof.json').write_bytes(proof_raw.encode())
    return dict(status='Q1_GPU_SOURCE_STAGED_NO_AUTHORITY',stage=str(stage),host=host,
        source_revision=registration['source_revision'],registration_sha256=sha(stage/'registration.json'),
        CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),GPU_submissions=0,ledger_writes=0)


def verify_assets(project,stage):
    """Bounded, GPU-free streaming SHA before admission; preserve missing assets."""
    project,stage=Path(project),Path(stage);root=project/ASSETS;manifest=root/'manifest.json'
    if not manifest.exists():
        result=dict(status='Q1_ORIGINAL_B1_ABSENT_NOT_ADMISSIBLE',manifest_exists=False,GPU_submissions=0)
        atomic_json(stage/'Q1-asset-verification.json',result);return result
    require(sha(manifest)==MANIFEST_SHA,'Original immutable B1 manifest differs')
    value=read(manifest);refs=value['unique_anchors']+[row['artifact'] for row in value['states']]
    refs={row['name']:row for row in refs};require(len(refs)==32,'Original complete B1 file cohort required')
    refs=dict(refs);refs['__checkpoint__']=dict(name=WEIGHT,sha256=CHECKPOINT_SHA,bytes=CHECKPOINT_BYTES)
    observed={};started=time.monotonic()
    def identity(path):
        stat=path.stat();return [stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns]
    for key,ref in refs.items():
        path=project/WEIGHT if key=='__checkpoint__' else root/ref['name']
        hf_link=key=='__checkpoint__' and path.is_symlink()
        if hf_link:
            blob=project/'cache/huggingface/hub/models--nvidia--Cosmos-Predict2.5-2B/blobs'/CHECKPOINT_SHA
            require(path.resolve(strict=True)==blob.resolve(strict=True),'Original HF snapshot points to a foreign blob')
        require((not path.is_symlink() or hf_link) and (key=='__checkpoint__' or path.resolve().parent==root.resolve())
                and path.stat().st_size==ref['bytes'],'Original B1/weight path or size differs')
        before=identity(path);digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(8*1024**2),b''):
                require(time.monotonic()-started<7200,'Bounded CPU asset SHA timeout')
                digest.update(block)
        require(digest.hexdigest()==ref['sha256'] and identity(path)==before,'Original B1/weight SHA or file identity changed')
        observed[str(path)]=dict(sha256=ref['sha256'],identity=before,
            resolved_path=str(path.resolve()),immutable_HF_link=hf_link)
    result=dict(status='Q1_ORIGINAL_ASSETS_SHA_VERIFIED_CPU_ONLY',manifest_sha256=MANIFEST_SHA,
        checkpoint_sha256=CHECKPOINT_SHA,files=observed,observed_unix=time.time(),
        wall_seconds=time.monotonic()-started,GPU_submissions=0)
    atomic_json(stage/'Q1-asset-verification.json',result);return result


def asset_identity_current(stage):
    path=Path(stage)/'Q1-asset-verification.json'
    if not path.is_file():return False
    value=read(path)
    if value['status']!='Q1_ORIGINAL_ASSETS_SHA_VERIFIED_CPU_ONLY':return False
    for name,ref in value['files'].items():
        path=Path(name)
        if (not path.is_file() or (path.is_symlink() and not ref['immutable_HF_link'])
                or str(path.resolve())!=ref['resolved_path']):return False
        stat=path.stat()
        if [stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns]!=ref['identity']:return False
    return len(value['files'])==33


def reuse_prepared_inputs(project,host,expected):
    """Reuse accepted full digests and empty private storage with fresh identities."""
    from .history104_storage_r2 import StorageGuard
    project=Path(project);stage=stage_path(project,host)
    old=project/'.sync'/('cara-sq-q1-saved-'+host.replace('_','-')+'-r1-20261028')
    require(old.is_dir() and not old.is_symlink() and stage.is_dir(),'Original and corrected Q1 stages required')
    for source in (old,stage):
        require(not any((source/name).exists() for name in (
            'GPU-intent.json','GPU-launch.json','GPU-dispatch-consumed.json','pg-host-guardian.json')),
            'An original Q1 intent exists; recover only')
    names=dict(registration='registration.json',assets='Q1-asset-verification.json',storage='history104-storage.json')
    require(all(sha(old/name)==expected[key+'_sha256'] for key,name in names.items()),
            'Original accepted prepared-input receipt bytes differ')
    require(read(old/'registration.json')['host']==host==read(stage/'registration.json')['host']
            and read(old/'registration.json')['runtime_source_sha256']==read(stage/'registration.json')['runtime_source_sha256']
            and asset_identity_current(old) and sha(project/ASSETS/'manifest.json')==MANIFEST_SHA,
            'Accepted complete asset identities or pinned runtime changed')
    assets=read(old/'Q1-asset-verification.json');contract=read(old/'history104-storage.json')
    require(assets['manifest_sha256']==MANIFEST_SHA and assets['checkpoint_sha256']==CHECKPOINT_SHA
            and contract['run_id']==RUN and contract['output_mount']==str(project/'outputs'/RUN)
            and not any(Path(contract['output_mount']).iterdir()),
            'Only the same verified assets and never-used empty Q1 output may be reused')
    check=StorageGuard(contract).check()
    require(not any((stage/name).exists() for name in ('Q1-asset-verification.json','history104-storage.json',
        'Q1-prepared-inputs-reuse.json')),'Prepared-input binding already exists; recover it')
    for name in ('Q1-asset-verification.json','history104-storage.json'):
        with (stage/name).open('xb') as stream:
            stream.write((old/name).read_bytes());stream.flush();os.fsync(stream.fileno())
    result=dict(status='Q1_ACCEPTED_INPUTS_REBOUND_WITH_FRESH_IDENTITIES_NO_RESCAN',host=host,
        old_stage=str(old),stage=str(stage),original_receipt_sha256=expected,
        assets_current=True,verified_asset_files=33,empty_private_output=True,
        storage_check=check,observed_unix=time.time(),GPU_submissions=0,ledger_writes=0)
    exclusive_json(stage/'Q1-prepared-inputs-reuse.json',result);return result


def prepare_intent(project,host,authority):
    """No process/mode action; an existing intent permanently blocks replay."""
    stage=stage_path(project,host)
    for name in ('GPU-intent.json','GPU-launch.json','GPU-dispatch-consumed.json'):
        require(not (stage/name).exists(),'Original Q1 intent exists; recover only')
    require(authority['direct_user_authorization'] is True and bool(authority['user_quote'])
            and authority['host']==host and authority['run_id']==RUN and authority['scope_counts']==COUNTS
            and authority['whole_GPUh']==LIMITS[host] and authority['authorizes_retry'] is False
            and authority['authorizes_S_collection'] is False,'Exact new Q1-only human authority required')
    require(authority['registration_sha256']==sha(stage/'registration.json')
            and authority['source_revision']==read(stage/'registration.json')['source_revision']
            and authority['CPU_proof_sha256']==sha(stage/'execution-CPU-proof.json')
            and authority['scope_sha256']==sha(stage/SCOPE) and authority['quote_sha256']==sha(stage/QUOTES[host])
            and authority['storage_contract_sha256']==sha(stage/'history104-storage.json')
            and asset_identity_current(stage),'Original source/proof/quote/assets changed')
    # O_EXCL is the at-most-once boundary even if two local controllers race.
    intent=dict(status='SQ_Q1_PRE_GPU_INTENT_NO_DISPATCH_YET',run_id=RUN,
        launch_id=authority['launch_id'],host=host,source_revision=authority['source_revision'],
        registration_sha256=authority['registration_sha256'],gpu_uuid=authority['gpu_uuid'],
        created_unix=time.time(),authorizes_retry=False)
    exclusive_json(stage/'GPU-intent.json',intent)
    atomic_json(stage/'pg-GPU-authorization.json',authority)
    return dict(intent=intent,intent_sha256=sha(stage/'GPU-intent.json'),
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'))


def dispatch(project,host,envelope,intent_sha256,password,*,host_python=sys.executable):
    """Consume the original handoff before spawning; any ambiguity is recover-only."""
    stage=stage_path(project,host)
    require(sha(stage/'GPU-intent.json')==intent_sha256,'Original Q1 intent bytes differ')
    require(all(not (stage/name).exists() for name in ('GPU-launch.json','GPU-dispatch-consumed.json',
        'central-reservation.json','launch-binding.json')),'Original Q1 handoff exists; recover only')
    atomic_json(stage/'central-reservation.json',envelope)
    atomic_json(stage/'launch-binding.json',dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        central_reservation_sha256=sha(stage/'central-reservation.json')))
    scope,registration,authority=validate(project,stage)
    require(asset_identity_current(stage),'Original assets changed before context dispatch')
    consumed=stage/'GPU-dispatch-consumed.json'
    exclusive_json(consumed,dict(intent_sha256=intent_sha256,launch_id=authority['launch_id'],
        consumed_unix=time.time(),no_automatic_replay=True))
    command=[host_python,'-u',str(stage/'scripts/cara_sq_q1_guardian_r1.py'),
        '--project',str(project),'--stage',str(stage)]
    with (stage/'GPU-guardian.log').open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,
            start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
        delivery_error=None
        try:child.stdin.write(json.dumps(dict(sudo_password=password)).encode());child.stdin.close()
        except (BrokenPipeError,OSError) as error:
            delivery_error=type(error).__name__
            try:child.stdin.close()
            except OSError:pass
    if delivery_error:
        exclusive_json(stage/'GPU-credential-delivery-diagnostic.json',dict(
            launch_id=authority['launch_id'],error_type=delivery_error,observed_unix=time.time(),
            authorizes_retry=False))
    # Only the child can publish its PID/start ticks. Credential loss or an
    # early exit cannot turn a consumed handoff into another submission.
    until=time.monotonic()+5
    while time.monotonic()<until:
        if (stage/'GPU-launch.json').exists():
            launch=read(stage/'GPU-launch.json')
            require(launch['launch_id']==authority['launch_id'],'Original child launch differs')
            return launch
        if child.poll() is not None:break
        time.sleep(.02)
    return dict(status='Q1_CONSUMED_HANDOFF_NO_PUBLISHED_LAUNCH_RECOVER_ONLY',
        launch_id=authority['launch_id'],guardian_identity=process_identity(child.pid),
        credential_delivery_error=delivery_error,actual_GPU_started=False,authorizes_retry=False)


def publish_launch(project,stage):
    """Publish this original child before reading any credential pipe."""
    stage=Path(stage);authority=read(stage/'pg-GPU-authorization.json')
    require(stage==stage_path(project,authority['host']) and (stage/'GPU-dispatch-consumed.json').exists(),
            'Original consumed Q1 handoff required')
    launch=dict(status='SQ_Q1_SINGLE_DISPATCHED_HARDWARE_ADMISSION_PENDING',
        **{key:authority[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256',
            'scope_counts','whole_GPUh','registration_sha256')},
        stage=str(stage),container=stage.name+'-gpu',guardian_identity=process_identity(os.getpid()),
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'),started_unix=time.time(),
        actual_GPU_started=False,automatic_retry_authorized=False)
    exclusive_json(stage/'GPU-launch.json',launch);return launch


def preflight(project,host):
    """Fresh read-only physical/resource observation; no reservation or mode change."""
    from .sq_q1_capture_r1 import lock_free
    from .wc73_exclusive_r1 import observe
    from .history104_storage_r2 import storage_for
    project=Path(project);stage=stage_path(project,host)
    reg=read(stage/'registration.json');profile=read(stage/PROFILE)
    require(reg['host']==host and reg['native_hostname']==socket.gethostname(),'Selected stage belongs to another host')
    require(all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
            and all(sha(project/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()),
            'Original source/runtime changed')
    reasons=[]
    probe=stage/'Q1-native-probe.json'
    if not probe.exists() or read(probe).get('status')!='Q1_NATIVE_HOST_COMMAND_CPU_PASS':
        reasons.append('Actual native host command/import CPU probe is not accepted')
    if not asset_identity_current(stage):reasons.append('Original assets not completely SHA-verified/current')
    if (stage/'asset-CPU-launch.json').exists():
        from .gpu_budget_pool_v2 import same_live_process
        scan=read(stage/'asset-CPU-launch.json');terminal=stage/'asset-CPU-exit.json'
        if same_live_process(scan['identity']) or not terminal.exists() or read(terminal).get('exit_code')!=0:
            reasons.append('Original asset CPU process is not cleanly terminal')
    try:storage_for(stage).check()
    except (OSError,ValueError) as error:reasons.append('Private storage not admitted: '+str(error))
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
        if line.startswith('MemAvailable:')))*1024
    if available<profile['minimum_host_MemAvailable_GiB']*2**30:reasons.append('Insufficient available host RAM')
    if not set(map(int,profile['hosts'][host]['cpuset_cpus'].split(',')))<=os.sched_getaffinity(0):
        reasons.append('Registered CPU set unavailable')
    columns='uuid,name,compute_cap,memory.used,utilization.gpu,temperature.gpu'
    raw=subprocess.check_output(['/usr/bin/nvidia-smi','--query-gpu='+columns,
        '--format=csv,noheader,nounits'],text=True,timeout=20)
    candidates=[]
    for line in raw.splitlines():
        uuid,name,cap,memory,util,temperature=[value.strip() for value in line.split(',')]
        expected_name,expected_cap={'two_card':('RTX A6000','8.6'),'four_card':('RTX 6000 Ada','8.9')}[host]
        if expected_name not in name or cap!=expected_cap:continue
        observation=observe(uuid)
        free=all(lock_free(project/'.sync/gpu-locks'/(uuid+suffix)) is not False
                 for suffix in ('.lock','.mode-owner.lock'))
        idle=(observation['compute_apps']==[] and observation['mps_processes']==[]
            and observation['compute_mode'] in ('Default','Exclusive_Process') and free
            and int(util)==0 and 0<=int(memory)<=1024
            and float(temperature)<profile['maximum_idle_admission_temperature_C'])
        candidates.append(dict(uuid=uuid,name=name,compute_cap=cap,memory_used_mib=int(memory),
            utilization_percent=int(util),temperature_C=float(temperature),
            pids=[row.get('pid') for row in observation['compute_apps']],unix=time.time(),
            idle_candidate=idle,hardware_observation=observation))
    selected=next((row for row in candidates if row['idle_candidate']),None)
    return dict(status='Q1_READONLY_PREFLIGHT',host=host,observed_unix=time.time(),
        source_revision=reg['source_revision'],stage=str(stage),registration_sha256=sha(stage/'registration.json'),
        CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),scope_sha256=sha(stage/SCOPE),
        storage_contract_sha256=sha(stage/'history104-storage.json') if (stage/'history104-storage.json').exists() else None,
        quote_sha256=sha(stage/QUOTES[host]),admissible=not reasons and selected is not None,
        selected_gpu=selected,candidates=candidates,reasons=reasons,
        source_bound=True,assets_current=asset_identity_current(stage),MemAvailable_bytes=available,
        GPU_submissions=0,ledger_writes=0)


def provision_storage(project,host,password):
    """Allocate only the frozen 1 GiB private image and 48 MiB journal."""
    from .history104_storage_r2 import FixedJournal,StorageGuard
    project=Path(project);stage=stage_path(project,host);profile=read(stage/PROFILE)
    target=stage/'history104-storage.json'
    if target.exists():
        return dict(status='Q1_EXISTING_PRIVATE_STORAGE_REVERIFIED',storage_contract=read(target),
            check=StorageGuard(read(target)).check(),GPU_submissions=0)
    output=project/'outputs'/RUN;image=Path(profile['hosts'][host]['image_path'])
    journal=Path(profile['hosts'][host]['journal_path']);size=profile['output_image_GiB']*2**30
    require(not output.exists() and not image.exists() and not journal.exists(),
        'Existing partial private storage: recover original, do not overwrite')
    image.parent.mkdir(parents=True,exist_ok=True)
    require(image.parent.stat().st_dev!=journal.parent.stat().st_dev,'Q1 image and control journal must be on different filesystems')
    require(shutil.disk_usage(image.parent).free>size+profile['minimum_storage_host_free_GiB']*2**30
            and shutil.disk_usage(journal.parent).free>128*2**20,'Private storage or journal space unavailable')
    output.mkdir(mode=0o700)
    descriptor=os.open(image,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
    try:os.posix_fallocate(descriptor,0,size);os.fsync(descriptor)
    finally:os.close(descriptor)
    subprocess.run(['/usr/sbin/mkfs.ext4','-q','-F','-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0',
        '-m','0',str(image)],check=True,capture_output=True,timeout=60)
    descriptor=os.open(image,os.O_RDWR)
    try:os.posix_fallocate(descriptor,0,size);os.fsync(descriptor)
    finally:os.close(descriptor)
    def sudo(command):
        result=subprocess.run(['sudo','-S','-p','']+command,input=password+'\n',text=True,capture_output=True,timeout=45)
        require(result.returncode==0,'Private Q1 storage operation failed: '+command[0])
    sudo(['/usr/bin/mount','-o','loop,nodev,nosuid,noexec',str(image),str(output)])
    sudo(['/usr/bin/chown',str(os.getuid())+':'+str(os.getgid()),str(output)])
    sudo(['/usr/bin/rmdir',str(output/'lost+found')]);password=None
    FixedJournal(journal).create()
    contract=dict(version='HISTORY104_PRIVATE_STORAGE_R2',run_id=RUN,output_mount=str(output),
        output_device=output.stat().st_dev,image_path=str(image),image_inode=image.stat().st_ino,
        image_bytes=size,journal_path=str(journal),journal_bytes=48*2**20,
        minimum_output_free_bytes=profile['minimum_output_free_MiB']*2**20,minimum_free_inodes=1024,
        minimum_host_free_bytes=profile['minimum_storage_host_free_GiB']*2**30,
        shared_disk_reserve_ratio_modified=False,reboot_remount_must_be_reverified=True)
    check=StorageGuard(contract).check();atomic_json(target,contract)
    return dict(status='Q1_PRIVATE_STORAGE_PREPARED_NO_GPU',storage_contract=contract,check=check,GPU_submissions=0)


def native_probe(project,host):
    """Actual imports/command and original-container observation; no dispatch/mode action."""
    import importlib.util
    project=Path(project);stage=stage_path(project,host);profile=read(stage/PROFILE)
    from .history104_storage_r2 import storage_for
    from . import sq_gpu_allocation_r1,sq_q1_capture_r1,sq_q1_terminal_r1
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Native probe must hide CUDA')
    storage=storage_for(stage);storage.check()
    spec=importlib.util.spec_from_file_location('q1_native_guardian',stage/'scripts/cara_sq_q1_guardian_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    command=module.container_arguments(project,stage,storage,sha(stage/'registration.json'),
        profile['hosts'][host]['cpuset_cpus'],os.getuid(),os.getgid(),'GPU-CPU-NATIVE-PROBE')
    require(command[command.index('--memory')+1]=='16g' and command.count('--memory-swap')==1
            and command[command.index('--memory-swap')+1]=='16g' and 'torch' not in sys.modules,
            'Native command memory or import boundary differs')
    require(sq_gpu_allocation_r1.SystemOperations().inspect_container(stage,sha(stage/'registration.json'),
        'GPU-CPU-NATIVE-PROBE') is None,'Recover an existing Q1 container before native preparation')
    result=dict(status='Q1_NATIVE_HOST_COMMAND_CPU_PASS',host=host,native_python=sys.version,
        source_revision=read(stage/'registration.json')['source_revision'],
        guardian_sha256=sha(stage/'scripts/cara_sq_q1_guardian_r1.py'),
        command_sha256=hashlib.sha256(json.dumps(command).encode()).hexdigest(),
        command_executed=False,original_container_definitely_absent=True,
        actual_Docker_inspection_only=True,torch_imported=False,GPU_submissions=0,mode_changes=0,ledger_writes=0)
    atomic_json(stage/'Q1-native-probe.json',result);return result


def start_assets(project,host,*,host_python=sys.executable):
    """One recoverable, CPU-affinity-limited source scan before GPU admission."""
    stage=stage_path(project,host);launch=stage/'asset-CPU-launch.json'
    if launch.exists():return dict(status='Q1_EXISTING_ASSET_CPU_HANDLE_RECOVER_ONLY',launch=read(launch))
    exclusive_json(stage/'asset-CPU-intent.json',dict(host=host,created_unix=time.time(),GPU_submissions=0))
    command=['/usr/bin/timeout','--signal=TERM','--kill-after=10s','7200',
        '/usr/bin/ionice','-c','3',host_python,'-u',str(stage/'scripts/cara_sq_q1_assets_cpu_r1.py'),
        '--project',str(project),'--stage',str(stage)]
    with (stage/'asset-CPU.log').open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
                PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
    result=dict(status='Q1_GPU_FREE_ASSET_CPU_STARTED',host=host,identity=process_identity(child.pid),
        started_unix=time.time(),CPUs_max=2,address_space_GiB_max=2,wall_seconds_max=7200,GPU_submissions=0)
    atomic_json(launch,result);return result


def assets_status(project,host):
    from .gpu_budget_pool_v2 import same_live_process
    stage=stage_path(project,host);path=stage/'asset-CPU-launch.json'
    require(path.exists(),'Recover the exact original asset CPU launch')
    launch=read(path);live=same_live_process(launch['identity'])
    return dict(status='Q1_ASSET_CPU_ORIGINAL_STATUS',launch=launch,original_handle_live=live,
        exit=read(stage/'asset-CPU-exit.json') if (stage/'asset-CPU-exit.json').exists() else None,
        verification=read(stage/'Q1-asset-verification.json') if not live and (stage/'Q1-asset-verification.json').exists() else None,
        GPU_submissions=0,ledger_writes=0)
