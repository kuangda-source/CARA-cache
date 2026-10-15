#!/usr/bin/env python3
"""One collection after the registered ETA; no retries or launch operations."""
import argparse,gzip,json,shlex,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',default='reports/wc_simple26d_full36_GPU_launch_20261015.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    launch=json.loads((ROOT/a.launch_ref).read_text())['dispatch']
    if time.time()<launch['next_check_not_before_unix']:raise SystemExit('Before original ETA; no SSH collection')
    assert not a.output.exists()
    code='LAUNCH='+repr(launch)+'\n'+r'''
import fcntl,gzip,json,pathlib,subprocess,sys,time
stage=pathlib.Path(LAUNCH['stage']);root=stage.parents[1];out=root/'outputs'/LAUNCH['run_id'];sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity,sha
reg=json.loads((stage/'registration.json').read_text())
assert reg['source_revision']==LAUNCH['source_revision'] and sha(stage/'registration.json')==LAUNCH['registration_sha256']
r=dict(observed_unix=time.time(),launch=LAUNCH,payload_verified={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()},
    pool=BudgetPool(root).read(),original_processes={})
for k,path in [('supervisor',out/'supervisor.json'),('runner',out/'runner.json'),('billing',out/'billing.json'),
    ('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),('production_CPU',stage/'production-CPU-result.json'),('legacy_bridge',stage/'legacy-bridge.json')]:
 if path.exists():r[k]=json.loads(path.read_text());r[k+'_sha256']=sha(path)
ids={k:LAUNCH[k] for k in ('supervisor_pid','post_watcher_pid')}
if r.get('supervisor',{}).get('child_pid'):ids['child_pid']=r['supervisor']['child_pid']
for k,pid in ids.items():r['original_processes'][k]=process_identity(pid)
with (root/'.sync/gpu-locks'/(LAUNCH['gpu_uuid']+'.lock')).open('a+') as handle:
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);r['own_UUID_lock_free']=True;fcntl.flock(handle,fcntl.LOCK_UN)
 except BlockingIOError:r['own_UUID_lock_free']=False
r['own_GPU']=subprocess.check_output(['nvidia-smi','-i',LAUNCH['gpu_uuid'],'--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
for k,path in [('GPU_log_tail',out/'GPU.log'),('supervisor_log_tail',stage/'supervisor.log'),('post_log_tail',stage/'post-CPU.log')]:
 if path.exists():r[k]='\n'.join(path.read_text(errors='replace').splitlines()[-12:])
sys.stdout.buffer.write(gzip.compress(json.dumps(r,allow_nan=False).encode()))
'''
    run=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -c '+shlex.quote(code)],capture_output=True,timeout=120)
    if run.returncode:raise RuntimeError(run.stderr.decode())
    result=json.loads(gzip.decompress(run.stdout));a.output.write_bytes(run.stdout)
    print(json.dumps(dict(receipt=str(a.output),source_revision=launch['source_revision'],original_processes=result['original_processes'],
        payload_all_verified=all(result['payload_verified'].values()),planned_slots=36,actual_runner_slots=len(result.get('runner',{}).get('runs',[])),
        final_status=result.get('final',{}).get('status'),post_exit=result.get('post_exit',{}).get('exit_code'),own_UUID_lock_free=result['own_UUID_lock_free'],pool_totals={k:result['pool'][k] for k in ('used_gpu_hours','reserved_gpu_hours','available_gpu_hours')})))

if __name__=='__main__':main()
