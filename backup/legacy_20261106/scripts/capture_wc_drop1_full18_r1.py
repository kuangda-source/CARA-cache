#!/usr/bin/env python3
"""One original-task snapshot: halfway technical only, terminal raw acceptance."""
import argparse,gzip,json,shlex,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
DEFAULT_LAUNCH='reports/wc_drop1_full18_GPU_launch_20261017.json'

def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',default=DEFAULT_LAUNCH)
    p.add_argument('--mode',choices=['admission','halfway','terminal'],required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    launch=json.loads((ROOT/a.launch_ref).read_text())['dispatch']
    key={'halfway':'halfway_check_not_before_unix','terminal':'next_check_not_before_unix'}.get(a.mode)
    if key and time.time()<launch[key]:raise SystemExit('Before frozen check time; no SSH')
    code='LAUNCH='+repr(launch)+'\nMODE='+repr(a.mode)+'\n'+r'''
import fcntl,gzip,json,pathlib,subprocess,sys,time,collections
stage=pathlib.Path(LAUNCH['stage']);root=stage.parents[1];out=root/'outputs'/LAUNCH['run_id'];sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity,sha
reg=json.loads((stage/'registration.json').read_text())
assert reg['source_revision']==LAUNCH['source_revision'] and sha(stage/'registration.json')==LAUNCH['registration_sha256']
v=dict(mode=MODE,observed_unix=time.time(),launch=LAUNCH,registration_sha256=sha(stage/'registration.json'),pool=BudgetPool(root).read(),original_processes={})
sup=json.loads((out/'supervisor.json').read_text()) if (out/'supervisor.json').exists() else {}
run=json.loads((out/'runner.json').read_text()) if (out/'runner.json').exists() else {}
for k,pid in [('supervisor',LAUNCH['supervisor_pid']),('post',LAUNCH['post_watcher_pid']),('runner',sup.get('child_pid'))]:
 if pid:v['original_processes'][k]=process_identity(pid)
v['own_GPU']=subprocess.check_output(['nvidia-smi','-i',LAUNCH['gpu_uuid'],'--query-gpu=uuid,name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
v['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
with (root/'.sync/gpu-locks'/(LAUNCH['gpu_uuid']+'.lock')).open('r+') as handle:
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);v['own_UUID_lock_free']=True;fcntl.flock(handle,fcntl.LOCK_UN)
 except BlockingIOError:v['own_UUID_lock_free']=False
if MODE=='halfway':
 v['technical_progress']=dict(supervisor_status=sup.get('status'),runner_status=run.get('status'),planned_slots=18,states=dict(collections.Counter(q.get('status','UNKNOWN') for q in run.get('runs',[]))),not_reached=18-len(run.get('runs',[])),source_revision=run.get('source_revision'),config_sha256=run.get('config_sha256'))
 stat=__import__('os').statvfs(root);v['disk_available_bytes']=stat.f_bavail*stat.f_frsize
 v['error_tags']={}
 for n,p in [('GPU',out/'GPU.log'),('supervisor',stage/'supervisor.log'),('post',stage/'post-CPU.log')]:
  if p.exists():
   with p.open('rb') as f:f.seek(max(0,p.stat().st_size-65536));s=f.read().decode(errors='replace')
   v['error_tags'][n]=[tag for tag in ['CUDA out of memory','Traceback','RuntimeError','AssertionError','No space left'] if tag in s]
 v['scientific_partial_read']=False
else:
 v['registration']=reg;v['payload_verified']={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()}
 v['runtime_verified']={n:sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()}
 for k,p in [('supervisor',out/'supervisor.json'),('runner',out/'runner.json'),('billing',out/'billing.json'),('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),('production_CPU',stage/'production-CPU-result.json'),('numeric_CPU',stage/'drop1-sampling-CPU-result.json'),('CPU_bundle',stage/'CPU-bundle-result.json')]:
  if p.exists():v[k]=json.loads(p.read_text());v[k+'_sha256']=sha(p)
 for k,p in [('GPU_log_tail',out/'GPU.log'),('supervisor_log_tail',stage/'supervisor.log'),('post_log_tail',stage/'post-CPU.log')]:
  if p.exists():
   with p.open('rb') as f:f.seek(max(0,p.stat().st_size-16384));v[k]=f.read().decode(errors='replace')
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,timeout=120)
    if r.returncode:raise RuntimeError(r.stderr.decode())
    v=json.loads(gzip.decompress(r.stdout));a.output.write_bytes(r.stdout)
    print(json.dumps(dict(receipt=str(a.output),mode=a.mode,processes=v['original_processes'],technical_progress=v.get('technical_progress'),final_status=v.get('final',{}).get('status'),own_UUID_lock_free=v['own_UUID_lock_free'])))

if __name__=='__main__':main()
