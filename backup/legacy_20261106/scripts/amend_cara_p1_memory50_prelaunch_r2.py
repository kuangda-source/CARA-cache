"""Amend only the unstarted P1 source; archive original bytes before replacement."""
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
import sys
import time

from cara_two_card_transport_r1 import password

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import fcntl,hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];plan=p['plan'];stage=pathlib.Path(plan['stage']);root=stage.parents[1]
sha=lambda body:hashlib.sha256(body).hexdigest()
encoded=lambda value:(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def atomic(path,body):
 temp=path.with_name(path.name+'.memory50.tmp')
 with temp.open('wb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
 os.replace(temp,path)
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_source_lifecycle_p1_capture_r1 import inspect_container
from wcomr.cara_fast_b36_dispatch_r2 import assets_unchanged
from wcomr.cara_budget_dispatch_r1 import ASSETS
from wcomr.history104_storage_r2 import storage_for
from wcomr.cara_source_lifecycle_p1_identity_r1 import RUN_ID,STAGE_NAME
assert plan['run_id']==RUN_ID and stage==root/'.sync'/STAGE_NAME
assert plan['launch_id']=='a2b1dcf993774897902a5f0cc0858220'
for row in (p['original'],p['central']['snapshot']):assert 0<=time.time()-row['observed_unix']<=60
assert p['original']['stage']==str(stage) and p['original']['run_id']==RUN_ID
assert p['original']['dispatch_records']==[] and p['original']['container'] is None
assert p['central']['envelope'] is None and RUN_ID not in p['central']['snapshot']['ledger']['jobs']
changes=plan['replacements'];allowed={
 'src/wcomr/cara_source_lifecycle_p1_runner_binding_r1.py',
 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_CONTAINER_PROFILE_R1.json',
 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json',
 'tests/test_cara_source_lifecycle_p1_dispatch_r1.py',
 'registration.json','execution-CPU-proof.json','whole-quote.json','GPU-authorization.json'}
assert set(changes)==allowed
with (stage/'dispatch-control.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 forbidden=('GPU-intent.json','GPU-dispatch.json','GPU-launch.json','guardian-intent.json',
  'guardian.json','supervisor-start.json','runner-start.json','central-reservation.json')
 assert not any((stage/n).exists() for n in forbidden),'Existing original run: recover only'
 assert inspect_container(stage.name+'-gpu') is None,'Existing original container'
 archive=stage/'prelaunch-memory50-r2';archive.mkdir(exist_ok=True,mode=0o700)
 marker=archive/'intent.json';complete=archive/'complete.json'
 expected=dict(plan_sha256=sha(encoded(plan)),launch_id=plan['launch_id'],source_revision=plan['source_revision'])
 if marker.exists():assert json.loads(marker.read_bytes())==expected
 newreg=json.loads(changes['registration.json']['new_raw_utf8'])
 assert sha(changes['registration.json']['new_raw_utf8'].encode())==plan['new_registration_sha256']
 for name,h in newreg['payload_sha256'].items():
  current=sha((stage/name).read_bytes())
  assert current in ({h,changes[name]['old_sha256']} if name in changes else {h}),'Unexpected source bytes: '+name
 for name,row in changes.items():
  assert sha((stage/name).read_bytes()) in (row['old_sha256'],sha(row['new_raw_utf8'].encode()))
 storage=storage_for(stage);storage.check();assert not list(storage.output.iterdir())
 with storage.journal.path.open('rb') as stream:
  assert all(block==bytes(len(block)) for block in iter(lambda:stream.read(2**20),b''))
 cache=json.loads((stage/'fresh-admission.json').read_bytes())
 assert cache['registration_sha256'] in (plan['base_registration_sha256'],plan['new_registration_sha256'])
 assert cache['authorization_sha256'] in (changes['GPU-authorization.json']['old_sha256'],sha(changes['GPU-authorization.json']['new_raw_utf8'].encode()))
 assert cache['asset_spec_sha256']==sha((stage/ASSETS).read_bytes())
 assets_unchanged(root,json.loads((stage/ASSETS).read_bytes()),cache['assets'])
 if not marker.exists():
  for name,row in changes.items():
   body=(stage/name).read_bytes();assert sha(body)==row['old_sha256']
   target=archive/'original'/name;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():assert target.read_bytes()==body
   else:target.write_bytes(body)
  original_cache=archive/'original/fresh-admission.json'
  if original_cache.exists():assert original_cache.read_bytes()==(stage/'fresh-admission.json').read_bytes()
  else:original_cache.write_bytes((stage/'fresh-admission.json').read_bytes())
  atomic(marker,encoded(expected))
 for name,row in changes.items():assert sha((archive/'original'/name).read_bytes())==row['old_sha256']
 if not complete.exists():
  order=sorted(allowed-{'registration.json','GPU-authorization.json'})
  for name in order:atomic(stage/name,changes[name]['new_raw_utf8'].encode())
  rebound=dict(registration_sha256=plan['new_registration_sha256'],
   authorization_sha256=sha(changes['GPU-authorization.json']['new_raw_utf8'].encode()),
   asset_spec_sha256=cache['asset_spec_sha256'],assets=cache['assets'],
   source_rebound_memory50_requires_fresh_admission=True)
  atomic(stage/'fresh-admission.json',encoded(rebound))
  for name in ('registration.json','GPU-authorization.json'):atomic(stage/name,changes[name]['new_raw_utf8'].encode())
 for name,row in changes.items():assert (stage/name).read_bytes()==row['new_raw_utf8'].encode()
 check="import sys;sys.dont_write_bytecode=True;sys.path[:0]="+repr([str(stage/'src'),str(stage/'scripts')])+";from wcomr.cara_source_lifecycle_p1_dispatch_r1 import ready_inputs;r=ready_inputs("+repr(str(root))+","+repr(str(stage))+");assert r[3]['hosts']['two_card']['minimum_MemAvailable_GiB']==50;print('MEMORY50_BOUND_NO_DISPATCH')"
 checked=subprocess.check_output([sys.executable,'-c',check],text=True,timeout=50)
 assert checked.strip()=='MEMORY50_BOUND_NO_DISPATCH'
 result=dict(status='P1_UNSTARTED_MEMORY50_SOURCE_AMENDED_NO_GPU',stage=str(stage),
  run_id=RUN_ID,launch_id=plan['launch_id'],source_revision=plan['source_revision'],
  registration_sha256=plan['new_registration_sha256'],archive=str(archive/'original'),
  original_sha256={n:r['old_sha256'] for n,r in changes.items()},
  amended_sha256={n:sha(r['new_raw_utf8'].encode()) for n,r in changes.items()},
  initial_MemAvailable_GiB=50,GPU_container_GiB=40,CPU_container_GiB=8,
  per_query_fresh_GiB=12,fresh_admission_required=True,scientific_scope_changed=False,
  GPU_submissions=0,ledger_written=False,completed_unix=time.time())
 if complete.exists():
  saved=json.loads(complete.read_bytes())
  assert all(saved[k]==v for k,v in result.items() if k!='completed_unix');result=saved
 else:atomic(complete,encoded(result))
print(json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--original-status', type=Path, required=True)
    parser.add_argument('--central-status', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    plan = json.loads(args.plan.read_bytes())
    original = json.loads(args.original_status.read_bytes())
    central = json.loads(args.central_status.read_bytes())
    assert original['exit_code'] == central['exit_code'] == 0
    assert original['result']['recovery'] is None and central['result']['ledger_written'] is False
    assert plan['unstarted_and_unreserved_required'] is True
    payload = dict(plan=plan,original=original['result']['original'],central=central['result'])
    for row in (payload['original'],payload['central']['snapshot']):
        assert 0 <= time.time()-row['observed_unix'] <= 60
    cpu = json.loads((ROOT/'reports/cara_v1_P1_memory50_Linux_CPU_r1_20261102.json').read_bytes())
    assert cpu['result']['terminal']['exit_code'] == 0
    assert cpu['result']['proof']['tests_run'] == 9 and cpu['result']['proof']['failures'] == 0
    secret = password()
    private = ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'
    assert private.stat().st_mode & 0o077 == 0
    body = base64.b64encode(gzip.compress(json.dumps(dict(code=REMOTE,arguments=payload)).encode())).decode()
    code = "import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])"
    interpreter = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command = "sudo -S -p '' -u gaokuangda -g docker "+shlex.quote(interpreter)+' -c '+shlex.quote(code)
    started = time.time()
    child = subprocess.Popen(['ssh','-C','-F',str(private),'-o','BatchMode=yes','-o','ConnectTimeout=30',
        '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out,err = child.communicate((secret+'\n'+body).encode(),timeout=150)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL)
        out,err = child.communicate()
    result = json.loads(out) if child.returncode == 0 else None
    receipt = dict(exit_code=child.returncode,result=result,started_unix=started,observed_unix=time.time(),
        stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),
        plan_ref=str(args.plan),plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),
        unknown_requires_same_amendment_recovery=True)
    with args.output.open('x') as stream:
        json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,status=(result or {}).get('status'),stderr=receipt['stderr'][-1500:])))


if __name__ == '__main__':
    main()
