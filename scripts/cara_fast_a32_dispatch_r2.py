"""One authorized A32 on A6000; explicit steps recover their original receipts."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from cara_two_card_transport_r1 import ssh, four_ssh, password

ROOT = Path(__file__).resolve().parents[1]
STAGE = '/data20t/gaokuangda/worldcache_workspace/.sync/cara-fast-cal-a32-a6000-r2-20261028'
GPU = 'GPU-cebf7119-cf03-23b9-e192-cd196332b704'
ACCEPT = 'reports/cara_fast_resource_CPU_acceptance_r4_20261028.json'
POST = 'reports/cara_fast_post_CPU_acceptance_r2_20261028.json'
REMOTE = r'''
import base64,fcntl,hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid
p=json.load(sys.stdin);action=p['action'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');stage=pathlib.Path(p['stage'])
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
read=lambda path:json.loads(pathlib.Path(path).read_text())
def create(path,value):
 path=pathlib.Path(path)
 with path.open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n');handle.flush();os.fsync(handle.fileno())
 fd=os.open(str(path.parent),os.O_RDONLY);os.fsync(fd);os.close(fd)
if action=='prepare':
 assert not stage.exists(),'Existing A32 stage: recover; never replace'
 base=pathlib.Path(p['base_stage']);assert sha(base/'registration.json')==p['base_registration_sha256']
 assert all(sha(root/'runtime'/n)==h for n,h in p['runtime_source_sha256'].items())
 stage.mkdir(mode=0o700)
 for name,expected in p['hashes'].items():
  relative=pathlib.Path(name);assert not relative.is_absolute() and '..' not in relative.parts
  dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True)
  original=base/name
  if name not in p['files']:
   assert sha(original)==expected;shutil.copyfile(original,dest)
  else:
   body=base64.b64decode(p['files'][name]);assert hashlib.sha256(body).hexdigest()==expected;dest.write_bytes(body)
 reg=dict(host='two_card',stage=str(stage),source_revision=p['source_revision'],payload_sha256=p['hashes'],runtime_source_sha256=p['runtime_source_sha256'])
 create(stage/'registration.json',reg);create(stage/'execution-CPU-proof.json',p['CPU_proof'])
 from_context=p['authority'];from_context.update(registration_sha256=sha(stage/'registration.json'),CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'))
 create(stage/'pg-GPU-authorization.json',from_context)
 print(json.dumps(dict(status='A32_IMMUTABLE_STAGE_PREPARED_NO_GPU',stage=str(stage),registration_sha256=sha(stage/'registration.json'),authorization=from_context,payload_count=len(reg['payload_sha256']))));sys.exit()
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_fast_execution_r2 import RUN,PROFILE,Pool,validate
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity,DeviceLease
from wcomr.history104_storage_r2 import FixedJournal,StorageGuard,storage_for
reg=read(stage/'registration.json');auth=read(stage/'pg-GPU-authorization.json');profile=read(stage/PROFILE);host=profile['hosts']['two_card']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
def gpu():
 values=subprocess.check_output(['/usr/bin/nvidia-smi','-i',auth['gpu_uuid'],'--query-gpu=uuid,name,compute_cap,utilization.gpu,memory.used,compute_mode,temperature.gpu','--format=csv,noheader,nounits'],text=True,timeout=20).strip().split(', ')
 apps=subprocess.check_output(['/usr/bin/nvidia-smi','-i',auth['gpu_uuid'],'--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=20)
 return dict(uuid=values[0],name=values[1],compute_cap=values[2],utilization_percent=int(values[3]),memory_used_mib=int(values[4]),compute_mode=values[5],temperature_C=int(values[6]),pids=[int(s) for s in apps.splitlines() if s.strip()],unix=time.time())
def memory():
 return int(next(line.split()[1] for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
def idle():
 value=gpu();assert value['uuid']==auth['gpu_uuid'] and value['compute_cap']=='8.6' and 'RTX A6000' in value['name']
 assert value['utilization_percent']==0 and not value['pids'] and value['memory_used_mib']<=1024
 assert memory()>=host['minimum_host_MemAvailable_GiB']*2**30,'Host memory below registered margin'
 assert set(map(int,host['cpuset_cpus'].split(',')))<=os.sched_getaffinity(0)
 with DeviceLease(root,auth['gpu_uuid']):pass
 return value
if action=='provision':
 if (stage/'history104-storage.json').exists():
  print(json.dumps(dict(status='RECOVERED_ORIGINAL_A32_STORAGE',check=storage_for(stage).check())));sys.exit()
 image=pathlib.Path(host['image_path']);out=pathlib.Path(host['output_mount']);journal=pathlib.Path(host['journal_path'])
 assert not image.exists() and not out.exists() and not journal.exists(),'Existing original storage requires recovery'
 assert shutil.disk_usage(image.parent.parent).free>=host['minimum_SSD_free_before_provision_GiB']*2**30
 assert shutil.disk_usage(journal.parent).free>=2**30
 create(stage/'storage-provision-intent.json',dict(image=str(image),output=str(out),journal=str(journal),unix=time.time()))
 image.parent.mkdir(mode=0o700,exist_ok=True);out.mkdir(mode=0o700)
 fd=os.open(image,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
 try:os.posix_fallocate(fd,0,32*2**30);os.fsync(fd)
 finally:os.close(fd)
 subprocess.run(['/usr/sbin/mkfs.ext4','-q','-F','-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0','-m','0',str(image)],capture_output=True,check=True,timeout=120)
 fd=os.open(image,os.O_RDWR)
 try:os.posix_fallocate(fd,0,32*2**30);os.fsync(fd)
 finally:os.close(fd)
 secret=p.pop('sudo_password')
 def sudo(args):
  result=subprocess.run(['sudo','-S','-p','']+args,input=secret+'\n',capture_output=True,text=True,timeout=60)
  assert result.returncode==0,'Private storage operation failed: '+args[0]
 sudo(['/usr/bin/mount','-o','loop,nodev,nosuid,noexec',str(image),str(out)])
 sudo(['/usr/bin/chown',str(os.getuid())+':'+str(os.getgid()),str(out)])
 sudo(['/usr/bin/rmdir',str(out/'lost+found')]);secret=None
 FixedJournal(journal).create()
 config=dict(version='HISTORY104_PRIVATE_STORAGE_R2',run_id=RUN,output_mount=str(out),output_device=out.stat().st_dev,image_path=str(image),image_inode=image.stat().st_ino,image_bytes=32*2**30,journal_path=str(journal),journal_bytes=48*2**20,minimum_output_free_bytes=4*2**30,minimum_free_inodes=1024,minimum_host_free_bytes=128*2**20,shared_disk_reserve_ratio_modified=False,reboot_remount_must_be_reverified=True)
 check=StorageGuard(config).check();create(stage/'history104-storage.json',config)
 value=dict(status='A32_SSD_PRIVATE_STORAGE_PROVISIONED_NO_GPU',storage_contract=config,check=check,observed_unix=time.time(),GPU_submissions=0)
 create(stage/'storage-provision.json',value);print(json.dumps(value))
elif action=='admit':
 from four_card_bank24_execution_tools_r1 import verify_nltk_resources
 assert not (stage/'GPU-intent.json').exists() and not (stage/'GPU-launch.json').exists(),'Recover original handle'
 snapshot=idle();storage=storage_for(stage).check();nltk=verify_nltk_resources(root.resolve())
 image=profile['GPU_container']['image']
 actual=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
 assert actual['Id']==image
 value=dict(status='A32_FRESH_A6000_ADMISSION_NO_GPU',gpu=snapshot,MemAvailable_bytes=memory(),storage=storage,nltk=nltk,source_revision=reg['source_revision'],registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'pg-GPU-authorization.json'),authorization=auth,stage=str(stage),image=image,observed_unix=time.time())
 atomic_json(stage/'fresh-admission.json',value);print(json.dumps(value))
elif action=='bind':
 envelope=p['envelope'];assert envelope['job']['launch_id']==auth['launch_id']
 for name,value in [('central-reservation.json',envelope),('launch-binding.json',dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),central_reservation_sha256=hashlib.sha256((json.dumps(envelope,indent=2)+'\n').encode()).hexdigest()))]:
  if (stage/name).exists():assert read(stage/name)==value
  else:create(stage/name,value)
 validate(root,stage);print(json.dumps(dict(status='A32_CENTRAL_ENVELOPE_BOUND_NO_GPU',launch_id=auth['launch_id'])))
elif action=='launch':
 if (stage/'GPU-launch.json').exists():print(json.dumps(read(stage/'GPU-launch.json')));sys.exit()
 with (stage/'dispatch-control.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (stage/'GPU-intent.json').exists(),'Original dispatch uncertain: recover; never relaunch'
  validate(root,stage);storage_for(stage).check();snapshot=idle()
  create(stage/'GPU-intent.json',dict(launch_id=auth['launch_id'],source_revision=reg['source_revision'],gpu_uuid=auth['gpu_uuid'],unix=time.time(),no_replay=True))
  command=[sys.executable,str(stage/'scripts/cara_fast_host_guardian_r2.py'),'--project',str(root),'--stage',str(stage)]
  value={key:auth[key] for key in ('run_id','phase','physical_paths','whole_GPUh','host','gpu_uuid','launch_id','source_revision','scope_sha256','registration_sha256')}
  value.update(status='A32_ONCE_ONLY_HOST_GUARDIAN_DISPATCHED',stage=str(stage),project=str(root),container=stage.name+'-gpu',authorization_sha256=sha(stage/'pg-GPU-authorization.json'),forecast_GPUh=host['stage_A_forecast_GPUh'],model_sha256='565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47',dispatched_unix=time.time(),command=command)
  with (stage/'host-guardian.log').open('x') as log:
   child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
   value['guardian_identity']=process_identity(child.pid);atomic_json(stage/'GPU-launch.json',value)
   child.stdin.write(json.dumps(dict(sudo_password=p.pop('sudo_password'))).encode());child.stdin.close()
  print(json.dumps(value))
elif action=='status':
 value=dict(status='A32_OPERATIONAL_STATUS_ONLY',observed_unix=time.time(),stage=str(stage),GPU_relaunch=False)
 for name,key in [('GPU-launch.json','launch'),('pg-host-guardian.json','guardian')]:
  if (stage/name).exists():value[key]=read(stage/name)
 for name,key in [('A-supervisor.json','supervisor'),('A-check-schedule.json','check_schedule')]:
  path=root/'outputs'/RUN/name
  if path.exists():value[key]=read(path)
 collection=root/'outputs'/RUN/'A-collection.json'
 if collection.exists():
  c=read(collection);value['progress']=dict(status=c['status'],complete=sum(r['status']=='COMPLETE' for r in c['rows']),recorded=len(c['rows']),denominator=32)
 if 'launch' in value:
  from wcomr.gpu_budget_pool_v2 import same_live_process
  value['guardian_live']=same_live_process(value['launch']['guardian_identity'])
  result=subprocess.run(['docker','inspect',value['launch']['container']],capture_output=True,text=True)
  value['container_state']=json.loads(result.stdout)[0]['State'] if result.returncode==0 else None
  value['guardian_log_tail']=(stage/'host-guardian.log').read_text(errors='replace')[-2500:]
  if (stage/'pg-container.log').exists():value['container_log_tail']=(stage/'pg-container.log').read_text(errors='replace')[-3500:]
 print(json.dumps(value))
else:raise ValueError(action)
'''

CENTRAL = r'''
import hashlib,json,pathlib,sys,time
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');base=pathlib.Path(p['CPU_stage'])
for name,expected in p['sources'].items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==expected
sys.path.insert(0,str(base/'src'))
from wcomr.cara_fast_execution_r2 import Pool,RUN
from wcomr.gpu_budget_pool_v2 import atomic_json
pool=Pool(root);before=pool.read();job=p['job'];receipt=root/'reports'/(RUN+'.central-reservation.json')
other_intents=[str(path) for stage in (root/'.sync').glob('cara-fast-cal-a32-*') for path in stage.glob('GPU-intent.json')]
assert not other_intents,'Recover an original four-card A32 intent'
if RUN in before['jobs']:
 assert receipt.exists() and before['jobs'][RUN]['launch_id']==job['launch_id'],'Existing A32 envelope: recover original'
 result=json.loads(receipt.read_text());assert result['job']==before['jobs'][RUN]
else:
 assert not receipt.exists()
 after=pool.reserve(job,p['gpu'])
 result=dict(central_ledger_host='four_card',new_reservation=True,job=after['jobs'][RUN],central_before=before,central_after=after,observed_unix=time.time())
 atomic_json(receipt,result)
print(json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare','provision','admit','reserve','launch','status'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    payload = dict(action=args.action, stage=STAGE)
    if args.action == 'prepare':
        capture = json.loads((ROOT/'reports/cara_fast_resource_two_card_CPU_capture_r14_20261028.json').read_text())
        proof = json.loads((ROOT/ACCEPT).read_text())
        post = json.loads((ROOT/POST).read_text())
        proof['critical_source_sha256'].update(post['critical_source_sha256'])
        proof['post_metadata_acceptance_ref'] = POST
        names = set(capture['registration']['payload_sha256'])
        names.update(proof['critical_source_sha256'])
        names.update(['configs/f1_setup.json','configs/wc_ra_comparison_production_r2_20261010.json',
                      'manifests/wc_h0_eval_mode_contract_20261003.json',
                      'reports/cara_fast_four_card_host_profile_readonly_r2_20261028.json',
                      'scripts/cara_fast_a32_dispatch_r2.py'])
        revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        files = {}; hashes = {}
        for name in sorted(names):
            body = (ROOT/name).read_bytes()
            assert subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)==body, 'Unpublished source: '+name
            hashes[name] = hashlib.sha256(body).hexdigest()
            if capture['registration']['payload_sha256'].get(name) != hashes[name]:
                files[name] = base64.b64encode(body).decode()
        authority = dict(direct_user_authorization=True,user_quote='A32gpu 实验能跑就开始跑，其他的可以边跑边补',
            run_id='cara-fast-cal-a32-r2-20261028',phase='A',physical_paths=32,whole_GPUh=5,
            authorizes_phase_B=False,authorizes_replay=False,host='two_card',gpu_uuid=GPU,
            launch_id=__import__('uuid').uuid4().hex,source_revision=revision,
            scope_sha256='d0ad38bc0fd29615e82dae7f726938bac15aec2842e4484bb3577e0949694fb4')
        payload.update(files=files,hashes=hashes,CPU_proof=proof,authority=authority,
            base_stage=capture['launch']['stage'],base_registration_sha256=capture['registration_sha256'],
            runtime_source_sha256=capture['registration']['runtime_source_sha256'],source_revision=revision)
    if args.action in ('provision','launch'):
        payload['sudo_password'] = password()
    if args.action == 'reserve':
        admission = ssh(REMOTE, dict(action='admit',stage=STAGE),docker_group=True,timeout=90)
        auth = admission['authorization']
        job = {key:auth[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256','registration_sha256')}
        job.update(job_id=auth['run_id'],phase='A',stage=STAGE,billed_limit_GPUh=5,
            forecast_GPUh=4.953222232105553,authorization_sha256=admission['authorization_sha256'])
        sources = json.loads((ROOT/ACCEPT).read_text())['critical_source_sha256']
        sources = {n:h for n,h in sources.items() if n.startswith('src/')}
        ada = json.loads((ROOT/'reports/cara_fast_resource_four_card_CPU_capture_r14_20261028.json').read_text())
        envelope = four_ssh(CENTRAL,dict(CPU_stage=ada['launch']['stage'],sources=sources,job=job,gpu=admission['gpu']),timeout=60)
        with args.output.with_suffix('.central.json').open('x') as handle:
            json.dump(envelope,handle,indent=2);handle.write('\n')
        result = ssh(REMOTE,dict(action='bind',stage=STAGE,envelope=envelope),docker_group=True,timeout=90)
        result['central_envelope'] = envelope
    else:
        if args.action == 'launch':
            central = four_ssh("import pathlib,json;v=json.loads(pathlib.Path('/data20t/gaokuangda/worldcache_workspace/reports/gpu-budget-v2.json').read_text());print(json.dumps(v['jobs'].get('cara-fast-cal-a32-r2-20261028')))",timeout=40)
            assert central and central['status']=='RESERVED_OR_RUNNING' and central['host']=='two_card'
        result = ssh(REMOTE,payload,docker_group=True,timeout=300 if args.action=='provision' else 90)
    with args.output.open('x') as handle:
        json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({key:result.get(key) for key in ('status','stage','source_revision','launch_id','container','guardian_identity','progress','container_state')}))


if __name__ == '__main__':
    main()
