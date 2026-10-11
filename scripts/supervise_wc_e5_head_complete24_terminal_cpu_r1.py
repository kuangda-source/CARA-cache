"""One read-only audit after all original whole24 GPU handles have exited."""
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
    p.add_argument('--original-supervisor-pid',type=int,required=True)
    p.add_argument('--source-revision',required=True);args=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e5_head_complete24_production_r1 import RUN,sha,write
    target=args.stage/'terminal-CPU-supervisor.json';assert not target.exists()
    result=args.stage/'real-GPU-audit.json';assert not result.exists()
    state={'status':'E5_TERMINAL_CPU_WAITING_ORIGINAL_GPU_HANDLES','pid':os.getpid(),
        'source_revision':args.source_revision,'original_GPU_supervisor_pid':args.original_supervisor_pid,
        'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,
        'audit_source_sha256':sha(args.stage/'scripts/audit_wc_e5_head_complete24_terminal_cpu_r1.py')}
    write(target,state)
    try:
        while Path('/proc/'+str(args.original_supervisor_pid)).exists():time.sleep(15)
        sup=json.loads((args.project/'outputs'/RUN/'supervisor.json').read_text())
        assert sup['pid']==args.original_supervisor_pid and sup['source_revision']==args.source_revision
        assert not any(Path('/proc/'+str(a['pid'])).exists() for a in sup['arms'] if 'pid' in a)
        state.update(status='E5_TERMINAL_CPU_READING_ALL_ORIGINAL_ARTIFACTS',
            original_handles_absent=True,budget_before_sha256=sha(args.project/'reports/budget.json'));write(target,state)
        command=[sys.executable,str(args.stage/'scripts/audit_wc_e5_head_complete24_terminal_cpu_r1.py'),
            '--project',str(args.project),'--stage',str(args.stage),'--output',str(result)]
        with (args.stage/'terminal-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',
                    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'))
            state.update(child_pid=child.pid,command=command);write(target,state);state['exit_code']=child.wait()
        state.update(status='E5_TERMINAL_CPU_EXIT0_REQUIRES_INDEPENDENT_CAPTURE' if state['exit_code']==0
            else 'E5_TERMINAL_CPU_FAILED_RETAIN_ORIGINALS')
        if result.exists():state['result_sha256']=sha(result)
        assert sha(args.stage/'scripts/audit_wc_e5_head_complete24_terminal_cpu_r1.py')==state['audit_source_sha256']
        assert sha(args.project/'reports/budget.json')==state['budget_before_sha256']
    except BaseException as error:
        state.update(status='E5_TERMINAL_CPU_FAILED_RETAIN_ORIGINALS',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        state.update(ended_unix=time.time(),budget_after_sha256=sha(args.project/'reports/budget.json'));write(target,state)
    return state['exit_code']


if __name__=='__main__':raise SystemExit(main())
