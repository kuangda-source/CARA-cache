"""Authorized COMMON_LONG6 single dispatch, recovery and technical-only capture."""
import argparse,base64,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
import cara_two_card_transport_r1 as transport
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.common_long_card_r1 import RUN,COUNTS,CONFIG,CPU_PROOF,MANIFEST,read,sha,matrix
from wcomr.common_long_finance_r1 import ENVELOPE
from audit_common_long_combination_cpu_r1 import accept as cpu_accept
USER='资源准备完成的情况下，授权 gpu，在 2 卡服务器上推进，安排半程检查和定时验收'
def remote(host,code,data=None):
 return transport.ssh(code,data,docker_group=True,timeout=180) if host=='two_card' else transport.four_ssh(code,data,timeout=180)
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def published():
 rev=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],text=True).split()[0]==rev
 for n in ['scripts/wc_two_card_common_long6_gpu_r1.py',*cpu_accept(read(ROOT/'reports/cara_common_long_combination_two_card_CPU_completed_r5_20261027.json'))['source_sha256']]:
  assert subprocess.check_output(['git','show',rev+':'+n])==(ROOT/n).read_bytes(),n
 return rev
PREPARE=r'''
import pathlib,json,sys,shutil,hashlib,base64,os,subprocess,time
p=json.load(sys.stdin);password=p.pop('sudo_password');root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
base=root/'.sync/cara-shared66-full-ada-r2-20261025';cpu=pathlib.Path(p['CPU_launch']['stage']);stage=root/'.sync'/p['stage_name']
read=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert not stage.exists(),'Recover existing COMMON_LONG6 stage; never overwrite'
assert sha(base/'registration.json')=='48193714a15f219b33fd62a6f929ee8e7a5c17b1b6c3dfd9c7615318318c7561'
assert sha(cpu/'registration.json')==p['CPU_launch']['registration_sha256'] and sha(cpu/'CPU-proof.json')==p['CPU_proof_sha256']
br=read(base/'registration.json');cr=read(cpu/'registration.json');assert cr['host']==p['host']
assert all(sha(root/'runtime'/n)==h for n,h in cr['runtime_source_sha256'].items())
# Copy only registered assets; never inherit old authorization, intent or ledger.
stage.mkdir(mode=0o700);names=set()
for source,reg in ((base,br),(cpu,cr)):
 for n,h in reg['payload_sha256'].items():
  assert sha(source/n)==h
  if n in ('registration.json','pg-GPU-authorization.json','central-envelope.json'):continue
  target=stage/n;assert target.is_relative_to(stage) and '..' not in pathlib.Path(n).parts
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/n,target);names.add(n)
for n,b64 in p['files'].items():
 data=base64.b64decode(b64);assert hashlib.sha256(data).hexdigest()==p['hashes'][n]
 (stage/n).parent.mkdir(parents=True,exist_ok=True);(stage/n).write_bytes(data);names.add(n)
shutil.copyfile(cpu/'CPU-proof.json',stage/'CPU-proof.json');names.add('CPU-proof.json')
(stage/'cache').mkdir(exist_ok=True);(stage/'cache/runtime').symlink_to(root/'runtime',target_is_directory=True)
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.common_long_card_r1 import RUN,validate
from wcomr.history104_storage_r2 import FixedJournal,StorageGuard
base_storage=root/'.sync/storage-reservations/common-long6-r1';image=base_storage/'output.ext4';out=root/'outputs'/RUN
journal=pathlib.Path(p['journal'])
assert not base_storage.exists() and not out.exists() and not journal.parent.exists(),'Existing storage recover only'
assert shutil.disk_usage(root).free>100*2**30 and shutil.disk_usage(journal.parent.parent).free>2**30
base_storage.mkdir(mode=0o700);out.mkdir(mode=0o700);journal.parent.mkdir(mode=0o700)
fd=os.open(image,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
try:os.posix_fallocate(fd,0,32*2**30);os.fsync(fd)
finally:os.close(fd)
subprocess.run(['/usr/sbin/mkfs.ext4','-q','-F','-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0','-m','0',str(image)],check=True,capture_output=True,timeout=60)
fd=os.open(image,os.O_RDWR)
try:os.posix_fallocate(fd,0,32*2**30);os.fsync(fd)
finally:os.close(fd)
def sudo(args):
 r=subprocess.run(['sudo','-S','-p','']+args,input=password+'\n',text=True,capture_output=True,timeout=45)
 if r.returncode:raise RuntimeError('Private COMMON_LONG6 storage operation failed: '+args[0])
sudo(['/usr/bin/mount','-o','loop,nodev,nosuid,noexec',str(image),str(out)])
sudo(['/usr/bin/chown',str(os.getuid())+':'+str(os.getgid()),str(out)])
sudo(['/usr/bin/rmdir',str(out/'lost+found')]);password=None
FixedJournal(journal).create()
storage=dict(version='HISTORY104_PRIVATE_STORAGE_R2',run_id=RUN,output_mount=str(out),output_device=out.stat().st_dev,image_path=str(image),image_inode=image.stat().st_ino,image_bytes=32*2**30,journal_path=str(journal),journal_bytes=48*2**20,minimum_output_free_bytes=4*2**30,minimum_free_inodes=1024,minimum_host_free_bytes=128*2**20,shared_disk_reserve_ratio_modified=False,reboot_remount_must_be_reverified=True)
(stage/'history104-storage.json').write_text(json.dumps(storage,indent=2)+'\n');names.add('history104-storage.json')
reg=dict(namespace='CARA_COMMON_LONG6_R1',stage=str(stage),host=p['host'],source_revision=p['controller_revision'],payload_sha256={n:sha(stage/n) for n in sorted(names)},runtime_source_sha256=cr['runtime_source_sha256'],parent_CPU_registration_sha256=p['CPU_launch']['registration_sha256'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
validate(root,stage);snapshot=StorageGuard(storage).check()
# Validate reconstruction and frozen inputs before any GPU reservation.
from four_card_policy_assets_port_r1 import reconstruct
reconstruct(stage)
v=dict(status='COMMON_LONG6_STAGE_PREPARED_NO_GPU',host=p['host'],project=str(root),stage=str(stage),run_id=RUN,source_revision=reg['source_revision'],controller_revision=p['controller_revision'],registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/'common-config.json'),production_CPU_sha256=sha(stage/'common-combination-CPU.json'),storage=snapshot,observed_unix=time.time(),GPU_submissions=0)
(stage/'pg-stage-reference.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''

LAUNCH=r'''
import pathlib,json,sys,time,os,fcntl,subprocess
p=json.load(sys.stdin);L=p['stage_ref'];root=pathlib.Path(L['project']);stage=pathlib.Path(L['stage']);sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.common_long_card_r1 import validate,read,sha,RUN,COUNTS
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity,DeviceLease
from wcomr.policy_generator_r1.production_exclusive import observe
from wcomr.history104_storage_r2 import storage_for
lock=(stage/'pg-dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (stage/'pg-GPU-intent.json').exists() and not (stage/'pg-GPU-launch.json').exists(),'Recover original'
c,reg,*_=validate(root,stage);auth=p['auth'];assert read(stage/'pg-GPU-authorization.json')==auth
assert sha(stage/'registration.json')==L['registration_sha256'];assert 0<=time.time()-p['envelope']['observed_unix']<180
storage=storage_for(stage);storage.check();assert not any(storage.output.iterdir())
with DeviceLease(root,auth['gpu_uuid']):
 snap=observe(auth['gpu_uuid']);assert not snap['compute_apps'] and not snap['mps_processes'] and snap['compute_mode'] in ('Default','Exclusive_Process')
 mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 assert mem>=40*2**30
 assert set(map(int,c['cpuset_cpus'].split(',')))<=os.sched_getaffinity(0)
 intent=dict(status='COMMON_LONG6_ONCE_ONLY_INTENT',launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],source_revision=reg['source_revision'],created_unix=time.time())
 with (stage/'pg-GPU-intent.json').open('x') as f:json.dump(intent,f);f.flush();os.fsync(f.fileno())
