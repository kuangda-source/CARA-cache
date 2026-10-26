"""One authorized DEV128 on A6000; original recovery, capture and central settlement.

Runtime source is copied byte-for-byte from independently accepted full CPU.
This controller adds no scientific configuration or new GPU retry permission.
"""
import argparse,base64,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
import cara_two_card_transport_r1 as transport
from audit_cara_dev128_full_cpu_r1 import accept as cpu_accept
from wc_four_card_cara_shared66_terminal_r1 import CAPTURE as ORIGINAL_CAPTURE
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.dev128_execution import RUN,COUNTS,CONFIG,MANIFEST,CPU_PROOF,QUOTE,execution_quote,read,sha
from wcomr.policy_generator_r1.dev128_finance import ENVELOPE
STAGE='cara-dev128-full-a6000-r1-20261026'
PROJECT='/data20t/gaokuangda/worldcache_workspace'
USER_QUOTE='那就按完整128路径方案在两卡服务器启动，先检查空闲GPU、磁盘保护和账本，独占一张卡运行，单卡12 GPUh、累计226 GPUh和最终部署预算不变，安排好半程检查、释放GPU后的评分和最终验收。'
def ssh(code,data=None):return transport.ssh(code,data,docker_group=True,timeout=600)
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def published(ref):
 rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 p=ROOT/'scripts/wc_two_card_cara_dev128_gpu_r1.py'
 assert subprocess.check_output(['git','show',rev+':scripts/'+p.name],cwd=ROOT)==p.read_bytes()
 r=read(ref);assert r['repository']=='kuangda-source/CARA-cache' and r['branch']=='main' and r['sha']==rev and 0<=time.time()-r['observed_unix']<600
 return rev

