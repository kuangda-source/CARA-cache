"""Transport published source preparation only; never start a GPU or CPU job."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import base64,hashlib,io,json,os,sys,tarfile,tempfile
from pathlib import Path
p=json.load(sys.stdin);project=Path('/data20t/gaokuangda/worldcache_workspace')
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1')
with tempfile.TemporaryDirectory(prefix='calibration-source-operator-') as temporary:
 root=Path(temporary);expected=p['plan']['overlay_sha256'];found=set()
 raw=base64.b64decode(p['archive']);assert hashlib.sha256(raw).hexdigest()==p['archive_sha256']
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
  for member in archive:
   name=member.name;relative=Path(name)
   assert member.isfile() and name in expected and name not in found
   assert not relative.is_absolute() and '..' not in relative.parts and str(relative)==name
   body=archive.extractfile(member).read();assert hashlib.sha256(body).hexdigest()==expected[name]
   target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body);found.add(name)
 assert found==set(expected)
 sys.path[:0]=[str(root/'src'),str(root/'scripts')]
 from wcomr.cara_budget_prepare_r1 import observe_original,prepare
 if p['action']=='observe':result=observe_original(project,p['host'])
 elif p['action']=='prepare':
  registration=prepare(project,p['host'],Path(p['base_stage']),raw,p['plan'],p['source_revision'],p['observations'])
  stage=Path(registration['stage'])
  result=dict(status='PUBLISHED_SOURCE_STAGE_PREPARED_NO_GPU_AUTHORITY',host=p['host'],stage=str(stage),
   registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
   payload_files=len(registration['payload_sha256']),source_revision=registration['source_revision'],
   GPU_authority_present=(stage/'GPU-authorization.json').exists(),GPU_submissions=0,CPU_jobs_started=0)
 else:raise ValueError('Unknown preparation action')
 print(json.dumps(result,allow_nan=False))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['observe','prepare'])
    parser.add_argument('--host',choices=['four_card','two_card'],required=True)
    for name in ('ssh-config','plan','archive','output','binding'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--observations',type=Path);parser.add_argument('--base-stage')
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    if args.output.exists() or args.binding.exists():raise ValueError('Fresh transport observation files required')
    if args.ssh_config.stat().st_mode&0o077:raise ValueError('Task SSH configuration must remain0600')
    if args.action=='prepare' and (args.observations is None or not args.base_stage):
        raise ValueError('Both original observations and base stage required')
    archive=args.archive.read_bytes();plan=json.loads(args.plan.read_text())
    payload=dict(action=args.action,host=args.host,source_revision=args.source_revision,plan=plan,
        archive=base64.b64encode(archive).decode(),archive_sha256=hashlib.sha256(archive).hexdigest(),base_stage=args.base_stage)
    if args.observations:payload['observations']=json.loads(args.observations.read_text())
    binding=dict(action=args.action,host=args.host,source_revision=args.source_revision,
        archive_sha256=payload['archive_sha256'],plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        transport_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),started_unix=time.time(),
        GPU_submissions=0,CPU_jobs_started=0)
    with args.binding.open('x') as f:json.dump(binding,f,indent=2);f.write('\n')
    interpreter=('python3' if args.host=='four_card' else
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python')
    command=shlex.quote(interpreter)+' -c '+shlex.quote(REMOTE);data=json.dumps(payload);secret=None
    if args.host=='two_card':
        from cara_two_card_transport_r1 import password
        secret=password();command="sudo -S -p '' -u gaokuangda -g docker "+command;data=secret+'\n'+data
    target='four_card' if args.host=='four_card' else 'two_card_lan'
    child=subprocess.Popen(['ssh','-F',str(args.ssh_config),'-o','BatchMode=yes','-o','ConnectTimeout=60',
        '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3',target,command],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate(data.encode(),timeout=90)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
        err+=b'\nTransport timeout; recover the original stage before any preparation retry.'
    message=err.decode(errors='replace')
    if secret:message=message.replace(secret,'[REDACTED]')
    result=dict(binding,exit_code=child.returncode,observed_unix=time.time(),stderr=message,
        result=json.loads(out) if child.returncode==0 else None)
    with args.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,allow_nan=False))
    raise SystemExit(0 if child.returncode==0 else 1)


if __name__=='__main__':main()
