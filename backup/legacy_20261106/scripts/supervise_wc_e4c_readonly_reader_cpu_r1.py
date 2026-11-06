"""Only read accepted artifacts on CPU; record handles, source and outcome."""
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
    for n in ('stage','original-stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--revision',required=True);args=p.parse_args();s=args.stage;old=args.original_stage
    reg=json.loads((s/'registration.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    budget=s.parents[1]/'reports/budget.json'
    state={'status':'E4C_READONLY_CPU_READER_RUNNING_NOT_GPU','pid':os.getpid(),'source_revision':args.revision,
        'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'budget_before_sha256':sha(budget)}
    def save(): (s/'receipt.json').write_text(json.dumps(state,indent=2)+'\n')
    save();start=time.monotonic()
    try:
        command=[sys.executable,str(s/'scripts/check_wc_e4c_readonly_reader_cpu_r1.py'),
            '--reader-stage',str(s),'--original-stage',str(old),'--output',str(s/'result.json')]
        with (s/'CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
            state['child_pid']=child.pid;save();state['child_exit_code']=child.wait()
        state['exit_code']=state['child_exit_code']
        state['status']='E4C_READONLY_CPU_READER_EXIT0_NOT_GPU' if state['exit_code']==0 else 'E4C_READONLY_CPU_READER_FAILED_NOT_GPU'
        if (s/'result.json').exists():state['result_sha256']=sha(s/'result.json')
        assert {n:sha(s/n) for n in reg['new_payload_sha256']}==reg['new_payload_sha256']
        assert {n:sha(old/n) for n in reg['original_payload_sha256']}==reg['original_payload_sha256']
        assert sha(old/'receipt.json')==reg['original_receipt_sha256'] and sha(old/'result.json')==reg['original_result_sha256']
        state['source_after_sha256']=reg['new_payload_sha256'];state['original_source_unchanged']=True
    except Exception as error:
        state.update(status='E4C_READONLY_CPU_READER_FAILED_NOT_GPU',exit_code=1,error=repr(error))
        raise
    finally:
        state.update(CPU_wall_seconds=time.monotonic()-start,ended_unix=time.time(),budget_after_sha256=sha(budget))
        state['concurrent_GPU_may_legitimately_update_ledger']=True
        save()
    return state['exit_code']


if __name__=='__main__':raise SystemExit(main())