PREPARE=r'''
import pathlib,json,sys,shutil,hashlib,base64,time
p=json.load(sys.stdin);L=p['CPU_launch'];root=pathlib.Path(L['project']);base=pathlib.Path(L['stage']);stage=root/'.sync'/p['stage_name']
read=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert stage.parent==root/'.sync' and stage.name=='cara-dev128-full-a6000-r1-20261026' and not stage.exists(),'Recover existing stage'
assert sha(base/'registration.json')==L['registration_sha256'] and sha(base/'DEV128-lifecycle-CPU.json')==p['CPU_proof_sha256']
reg=read(base/'registration.json');assert reg['host']=='two_card'
for n,h in reg['payload_sha256'].items():assert sha(base/n)==h
for n,h in reg['runtime_source_sha256'].items():assert sha(root/'runtime'/n)==h
stage.mkdir(mode=0o700)
for n in reg['payload_sha256']:
 t=stage/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,t)
shutil.copyfile(base/'DEV128-lifecycle-CPU.json',stage/'DEV128-lifecycle-CPU.json')
for n,b64 in p['files'].items():
 raw=base64.b64decode(b64);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n];(stage/n).write_bytes(raw)
names=set(reg['payload_sha256'])|set(p['files'])|{'DEV128-lifecycle-CPU.json'}
reg.update(namespace='CARA_DEV128_EXECUTION_R1',stage=str(stage),payload_sha256={n:sha(stage/n) for n in sorted(names)},parent_CPU_registration_sha256=L['registration_sha256'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.policy_generator_r1.dev128_card import check_card,MANIFEST,COUNTS,RUN,CONFIG
from wcomr.policy_generator_r1.dev128_execution import execution_quote
from wcomr.history104_storage_r2 import storage_for
card=check_card(read(stage/MANIFEST));q=execution_quote(card,'two_card',stage/p['quote_path']);c=read(stage/CONFIG)
assert c['matrix']==card['matrix'] and c['scope_counts']==COUNTS and c['run_id']==RUN and c['forecast_complete_GPUh']==q['forecast_GPUh'] and c['billed_limit_GPUh']==12 and c['GPU_dispatch_authorized']
storage=storage_for(stage);storage.check();assert not any(storage.output.iterdir())
v=dict(status='DEV128_EXECUTION_STAGE_BOUND_PENDING_CENTRAL_ADMISSION',host='two_card',project=str(root),stage=str(stage),run_id=RUN,source_revision=reg['source_revision'],registration_sha256=sha(stage/'registration.json'),CPU_proof_sha256=sha(stage/'DEV128-lifecycle-CPU.json'),config_sha256=sha(stage/CONFIG),independent_CPU_acceptance_sha256=sha(stage/'pg-independent-CPU-acceptance.json'),controller_source_revision=p['controller_source_revision'],GPU_submissions=0,ledger_written=False,observed_unix=time.time())
(stage/'pg-stage-reference.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''

PREFLIGHT=r'''
import pathlib,json,sys,subprocess,time,shutil,hashlib,fcntl
p=json.load(sys.stdin);L=p['stage_ref'];root=pathlib.Path(L['project']);stage=pathlib.Path(L['stage'])
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.policy_generator_r1.dev128_execution import RUN,COUNTS,CONFIG,CPU_PROOF,read,sha,execution_quote
from wcomr.policy_generator_r1.dev128_card import check_card,MANIFEST
from wcomr.policy_generator_r1.production_exclusive import observe
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool as BudgetPool
from wcomr.history104_storage_r2 import storage_for
assert sha(stage/'registration.json')==L['registration_sha256'];reg=read(stage/'registration.json')
assert reg['namespace']=='CARA_DEV128_EXECUTION_R1' and reg['host']=='two_card' and reg['stage']==str(stage)
for n,h in reg['payload_sha256'].items():assert sha(stage/n)==h
for n,h in reg['runtime_source_sha256'].items():assert sha(root/'runtime'/n)==h
card=check_card(read(stage/MANIFEST));c=read(stage/CONFIG);q=execution_quote(card,'two_card',stage/'manifests/cara_DEV128_dual_host_whole_quote_r1_20261026.json')
assert c['matrix']==card['matrix'] and c['scope_counts']==COUNTS and c['run_id']==RUN and c['host']=='two_card' and c['compute_capability']==[8,6] and c['GPU_dispatch_authorized'] is True and c['storage_contract_required']
assert c['forecast_complete_GPUh']==q['forecast_GPUh']<=c['billed_limit_GPUh']==12
cpu=read(stage/'pg-independent-CPU-acceptance.json');assert cpu['host']=='two_card' and cpu['production_CPU_accepted'] and cpu['full_GPU_lifecycle_CPU_accepted'] and cpu['independent_quality_models_CPU_accepted']
assert cpu['proof_sha256']==sha(stage/CPU_PROOF)==L['CPU_proof_sha256']
pool=BudgetPool(root).read();assert pool['cap_gpu_hours']==226 and all(pool[k]==v for k,v in BudgetPool.accounting(pool).items())
reasons=[]
if RUN in pool['jobs']:reasons.append('EXISTING_ORIGINAL_JOB_RECOVER_ONLY')
if any(j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False for j in pool['jobs'].values()):reasons.append('OWN_JOB_ACTIVE')
snap=observe(p['gpu_uuid']);g=subprocess.check_output(['/usr/bin/nvidia-smi','-i',p['gpu_uuid'],'--query-gpu=uuid,name,compute_cap,memory.used','--format=csv,noheader,nounits'],text=True).strip().split(',')
assert g[0].strip()==p['gpu_uuid'] and 'RTX A6000' in g[1] and g[2].strip()=='8.6'
if snap['compute_apps'] or int(g[3])>1024:reasons.append('GPU_BUSY')
if snap['mps_processes']!=[]:reasons.append('MPS_PRESENT_OR_UNKNOWN')
if snap['compute_mode'] not in ('Default','Exclusive_Process'):reasons.append('MODE_UNSUPPORTED')
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
if mem<24*2**30:reasons.append('MEMORY')
if pool['available_gpu_hours']<12:reasons.append('BUDGET')
storage=storage_for(stage);storage_snapshot=storage.check();assert not any(storage.output.iterdir())
binding=read(stage/'quality-binding.json');breg=binding['registration'];broot=pathlib.Path(breg['stage'])
assert sha(broot/'registration.json')==binding['acceptance']['registration_sha256']
for n,h in breg['payload_sha256'].items():assert sha(broot/n)==h
ov=pathlib.Path(binding['dependency_overlay']);om=ov.parent/'dependency-overlay-manifest.json';assert sha(om)==binding['dependency_overlay_manifest_sha256']
for n,h in read(om)['files'].items():assert sha(ov/n)==h
value=dict(status='DEV128_PREFLIGHT_PASS' if not reasons else 'DEV128_WAIT',admissible=not reasons,reasons=reasons,observed_unix=time.time(),GPU=snap,storage=storage_snapshot,MemAvailable_bytes=mem,pool_totals=BudgetPool.accounting(pool),quality_binding_verified=True,source_revision=reg['source_revision'],GPU_submissions=0)
'''

CENTRAL=r'''
import json,sys,pathlib,time,copy,hashlib
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
sys.path[:0]=[str(root/'.sync/cara-dev128-fullCPU-ada-r3-20261026/src')]
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool as BudgetPool
from wcomr.policy_generator_r1.dev128_finance import ENVELOPE,RUN
pool=BudgetPool(root);auth=p['auth'];target=root/'reports/dev128-central-envelope-original.json'
with pool.transaction() as v:
 assert v['cap_gpu_hours']==226 and all(v[k]==x for k,x in pool.accounting(v).items())
 if ENVELOPE in v['jobs']:
  assert target.exists(),'Partial reservation: original recovery only'
  old=json.loads(target.read_text());assert old['job']['launch_id']==auth['launch_id'];print(json.dumps(old));raise SystemExit(0)
 assert not any(j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False for j in v['jobs'].values())
 assert RUN not in v['jobs'] and pool.accounting(v)['available_gpu_hours']>=12
 for s in (root/'.sync').glob('cara-dev128-*'):
  assert not (s/'pg-GPU-intent.json').exists() and not (s/'pg-GPU-launch.json').exists(),'Other-host original intent exists'
 before=copy.deepcopy(v)
 job={k:auth[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','stage','scope_counts','billed_limit_GPUh')}
 job.update(job_id=ENVELOPE,kind='EXTERNAL_HOST_DEV128',host='two_card',status='RESERVED_OR_RUNNING',confirmed_GPU_submission=False,actual_GPU_submission_known=False,created_unix=time.time())
 v['jobs'][ENVELOPE]=job;pool.commit(v,dict(type='RESERVE_EXTERNAL_DEV128_ONCE',job_id=ENVELOPE))
 receipt=dict(status='DEV128_CENTRAL_ENVELOPE_RESERVED',central_reservation_verified=True,same_money_not_two_reservations=True,job=job,prior_pool=before,central_after=v,observed_unix=time.time())
 atomic_json(target,receipt);print(json.dumps(receipt))
'''

LAUNCH=r'''
import os,fcntl
p=json.load(sys.stdin);stage=pathlib.Path(p['stage_ref']['stage'])
lock=(stage/'pg-dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for n in ('pg-GPU-intent.json','pg-GPU-launch.json'):
 if (stage/n).exists():print(json.dumps(dict(status='EXISTING_HANDLE_RECOVER_ONLY',original=json.loads((stage/n).read_text()))));raise SystemExit(0)
'''
# Fixed imports followed by the same fresh preflight inside the dispatch lock.
LAUNCH='import json,pathlib,sys,subprocess,time\n'+LAUNCH+PREFLIGHT.replace('p=json.load(sys.stdin);','')+r'''
assert value['admissible'],value['reasons']
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
from wcomr.policy_generator_r1.dev128_execution import validate
auth=p['auth'];assert read(stage/'pg-GPU-authorization.json')==auth and read(stage/'central-envelope.json')==p['envelope']
validate(root,stage)
assert auth['billed_limit_GPUh']==12 and auth['scope_counts']==COUNTS and auth['production_CPU_sha256']==sha(stage/CPU_PROOF)
intent=dict(status='DEV128_ONCE_ONLY_INTENT',launch_id=auth['launch_id'],source_revision=reg['source_revision'],registration_sha256=L['registration_sha256'],gpu_uuid=auth['gpu_uuid'],created_unix=time.time(),no_replay=True)
with (stage/'pg-GPU-intent.json').open('x') as f:json.dump(intent,f);f.flush();os.fsync(f.fileno())
# Same already accepted host interpreter used for both-server CPU orchestration.
command=[sys.executable,'-u',str(stage/'scripts/wc_cara_dev128_host_guardian_r1.py'),'--project',str(root),'--stage',str(stage)]
with (stage/'pg-host-guardian.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 child.stdin.write(json.dumps(dict(sudo_password=p.pop('sudo_password'))).encode());child.stdin.close()
now=time.time();identity=process_identity(child.pid);assert identity['start_ticks'] is not None
result=dict(status='DEV128_SINGLE_DISPATCHED_ADMISSION_PENDING',host='two_card',project=str(root),stage=str(stage),run_id=RUN,launch_id=auth['launch_id'],source_revision=reg['source_revision'],registration_sha256=L['registration_sha256'],config_sha256=auth['config_sha256'],production_CPU_sha256=auth['production_CPU_sha256'],authorization_sha256=sha(stage/'pg-GPU-authorization.json'),gpu_uuid=auth['gpu_uuid'],scope_counts=COUNTS,guardian_identity=identity,container=stage.name+'-gpu',started_unix=now,forecast_GPUh=auth['forecast_GPUh'],billed_limit_GPUh=12,controller_source_revision=auth['controller_source_revision'],halfway_check_not_before_unix=now+auth['forecast_GPUh']*1800,collection_check_not_before_unix=now+auth['forecast_GPUh']*3600+900,next_check_not_before_unix=now+(auth['forecast_GPUh']+8.564486974358973)*3600+900,post_CPU_wall_limit_hours=10)
with (stage/'pg-GPU-launch.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps(result))
'''
CAPTURE=ORIGINAL_CAPTURE.replace('shared66','dev128').replace('SHARED66','DEV128')
CAPTURE=CAPTURE.replace("from wcomr.policy_generator_r1.dev128_card import RUN,read,sha", "from wcomr.policy_generator_r1.dev128_card import RUN,read,sha")
# Technical state always includes original storage, never scientific values while running.
CAPTURE=CAPTURE.replace('print(json.dumps(v,allow_nan=False))',"\nfrom wcomr.history104_storage_r2 import storage_for\ntry:\n g=storage_for(stage);v['technical_storage']=g.check();v['journal_latest']=g.journal.read('telemetry')\nexcept Exception as e:v['technical_storage_error']=str(e)\nprint(json.dumps(v,allow_nan=False))")

def prepare(a):
 cap=read(a.cpu_capture);accepted=read(a.cpu_acceptance);cpu=cpu_accept(cap)
 assert all(accepted[k]==v for k,v in cpu.items()) and accepted['capture_sha256']==sha(a.cpu_capture) and accepted['host']=='two_card'
 card=read(ROOT/MANIFEST);q=execution_quote(card,'two_card');storage=read(a.storage_ref)['storage_contract'];assert storage['run_id']==RUN
 c=dict(host='two_card',compute_capability=[8,6],version='CARA_DEV128_EXECUTION_R1',run_id=RUN,scope_counts=COUNTS,matrix=card['matrix'],forecast_complete_GPUh=q['forecast_GPUh'],billed_limit_GPUh=12,storage_contract_required=True,thermal_telemetry_required=True,GPU_dispatch_authorized=True)
 exposure=read(a.exposure);assert exposure['scoped_no_execution_evidence'] and not exposure['local_read_errors'] and not exposure['protected_remote_hits'] and 0<=time.time()-exposure['observed_unix']<1800
 raw={CONFIG:(json.dumps(c,indent=2)+'\n').encode(),'pg-whole-quote.json':(json.dumps(q,indent=2)+'\n').encode(),'history104-storage.json':(json.dumps(storage,indent=2)+'\n').encode(),'pg-independent-CPU-acceptance.json':a.cpu_acceptance.read_bytes(),'dev128-first-use-exposure.json':a.exposure.read_bytes()}
 return ssh(PREPARE,dict(CPU_launch=cap['launch'],CPU_proof_sha256=cap['proof_sha256'],stage_name=STAGE,quote_path=QUOTE,controller_source_revision=published(a.published_ref),files={n:base64.b64encode(b).decode() for n,b in raw.items()},hashes={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}))

def launch(a):
 L=read(a.stage_ref);rev=published(a.published_ref)
 prior=recover(L)
 if prior['original_files']:return prior
 fresh=ssh(PREFLIGHT+'\nprint(json.dumps(value))',dict(stage_ref=L,gpu_uuid=a.gpu_uuid))
 if not fresh['admissible']:return fresh
 metadata=ssh("import pathlib,json,sys;L=json.load(sys.stdin);s=pathlib.Path(L['stage']);print(json.dumps(dict(exposure=json.loads((s/'dev128-first-use-exposure.json').read_text()),quote=json.loads((s/'pg-whole-quote.json').read_text()))))",L)
 assert time.time()-metadata['exposure']['observed_unix']<1800 and metadata['exposure']['scoped_no_execution_evidence']
 auth=dict(kind='DIRECT_USER_COMPLETE128_LIMIT12',host='two_card',run_id=RUN,launch_id=str(uuid.uuid4()),stage=L['stage'],entry_stage=L['stage'],source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],config_sha256=L['config_sha256'],production_CPU_sha256=L['CPU_proof_sha256'],independent_CPU_acceptance_sha256=L['independent_CPU_acceptance_sha256'],gpu_uuid=a.gpu_uuid,scope_counts=COUNTS,forecast_GPUh=metadata['quote']['forecast_GPUh'],billed_limit_GPUh=12,cumulative_cap_GPUh=226,deployment_limit_seconds=257.7712338712067,relative_native=.8,direct_user_authorization=True,user_reply_quote=USER_QUOTE,controller_source_revision=rev)
 # Persist identity before central mutation; an interruption always recovers this exact identity.
 ssh("import pathlib,json,sys,os;p=json.load(sys.stdin);s=pathlib.Path(p['stage']);f=(s/'pg-GPU-authorization.json').open('x');json.dump(p,f,indent=2);f.write('\\n');f.flush();os.fsync(f.fileno());f.close();print(json.dumps({'authority_bound':True}))",auth)
 envelope=transport.four_ssh(CENTRAL,dict(auth=auth));write(a.output.with_suffix('.central-envelope.json'),envelope)
 ssh(r'''
import pathlib,json,sys
p=json.load(sys.stdin);s=pathlib.Path(p['auth']['stage']);root=pathlib.Path(p['project']);sys.path[:0]=[str(s/'src')]
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool as BudgetPool
pool=BudgetPool(root)
with pool.transaction() as old:
 assert p['auth']['run_id'] not in old['jobs']
 assert not any(j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False for j in old['jobs'].values())
 atomic_json(root/'reports/gpu-budget-v2.json',p['envelope']['prior_pool'])
 atomic_json(s/'central-envelope.json',p['envelope'])
from wcomr.policy_generator_r1.dev128_execution import validate
validate(root,s)
print(json.dumps(dict(execution_binding_CPU_passed=True,GPU_submissions=0)))
''',dict(auth=auth,project=L['project'],envelope=envelope))
 data=dict(stage_ref=L,gpu_uuid=a.gpu_uuid,auth=auth,envelope=envelope,sudo_password=transport.password())
 try:return ssh(LAUNCH,data)
 except Exception as e:return dict(status='DEV128_DISPATCH_UNKNOWN_RECOVER_ONLY',stage_reference=L,intended_launch_id=auth['launch_id'],error_type=type(e).__name__,GPU_replay_allowed=False)
 finally:data.pop('sudo_password',None)

def recover(L):
 return ssh("import pathlib,json,sys;L=json.load(sys.stdin);s=pathlib.Path(L['stage']);v={n:json.loads((s/n).read_text()) for n in ('pg-GPU-authorization.json','central-envelope.json','pg-GPU-intent.json','pg-GPU-launch.json','pg-host-guardian.json','pg-admission-failure.json') if (s/n).exists()};print(json.dumps(dict(status='DEV128_ORIGINAL_RECOVERY_NO_DISPATCH',stage_reference=L,original_files=v)))",L)

def confirm(a):
 v=read(a.capture);L=read(a.launch_ref);assert v['launch']==L and all(v['original_live_handles'].values()) and not v['own_UUID_lock_free']
 from wcomr.policy_price_terminal_r1 import record
 from wcomr.policy_asset_price_review_r1 import exclusive_gate
 ready=record(v,'ready');grant=record(v,'grant');guard=record(v,'guardian');ident=ready['identity']
 assert ready['GPU_context_held'] and grant['runner']==ident and grant['source_revision']==L['source_revision']
 for snap,phase,kw in ((guard['mode_admission']['verified_snapshot'],'idle',{}),(v['current_GPU'],'active',dict(runner=ident))):assert exclusive_gate(snap,gpu_uuid=L['gpu_uuid'],phase=phase,now=snap['observed_unix'],**kw)['observation_passed']
 return transport.four_ssh(r'''
import pathlib,json,sys,time
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');sys.path.insert(0,str(root/'.sync/cara-dev128-fullCPU-ada-r3-20261026/src'))
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool as BudgetPool
from wcomr.policy_generator_r1.dev128_finance import ENVELOPE
pool=BudgetPool(root);L=p['launch']
with pool.transaction() as v:
 j=v['jobs'][ENVELOPE]
 for k in ('launch_id','source_revision','stage','gpu_uuid','run_id'):assert j[k]==L[k]
 assert j['status']=='RESERVED_OR_RUNNING'
 j.update(confirmed_GPU_submission=True,actual_GPU_submission_known=True,admission_capture_sha256=p['capture_sha256']);pool.commit(v,dict(type='CONFIRM_DEV128_EXCLUSIVE_RUNNER',job_id=ENVELOPE))
 print(json.dumps(dict(status='DEV128_CENTRAL_EXCLUSIVE_ADMISSION_CONFIRMED',launch=L,job=j,pool_totals=pool.accounting(v),observed_unix=time.time())))
''',dict(launch=L,capture_sha256=sha(a.capture)))

def settle(a):
 v=read(a.capture)
 from wcomr.policy_generator_r1.dev128_finance import financial_original
 financial_original(v)
 # Financial envelope only; original tensor/video payload is not sent to central host.
 subset={k:v[k] for k in ('launch','pool','original_live_handles','own_UUID_lock_free')};subset['files']={'billing':v['files']['billing']}
 return transport.four_ssh(r'''
import pathlib,json,sys,time
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');sys.path.insert(0,str(root/'.sync/cara-dev128-fullCPU-ada-r3-20261026/src'))
from wcomr.policy_generator_r1.dev128_finance import settle_original
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool as BudgetPool
v=settle_original(BudgetPool(root),p);target=root/'reports/dev128-central-settlement-original.json'
if target.exists():
 old=json.loads(target.read_text());assert old['billing_sha256']==v['billing_sha256'] and old['launch_id']==v['launch_id'];v=old
else:atomic_json(target,v)
print(json.dumps(v))
''',subset)

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','preflight','launch-gpu','recover','capture','confirm-central','settle-central','accept-gpu'])
 for n in ('cpu-capture','cpu-acceptance','storage-ref','exposure','published-ref','stage-ref','launch-ref','capture','central-settlement'):p.add_argument('--'+n,type=Path)
 p.add_argument('--gpu-uuid');p.add_argument('--mode',choices=['admission','halfway','terminal'],default='terminal');p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 if a.command=='prepare':v=prepare(a)
 elif a.command=='preflight':v=ssh(PREFLIGHT+'\nprint(json.dumps(value))',dict(stage_ref=read(a.stage_ref),gpu_uuid=a.gpu_uuid))
 elif a.command=='launch-gpu':v=launch(a)
 elif a.command=='recover':v=recover(read(a.stage_ref))
 elif a.command=='capture':v=ssh(CAPTURE,dict(launch=read(a.launch_ref),terminal=a.mode=='terminal'))
 elif a.command=='confirm-central':v=confirm(a)
 elif a.command=='settle-central':v=settle(a)
 else:
  from wcomr.policy_generator_r1.dev128_terminal import accept
  cap=read(a.capture);cap['central_settlement']=read(a.central_settlement);v=accept(cap);v.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture),central_settlement_ref=str(a.central_settlement),central_settlement_sha256=sha(a.central_settlement))
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','launch_id','admissible','reasons','health','original_live_handles','terminal_collection_error','full_protocol_accepted')}))
if __name__=='__main__':main()
