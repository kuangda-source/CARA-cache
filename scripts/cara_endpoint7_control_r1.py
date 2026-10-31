"""Approved single E1 control, using its unchanged accepted production modules."""
import argparse,base64,gzip,hashlib,io,json,os,shlex,signal,subprocess,sys,tarfile,time
from pathlib import Path
from cara_two_card_transport_r1 import password
ROOT=Path(__file__).resolve().parents[1]
AUTH='plans/cara_next_stage_20261101/e1/ENDPOINT7_SINGLE7GPUH_USER_AUTHORIZATION_R1.json'
TWO=r'''
import hashlib,json,os,pathlib,sys,time
p=packet['arguments'];auth=p['authority'];stage=pathlib.Path(auth['stage']);root=stage.parent.parent
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
assert sha(stage/'registration.json')==p['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==auth['source_revision']
assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.cara_s_endpoint_gpu_dispatch_r1 import ready_inputs,fresh_resources,dispatch,recover
from wcomr.cara_s_endpoint_lifecycle_capture_r1 import inspect_container,capture_lifecycle
from wcomr.cara_budget_dispatch_r1 import ASSETS,central_binding
from wcomr.cara_endpoint7_central_r1 import RUN,STAGES
from wcomr.cara_fast_b36_dispatch_r2 import create,assets_check,selected_gpu
from wcomr.gpu_budget_pool_v2 import atomic_json
assert auth['run_id']==RUN and stage==root/'.sync'/STAGES['two_card']
def original():
 return dict(host='two_card',stage=str(stage),run_id=RUN,stage_exists=stage.exists(),dispatch_records=[n for n in ('GPU-intent.json','GPU-dispatch.json','GPU-launch.json','guardian-intent.json') if (stage/n).exists()],container=inspect_container(stage.name+'-gpu'),observation_complete=True,observed_unix=time.time())
if p['action']=='bind':
 assert recover(stage) is None and original()['container'] is None
 for name,digest in [('execution-CPU-proof.json',auth['CPU_proof_sha256']),('whole-quote.json',auth['quote_sha256'])]:assert sha(stage/name)==digest
 path=stage/'GPU-authorization.json'
 if path.exists():assert json.loads(path.read_text())==auth
 else:create(path,auth)
 ready_inputs(root,stage)
 result=dict(status='ENDPOINT7_ORIGINAL_AUTHORITY_BOUND_NO_GPU',authorization_sha256=sha(path),original=original())
elif p['action'] in ('admit','refresh'):
 assert recover(stage) is None
 card,bound,proposal,registration,authority,profile=ready_inputs(root,stage)
 assert authority==auth
 if p['action']=='admit':
  assets=assets_check(root,json.loads((stage/ASSETS).read_text()))
  admission=dict(registration_sha256=sha(stage/'registration.json'),authorization_sha256=sha(stage/'GPU-authorization.json'),asset_spec_sha256=sha(stage/ASSETS),assets=assets)
  atomic_json(stage/'fresh-admission.json',admission)
 else:admission=json.loads((stage/'fresh-admission.json').read_text())
 storage,resources=fresh_resources(root,stage,authority,profile)
 assert not list(storage.output.iterdir())
 with storage.journal.path.open('rb') as f:assert all(b==bytes(len(b)) for b in iter(lambda:f.read(2**20),b''))
 quote=json.loads((stage/'whole-quote.json').read_text())['host_quotes']['two_card']
 admission.update(status='ENDPOINT7_COMPLETE_FRESH_ADMISSION_NO_GPU',authorization=authority,
  central_operator_sha256=registration['payload_sha256']['src/wcomr/cara_endpoint7_central_r1.py'],
  authorization_raw_utf8=(stage/'GPU-authorization.json').read_text(),resources=resources,
  forecast_GPUh=quote['forecast_GPUh'],physical_paths=46,new_scoring_pairs=16,
  required_hosts=['two_card'],required_host_whole_card_CPU_accepted=True,
  execution_host_policy_sha256=authority['execution_host_policy_sha256'],observed_unix=time.time(),GPU_submissions=0)
 atomic_json(stage/'fresh-admission.json',admission)
 result=dict(status='ENDPOINT7_FRESH_ADMISSION_NO_GPU',admission=admission,original=original(),GPU_submissions=0,ledger_written=False)
elif p['action']=='dispatch':
 result=recover(stage)
 if result is None:
  envelope=p['central']['envelope'];path=stage/'central-reservation.json'
  if path.exists():assert json.loads(path.read_text())==envelope
  else:create(path,envelope)
  central_binding(stage,auth,p['central']['snapshot'])
  result=dispatch(root,stage,p['central']['snapshot'],p['sudo_password'])
else:
 assert p['action']=='status'
 result=dict(status='ENDPOINT7_ORIGINAL_OPERATIONAL_CAPTURE',recovery=recover(stage),original=original(),GPU_submissions=0,ledger_written=False)
 launch=stage/'GPU-launch.json'
 if launch.exists():
  result['launch_sha256']=sha(launch);result['lifecycle']=capture_lifecycle(root,stage,result['launch_sha256'])
  result['selected_gpu']=selected_gpu(auth['gpu_uuid'])
  for name in ('guardian.json','supervisor-start.json','supervisor.json','runner-start.json','pg-runner-context-granted.json','billing.json'):
   path=stage/name
   if path.exists():result[name]=json.loads(path.read_text())
 output=root/'outputs'/auth['run_id']
 if output.exists():
  disk=os.statvfs(output)
  progress=dict(expected_physical_paths=46,encoded_video_files=len(list((output/'B').rglob('*.mp4'))),free_bytes=disk.f_bavail*disk.f_frsize,scientific_scores_read=False)
  collection=output/'endpoint-collection.json'
  if collection.exists():
   # Export only operational row states, never partial scores or timings.
   state=json.loads(collection.read_text())
   assert state['scope_sha256']==auth['scope_sha256'] and len(state['rows'])==46
   counts={name:sum(row['status']==name for row in state['rows']) for name in ('COMPLETE','TECH_FAILED','RUNNING','NOT_REACHED')}
   assert sum(counts.values())==46
   progress.update(collection_state=state['status'],counts=counts)
  else:progress['collection_state']='NOT_STARTED'
  result['operational_progress']=progress
 if result.get('lifecycle',{}).get('status')=='ORIGINAL_ENDPOINT_LIFECYCLE_CAPTURE':
  result['terminal_diagnostic_logs']={n:(stage/n).read_text(errors='replace')[-9000:] for n in ('runner.log','container-cli.log') if (stage/n).exists()}
 result['host_guardian_log_tail']=(stage/'host-guardian.log').read_text(errors='replace')[-2500:] if (stage/'host-guardian.log').exists() else None
print(json.dumps(result))
'''
CENTRAL=r'''
import base64,hashlib,io,json,pathlib,sys,tarfile,time
p=packet['arguments'];auth=p['authority'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
assert auth['central_transaction_authorized'] and auth['run_id']=='cara-S-endpoint-seven46-r1-20261101'
source=pathlib.Path('/tmp')/('endpoint7-central-operator-'+auth['launch_id'])
expected=p['plan']['overlay_sha256']
if p['action']=='central-prepare':
 assert not source.exists(),'Existing or partial operator: recover only'
 raw=base64.b64decode(p['archive']);assert hashlib.sha256(raw).hexdigest()==p['archive_sha256']
 source.mkdir(mode=0o700);found=set()
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
  for member in archive:
   name=member.name;relative=pathlib.Path(name)
   assert member.isfile() and name in expected and name not in found and not relative.is_absolute() and '..' not in relative.parts
   body=archive.extractfile(member).read();assert hashlib.sha256(body).hexdigest()==expected[name]
   target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body);found.add(name)
 assert found==set(expected)
assert source.is_dir() and not source.is_symlink()
assert all(hashlib.sha256((source/n).read_bytes()).hexdigest()==h for n,h in expected.items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(source/'src'),str(source/'scripts')]
from wcomr.cara_endpoint7_central_r1 import reserve,settle,Pool,RUN,ledger_valid
pool=Pool(root);receipt=root/'reports'/(RUN+'.central-reservation.json');envelope=None
if p['action']=='reserve':
 assert auth==p['refresh']['admission']['authorization']
 envelope=reserve(root,p['refresh']['admission'],dict(two_card=p['refresh']['original']))
elif p['action']=='settle':
 envelope=settle(root,p['capture'],p['expected_launch_sha256'])
else:
 assert p['action'] in ('central-prepare','central-status','central-recover')
 if receipt.exists():envelope=json.loads(receipt.read_text())
snapshot=dict(central_ledger_host='four_card',ledger=pool.read(),observed_unix=time.time());ledger_valid(snapshot['ledger'])
print(json.dumps(dict(status='ENDPOINT7_ORIGINAL_CENTRAL_TRANSACTION_OR_RECOVERY',action=p['action'],operator_cache=str(source),operator_source_files=len(expected),envelope=envelope,snapshot=snapshot,GPU_submissions=0,ledger_written=p['action'] in ('reserve','settle'))))
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['bind','admit','refresh','dispatch','status','central-prepare','central-recover','central-status','reserve','settle'])
 p.add_argument('--input',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 read=lambda n:json.loads((ROOT/n).read_text())
 auth=read(AUTH);assert auth['execution_authorized'] and auth['central_transaction_authorized'] and auth['hard_GPUh']==7
 central=a.action.startswith('central-') or a.action in ('reserve','settle')
 packet=dict(action=a.action,authority=auth)
 if central:
  sys.path.insert(0,str(ROOT/'src'))
  from wcomr.immutable_stage_payload_r1 import local_python_closure
  proof=read('reports/cara_endpoint7_whole_CPU_accepted_r1_20261101.json')
  expected=local_python_closure(ROOT,['src/wcomr/cara_endpoint7_central_r1.py'])
  assert all(proof['payload_sha256'].get(n)==h for n,h in expected.items())
  packet['plan']=dict(overlay_sha256=expected)
  if a.action=='central-prepare':
   buffer=io.BytesIO()
   with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
    for n in sorted(expected):
     raw=(ROOT/n).read_bytes();member=tarfile.TarInfo(n);member.size=len(raw);member.mode=0o644;archive.addfile(member,io.BytesIO(raw))
   raw=buffer.getvalue();packet.update(archive=base64.b64encode(raw).decode(),archive_sha256=hashlib.sha256(raw).hexdigest())
 else:packet['registration_sha256']=read('reports/cara_endpoint7_source_preparation_r1_20261101.json')['result']['registration_sha256']
 if a.action in ('reserve','dispatch','settle'):
  assert a.input is not None
  supplied=json.loads(a.input.read_text());assert supplied['exit_code']==0
  if a.action=='reserve':packet['refresh']=supplied['result']
  elif a.action=='dispatch':packet['central']=supplied['result']
  else:packet.update(capture=supplied['result']['lifecycle'],expected_launch_sha256=supplied['result']['launch_sha256'])
 secret=None if central else password()
 if a.action=='dispatch':packet['sudo_password']=secret
 remote=CENTRAL if central else TWO
 code="import io,sys,json,gzip,base64,hashlib\nsaved=sys.stdout;sys.stdout=io.StringIO()\nexec("+repr(remote)+")\nraw=sys.stdout.getvalue().encode();sys.stdout=saved\nprint(json.dumps(dict(gzip_base64=base64.b64encode(gzip.compress(raw)).decode(),sha256=hashlib.sha256(raw).hexdigest())))\n"
 encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=code,arguments=packet)).encode())).decode()
 interpreter='python3' if central else '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
 command=shlex.quote(interpreter)+' -c '+shlex.quote("import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
 if not central:command="sudo -S -p '' -u gaokuangda -g docker "+command
 started=time.time();child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),'-o','BatchMode=yes','-o','ConnectTimeout=25','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','four_card_lan' if central else 'two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:out,err=child.communicate(((secret+'\n' if secret else '')+encoded).encode(),timeout=300 if a.action=='admit' else 110)
 except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
 result=None
 if child.returncode==0:
  wrapped=json.loads(out);raw=gzip.decompress(base64.b64decode(wrapped['gzip_base64']));assert hashlib.sha256(raw).hexdigest()==wrapped['sha256'];result=json.loads(raw)
 stderr=err.decode(errors='replace');stderr=stderr.replace(secret,'[REDACTED]') if secret else stderr
 report=dict(action=a.action,started_unix=started,observed_unix=time.time(),exit_code=child.returncode,result=result,stderr=stderr,transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_code_sha256=hashlib.sha256(remote.encode()).hexdigest(),launch_id=auth['launch_id'],source_revision=auth['source_revision'],unknown_requires_original_recovery=True)
 with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(action=a.action,exit_code=child.returncode,status=(result or {}).get('status'),stderr=stderr[-1800:])))
if __name__=='__main__':main()
