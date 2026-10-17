#!/usr/bin/env python3
"""Immutable complete88 numerical CPU preparation, never a GPU production proof."""
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

ROOT = Path(__file__).resolve().parents[1]
PROJECT = '/home/gaokuangda/data/gkd/worldcache_omr'
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
BASE = '.sync/wc-drop1-production-r1-20261017'
BASE_SHA = '2532bde9cc5ba858ac3018f3bbe82e88be2e459b8e5e985734c78659f42bc134'
FILES = ('scripts/wc_drop1_window88_cpu_r1.py',
    'scripts/capture_wc_drop1_window88_cpu_r1.py',
    'scripts/check_wc_drop1_correction_window88_cpu_r1.py',
    'src/wcomr/drop1_correction_window24_r1.py',
    'tests/check_drop1_correction_window88_sampling_cpu_r1.py',
    'tests/test_drop1_correction_window24_r1.py',
    'manifests/wc_drop1_correction_window_full24_static_scope_20261018.json',
    'plans/WC_DROP1_CORRECTION_WINDOW_FULL24_20261018.md',
    'plans/WC_DROP1_WINDOW88_CPU_RESOURCE_WAIT_ORDER_20261018.md',
    'reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz',
    'reports/wc_drop1_complete_results_analysis_20261018.json',
    'reports/wc_drop1_correction_window24_adapter_full88_entry_local_CPU_r2_20261018.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as h:
        json.dump(value, h, indent=2, allow_nan=False);h.write('\n')


def remote(code, payload=None):
    call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',
        '-o','ClearAllForwardings=yes','gkd_minchen',PYTHON+' -c '+shlex.quote(code)],
        input=payload, capture_output=True, timeout=120)
    if call.returncode:
        raise RuntimeError(call.stderr.decode())
    return call.stdout


BOOT = r'''
import hashlib,io,json,os,pathlib,shutil,subprocess,sys,tarfile,time
root=pathlib.Path(M['project']).resolve();base=root/M['base'];stage=root/M['stage']
assert not stage.exists(),'Never overwrite a CPU or GPU stage'
regpath=base/'registration.json'
assert hashlib.sha256(regpath.read_bytes()).hexdigest()==M['base_sha']
reg=json.loads(regpath.read_text());assert reg['source_revision']=='e76b4f8b934bb07bf045e6083f36eddb4711640d'
assert not set(M['overlay'])&set(reg['payload_sha256']),'No inherited numerical file may be overwritten'
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
assert not any(v['status']=='RESERVED_OR_RUNNING' for v in pool['jobs'].values()),'Do not disturb actual GPU timing'
stage.mkdir()
for n,h in reg['payload_sha256'].items():
 src=base/n;raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
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
 read_only_base_registration_sha256=M['base_sha'],CPU_scope='CORRECTION_WINDOW_COMPLETE88_NUMERICAL_ONLY_NOT_PRODUCTION')
reg['payload_sha256'].update(M['overlay'])
raw=(json.dumps(reg,indent=2)+'\n').encode();(stage/'registration.json').write_bytes(raw)
command=[sys.executable,str(stage/'scripts/wc_drop1_window88_cpu_r1.py'),'worker','--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONPATH=str(stage/'src'))
with (stage/'CPU-window88.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
fields=(pathlib.Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split();now=time.time()
value=dict(status='CORRECTION_WINDOW_FULL88_NUMERICAL_CPU_SINGLE_DISPATCHED',source_revision=M['revision'],stage=str(stage),pid=child.pid,start_ticks=int(fields[19]),command=command,registration_sha256=hashlib.sha256(raw).hexdigest(),payload_files=len(reg['payload_sha256']),started_unix=now,halfway_not_before_unix=now+360,final_not_before_unix=now+720,registered_CPU_paths=88,production_CPU_accepted=False,GPU_submissions=0,ledger_written=False)
(stage/'CPU-window88-launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''


def deploy(a):
    if a.output.exists():raise ValueError('Original dispatch receipt exists; never relaunch')
    path = Path(a.stage)
    if path.is_absolute() or len(path.parts)!=2 or path.parts[0]!='.sync' or '..' in path.parts or not path.name.startswith('wc-drop1-window88-cpu-'):
        raise ValueError('Fresh independent CPU-only stage required')
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    stream=io.BytesIO();overlay={}
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for name in FILES:
            raw=(ROOT/name).read_bytes()
            if subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)!=raw:
                raise ValueError('Commit all CPU source and references before staging: '+name)
            overlay[name]=hashlib.sha256(raw).hexdigest()
            member=tarfile.TarInfo(name);member.size=len(raw);archive.addfile(member,io.BytesIO(raw))
    meta=dict(project=PROJECT,base=BASE,base_sha=BASE_SHA,stage=str(path),revision=revision,overlay=overlay)
    try:
        value=dict(status='CPU_WINDOW88_DISPATCH_RESPONSE',launch=json.loads(remote('M='+repr(meta)+'\n'+BOOT,stream.getvalue())),overlay=overlay)
    except Exception as error:
        write(a.output,dict(status='CPU_WINDOW88_TRANSPORT_UNKNOWN_NO_AUTOMATIC_RETRY',source_revision=revision,stage=str(path),error_type=type(error).__name__,error=str(error),GPU_submissions=0))
        raise
    write(a.output,value);print(json.dumps(value['launch']))


def worker(a):
    stage=Path(a.stage);reg=json.loads((stage/'registration.json').read_text())
    assert all(sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    commands=[
        [sys.executable,str(stage/'scripts/check_wc_drop1_correction_window88_cpu_r1.py'),'--stage',str(stage),'--runtime',str(a.project/'runtime'),'--output',str(stage/'window88-numerical-CPU-result.json')],
        [sys.executable,'-m','unittest','discover','-s',str(stage/'tests'),'-p','test_drop1_correction_window24_r1.py','-v'],
        [sys.executable,'-m','unittest','discover','-s',str(stage/'tests'),'-p','test_drop1_full18_r1.py','-v']]
    value=dict(status='CPU_WINDOW88_RUNNING',source_revision=reg['source_revision'],commands=[],started_unix=time.time(),GPU_submissions=0,ledger_written=False,production_CPU_accepted=False)
    try:
        for cmd in commands:
            code=subprocess.call(cmd,cwd=a.project/'runtime',env=os.environ)
            value['commands'].append(dict(command=cmd,exit_code=code))
            if code:raise RuntimeError('Full CPU command failed: '+str(code))
        value.update(status='CPU_WINDOW88_COMPLETE_NOT_PRODUCTION_OR_GPU',exit_code=0)
    except BaseException as error:
        value.update(status='CPU_WINDOW88_FAILURE_RETAINED_NOT_PRODUCTION_OR_GPU',exit_code=1,error_type=type(error).__name__,error=str(error));raise
    finally:
        value['wall_seconds']=time.time()-value['started_unix'];write(stage/'CPU-window88-result.json',value)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    d=sub.add_parser('deploy');d.add_argument('--stage',required=True);d.add_argument('--output',type=Path,required=True)
    w=sub.add_parser('worker');w.add_argument('--stage',type=Path,required=True);w.add_argument('--project',type=Path,required=True)
    a=p.parse_args()
    if a.mode=='deploy':deploy(a)
    else:worker(a)


if __name__=='__main__':main()
