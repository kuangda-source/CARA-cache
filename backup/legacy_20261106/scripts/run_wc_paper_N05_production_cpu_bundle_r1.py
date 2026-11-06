#!/usr/bin/env python3
"""Source-verified no-GPU production glue suite; original stages stay read-only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();start=time.time();reg=json.loads((a.stage/'registration.json').read_text())
    assert all(hashlib.sha256((a.stage/n).read_bytes()).hexdigest()==h for n,h in reg['payload_sha256'].items())
    destination=a.stage/'CPU-bundle-result.json';assert not destination.exists()
    commands=[[sys.executable,'-m','unittest','discover','-s',str(a.stage/'tests'),'-p',name,'-v'] for name in (
        'test_paper_baseline_grid_r1.py','test_paper_baseline_production_and_post_r1.py','test_paper_baseline_launch_cpu_r1.py')]
    commands.append([sys.executable,str(a.stage/'scripts/run_wc_paper_N05_core66_r1.py'),'--project',str(a.project),'--stage',str(a.stage),'--cpu-check'])
    state=dict(status='N05_CORE66_COMPLETE_PRODUCTION_CPU_RUNNING',source_revision=reg['source_revision'],commands=[],
        GPU_submissions=0,model_weights_loaded=0,ledger_written=False,shared_runtime_written=False,original_N06_stage_written=False,started_unix=start)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        PYTHONPATH=str(a.stage/'src'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    try:
        for command in commands:
            code=subprocess.call(command,cwd=a.project/'runtime',env=env)
            state['commands'].append(dict(command=command,exit_code=code))
            if code:raise RuntimeError('N05 production CPU command failed: '+str(code))
        state.update(status='N05_CORE66_COMPLETE_PRODUCTION_CPU_PASS_NOT_GPU',exit_code=0)
    except BaseException as error:
        state.update(status='N05_CORE66_PRODUCTION_CPU_FAILED_NOT_GPU',exit_code=1,error_type=type(error).__name__,error=str(error));raise
    finally:state['wall_seconds']=time.time()-start;destination.write_text(json.dumps(state,indent=2)+'\n')

if __name__=='__main__':main()
