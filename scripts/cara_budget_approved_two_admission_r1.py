"""Bind the approved original card and launch one bounded CPU asset admission."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time
from cara_two_card_transport_r1 import password

ROOT=Path(__file__).resolve().parents[1]
WORKER=r'''
import json,os,pathlib,resource,signal,sys,time,traceback
stage=pathlib.Path(sys.argv[1]);root=stage.parent.parent
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.cara_budget_prepare_r1 import admit
assert sys.stdin.readline().strip()=='PARENT_PUBLISHED_ORIGINAL_IDENTITY'
launch=json.loads((stage/'CPU-admission-launch.json').read_text());assert launch['identity']==bind_original_process(os.getpid())
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
resource.setrlimit(resource.RLIMIT_AS,(2*2**30,2*2**30));signal.alarm(1200)
state=dict(status='ORIGINAL_ADMISSION_CPU_RUNNING_NO_GPU',identity=launch['identity'],started_unix=time.time(),GPU_submissions=0,ledger_written=False)
atomic_json(stage/'CPU-admission-state.json',state)
try:
 result=admit(root,stage);state.update(status='ORIGINAL_ADMISSION_CPU_COMPLETE_NO_GPU',result=result)
except BaseException as error:
 state.update(status='ORIGINAL_ADMISSION_CPU_FAILED_NO_GPU',error_type=type(error).__name__,error=str(error));traceback.print_exc();raise
finally:
 state['ended_unix']=time.time();atomic_json(stage/'CPU-admission-state.json',state)
'''
REMOTE=r'''
import hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];stage=pathlib.Path(p['authority']['stage']);root=stage.parent.parent
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(stage/'registration.json')==p['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_prepare_r1 import bind_authority
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_fast_b36_dispatch_r2 import create
from wcomr.history104_storage_r2 import StorageGuard
if p['action']=='launch':
 assert not (stage/'CPU-admission-launch.json').exists(),'Capture the original admission; never replay'
 provision=root/'.sync/storage-reservations/budget-calibration-r1/provision.json';assert sha(provision)==p['provision_sha256']
 config=json.loads(provision.read_text())['storage_contract'];assert config==p['storage_contract']
 guard=StorageGuard(config);guard.check();assert list(guard.output.iterdir())==[]
 storage=stage/'history104-storage.json'
 if storage.exists():assert json.loads(storage.read_text())==config
 else:create(storage,config)
 authority=bind_authority(root,stage,p['authority'],p['proof'],p['quote'])
 worker=stage/'CPU-admission-worker.py';assert not worker.exists();worker.write_text(p['worker'])
 with (stage/'CPU-admission.log').open('x') as stream:
  child=subprocess.Popen([sys.executable,str(worker),str(stage)],stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   launch=dict(status='ORIGINAL_ADMISSION_CPU_LAUNCHED_NO_GPU',identity=bind_original_process(child.pid),worker_sha256=sha(worker),authority_sha256=sha(stage/'GPU-authorization.json'),registration_sha256=sha(stage/'registration.json'),started_unix=time.time(),wall_limit_seconds=1200,GPU_submissions=0,ledger_written=False)
   create(stage/'CPU-admission-launch.json',launch);child.stdin.write(b'PARENT_PUBLISHED_ORIGINAL_IDENTITY\n');child.stdin.flush()
  finally:child.stdin.close()
 print(json.dumps(launch))
else:
 assert p['action']=='capture'
 path=stage/'CPU-admission-launch.json'
 if not path.exists():
  print(json.dumps(dict(status='ORIGINAL_ADMISSION_LAUNCH_ABSENT',authority_present=(stage/'GPU-authorization.json').exists(),worker_present=(stage/'CPU-admission-worker.py').exists(),GPU_submissions=0)))
 else:
  launch=json.loads(path.read_text());state=stage/'CPU-admission-state.json'
  print(json.dumps(dict(status='ORIGINAL_ADMISSION_CAPTURE_NO_GPU',launch=launch,observation=observe_original_process(launch['identity']),worker_intact=sha(stage/'CPU-admission-worker.py')==launch['worker_sha256'],state=json.loads(state.read_text()) if state.exists() else None,log_tail=(stage/'CPU-admission.log').read_text(errors='replace')[-2500:],observed_unix=time.time(),GPU_submissions=0,ledger_written=False)))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['launch','capture']);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    read=lambda f:json.loads((ROOT/f).read_text())
    storage=read('reports/cara_budget_two_card_private_storage_accepted_r1_20261031.json')
    payload=dict(action=args.action,authority=read('plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14GPUH_USER_AUTHORIZATION_20261031.json'),proof=read('reports/cara_budget_two_card_whole_CPU_composed_r1_20261031.json'),quote=read('reports/cara_budget_two_card_whole_quote_r1_20261031.json'),registration_sha256=read('reports/cara_budget_approved_two_source_prepare_r1_20261031.json')['result']['registration_sha256'],storage_contract=storage['storage_contract'],provision_sha256=storage['provision_sha256'],worker=WORKER)
    secret=password();command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote("import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=REMOTE,arguments=payload)).encode())).decode()
    start=time.time();child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),'-o','BatchMode=yes','-o','ConnectTimeout=35','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate((secret+'\n'+encoded).encode(),timeout=110)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
    report=dict(started_unix=start,observed_unix=time.time(),action=args.action,exit_code=child.returncode,result=json.loads(out) if child.returncode==0 else None,stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),GPU_submissions=0,ledger_written=False,recover_original_only_if_unknown=True)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    result=report['result'] or {};print(json.dumps(dict(exit_code=child.returncode,status=result.get('status'),identity=result.get('identity'),state_status=(result.get('state') or {}).get('status'),error=(result.get('state') or {}).get('error'),stderr=report['stderr'][-1000:])))


if __name__=='__main__':main()
