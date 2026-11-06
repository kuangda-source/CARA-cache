"""Actual whole controller with CPU-only child fixture replacements at host boundary."""
import json,os,sys,subprocess,signal
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

def run(stage,dest):
 sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
 import wcomr.wc73_execution_r1 as c
 import wcomr.history104_storage_r2 as hs
 from wcomr.gpu_budget_pool_v2 import atomic_json,sha
 import wc73_whole_controller_r1 as ctl
 import four_card_policy_assets_port_r1 as container
 import four_card_bank24_execution_tools_r1 as bank
 checks=[]
 for scenario in ('success','A_gate_fail','CPU_freeze_fail','B_admission_fail'):
  root=dest/scenario;s=root/'.sync/A';s.mkdir(parents=True);out=root/'outputs'/c.RUN;out.mkdir(parents=True);(root/'reports').mkdir();(s/'scripts').mkdir()
  auth=dict(phase='A',host='four_card',gpu_uuid='GPU-fixture',CPU_score_cpuset='0-3',launch_id=scenario)
  card={'scope_sha256':'fixture'}
  gpu='''import sys,json
from pathlib import Path
sys.path.insert(0,SOURCE)
from wcomr.wc73_execution_r1 import Pool,RUN,read
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
args=dict(zip(sys.argv[1::2],sys.argv[2::2]));r=Path(args['--project']);s=Path(args['--stage']);a=read(s/'pg-GPU-authorization.json');p=Pool(r);phase=a['phase']
assert set(json.load(sys.stdin))=={'sudo_password'}
if phase=='A':
 p.reserve(dict(job_id=RUN,run_id=RUN,billed_limit_GPUh=12,forecast_GPUh=9.5,host='four_card',gpu_uuid='GPU-fixture'),dict(uuid='GPU-fixture',name='RTX 6000 Ada',compute_cap='8.9',memory_used_mib=0,pids=[]))
 p.finish_A(1,'a'*64,SCENARIO!='A_gate_fail')
else:
 if SCENARIO=='B_admission_fail':raise SystemExit(1)
 p.settle(RUN,2,'b'*64)
atomic_json(s/'pg-host-guardian.json',dict(container_exit_code=1 if SCENARIO=='A_gate_fail' else 0,mode_restoration={'restored':True}))
'''.replace('SOURCE',repr(str(stage/'src'))).replace('SCENARIO',repr(scenario))
  post='''import sys,json
from pathlib import Path
sys.path.insert(0,SOURCE)
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.wc73_execution_r1 import RUN,read
args=dict(zip(sys.argv[1::2],sys.argv[2::2]));r=Path(args['--project']);s=Path(args['--stage']);a=read(s/'pg-GPU-authorization.json')
if SCENARIO=='CPU_freeze_fail':raise SystemExit(1)
if a['phase']=='A':atomic_json(r/'outputs'/RUN/'frozen-selection.json',dict(phase_A_GPU_released=True,scope_sha256='fixture',selected_tau=.04))
'''.replace('SOURCE',repr(str(stage/'src'))).replace('SCENARIO',repr(scenario))
  (s/'scripts/wc_wc73_host_guardian_r1.py').write_text(gpu);(s/'scripts/postprocess_cara_wc73_r1.py').write_text(post)
  files={str(f.relative_to(s)):sha(f) for f in (s/'scripts').iterdir()};reg=dict(source_revision='fixture',payload_sha256=files,stage=str(s));atomic_json(s/'registration.json',reg)
  for n,v in [('pg-GPU-authorization.json',auth),('execution-CPU-proof.json',{'passed':True}),('history104-storage.json',{})]:atomic_json(s/n,v)
  value=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=1,origin_gpu_jobs_launched=0,jobs={},events=[]);value.update(c.Pool.accounting(value));atomic_json(root/'reports/gpu-budget-v2.json',value)
  class Storage:
   journal=SimpleNamespace(path=root/'journal')
   def persist(self,k,p,v,write):write(p,v)
  def command(*args,**kw):return ['docker','--name','fixture','--cpus','2','--memory','16g','--entrypoint',sys.executable,'image']
  popen=subprocess.Popen
  def launch(cmd,**kw):
   if cmd[0]=='docker':cmd=[sys.executable]+cmd[cmd.index('image')+1:]
   return popen(cmd,**kw)
  original_run=subprocess.run
  def execute(cmd,**kw):
   if cmd[:2]==['docker','inspect']:return SimpleNamespace(returncode=1,stdout='')
   return original_run(cmd,**kw)
  error=None;old=signal.getsignal(signal.SIGTERM)
  import io
  try:
   with patch.object(c,'validate',lambda *a:(card,reg,auth)),patch.object(hs,'storage_for',lambda *a:Storage()),patch.object(container,'container_command',command),patch.object(bank,'process_environment',lambda *a:{}),patch.object(sys,'argv',['ctl','--project',str(root),'--stage',str(s)]),patch.object(sys,'stdin',io.StringIO('{"sudo_password":"CPU_FIXTURE_NOT_SECRET"}')),patch.object(subprocess,'Popen',launch),patch.object(subprocess,'run',execute):
    try:ctl.main()
    except (AssertionError,RuntimeError):error=True
  finally:signal.signal(signal.SIGTERM,old)
  v=c.Pool(root).read();assert v['reserved_gpu_hours']==0
  if scenario=='success':assert error is None and v['used_gpu_hours']==4 and (s.with_name('A-B')/'pg-host-guardian.json').exists()
  else:
   assert error and v['used_gpu_hours']==2
   if scenario!='B_admission_fail':assert not s.with_name('A-B').exists()
  checks.append(dict(scenario=scenario,passed=True,real_CPU_children=True,GPU_submissions=0))
 return dict(passed=True,checks=checks)
if __name__=='__main__':
 s=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir();r=run(s,out);(out/'proof.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
