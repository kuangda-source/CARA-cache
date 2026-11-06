"""Read one original B1 handle; confirm or settle the same central envelope."""
import argparse,json,sys,time
from pathlib import Path
from wc_cara_ig_b1_gpu_r1 import remote,read,write,ROOT

CAPTURE=r'''
import pathlib,json,sys,subprocess,time
p=json.load(sys.stdin);stage=pathlib.Path(p['stage']);root=pathlib.Path(p['project']);sys.path[:0]=[str(stage/'src')]
from wcomr.innovation_gain_b1_card_r1 import RUN,read,sha,PhaseBudgetPool
from wcomr.gpu_budget_pool_v2 import same_live_process,DeviceLease
from wcomr.policy_generator_r1.production_exclusive import observe
from wcomr.history104_storage_r2 import storage_for
out=root/'outputs'/RUN
files={}
for name,path in dict(launch=stage/'pg-GPU-launch.json',auth=stage/'pg-GPU-authorization.json',guardian=stage/'pg-host-guardian.json',admission_failure=stage/'pg-admission-failure.json',ready=stage/'pg-runner-context-ready.json',grant=stage/'pg-runner-context-granted.json',supervisor=out/'supervisor.json',health=out/'runner-health.json',billing=out/'billing.json',release=out/'exclusive-monitor-final.json',post_exit=out/'post-exit.json').items():
 if path.exists():files[name]=dict(value=read(path),sha256=sha(path))
L=files.get('launch',{}).get('value');sup=files.get('supervisor',{}).get('value',{});guard=files.get('guardian',{}).get('value',{})
live={n:same_live_process(i) for n,i in dict(guardian=guard.get('identity'),supervisor=sup.get('supervisor_identity'),runner=sup.get('child_identity'),post=sup.get('post_identity')).items() if i}
lease=DeviceLease(root,files['auth']['value']['gpu_uuid'])
try:lease.acquire();free=True
except BlockingIOError:free=False
finally:lease.close()
terminal=bool(guard.get('status')=='IG_B1_HOST_GUARDIAN_TERMINAL' and not any(live.values()))
if terminal:
 for name in ('B1-results.json','post-results.json','collection-verified.json'):
  path=out/name
  if path.exists():files[name]=dict(value=read(path),sha256=sha(path))
logs={}
for name,path in dict(guardian=stage/'pg-host-guardian.log',container=stage/'pg-container.log',GPU=out/'GPU.log',post=out/'post-CPU.log').items():
 if path.exists():
  with path.open('rb') as f:f.seek(max(0,path.stat().st_size-2500));logs[name]=f.read().decode(errors='replace')
print(json.dumps(dict(status='IG_B1_ORIGINAL_CAPTURE',observed_unix=time.time(),stage=str(stage),project=str(root),files=files,live_handles=live,UUID_lock_free=free,terminal=terminal,GPU=observe(files['auth']['value']['gpu_uuid']),private_pool=PhaseBudgetPool(root,stage).read() if (stage/'IG-private-phase-ledger.json').exists() else None,storage=storage_for(stage).check(),log_tails=logs)))
'''
CENTRAL=r'''
import pathlib,json,sys,time,copy
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');sys.path.insert(0,p['source_stage']+'/src')
from wcomr.innovation_gain_b1_card_r1 import RUN,ENVELOPE
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool
from wcomr.gpu_budget_pool_v2 import atomic_json
v=p['capture'];auth=v['files']['auth']['value'];pool=HostBudgetPool(root)
assert 0<=time.time()-v['observed_unix']<180
with pool.transaction() as current:
 j=current['jobs'][ENVELOPE]
 assert all(j[k]==auth[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','stage','scope_counts','billed_limit_GPUh','host'))
 if p['command']=='confirm':
  from wcomr.policy_generator_r1.production_exclusive import verify
  ready=v['files']['ready']['value'];grant=v['files']['grant']['value'];assert ready['GPU_context_held'] and grant['runner']==ready['identity'] and v['live_handles']['runner'] and not v['UUID_lock_free']
  verify(v['GPU'],auth['gpu_uuid'],ready['identity'])
  j.update(confirmed_GPU_submission=True,actual_GPU_submission_known=True);pool.commit(current,dict(type='IG_B1_EXCLUSIVE_CONTEXT_CONFIRMED',job_id=ENVELOPE))
  result=dict(status='IG_B1_CENTRAL_ADMISSION_CONFIRMED',job=j,observed_unix=time.time())
 else:
  assert v['terminal'] and v['UUID_lock_free'] and not any(v['live_handles'].values()) and not v['GPU']['compute_apps']
  bill=v['files']['billing']['value'];job=v['private_pool']['jobs'][RUN]
  assert all(bill[k]==auth[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh'))
  assert bill['actual_GPUh']==bill['wall_seconds']/3600 and bill['actual_GPUh']>=0
  assert job['status']=='SETTLED' and job['billing_sha256']==v['files']['billing']['sha256'] and job['actual_GPUh']==bill['actual_GPUh']
  if j['status']=='SETTLED':assert j['actual_GPUh']==bill['actual_GPUh'] and j['billing_sha256']==job['billing_sha256']
  else:
   j.update(status='SETTLED',actual_GPUh=bill['actual_GPUh'],billing_sha256=job['billing_sha256'],settled_unix=time.time())
   if bill['actual_GPUh']>j['billed_limit_GPUh']:current['budget_overrun_recorded']=True
   pool.commit(current,dict(type='IG_B1_SETTLE_EXACT_ORIGINAL_PHASE_ONCE',job_id=ENVELOPE))
  result=dict(status='IG_B1_CENTRAL_SETTLED',job=j,pool_totals=pool.accounting(current),observed_unix=time.time(),same_money_not_two_charges=True)
 atomic_json(root/('reports/ig-b1-central-'+p['command']+'-original.json'),result)
print(json.dumps(result))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['capture','confirm','settle']);p.add_argument('--host',choices=['two_card','four_card'],default='two_card')
 for n in ('stage-ref','capture','four-cpu-capture'):p.add_argument('--'+n,type=Path)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 if a.command=='capture':v=remote(a.host,CAPTURE,read(a.stage_ref))
 else:v=remote('four_card',CENTRAL,dict(command=a.command,capture=read(a.capture),source_stage=read(a.four_cpu_capture)['launch']['stage']))
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','terminal','live_handles','job','pool_totals')}))
if __name__=='__main__':main()
