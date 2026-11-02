"""Scoped P1 RPC; four-card is inaccessible without this exact new exception."""
import argparse
import base64
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tarfile
import time

from cara_two_card_transport_r1 import password

ROOT=Path(__file__).resolve().parents[1]
PROJECT='/data20t/gaokuangda/worldcache_workspace'
AUTH='plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SINGLE_CARD_AUTHORIZATION_R1.json'
PROOF='reports/cara_v1_P1_whole_CPU_accepted_r1_20261102.json'
PREPARED='reports/cara_v1_P1_source_preparation_r1_20261102.json'
TWO=r'''
import hashlib,json,os,pathlib,sys,time
p=packet['arguments'];auth=p['authority'];stage=pathlib.Path(auth['stage']);root=stage.parents[1]
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
assert sha(stage/'registration.json')==p['registration_sha256']
reg=json.loads((stage/'registration.json').read_bytes())
assert reg['source_revision']==auth['source_revision'] and all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_source_lifecycle_p1_dispatch_r1 import ready_inputs,fresh_resources,dispatch,recover,central_binding,ASSETS
from wcomr.cara_source_lifecycle_p1_capture_r1 import inspect_container,capture_lifecycle
from wcomr.cara_source_lifecycle_p1_central_r1 import validate_authority
from wcomr.cara_source_lifecycle_p1_identity_r1 import RUN_ID,STAGE_NAME
from wcomr.cara_fast_b36_dispatch_r2 import create,assets_check,selected_gpu
from wcomr.gpu_budget_pool_v2 import atomic_json
validate_authority(auth,root)
def original():
 return dict(host='two_card',stage=str(stage),run_id=RUN_ID,
  dispatch_records=[n for n in ('GPU-intent.json','GPU-dispatch.json','GPU-launch.json','guardian-intent.json') if (stage/n).exists()],
  container=inspect_container(stage.name+'-gpu'),observation_complete=True,observed_unix=time.time())
action=p['action']
if action=='bind':
 assert recover(stage) is None and original()['container'] is None
 for name,key in (('execution-CPU-proof.json','CPU_proof_sha256'),('whole-quote.json','quote_sha256'),('internal-score-environment.json','FIT_environment_sha256')):
  assert sha(stage/name)==auth[key]
 path=stage/'GPU-authorization.json'
 if path.exists():assert json.loads(path.read_bytes())==auth
 else:create(path,auth)
 ready_inputs(root,stage)
 result=dict(status='P1_ORIGINAL_AUTHORITY_BOUND_NO_GPU',authorization_sha256=sha(path),original=original())
elif action in ('admit','refresh'):
 assert recover(stage) is None
 card,registration,authority,profile,quote=ready_inputs(root,stage);assert authority==auth
 if action=='admit':
  admission=dict(registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'GPU-authorization.json'),
   asset_spec_sha256=sha(stage/ASSETS),assets=assets_check(root,json.loads((stage/ASSETS).read_bytes())))
  atomic_json(stage/'fresh-admission.json',admission)
 else:admission=json.loads((stage/'fresh-admission.json').read_bytes())
 storage,resources=fresh_resources(root,stage,authority,profile)
 assert not list(storage.output.iterdir())
 with storage.journal.path.open('rb') as stream:assert all(block==bytes(len(block)) for block in iter(lambda:stream.read(2**20),b''))
 admission.update(status='P1_COMPLETE_FRESH_ADMISSION_NO_GPU',authorization=authority,
  authorization_raw_utf8=(stage/'GPU-authorization.json').read_text(),resources=resources,forecast_GPUh=quote['forecast_GPUh'],
  central_operator_sha256=registration['payload_sha256']['src/wcomr/cara_source_lifecycle_p1_central_r1.py'],
  semantic_positions=146,physical_generation_upper=142,physical_model_pairs_upper=5176,postrelease_new_pairs_upper=32,
  required_hosts=['two_card'],required_host_whole_card_CPU_accepted=True,
  execution_host_policy_sha256=authority['execution_host_policy_sha256'],observed_unix=time.time(),GPU_submissions=0)
 atomic_json(stage/'fresh-admission.json',admission)
 result=dict(status='P1_FRESH_ADMISSION_NO_GPU',admission=admission,original=original(),GPU_submissions=0,ledger_written=False)
elif action=='dispatch':
 result=recover(stage)
 if result is None:
  envelope=p['central']['envelope'];path=stage/'central-reservation.json'
  if path.exists():assert json.loads(path.read_bytes())==envelope
  else:create(path,envelope)
  central_binding(stage,auth,p['central']['snapshot'])
  result=dispatch(root,stage,p['central']['snapshot'],p['sudo_password'])
else:
 assert action=='status'
 result=dict(status='P1_ORIGINAL_OPERATIONAL_CAPTURE',recovery=recover(stage),original=original(),GPU_submissions=0,ledger_written=False)
 launch=stage/'GPU-launch.json'
 if launch.exists():
  result['launch_sha256']=sha(launch);result['lifecycle']=capture_lifecycle(root,stage,result['launch_sha256'])
  result['selected_gpu']=selected_gpu(auth['gpu_uuid'])
  for name in ('guardian.json','supervisor-start.json','supervisor.json','runner-start.json','pg-runner-context-granted.json','billing.json'):
   path=stage/name
   if path.exists():result[name]=json.loads(path.read_bytes())
 output=root/'outputs'/RUN_ID
 if output.exists():
  disk=os.statvfs(output);algorithm=output/'algorithm'
  result['operational_progress']=dict(semantic_denominator=146,physical_generation_upper=142,
   completed_physical_request_files=len(list((algorithm/'operations').glob('*/request-complete.json'))),
   internal_query_intent_files=len(list((algorithm/'operations').glob('score-*/intent.json'))),
   semantic_alias_count_unknown_before_complete_acceptance=True,free_bytes=disk.f_bavail*disk.f_frsize,scientific_scores_read=False)
print(json.dumps(result))
'''
CENTRAL=r'''
import base64,hashlib,io,json,pathlib,sys,tarfile,time
p=packet['arguments'];auth=p['authority'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
source=pathlib.Path('/tmp')/('source-lifecycle-P1-central-operator-'+auth['launch_id']);expected=p['plan']['overlay_sha256']
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
if p['action']=='central-prepare':
 assert not source.exists(),'Existing or partial original operator: recover only'
 raw=base64.b64decode(p['archive'],validate=True);assert hashlib.sha256(raw).hexdigest()==p['archive_sha256']
 source.mkdir(mode=0o700);found=set()
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
  for member in archive:
   name=member.name;relative=pathlib.Path(name)
   assert member.isfile() and name in expected and name not in found and not relative.is_absolute() and '..' not in relative.parts
   body=archive.extractfile(member).read();assert hashlib.sha256(body).hexdigest()==expected[name]
   target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body);found.add(name)
 assert found==set(expected)
assert source.is_dir() and not source.is_symlink() and all(sha(source/n)==h for n,h in expected.items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(source/'src'),str(source/'scripts')]
from wcomr.cara_source_lifecycle_p1_central_r1 import reserve,settle,Pool,ledger_valid,validate_authority,RUN
validate_authority(auth,root)
pool=Pool(root);receipt=root/'reports'/(RUN+'.central-reservation.json');envelope=None
before_sha=sha(pool.path)
if p['action']=='reserve':
 assert auth==p['refresh']['admission']['authorization']
 envelope=reserve(root,p['refresh']['admission'],dict(two_card=p['refresh']['original']))
elif p['action']=='settle':
 envelope=settle(root,p['capture'],p['expected_launch_sha256'])
elif p['action']=='central-recover' and receipt.exists():
 saved=json.loads(receipt.read_bytes());job=saved['job']
 # reserve() recognizes the original persisted receipt before fresh admission;
 # this can finish only that exact proposed write, with no new GPU or cap step.
 envelope=reserve(root,dict(authorization=auth,authorization_raw_utf8=p['authorization_raw_utf8'],
  authorization_sha256=hashlib.sha256(p['authorization_raw_utf8'].encode()).hexdigest(),
  registration_sha256=job['registration_sha256'],forecast_GPUh=job['forecast_GPUh']),{})
else:
 assert p['action'] in ('central-prepare','central-status','central-recover')
 if receipt.exists():envelope=json.loads(receipt.read_bytes())
snapshot=dict(central_ledger_host='four_card',ledger=pool.read(),observed_unix=time.time());ledger_valid(snapshot['ledger'])
print(json.dumps(dict(status='P1_ORIGINAL_CENTRAL_TRANSACTION_OR_RECOVERY',action=p['action'],operator_cache=str(source),
 operator_source_files=len(expected),envelope=envelope,snapshot=snapshot,GPU_submissions=0,ledger_written=before_sha!=sha(pool.path))))
'''


