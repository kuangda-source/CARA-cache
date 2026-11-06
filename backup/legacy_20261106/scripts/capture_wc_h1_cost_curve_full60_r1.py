"""One bounded read of original full60 handles; no retry, launch, or ledger write."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen']
CODE = r'''
import fcntl,hashlib,json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=root/'.sync/wc-h1-cost-curve-production-r2-20261013'
output=root/'outputs/wc-h1-cost-curve-static-full60-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text())
assert reg['source_revision']=='361ea5c9372332299f7ca29dbffe0ab942274d0f'
launch=json.loads((stage/'GPU-launch.json').read_text())
assert launch['source_revision']==reg['source_revision']
r=dict(observed_unix=time.time(),stage=str(stage),output=str(output),source_revision=reg['source_revision'],
 registration_sha256=sha(stage/'registration.json'),launch=launch,
 payload_verified={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()})
for key,path in [('supervisor',output/'supervisor.json'),('runner',output/'runner.json'),
                 ('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),
                 ('production_CPU',stage/'production-CPU-result.json')]:
 if path.exists():r[key]=json.loads(path.read_text());r[key+'_sha256']=sha(path)
ids={k:launch[k] for k in ('supervisor_pid','post_watcher_pid')}
if r.get('supervisor',{}).get('child_pid'):ids['child_pid']=r['supervisor']['child_pid']
r['original_processes']={}
for key,pid in ids.items():
 proc=pathlib.Path('/proc',str(pid));value=dict(pid=pid,exists=proc.exists())
 if proc.exists():
  try:value['cmdline']=proc.joinpath('cmdline').read_bytes().replace(b'\x00',b' ').decode(errors='replace').strip()
  except FileNotFoundError:value['exists']=False
 r['original_processes'][key]=value
r['ledger']=json.loads((root/'reports/budget.json').read_text());r['ledger_sha256']=sha(root/'reports/budget.json')
r['GPU']=subprocess.check_output(['nvidia-smi','-i','GPU-cebf7119-cf03-23b9-e192-cd196332b704',
 '--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
lock=(root/'.sync/f1.lock').open('a+')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r['kernel_lock_free']=True;fcntl.flock(lock,fcntl.LOCK_UN)
except BlockingIOError:r['kernel_lock_free']=False
lock.close()
for key,path in [('GPU_log_tail',output/'GPU.log'),('post_log_tail',stage/'post-CPU.log')]:
 if path.exists():r[key]='\n'.join(path.read_text(errors='replace').splitlines()[-8:])
print(json.dumps(r,allow_nan=False))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='reports/wc_h1_cost_curve_full60_collection_20261013.json')
    args = parser.parse_args()
    compile(CODE, 'full60-readonly-original-handles', 'exec')
    path = ROOT/args.output
    assert not path.exists(), 'Preserve earlier observation; select a fresh receipt filename'
    result = json.loads(subprocess.check_output(HOST+['python3 -'], input=CODE, text=True, timeout=120))
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    runs = result.get('runner', {}).get('runs', [])
    print(json.dumps(dict(source_revision=result['source_revision'],
                         original_processes=result['original_processes'],
                         finished=sum(r['status']!='RUNNING' for r in runs), planned=60,
                         runner_status=result.get('runner',{}).get('status'),
                         final_status=result.get('final',{}).get('status'),
                         post_exit=result.get('post_exit',{}).get('exit_code'),
                         payload_all_verified=all(result['payload_verified'].values()),
                         kernel_lock_free=result['kernel_lock_free'], GPU=result['GPU'],
                         receipt=str(path))))


if __name__ == '__main__':main()
