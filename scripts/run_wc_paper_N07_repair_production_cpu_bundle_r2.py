#!/usr/bin/env python3
"""Eight original/new controls plus actual Cosmos full180 repair CPU entry."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    args=p.parse_args();sys.path.insert(0,str(args.stage/'src'))
    from wcomr.frozen_repair_cpu_acceptance_r2 import PATTERNS,BUNDLE_WORKER,CPU_BUNDLE_STATUS,WORKER
    from wcomr.frozen_repair180_r2 import sha
    registration=json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/n)==h for n,h in registration['payload_sha256'].items())
    destination=args.stage/'CPU-bundle-result.json';assert not destination.exists()
    commands=[[sys.executable,'-m','unittest','discover','-s',str(args.stage/'tests'),'-p',n,'-v'] for n in PATTERNS]
    commands.append([sys.executable,str(args.stage/WORKER),'--project',str(args.project),'--stage',str(args.stage),'--cpu-check'])
    sources={n:sha(args.stage/n) for n in [BUNDLE_WORKER]+['tests/'+n for n in PATTERNS]}
    state=dict(status='N07_REFUSAL_REPAIR180_PRODUCTION_CPU_RUNNING',source_revision=registration['source_revision'],
        commands=[],stage=str(args.stage),project=str(args.project),python_executable=sys.executable,
        control_source_sha256=sources,started_unix=time.time(),GPU_submissions=0,model_weights_loaded=0,
        ledger_written=False,shared_runtime_written=False,original_base_stage_written=False)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        PYTHONPATH=str(args.stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    try:
        for command in commands:
            code=subprocess.call(command,cwd=args.project/'runtime',env=env)
            state['commands'].append(dict(command=command,exit_code=code))
            if code:raise RuntimeError('Original repair CPU command failed: '+str(code))
        state.update(status=CPU_BUNDLE_STATUS,exit_code=0)
    except BaseException as error:
        state.update(status='N07_REFUSAL_REPAIR180_PRODUCTION_CPU_FAILED',exit_code=1,
            error_type=type(error).__name__,error=str(error));raise
    finally:
        state['wall_seconds']=time.time()-state['started_unix']
        destination.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
