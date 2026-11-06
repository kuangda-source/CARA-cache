#!/usr/bin/env python3
"""Actual guarded entry imports, complete scalar controls and metric assets."""
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
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e2_execution_r1 import sha,write,validate_execution
    c=json.loads((args.stage/'e2-config.json').read_text());p=json.loads((args.stage/'execution-protocol.json').read_text())
    validate_execution(c,p,args.stage);target=args.stage/'execution-CPU-receipt.json';assert not target.exists()
    r={'status':'E2_EXECUTION_ACTUAL_CPU_RUNNING_NOT_GPU','pid':os.getpid(),'source_revision':args.source_revision,
        'started_unix':time.time(),'budget_before_sha256':sha(args.project/'reports/budget.json'),
        'config_binding_sha256':p['method_config_binding_sha256'],'execution_protocol_sha256':sha(args.stage/'execution-protocol.json'),
        'GPU_submissions':0,'ledger_written':False,'CUDA_initialized':False,'config_sha256':sha(args.stage/'e2-config.json')}
    write(target,r);start=time.perf_counter()
    python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        HF_HUB_CACHE=str(args.project/'hfhub'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    try:
        commands=[['python3',str(args.stage/'tests/check_e2_full76_execution_cpu_r1.py'),'--root',str(args.stage),
                   '--output',str(args.stage/'scalar-CPU-result.json')],
            [python,str(args.stage/'scripts/run_wc_e2_observed_r1.py'),'--project',str(args.project),'--stage',str(args.stage),'--cpu-check']]
        with (args.stage/'execution-CPU.log').open('x') as log:
            for command in commands:
                child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=args.project/'runtime')
                r.update(child_pid=child.pid,current_command=command);write(target,r)
                code=child.wait();r['last_child_exit_code']=code;assert code==0,'Actual execution CPU failed; no GPU dispatch'
        results=[]
        for line in (args.stage/'execution-CPU.log').read_text().splitlines():
            try:v=json.loads(line)
            except ValueError:continue
            if isinstance(v,dict) and v.get('status')=='E2_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU':results.append(v)
        assert len(results)==1 and results[0]['config_binding_sha256']==p['method_config_binding_sha256']
        assert results[0]['payload_sha256']==c['payload_sha256'] and results[0]['scope_counts']==c['scope_counts']
        assert len(results[0]['contract_mutation_refusals'])==13 and not results[0]['CUDA_initialized']
        from wcomr.lpips_resource_identity import audit
        identity=audit(args.project/'.sync/wc-rv0-lpips-resource-v2',p['execution_payload_sha256']['src/wcomr/rv0_lpips.py'])
        result={'status':'E2_ACTUAL_EXECUTION_WRAPPER_CPU_PASS_NOT_GPU_OR_LPIPS_SCORE',
            'original_guarded_entry_CPU_result':results[0],'scalar_result_sha256':sha(args.stage/'scalar-CPU-result.json'),
            'actual_offline_metric_resource_identity':identity,'GPU_submissions':0,'ledger_written':False}
        write(args.stage/'execution-CPU-result.json',result)
        r.update(status='E2_EXECUTION_ACTUAL_CPU_PASS_NOT_GPU',exit_code=0,result_sha256=sha(args.stage/'execution-CPU-result.json'))
    except BaseException as error:
        r.update(status='E2_EXECUTION_ACTUAL_CPU_FAILED_SCOPE_RETAINED_NOT_PASS',exit_code=1,error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),budget_after_sha256=sha(args.project/'reports/budget.json'),
            method_payload_after_sha256={n:sha(args.stage/n) for n in c['payload_sha256']},
            execution_payload_after_sha256={n:sha(args.stage/n) for n in p['execution_payload_sha256']})
        if (r['budget_before_sha256']!=r['budget_after_sha256'] or r['method_payload_after_sha256']!=c['payload_sha256']
                or r['execution_payload_after_sha256']!=p['execution_payload_sha256'] or sha(args.stage/'e2-config.json')!=r['config_sha256']):
            r.update(status='E2_EXECUTION_CPU_IDENTITY_CHANGED_NOT_PASS',exit_code=1)
        write(target,r)
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
