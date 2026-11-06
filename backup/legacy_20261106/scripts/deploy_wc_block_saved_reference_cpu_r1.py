#!/usr/bin/env python3
"""Read-only accepted B outputs audit in an isolated immutable CPU directory."""
import argparse
import base64
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SERVER='/home/gaokuangda/data/gkd/worldcache_omr'
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
BASE='wc-block-velocity-suffix3-cpu-r2-20261013'
CONFIG='configs/wc_block_velocity_suffix3_cpu_r1_20261013.json'
NEW=['src/wcomr/block_saved_reference_r1.py',
 'tests/check_block_saved_reference_cpu_r1.py',
 'scripts/check_wc_block_saved_reference_cpu_r1.py',
 'scripts/deploy_wc_block_saved_reference_cpu_r1.py',CONFIG]


def remote(code):
    compile(code,'fixed-mask-cpu-deploy','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--suffix',default='r1');a=p.parse_args()
    if a.suffix not in ('r1','r2','r3'):raise ValueError('Explicit immutable CPU revision required')
    stage=SERVER+'/.sync/wc-block-saved-reference-cpu-'+a.suffix+'-20261013'
    config=json.loads((ROOT/CONFIG).read_text());names=NEW
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    packet={'source_revision':rev,'new_payload_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}}
    for n,h in packet['new_payload_sha256'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)).hexdigest()==h
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as tar:
        for n in names:tar.add(ROOT/n,arcname=n)
    code='P='+repr(packet)+'\nBASE='+repr(SERVER+'/.sync/'+BASE)+'\nSTAGE='+repr(stage)+'\nROOT='+repr(SERVER)+'\nARCHIVE='+repr(base64.b64encode(buf.getvalue()).decode())+'\n'+r'''import pathlib,json,hashlib,shutil,subprocess,os,time,base64,io,tarfile,sys
base=pathlib.Path(BASE);stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT)
if (stage/'CPU-launch.json').exists():
 old=json.loads((stage/'registration.json').read_text())
 assert old['new_payload_sha256']==P['new_payload_sha256'], 'Already launched immutable source differs; inspect original only'
 print((stage/'CPU-launch.json').read_text());sys.exit(0)
assert not (stage/'CPU.log').exists(), 'Unknown started CPU scope; no duplicate submit'
proof=json.loads((base/'CPU-result.json').read_text())
assert proof['status']=='B_SAVED_VELOCITY_SUFFIX3_TWO_FLOW32_PARENTS64_SUFFIXES_CPU_PASS_NOT_GPU'
assert proof['GPU_submissions']==0 and not proof['CUDA_initialized'] and proof['actual_CPU_parents']==32 and proof['endpoint_suffixes']==64
base_reg=json.loads((base/'registration.json').read_text());assert proof['payload_sha256']==base_reg['payload_sha256']
stage.mkdir(exist_ok=True)
for n,h in base_reg['payload_sha256'].items():
 source=base/n;assert hashlib.sha256(source.read_bytes()).hexdigest()==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==h
 else:shutil.copyfile(source,target)
(stage/'base-registration.json').write_text(json.dumps(base_reg,indent=2)+'\n')
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(ARCHIVE)),mode='r:gz') as archive:
 for member in archive.getmembers():
  assert member.isfile() and member.name in P['new_payload_sha256']
  data=archive.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==P['new_payload_sha256'][member.name]
  target=stage/member.name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert hashlib.sha256(target.read_bytes()).hexdigest()==P['new_payload_sha256'][member.name]
  else:target.write_bytes(data)
payload=dict(base_reg['payload_sha256'])
for n,h in P['new_payload_sha256'].items():
 assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
 if n in payload:assert payload[n]==h
 payload[n]=h
reg={'source_revision':P['source_revision'],'payload_sha256':payload,
 'runtime_source_sha256':base_reg['runtime_source_sha256'],'new_payload_sha256':P['new_payload_sha256'],
 'base_source_revision':base_reg['source_revision'],'CPU_only':True,'GPU_execution_selected':False}
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/check_wc_block_saved_reference_cpu_r1.py'),
 '--stage',str(stage),'--project',str(root)]
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
r={'stage':str(stage),'CPU_pid':child.pid,'command':command,'started_unix':time.time(),
 'source_revision':reg['source_revision'],'payload_files':len(payload),'GPU_submissions':0,'ledger_written':False,
 'expected_saved_B_points':4,'live_confirmation_not_inspected_or_modified':True,'registration_sha256':hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()}
(stage/'CPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
    result=json.loads(remote(code))
    (ROOT/'reports'/('wc_block_saved_reference_cpu_'+a.suffix+'_launch_20261013.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
