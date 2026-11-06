"""Prepare or recover only the selected46 source; no authority, GPU or central access."""
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
REMOTE=r'''
import hashlib,json,pathlib,shutil,subprocess,sys,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');base=pathlib.Path(p['base_stage'])
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(base/'registration.json')==p['base_registration_sha256']
reg=json.loads((base/'registration.json').read_text());assert reg['parent_git_revision']==p['source_revision']
assert reg['payload_sha256']==p['proof']['payload_sha256'] and reg['runtime_source_sha256']==p['proof']['runtime_source_sha256']
assert base.parent==root/'.sync' and not base.is_symlink()
assert all(sha(base/n)==h for n,h in reg['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(base/'src'),str(base/'scripts')]
from wcomr.cara_endpoint7_central_r1 import RUN,STAGES
from wcomr.cara_budget_lifecycle_capture_r1 import inspect_container
from wcomr.cara_fast_b36_dispatch_r2 import create
from wcomr.history104_storage_r2 import StorageGuard
stage=root/'.sync'/STAGES['two_card'];assert str(stage)==p['stage'] and RUN==p['run_id']
assert not stage.is_symlink()
records=[n for n in ('GPU-intent.json','GPU-dispatch.json','GPU-launch.json','guardian-intent.json','GPU-authorization.json') if (stage/n).exists()]
container=inspect_container(stage.name+'-gpu')
assert not records and container is None,'Original or authorized run: recover only'
base_rows=json.loads(subprocess.check_output(['docker','inspect','--type','container',base.name+'-cpu'],text=True,timeout=20))
assert len(base_rows)==1
base_container=base_rows[0]
assert base_container['State']['Status']=='exited' and base_container['State']['ExitCode']==0 and not base_container['State']['OOMKilled'] and base_container['HostConfig']['DeviceRequests'] is None
if p['action']=='prepare':
 assert not stage.exists(),'Existing or partial source stage: capture only'
 stage.mkdir(mode=0o700)
 for name,digest in reg['payload_sha256'].items():
  assert not pathlib.Path(name).is_absolute() and '..' not in pathlib.Path(name).parts
  target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,target)
 assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
 profile=json.loads((stage/'configs/cara_endpoint_container_profile.json').read_text())
 prepared=dict(host='two_card',stage=str(stage),source_revision=p['source_revision'],payload_sha256=reg['payload_sha256'],
  runtime_source_sha256=reg['runtime_source_sha256'],container_image=profile['GPU_container']['image'],
  read_only_base_registration_sha256=p['base_registration_sha256'],base_stage=str(base),
  CPU_scope='ENDPOINT7_PREPARATION_NO_GPU_AUTHORITY',GPU_submissions_by_installer=0)
 create(stage/'registration.json',prepared)
 provision=pathlib.Path(p['storage']['storage_contract']['image_path']).parent/'provision.json'
 assert sha(provision)==p['storage']['provision_sha256']
 config=json.loads(provision.read_text())['storage_contract'];assert config==p['storage']['storage_contract'] and config['run_id']==RUN
 storage=StorageGuard(config);storage.check();assert list(storage.output.iterdir())==[]
 with storage.journal.path.open('rb') as stream:assert all(block==bytes(len(block)) for block in iter(lambda:stream.read(2**20),b''))
 for name,value in [('history104-storage.json',config),('execution-CPU-proof.json',p['proof']),('whole-quote.json',p['quote'])]:create(stage/name,value)
else:
 assert p['action']=='capture'
 prepared=json.loads((stage/'registration.json').read_text()) if (stage/'registration.json').exists() else None
 if prepared is not None:
  assert prepared['source_revision']==p['source_revision'] and prepared['payload_sha256']==reg['payload_sha256']
  assert all(sha(stage/n)==h for n,h in prepared['payload_sha256'].items())
result=dict(status='ENDPOINT7_SOURCE_PREPARATION_OR_CAPTURE_NO_AUTHORITY',stage=str(stage),source_revision=p['source_revision'],
 registration=prepared,registration_sha256=sha(stage/'registration.json') if prepared else None,
 source_files=len(prepared['payload_sha256']) if prepared else 0,source_intact=prepared is not None,
 storage_bound=(stage/'history104-storage.json').exists(),original_dispatch_records=records,original_container=container,
 GPU_authority_present=False,GPU_submissions=0,ledger_written=False,observed_unix=time.time())
if prepared and all((stage/n).exists() for n in ('history104-storage.json','execution-CPU-proof.json','whole-quote.json')):
 for name,value in [('execution-CPU-proof.json',p['proof']),('whole-quote.json',p['quote'])]:assert json.loads((stage/name).read_text())==value
 guard=StorageGuard(json.loads((stage/'history104-storage.json').read_text()))
 result['storage_observation']=guard.check();assert not list(guard.output.iterdir())
 from wcomr.cara_s_endpoint_reuse_admission_r1 import verify_reuse
 result['original_reuse']=verify_reuse(root,json.loads((stage/'configs/cara_endpoint_proposal.json').read_text()),json.loads((stage/'configs/cara_endpoint_original_B36_scores.json').read_text()))
 bound=json.loads((stage/'configs/cara_endpoint_frozen_binding.json').read_text())
 assert sha(bound['original_freeze_path'])==bound['original_freeze_sha256']
 result['original_budget_freeze_sha256']=bound['original_freeze_sha256'];result['preparation_complete']=True
else:result['preparation_complete']=False
print(json.dumps(result))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','capture']);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists()
    read=lambda name:json.loads((ROOT/name).read_text())
    proof=read('reports/cara_endpoint7_whole_CPU_accepted_r1_20261101.json')
    assert proof['whole_card_CPU_accepted'] and not proof['execution_authorized']
    accepted=read('reports/cara_endpoint7_central_CPU_accepted_r1_20261101.json')
    assert hashlib.sha256((ROOT/accepted['capture_ref']).read_bytes()).hexdigest()==accepted['capture_sha256']
    cap=read(accepted['capture_ref'])['result'];reg=cap['registration']
    payload=dict(action=args.action,run_id='cara-S-endpoint-seven46-r1-20261101',
        stage='/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-GPU-a6000-seven46-r1-20261101',
        source_revision=proof['source_revision'],base_stage=cap['launch']['stage'],base_registration_sha256=cap['registration_sha256'],
        proof=proof,quote=read('configs/cara_endpoint_whole_quote.json'),storage=read('reports/cara_endpoint7_storage_accepted_r1_20261101.json'))
    secret=password();encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=REMOTE,arguments=payload)).encode())).decode()
    command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote("import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    started=time.time();child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),'-o','BatchMode=yes','-o','ConnectTimeout=25','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate((secret+'\n'+encoded).encode(),timeout=180)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
    report=dict(action=args.action,started_unix=started,observed_unix=time.time(),exit_code=child.returncode,result=json.loads(out) if child.returncode==0 else None,
        stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),GPU_submissions=0,ledger_written=False,original_handle_recovery_on_unknown=True)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,status=report['result']['status'] if report['result'] else None,preparation_complete=report['result'].get('preparation_complete') if report['result'] else None,stderr=report['stderr'][-1000:])))


if __name__=='__main__':main()