def authorized(action, auth):
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.cara_source_lifecycle_p1_central_r1 import validate_authority
    validate_authority(auth,Path(PROJECT))
    # This runs before reading credentials, constructing an SSH process, or
    # probing either host. Prior P0/M1 exceptions cannot reach four-card.
    central=action.startswith('central-') or action in ('reserve','settle')
    return central


def wrapped_rpc_code(remote):
    return ("import contextlib,io,json,gzip,base64,hashlib\n"
            "with contextlib.redirect_stdout(io.StringIO()) as rpc_output:\n"
            " exec("+repr(remote)+", {'packet':packet})\n"
            "rpc_bytes=rpc_output.getvalue().encode()\n"
            "print(json.dumps(dict(gzip_base64=base64.b64encode(gzip.compress(rpc_bytes)).decode(),"
            "sha256=hashlib.sha256(rpc_bytes).hexdigest())))\n")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('bind','admit','refresh','dispatch','status','central-prepare','central-recover','central-status','reserve','settle'))
    parser.add_argument('--input',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    raw=(ROOT/AUTH).read_text();auth=json.loads(raw);central=authorized(args.action,auth)
    read=lambda name:json.loads((ROOT/name).read_bytes())
    payload=dict(action=args.action,authority=auth,authorization_raw_utf8=raw)
    if central:
        from wcomr.immutable_stage_payload_r1 import local_python_closure
        expected=local_python_closure(ROOT,['src/wcomr/cara_source_lifecycle_p1_central_r1.py'])
        proof=read(PROOF)
        assert proof['whole_card_CPU_accepted'] and all(proof['payload_sha256'].get(n)==h for n,h in expected.items())
        payload['plan']=dict(overlay_sha256=expected)
        if args.action=='central-prepare':
            buffer=io.BytesIO()
            with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
                for name in sorted(expected):
                    body=(ROOT/name).read_bytes();member=tarfile.TarInfo(name);member.size=len(body);member.mode=0o644
                    archive.addfile(member,io.BytesIO(body))
            body=buffer.getvalue();payload.update(archive=base64.b64encode(body).decode(),archive_sha256=hashlib.sha256(body).hexdigest())
    else:payload['registration_sha256']=read(PREPARED)['result']['registration_sha256']
    if args.action in ('reserve','dispatch','settle'):
        assert args.input is not None
        supplied=json.loads(args.input.read_bytes());assert supplied['exit_code']==0
        if args.action=='reserve':payload['refresh']=supplied['result']
        elif args.action=='dispatch':payload['central']=supplied['result']
        else:payload.update(capture=supplied['result']['lifecycle'],expected_launch_sha256=supplied['result']['launch_sha256'])
    secret=None if central else password()
    if args.action=='dispatch':payload['sudo_password']=secret
    remote=CENTRAL if central else TWO
    code=wrapped_rpc_code(remote)
    encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=code,arguments=payload)).encode())).decode()
    interpreter='python3' if central else '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=shlex.quote(interpreter)+' -c '+shlex.quote("import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    if not central:command="sudo -S -p '' -u gaokuangda -g docker "+command
    private=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'
    assert private.stat().st_mode&0o077==0
    started=time.time()
    child=subprocess.Popen(['ssh','-C','-F',str(private),'-o','BatchMode=yes','-o','ConnectTimeout=60',
        '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','four_card_lan' if central else 'two_card_lan',command],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate(((secret+'\n' if secret else '')+encoded).encode(),timeout=300 if args.action=='admit' else 110)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
    result=None
    if child.returncode==0:
        wrapped=json.loads(out);body=gzip.decompress(base64.b64decode(wrapped['gzip_base64']))
        assert hashlib.sha256(body).hexdigest()==wrapped['sha256'];result=json.loads(body)
    stderr=err.decode(errors='replace');stderr=stderr.replace(secret,'[REDACTED]') if secret else stderr
    receipt=dict(action=args.action,started_unix=started,observed_unix=time.time(),exit_code=child.returncode,result=result,stderr=stderr,
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_code_sha256=hashlib.sha256(remote.encode()).hexdigest(),
        launch_id=auth['launch_id'],source_revision=auth['source_revision'],unknown_requires_original_recovery=True)
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(action=args.action,exit_code=child.returncode,status=(result or {}).get('status'),stderr=stderr[-1800:])))


if __name__=='__main__':
    main()
