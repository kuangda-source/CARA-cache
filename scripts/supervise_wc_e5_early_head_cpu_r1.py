"""Run isolated E5 CPU prototype, without a GPU/resource/ledger writer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--revision',required=True);args=p.parse_args();stage=args.stage
    reg=json.loads((stage/'registration.json').read_text());project=stage.parents[1]
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    files=dict(reg['inherited_payload_sha256'],**reg['new_payload_sha256'])
    assert {n:sha(stage/n) for n in files}==files
    state={'status':'E5_EARLY_HEAD_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
        'source_revision':args.revision,'started_unix':time.time(),
        'budget_before_sha256':sha(project/'reports/budget.json'),'GPU_submissions':0,'ledger_written':False}
    receipt=stage/'receipt.json';assert not receipt.exists()
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(receipt)
    save();start=time.monotonic()
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                 PYTHONPATH=str(stage/'src')+':'+str(stage/'tests'))
        command=[sys.executable,str(stage/'tests/check_early_head_elision_cpu_r1.py'),
                 '--runtime',str(project/'runtime'),'--output',str(stage/'CPU-artifacts')]
        with (stage/'CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
            state['child_pid']=child.pid;save();state['child_exit_code']=child.wait()
        state['exit_code']=state['child_exit_code']
        state['status']='E5_EARLY_HEAD_CPU_EXIT0_REQUIRES_INDEPENDENT_CAPTURE' if state['exit_code']==0 else 'E5_EARLY_HEAD_CPU_FAILED_RETAIN_ATTEMPT'
        result=stage/'CPU-artifacts/result.json'
        if result.exists():state['result_sha256']=sha(result)
        assert {n:sha(stage/n) for n in files}==files
        state['payload_after_sha256']=files
    except Exception as error:
        state.update(exit_code=1,status='E5_EARLY_HEAD_CPU_FAILED_RETAIN_ATTEMPT',error=repr(error));raise
    finally:
        state.update(CPU_wall_seconds=time.monotonic()-start,ended_unix=time.time(),
            budget_after_sha256=sha(project/'reports/budget.json'),
            concurrent_GPU_may_legitimately_update_ledger=True)
        save()
    return state['exit_code']


if __name__=='__main__':raise SystemExit(main())