command=[sys.executable,'-u',str(stage/'scripts/wc_common_long6_host_guardian_r1.py'),'--project',str(root),'--stage',str(stage)]
with (stage/'pg-host-guardian.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 child.stdin.write(json.dumps(dict(sudo_password=p.pop('sudo_password'))).encode());child.stdin.close()
result=dict(status='COMMON_LONG6_SINGLE_DISPATCHED_ADMISSION_PENDING',**{k:auth[k] for k in ('host','run_id','launch_id','stage','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh')},project=str(root),guardian_identity=process_identity(child.pid),container=stage.name+'-gpu',started_unix=time.time(),forecast_GPUh=c['forecast_complete_GPUh'],registration_sha256=L['registration_sha256'],authorization_sha256=sha(stage/'pg-GPU-authorization.json'))
atomic_json(stage/'pg-GPU-launch.json',result);print(json.dumps(result))
'''

PROBE=r'''
import pathlib,json,sys,time,subprocess,os
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');sys.path.insert(0,p['source_stage']+'/src')
from wcomr.common_long_finance_r1 import HostBudgetPool
from wcomr.policy_generator_r1.production_exclusive import observe
intents={str(f):json.loads(f.read_text()) for s in (root/'.sync').glob('cara-common-long6-*-r1-20261027') for n in ('pg-GPU-intent.json','pg-GPU-launch.json','pg-GPU-authorization.json') for f in [s/n] if f.exists()}
print(json.dumps(dict(host=p['host'],observed_unix=time.time(),pool=HostBudgetPool(root).read(),intents=intents,GPU=observe(p['gpu_uuid']) if p.get('gpu_uuid') else None,MemAvailable_bytes=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024)))
'''
CENTRAL=r'''
import pathlib,json,sys,time,copy
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');sys.path.insert(0,p['source_stage']+'/src')
from wcomr.common_long_card_r1 import RUN
from wcomr.common_long_finance_r1 import HostBudgetPool,ENVELOPE,financial_hold
from wcomr.gpu_budget_pool_v2 import atomic_json
pool=HostBudgetPool(root);auth=p['auth']
assert all(0<=time.time()-v['observed_unix']<180 and not v['intents'] for v in p['probes'].values())
with pool.transaction() as v:
 assert v['cap_gpu_hours']==226 and ENVELOPE not in v['jobs'] and RUN not in v['jobs']
 assert all(j['status']!='RESERVED_OR_RUNNING' or financial_hold(j) for j in v['jobs'].values()),'Another owned original is active: wait, no double expensive job'
 assert pool.accounting(v)['available_gpu_hours']>=3
 before=copy.deepcopy(v)
 job={k:auth[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','stage','scope_counts','billed_limit_GPUh','host')}
 job.update(job_id=ENVELOPE,kind='COMMON_LONG6_EXTERNAL_ENVELOPE',status='RESERVED_OR_RUNNING',confirmed_GPU_submission=False,actual_GPU_submission_known=False,created_unix=time.time())
 v['jobs'][ENVELOPE]=job;pool.commit(v,dict(type='COMMON_LONG6_AUTHORIZED_SINGLE_ENVELOPE',job_id=ENVELOPE))
 receipt=dict(status='COMMON_LONG6_CENTRAL_RESERVED',job=job,prior_pool=before,central_after=v,same_money_not_two_charges=True,observed_unix=time.time())
 atomic_json(root/'reports/common-long6-central-envelope-original.json',receipt);print(json.dumps(receipt))
'''
TECH=r'''
import pathlib,json,sys,time,subprocess
p=json.load(sys.stdin);s=pathlib.Path(p['stage']);root=s.parent.parent;sys.path[:0]=[str(s/'src'),str(s/'scripts')]
from wcomr.common_long_card_r1 import read,RUN,sha
from wcomr.gpu_budget_pool_v2 import process_identity,same_live_process
from wcomr.policy_generator_r1.production_exclusive import observe
from wcomr.history104_storage_r2 import storage_for
files={n:read(s/n) for n in ('pg-stage-reference.json','pg-GPU-intent.json','pg-GPU-launch.json','pg-host-guardian.json','pg-admission-failure.json') if (s/n).exists()}
L=files.get('pg-GPU-launch.json');out=root/'outputs'/RUN
if not L:print(json.dumps(dict(status='RECOVERED_NO_LAUNCH',files=files,observed_unix=time.time())));raise SystemExit
sup=read(out/'supervisor.json') if (out/'supervisor.json').exists() else {}
health=read(out/'runner-health.json') if (out/'runner-health.json').exists() else {}
mon=out/'exclusive-monitor.jsonl';rows=[json.loads(l) for l in mon.read_text().splitlines()] if mon.exists() else []
from wcomr.policy_generator_r1.production_exclusive import exclusive_gate
bad=0
for r in rows:
 try:
  active=bool(r['snapshot']['compute_apps']);gate=exclusive_gate(r['snapshot'],gpu_uuid=L['gpu_uuid'],phase='active' if active else 'idle',runner=sup.get('child_identity') if active else None,now=r['snapshot']['observed_unix']);bad+=int(not gate['observation_passed'])
 except (ValueError,AssertionError):bad+=1
ins=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=15)
con=json.loads(ins.stdout)[0]['State'] if ins.returncode==0 else {'missing':True}
identity={k:dict(identity=sup.get(k),live=same_live_process(sup[k]) if sup.get(k) else False) for k in ('supervisor_identity','child_identity','post_identity')}
raw={n:(out/n).read_text(errors='replace')[-1600:] for n in ('GPU.log','post-CPU.log') if (out/n).exists()}
# No score payloads: logs restricted to failure suffix only.
logs={k:v for k,v in raw.items() if 'Traceback' in v or 'Error' in v}
v=dict(status='COMMON_LONG6_TECHNICAL_ONLY',observed_unix=time.time(),launch=L,guardian=files.get('pg-host-guardian.json'),container_state=con,original_identities=identity,health=health,GPU=observe(L['gpu_uuid']),storage=storage_for(s).check(),monitor_samples=len(rows),monitor_violations=bad,max_monitor_gap=max([b['monotonic_elapsed']-a['monotonic_elapsed'] for a,b in zip(rows,rows[1:])] or [0]),context_granted=read(s/'pg-runner-context-granted.json') if (s/'pg-runner-context-granted.json').exists() else None,billing=read(out/'billing.json') if (out/'billing.json').exists() else None,post_exit=read(out/'post-exit.json') if (out/'post-exit.json').exists() else None,error_logs=logs)
print(json.dumps(v))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','probe','launch','recover','capture','settle-central','accept'])
 p.add_argument('--stage-ref',type=Path);p.add_argument('--launch-ref',type=Path);p.add_argument('--capture',type=Path);p.add_argument('--central-settlement',type=Path)
 p.add_argument('--mode',choices=['admission','halfway','terminal'],default='admission');p.add_argument('--gpu-uuid');p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();assert not a.output.exists()
 caps={h:read(ROOT/f'reports/cara_common_long_combination_{h}_CPU_completed_r5_20261027.json') for h in ('four_card','two_card')}
 if a.command=='prepare':
  rev=published();cap=caps['two_card'];accepted=cpu_accept(cap);q=read(ROOT/'reports/cara_common_long6_quote_verified_20261027.json');q['scope_counts']=COUNTS
  m=read(ROOT/MANIFEST)
  c=dict(run_id=RUN,host='two_card',compute_capability=[8,6],scope_counts=COUNTS,matrix=matrix(m),billed_limit_GPUh=3,forecast_complete_GPUh=q['forecast_GPUh'],storage_contract_required=True,cpuset_cpus='2,3',logical_copy_cap_bytes=32*2**30,asset_byte_limit=24*2**30,post_CPU_limit_seconds=3600,post_CPU_memory_bytes=8*2**30,model_identity='Cosmos-Predict2.5-2B-post-trained')
  files={CONFIG:c,'pg-whole-quote.json':q,CPU_PROOF:accepted,'pg-independent-CPU-acceptance.json':dict(accepted,production_CPU_accepted=True)}
  raw={k:(json.dumps(v,indent=2)+'\n').encode() for k,v in files.items()}
  data=dict(controller_revision=rev,host='two_card',CPU_launch=cap['launch'],CPU_proof_sha256=cap['CPU_proof_sha256'],stage_name='cara-common-long6-a6000-r1-20261027',files={k:base64.b64encode(v).decode() for k,v in raw.items()},hashes={k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},journal='/home/gaokuangda/cara_control/common-long6-r1/control.journal',sudo_password=transport.password())
  v=remote('two_card',PREPARE,data)
 elif a.command=='probe':
  v={h:remote(h,PROBE,dict(host=h,source_stage=cap['launch']['stage'],gpu_uuid=a.gpu_uuid if h=='two_card' else None)) for h,cap in caps.items()}
 elif a.command=='launch':
  rev=published();L=read(a.stage_ref)
  for cap in caps.values():cpu_accept(cap)
  probes={h:remote(h,PROBE,dict(host=h,source_stage=cap['launch']['stage'],gpu_uuid=a.gpu_uuid if h=='two_card' else None)) for h,cap in caps.items()}
  assert all(not x['intents'] for x in probes.values()),'Recover original, never repeat dispatch'
  assert not probes['two_card']['GPU']['compute_apps'] and probes['two_card']['MemAvailable_bytes']>=40*2**30
  auth=dict(controller_revision=rev,kind='DIRECT_USER_COMMON_LONG6',host='two_card',run_id=RUN,launch_id=str(uuid.uuid4()),stage=L['stage'],source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],config_sha256=L['config_sha256'],production_CPU_sha256=L['production_CPU_sha256'],gpu_uuid=a.gpu_uuid,scope_counts=COUNTS,billed_limit_GPUh=3,cumulative_cap_GPUh=226,direct_user_authorization=True,user_reply_quote=USER)
  write(a.output.with_suffix('.authorization.json'),auth)
  envelope=remote('four_card',CENTRAL,dict(source_stage=caps['four_card']['launch']['stage'],auth=auth,probes=probes));write(a.output.with_suffix('.central-envelope.json'),envelope)
  remote('two_card',"import pathlib,json,sys;p=json.load(sys.stdin);s=pathlib.Path(p['auth']['stage']);\nfor n,v in [('pg-GPU-authorization.json',p['auth']),('central-envelope.json',p['envelope'])]:\n with (s/n).open('x') as f:json.dump(v,f,indent=2);f.write('\\n')\nprint(json.dumps({'bound':True}))",dict(auth=auth,envelope=envelope))
  v=remote('two_card',LAUNCH,dict(stage_ref=L,auth=auth,envelope=envelope,sudo_password=transport.password()))
  v.update(halfway_check_not_before_unix=v['started_unix']+v['forecast_GPUh']*1800,next_check_not_before_unix=v['started_unix']+(v['forecast_GPUh']+1)*3600)
 elif a.command in ('capture','recover'):
  L=read(a.launch_ref or a.stage_ref);v=remote('two_card',TECH,dict(stage=L['stage']))
  if a.command=='capture' and a.mode=='terminal' and v.get('container_state',{}).get('Status')=='exited':
   code="import pathlib,json,sys;p=json.load(sys.stdin);s=pathlib.Path(p['stage']);sys.path[:0]=[str(s/'src'),str(s/'scripts')];from capture_common_long6_terminal_r1 import capture;print(json.dumps(capture(s.parent.parent,s,p['launch'])))"
   v=remote('two_card',code,dict(stage=L['stage'],launch=L))
 elif a.command=='settle-central':
  v=remote('four_card',"import pathlib,json,sys;p=json.load(sys.stdin);sys.path.insert(0,p['source_stage']+'/src');from wcomr.common_long_finance_r1 import HostBudgetPool,settle_original;print(json.dumps(settle_original(HostBudgetPool(pathlib.Path('/data20t/gaokuangda/worldcache_workspace')),p['capture'])))",dict(source_stage=caps['four_card']['launch']['stage'],capture=read(a.capture)))
 else:
  from wcomr.common_long_terminal_r1 import accept
  original=read(a.capture);original['central_settlement']=read(a.central_settlement);v=accept(original)
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','launch_id','health','monitor_samples','monitor_violations','context_granted')}))
if __name__=='__main__':main()
