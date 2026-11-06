"""One cross-host B1 envelope, immutable stage and original-handle recovery."""
import argparse,base64,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
import cara_two_card_transport_r1 as transport
from wc_four_card_bank24_native_transport_r4 import bridge,RUNTIME_REF
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.innovation_gain_b1_card_r1 import RUN,ROUND,ENVELOPE,COUNTS,CONFIG,read,sha
PROJECT='/data20t/gaokuangda/worldcache_workspace'
USER='这是 Cara-Cache 的一个新探索方向，抓紧做验证，得到结果后再决定是否并入主线；做两卡服务器和四卡服务器都能用的兼容版本，当前两卡服务器应该是空闲的'

def remote(host,code,p=None):
 if host=='two_card':return transport.ssh(code,p,docker_group=True,timeout=180)
 return transport.four_ssh(bridge(code,read(ROOT/RUNTIME_REF)),p,timeout=180)
def write(path,value):
 with Path(path).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def published():
 rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 name='scripts/wc_cara_ig_b1_gpu_r1.py'
 assert subprocess.check_output(['git','show',rev+':'+name],cwd=ROOT)==(ROOT/name).read_bytes()
 assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==rev
 return rev

def secret(host):
 if host=='two_card':return transport.password()
 from wc_four_card_price_refresh_gpu_r1 import saved_secret
 return saved_secret()

def cpu_accept(cap):
 p=cap['proof'];reg=cap['launch'];assert p['status']=='IG_SOURCE_BOUND_CPU_PASS_NOT_REAL_MODEL_RESULT'
 assert cap['all_payload_hashes_equal'] and cap['runtime_hashes_equal'] and not cap['device_requests']
 assert cap['container_state']['Status']=='exited' and cap['container_state']['ExitCode']==0
 assert p['unit_tests']==9 and p['B1_batch_controls']['status']=='B1_BATCH_SOURCE_CPU_PASS_NOT_REAL_MODEL'
 assert p['actual_request_schema']['actual_frozen'] and not p['cuda_initialized'] and p['GPU_submissions']==0
 assert {r['flow'] for r in p['B1_batch_controls']['checks']}=={True,False}
 for n,h in p['source_sha256'].items():assert sha(ROOT/n)==h,'Current source differs: '+n
 return dict(host=reg['host'],production_CPU_accepted=True,proof_sha256=cap['proof_sha256'],source_revision=reg['source_revision'])

