"""Explicit B operations. Authority is supplied externally; UNKNOWN never launches."""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .cara_fast_b36_execution_r1 import RUN,PROFILE,SPEC,QUOTE,admitted_inputs,validate,read,require
from .gpu_budget_pool_v2 import DeviceLease,atomic_json,process_identity,sha,same_live_process
from .history104_storage_r2 import FixedJournal,StorageGuard,storage_for

ASSETS='plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'
STAGE_NAME='cara-fast-f19-b36-a6000-r1-20261029'


def create(path,value):
    path=Path(path)
    with path.open('x') as handle:
        json.dump(value,handle,indent=2,allow_nan=False);handle.write('\n')
        handle.flush();os.fsync(handle.fileno())
    descriptor=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def validate_grant(authority,profile):
    require(authority.get('direct_user_authorization') is True and bool(authority.get('user_quote'))
        and authority.get('new_B36_authorization') is True and authority.get('authorizes_replay') is False,
        'Separate human B36 approval required; preparation does not grant it')
    expected=dict(run_id=RUN,phase='B',physical_paths=36,whole_GPUh=5.5,host='two_card',
        gpu_uuid=profile['A_gpu_uuid'],A_launch_id=profile['A_launch_id'],
        frozen_file_sha256=profile['A_frozen_sha256'],scope_sha256=profile['scope_sha256'])
    require(all(authority.get(key)==value for key,value in expected.items()),'Exact whole B36 authority required')
    require(profile['A_host']=='two_card' and authority.get('launch_id') not in (None,'',profile['A_launch_id']),
            'New B launch on the original A physical device required')


def prepare_stage(project,stage,payload):
    project,stage=Path(project),Path(stage)
    require(stage.parent==project/'.sync' and stage.name==STAGE_NAME,'Exact B stage required')
    require(not stage.exists(),'Existing B stage: recover it, never overwrite or replace')
    validate_grant(payload['authority'],json.loads(base64.b64decode(payload['files'][PROFILE])))
    base=Path(payload['base_stage'])
    require(sha(base/'registration.json')==payload['base_registration_sha256'],'Original A base changed')
    require(all(sha(project/'runtime'/name)==expected for name,expected in payload['runtime_source_sha256'].items()),
            'Pinned runtime changed')
    stage.mkdir(mode=0o700)
    for name,expected in payload['hashes'].items():
        relative=Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts,'Invalid staged relative path')
        target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if name in payload['files']:
            raw=base64.b64decode(payload['files'][name])
            require(hashlib.sha256(raw).hexdigest()==expected,'Changed B overlay bytes')
            target.write_bytes(raw)
        else:
            require(sha(base/name)==expected,'Changed original A source')
            shutil.copyfile(base/name,target)
    profile=read(stage/PROFILE)
    authority=dict(payload['authority'])
    validate_grant(authority,profile)
    registration=dict(host='two_card',stage=str(stage),source_revision=payload['source_revision'],
        base_A_source_revision=payload['base_source_revision'],base_A_registration_sha256=payload['base_registration_sha256'],
        payload_sha256=payload['hashes'],runtime_source_sha256=payload['runtime_source_sha256'])
    create(stage/'registration.json',registration)
    create(stage/'execution-CPU-proof.json',payload['CPU_proof'])
    create(stage/'B36-core-CPU-proof.json',payload['core_CPU_proof'])
    authority.update(registration_sha256=sha(stage/'registration.json'),CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),
        core_CPU_proof_sha256=sha(stage/'B36-core-CPU-proof.json'))
    create(stage/'pg-GPU-authorization.json',authority)
    admitted_inputs(project,stage)
    return dict(status='B36_SOURCE_PREPARED_NO_GPU',stage=str(stage),registration_sha256=sha(stage/'registration.json'),
                launch_id=authority['launch_id'],GPU_submissions=0)


def assets_check(project,specification):
    """Hash actual content once, then retain inode/time stamps for dispatch revalidation."""
    result=[]
    for descriptor in specification['files']:
        path=Path(project)/descriptor['path']
        require(path.is_file() and not path.is_symlink(),'Original regular asset required')
        before=path.stat()
        require(before.st_size==descriptor['bytes'],'Asset size changed')
        if descriptor['digest_kind']=='sha256':value=hashlib.sha256()
        elif descriptor['digest_kind']=='git_blob_sha1':value=hashlib.sha1(b'blob '+str(before.st_size).encode()+b'\0')
        else:raise ValueError('Unknown registered asset digest')
        with path.open('rb') as handle:
            for chunk in iter(lambda:handle.read(4*1024**2),b''):value.update(chunk)
        after=path.stat()
        stamp=lambda stat:[stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns]
        require(stamp(before)==stamp(after) and value.hexdigest()==descriptor['digest'],'Actual asset content changed')
        result.append(dict(path=descriptor['path'],digest=value.hexdigest(),stamp=stamp(after)))
    for link in specification['snapshot_links']:
        path=Path(project)/link['path']
        require(path.is_symlink() and path.resolve()==(Path(project)/link['target']).resolve(),'Frozen snapshot pointer changed')
    return result


