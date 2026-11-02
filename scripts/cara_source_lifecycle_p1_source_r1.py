"""Prepare/capture the P1 GPU source from accepted CPU bytes, without authority."""
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

ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import hashlib,json,pathlib,shutil,sys,time
p=packet['arguments'];root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');base=pathlib.Path(p['base_stage'])
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
assert base.parent==root/'.sync' and not base.is_symlink()
assert sha(base/'registration.json')==p['base_registration_sha256']
reg=json.loads((base/'registration.json').read_bytes())
assert reg['parent_git_revision']==p['source_revision'] and reg['payload_sha256']==p['proof']['payload_sha256']
assert reg['runtime_source_sha256']==p['proof']['runtime_source_sha256']
assert all(sha(base/n)==h for n,h in reg['payload_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
assert all(sha(root/'runtime'/n)==h for n,h in p['proof']['supplemental_runtime_sha256'].items())
sys.dont_write_bytecode=True;sys.path[:0]=[str(base/'src'),str(base/'scripts')]
from wcomr.cara_source_lifecycle_p1_identity_r1 import RUN_ID,STAGE_NAME,SCOPE_SHA256
from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import PROFILE,CARD,validate_profile
from wcomr.cara_source_lifecycle_p1_plan_r1 import validate
from wcomr.cara_source_lifecycle_p1_capture_r1 import inspect_container
from wcomr.cara_fast_b36_dispatch_r2 import create
from wcomr.history104_storage_r2 import StorageGuard
stage=root/'.sync'/STAGE_NAME
assert str(stage)==p['stage'] and not stage.is_symlink()
assert p['proof']['schema']=='CARA_V1_P1_WHOLE_CPU_COMPOSED_R1' and p['proof']['whole_card_CPU_accepted'] is True
assert p['proof']['scope_sha256']==SCOPE_SHA256 and p['proof']['execution_authorized'] is False
records=[n for n in ('GPU-intent.json','GPU-dispatch.json','GPU-launch.json','guardian-intent.json','GPU-authorization.json') if (stage/n).exists()]
container=inspect_container(stage.name+'-gpu')
assert not records and container is None,'Existing or authorized P1 run: recover only'
profile=json.loads((base/PROFILE).read_bytes());validate_profile(profile,SCOPE_SHA256)
config=p['storage']['storage_contract'];provision=pathlib.Path(config['image_path']).parent/'provision.json'
assert sha(provision)==p['storage']['provision_sha256'] and json.loads(provision.read_bytes())['storage_contract']==config
assert config['run_id']==RUN_ID
guard=StorageGuard(config);guard.check();assert not list(guard.output.iterdir())
with guard.journal.path.open('rb') as stream:assert all(b==bytes(len(b)) for b in iter(lambda:stream.read(2**20),b''))
environment=p['score_environment']
assert len(environment['weights_sha256'])==2 and all(sha(n)==h for n,h in environment['weights_sha256'].items())
assert (pathlib.Path(environment['piq_site'])/'piq/__init__.py').is_file()
if p['action']=='prepare':
 assert not stage.exists(),'Existing/partial P1 source stage: capture only'
 stage.mkdir(mode=0o700)
 create(stage/'source-preparation-intent.json',dict(source_revision=p['source_revision'],base_registration_sha256=p['base_registration_sha256'],no_replay=True,GPU_submissions=0))
 for name,h in reg['payload_sha256'].items():
  assert not pathlib.Path(name).is_absolute() and '..' not in pathlib.Path(name).parts
  target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,target)
 assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
 profile=json.loads((stage/PROFILE).read_bytes());validate_profile(profile,SCOPE_SHA256)
 prepared=dict(host='two_card',stage=str(stage),source_revision=p['source_revision'],payload_sha256=reg['payload_sha256'],
  runtime_source_sha256=reg['runtime_source_sha256'],container_image=profile['GPU_container']['image'],
  read_only_base_registration_sha256=p['base_registration_sha256'],base_stage=str(base),
  CPU_scope='P1_FULL146_PREPARATION_NO_GPU_AUTHORITY',GPU_submissions_by_installer=0)
 create(stage/'registration.json',prepared)
 for name,value in (('history104-storage.json',config),('execution-CPU-proof.json',p['proof']),
                    ('whole-quote.json',p['quote']),('internal-score-environment.json',environment)):
  create(stage/name,value)
else:
 assert p['action']=='capture'
 prepared=json.loads((stage/'registration.json').read_bytes()) if (stage/'registration.json').exists() else None
 if prepared is not None:
  assert prepared['source_revision']==p['source_revision'] and prepared['payload_sha256']==reg['payload_sha256']
  assert all(sha(stage/n)==h for n,h in prepared['payload_sha256'].items())
result=dict(status='P1_ORIGINAL_SOURCE_PREPARATION_OR_CAPTURE_NO_AUTHORITY',stage=str(stage),source_revision=p['source_revision'],
 registration=prepared,registration_sha256=sha(stage/'registration.json') if prepared else None,
 source_files=len(prepared['payload_sha256']) if prepared else 0,source_intact=prepared is not None,
 original_dispatch_records=records,original_container=container,GPU_authority_present=False,
 GPU_submissions=0,ledger_written=False,observed_unix=time.time())
sidecars=('history104-storage.json','execution-CPU-proof.json','whole-quote.json','internal-score-environment.json')
if prepared is not None and all((stage/n).is_file() for n in sidecars):
 for name,value in (('execution-CPU-proof.json',p['proof']),('whole-quote.json',p['quote']),('internal-score-environment.json',p['score_environment'])):
  assert json.loads((stage/name).read_bytes())==value
 card=json.loads((stage/CARD).read_bytes());validate(card)
 validate_profile(json.loads((stage/PROFILE).read_bytes()),card['scope_sha256'])
 guard=StorageGuard(json.loads((stage/'history104-storage.json').read_bytes()))
 result['storage_observation']=guard.check();assert not list(guard.output.iterdir())
 result.update(preparation_complete=True,sidecar_sha256={n:sha(stage/n) for n in sidecars})
else:result['preparation_complete']=False
print(json.dumps(result))
'''


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('prepare','capture'))
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    read=lambda name:json.loads((ROOT/name).read_bytes())
    proof=read('reports/cara_v1_P1_whole_CPU_accepted_r1_20261102.json')
    accepted=read('reports/cara_v1_P1_final_CPU_accepted_r1_20261102.json')
    assert proof['whole_card_CPU_accepted'] and not proof['execution_authorized']
    assert hashlib.sha256((ROOT/accepted['capture_ref']).read_bytes()).hexdigest()==accepted['capture_sha256']
    cap=read(accepted['capture_ref'])['result']
    assert cap['original_host_observation']['original_live'] is False and cap['host_terminal']['error'] is None
    assert cap['payload_intact'] and cap['runtime_intact']
    old=read('reports/cara_fast_B36_original_score_manifest_r1_20261029.json')
    project=Path('/data20t/gaokuangda/worldcache_workspace')
    environment={k:old[k] for k in ('torch_home','piq_site')}
    environment['weights_sha256']={
        str(Path(environment['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'):'7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02',
        str(project/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages/lpips/weights/v0.1/alex.pth'):'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'}
    payload=dict(action=args.action,stage=str(project/'.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r1-20261102'),
        source_revision=proof['source_revision'],base_stage=cap['launch']['stage'],base_registration_sha256=cap['registration_sha256'],
        proof=proof,quote=read('plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json'),
        storage=read('reports/cara_v1_P1_storage_accepted_r1_20261102.json'),score_environment=environment)
    secret=password();encoded=base64.b64encode(gzip.compress(json.dumps(dict(code=REMOTE,arguments=payload)).encode())).decode()
    command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote(
        "import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    started=time.time();child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'),
        '-o','BatchMode=yes','-o','ConnectTimeout=60','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',command],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate((secret+'\n'+encoded).encode(),timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
    result=json.loads(out) if child.returncode==0 else None
    receipt=dict(action=args.action,started_unix=started,observed_unix=time.time(),exit_code=child.returncode,result=result,
        stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),GPU_submissions=0,ledger_written=False,unknown_requires_original_capture=True)
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,preparation_complete=(result or {}).get('preparation_complete'),status=(result or {}).get('status'))))
