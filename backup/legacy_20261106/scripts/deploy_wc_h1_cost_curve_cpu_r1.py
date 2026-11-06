#!/usr/bin/env python3
"""Immutable CPU-only attribution stage; never inspect or modify live F/B."""
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
BASE='wc-source-fixed-mask-cpu-r1-20261013'
CONFIG='configs/wc_h1_cost_curve_cpu_r1_20261013.json'
NEW=['src/wcomr/h1_cost_curve_batch_r1.py',
 'tests/check_h1_cost_curve_sampling_cpu_r1.py',
 'scripts/check_wc_h1_cost_curve_cpu_r1.py',
 'scripts/deploy_wc_h1_cost_curve_cpu_r1.py',CONFIG,
 'manifests/wc_h1_cost_curve_full60_planning_cost_r1_20261013.json']


def remote(code):
    compile(code,'fixed-mask-cpu-deploy','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--suffix',default='r1');a=p.parse_args()
    if a.suffix not in ('r1','r2','r3'):raise ValueError('Explicit immutable CPU revision required')
    stage=SERVER+'/.sync/wc-h1-cost-curve-cpu-'+a.suffix+'-20261013'
    config=json.loads((ROOT/CONFIG).read_text());names=NEW+list(config['source_sha256'])
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
assert proof['status']=='SOURCE_PHASE_FIXED_MASK_TWO_FLOW_FULL80_CPU_PASS_NOT_GPU'
assert proof['actual_CPU_paths']==80 and proof['GPU_submissions']==0 and not proof['CUDA_initialized']
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
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/check_wc_h1_cost_curve_cpu_r1.py'),
 '--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(stage/'CPU-result.json')]
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
r={'stage':str(stage),'CPU_pid':child.pid,'command':command,'started_unix':time.time(),
 'source_revision':reg['source_revision'],'payload_files':len(payload),'GPU_submissions':0,'ledger_written':False,
 'expected_CPU_paths':160,'live_FB_not_inspected_or_modified':True,'registration_sha256':hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()}
(stage/'CPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
    result=json.loads(remote(code))
    (ROOT/'reports'/('wc_h1_cost_curve_cpu_'+a.suffix+'_launch_20261013.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
