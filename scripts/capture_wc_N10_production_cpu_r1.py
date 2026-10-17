#!/usr/bin/env python3
"""One original production CPU health/capture, then independent offline accept."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
REMOTE=r'''
import gzip,hashlib,json,pathlib,sys,time
sys.dont_write_bytecode=True
stage=pathlib.Path(L['stage']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==L['source_revision']
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
v=dict(status='N10_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',observed_unix=time.time(),launch=L,
 registration_sha256=sha(stage/'registration.json'),registration=reg,process=process_identity(L['identity']['pid']),
 GPU_submissions=0,ledger_written=False,files={})
if MODE=='terminal':
 v['payload_actual_sha256']={n:sha(stage/n) for n in reg['payload_sha256']}
 for name,ref in [('bundle','N10-production-CPU-bundle-result.json'),('proof','CPU-scoring-entry-result.json'),
  ('exit','N10-production-CPU-exit.json'),('config','N10-production-config.json')]:
  p=stage/ref;v['files'][name]=dict(data=json.loads(p.read_text()),sha256=sha(p)) if p.is_file() else dict(data=None)
 config=v['files']['config'].get('data')
 if config:
  for name in ('unpriced_scope','whole_card_cost'):
   p=stage/config['references'][name]['ref'];v['files'][name]=dict(data=json.loads(p.read_text()),sha256=sha(p))
 for name in ['production-CPU.log']+['production-CPU-command-'+str(i)+'.log' for i in range(5)]:
  p=stage/name
  if p.is_file():
   with p.open('rb') as h:h.seek(0,2);size=h.tell();h.seek(max(0,size-16000));v.setdefault('log_tails',{})[name]=h.read().decode(errors='replace')
else:
 v['scientific_data_read']=False
 p=stage/'N10-production-CPU-exit.json';v['exit_available']=p.is_file()
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--mode',choices=['health','terminal','accept'],required=True)
    p.add_argument('--capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve each original receipt; use it offline')
    if a.mode=='accept':
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
        from wcomr.automatic_quality_production_cpu_r1 import accept
        raw=a.capture.read_bytes();v=json.loads(gzip.decompress(raw));r=accept(v)
        r.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest(),verifier_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        with a.output.open('x') as h:json.dump(r,h,indent=2,allow_nan=False);h.write('\n')
        print(json.dumps(r));return
    launch=json.loads(a.launch_ref.read_text())['launch'];key='halfway_not_before_unix' if a.mode=='health' else 'final_not_before_unix'
    if time.time()<launch[key]:raise ValueError('Before original CPU check time; no SSH')
    code='L='+repr(launch)+'\nMODE='+repr(a.mode)+'\n'+REMOTE
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(code)],capture_output=True,timeout=120)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
    except (OSError,subprocess.TimeoutExpired,RuntimeError) as error:
        v=dict(status='N10_CPU_OBSERVATION_UNKNOWN_NOT_TASK_TERMINAL',launch=launch,error_type=type(error).__name__,error=str(error))
        with a.output.open('xb') as h:h.write(gzip.compress(json.dumps(v).encode()))
        raise
    with a.output.open('xb') as h:h.write(call.stdout)
    v=json.loads(gzip.decompress(call.stdout));print(json.dumps(dict(status=v['status'],process=v['process'],receipt=str(a.output))))


if __name__=='__main__':main()