PREPARE=r'''
import pathlib,json,sys,shutil,hashlib,base64,os,subprocess,time
p=json.load(sys.stdin);password=p.pop('sudo_password');root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
base=root/'.sync/cara-shared66-full-ada-r2-20261025';cpu=pathlib.Path(p['CPU_launch']['stage']);stage=root/'.sync'/p['stage_name']
read=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert not stage.exists(),'Recover existing B1 stage; never overwrite'
assert sha(base/'registration.json')=='48193714a15f219b33fd62a6f929ee8e7a5c17b1b6c3dfd9c7615318318c7561'
assert sha(cpu/'registration.json')==p['CPU_launch']['registration_sha256'] and sha(cpu/'IG-CPU.json')==p['CPU_proof_sha256']
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
 (stage/n).write_bytes(data);names.add(n)
shutil.copyfile(cpu/'IG-CPU.json',stage/'IG-CPU.json');names.add('IG-CPU.json')
(stage/'cache').mkdir(exist_ok=True);(stage/'cache/runtime').symlink_to(root/'runtime',target_is_directory=True)
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.innovation_gain_b1_card_r1 import RUN,validate
from wcomr.history104_storage_r2 import FixedJournal,StorageGuard
base_storage=root/'.sync/storage-reservations/ig-b1-r1';image=base_storage/'output.ext4';out=root/'outputs'/RUN
journal=pathlib.Path(p['journal'])
assert not base_storage.exists() and not out.exists() and not journal.parent.exists(),'Existing storage recover only'
assert shutil.disk_usage(root).free>100*2**30 and shutil.disk_usage(journal.parent.parent).free>2**30
base_storage.mkdir(mode=0o700);out.mkdir(mode=0o700);journal.parent.mkdir(mode=0o700)
fd=os.open(image,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
try:os.posix_fallocate(fd,0,64*2**30);os.fsync(fd)
finally:os.close(fd)
subprocess.run(['/usr/sbin/mkfs.ext4','-q','-F','-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0','-m','0',str(image)],check=True,capture_output=True,timeout=60)
fd=os.open(image,os.O_RDWR)
try:os.posix_fallocate(fd,0,64*2**30);os.fsync(fd)
finally:os.close(fd)
def sudo(args):
 r=subprocess.run(['sudo','-S','-p','']+args,input=password+'\n',text=True,capture_output=True,timeout=45)
 if r.returncode:raise RuntimeError('Private B1 storage operation failed: '+args[0])
sudo(['/usr/bin/mount','-o','loop,nodev,nosuid,noexec',str(image),str(out)])
sudo(['/usr/bin/chown',str(os.getuid())+':'+str(os.getgid()),str(out)])
sudo(['/usr/bin/rmdir',str(out/'lost+found')]);password=None
FixedJournal(journal).create()
storage=dict(version='HISTORY104_PRIVATE_STORAGE_R2',run_id=RUN,output_mount=str(out),output_device=out.stat().st_dev,image_path=str(image),image_inode=image.stat().st_ino,image_bytes=64*2**30,journal_path=str(journal),journal_bytes=48*2**20,minimum_output_free_bytes=4*2**30,minimum_free_inodes=1024,minimum_host_free_bytes=128*2**20,shared_disk_reserve_ratio_modified=False,reboot_remount_must_be_reverified=True)
(stage/'history104-storage.json').write_text(json.dumps(storage,indent=2)+'\n');names.add('history104-storage.json')
reg=dict(namespace='CARA_IG_B1_EXECUTION_R1',stage=str(stage),host=p['host'],source_revision=cr['source_revision'],payload_sha256={n:sha(stage/n) for n in sorted(names)},runtime_source_sha256=cr['runtime_source_sha256'],parent_CPU_registration_sha256=p['CPU_launch']['registration_sha256'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
validate(root,stage);snapshot=StorageGuard(storage).check()
# Validate reconstruction and frozen inputs before any GPU reservation.
from four_card_policy_assets_port_r1 import reconstruct
reconstruct(stage)
v=dict(status='IG_B1_STAGE_PREPARED_NO_GPU',host=p['host'],project=str(root),stage=str(stage),run_id=RUN,source_revision=reg['source_revision'],controller_revision=p['controller_revision'],registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/'IG-config.json'),production_CPU_sha256=sha(stage/'IG-CPU.json'),storage=snapshot,observed_unix=time.time(),GPU_submissions=0)
(stage/'pg-stage-reference.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''

PROBE=r'''
import pathlib,json,sys,subprocess,time,os
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');s=pathlib.Path(p['source_stage']);sys.path[:0]=[str(s/'src')]
from wcomr.gpu_budget_pool_v2 import same_live_process
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool
from wcomr.policy_generator_r1.production_exclusive import observe
read=lambda f:json.loads(f.read_text())
old=root/'.sync/cara-dev128-full-a6000-r1-20261026';released=None
if (old/'pg-GPU-launch.json').exists():
 L=read(old/'pg-GPU-launch.json');out=root/'outputs'/L['run_id']
 b=read(out/'billing.json');e=read(out/'exclusive-monitor-final.json');sup=read(out/'supervisor.json')
 assert L['launch_id']=='61587bb0-0e0d-4379-973b-d5502158fcd2'
 assert e['accepted'] and sup['child_exit_code']==0 and not same_live_process(sup['child_identity'])
 assert all(b[k]==L[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts'))
 assert not e['final_snapshot']['compute_apps'] and not observe(L['gpu_uuid'])['compute_apps']
 released=dict(launch=L,bill=b,exclusive_accepted=True,child_dead=True,CPU_post_preserved=True)
intents={str(t):read(t) for st in (root/'.sync').glob('cara-ig-b1-*') for n in ('pg-GPU-authorization.json','pg-GPU-intent.json','pg-GPU-launch.json') for t in [st/n] if t.exists()}
print(json.dumps(dict(observed_unix=time.time(),host=p['host'],pool=HostBudgetPool(root).read(),released_DEV128=released,intents=intents,
 GPU=observe(p['gpu_uuid']) if p.get('gpu_uuid') else None,
 MemAvailable_bytes=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024,
 allowed_CPUs=sorted(os.sched_getaffinity(0)))))
'''

CENTRAL=r'''
import pathlib,json,sys,time,copy
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');sys.path.insert(0,p['source_stage']+'/src')
from wcomr.innovation_gain_b1_card_r1 import RUN,ENVELOPE,ROUND,COUNTS
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool,financial_hold
from wcomr.gpu_budget_pool_v2 import atomic_json
pool=HostBudgetPool(root);auth=p['auth'];target=root/'reports/ig-b1-central-envelope-original.json'
assert 0<=time.time()-p['two_probe']['observed_unix']<180 and 0<=time.time()-p['four_probe']['observed_unix']<180
assert not p['two_probe']['intents'] and not p['four_probe']['intents']
with pool.transaction() as v:
 assert v['cap_gpu_hours']==226 and ENVELOPE not in v['jobs'] and RUN not in v['jobs']
 assert pool.accounting(v)['available_gpu_hours']>=29,'Preserve full seven-hour exploration plus confirmation/transfer'
 for key,j in v['jobs'].items():
  if j['status']!='RESERVED_OR_RUNNING' or financial_hold(j):continue
  r=p['two_probe']['released_DEV128'];assert r and r['exclusive_accepted'] and r['child_dead']
  assert j['launch_id']==r['launch']['launch_id'] and j['gpu_uuid']==r['launch']['gpu_uuid'] and j['gpu_uuid']!=auth['gpu_uuid']
 before=copy.deepcopy(v)
 job={k:auth[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','stage','scope_counts','billed_limit_GPUh','host')}
 job.update(job_id=ENVELOPE,round_id=ROUND,kind='IG_B1_EXTERNAL_PHASE_ENVELOPE',status='RESERVED_OR_RUNNING',confirmed_GPU_submission=False,actual_GPU_submission_known=False,created_unix=time.time())
 v['jobs'][ENVELOPE]=job;pool.commit(v,dict(type='IG_B1_RESERVE_WITH_DEV128_FINANCIAL_LIABILITY_PRESERVED',job_id=ENVELOPE))
 receipt=dict(status='IG_B1_CENTRAL_ENVELOPE_RESERVED',job=job,prior_pool=before,central_after=v,same_money_not_two_charges=True,observed_unix=time.time())
 atomic_json(target,receipt);print(json.dumps(receipt))
'''

LAUNCH=r'''
import pathlib,json,sys,time,os,fcntl,subprocess
p=json.load(sys.stdin);L=p['stage_ref'];root=pathlib.Path(L['project']);stage=pathlib.Path(L['stage']);sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.innovation_gain_b1_card_r1 import validate,read,sha,RUN,COUNTS
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity,DeviceLease
from wcomr.policy_generator_r1.production_exclusive import observe
from wcomr.history104_storage_r2 import storage_for
lock=(stage/'pg-dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (stage/'pg-GPU-intent.json').exists() and not (stage/'pg-GPU-launch.json').exists(),'Recover original'
c,reg=validate(root,stage);auth=p['auth'];assert read(stage/'pg-GPU-authorization.json')==auth
assert sha(stage/'registration.json')==L['registration_sha256'];assert 0<=time.time()-p['envelope']['observed_unix']<180
storage=storage_for(stage);storage.check();assert not any(storage.output.iterdir())
with DeviceLease(root,auth['gpu_uuid']):
 snap=observe(auth['gpu_uuid']);assert not snap['compute_apps'] and not snap['mps_processes'] and snap['compute_mode'] in ('Default','Exclusive_Process')
 mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 assert mem>=40*2**30
 assert set(map(int,c['cpuset_cpus'].split(',')))<=os.sched_getaffinity(0)
 intent=dict(status='IG_B1_ONCE_ONLY_INTENT',launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],source_revision=reg['source_revision'],created_unix=time.time())
 with (stage/'pg-GPU-intent.json').open('x') as f:json.dump(intent,f);f.flush();os.fsync(f.fileno())
command=[sys.executable,'-u',str(stage/'scripts/wc_cara_ig_b1_host_guardian_r1.py'),'--project',str(root),'--stage',str(stage)]
with (stage/'pg-host-guardian.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 child.stdin.write(json.dumps(dict(sudo_password=p.pop('sudo_password'))).encode());child.stdin.close()
result=dict(status='IG_B1_SINGLE_DISPATCHED_ADMISSION_PENDING',**{k:auth[k] for k in ('host','run_id','launch_id','stage','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh')},project=str(root),guardian_identity=process_identity(child.pid),container=stage.name+'-gpu',started_unix=time.time(),forecast_GPUh=c['forecast_complete_GPUh'],registration_sha256=L['registration_sha256'])
atomic_json(stage/'pg-GPU-launch.json',result);print(json.dumps(result))
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','probe','launch'])
 p.add_argument('--host',choices=['two_card','four_card'],default='two_card')
 for n in ('cpu-capture','two-cpu-capture','four-cpu-capture','stage-ref'):p.add_argument('--'+n,type=Path)
 p.add_argument('--gpu-uuid');p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 if a.command=='prepare':
  controller_revision=published()
  cap=read(a.cpu_capture);accepted=cpu_accept(cap);assert accepted['host']==a.host
  # Planning allowance for all load/teacher/head/IO work, never a measured speed claim.
  terms=dict(parent_paths_seconds=4*246.851957,model_load_allowance_seconds=600,teacher_and_original_readout_allowance_seconds=900,new_head_replay_allowance_seconds=720,transfer_hash_save_allowance_seconds=1200)
  forecast=sum(terms.values())/3600;assert forecast<1.5
  q=dict(scope_counts=COUNTS,forecast_GPUh=forecast,terms=terms,basis='CAL66 historical parent time plus explicit unmeasured diagnostic allowances',hard_stop_GPUh=1.5,round_cap_GPUh=7,remaining_B2_B3_upper_GPUh=5.5)
  c=dict(run_id=RUN,host=a.host,compute_capability=[8,6] if a.host=='two_card' else [8,9],scope_counts=COUNTS,billed_limit_GPUh=1.5,round_cap_GPUh=7,cumulative_cap_GPUh=226,forecast_complete_GPUh=forecast,storage_contract_required=True,thermal_telemetry_required=True,cpuset_cpus='2,3',logical_copy_cap_bytes=32*2**30,asset_byte_limit=56*2**30,model_identity='Cosmos-Predict2.5-2B-post-trained',prompts=[r['name'] for r in read(ROOT/'configs/wc_scout_cal12_production_entry_r1_20261018.json')['requests'][:2]])
  files={CONFIG:c,'pg-whole-quote.json':q,'pg-independent-CPU-acceptance.json':accepted}
  raw={k:(json.dumps(v,indent=2)+'\n').encode() for k,v in files.items()}
  data=dict(controller_revision=controller_revision,host=a.host,CPU_launch=cap['launch'],CPU_proof_sha256=cap['proof_sha256'],stage_name='cara-ig-b1-'+('a6000' if a.host=='two_card' else 'ada')+'-r1-20261027',files={k:base64.b64encode(v).decode() for k,v in raw.items()},hashes={k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},journal=('/home/gaokuangda/cara_control' if a.host=='two_card' else '/data1/gaokuangda_cara_control')+'/ig-b1-r1/control.journal',sudo_password=secret(a.host))
  try:v=remote(a.host,PREPARE,data)
  finally:data.pop('sudo_password',None)
 elif a.command=='probe':
  cap=read(a.cpu_capture);v=remote(a.host,PROBE,dict(host=a.host,source_stage=cap['launch']['stage'],gpu_uuid=a.gpu_uuid))
 else:
  controller_revision=published()
  L=read(a.stage_ref);caps={h:read(getattr(a,h.replace('_card','')+'_cpu_capture')) for h in ('two_card','four_card')}
  for h,cap in caps.items():assert cpu_accept(cap)['host']==h
  probes={h:remote(h,PROBE,dict(host=h,source_stage=cap['launch']['stage'],gpu_uuid=a.gpu_uuid if h==a.host else None)) for h,cap in caps.items()}
  assert all(not x['intents'] for x in probes.values()),'Recover existing authorization/intent; never duplicate'
  selected=probes[a.host];assert not selected['GPU']['compute_apps'] and selected['MemAvailable_bytes']>=40*2**30
  auth=dict(controller_revision=controller_revision,kind='DIRECT_USER_ISOLATED_IG_VALIDATION',host=a.host,run_id=RUN,launch_id=str(uuid.uuid4()),stage=L['stage'],source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],config_sha256=L['config_sha256'],production_CPU_sha256=L['production_CPU_sha256'],gpu_uuid=a.gpu_uuid,scope_counts=COUNTS,billed_limit_GPUh=1.5,round_cap_GPUh=7,cumulative_cap_GPUh=226,direct_user_authorization=True,user_reply_quote=USER)
  # Local durable intent survives network ambiguity before any central mutation.
  write(a.output.with_suffix('.authorization.json'),auth)
  envelope=remote('four_card',CENTRAL,dict(source_stage=caps['four_card']['launch']['stage'],auth=auth,two_probe=probes['two_card'],four_probe=probes['four_card']))
  write(a.output.with_suffix('.central-envelope.json'),envelope)
  remote(a.host,"import pathlib,json,sys;p=json.load(sys.stdin);s=pathlib.Path(p['auth']['stage']);\nfor n,v in [('pg-GPU-authorization.json',p['auth']),('central-envelope.json',p['envelope']),('IG-private-phase-ledger.json',p['envelope']['prior_pool'])]:\n with (s/n).open('x') as f:json.dump(v,f,indent=2)\nprint(json.dumps({'private_phase_bound':True,'original_host_ledger_untouched':True}))",dict(auth=auth,envelope=envelope))
  data=dict(stage_ref=L,auth=auth,envelope=envelope,sudo_password=secret(a.host))
  try:v=remote(a.host,LAUNCH,data)
  finally:data.pop('sudo_password',None)
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','launch_id','MemAvailable_bytes')}))
if __name__=='__main__':main()
