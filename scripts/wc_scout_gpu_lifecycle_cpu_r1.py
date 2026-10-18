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
BASE_CAPTURE=None

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
 read_only_base_registration_sha256=M['base_sha'],CPU_scope='SCOUT_GPU_LIFECYCLE_OVER_ACCEPTED_ENTRY',scout_kind=M['kind'])
reg['payload_sha256'].update(M['plan']['overlay_sha256'])
raw=(json.dumps(reg,indent=2)+'\n').encode();(stage/'registration.json').write_bytes(raw)
command=[sys.executable,str(stage/'scripts/wc_scout_gpu_lifecycle_cpu_r1.py'),'worker','--project',str(root),'--stage',str(stage),'--kind',M['kind']]
env=dict(os.environ,WC_SCOUT_KIND=M['kind'],CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'scout-lifecycle-CPU.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
from wcomr.gpu_budget_pool_v2 import process_identity
now=time.time();value=dict(status='SCOUT_LIFECYCLE_CPU_SINGLE_DISPATCHED',kind=M['kind'],
 source_revision=M['revision'],stage=str(stage),project=str(root),identity=process_identity(child.pid),command=command,
 registration_sha256=hashlib.sha256(raw).hexdigest(),payload_files=len(reg['payload_sha256']),started_unix=now,
 halfway_not_before_unix=now+180,final_not_before_unix=now+360,GPU_submissions=0,ledger_written=False,GPU_lifecycle_accepted=False)
(stage/'scout-lifecycle-CPU-launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''


def deploy(a):
    assert not a.output.exists();sys.path.insert(0,str(ROOT/'src'));os.environ['WC_SCOUT_KIND']=a.kind
    from wcomr.scout_gpu_lifecycle_r1 import DEPENDENCIES,read,sha,ENTRY_SOURCE
    from wcomr.immutable_stage_payload_r1 import plan,git_archive,registered_base_reference
    prefix='reports/wc_scout_'+a.kind+'_real_entry_CPU_R1_'
    launchref=prefix+'launch_20261018.json';capref=prefix+'collection_20261018.json.gz';acceptedref=prefix+'independent_acceptance_20261018.json'
    base=read(ROOT/capref);reg=base['registration'];saved=read(ROOT/acceptedref)
    spec=__import__('importlib.util',fromlist=['spec_from_file_location'])
    sp=spec.spec_from_file_location('accepted_original_scout_entry',ROOT/'scripts/capture_wc_scout_production_entry_cpu_r1.py')
    module=spec.module_from_spec(sp);sp.loader.exec_module(module);accepted=module.accept(base)
    assert all(saved.get(k)==v for k,v in accepted.items()) and saved['capture_sha256']==sha(ROOT/capref)
    assert reg['source_revision']==ENTRY_SOURCE
    entrypoints=['scripts/wc_scout_gpu_lifecycle_cpu_r1.py','scripts/check_wc_scout_gpu_lifecycle_r1.py',
        'scripts/launch_wc_scout_gpu_r1.py','scripts/supervise_wc_scout_gpu_r1.py','scripts/watch_wc_scout_post_cpu_r1.py',
        'scripts/postprocess_wc_scout_gpu_r1.py','scripts/capture_wc_scout_gpu_r1.py','scripts/analyze_wc_scout_gpu_r1.py',
        'scripts/capture_wc_scout_gpu_lifecycle_cpu_r1.py']
    dep=read(ROOT/DEPENDENCIES[a.kind])
    assert dep['entry_registration_sha256']==base['registration_sha256'] and dep['entry_stage']==reg['stage']
    packet=plan(ROOT,config_roots=[dep['config_ref']],python_entrypoints=entrypoints,
        extra_files=[DEPENDENCIES[a.kind],launchref,capref,acceptedref,'tests/test_scout_gpu_lifecycle_r1.py',
            'scripts/capture_wc_scout_production_entry_cpu_r1.py'],
        base_registration_sha256=base['registration_sha256'],base_source_revision=reg['source_revision'],numeric_sources={})
    changed=[n for n,h in packet['overlay_sha256'].items() if n in reg['payload_sha256'] and reg['payload_sha256'][n]!=h]
    assert not changed,'Accepted execution/entry bytes cannot change: '+str(changed)
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();archive=git_archive(ROOT,packet,rev)
    stage=Path(a.stage);assert not stage.is_absolute() and len(stage.parts)==2 and stage.parts[0]=='.sync'
    assert stage.name.startswith('wc-scout-'+a.kind.lower()+'-gpu-lifecycle-cpu-')
    meta=dict(base=registered_base_reference(reg['stage'],base['launch']['stage'])['original_absolute'],
        base_sha=base['registration_sha256'],stage=str(stage),kind=a.kind,revision=rev,plan=packet)
    code='M='+repr(meta)+'\n'+BOOT
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
            PY+' -c '+shlex.quote(code)],input=archive,capture_output=True,timeout=180)
        value=dict(status='SCOUT_LIFECYCLE_CPU_DISPATCH_RESPONSE',source_revision=rev,kind=a.kind,
            exit_code=call.returncode,launch=json.loads(call.stdout) if call.returncode==0 else None,
            stderr=call.stderr.decode(),stage=str(stage),GPU_submissions=0)
    except (OSError,subprocess.TimeoutExpired,ValueError) as e:
        value=dict(status='SCOUT_LIFECYCLE_CPU_DISPATCH_UNKNOWN_NO_REPLAY',stage=str(stage),source_revision=rev,
            error_type=type(e).__name__,error=str(e),original_recovery_ref=str(stage)+'/scout-lifecycle-CPU-launch.json',GPU_submissions=0)
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(value.get('launch') or value));raise SystemExit(value.get('exit_code',1))


