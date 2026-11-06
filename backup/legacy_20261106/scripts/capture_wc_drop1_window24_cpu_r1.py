#!/usr/bin/env python3
"""One gated original CPU observation, then offline full24 production acceptance."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'

CODE = r'''
import gzip,hashlib,json,pathlib,sys,time
sys.dont_write_bytecode=True
stage=pathlib.Path(L['stage']);project=pathlib.Path(L['project'])
assert stage.relative_to(project).parts[0]=='.sync'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==L['source_revision']
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
v=dict(status='WINDOW24_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',mode=MODE,launch=L,
 observed_unix=time.time(),registration_sha256=sha(stage/'registration.json'),
 process=process_identity(L['identity']['pid']),GPU_submissions=0,ledger_written=False)
if MODE=='halfway':
 worker='scripts/run_wc_drop1_window24_cpu_bundle_r1.py'
 assert sha(stage/worker)==reg['payload_sha256'][worker]
 v.update(worker_source_SHA_accepted=True,bundle_exists=(stage/'window24-CPU-bundle-result.json').is_file(),
  production_proof_exists=(stage/'window24-production-CPU-result.json').is_file(),scientific_results_read=False)
else:
 v.update(registration=reg,payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},
  runtime_actual_sha256={n:sha(project/'runtime'/n) for n in reg['runtime_source_sha256']},files={})
 for key,name in [('bundle','window24-CPU-bundle-result.json'),('proof','window24-production-CPU-result.json'),
  ('config','configs/wc_drop1_correction_window_full24_production_r1_20261018.json')]:
  p=stage/name;info=dict(exists=p.is_file(),data=None)
  if p.is_file():
   raw=p.read_bytes();info.update(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
   try:info['data']=json.loads(raw)
   except ValueError as e:info['parse_error']=str(e)
  v['files'][key]=info
log=stage/'window24-CPU-bundle.log'
if log.is_file():
 with log.open('rb') as h:h.seek(0,2);n=h.tell();h.seek(max(0,n-65536));tail=h.read().decode(errors='replace')
 if MODE=='halfway':v['error_lines']=[s for s in tail.splitlines() if any(x in s for x in ('Traceback','RuntimeError','AssertionError','MemoryError','No space left'))][-12:]
 else:v['original_log_tail']=tail
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['halfway','terminal','accept'],required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--capture',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Read the original receipt offline; do not observe twice')
    if a.mode=='accept':
        sys.path.insert(0,str(ROOT/'src'))
        from wcomr.drop1_window24_cpu_acceptance_r1 import accept
        raw=a.capture.read_bytes();result=accept(json.loads(gzip.decompress(raw)))
        result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
        with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
        print(json.dumps(result));return
    launch=json.loads(a.launch_ref.read_text())['launch']
    assert launch['status']=='WINDOW24_REAL_PRODUCTION_CPU_SINGLE_DISPATCHED' and launch['GPU_submissions']==0
    gate=launch['halfway_not_before_unix' if a.mode=='halfway' else 'final_not_before_unix']
    if time.time()<gate:raise ValueError('Before original CPU check time; no SSH')
    code='L='+repr(launch)+'\nMODE='+repr(a.mode)+'\n'+CODE
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(code)],capture_output=True,timeout=150)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
    except (OSError,subprocess.TimeoutExpired,RuntimeError) as e:
        value=dict(status='WINDOW24_CPU_OBSERVATION_UNKNOWN_NOT_TERMINAL',launch=launch,
            error_type=type(e).__name__,error=str(e),original_task_terminal=False,no_relaunch_authority=True,
            GPU_submissions=0,ledger_written=False)
        with a.output.open('xb') as h:h.write(gzip.compress(json.dumps(value).encode()))
        raise
    with a.output.open('xb') as h:h.write(call.stdout)
    result=json.loads(gzip.decompress(call.stdout))
    print(json.dumps({k:result.get(k) for k in ('status','mode','observed_unix','process','error_lines')}))


if __name__=='__main__':main()
