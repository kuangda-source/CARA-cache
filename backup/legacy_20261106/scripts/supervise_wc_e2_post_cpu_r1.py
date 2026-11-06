#!/usr/bin/env python3
"""Follow the single original GPU handle, then audit and score on CPU."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--original-supervisor-pid',type=int,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e2_execution_r1 import RUN,sha,write
    target=args.stage/'post-CPU-receipt.json';assert not target.exists()
    r={'status':'WAITING_ORIGINAL_E2_GPU_SUPERVISOR','pid':os.getpid(),'source_revision':args.source_revision,
        'original_supervisor_pid':args.original_supervisor_pid,'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}
    write(target,r);start=time.perf_counter()
    try:
        while Path('/proc/'+str(args.original_supervisor_pid)).exists():time.sleep(3)
        gpu=json.loads((args.project/'outputs'/RUN/'supervisor.json').read_text())
        assert gpu['pid']==args.original_supervisor_pid and gpu['exit_code']==0
        assert not Path('/proc/'+str(gpu['child_pid'])).exists()
        r.update(status='E2_RELEASED_GPU_COMPLETE_CPU_AUDIT_AND_SCORE_RUNNING',budget_before_sha256=sha(args.project/'reports/budget.json'));write(target,r)
        command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
            str(args.stage/'scripts/postprocess_wc_e2_full76_cpu_r1.py'),'--project',str(args.project),'--stage',str(args.stage)]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (args.stage/'post-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
            r.update(child_pid=child.pid,command=command);write(target,r);r['child_exit_code']=child.wait()
        assert r['child_exit_code']==0
        result=json.loads((args.stage/'score-result.json').read_text())
        assert result['status']=='E2_FULL76_ALL_AVAILABLE93_CPU_SCORE_COMPLETE_NOT_AUTOMATIC_METHOD_ACCEPTANCE'
        assert result['summary']['scored_pairs']==sum(p['status']=='PAIRED' for p in result['pairs_all68'])
        r.update(status='E2_COMPLETE_RAW_AND_ALL_AVAILABLE93_CPU_EXIT0_NOT_METHOD_ACCEPTANCE',exit_code=0,
            raw_sha256=sha(args.stage/'raw-audit.json'),score_sha256=sha(args.stage/'score-result.json'))
    except BaseException as error:
        r.update(status='E2_CPU_POST_FAILED_OR_ORIGINAL_GPU_FAILED_SCOPE_RETAINED',exit_code=1,
            error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_driver_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            budget_after_sha256=sha(args.project/'reports/budget.json'));write(target,r)
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
