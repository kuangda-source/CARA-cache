#!/usr/bin/env python3
"""Separate immutable real-entry CPU stages; this cannot launch a GPU job."""
import argparse
import gzip
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
BASE_CAPTURE='reports/wc_scout_numeric248_actual_CPU_R2_collection_20261018.json.gz'

BOOT=r'''
import hashlib,io,json,os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve();base=pathlib.Path(M['base']);stage=root/M['stage']
assert not stage.exists() and base.parent==stage.parent
raw=(base/'registration.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==M['base_sha']
reg=json.loads(raw)
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
assert not any(v['status']=='RESERVED_OR_RUNNING' and k.startswith(('wc-paper-n09-','wc-paper-n10-')) for k,v in pool['jobs'].items())
sys.path.insert(0,str(base/'src'))
from wcomr.immutable_stage_payload_r1 import overlay_bytes
extra=overlay_bytes(sys.stdin.buffer.read(),M['plan'])
assert all(n not in reg['payload_sha256'] or hashlib.sha256(v).hexdigest()==reg['payload_sha256'][n] for n,v in extra.items())
stage.mkdir()
for n,h in reg['payload_sha256'].items():
 data=(base/n).read_bytes();assert hashlib.sha256(data).hexdigest()==h
 p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
for n,data in extra.items():
 p=stage/n
 if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
reg.update(source_revision=M['revision'],stage=str(stage),read_only_base_stage=str(base),
 read_only_base_registration_sha256=M['base_sha'],CPU_scope='SCOUT_REAL_PRODUCTION_ENTRY_NOT_GPU_LIFECYCLE',scout_kind=M['kind'])
reg['payload_sha256'].update(M['plan']['overlay_sha256'])
raw=(json.dumps(reg,indent=2)+'\n').encode();(stage/'registration.json').write_bytes(raw)
command=[sys.executable,str(stage/'scripts/wc_scout_production_entry_cpu_r1.py'),'worker','--project',str(root),'--stage',str(stage),'--kind',M['kind']]
env=dict(os.environ,WC_SCOUT_KIND=M['kind'],CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'scout-entry-CPU.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
from wcomr.gpu_budget_pool_v2 import process_identity
now=time.time();value=dict(status='SCOUT_REAL_ENTRY_CPU_SINGLE_DISPATCHED_NOT_GPU_LIFECYCLE',kind=M['kind'],
 source_revision=M['revision'],stage=str(stage),project=str(root),identity=process_identity(child.pid),command=command,
 registration_sha256=hashlib.sha256(raw).hexdigest(),payload_files=len(reg['payload_sha256']),started_unix=now,
 halfway_not_before_unix=now+180,final_not_before_unix=now+360,GPU_submissions=0,ledger_written=False,GPU_lifecycle_accepted=False)
(stage/'scout-entry-CPU-launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''


def deploy(a):
    assert not a.output.exists();sys.path.insert(0,str(ROOT/'src'));os.environ['WC_SCOUT_KIND']=a.kind
    from wcomr import scout_production_entry_r1 as entry
    from wcomr.immutable_stage_payload_r1 import plan,git_archive,registered_base_reference
    raw=(ROOT/BASE_CAPTURE).read_bytes();base=json.loads(gzip.decompress(raw));reg=base['registration']
    spec=__import__('importlib.util',fromlist=['spec_from_file_location'])
    s=spec.spec_from_file_location('accepted_scout_R2',ROOT/'scripts/capture_wc_scout_numeric248_cpu_r1.py');m=spec.module_from_spec(s);s.loader.exec_module(m)
    accepted=m.accept(base);saved=json.loads((ROOT/entry.REFERENCES['numeric_acceptance']).read_text())
    assert accepted['guard_refusal_controls']==10 and all(saved.get(k)==v for k,v in accepted.items())
    packet=plan(ROOT,config_roots=[entry.CONFIG],python_entrypoints=[
        'scripts/wc_scout_production_entry_cpu_r1.py','scripts/run_wc_scout_production_entry_r1.py',
        'scripts/capture_wc_scout_production_entry_cpu_r1.py'],extra_files=[
        'tests/test_scout_production_entry_r1.py','scripts/run_wc_drop1_full18_r1.py',
        'scripts/capture_wc_scout_numeric248_cpu_r1.py'],
        base_registration_sha256=base['registration_sha256'],base_source_revision=reg['source_revision'],numeric_sources={})
    changed=[n for n,h in packet['overlay_sha256'].items() if n in reg['payload_sha256'] and reg['payload_sha256'][n]!=h]
    assert not changed,'Do not alter accepted numerical source: '+str(changed)
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();archive=git_archive(ROOT,packet,rev)
    stage=Path(a.stage);assert not stage.is_absolute() and len(stage.parts)==2 and stage.parts[0]=='.sync'
    assert stage.name.startswith('wc-scout-'+a.kind.lower()+'-production-entry-cpu-')
    meta=dict(base=registered_base_reference(reg['stage'],base['launch']['stage'])['original_absolute'],
        base_sha=base['registration_sha256'],stage=str(stage),kind=a.kind,revision=rev,plan=packet)
    code='M='+repr(meta)+'\n'+BOOT
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
            PY+' -c '+shlex.quote(code)],input=archive,capture_output=True,timeout=180)
        value=dict(status='SCOUT_REAL_ENTRY_CPU_DISPATCH_RESPONSE',source_revision=rev,kind=a.kind,
            exit_code=call.returncode,launch=json.loads(call.stdout) if call.returncode==0 else None,
            stderr=call.stderr.decode(),stage=str(stage),GPU_submissions=0)
    except (OSError,subprocess.TimeoutExpired,ValueError) as e:
        value=dict(status='SCOUT_ENTRY_CPU_DISPATCH_UNKNOWN_NO_REPLAY',stage=str(stage),source_revision=rev,
            error_type=type(e).__name__,error=str(e),original_recovery_ref=str(stage)+'/scout-entry-CPU-launch.json',GPU_submissions=0)
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(value.get('launch') or value));raise SystemExit(value.get('exit_code',1))


def worker(a):
    os.environ['WC_SCOUT_KIND']=a.kind;sys.path.insert(0,str(a.stage/'src'))
    from wcomr import scout_production_entry_r1 as entry
    sha=lambda p:__import__('hashlib').sha256(p.read_bytes()).hexdigest()
    reg=json.loads((a.stage/'registration.json').read_text())
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    commands=[[sys.executable,'-m','unittest','discover','-s',str(a.stage/'tests'),'-p','test_scout_production_entry_r1.py','-v'],
        [sys.executable,str(a.stage/'scripts/run_wc_scout_production_entry_r1.py'),'--project',str(a.project),'--stage',str(a.stage),'--cpu-check']]
    value=dict(status='SCOUT_ENTRY_CPU_RUNNING',kind=a.kind,source_revision=reg['source_revision'],
        registration_sha256=sha(a.stage/'registration.json'),config_sha256=sha(a.stage/entry.CONFIG),commands=[],
        GPU_submissions=0,ledger_written=False,GPU_lifecycle_accepted=False,started_unix=__import__('time').time())
    try:
        for command in commands:
            call=subprocess.run(command,cwd=a.project/'runtime',env=dict(os.environ,PYTHONPATH=str(a.stage/'src'),WC_SCOUT_KIND=a.kind))
            value['commands'].append(dict(command=command,exit_code=call.returncode))
            if call.returncode:raise RuntimeError('Actual scout entry CPU command failed')
        value.update(status='SCOUT_REAL_PRODUCTION_ENTRY_CPU_BUNDLE_PASS_NOT_GPU_LIFECYCLE',exit_code=0,
            proof_sha256=sha(a.stage/entry.CPU_RESULT))
    except BaseException as e:
        value.update(status='SCOUT_ENTRY_CPU_FAILURE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e));raise
    finally:
        value['CPU_wall_seconds']=__import__('time').time()-value['started_unix']
        with (a.stage/'scout-entry-CPU-bundle.json').open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='mode',required=True)
    for mode in ('deploy','worker'):
        q=s.add_parser(mode);q.add_argument('--kind',choices=['CAL12','BANK24'],required=True)
        q.add_argument('--stage',type=Path,required=True)
        q.add_argument('--output' if mode=='deploy' else '--project',type=Path,required=True)
    a=p.parse_args();(deploy if a.mode=='deploy' else worker)(a)


if __name__=='__main__':main()
