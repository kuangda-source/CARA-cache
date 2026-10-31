"""Prepare or recover only the approved two-card source stage; never dispatch."""
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
import hashlib,io,json,os,pathlib,sys,tarfile,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');base=pathlib.Path(p['base_stage'])
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(base/'registration.json')==p['plan']['base_registration_sha256']
reg=json.loads((base/'registration.json').read_text());assert reg['payload_sha256']==p['plan']['overlay_sha256']
assert all(sha(base/n)==h for n,h in reg['payload_sha256'].items())
sys.dont_write_bytecode=True;os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
sys.path[:0]=[str(base/'src'),str(base/'scripts')]
from wcomr.cara_budget_prepare_r1 import observe_original,prepare
observed=observe_original(root,'two_card');stage=pathlib.Path(observed['stage'])
if p['action']=='prepare':
 assert not observed['dispatch_records'] and observed['container'] is None
 stream=io.BytesIO()
 with tarfile.open(fileobj=stream,mode='w:gz') as archive:
  for name,expected in p['plan']['overlay_sha256'].items():
   raw=(base/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
   info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644;archive.addfile(info,io.BytesIO(raw))
 prepare(root,'two_card',base,stream.getvalue(),p['plan'],p['source_revision'],{'two_card':observed})
else:assert p['action']=='capture'
registration=stage/'registration.json';current=json.loads(registration.read_text()) if registration.exists() else None
print(json.dumps(dict(status='APPROVED_TWO_CARD_SOURCE_STAGE_OBSERVATION_NO_GPU',action=p['action'],observed_before=observed,stage=str(stage),registration_sha256=sha(registration) if current else None,source_revision=current['source_revision'] if current else None,payload_files=len(current['payload_sha256']) if current else 0,payload_intact=all(sha(stage/n)==h for n,h in current['payload_sha256'].items()) if current else None,runtime_intact=all(sha(root/'runtime'/n)==h for n,h in current['runtime_source_sha256'].items()) if current else None,authority_present=(stage/'GPU-authorization.json').exists(),observed_after=observe_original(root,'two_card'),observed_unix=time.time(),GPU_submissions=0,CPU_jobs_started=0,ledger_written=False)))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','capture'])
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    proof=json.loads((ROOT/'reports/cara_budget_two_card_whole_CPU_composed_r1_20261031.json').read_text())
    plan_path=ROOT/proof['package_ref']/'source-plan.json'
    assert hashlib.sha256(plan_path.read_bytes()).hexdigest()==proof['package_plan_sha256']
    base=json.loads((ROOT/proof['package_ref']/'base-registration.json').read_text())
    payload=dict(action=args.action,plan=json.loads(plan_path.read_text()),base_stage=base['stage'],source_revision=proof['source_revision'])
    secret=password();command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote("import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=REMOTE,arguments=payload)).encode())).decode()
    start=time.time();child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),'-o','BatchMode=yes','-o','ConnectTimeout=35','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate((secret+'\n'+encoded).encode(),timeout=110)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
    report=dict(started_unix=start,observed_unix=time.time(),action=args.action,exit_code=child.returncode,result=json.loads(out) if child.returncode==0 else None,stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),source_revision=proof['source_revision'],transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),GPU_submissions=0,ledger_written=False,recover_original_only_if_unknown=True)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report))


if __name__=='__main__':main()
