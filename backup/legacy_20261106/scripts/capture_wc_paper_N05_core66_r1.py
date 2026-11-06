#!/usr/bin/env python3
"""One original-handle collection after ETA; no launch, retries or mutations."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    launch=json.loads(a.launch_ref.read_text())['dispatch']
    if time.time()<launch['next_check_not_before_unix']:raise SystemExit('Before original N05 ETA; no SSH')
    assert not a.output.exists()
    code='LAUNCH='+repr(launch)+'\n'+r'''
import fcntl,gzip,json,pathlib,subprocess,sys,time
stage=pathlib.Path(LAUNCH['stage']);root=stage.parents[1];out=root/'outputs'/LAUNCH['run_id'];sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity,sha
reg=json.loads((stage/'registration.json').read_text())
assert reg['source_revision']==LAUNCH['source_revision'] and sha(stage/'registration.json')==LAUNCH['registration_sha256']
r=dict(status='N05_CORE66_ORIGINAL_ONCE_CAPTURE',observed_unix=time.time(),launch=LAUNCH,registration=reg,
 payload_verified={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()},pool=BudgetPool(root).read(),original_processes={})
for k,path in [('supervisor',out/'supervisor.json'),('runner',out/'runner.json'),('billing',out/'billing.json'),
 ('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),('production_CPU',stage/'production-CPU-result.json'),
 ('production_bundle',stage/'CPU-bundle-result.json'),('authorization',stage/'GPU-authorization.json')]:
 if path.exists():r[k]=json.loads(path.read_text());r[k+'_sha256']=sha(path)
ids={k:LAUNCH[k] for k in ('supervisor_pid','post_watcher_pid') if LAUNCH.get(k)}
if r.get('supervisor',{}).get('child_pid'):ids['child_pid']=r['supervisor']['child_pid']
for k,pid in ids.items():r['original_processes'][k]=process_identity(pid)
with (root/'.sync/gpu-locks'/(LAUNCH['gpu_uuid']+'.lock')).open('a+') as handle:
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);r['own_UUID_lock_free']=True;fcntl.flock(handle,fcntl.LOCK_UN)
 except BlockingIOError:r['own_UUID_lock_free']=False
r['own_GPU']=subprocess.check_output(['nvidia-smi','-i',LAUNCH['gpu_uuid'],'--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
r['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
for k,path in [('GPU_log_tail',out/'GPU.log'),('supervisor_log_tail',stage/'supervisor.log'),('post_log_tail',stage/'post-CPU.log')]:
 if path.exists():r[k]='\n'.join(path.read_text(errors='replace').splitlines()[-16:])
sys.stdout.buffer.write(gzip.compress(json.dumps(r,allow_nan=False).encode()))
'''
    run=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -c '+shlex.quote(code)],capture_output=True,timeout=120)
    if run.returncode:raise RuntimeError(run.stderr.decode())
    a.output.write_bytes(run.stdout)
    v=json.loads(gzip.decompress(run.stdout))
    print(json.dumps(dict(receipt=str(a.output),source_revision=launch['source_revision'],payload_all_verified=all(v['payload_verified'].values()),
        original_processes=v['original_processes'],planned_slots=66,runner_slots=len(v.get('runner',{}).get('runs',[])),
        final_status=v.get('final',{}).get('status'),post_exit=v.get('post_exit',{}).get('exit_code'),own_UUID_lock_free=v['own_UUID_lock_free'],
        pool_totals={k:v['pool'][k] for k in ('used_gpu_hours','reserved_gpu_hours','available_gpu_hours')})))

if __name__=='__main__':main()