def assets_unchanged(project,specification,accepted):
    require(len(accepted)==len(specification['files']),'Complete fresh asset receipt required')
    for descriptor,row in zip(specification['files'],accepted):
        path=Path(project)/descriptor['path'];stat=path.stat()
        require(not path.is_symlink() and row['path']==descriptor['path'] and row['digest']==descriptor['digest']
            and row['stamp']==[stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns],
            'An asset changed after its full digest; perform fresh admission')
    for link in specification['snapshot_links']:
        path=Path(project)/link['path']
        require(path.is_symlink() and path.resolve()==(Path(project)/link['target']).resolve(),'Snapshot pointer changed')


def selected_gpu(uuid):
    fields='uuid,name,compute_cap,utilization.gpu,memory.used,compute_mode,temperature.gpu'
    values=subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,'--query-gpu='+fields,
        '--format=csv,noheader,nounits'],text=True,timeout=20).strip().split(',')
    values=[value.strip() for value in values]
    apps=subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,'--query-compute-apps=pid',
        '--format=csv,noheader,nounits'],text=True,timeout=20)
    return dict(uuid=values[0],name=values[1],compute_cap=values[2],utilization_percent=int(values[3]),
        memory_used_mib=int(values[4]),compute_mode=values[5],temperature_C=int(values[6]),
        pids=[int(value) for value in apps.splitlines() if value.strip()],unix=time.time())


def fresh_idle(project,authority,profile):
    gpu=selected_gpu(authority['gpu_uuid'])
    require(gpu['uuid']==authority['gpu_uuid'] and 'RTX A6000' in gpu['name'] and gpu['compute_cap']=='8.6'
        and gpu['utilization_percent']==0 and not gpu['pids'] and 0<=gpu['memory_used_mib']<=1024
        and gpu['temperature_C']<90 and gpu['compute_mode'] in ('Default','Exclusive_Process'),'Selected A GPU is not admissible')
    memory=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    host=profile['hosts']['two_card']
    require(memory>=host['minimum_host_MemAvailable_GiB']*2**30,'Host memory below the registered margin')
    require(set(map(int,host['cpuset_cpus'].split(',')))<=os.sched_getaffinity(0),'GPU host CPU cores unavailable')
    with DeviceLease(project,authority['gpu_uuid']):pass
    mode_path=Path(project)/'.sync/gpu-locks'/(authority['gpu_uuid']+'.mode-owner.lock')
    with mode_path.open('a+') as handle:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    return gpu,memory


def english_resources(project):
    from four_card_bank24_execution_tools_r1 import NLTK_RESOURCE_REL,NLTK_MANIFEST_SHA
    nltk_root=Path(project).resolve()/NLTK_RESOURCE_REL;manifest=nltk_root.with_suffix('.manifest.json')
    require(sha(manifest)==NLTK_MANIFEST_SHA and nltk_root.is_dir() and not nltk_root.is_symlink(),'Original NLTK bundle differs')
    entries=read(manifest)['files'];english=[name for name in entries if name.startswith('tokenizers/punkt_tab/english/')]
    require(len(english)==4,'Four actual English resources required')
    for name in english:
        path=nltk_root/name
        require(not path.is_symlink() and path.stat().st_size==entries[name]['bytes'] and sha(path)==entries[name]['sha256'],
                'English resource changed')
    return dict(manifest_sha256=NLTK_MANIFEST_SHA,English_files=english)


