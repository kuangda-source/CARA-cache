"""Scoped original-card refresh, central transaction, dispatch and recovery.

Only reserve/settle actions may write the user's original central ledger.
Unknown dispatch responses must use status, never another submission.
"""
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
TWO=r'''
import hashlib,json,os,pathlib,sys,time
p=packet['arguments'];stage=pathlib.Path(p['authority']['stage']);root=stage.parent.parent
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(stage/'registration.json')==p['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==p['authority']['source_revision']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_budget_prepare_r1 import observe_original,bind_reservation
from wcomr.cara_budget_dispatch_r1 import ready_inputs,fresh_resources,dispatch,recover
from wcomr.gpu_budget_pool_v2 import atomic_json
if p['action']=='refresh':
 assert recover(stage) is None,'Original dispatch exists: recover only'
 card,registration,authority,profile,limits=ready_inputs(root,stage)
 admission=json.loads((stage/'fresh-admission.json').read_text())
 assert admission['status']=='CALIBRATION_COMPLETE_FRESH_ADMISSION_NO_GPU'
 storage,resources=fresh_resources(root,stage,authority,profile)
 admission.update(resources=resources,observed_unix=time.time());atomic_json(stage/'fresh-admission.json',admission)
 result=dict(status='ORIGINAL_PRELAUNCH_ADMISSION_REFRESHED_NO_GPU',admission=admission,original=observe_original(root,'two_card'),GPU_submissions=0,ledger_written=False)
elif p['action']=='dispatch':
 original=recover(stage)
 if original is not None:result=original
 else:
  bind_reservation(root,stage,p['central']['envelope'],p['central']['snapshot'])
  result=dispatch(root,stage,p['central']['snapshot'],p['sudo_password'])
else:
 assert p['action']=='status'
 result=dict(status='ORIGINAL_CARD_OPERATIONAL_CAPTURE',recovery=recover(stage),GPU_submissions=0,ledger_written=False)
 launch=stage/'GPU-launch.json'
 if launch.exists():
  from wcomr.cara_budget_lifecycle_capture_r1 import capture_lifecycle
  result['launch_sha256']=sha(launch);result['lifecycle']=capture_lifecycle(root,stage,result['launch_sha256'])
  from wcomr.cara_fast_b36_dispatch_r2 import selected_gpu
  result['selected_gpu']=selected_gpu(p['authority']['gpu_uuid'])
  for name in ('guardian.json','supervisor-start.json','runner-start.json','billing.json'):
   path=stage/name
   if path.exists():result[name]=json.loads(path.read_text())
 result['host_guardian_log_tail']=(stage/'host-guardian.log').read_text(errors='replace')[-2000:] if (stage/'host-guardian.log').exists() else None
print(json.dumps(result))
'''
CENTRAL=r'''
import base64,hashlib,io,json,os,pathlib,subprocess,sys,tarfile,tempfile,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
raw=base64.b64decode(p['archive']);assert hashlib.sha256(raw).hexdigest()==p['archive_sha256']
with tempfile.TemporaryDirectory(prefix='single14-central-operator-') as temporary:
 source=pathlib.Path(temporary);expected=p['plan']['overlay_sha256'];found=set()
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
  for member in archive:
   name=member.name;relative=pathlib.Path(name)
   assert member.isfile() and name in expected and name not in found and not relative.is_absolute() and '..' not in relative.parts
   body=archive.extractfile(member).read();assert hashlib.sha256(body).hexdigest()==expected[name]
   target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body);found.add(name)
 assert found==set(expected)
 sys.dont_write_bytecode=True;sys.path[:0]=[str(source/'src'),str(source/'scripts')]
 from wcomr.cara_budget_central_r1 import reserve,settle,Pool,STAGES,RUN
 from wcomr.cara_budget_lifecycle_capture_r1 import inspect_container
 stage=root/'.sync'/STAGES['four_card']
 original=dict(host='four_card',stage=str(stage),run_id=RUN,stage_exists=stage.exists(),dispatch_records=[n for n in ('GPU-intent.json','GPU-dispatch.json','GPU-launch.json','guardian-intent.json') if (stage/n).exists()],container=inspect_container(stage.name+'-gpu'),observation_complete=True,observed_unix=time.time())
 pool=Pool(root);receipt=root/'reports'/(RUN+'.central-reservation.json')
 if p['action']=='reserve':
  assert p['transaction_authority']['launch_id']==p['refresh']['admission']['authorization']['launch_id']
  envelope=reserve(root,p['refresh']['admission'],dict(two_card=p['refresh']['original'],four_card=original))
 elif p['action']=='settle':
  assert p['transaction_authority']['launch_id']==p['expected_launch_id']
  envelope=settle(root,p['capture'],p['expected_launch_sha256'])
 else:
  assert p['action']=='central-status'
  envelope=json.loads(receipt.read_text()) if receipt.exists() else None
 snapshot=dict(central_ledger_host='four_card',ledger=pool.read(),observed_unix=time.time())
 print(json.dumps(dict(status='ORIGINAL_CENTRAL_CARD_TRANSACTION_OR_RECOVERY',action=p['action'],envelope=envelope,snapshot=snapshot,original=original,GPU_submissions=0,ledger_written=p['action'] in ('reserve','settle'))))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['refresh','reserve','dispatch','status','central-status','settle'])
    parser.add_argument('--input',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    read=lambda name:json.loads((ROOT/name).read_text())
    authority=read('plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14GPUH_EXECUTION_BINDING_R2_20261031.json')
    transaction=read('plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14_CENTRAL_TRANSACTION_AUTHORIZATION_20261031.json')
    assert transaction['launch_id']==authority['launch_id'] and transaction['hard_GPUh']==14
    central=args.action in ('reserve','central-status','settle')
    p=dict(action=args.action,authority=authority,transaction_authority=transaction)
    if central:
        proof=read('reports/cara_budget_two_card_whole_CPU_composed_r2_20261031.json');package=ROOT/proof['package_ref']
        raw=(package/'source.tar.gz').read_bytes();assert hashlib.sha256(raw).hexdigest()==proof['package_archive_sha256']
        p.update(archive=base64.b64encode(raw).decode(),archive_sha256=proof['package_archive_sha256'],plan=json.loads((package/'source-plan.json').read_text()))
    else:p['registration_sha256']=read('reports/cara_budget_approved_two_source_prepare_r2_20261031.json')['result']['registration_sha256']
    if args.action in ('reserve','dispatch','settle'):
        assert args.input is not None
        supplied=json.loads(args.input.read_text());assert supplied['exit_code']==0
        if args.action=='reserve':p['refresh']=supplied['result']
        elif args.action=='dispatch':p['central']=supplied['result']
        else:
            original=supplied['result'];p.update(capture=original['lifecycle'],expected_launch_sha256=original['launch_sha256'],expected_launch_id=authority['launch_id'])
    secret=None if central else password()
    if args.action=='dispatch':p['sudo_password']=secret
    remote=CENTRAL if central else TWO
    code="import io,sys,json,gzip,base64\nsaved=sys.stdout;sys.stdout=io.StringIO()\nexec("+repr(remote)+")\nraw=sys.stdout.getvalue().encode();sys.stdout=saved\nprint(json.dumps(dict(gzip_base64=base64.b64encode(gzip.compress(raw)).decode(),sha256=hashlib.sha256(raw).hexdigest())))\n"
    encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=code,arguments=p)).encode())).decode()
    interpreter='python3' if central else '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=shlex.quote(interpreter)+' -c '+shlex.quote("import sys,json,gzip,base64,hashlib;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    if not central:command="sudo -S -p '' -u gaokuangda -g docker "+command
    started=time.time();child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),'-o','BatchMode=yes','-o','ConnectTimeout=25','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','four_card_lan' if central else 'two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate(((secret+'\n' if secret else '')+encoded).encode(),timeout=110)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
    result=None
    if child.returncode==0:
        wrapped=json.loads(out);decoded=gzip.decompress(base64.b64decode(wrapped['gzip_base64']));assert hashlib.sha256(decoded).hexdigest()==wrapped['sha256'];result=json.loads(decoded)
    stderr=err.decode(errors='replace')
    if secret:stderr=stderr.replace(secret,'[REDACTED]')
    report=dict(action=args.action,started_unix=started,observed_unix=time.time(),exit_code=child.returncode,result=result,stderr=stderr,transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_code_sha256=hashlib.sha256(remote.encode()).hexdigest(),launch_id=authority['launch_id'],source_revision=authority['source_revision'],unknown_requires_original_recovery=True)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(action=args.action,exit_code=child.returncode,status=(result or {}).get('status'),stderr=stderr[-1500:])))


if __name__=='__main__':main()
