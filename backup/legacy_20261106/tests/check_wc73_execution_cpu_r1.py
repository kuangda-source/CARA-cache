"""Actual WC73 supervisor, real CPU children; fixture ledgers and GPU observations."""
import json,os,subprocess,sys,time,signal,math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

def run(stage,output):
 sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
 import wcomr.wc73_execution_r1 as c
 import wcomr.wc73_exclusive_r1 as ex
 import wcomr.history104_storage_r2 as hs
 import wc_wc73_worker_r1 as worker
 from wcomr.gpu_budget_pool_v2 import atomic_json,sha,process_identity,DeviceLease
 checks=[]
 for scenario in ('success_A','failure_A','foreign_context','release_lost','success_B','timeout_A'):
  root=output/scenario;fixture=root/'.sync/stage';fixture.mkdir(parents=True);out=root/'outputs'/c.RUN;out.mkdir(parents=True)
  (fixture/'scripts').mkdir();(root/'reports').mkdir();(root/'runtime').mkdir()
  phase='B' if scenario=='success_B' else 'A';reg={'source_revision':'CPU_FIXTURE'};card={'scope_sha256':'fixture'}
  auth=dict(phase=phase,host='four_card',gpu_uuid='GPU-CPU-fixture',launch_id=scenario,forecast_GPUh=9.5)
  for n,v in [('registration.json',reg),(c.MATRIX,card),('execution-CPU-proof.json',{}),('pg-GPU-authorization.json',auth),('plans/cara_wc_time_protocol_r1_20261027/EXECUTION_PLAN.json',{'scope_counts':{'physical_paths':73}})]:atomic_json(fixture/n,v)
  value=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=1,origin_gpu_jobs_launched=0,jobs={},events=[])
  value.update(c.Pool.accounting(value));atomic_json(root/'reports/gpu-budget-v2.json',value)
  pool=c.Pool(root)
  if phase=='B':
   pool.reserve(dict(job_id=c.RUN,run_id=c.RUN,billed_limit_GPUh=12,forecast_GPUh=9.5,host='four_card',gpu_uuid=auth['gpu_uuid'],source_revision='CPU_FIXTURE'),dict(uuid=auth['gpu_uuid'],name='RTX 6000 Ada',compute_cap='8.9',memory_used_mib=0,pids=[]))
   pool.finish_A(1,'a'*64,True)
   atomic_json(out/'frozen-selection.json',dict(scope_sha256='fixture',phase_A_GPU_released=True));auth['frozen_selection_sha256']=sha(out/'frozen-selection.json')
  class Storage:
   output=out
   journal=SimpleNamespace(write=lambda *a:None)
   def check(self):pass
   def persist(self,k,p,v,write):write(p,v)
  childcode='''import sys,os,time,json
from pathlib import Path
sys.path.insert(0,SOURCE)
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
args=dict(zip(sys.argv[1::2],sys.argv[2::2]));s=Path(args['--stage']);p=Path(args['--project'])
assert os.getppid()==int(os.environ['WC_SUPERVISOR_PID'])
assert os.fstat(int(os.environ['WC_LOCK_FD'])).st_ino==(p/'.sync/gpu-locks/GPU-CPU-fixture.lock').stat().st_ino
i={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};i['uid']=os.getuid()
atomic_json(s/'pg-runner-context-ready.json',{'identity':i})
t=time.monotonic()
while not (s/'pg-runner-context-granted.json').exists():
 assert time.monotonic()-t<20
 time.sleep(.02)
time.sleep(2.2)
atomic_json(p/'outputs'/RUN/'A-collection.json',{'diagnostic_gate':{'passed':True}})
sys.exit(EXIT)
'''.replace('SOURCE',repr(str(stage/'src'))).replace('RUN',repr(c.RUN)).replace('EXIT','1' if scenario=='failure_A' else '0')
  (fixture/'scripts/run_cara_wc73_r1.py').write_text(childcode)
  def observe(uuid):
   apps=[];ready=fixture/'pg-runner-context-ready.json'
   if ready.exists():
    i=c.read(ready)['identity'];x=process_identity(i['pid']);live=x['start_ticks']==i['start_ticks'] and x['state'] not in (None,'Z','X')
    if live:apps=[i]
    elif scenario=='release_lost':raise RuntimeError('FIXTURE_RELEASE_TELEMETRY_LOST')
    if scenario=='foreign_context' and (fixture/'pg-runner-context-granted.json').exists():apps.append(dict(pid=99999999,uid=9999,start_ticks=1))
   return dict(gpu_uuid=uuid,compute_mode='Exclusive_Process',compute_apps=apps,mps_processes=[],observed_unix=time.time())
  def smi(args,**kw):
   assert args[0]=='/usr/bin/nvidia-smi'
   return '55, 100, 1500, 0, 0\n' if 'temperature.gpu' in ' '.join(args) else 'GPU-CPU-fixture, RTX 6000 Ada, 0, 8.9\n'
  old=signal.getsignal(signal.SIGTERM);error=None
  original_mono=time.monotonic;calls=[0]
  def mono():
   calls[0]+=1
   return original_mono()+(18000 if scenario=='timeout_A' and calls[0]>1 else 0)
  try:
   with patch.object(c,'validate',lambda *a:(card,reg,auth)),patch.object(hs,'storage_for',lambda *a:Storage()),patch.object(ex,'observe',observe),patch.object(subprocess,'check_output',smi),patch.object(time,'monotonic',mono):
    try:worker.supervise(SimpleNamespace(project=root,stage=fixture))
    except (RuntimeError,ValueError,TimeoutError) as e:error=str(e)
  finally:signal.signal(signal.SIGTERM,old)
  after=pool.read();bill=c.read(out/(phase+'-billing.json'));release=c.read(out/(phase+'-release.json'))
  with DeviceLease(root,auth['gpu_uuid']):pass
  if scenario=='success_A':
   assert error is None and after['reserved_gpu_hours']==7 and math.isclose(after['used_gpu_hours'],1+bill['actual_GPUh'],rel_tol=0,abs_tol=1e-12) and release['numerical_GPU_equivalence_passed']
  elif scenario=='success_B':assert error is None and after['reserved_gpu_hours']==0 and math.isclose(after['used_gpu_hours'],2+bill['actual_GPUh'],rel_tol=0,abs_tol=1e-12)
  else:assert error and after['reserved_gpu_hours']==0
  checks.append(dict(scenario=scenario,passed=True,real_child=True,fixture_ledger_only=True))
 # Missing exact freeze and foreign active reservation must never enter B/new envelope.
 root=output/'finance';(root/'reports').mkdir(parents=True)
 v=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=1,origin_gpu_jobs_launched=0,jobs={},events=[]);v.update(c.Pool.accounting(v));atomic_json(root/'reports/gpu-budget-v2.json',v)
 pool=c.Pool(root);job=dict(job_id=c.RUN,run_id=c.RUN,billed_limit_GPUh=12,forecast_GPUh=9.5,host='four_card',gpu_uuid='GPU-fixture');gpu=dict(uuid='GPU-fixture',name='RTX 6000 Ada',compute_cap='8.9',memory_used_mib=0,pids=[])
 pool.reserve(job,gpu)
 try:pool.reserve(job,gpu)
 except ValueError:pass
 else:raise AssertionError('duplicate launch accepted')
 pool.finish_A(2,'a'*64,True);pool.finish_A(2,'a'*64,True);pool.settle(c.RUN,3,'b'*64);assert pool.read()['used_gpu_hours']==6
 return dict(passed=True,checks=checks,finance_idempotent=True,GPU_submissions=0)
if __name__=='__main__':
 stage=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir();r=run(stage,out);(out/'proof.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
