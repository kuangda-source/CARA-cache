#!/usr/bin/env python3
"""One original-handle snapshot; terminal collection is refused before its ETA."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time


def remote_code(launch, mode):
    return 'LAUNCH=' + repr(launch) + '\nMODE=' + repr(mode) + '\n' + r'''
import fcntl,gzip,json,pathlib,subprocess,sys,time
root=pathlib.Path(LAUNCH['project']).resolve();stage=pathlib.Path(LAUNCH['stage']).resolve()
assert root==pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve() and stage.parent==root/'.sync'
out=(root/'outputs'/LAUNCH['run_id']).resolve()
sys.path.insert(0,str(stage/'src'))
from wcomr.frozen_shared_production_r1 import CONFIG,sha
from wcomr.gpu_budget_pool_v2 import BudgetPool,process_identity
registration=json.loads((stage/'registration.json').read_text())
assert registration['source_revision']==LAUNCH['source_revision'] and sha(stage/'registration.json')==LAUNCH['registration_sha256']
value=dict(status='N07_SHARED180_ORIGINAL_ONCE_CAPTURE',mode=MODE,observed_unix=time.time(),
 launch=LAUNCH,registration=registration,registration_sha256=sha(stage/'registration.json'),output_root=str(out),
 payload_verified={n:sha(stage/n)==digest for n,digest in registration['payload_sha256'].items()},
 pool=BudgetPool(root).read(),original_processes={})
paths=[('supervisor',out/'supervisor.json'),('authorization',stage/'launch-authorization.json'),
 ('admission_failure',stage/'supervisor-admission-failure.json')]
if MODE=='terminal':
 paths += [('config',stage/CONFIG),('runner',out/'runner.json'),('billing',out/'billing.json'),
  ('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json'),
  ('production_CPU',stage/'production-CPU-result.json'),
  ('production_CPU_bundle',stage/'CPU-bundle-result.json'),('production_CPU_launch',stage/'CPU-launch.json')]
for key,path in paths:
 if path.exists():value[key]=json.loads(path.read_text());value[key+'_sha256']=sha(path)
if MODE=='terminal' and value.get('config'):
 binding=value['config']['references']['bound_inputs'];path=stage/binding['ref']
 assert sha(path)==binding['sha256']
 value['bound_inputs']=json.loads(path.read_text());value['bound_inputs_sha256']=sha(path)
 if 'supervisor' not in value and (stage/'supervisor.json').exists():
  value['supervisor_fallback']=json.loads((stage/'supervisor.json').read_text())
  value['supervisor_fallback_sha256']=sha(stage/'supervisor.json')
 if 'billing' not in value and (stage/'billing.json').exists():
  value['billing_fallback']=json.loads((stage/'billing.json').read_text())
  value['billing_fallback_sha256']=sha(stage/'billing.json')
ids={k:LAUNCH[k] for k in ('supervisor_pid','post_watcher_pid') if LAUNCH.get(k)}
if value.get('supervisor',{}).get('child_pid'):ids['child_pid']=value['supervisor']['child_pid']
for key,pid in ids.items():value['original_processes'][key]=process_identity(pid)
lock=root/'.sync/gpu-locks'/(LAUNCH['gpu_uuid']+'.lock')
value['own_UUID_lock_exists']=lock.is_file();value['own_UUID_lock_free']=False
if lock.is_file():
 with lock.open('r') as handle:
  try:
   fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);value['own_UUID_lock_free']=True
   fcntl.flock(handle,fcntl.LOCK_UN)
  except BlockingIOError:pass
value['own_GPU']=subprocess.check_output(['nvidia-smi','-i',LAUNCH['gpu_uuid'],
 '--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
value['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid',
 '--format=csv,noheader,nounits'],text=True,timeout=10)
if MODE=='terminal':
 for key,path in [('GPU_log_tail',out/'GPU.log'),('supervisor_log_tail',stage/'supervisor.log'),('post_log_tail',stage/'post-CPU.log')]:
  if path.exists():value[key]='\n'.join(path.read_text(errors='replace').splitlines()[-16:])
sys.stdout.buffer.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('admission', 'terminal'), default='terminal')
    args = parser.parse_args()
    launch = json.loads(args.launch_ref.read_text())['dispatch']
    if args.mode == 'terminal' and time.time() < launch['next_check_not_before_unix']:
        raise SystemExit('Before original frozen final-card ETA; no SSH')
    assert not args.output.exists()
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen',
        'python3 -c ' + shlex.quote(remote_code(launch, args.mode))], capture_output=True, timeout=150)
    if result.returncode: raise RuntimeError(result.stderr.decode())
    value = json.loads(gzip.decompress(result.stdout))
    args.output.write_bytes(result.stdout)
    print(json.dumps(dict(receipt=str(args.output), mode=args.mode, source_revision=launch['source_revision'],
        original_processes=value['original_processes'], all_payloads_verified=all(value['payload_verified'].values()),
        original_runner_paths=len(value.get('runner', {}).get('runs', [])),
        final_status=value.get('final', {}).get('status'), post_exit=value.get('post_exit', {}).get('exit_code'))))


if __name__ == '__main__': main()
