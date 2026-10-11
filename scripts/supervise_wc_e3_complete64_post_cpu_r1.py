#!/usr/bin/env python3
"""Follow the unique original full-card handle, including technical failure."""
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
    from wcomr.e3_complete64_production_r1 import RUN,sha,write
    from wcomr.e3_complete64_execution_r1 import PYTHON,original_gone
    target=args.stage/'post-CPU-receipt.json';assert not target.exists()
    r={'status':'WAITING_ORIGINAL_E3_FULL_CARD_RELEASE','pid':os.getpid(),'source_revision':args.source_revision,
        'original_supervisor_pid':args.original_supervisor_pid,'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}
    write(target,r);start=time.perf_counter()
    try:
        while Path('/proc/'+str(args.original_supervisor_pid)).exists():time.sleep(3)
        s=json.loads((args.project/'outputs'/RUN/'supervisor.json').read_text())
        original_gone(s,args.original_supervisor_pid,lambda pid:Path('/proc/'+str(pid)).exists())
        r.update(status='E3_RELEASED_GPU_COMPLETE_SCOPE_CPU_RUNNING',budget_before_sha256=sha(args.project/'reports/budget.json'));write(target,r)
        command=[PYTHON,str(args.stage/'scripts/postprocess_wc_e3_complete64_cpu_r1.py'),
            '--project',str(args.project),'--stage',str(args.stage)]
        with (args.stage/'post-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                    PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
            r.update(child_pid=child.pid,command=command);write(target,r);r['child_exit_code']=child.wait()
        if r['child_exit_code']!=0:raise ValueError('E3 post child failed; original full64 slots remain in raw/score receipts')
        result=json.loads((args.stage/'score-result.json').read_text())
        assert result['status']=='E3_COMPLETE64_ALL_AVAILABLE93_CPU_TERMINAL_NOT_AUTOMATIC_METHOD_ACCEPTANCE'
        assert len(result['slots_all64'])==64 and result['summary']['scored_pairs']==sum(x['scored'] for x in result['slots_all64'])
        r.update(status='E3_COMPLETE_SCOPE_CPU_EXIT0_ALL_AVAILABLE93_NOT_METHOD_ACCEPTANCE',exit_code=0,
            raw_sha256=sha(args.stage/'raw-audit.json'),score_sha256=sha(args.stage/'score-result.json'),
            whole64_all_scored=result['whole64_all_scored'],actual_score_failures=result['actual_score_failures'])
    except BaseException as error:
        r.update(status='E3_POST_CPU_FAILURE_SCOPE_RETAINED',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_driver_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            budget_after_sha256=sha(args.project/'reports/budget.json'));write(target,r)
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
