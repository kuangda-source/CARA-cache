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
    from wcomr.p_reference_same_state_production_r1 import RUN,sha,write
    from wcomr.p_reference_same_state_execution_r1 import PYTHON
    from wcomr.p_reference_same_state_terminal_r1 import original_gone
    target=args.stage/'post-CPU-receipt.json';assert not target.exists()
    r={'status':'WAITING_ORIGINAL_P_REFERENCE_RELEASE','pid':os.getpid(),'source_revision':args.source_revision,
        'original_supervisor_pid':args.original_supervisor_pid,'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}
    write(target,r);start=time.perf_counter()
    try:
        while Path('/proc/'+str(args.original_supervisor_pid)).exists():time.sleep(3)
        s=json.loads((args.project/'outputs'/RUN/'supervisor.json').read_text())
        original_gone(s,args.original_supervisor_pid,lambda pid:Path('/proc/'+str(pid)).exists())
        r.update(status='P_REFERENCE_RELEASED_COMPLETE_SCOPE_CPU_RUNNING',budget_before_sha256=sha(args.project/'reports/budget.json'));write(target,r)
        command=[PYTHON,str(args.stage/'scripts/postprocess_wc_p_reference_same_state_cpu_r1.py'),
            '--project',str(args.project),'--stage',str(args.stage)]
        with (args.stage/'post-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                    PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
            r.update(child_pid=child.pid,command=command);write(target,r);r['child_exit_code']=child.wait()
        if r['child_exit_code']!=0:raise ValueError('P-reference post child failed; original complete slots remain in raw receipts')
        result=json.loads((args.stage/'raw-audit.json').read_text())
        assert result['status']=='P_REFERENCE_COMPLETE_SCOPE_CPU_READ_NOT_METHOD_ACCEPTANCE'
        assert len(result['parent_slots'])==8 and len(result['suffix_slots'])==32 and len(result['point_slots'])==48
        r.update(status='P_REFERENCE_COMPLETE_SCOPE_CPU_EXIT0_NOT_METHOD_ACCEPTANCE',exit_code=0,
            raw_sha256=sha(args.stage/'raw-audit.json'),whole_scope_verified=result['whole_scope_verified'],
            actual_audit_failures=result['actual_audit_failures'])
    except BaseException as error:
        r.update(status='P_REFERENCE_POST_CPU_FAILURE_SCOPE_RETAINED',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_driver_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            budget_after_sha256=sha(args.project/'reports/budget.json'));write(target,r)
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
