#!/usr/bin/env python3
"""Run one original production CPU checker; never dispatch or reserve GPU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    config=args.stage/'e2-config.json';c=json.loads(config.read_text());budget=args.project/'reports/budget.json'
    receipt=args.stage/'receipt.json';assert not receipt.exists() and not c['GPU_execution_selected']
    value={'status':'E2_ACTUAL_PRODUCTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
        'source_revision':args.source_revision,'started_unix':time.time(),'config_sha256':sha(config),
        'budget_before_sha256':sha(budget),'GPU_submissions':0,'ledger_written':False,'CUDA_initialized':False}
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(receipt)
    save();start=time.perf_counter()
    try:
        assert {n:sha(args.stage/n) for n in c['payload_sha256']}==c['payload_sha256']
        command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
            str(args.stage/'scripts/run_wc_e2_confirmation_r1.py'),'--project',str(args.project),'--stage',str(args.stage),'--cpu-check']
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',
            TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (args.stage/'production-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=args.project/'runtime')
            value.update(child_pid=child.pid,command=command);save();value['child_exit_code']=child.wait()
        assert value['child_exit_code']==0,'Original E2 production CPU failed; no GPU dispatch'
        candidates=[]
        for line in (args.stage/'production-CPU.log').read_text().splitlines():
            try:item=json.loads(line)
            except ValueError:continue
            if isinstance(item,dict) and item.get('status')=='E2_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU':candidates.append(item)
        assert len(candidates)==1;result=candidates[0]
        assert result['payload_sha256']==c['payload_sha256'] and result['scope_counts']==c['scope_counts']
        assert len(result['contract_mutation_refusals'])==13
        assert not result['CUDA_initialized'] and result['GPU_submissions']==0
        assert result['actual_ten_requests_parsed'] and result['actual_guardrail_resource_and_Native_origin_checked']
        assert result['five_guardrail_less_methods_refused']
        p=args.stage/'CPU-result.json';p.write_text(json.dumps(result,indent=2)+'\n')
        value.update(status='E2_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',exit_code=0,
            result_sha256=sha(p),config_binding_sha256=result['config_binding_sha256'])
    except BaseException as error:
        value.update(status='E2_ACTUAL_PRODUCTION_CPU_FAILED_SCOPE_RETAINED_NOT_PASS',exit_code=1,
            error_type=type(error).__name__,error=str(error))
    finally:
        value.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            budget_after_sha256=sha(budget),payload_after_sha256={n:sha(args.stage/n) for n in c['payload_sha256']})
        if (value['budget_before_sha256']!=value['budget_after_sha256'] or sha(config)!=value['config_sha256']
                or value['payload_after_sha256']!=c['payload_sha256']):
            value.update(status='E2_ACTUAL_PRODUCTION_CPU_IDENTITY_CHANGED_NOT_PASS',exit_code=1)
        save()
    raise SystemExit(value['exit_code'])


if __name__=='__main__':main()
