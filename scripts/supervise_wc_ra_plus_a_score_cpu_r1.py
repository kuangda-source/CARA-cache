#!/usr/bin/env python3
"""Follow original handles to exit, then launch exactly one complete CPU score."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);a=p.parse_args()
    reg=json.loads((a.stage/'score-preregistration.json').read_text());launch=reg['original_launch']
    post=Path(launch['post_CPU_stage']);out=a.project/'outputs'/launch['run_id']
    target=a.stage/'receipt.json'
    if target.exists():raise ValueError('No repeated scoring identity')
    r={'status':'WAITING_ORIGINAL_GPU_AND_RAW_CPU_HANDLES','pid':os.getpid(),
       'source_revision':a.source_revision,'original_launch':launch,'started_unix':time.time(),
       'GPU_submissions':0,'ledger_written':False,'planned_scope':reg['scope_counts']}
    def save():
        tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(target)
    save();start=time.perf_counter()
    try:
        while any(Path('/proc/'+str(p)).exists() for p in (launch['supervisor_pid'],launch['post_CPU_pid'])):
            time.sleep(3)
        gpu=json.loads((out/'supervisor.json').read_text());raw=json.loads((post/'receipt.json').read_text())
        if (gpu['pid']!=launch['supervisor_pid'] or raw['pid']!=launch['post_CPU_pid']
                or gpu['exit_code']!=0 or raw['exit_code']!=0 or raw['child_exit_code']!=0
                or any(Path('/proc/'+str(p)).exists() for p in (gpu['child_pid'],raw['child_pid']))):
            raise ValueError('Original complete GPU/raw CPU failed; do not score a subset')
        r.update(status='COMPLETE_RA_CPU_SCORING_RUNNING',budget_before_scoring_sha256=sha(a.project/'reports/budget.json'));save()
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        with (a.stage/'score.log').open('x') as log:
            child=subprocess.Popen([python,str(a.stage/'scripts/score_wc_ra_plus_a_cpu_r1.py'),
                '--project',str(a.project),'--stage',str(a.stage)],stdout=log,stderr=subprocess.STDOUT,env=env)
            r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()
        if r['child_exit_code']!=0:raise RuntimeError('Original full comparison CPU scoring failed')
        result=json.loads((a.stage/'result.json').read_text())
        if (result['status']!='RA_PLUS_A_FULL_COMPARISON_COMPLETE_AVAILABLE_ALL93_FIDELITY_AND_COST_NOT_CLEAN_SPEED'
                or result['CUDA_initialized'] or result['GPU_submissions'] or result['ledger_written']
                or result['summary']['scored_pairs']!=result['available_planned_pairs']):
            raise ValueError('Original full all93 score result incomplete')
        r.update(status='RA_PLUS_A_COMPLETE_ALL93_CPU_SCORING_EXIT0_NOT_METHOD_ACCEPTANCE',exit_code=0,result_sha256=sha(a.stage/'result.json'))
    except BaseException as error:
        r.update(status='RA_CPU_SCORE_FAILED_COMPLETE_SCOPE_RETAINED',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        r.update(total_driver_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            budget_after_sha256=sha(a.project/'reports/budget.json'),
            payload_after_sha256={n:sha(a.stage/n) for n in reg['payload_sha256']})
        save()
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
