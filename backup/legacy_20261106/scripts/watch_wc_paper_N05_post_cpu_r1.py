#!/usr/bin/env python3
"""Run CPU postprocessing after this exact supervisor; never restart it."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--supervisor-pid',type=int,required=True);p.add_argument('--supervisor-start-ticks',type=int,required=True)
    a=p.parse_args();assert a.supervisor_pid>0
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    from wcomr.gpu_budget_pool_v2 import same_live_process
    from wcomr.paper_baseline_production_r1 import RUN,COUNTS,write
    identity=dict(pid=a.supervisor_pid,start_ticks=a.supervisor_start_ticks)
    while same_live_process(identity):time.sleep(10)
    root=a.project/'outputs'/RUN;receipt=dict(status='N05_CORE66_POST_CPU_TERMINAL',GPU_submissions=0,ledger_written=False,
        original_supervisor=identity,scope_counts=COUNTS,exit_code=None)
    try:
        supervisor=json.loads((root/'supervisor.json').read_text())
        assert supervisor['pid']==a.supervisor_pid and supervisor['status']=='N05_CORE66_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
        command=[sys.executable,str(a.stage/'scripts/postprocess_wc_paper_N05_core66_r1.py'),'--project',str(a.project),'--stage',str(a.stage)]
        receipt['command']=command
        with (a.stage/'post-CPU.log').open('x') as log:
            receipt['exit_code']=subprocess.call(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    except BaseException as error:
        receipt.update(exit_code=1,error_type=type(error).__name__,error=str(error));raise
    finally:receipt['ended_unix']=time.time();write(a.stage/'post-CPU-exit.json',receipt)

if __name__=='__main__':main()
