"""Wait for original GPU handles, then run exactly one read-only CPU audit."""
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
    for n in ('project','stage','reader-stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);args=p.parse_args()
    reader=args.reader_stage;receipt=reader/'terminal-CPU-supervisor.json';assert not receipt.exists()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg=json.loads((reader/'postprocessor-registration.json').read_text())
    assert sha(reader/reg['postprocessor_ref'])==reg['postprocessor_sha256']
    state={'status':'E4C_CPU_WAITING_ORIGINAL_GPU_HANDLES','pid':os.getpid(),
        'source_revision':args.source_revision,'postprocessor_sha256':reg['postprocessor_sha256'],
        'original_GPU_PIDs':[4075406,4075494],'started_unix':time.time(),
        'GPU_submissions':0,'ledger_written':False,'CUDA_initialization_or_model_loading':False}
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(receipt)
    save()
    try:
        while any(Path('/proc/'+str(i)).exists() for i in state['original_GPU_PIDs']):
            time.sleep(15)
        state.update(status='E4C_ORIGINAL_GPU_TERMINAL_CPU_AUDIT_RUNNING',original_handles_absent=True,
            audit_started_unix=time.time(),budget_before_sha256=sha(args.project/'reports/budget.json'));save()
        command=[sys.executable,str(reader/reg['postprocessor_ref']),'--project',str(args.project),
            '--stage',str(args.stage),'--reader-stage',str(reader),'--output',str(reader/'real-GPU-audit.json')]
        with (reader/'terminal-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'))
            state['child_pid']=child.pid;save();state['child_exit_code']=child.wait()
        state.update(status='E4C_TERMINAL_RAW_CPU_EXIT0_REQUIRES_INDEPENDENT_CAPTURE' if state['child_exit_code']==0 else 'E4C_TERMINAL_RAW_CPU_FAILED_RETAIN_ORIGINALS',
            exit_code=state['child_exit_code'],audit_ended_unix=time.time())
        if (reader/'real-GPU-audit.json').exists():state['result_sha256']=sha(reader/'real-GPU-audit.json')
        assert sha(reader/reg['postprocessor_ref'])==reg['postprocessor_sha256']
    except Exception as error:
        state.update(status='E4C_TERMINAL_RAW_CPU_FAILED_RETAIN_ORIGINALS',exit_code=1,error=repr(error))
        raise
    finally:
        state.update(ended_unix=time.time(),budget_after_sha256=sha(args.project/'reports/budget.json'));save()
    return state['exit_code']


if __name__=='__main__':raise SystemExit(main())