def worker(a):
    os.environ['WC_SCOUT_KIND']=a.kind;sys.path.insert(0,str(a.stage/'src'))
    from wcomr.scout_gpu_lifecycle_r1 import read,sha,CPU_BUNDLE,CPU_PROOF,PATTERNS,dependency_ref
    from wcomr.gpu_budget_pool_v2 import atomic_json
    reg=read(a.stage/'registration.json');assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    commands=[[sys.executable,'-m','unittest','discover','-s',str(a.stage/'tests'),'-p',PATTERNS[0],'-v'],
        [sys.executable,str(a.stage/'scripts/check_wc_scout_gpu_lifecycle_r1.py'),'--project',str(a.project),'--stage',str(a.stage)]]
    value=dict(status='SCOUT_LIFECYCLE_CPU_RUNNING',kind=a.kind,source_revision=reg['source_revision'],
        registration_sha256=sha(a.stage/'registration.json'),commands=[],GPU_submissions=0,ledger_written=False,
        started_unix=__import__('time').time(),unchanged_entry_CPU_reexecuted=False,numerical_paths_reexecuted=0)
    try:
        for command in commands:
            call=subprocess.run(command,cwd=a.project/'runtime',env=dict(os.environ,PYTHONPATH=str(a.stage/'src'),WC_SCOUT_KIND=a.kind))
            value['commands'].append(dict(command=command,exit_code=call.returncode))
            if call.returncode:raise RuntimeError('Scout lifecycle CPU command failed')
        value.update(status='SCOUT_LIFECYCLE_CPU_PASS_REUSING_REAL_ENTRY',exit_code=0,proof_sha256=sha(a.stage/CPU_PROOF))
    except BaseException as e:
        value.update(status='SCOUT_LIFECYCLE_CPU_FAILURE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e));raise
    finally:
        value['CPU_wall_seconds']=__import__('time').time()-value['started_unix'];atomic_json(a.stage/CPU_BUNDLE,value)


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='mode',required=True)
    for mode in ('deploy','worker'):
        q=s.add_parser(mode);q.add_argument('--kind',choices=['CAL12','BANK24'],required=True)
        q.add_argument('--stage',type=Path,required=True)
        q.add_argument('--output' if mode=='deploy' else '--project',type=Path,required=True)
    a=p.parse_args();(deploy if a.mode=='deploy' else worker)(a)


if __name__=='__main__':main()
