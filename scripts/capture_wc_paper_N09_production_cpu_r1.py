#!/usr/bin/env python3
"""One read-only original CPU snapshot after its ETA, saved before parsing."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time


def remote_code(launch):
    return 'LAUNCH=' + repr(launch) + '\n' + r'''
import gzip,hashlib,json,pathlib,sys,time
project=pathlib.Path(LAUNCH['project']).resolve();stage=pathlib.Path(LAUNCH['stage']).resolve()
assert stage.relative_to(project).parts[0]=='.sync'
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
CONFIG='configs/wc_paper_N09_runtime_profile40_production_r1_20261016.json'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def path(name):
 relative=pathlib.PurePosixPath(name)
 assert not relative.is_absolute() and '..' not in relative.parts
 p=stage.joinpath(*relative.parts).resolve();p.relative_to(stage)
 return p
def read(name):
 p=path(name)
 if not p.is_file():return dict(exists=False,ref=name,sha256=None,data=None)
 raw=p.read_bytes();v=dict(exists=True,ref=name,sha256=sha(raw),bytes=len(raw),data=None)
 try:v['data']=json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
 except (ValueError,OSError,EOFError) as error:v['parse_error']=str(error)
 return v
raw=path('registration.json').read_bytes();registration=json.loads(raw)
assert registration['source_revision']==LAUNCH['source_revision'] and sha(raw)==LAUNCH['registration_sha256']
actual={n:sha(path(n).read_bytes()) if path(n).is_file() else None for n in registration['payload_sha256']}
value=dict(status='N09_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',launch=LAUNCH,observed_unix=time.time(),
 registration=registration,registration_sha256=sha(raw),payload_actual_sha256=actual,
 payload_verified={n:actual[n]==h for n,h in registration['payload_sha256'].items()},
 process=process_identity(LAUNCH['identity']['pid']),files={},GPU_submissions=0,ledger_written=False)
for key,name in [('bundle','N09-CPU-bundle-result.json'),('proof','N09-production-CPU-result.json'),
                 ('CPU_exit','N09-production-CPU-exit.json'),('config',CONFIG)]:
 value['files'][key]=read(name)
config=value['files']['config']['data']
if config:
 for key,info in config['references'].items():value['files'][key]=read(info['ref'])
bundle=value['files']['bundle']['data']
if not bundle or bundle.get('exit_code')!=0:
 p=path('N09-CPU-bundle.log')
 if p.is_file():
  with p.open('rb') as h:
   h.seek(max(0,p.stat().st_size-24576));value['CPU_log_tail']=h.read(24576).decode(errors='replace')
sys.stdout.buffer.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original once-capture')
    launch = json.loads(args.launch_ref.read_text())['launch']
    if time.time() < launch['first_collection_not_before_unix']:
        raise SystemExit('Before original N09 production CPU ETA; no SSH')
    try:
        call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o',
            'ClearAllForwardings=yes', 'gkd_minchen', 'python3 -c ' + shlex.quote(remote_code(launch))],
            capture_output=True, timeout=150)
    except (subprocess.TimeoutExpired, OSError) as error:
        value = dict(status='N09_CPU_CAPTURE_TRANSPORT_UNKNOWN_ORIGINAL_HANDLE_RETAINED', launch=launch,
            error_type=type(error).__name__, error=str(error), original_task_terminal=False,
            no_CPU_or_GPU_relaunch_authority=True, GPU_submissions=0, ledger_written=False)
        with args.output.open('xb') as handle:handle.write(gzip.compress(json.dumps(value).encode()))
        raise
    if call.returncode:
        value = dict(status='N09_CPU_CAPTURE_COMMAND_FAILED_ORIGINAL_HANDLE_RETAINED', launch=launch,
            transport_exit_code=call.returncode, stderr=call.stderr.decode(errors='replace')[-24576:],
            stdout=call.stdout.decode(errors='replace')[-24576:], original_task_terminal=False,
            no_CPU_or_GPU_relaunch_authority=True, GPU_submissions=0, ledger_written=False)
        with args.output.open('xb') as handle:handle.write(gzip.compress(json.dumps(value).encode()))
        raise RuntimeError('Original CPU collection command failed; raw failure retained, no relaunch')
    with args.output.open('xb') as handle:handle.write(call.stdout)
    value = json.loads(gzip.decompress(call.stdout))
    bundle = value['files']['bundle']['data']
    print(json.dumps(dict(receipt=str(args.output), original_process=value['process'],
        payload_files=len(value['payload_verified']), bundle_status=bundle.get('status') if bundle else None,
        production_proof_present=value['files']['proof']['exists'])))


if __name__ == '__main__':main()
