#!/usr/bin/env python3
"""Same full76 method; independently check required pre-load wrapper assets."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e2_execution_r1 import sha,write,validate_execution,binding
    c=json.loads((args.stage/'e2-config.json').read_text())
    p=json.loads((args.stage/'execution-protocol.json').read_text())
    reg=json.loads((args.stage/'registration.json').read_text())
    assert not c['GPU_execution_selected'] and binding(c)==reg['method_config_binding_sha256']
    assert p['execution_payload_sha256']==reg['execution_payload_sha256']
    required=reg['required_startup_assets']
    assert len(required)==2 and all(p['execution_payload_sha256'][n]==h for n,h in required.items())
    validate_execution(c,p,args.stage)
    target=args.stage/'startup-CPU-receipt.json';assert not target.exists()
    r={'status':'E2_STARTUP_WRAPPER_R2_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
       'source_revision':args.source_revision,'started_unix':time.time(),
       'config_binding_sha256':binding(c),'execution_protocol_sha256':sha(args.stage/'execution-protocol.json'),
       'registration_sha256':sha(args.stage/'registration.json'),
       'budget_before_sha256':sha(args.project/'reports/budget.json'),'GPU_submissions':0,'ledger_written':False}
    write(target,r);start=time.perf_counter()
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(args.project/'hfhub'),
        OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    try:
        # This is the exact hash validator called by the observed production
        # entry before model loading. Mutations occur only in a private copy.
        refusals=[]
        with tempfile.TemporaryDirectory(prefix='E2_STARTUP_R2_CPU_') as folder:
            copy=Path(folder)
            for n in p['execution_payload_sha256']:
                (copy/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.stage/n,copy/n)
            validate_execution(c,p,copy)
            for n in required:
                path=copy/n;original=path.read_bytes()
                for action in ('missing','changed'):
                    if action=='missing':path.unlink()
                    else:path.write_bytes(original+b'CHANGED_CPU_CONTROL')
                    try:validate_execution(c,p,copy)
                    except (ValueError,FileNotFoundError):refusals.append({'asset':n,'control':action})
                    else:raise AssertionError('Changed required startup asset admitted')
                    path.write_bytes(original)
        assert len(refusals)==4
        command=['python3',str(args.stage/'scripts/check_wc_e2_execution_cpu_r1.py'),
                 '--project',str(args.project),'--stage',str(args.stage),'--source-revision',args.source_revision]
        with (args.stage/'startup-wrapper-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',env=env)
            r.update(child_pid=child.pid,current_command=command);write(target,r)
            r['wrapper_child_exit_code']=child.wait()
        assert r['wrapper_child_exit_code']==0
        wrapper=json.loads((args.stage/'execution-CPU-receipt.json').read_text())
        assert wrapper['exit_code']==0 and wrapper['pid']==r['child_pid']
        assert wrapper['config_binding_sha256']==binding(c) and not wrapper['CUDA_initialized']
        mode_ref='manifests/wc_h0_eval_mode_contract_20261003.json'
        meta_command=[python,str(args.stage/'scripts/check_wc_h0_native_mode_cpu.py'),
                      '--runtime',str(args.project/'runtime'),'--contract',str(args.stage/mode_ref)]
        with (args.stage/'native-mode-meta-CPU.log').open('x') as log:
            child=subprocess.Popen(meta_command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                env=dict(env,PYTHONPATH=str(args.stage/'src')))
            r.update(meta_child_pid=child.pid,current_command=meta_command);write(target,r)
            r['meta_child_exit_code']=child.wait()
        assert r['meta_child_exit_code']==0
        modes=[]
        for line in (args.stage/'native-mode-meta-CPU.log').read_text().splitlines():
            try:v=json.loads(line)
            except ValueError:continue
            if isinstance(v,dict) and v.get('status')=='ACTUAL_NATIVE_META_DEFAULT_MODE_AND_SHARED_EVAL_STARTUP_CPU_PASS':modes.append(v)
        assert len(modes)==1;mode=modes[0]
        assert mode['parameter_count']==2059174912 and mode['mode']['before']['module_count']==1173
        assert mode['mode']['before']['training_modules']==1173 and mode['mode']['after']['training_modules']==0
        assert mode['contract_sha256']==required[mode_ref]
        assert not mode['cuda_initialized'] and not mode['weights_loaded'] and not mode['forward_executed']
        r.update(status='E2_STARTUP_WRAPPER_R2_CPU_PASS_NOT_GPU',exit_code=0,CUDA_initialized=False,
            required_startup_asset_refusals=refusals,native_mode_meta_CPU_result=mode,
            original_execution_CPU_receipt_sha256=sha(args.stage/'execution-CPU-receipt.json'),
            original_execution_CPU_result_sha256=sha(args.stage/'execution-CPU-result.json'))
    except BaseException as error:
        r.update(status='E2_STARTUP_WRAPPER_R2_CPU_FAILED_SCOPE_RETAINED',exit_code=1,
                 error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            budget_after_sha256=sha(args.project/'reports/budget.json'),
            method_payload_after_sha256={n:sha(args.stage/n) for n in c['payload_sha256']},
            execution_payload_after_sha256={n:sha(args.stage/n) for n in p['execution_payload_sha256']})
        if (r['budget_before_sha256']!=r['budget_after_sha256'] or r['method_payload_after_sha256']!=c['payload_sha256']
                or r['execution_payload_after_sha256']!=p['execution_payload_sha256']
                or sha(args.stage/'execution-protocol.json')!=r['execution_protocol_sha256']
                or sha(args.stage/'registration.json')!=r['registration_sha256']):
            r.update(status='E2_STARTUP_WRAPPER_R2_CPU_IDENTITY_CHANGED_NOT_PASS',exit_code=1)
        write(target,r)
    print(json.dumps({k:r[k] for k in ('status','exit_code','CPU_wall_seconds','GPU_submissions')}))
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
