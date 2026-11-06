#!/usr/bin/env python3
"""Immutable CPU-only attribution stage; never inspect or modify live F/B."""
import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SERVER='/home/gaokuangda/data/gkd/worldcache_omr'
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
BASE='wc-source-confirmation-production-r1-20261013'
CONFIG='configs/wc_source_phase_fixed_mask_cpu_r1_20261013.json'
NEW=['src/wcomr/source_phase_fixed_mask_r1.py',
 'tests/check_source_phase_fixed_mask_sampling_cpu_r1.py',
 'scripts/check_wc_source_phase_fixed_mask_cpu_r1.py',
 'scripts/deploy_wc_source_fixed_mask_cpu_r1.py',CONFIG]


def remote(code):
    compile(code,'fixed-mask-cpu-deploy','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--suffix',default='r1');a=p.parse_args()
    if a.suffix not in ('r1','r2','r3'):raise ValueError('Explicit immutable CPU revision required')
    stage=SERVER+'/.sync/wc-source-fixed-mask-cpu-'+a.suffix+'-20261013'
    config=json.loads((ROOT/CONFIG).read_text());names=NEW+list(config['source_sha256'])
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    packet={'source_revision':rev,'new_payload_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}}
    for n,h in packet['new_payload_sha256'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)).hexdigest()==h
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as tar:
        for n in names:tar.add(ROOT/n,arcname=n)
    code='BASE='+repr(SERVER+'/.sync/'+BASE)+'\nSTAGE='+repr(stage)+'\n'+r'''import pathlib,json,hashlib,shutil
base=pathlib.Path(BASE);stage=pathlib.Path(STAGE);assert not stage.exists()
proof=json.loads((base/'production-CPU-result.json').read_text())
assert proof['status']=='SOURCE_CONFIRMATION_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
assert proof['registration_sha256']==hashlib.sha256((base/'registration.json').read_bytes()).hexdigest()
reg=json.loads((base/'registration.json').read_text());stage.mkdir()
for n,h in reg['payload_sha256'].items():
 source=base/n;assert hashlib.sha256(source.read_bytes()).hexdigest()==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
(stage/'base-registration.json').write_text(json.dumps(reg,indent=2)+'\n')
print(json.dumps({'status':'IMMUTABLE_HELPERS_COPIED_NOT_NEW_MASK_CPU_ACCEPTANCE','files':len(reg['payload_sha256'])}))
'''
    print(remote(code).strip())
    subprocess.run(HOST+['tar -xzf - -C '+stage],input=buf.getvalue(),check=True)
    code='P='+repr(packet)+'\nSTAGE='+repr(stage)+'\nROOT='+repr(SERVER)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);base=json.loads((stage/'base-registration.json').read_text())
payload=dict(base['payload_sha256'])
for n,h in P['new_payload_sha256'].items():
 assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
 if n in payload:assert payload[n]==h
 payload[n]=h
reg={'source_revision':P['source_revision'],'payload_sha256':payload,
 'runtime_source_sha256':base['runtime_source_sha256'],'new_payload_sha256':P['new_payload_sha256'],
 'base_source_revision':base['source_revision'],'CPU_only':True,'GPU_execution_selected':False}
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/check_wc_source_phase_fixed_mask_cpu_r1.py'),
 '--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(stage/'CPU-result.json')]
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
r={'stage':str(stage),'CPU_pid':child.pid,'command':command,'started_unix':time.time(),
 'source_revision':reg['source_revision'],'payload_files':len(payload),'GPU_submissions':0,'ledger_written':False,
 'expected_CPU_paths':80,'live_FB_not_inspected_or_modified':True,'registration_sha256':hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()}
(stage/'CPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
    result=json.loads(remote(code))
    (ROOT/'reports'/('wc_source_fixed_mask_cpu_'+a.suffix+'_launch_20261013.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