def provision(project,stage,password):
    admitted_inputs(project,stage)
    project,stage=Path(project),Path(stage)
    if (stage/'history104-storage.json').exists():
        return dict(status='B36_ORIGINAL_STORAGE_RECOVERED',check=storage_for(stage).check())
    require(not (stage/'storage-provision-intent.json').exists(),'Partial storage: recover original provision, never recreate')
    host=read(stage/PROFILE)['hosts']['two_card']
    image,out,journal=(Path(host[key]) for key in ('image_path','output_mount','journal_path'))
    require(not any(path.exists() for path in (image,out,journal)),'Existing storage requires original recovery')
    require(shutil.disk_usage(image.parent.parent).free>=host['minimum_SSD_free_before_provision_GiB']*2**30
            and shutil.disk_usage(journal.parent).free>=2**30,'Whole private storage margin unavailable')
    create(stage/'storage-provision-intent.json',dict(image=str(image),output=str(out),journal=str(journal),unix=time.time()))
    image.parent.mkdir(mode=0o700,exist_ok=True);out.mkdir(mode=0o700)
    fd=os.open(image,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
    try:os.posix_fallocate(fd,0,32*2**30);os.fsync(fd)
    finally:os.close(fd)
    subprocess.run(['/usr/sbin/mkfs.ext4','-q','-F','-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0','-m','0',str(image)],
                   capture_output=True,check=True,timeout=120)
    fd=os.open(image,os.O_RDWR)
    try:os.posix_fallocate(fd,0,32*2**30);os.fsync(fd)
    finally:os.close(fd)
    for command in [['/usr/bin/mount','-o','loop,nodev,nosuid,noexec',str(image),str(out)],
                    ['/usr/bin/chown',str(os.getuid())+':'+str(os.getgid()),str(out)],['/usr/bin/rmdir',str(out/'lost+found')]]:
        result=subprocess.run(['sudo','-S','-p','']+command,input=password+'\n',capture_output=True,text=True,timeout=60)
        require(result.returncode==0,'Private storage command failed: '+command[0])
    FixedJournal(journal).create()
    config=dict(version='HISTORY104_PRIVATE_STORAGE_R2',run_id=RUN,output_mount=str(out),output_device=out.stat().st_dev,
        image_path=str(image),image_inode=image.stat().st_ino,image_bytes=32*2**30,journal_path=str(journal),journal_bytes=48*2**20,
        minimum_output_free_bytes=4*2**30,minimum_free_inodes=1024,minimum_host_free_bytes=128*2**20,
        shared_disk_reserve_ratio_modified=False,reboot_remount_must_be_reverified=True)
    check=StorageGuard(config).check();create(stage/'history104-storage.json',config)
    return dict(status='B36_PRIVATE_STORAGE_PROVISIONED_NO_GPU',check=check,storage_contract=config,GPU_submissions=0)


def admit(project,stage):
    _,registration,authority,bound=admitted_inputs(project,stage)
    stage=Path(stage);project=Path(project)
    require(not (stage/'GPU-intent.json').exists() and not (stage/'GPU-launch.json').exists(),'Recover original B handle')
    storage=storage_for(stage).check()
    specification=read(stage/ASSETS)
    assets=assets_check(project,specification)
    nltk=english_resources(project)
    profile=read(stage/PROFILE);image=profile['GPU_container']['image']
    require(json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]['Id']==image,'Fixed Docker image missing')
    gpu,memory=fresh_idle(project,authority,profile)
    result=dict(status='B36_FRESH_ADMISSION_NO_GPU',stage=str(stage),authorization=authority,
        authorization_sha256=sha(stage/'pg-GPU-authorization.json'),registration_sha256=sha(stage/'registration.json'),
        gpu=gpu,MemAvailable_bytes=memory,storage=storage,nltk=nltk,asset_spec_sha256=sha(stage/ASSETS),assets=assets,
        observed_unix=time.time(),source_revision=registration['source_revision'],A_handoff_package_sha256=bound['package_sha256'],
        GPU_submissions=0)
    atomic_json(stage/'fresh-admission.json',result)
    return result


def bind(project,stage,envelope):
    _,_,authority,bound=admitted_inputs(project,stage)
    stage=Path(stage)
    require(envelope['job']['launch_id']==authority['launch_id'],'Original envelope required')
    binding=dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
        central_reservation_sha256=hashlib.sha256((json.dumps(envelope,indent=2)+'\n').encode()).hexdigest(),
        A_handoff_package_sha256=bound['package_sha256'])
    for name,value in [('central-reservation.json',envelope),('launch-binding.json',binding)]:
        if (stage/name).exists():require(read(stage/name)==value,'Existing B binding differs; recover original')
        else:create(stage/name,value)
    validate(project,stage)
    return dict(status='B36_ORIGINAL_CENTRAL_ENVELOPE_BOUND_NO_GPU',launch_id=authority['launch_id'])


