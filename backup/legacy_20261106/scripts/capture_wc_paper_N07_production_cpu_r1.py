#!/usr/bin/env python3
"""One capture of the original production CPU handle after its recorded ETA."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    launch = json.loads(args.launch_ref.read_text())['launch']
    if time.time() < launch['first_collection_not_before_unix']:
        raise SystemExit('Before original N07 production CPU ETA; no SSH')
    code = 'LAUNCH=' + repr(launch) + '\n' + r'''
import gzip,hashlib,json,pathlib,sys,time
stage=pathlib.Path(LAUNCH['stage']);sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
from wcomr.frozen_shared_production_r1 import CONFIG
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
registration=json.loads((stage/'registration.json').read_text())
assert registration['source_revision']==LAUNCH['source_revision']
assert sha(stage/'registration.json')==LAUNCH['registration_sha256']
value=dict(status='N07_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',launch=LAUNCH,observed_unix=time.time(),
 registration=registration,registration_sha256=sha(stage/'registration.json'),
 payload_verified={name:sha(stage/name)==digest for name,digest in registration['payload_sha256'].items()},
 process=process_identity(LAUNCH['pid']),files={},GPU_submissions=0,ledger_written=False)
for key,name in [('bundle','CPU-bundle-result.json'),('proof','production-CPU-result.json'),('config',CONFIG)]:
 path=stage/name
 value['files'][key]=dict(exists=path.is_file(),ref=name,sha256=sha(path) if path.is_file() else None,
  data=json.loads(path.read_text()) if path.is_file() else None)
config=value['files']['config']['data']
if config:
 binding=config['references']['bound_inputs'];path=stage/binding['ref']
 assert sha(path)==binding['sha256']
 value['files']['bound_inputs']=dict(exists=True,ref=binding['ref'],sha256=sha(path),data=json.loads(path.read_text()))
bundle=value['files']['bundle']['data']
if not bundle or bundle.get('exit_code')!=0:
 path=stage/'CPU-bundle.log'
 if path.is_file():value['CPU_log_tail']=path.read_text(errors='replace')[-24000:]
sys.stdout.buffer.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
'''
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen', 'python3 -c ' + shlex.quote(code)],
        capture_output=True, timeout=150)
    if result.returncode: raise RuntimeError(result.stderr.decode())
    value = json.loads(gzip.decompress(result.stdout))
    args.output.write_bytes(result.stdout)
    print(json.dumps(dict(receipt=str(args.output), original_process=value['process'],
        payload_files=len(value['payload_verified']), bundle_status=value['files']['bundle']['data']['status']
            if value['files']['bundle']['data'] else None,
        production_proof_present=value['files']['proof']['exists'])))


if __name__ == '__main__': main()
