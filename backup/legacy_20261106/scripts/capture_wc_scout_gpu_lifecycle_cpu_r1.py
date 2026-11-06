#!/usr/bin/env python3
"""One real-entry CPU observation and a separate offline entry-only acceptor."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CODE=r'''
import gzip,hashlib,json,pathlib,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path(L['project']);stage=pathlib.Path(L['stage']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert stage.parent==root/'.sync' and sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
v=dict(status='SCOUT_LIFECYCLE_CPU_ORIGINAL_ONCE_CAPTURE',mode=MODE,launch=L,observed_unix=time.time(),
 process=process_identity(L['identity']['pid']),GPU_submissions=0,ledger_written=False)
names=dict(bundle='scout-lifecycle-CPU-bundle.json',proof='scout-lifecycle-CPU-proof.json',
 config='configs/wc_scout_'+L['kind'].lower()+'_production_entry_r1_20261018.json',
 dependency='manifests/scout_'+L['kind'].lower()+'_lifecycle_dependency_r1_20261018.json')
if MODE=='halfway':v['result_files_present']={k:(stage/n).exists() for k,n in names.items()}
else:
 v.update(registration=reg,registration_sha256=sha(stage/'registration.json'),
  payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},
  runtime_actual_sha256={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']},files={})
 for k,n in names.items():
  p=stage/n;info=dict(exists=p.exists())
  if p.exists():info.update(sha256=sha(p),data=json.loads(p.read_text()))
  v['files'][k]=info
p=stage/'scout-lifecycle-CPU.log'
if p.exists():
 with p.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-65536));tail=f.read().decode(errors='replace')
 if MODE=='halfway':v['error_lines']=[s for s in tail.splitlines() if any(t in s for t in ('Traceback','AssertionError','RuntimeError','MemoryError'))][-12:]
 else:v['original_log_tail']=tail
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def accept(v):
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.scout_gpu_lifecycle_r1 import accept_cpu
    return accept_cpu(v)


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['halfway','terminal','accept'],required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    if a.mode=='accept':
        raw=a.capture.read_bytes();value=accept(json.loads(gzip.decompress(raw)))
        value.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
        with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
        print(json.dumps(value));return
    L=json.loads(a.launch_ref.read_text())['launch'];assert L is not None
    assert time.time()>=L['halfway_not_before_unix' if a.mode=='halfway' else 'final_not_before_unix'],'Before original check time; no SSH'
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
            PY+' -c '+shlex.quote('L='+repr(L)+'\nMODE='+repr(a.mode)+'\n'+CODE)],capture_output=True,timeout=150)
        if call.returncode:raise RuntimeError(call.stderr.decode())
        raw=call.stdout;value=json.loads(gzip.decompress(raw))
    except (OSError,subprocess.TimeoutExpired,RuntimeError,ValueError) as e:
        value=dict(status='SCOUT_LIFECYCLE_CPU_OBSERVATION_UNKNOWN_NOT_TERMINAL',error_type=type(e).__name__,error=str(e),GPU_submissions=0)
        raw=gzip.compress(json.dumps(value).encode())
    with a.output.open('xb') as f:f.write(raw)
    print(json.dumps({k:value.get(k) for k in ('status','mode','process','error_lines')}))


if __name__=='__main__':main()