def publish_launch(project,stage):
    _,registration,authority,bound=validate(project,stage)
    profile=read(Path(stage)/PROFILE)
    value={key:authority[key] for key in ('run_id','phase','physical_paths','whole_GPUh','host','gpu_uuid',
        'launch_id','source_revision','scope_sha256','registration_sha256','A_launch_id','frozen_file_sha256')}
    value.update(status='B36_ONCE_ONLY_HOST_GUARDIAN_DISPATCHED',stage=str(stage),project=str(project),
        container=Path(stage).name+'-gpu',authorization_sha256=sha(Path(stage)/'pg-GPU-authorization.json'),
        model_sha256=bound['A_model_sha256'],forecast_GPUh=profile['hosts']['two_card']['stage_B_forecast_GPUh'],
        guardian_identity=process_identity(os.getpid()),dispatched_unix=time.time())
    create(Path(stage)/'GPU-launch.json',value)
    return value


def launch(project,stage,password,central_state):
    stage=Path(stage);project=Path(project)
    with (stage/'dispatch-control.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (stage/'GPU-launch.json').exists():return read(stage/'GPU-launch.json')
        if (stage/'GPU-intent.json').exists():
            return dict(status='B36_ORIGINAL_DISPATCH_PENDING_OR_UNKNOWN_RECOVER_ONLY',intent=read(stage/'GPU-intent.json'),
                        GPU_submissions=0,authorizes_retry=False)
        _,registration,authority,_=validate(project,stage)
        require(central_state['central_ledger_host']=='four_card' and central_state['budget_overrun_recorded'] is False
            and 0<=time.time()-central_state['observed_unix']<=60,'Fresh authoritative central state required')
        job=central_state['job']
        require(job['status']=='RESERVED_OR_RUNNING' and job['job_id']==RUN
            and all(job[key]==authority[key] for key in ('run_id','phase','physical_paths','host','gpu_uuid','launch_id',
                'source_revision','scope_sha256','registration_sha256','A_launch_id','frozen_file_sha256'))
            and job['authorization_sha256']==sha(stage/'pg-GPU-authorization.json')
            and job['billed_limit_GPUh']==authority['whole_GPUh'],'Current central reservation differs')
        storage_for(stage).check()
        admission=read(stage/'fresh-admission.json')
        require(admission['registration_sha256']==sha(stage/'registration.json')
            and admission['authorization_sha256']==sha(stage/'pg-GPU-authorization.json')
            and admission['asset_spec_sha256']==sha(stage/ASSETS),'Original admitted source/assets differ')
        assets_unchanged(project,read(stage/ASSETS),admission['assets'])
        english_resources(project)
        fresh_idle(project,authority,read(stage/PROFILE))
        create(stage/'GPU-intent.json',dict(launch_id=authority['launch_id'],source_revision=registration['source_revision'],
            gpu_uuid=authority['gpu_uuid'],dispatcher_identity=process_identity(os.getpid()),unix=time.time(),no_replay=True))
        command=[sys.executable,str(stage/'scripts/cara_fast_b36_host_guardian_r1.py'),
                 '--project',str(project),'--stage',str(stage)]
        with (stage/'host-guardian.log').open('x') as log:
            child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
            dispatched=dict(status='B36_ORIGINAL_GUARDIAN_SPAWNED_AWAIT_ITS_LAUNCH_RECEIPT',
                guardian_identity=process_identity(child.pid),launch_id=authority['launch_id'],command=command)
            create(stage/'GPU-dispatch.json',dispatched)
            child.stdin.write(json.dumps(dict(sudo_password=password)).encode());child.stdin.close()
        return dispatched


def status(project,stage):
    project,stage=Path(project),Path(stage)
    result=dict(status='B36_OPERATIONAL_ONLY',GPU_relaunch=False,stage=str(stage),observed_unix=time.time())
    if (stage/'GPU-launch.json').exists():
        launched=read(stage/'GPU-launch.json');result['launch']=launched
        result['guardian_live']=same_live_process(launched['guardian_identity'])
    if (stage/'pg-host-guardian.json').exists():
        guardian=read(stage/'pg-host-guardian.json')
        result['guardian']={key:guardian.get(key) for key in ('status','identity','container_cli_identity','started_unix',
            'ended_unix','container_dispatch_state','error_type','container_terminal_witness','mode_restoration')}
    path=project/'outputs'/RUN/'B-supervisor.json'
    if path.exists():
        supervisor=read(path)
        result['supervisor']={key:supervisor.get(key) for key in ('status','supervisor_identity','child_identity',
            'started_unix','error_type','observations')}
    path=project/'outputs'/RUN/'B-collection.json'
    if path.exists():
        rows=read(path)['rows']
        result['progress']=dict(denominator=36,complete=sum(row['status']=='COMPLETE' for row in rows),
            failed=sum(row['status']=='TECH_FAILED' for row in rows),not_reached=sum(row['status']=='NOT_REACHED' for row in rows))
    path=project/'outputs'/RUN/'B-check-schedule.json'
    if path.exists():result['check_schedule']=read(path)
    return result
