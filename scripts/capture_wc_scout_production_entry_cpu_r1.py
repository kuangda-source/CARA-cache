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
v=dict(status='SCOUT_ENTRY_CPU_ORIGINAL_ONCE_CAPTURE',mode=MODE,launch=L,observed_unix=time.time(),
 process=process_identity(L['identity']['pid']),GPU_submissions=0,ledger_written=False)
names=dict(bundle='scout-entry-CPU-bundle.json',proof='scout-entry-production-CPU-result.json',
 config='configs/wc_scout_'+L['kind'].lower()+'_production_entry_r1_20261018.json')
if MODE=='halfway':v['result_files_present']={k:(stage/n).exists() for k,n in names.items()}
else:
 v.update(registration=reg,registration_sha256=sha(stage/'registration.json'),
  payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},
  runtime_actual_sha256={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']},files={})
 for k,n in names.items():
  p=stage/n;info=dict(exists=p.exists())
  if p.exists():info.update(sha256=sha(p),data=json.loads(p.read_text()))
  v['files'][k]=info
p=stage/'scout-entry-CPU.log'
if p.exists():
 with p.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-65536));tail=f.read().decode(errors='replace')
 if MODE=='halfway':v['error_lines']=[s for s in tail.splitlines() if any(t in s for t in ('Traceback','AssertionError','RuntimeError','MemoryError'))][-12:]
 else:v['original_log_tail']=tail
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def accept(v):
    L=v['launch'];assert v['mode']=='terminal' and v['observed_unix']>=L['final_not_before_unix']
    p=v['process'];assert p['state'] in (None,'Z','X') or p['start_ticks']!=L['identity']['start_ticks']
    reg=v['registration'];assert reg['source_revision']==L['source_revision']
    assert v['registration_sha256']==L['registration_sha256']
    assert v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256']
    assert reg['CPU_scope']=='SCOUT_REAL_PRODUCTION_ENTRY_NOT_GPU_LIFECYCLE' and reg['scout_kind']==L['kind']
    if not all(v['files'][k].get('data') for k in ('config','proof','bundle')):
        return dict(status='SCOUT_REAL_ENTRY_CPU_MISSING_RESULTS_RETAINED',production_entry_CPU_accepted=False,GPU_dispatch_ready=False)
    c,proof,bundle=(v['files'][k]['data'] for k in ('config','proof','bundle'))
    if bundle.get('exit_code')!=0:
        return dict(status='SCOUT_REAL_ENTRY_CPU_FAILURE_RETAINED',production_entry_CPU_accepted=False,GPU_dispatch_ready=False)
    os.environ['WC_SCOUT_KIND']=L['kind'];sys.path.insert(0,str(ROOT/'src'))
    from wcomr import scout_production_entry_r1 as entry
    entry.validate_contract(c)
    assert v['files']['config']['sha256']==reg['payload_sha256'][entry.CONFIG]
    assert bundle['status']=='SCOUT_REAL_PRODUCTION_ENTRY_CPU_BUNDLE_PASS_NOT_GPU_LIFECYCLE'
    assert bundle['source_revision']==reg['source_revision'] and bundle['kind']==L['kind']
    assert bundle['registration_sha256']==L['registration_sha256'] and bundle['config_sha256']==v['files']['config']['sha256']
    expected=[[L['command'][0],'-m','unittest','discover','-s',L['stage']+'/tests','-p','test_scout_production_entry_r1.py','-v'],
        [L['command'][0],L['stage']+'/scripts/run_wc_scout_production_entry_r1.py','--project',L['project'],'--stage',L['stage'],'--cpu-check']]
    assert [x['command'] for x in bundle['commands']]==expected and all(x['exit_code']==0 for x in bundle['commands'])
    assert bundle['proof_sha256']==v['files']['proof']['sha256']
    assert proof['status']==entry.PRODUCTION_CPU_STATUS and proof['exit_code']==0
    assert proof['source_revision']==reg['source_revision'] and proof['config_sha256']==bundle['config_sha256']
    assert proof['registration_sha256']==L['registration_sha256'] and proof['scope_counts']==entry.COUNTS
    assert proof['numerical_CPU_capture_sha256']==c['references']['numeric_capture']['sha256']
    assert proof['matrix']==entry.matrix([r['name'] for r in c['requests']]) and proof['input_evidence']
    assert set(proof['mutations_refused'])=={'scope_counts','methods','A_method','P_enabled','online_teachers','training',
        'autonomy_exclusive_upper_GPUh','cumulative_cap_GPUh','billed_limit_GPUh','timing_claim','plans'}
    assert proof['CUDA_initialized'] is False and proof['GPU_submissions']==0 and proof['ledger_written'] is False
    return dict(status='SCOUT_REAL_PRODUCTION_ENTRY_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU_LIFECYCLE',kind=L['kind'],
        production_entry_CPU_accepted=True,GPU_dispatch_ready=False,GPU_lifecycle_accepted=False,
        source_revision=reg['source_revision'],registration_sha256=L['registration_sha256'],
        config_sha256=bundle['config_sha256'],production_entry_CPU_sha256=v['files']['proof']['sha256'],
        CPU_commands=2,scope_counts=entry.COUNTS,CPU_wall_seconds=bundle['CPU_wall_seconds'],
        actual_video_or_quality_result=False,GPU_submissions=0,ledger_written=False)


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
        value=dict(status='SCOUT_ENTRY_CPU_OBSERVATION_UNKNOWN_NOT_TERMINAL',error_type=type(e).__name__,error=str(e),GPU_submissions=0)
        raw=gzip.compress(json.dumps(value).encode())
    with a.output.open('xb') as f:f.write(raw)
    print(json.dumps({k:value.get(k) for k in ('status','mode','process','error_lines')}))


if __name__=='__main__':main()
