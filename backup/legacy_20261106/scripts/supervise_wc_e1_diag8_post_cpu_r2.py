#!/usr/bin/env python3
"""Follow only the original E1 GPU supervisor, then audit all retained slots."""
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
    p.add_argument('--original-supervisor-pid',type=int,required=True);p.add_argument('--source-revision',required=True)
    args=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e1_diag8_production_r2 import RUN,write,sha
    root=args.project/'outputs'/RUN;target=args.stage/'post-CPU-receipt.json';assert not target.exists()
    r={'status':'E1_POST_CPU_WAITING_ORIGINAL_GPU_HANDLES','pid':os.getpid(),
        'original_supervisor_pid':args.original_supervisor_pid,'source_revision':args.source_revision,'GPU_submissions':0,'ledger_written':False}
    write(target,r)
    while Path('/proc/'+str(args.original_supervisor_pid)).exists():time.sleep(10)
    try:
        supervisor=json.loads((root/'supervisor.json').read_text())
        assert supervisor['pid']==args.original_supervisor_pid and supervisor['source_revision']==args.source_revision
        r['budget_before_sha256']=sha(args.project/'reports/budget.json');r['started_unix']=time.time()
        command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
            str(args.stage/'scripts/postprocess_wc_e1_diag8_cpu_r2.py'),'--project',str(args.project),'--stage',str(args.stage)]
        with (args.stage/'post-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
            r.update(status='E1_POST_ACTUAL_RAW_CPU_RUNNING',child_pid=child.pid,command=command);write(target,r)
            r['child_exit_code']=child.wait()
        assert r['child_exit_code']==0
        r.update(status='E1_POST_ACTUAL_RAW_CPU_PASS_NOT_METHOD_CONFIRMATION',exit_code=0,
            raw_audit_sha256=sha(root/'raw-CPU-audit.json'))
    except BaseException as error:
        r.update(status='E1_POST_ACTUAL_RAW_CPU_FAILED_SCOPE_RETAINED',exit_code=1,
            error_type=type(error).__name__,error=str(error))
    finally:
        r.update(ended_unix=time.time(),budget_after_sha256=sha(args.project/'reports/budget.json'));write(target,r)
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
