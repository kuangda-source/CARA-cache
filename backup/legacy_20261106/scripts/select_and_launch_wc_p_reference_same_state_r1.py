#!/usr/bin/env python3
"""Exact full-card authority and both CPU proofs precede the one GPU/post chain."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def launch_handles(project,stage,revision,c,production_sha,selected_cpu_sha,protocol_sha):
    from wcomr.p_reference_same_state_execution_r1 import PYTHON
    from wcomr.p_reference_same_state_production_r1 import CONFIG,sha,write
    assert not (stage/'selection.json').exists() and not (stage/'GPU-launch.json').exists()
    write(stage/'selection.json',{'source_revision':revision,'selected_config_sha256':sha(stage/CONFIG),
        'production_CPU_receipt_sha256':production_sha,'selected_CPU_receipt_sha256':selected_cpu_sha,
        'execution_protocol_sha256':protocol_sha})
    command=[PYTHON,str(stage/'scripts/supervise_wc_p_reference_same_state_r1.py'),
        '--project',str(project),'--stage',str(stage),'--source-revision',revision]
    with (stage/'GPU-supervisor.log').open('x') as log:
        gpu=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    post_command=[PYTHON,str(stage/'scripts/supervise_wc_p_reference_same_state_post_cpu_r1.py'),
        '--project',str(project),'--stage',str(stage),'--source-revision',revision,
        '--original-supervisor-pid',str(gpu.pid)]
    try:
        with (stage/'post-driver.log').open('x') as log:
            post=subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
        value={'status':'P_REFERENCE_ORIGINAL_GPU_AND_POST_HANDLES_DISPATCHED_ADMISSION_IN_SUPERVISOR',
            'source_revision':revision,'gpu_supervisor_pid':gpu.pid,'post_CPU_pid':post.pid,
            'scope_counts':c['scope_counts'],'selected_config_sha256':sha(stage/CONFIG),
            'execution_protocol_sha256':protocol_sha,'observed_unix':time.time()}
    except BaseException as error:
        # Preserve the original GPU handle; never silently resubmit the full card.
        write(stage/'GPU-launch.json',{'status':'P_REFERENCE_POST_DISPATCH_FAILED_ORIGINAL_GPU_HANDLE_RETAINED',
            'gpu_supervisor_pid':gpu.pid,'source_revision':revision,'error_type':type(error).__name__,'error':str(error)})
        raise
    write(stage/'GPU-launch.json',value);return value


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.p_reference_same_state_production_r1 import CONFIG,binding,sha,write,validate,validate_selected
    from wcomr.p_reference_same_state_execution_r1 import PROTOCOL,PYTHON,validate_execution,validate_post_proof
    c,*_=validate(args.project,args.stage);validate_selected(c,args.stage)
    protocol=json.loads((args.stage/PROTOCOL).read_text());validate_execution(c,protocol,args.stage)
    validate_post_proof(c,protocol,args.stage)
    target=args.stage/'selected-CPU-receipt.json';assert not target.exists()
    r={'status':'P_REFERENCE_SELECTED_EXECUTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),'source_revision':args.source_revision,
        'started_unix':time.time(),'method_binding_sha256':binding(c),'protocol_sha256':sha(args.stage/PROTOCOL),
        'budget_before_sha256':sha(args.project/'reports/budget.json'),'GPU_submissions':0,'ledger_written':False}
    write(target,r);start=time.perf_counter()
    try:
        values=[];exits=[]
        for arm,flow in c['flow_arms'].items():
            command=[PYTHON,str(args.stage/'scripts/run_wc_p_reference_same_state_r1.py'),
                '--project',str(args.project),'--stage',str(args.stage),'--cpu-check','--arm',arm]
            path=args.stage/('selected-CPU-'+arm+'.log')
            with path.open('x') as log:
                child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                        PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
                r.setdefault('children',[]).append({'arm':arm,'pid':child.pid,'command':command});write(target,r)
                code=child.wait();exits.append(code)
            assert code==0
            found=[]
            for line in path.read_text().splitlines():
                try:value=json.loads(line)
                except ValueError:continue
                if isinstance(value,dict) and value.get('status')=='P_REFERENCE_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU':found.append(value)
            assert len(found)==1;value=found[0]
            assert value['config_binding_sha256']==binding(c) and value['payload_sha256']==c['payload_sha256']
            assert value['scope_counts']==c['scope_counts'] and not value['CUDA_initialized'] and value['arm']==arm and value['flow']==flow
            values.append(value)
        r['child_exit_codes']=exits
        validate_execution(c,protocol,args.stage);validate_post_proof(c,protocol,args.stage);validate_selected(c,args.stage)
        assert sha(args.project/'reports/budget.json')==r['budget_before_sha256']
        r.update(status='P_REFERENCE_SELECTED_EXECUTION_CPU_PASS_NOT_GPU',exit_code=0,CPU_wall_seconds=time.perf_counter()-start,
            budget_after_sha256=r['budget_before_sha256']);write(target,r)
    except BaseException as error:
        r.update(status='P_REFERENCE_SELECTED_EXECUTION_CPU_FAILED_NOT_GPU',exit_code=1,error_type=type(error).__name__,error=str(error));write(target,r);raise
    value=launch_handles(args.project,args.stage,args.source_revision,c,sha(args.stage/'production-CPU-receipt.json'),
        sha(target),sha(args.stage/PROTOCOL));print(json.dumps(value))


if __name__=='__main__':main()
