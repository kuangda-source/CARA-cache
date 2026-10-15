#!/usr/bin/env python3
"""One original no-GPU production-CPU collection after its registered ETA."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'

def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    launch=json.loads(a.launch_ref.read_text())['launch']
    assert time.time()>=launch['first_collection_not_before_unix'],'Before original CPU ETA; no SSH'
    code='LAUNCH='+repr(launch)+'\n'+r'''
import hashlib,json,pathlib,sys,time
stage=pathlib.Path(LAUNCH['stage']);sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text())
value=dict(status='N05_PRODUCTION_CPU_ONCE_CAPTURE',observed_unix=time.time(),launch=LAUNCH,
 registration=reg,registration_SHA256=sha(stage/'registration.json'),
 payload_verified={name:sha(stage/name)==digest for name,digest in reg['payload_sha256'].items()},
 process=process_identity(LAUNCH['pid']),files={},GPU_submissions=0,ledger_written=False)
for name in ('CPU-bundle-result.json','production-CPU-result.json'):
 path=stage/name;value['files'][name]=dict(exists=path.exists(),sha256=sha(path) if path.exists() else None,
  data=json.loads(path.read_text()) if path.exists() else None)
if not value['files']['CPU-bundle-result.json']['exists'] or value['files']['CPU-bundle-result.json']['data'].get('exit_code')!=0:
 value['CPU_log_tail']=(stage/'CPU-bundle.log').read_text(errors='replace')[-24000:]
print(json.dumps(value))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,text=True,timeout=120)
    assert r.returncode==0,r.stderr
    value=json.loads(r.stdout);a.output.write_bytes(gzip.compress(json.dumps(value,indent=2).encode(),mtime=0))
    print(json.dumps(dict(status=value['status'],process=value['process'],bundle_exists=value['files']['CPU-bundle-result.json']['exists'],
        production_exists=value['files']['production-CPU-result.json']['exists'])))

if __name__=='__main__':main()
