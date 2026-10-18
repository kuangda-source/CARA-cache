#!/usr/bin/env python3
"""One midpoint/final CPU snapshot; acceptance after capture is purely offline."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CODE=r'''
import gzip,hashlib,json,pathlib,sys,time
sys.dont_write_bytecode=True
stage=pathlib.Path(L['stage']);root=pathlib.Path(L['project'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
v=dict(status='SCOUT248_ORIGINAL_CPU_ONCE_CAPTURE',mode=MODE,launch=L,observed_unix=time.time(),
 process=process_identity(L['identity']['pid']),GPU_submissions=0,ledger_written=False)
if MODE=='halfway':
 v['worker_source_SHA_accepted']=sha(stage/'scripts/wc_scout_numeric248_cpu_r1.py')==reg['payload_sha256']['scripts/wc_scout_numeric248_cpu_r1.py']
 v['result_files_present']={k:(stage/n).exists() for k,n in [('CAL12','scout-CAL12-sampling-CPU-result.json'),('BANK24','scout-BANK24-sampling-CPU-result.json'),('bundle','CPU-scout248-result.json')]}
else:
 v.update(registration=reg,registration_sha256=sha(stage/'registration.json'),
  payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},
  runtime_actual_sha256={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']},files={})
 for key,name in [('CAL12','scout-CAL12-sampling-CPU-result.json'),('BANK24','scout-BANK24-sampling-CPU-result.json'),('bundle','CPU-scout248-result.json')]:
  p=stage/name;info=dict(exists=p.exists())
  if p.exists():info.update(sha256=sha(p),data=json.loads(p.read_text()))
  v['files'][key]=info
log=stage/'CPU-scout248.log'
if log.exists():
 with log.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-65536));s=f.read().decode(errors='replace')
 if MODE=='halfway':v['error_lines']=[q for q in s.splitlines() if any(t in q for t in ['Traceback','RuntimeError','AssertionError','MemoryError'])][-10:]
 else:v['original_log_tail']=s
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def accept(v):
    assert v['mode']=='terminal' and v['observed_unix']>=v['launch']['final_not_before_unix']
    p=v['process'];ident=v['launch']['identity']
    assert p['state'] in (None,'Z','X') or p.get('start_ticks')!=ident['start_ticks']
    reg=v['registration'];assert v['registration_sha256']==v['launch']['registration_sha256']
    assert reg['source_revision']==v['launch']['source_revision'] and reg['CPU_scope']=='SCOUT_COMPLETE248_NUMERICAL_NOT_PRODUCTION'
    assert v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256']
    bundle=v['files']['bundle']['data'];assert bundle['status']=='SCOUT_COMPLETE248_NUMERICAL_CPU_PASS_NOT_PRODUCTION' and bundle['exit_code']==0
    assert len(bundle['commands'])==2 and all(x['exit_code']==0 for x in bundle['commands'])
    for kind,count in [('CAL12',80),('BANK24',168)]:
        q=v['files'][kind];r=q['data'];assert q['sha256']==bundle['result_sha256'][kind]
        assert r['status']=='SCOUT_'+kind+'_COMPLETE_SAMPLING_CPU_PASS_NOT_GPU' and r['actual_CPU_paths']==count
        assert r['payload_sha256']==reg['payload_sha256'] and r['GPU_submissions']==0 and r['CUDA_initialized'] is False
        assert {a['flow'] for a in r['checks']}=={False,True}
        assert all(a['complete_CPU_paths']==count//2 and a['full36_output_and_owner_controls'] for a in r['checks'])
        if reg.get('guard_refusal_controls_required')==10:
            methods={'G01_LATE_A','VARIATION26_C'} if kind=='CAL12' else {'D21','A21','NATIVE35'}
            for flow in r['checks']:
                guards=flow['guard_refusal_controls']
                assert {g['method'] for g in guards}==methods and len(guards)==len(methods)
                assert all(g['declared_guard_refusal_retained'] and g['zero_updates'] and g['owner_released'] for g in guards)
    return dict(status='SCOUT_COMPLETE248_NUMERICAL_CPU_INDEPENDENTLY_ACCEPTED_NOT_PRODUCTION',numerical_CPU_accepted=True,
        source_revision=reg['source_revision'],registration_sha256=v['registration_sha256'],actual_CPU_paths=248,
        CAL12_paths=80,BANK24_paths=168,all36_observer_OFF_ON_controls=True,production_CPU_accepted=False,
        guard_refusal_controls=reg.get('guard_refusal_controls_required',0),
        CPU_wall_seconds=bundle['wall_seconds'],GPU_submissions=0,new_GPUh=0,ledger_written=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['halfway','terminal','accept'],required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--capture',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    if a.mode=='accept':
        raw=a.capture.read_bytes();value=accept(json.loads(gzip.decompress(raw)))
        value.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
        with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
        print(json.dumps(value));return
    launch=json.loads(a.launch_ref.read_text())['launch'];assert launch is not None
    assert time.time()>=launch['halfway_not_before_unix' if a.mode=='halfway' else 'final_not_before_unix'],'Before original CPU check time; no SSH'
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
        PY+' -c '+shlex.quote('L='+repr(launch)+'\nMODE='+repr(a.mode)+'\n'+CODE)],capture_output=True,timeout=150)
    if call.returncode:
        value=dict(status='SCOUT248_CPU_OBSERVATION_UNKNOWN_NOT_TERMINAL',stderr=call.stderr.decode(),GPU_submissions=0)
        raw=gzip.compress(json.dumps(value).encode())
    else:raw=call.stdout;value=json.loads(gzip.decompress(raw))
    with a.output.open('xb') as f:f.write(raw)
    print(json.dumps({k:value.get(k) for k in ['status','mode','process','error_lines']}));raise SystemExit(call.returncode)


if __name__=='__main__':main()
