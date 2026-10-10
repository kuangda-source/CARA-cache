#!/usr/bin/env python3
"""Selected actual CPU must pass before a single original GPU/post chain."""
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
    from wcomr.e2_execution_r1 import binding,sha,write,validate_execution
    c=json.loads((args.stage/'e2-config.json').read_text());protocol=json.loads((args.stage/'execution-protocol.json').read_text())
    validate_execution(c,protocol,args.stage);assert c['GPU_execution_selected']
    path=args.stage/'selected-CPU-receipt.json';assert not path.exists()
    r={'status':'E2_SELECTED_EXECUTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),'source_revision':args.source_revision,
        'started_unix':time.time(),'config_binding_sha256':binding(c),'execution_protocol_sha256':sha(args.stage/'execution-protocol.json'),
        'budget_before_sha256':sha(args.project/'reports/budget.json'),'GPU_submissions':0,'ledger_written':False}
    write(path,r);python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=[python,str(args.stage/'scripts/run_wc_e2_observed_r1.py'),'--project',str(args.project),'--stage',str(args.stage),'--cpu-check']
    start=time.perf_counter()
    try:
        with (args.stage/'selected-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2'))
            r.update(child_pid=child.pid,command=command);write(path,r);r['child_exit_code']=child.wait()
        assert r['child_exit_code']==0
        result=[]
        for line in (args.stage/'selected-CPU.log').read_text().splitlines():
            try:v=json.loads(line)
            except ValueError:continue
            if isinstance(v,dict) and v.get('status')=='E2_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU':result.append(v)
        assert len(result)==1 and result[0]['config_binding_sha256']==binding(c)
        assert result[0]['payload_sha256']==c['payload_sha256'] and not result[0]['CUDA_initialized']
        assert result[0]['scope_counts']==c['scope_counts'] and len(result[0]['contract_mutation_refusals'])==13
        assert {n:sha(args.stage/n) for n in c['payload_sha256']}==c['payload_sha256']
        assert {n:sha(args.stage/n) for n in protocol['execution_payload_sha256']}==protocol['execution_payload_sha256']
        assert sha(args.project/'reports/budget.json')==r['budget_before_sha256']
        r.update(status='E2_SELECTED_EXECUTION_CPU_PASS_NOT_GPU',exit_code=0,CPU_wall_seconds=time.perf_counter()-start,
            budget_after_sha256=sha(args.project/'reports/budget.json'));write(path,r)
    except BaseException as error:
        r.update(status='E2_SELECTED_EXECUTION_CPU_FAILED_NOT_GPU',exit_code=1,error_type=type(error).__name__,error=str(error));write(path,r);raise
    selection={'source_revision':args.source_revision,'selected_config_sha256':sha(args.stage/'e2-config.json'),
        'selected_CPU_receipt_sha256':sha(path),'execution_protocol_sha256':sha(args.stage/'execution-protocol.json')}
    assert not (args.stage/'selection.json').exists();write(args.stage/'selection.json',selection)
    gpu_command=[python,str(args.stage/'scripts/supervise_wc_e2_full76_r1.py'),'--project',str(args.project),
        '--stage',str(args.stage),'--source-revision',args.source_revision]
    with (args.stage/'GPU-supervisor.log').open('x') as log:
        gpu=subprocess.Popen(gpu_command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    post_command=['python3',str(args.stage/'scripts/supervise_wc_e2_post_cpu_r1.py'),'--project',str(args.project),
        '--stage',str(args.stage),'--source-revision',args.source_revision,'--original-supervisor-pid',str(gpu.pid)]
    with (args.stage/'post-driver.log').open('x') as log:
        post=subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    launched={'status':'ORIGINAL_GPU_AND_POST_HANDLES_DISPATCHED_ADMISSION_IN_SUPERVISOR',
        'stage':str(args.stage),'source_revision':args.source_revision,'gpu_supervisor_pid':gpu.pid,'post_CPU_pid':post.pid,
        'scope_counts':c['scope_counts'],'selected_config_sha256':sha(args.stage/'e2-config.json'),
        'execution_protocol_sha256':sha(args.stage/'execution-protocol.json'),'observed_unix':time.time()}
    assert not (args.stage/'GPU-launch.json').exists();write(args.stage/'GPU-launch.json',launched);print(json.dumps(launched))


if __name__=='__main__':main()
