#!/usr/bin/env python3
"""Immutable two-scout numerical preparation, separate from production acceptance."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
PROJECT='/home/gaokuangda/data/gkd/worldcache_omr'
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
BASE_LAUNCH='reports/wc_drop1_window24_actual_production_CPU_R1_launch_20261018.json'
FILES=('scripts/wc_scout_numeric248_cpu_r1.py','scripts/check_wc_scout_sampling_cpu_r1.py',
       'scripts/capture_wc_scout_numeric248_cpu_r1.py','src/wcomr/scout_sampling_r1.py',
       'src/wcomr/scout_numeric_contract_r1.py','tests/check_scout_full_sampling_cpu_r1.py',
       'plans/scouts_20261018/SCOUT_CAL12_CARD.json','plans/scouts_20261018/SCOUT_DEV6_BANK24_CARD.json',
       'plans/WC_SCOUT_NUMERIC248_AND_PRODUCTION_ORDER_20261018.md')

BOOT=r'''
import hashlib,io,json,os,pathlib,shutil,subprocess,sys,tarfile,time
root=pathlib.Path(M['project']).resolve();base=pathlib.Path(M['base']);stage=root/M['stage']
assert base.parent==stage.parent and not stage.exists()
oldreg=(base/'registration.json').read_bytes();assert hashlib.sha256(oldreg).hexdigest()==M['base_sha']
reg=json.loads(oldreg)
assert not set(M['overlay'])&set(reg['payload_sha256']),'New scout files cannot overwrite old source bytes'
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
assert not any(v['status']=='RESERVED_OR_RUNNING' for v in pool['jobs'].values()),'Defer CPU during GPU measurement'
stage.mkdir()
for n,h in reg['payload_sha256'].items():
 raw=(base/n).read_bytes();assert hashlib.sha256(raw).hexdigest()==h
 dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
seen=set()
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz') as archive:
 for member in archive:
  n=pathlib.PurePosixPath(member.name)
  assert member.isfile() and not n.is_absolute() and '..' not in n.parts
  assert member.name in M['overlay'] and member.name not in seen
  raw=archive.extractfile(member).read();assert hashlib.sha256(raw).hexdigest()==M['overlay'][member.name]
  dst=stage/member.name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);seen.add(member.name)
assert seen==set(M['overlay'])
reg.update(source_revision=M['revision'],stage=str(stage),read_only_base_stage=str(base),
 read_only_base_registration_sha256=M['base_sha'],CPU_scope='SCOUT_COMPLETE248_NUMERICAL_NOT_PRODUCTION')
reg['payload_sha256'].update(M['overlay'])
raw=(json.dumps(reg,indent=2)+'\n').encode();(stage/'registration.json').write_bytes(raw)
command=[sys.executable,str(stage/'scripts/wc_scout_numeric248_cpu_r1.py'),'worker','--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONPATH=str(stage/'src'))
with (stage/'CPU-scout248.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
now=time.time();v=dict(status='SCOUT_COMPLETE248_NUMERICAL_CPU_SINGLE_DISPATCHED',source_revision=M['revision'],stage=str(stage),
 project=str(root),identity=process_identity(child.pid),command=command,registration_sha256=hashlib.sha256(raw).hexdigest(),
 payload_files=len(reg['payload_sha256']),started_unix=now,halfway_not_before_unix=now+900,final_not_before_unix=now+1800,
 registered_CPU_paths=248,production_CPU_accepted=False,GPU_submissions=0,ledger_written=False)
(stage/'CPU-scout248-launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''


def deploy(a):
    assert not a.output.exists()
    launch=json.loads((ROOT/BASE_LAUNCH).read_text())['launch']
    accepted=json.loads((ROOT/'reports/wc_drop1_window24_actual_production_CPU_R1_independent_acceptance_20261018.json').read_text())
    assert accepted['CPU_accepted'] and accepted['registration_sha256']==launch['registration_sha256']
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    stream=io.BytesIO();overlay={}
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for name in FILES:
            raw=(ROOT/name).read_bytes()
            assert raw==subprocess.check_output(['git','show',rev+':'+name],cwd=ROOT)
            overlay[name]=hashlib.sha256(raw).hexdigest();member=tarfile.TarInfo(name);member.size=len(raw)
            archive.addfile(member,io.BytesIO(raw))
    stage=Path(a.stage)
    assert not stage.is_absolute() and len(stage.parts)==2 and stage.parts[0]=='.sync' and stage.name.startswith('wc-scout-numeric248-cpu-')
    meta=dict(project=PROJECT,base=launch['stage'],base_sha=launch['registration_sha256'],stage=str(stage),revision=rev,overlay=overlay)
    code='M='+repr(meta)+'\n'+BOOT
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],
            input=stream.getvalue(),capture_output=True,timeout=150)
    except (OSError,subprocess.TimeoutExpired) as e:
        unknown=dict(status='SCOUT248_CPU_DISPATCH_UNKNOWN_NO_AUTOMATIC_REPLAY',stage=str(stage),source_revision=rev,
            error_type=type(e).__name__,error=str(e),original_task_terminal=False,
            original_recovery_ref=str(stage)+'/CPU-scout248-launch.json',GPU_submissions=0,ledger_written=False)
        with a.output.open('x') as h:json.dump(unknown,h,indent=2);h.write('\n')
        raise
    result=dict(status='SCOUT_NUMERICAL_CPU_DISPATCH_RESPONSE',source_revision=rev,stage=str(stage),
        exit_code=call.returncode,stdout=call.stdout.decode(),stderr=call.stderr.decode(),GPU_submissions=0,ledger_written=False)
    try:result['launch']=json.loads(call.stdout)
    except ValueError:result['launch']=None
    with a.output.open('x') as h:json.dump(result,h,indent=2);h.write('\n')
    print(json.dumps(result['launch'] or result));raise SystemExit(call.returncode)


def worker(a):
    stage=a.stage.resolve();reg=json.loads((stage/'registration.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    result=dict(status='SCOUT248_NUMERICAL_CPU_RUNNING',source_revision=reg['source_revision'],commands=[],
        GPU_submissions=0,ledger_written=False,production_CPU_accepted=False,started_unix=time.time())
    commands=[]
    for kind in ('CAL12','BANK24'):
        commands.append([sys.executable,str(stage/'scripts/check_wc_scout_sampling_cpu_r1.py'),'--kind',kind,
            '--stage',str(stage),'--runtime',str(a.project/'runtime'),'--output',str(stage/('scout-'+kind+'-sampling-CPU-result.json'))])
    try:
        for command in commands:
            call=subprocess.run(command,cwd=a.project/'runtime',env=dict(os.environ,PYTHONPATH=str(stage/'src')))
            result['commands'].append(dict(command=command,exit_code=call.returncode))
            if call.returncode:raise RuntimeError('Scout numerical CPU command failed')
        proofs=[json.loads((stage/('scout-'+k+'-sampling-CPU-result.json')).read_text()) for k in ('CAL12','BANK24')]
        assert [x['actual_CPU_paths'] for x in proofs]==[80,168]
        result.update(status='SCOUT_COMPLETE248_NUMERICAL_CPU_PASS_NOT_PRODUCTION',exit_code=0,actual_CPU_paths=248,
            result_sha256={k:sha(stage/('scout-'+k+'-sampling-CPU-result.json')) for k in ('CAL12','BANK24')})
    except BaseException as e:
        result.update(status='SCOUT248_NUMERICAL_CPU_FAILURE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e));raise
    finally:
        result['wall_seconds']=time.time()-result['started_unix']
        with (stage/'CPU-scout248-result.json').open('x') as h:json.dump(result,h,indent=2);h.write('\n')


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    d=sub.add_parser('deploy');d.add_argument('--stage',required=True);d.add_argument('--output',type=Path,required=True)
    w=sub.add_parser('worker');w.add_argument('--stage',type=Path,required=True);w.add_argument('--project',type=Path,required=True)
    a=p.parse_args();(deploy if a.mode=='deploy' else worker)(a)


if __name__=='__main__':main()
