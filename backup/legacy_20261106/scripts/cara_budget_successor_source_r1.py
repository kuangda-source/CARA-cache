"""Prepare or inspect only the successor source from its accepted CPU stage."""
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
import hashlib,io,json,pathlib,sys,tarfile,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');base=pathlib.Path(p['base_stage'])
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(base/'registration.json')==p['base_registration_sha256']
reg=json.loads((base/'registration.json').read_text());assert reg['parent_git_revision']==p['source_revision']
assert hashlib.sha256(json.dumps(reg['payload_sha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==p['full_payload_mapping_sha256']
assert all(sha(base/name)==digest for name,digest in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(base/'src'),str(base/'scripts')]
from wcomr.cara_budget_prepare_r1 import prepare,observe_original
from wcomr.cara_budget_central_r1 import RUN,STAGES
from wcomr.cara_fast_b36_dispatch_r2 import create
from wcomr.history104_storage_r2 import StorageGuard
stage=root/'.sync'/STAGES['two_card'];assert str(stage)==p['stage'] and RUN==p['run_id']
original=observe_original(root,'two_card')
assert original['dispatch_records']==[] and original['container'] is None
assert not (stage/'GPU-authorization.json').exists(),'An approved or original stage must only be recovered'
if p['action']=='prepare':
 plan=dict(status='CALIBRATION_SOURCE_PLAN_NO_GPU_AUTHORITY',overlay_sha256=reg['payload_sha256'],base_registration_sha256=p['base_registration_sha256'],base_source_revision=p['source_revision'],base_revision_field='parent_git_revision',GPU_submissions=0,execution_authorized=False)
 buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
  for name in sorted(reg['payload_sha256']):
   raw=(base/name).read_bytes();member=tarfile.TarInfo(name);member.size=len(raw);member.mode=0o644;archive.addfile(member,io.BytesIO(raw))
 prepared=prepare(root,'two_card',base,buffer.getvalue(),plan,p['source_revision'],dict(two_card=original))
 provision=pathlib.Path(p['storage']['storage_contract']['image_path']).parent/'provision.json'
 assert sha(provision)==p['storage']['provision_sha256']
 config=json.loads(provision.read_text())['storage_contract'];assert config==p['storage']['storage_contract'] and config['run_id']==RUN
 storage=StorageGuard(config);storage.check();assert list(storage.output.iterdir())==[]
 with storage.journal.path.open('rb') as stream:assert all(block==bytes(len(block)) for block in iter(lambda:stream.read(2**20),b''))
 path=stage/'history104-storage.json'
 if path.exists():assert json.loads(path.read_text())==config
 else:create(path,config)
else:
 assert p['action']=='capture'
 prepared=json.loads((stage/'registration.json').read_text()) if (stage/'registration.json').exists() else None
 if prepared is not None:
  assert prepared['source_revision']==p['source_revision'] and prepared['payload_sha256']==reg['payload_sha256']
  assert all(sha(stage/n)==h for n,h in prepared['payload_sha256'].items())
print(json.dumps(dict(status='SUCCESSOR_SOURCE_PREPARATION_OR_CAPTURE_NO_AUTHORITY',stage=str(stage),source_revision=p['source_revision'],registration_sha256=sha(stage/'registration.json') if prepared else None,source_files=len(prepared['payload_sha256']) if prepared else 0,source_intact=prepared is not None,storage_bound=(stage/'history104-storage.json').exists(),original=observe_original(root,'two_card'),GPU_authority_present=False,GPU_submissions=0,ledger_written=False,observed_unix=time.time())))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','capture']);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert not args.output.exists()
    read=lambda name:json.loads((ROOT/name).read_text())
    review=read('plans/cara_next_stage_20261028/mainline/r2/BUDGET_SUCCESSOR14GPUH_REVIEW_R1_20261031.json')
    assert review['execution_authorized'] is False
    accepted=read('reports/cara_budget_successor_CPU_accepted_r2_20261031.json')
    cap=read(accepted['capture_ref'])['result'];reg=cap['registration']
    payload=dict(action=args.action,run_id=review['run_id'],stage=review['stage'],source_revision=review['source_revision'],
        base_stage=cap['launch']['stage'],base_registration_sha256=cap['registration_sha256'],
        full_payload_mapping_sha256=hashlib.sha256(json.dumps(reg['payload_sha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        storage=read(review['storage_ref']))
    secret=password();encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=REMOTE,arguments=payload)).encode())).decode()
    command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote("import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    started=time.time();child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),'-o','BatchMode=yes','-o','ConnectTimeout=25','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate((secret+'\n'+encoded).encode(),timeout=100)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
    report=dict(action=args.action,started_unix=started,observed_unix=time.time(),exit_code=child.returncode,result=json.loads(out) if child.returncode==0 else None,
        stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),GPU_submissions=0,ledger_written=False,original_handle_recovery_on_unknown=True)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,result=report['result'],stderr=report['stderr'][-1000:])))


if __name__=='__main__':main()
