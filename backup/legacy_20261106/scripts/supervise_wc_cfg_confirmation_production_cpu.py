#!/usr/bin/env python3
"""One complete production CPU check; preserve source, budget and native output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    for name in ('project','stage'): p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-revision',required=True);a=p.parse_args()
    c=json.loads((a.stage/'teacher-config.json').read_text());budget=a.project/'reports/budget.json'
    state={'status':'CONFIRMATION_PRODUCTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
           'source_revision':a.source_revision,'started_unix':time.time(),
           'budget_before_sha256':sha(budget),'config_sha256':sha(a.stage/'teacher-config.json'),
           'GPU_submissions':0,'CUDA_initialized':False}
    receipt=a.stage/'receipt.json';assert not receipt.exists()
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(receipt)
    save();start=time.perf_counter()
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2')
    python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    try:
        with (a.stage/'production-CPU.log').open('x') as log:
            child=subprocess.Popen([python,str(a.stage/'scripts/run_wc_cfg_mechanism_confirmation.py'),
                  '--project',str(a.project),'--stage',str(a.stage),'--cpu-check'],env=env,
                  stdout=log,stderr=subprocess.STDOUT,cwd=a.project/'runtime')
            state['child_pid']=child.pid;save();state['child_exit_code']=child.wait()
        if state['child_exit_code']:raise RuntimeError('Original production CPU failed; no GPU dispatch')
        rows=[]
        for line in (a.stage/'production-CPU.log').read_text().splitlines():
            try: value=json.loads(line)
            except ValueError:continue
            if isinstance(value,dict) and value.get('status')=='TEACHER_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU':rows.append(value)
        assert len(rows)==1;result=rows[0]
        assert not result['CUDA_initialized'] and result['GPU_submissions']==0
        assert result['payload_sha256']==c['payload_sha256'] and result['registered_scope']==c['preregistration']['scope_counts']
        (a.stage/'CPU-result.json').write_text(json.dumps(result,indent=2)+'\n')
        state.update(status='TEACHER_PRODUCTION_CPU_PASS_NOT_GPU',exit_code=0,
             config_binding_sha256=result['config_binding_sha256'],result_sha256=sha(a.stage/'CPU-result.json'))
    except BaseException as error:
        state.update(status='CONFIRMATION_PRODUCTION_CPU_FAILED_NOT_PASS',exit_code=1,error=str(error),error_type=type(error).__name__)
    finally:
        state.update(CPU_wall_seconds=time.perf_counter()-start,budget_after_sha256=sha(budget),
              payload_after_sha256={name:sha(a.stage/name) for name in c['payload_sha256']})
        if (state['budget_before_sha256']!=state['budget_after_sha256'] or state['payload_after_sha256']!=c['payload_sha256']
                or state['config_sha256']!=sha(a.stage/'teacher-config.json')):
            state.update(status='CONFIRMATION_PRODUCTION_CPU_BINDING_CHANGED_NOT_PASS',exit_code=1)
        save()
    raise SystemExit(state['exit_code'])


if __name__=='__main__':main()
