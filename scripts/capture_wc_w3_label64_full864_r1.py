"""Read one original W3 GPU/post handle after its scheduled collection time.

This tool never launches, restarts, repairs, fits, or accepts an experiment.
Raw tensors remain on the server; the CPU post receipt carries their audit.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


REMOTE_PY = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--cpu-launch-ref', type=Path, required=True)
    parser.add_argument('--not-before-unix', type=float, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if time.time() < args.not_before_unix:
        raise ValueError('Collection is not due; no SSH or waiting performed')
    if args.output.exists():
        raise ValueError('Use a new collection receipt; never overwrite')
    launch = json.loads(args.launch_ref.read_text())['dispatch']
    cpu = json.loads(args.cpu_launch_ref.read_text())['launch']
    code = 'launch=' + repr(launch) + '\ncpu=' + repr(cpu) + '\n' + r'''
import fcntl,hashlib,json,subprocess,time
from pathlib import Path
stage=Path(launch['stage']).resolve();project=stage.parent.parent
root=project/'outputs/wc-w3-label-expldev8-parent18-local64-full864-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text())
assert sha(stage/'registration.json')==cpu['registration_sha256']
assert reg['source_revision']==launch['source_revision']==cpu['source_revision']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
original=json.loads((stage/'GPU-launch.json').read_text())
assert original==launch
def read(path):
 return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),
         'data':json.loads(path.read_text())} if path.exists() else None
def process(pid):
 path=Path('/proc')/str(pid)
 try:return {'pid':pid,'state':(path/'stat').read_text().split(') ',1)[1].split()[0],
             'command':(path/'cmdline').read_bytes().replace(bytes([0]),b' ').decode()}
 except FileNotFoundError:return {'pid':pid,'state':None,'command':None}
supervisor=read(root/'supervisor.json');state=supervisor['data'] if supervisor else {}
pids=[launch['supervisor_pid'],launch['post_watcher_pid']]
if state.get('child_pid') is not None:pids.append(state['child_pid'])
lock=(project/'.sync/f1.lock').open('r')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);lock_free=True;fcntl.flock(lock,fcntl.LOCK_UN)
except BlockingIOError:lock_free=False
receipts={str(p.relative_to(project)):read(p) for p in (
 stage/'GPU-launch.json',stage/'new-W3-GPU-authorization.json',
 stage/'production-CPU-result.json',stage/'CPU-final-results.json',
 stage/'post-CPU-exit.json',root/'runner.json',root/'supervisor.json',project/'reports/budget.json',
 project/'reports/gpu-budget-v2.json',
 project/'.sync/wc-simple26d-production-r1-20261015/legacy-bridge.json',
 project/'.sync/wc-simple26d-production-r1-20261015/legacy-W3-billing.json')}
logs={str(p.relative_to(project)):p.read_text(errors='replace')[-6000:]
      for p in (stage/'GPU-supervisor.log',stage/'post-watcher.log',stage/'post-CPU.log',root/'GPU.log') if p.exists()}
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
print(json.dumps({'observed_unix':time.time(),'source_revision':reg['source_revision'],
 'verified_payload_files':len(reg['payload_sha256']),'original_launch':original,
 'processes':[process(pid) for pid in pids],'lock_free':lock_free,'receipts':receipts,
 'log_tails':logs,'compute_apps':{'exit_code':gpu.returncode,'stdout':gpu.stdout,'stderr':gpu.stderr}},allow_nan=False))
'''
    compile(code, 'original-W3-read-only-capture', 'exec')
    call = subprocess.run(
        ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o',
         'ClearAllForwardings=yes', 'gkd_minchen', REMOTE_PY + ' -c ' + shlex.quote(code)],
        text=True, capture_output=True, timeout=180)
    result = {'transport_exit_code': call.returncode, 'stderr': call.stderr,
              'launch_ref': str(args.launch_ref), 'collected_unix': time.time(),
              'launch_ref_sha256': hashlib.sha256(args.launch_ref.read_bytes()).hexdigest()}
    try:
        result['capture'] = json.loads(call.stdout)
    except json.JSONDecodeError:
        result['stdout'] = call.stdout
    with args.output.open('xb') as handle:
        handle.write(gzip.compress(json.dumps(result, allow_nan=False).encode(), mtime=0))
    print(json.dumps({'receipt': str(args.output), 'transport_exit_code': call.returncode,
                      'acceptance_or_method_claim': False}))
    if call.returncode:
        raise SystemExit(call.returncode)


if __name__ == '__main__':
    main()
