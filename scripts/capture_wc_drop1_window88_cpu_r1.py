#!/usr/bin/env python3
"""Once-after-gate CPU observation and offline complete88 numerical acceptance."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

CODE = r'''
import gzip,hashlib,json,pathlib,sys,time
stage=pathlib.Path(L['stage']);root=stage.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==L['source_revision']
try:
 p=pathlib.Path('/proc')/str(L['pid']);f=(p/'stat').read_text().split(') ',1)[1].split()
 proc=dict(pid=L['pid'],state=f[0],start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode().strip())
except FileNotFoundError:proc=dict(pid=L['pid'],state=None,start_ticks=None,command=None)
live=proc['start_ticks']==L['start_ticks'] and proc['state'] not in (None,'Z','X')
v=dict(status='ORIGINAL_WINDOW88_CPU_ONCE_CAPTURE',mode=MODE,observed_unix=time.time(),launch=L,process=proc,original_process_alive=live,registration_sha256=sha(stage/'registration.json'),GPU_submissions=0,ledger_written=False)
if MODE=='halfway':
 v.update(registered_CPU_paths=88,numerical_result_exists=(stage/'window88-numerical-CPU-result.json').is_file(),worker_result_exists=(stage/'CPU-window88-result.json').is_file(),scientific_results_read=False)
else:
 v.update(registration=reg,payload_verified={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()},runtime_verified={n:sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()},files={})
 if not live:
  for n in ('CPU-window88-result.json','window88-numerical-CPU-result.json','window88-numerical-CPU-result.failure.json'):
   path=stage/n;r=dict(exists=path.is_file())
   if path.is_file():
    raw=path.read_bytes();r['sha256']=hashlib.sha256(raw).hexdigest()
    try:r['data']=json.loads(raw)
    except Exception as e:r.update(parse_error=str(e),raw_hex=raw.hex())
   v['files'][n]=r
path=stage/'CPU-window88.log'
if path.is_file():
 with path.open('rb') as h:h.seek(0,2);size=h.tell();h.seek(max(0,size-24000));log=h.read().decode(errors='replace')
 if MODE=='halfway':v['error_lines']=[x for x in log.splitlines() if any(t in x for t in ('Traceback','RuntimeError','AssertionError','MemoryError','No space left'))][-12:]
 elif not live:v['original_log_tail']=log
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''


def gate(launch, mode, now):
    if (launch['status']!='CORRECTION_WINDOW_FULL88_NUMERICAL_CPU_SINGLE_DISPATCHED'
            or launch['registered_CPU_paths']!=88 or launch['GPU_submissions']
            or launch['ledger_written'] or launch['production_CPU_accepted']):
        raise ValueError('Original complete88 CPU-only handle required')
    if now < launch['halfway_not_before_unix' if mode=='halfway' else 'final_not_before_unix']:
        raise ValueError('Before original CPU check time; no SSH')


def accept(value):
    launch=value['launch'];gate(launch,'terminal',value['observed_unix'])
    if value['status']!='ORIGINAL_WINDOW88_CPU_ONCE_CAPTURE' or value['mode']!='terminal':
        raise ValueError('Original terminal capture required')
    if value['original_process_alive']:
        return dict(status='WINDOW88_CPU_STILL_RUNNING_REESTIMATE_ONCE',numerical_CPU_accepted=False,GPU_submissions=0)
    reg=value['registration']
    if (value['registration_sha256']!=launch['registration_sha256']
            or reg['source_revision']!=launch['source_revision']
            or not value['payload_verified'] or not all(value['payload_verified'].values())
            or set(value['payload_verified'])!=set(reg['payload_sha256'])
            or not value['runtime_verified'] or not all(value['runtime_verified'].values())
            or set(value['runtime_verified'])!=set(reg['runtime_source_sha256'])
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Complete immutable CPU source/runtime identity must match')
    bundle=value['files']['CPU-window88-result.json'].get('data')
    numeric=value['files']['window88-numerical-CPU-result.json'].get('data')
    if bundle is None or numeric is None or bundle.get('exit_code')!=0:
        return dict(status='WINDOW88_CPU_ORIGINAL_FAILURE_RETAINED',numerical_CPU_accepted=False,registered_CPU_paths=88,production_CPU_accepted=False,GPU_submissions=0)
    if (bundle['status']!='CPU_WINDOW88_COMPLETE_NOT_PRODUCTION_OR_GPU'
            or bundle['source_revision']!=launch['source_revision']
            or len(bundle['commands'])!=3 or any(c['exit_code']!=0 for c in bundle['commands'])
            or bundle['production_CPU_accepted'] or bundle['GPU_submissions'] or bundle['ledger_written']
            or numeric['status']!='CORRECTION_WINDOW_COMPLETE88_TWO_FLOW_NUMERICAL_CPU_PASS_NOT_GPU'
            or numeric['actual_CPU_paths']!=88 or len(numeric['checks'])!=2
            or numeric['CUDA_initialized'] or numeric['GPU_submissions']
            or numeric['payload_sha256']!=reg['payload_sha256']
            or numeric['unchanged_CPU_import_guard_template_sha256']!='cdd6c1099227a195070f533136deab568b45b5097c3e5c17ef1368b99c70ec39'
            or not numeric['scope_replacements_reversibly_checked']):
        raise ValueError('All88 numerical paths, three CPU commands and unchanged guards required')
    if {c['flow'] for c in numeric['checks']} != {False, True}:
        raise ValueError('Both original sampling flows required')
    for flow in numeric['checks']:
        if (flow['status']!='PASS' or flow['complete_CPU_paths']!=44
                or flow['new_complete_paths']!=32 or flow['old_control_paths']!=12
                or len(flow['checks'])!=16 or not flow['all36_audit_guided_controls']
                or not flow['common_A1_A3_first21_guided_equal'] or not flow['ordinary_initial_state_restored']
                or not flow['CPU_video_payload_is_not_real_93frame_video']):
            raise ValueError('Each original flow must contain all44 complete numerical paths')
        seen=set()
        for row in flow['checks']:
            key=(row['scene'],row['method'])
            if key in seen:raise ValueError('Duplicate CPU scene/method')
            seen.add(key);method=row['method']
            if (method not in ('S26-C','S25-C','S25-A1','S25-A3')
                    or row['DD']!=(26 if method=='S26-C' else 25)
                    or row['A']!={'S26-C':0,'S25-C':0,'S25-A1':1,'S25-A3':3}[method]
                    or row['C']!=36-row['DD']-row['A']
                    or not row['all36_actual_readout_and_paid_source_checks']
                    or not row['audit_lean_endpoint_actions_history_CPU_video_payload_equal']
                    or row['original_all36_guided_control']!=(method!='S25-A3')):
                raise ValueError('Exact masks/readout/source/old-arm control required')
        if len({s for s,m in seen})!=4:raise ValueError('All four original CPU scenes required')
    return dict(status='CORRECTION_WINDOW_FULL88_NUMERICAL_CPU_INDEPENDENTLY_ACCEPTED_NOT_PRODUCTION_OR_GPU',numerical_CPU_accepted=True,source_revision=launch['source_revision'],registered_CPU_paths=88,new_paths=64,original_control_paths=24,CPU_wall_seconds=bundle['wall_seconds'],all36_guided_old_arms_and_audit_lean_history_checks=True,production_CPU_accepted=False,GPU_submissions=0,new_quality_scores=0,ledger_written=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['halfway','terminal','accept'],required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Read existing receipt offline; do not query twice')
    if a.mode=='accept':
        raw=a.capture.read_bytes();value=accept(json.loads(gzip.decompress(raw)))
        value.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
        a.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');print(json.dumps(value));return
    launch=json.loads(a.launch_ref.read_text())['launch'];gate(launch,a.mode,time.time())
    code='L='+repr(launch)+'\nMODE='+repr(a.mode)+'\n'+CODE
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c '+shlex.quote(code)],capture_output=True,timeout=120)
    if call.returncode:raise RuntimeError(call.stderr.decode())
    value=json.loads(gzip.decompress(call.stdout));a.output.write_bytes(call.stdout)
    print(json.dumps({k:value.get(k) for k in ('mode','observed_unix','original_process_alive','error_lines')}))


if __name__=='__main__':main()
