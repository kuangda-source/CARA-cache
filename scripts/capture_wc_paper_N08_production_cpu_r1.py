#!/usr/bin/env python3
"""One original CPU handle snapshot after its ETA; standard-library metadata."""
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
stage=pathlib.Path(LAUNCH['stage']).resolve();sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
CONFIG='configs/wc_paper_N08_balanced_full40_production_r1_20261016.json'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
registration=json.loads((stage/'registration.json').read_text())
assert registration['source_revision']==LAUNCH['source_revision'] and sha(stage/'registration.json')==LAUNCH['registration_sha256']
value=dict(status='N08_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',launch=LAUNCH,observed_unix=time.time(),
 registration=registration,registration_sha256=sha(stage/'registration.json'),
 payload_verified={n:sha(stage/n)==h for n,h in registration['payload_sha256'].items()},
 process=process_identity(LAUNCH['pid']),files={},GPU_submissions=0,ledger_written=False)
for key,name in [('bundle','N08-CPU-bundle-result.json'),('proof','N08-production-CPU-result.json'),('config',CONFIG)]:
 path=stage/name
 value['files'][key]=dict(exists=path.is_file(),ref=name,sha256=sha(path) if path.is_file() else None,
  data=json.loads(path.read_text()) if path.is_file() else None)
config=value['files']['config']['data']
if config:
 for key,b in config['references'].items():
  relative=pathlib.PurePosixPath(b['ref']);assert not relative.is_absolute() and '..' not in relative.parts
  path=stage/relative;assert sha(path)==b['sha256'];raw=path.read_bytes()
  value['files'][key]=dict(exists=True,ref=b['ref'],sha256=sha(path),data=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw))
bundle=value['files']['bundle']['data']
if not bundle or bundle.get('exit_code')!=0:
 path=stage/'N08-CPU-bundle.log'
 if path.is_file():value['CPU_log_tail']=path.read_text(errors='replace')[-24000:]
sys.stdout.buffer.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    launch = json.loads(args.launch_ref.read_text())['launch']
    if time.time() < launch['first_collection_not_before_unix']: raise SystemExit('Before original N08 CPU ETA; no SSH')
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ClearAllForwardings=yes',
        'gkd_minchen', 'python3 -c ' + shlex.quote(remote_code(launch))], capture_output=True, timeout=150)
    if call.returncode: raise RuntimeError(call.stderr.decode(errors='replace'))
    args.output.write_bytes(call.stdout)  # Keep the only observation before local parsing.
    value = json.loads(gzip.decompress(call.stdout))
    bundle = value['files']['bundle']['data']
    print(json.dumps(dict(receipt=str(args.output), original_process=value['process'], payload_files=len(value['payload_verified']),
                         bundle_status=bundle['status'] if bundle else None, production_proof_present=value['files']['proof']['exists'])))


if __name__ == '__main__': main()
