#!/usr/bin/env python3
"""Two complete fresh flow lifetimes under one exactly authorized whole-card job."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def observe(uuid):
    values=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap',
        '--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'],text=True,timeout=10)
    return {'unix':time.time(),'uuid':values[0].strip(),'name':values[1].strip(),'memory_used_mib':int(values[2]),
        'compute_cap':values[3].strip(),'pids':[int(v.split(',')[1]) for v in apps.splitlines() if v.split(',')[0].strip()==uuid]}


def monitored(uuid):
    try:return observe(uuid)
    except (OSError,subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:
        return {'unix':time.time(),'status':'TELEMETRY_UNAVAILABLE','error':str(error)}


def stop_own(child):
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);args=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(args.stage/'src'))
    from wcomr.p_reference_same_state_production_r1 import RUN,UUID,CONFIG,sha,write,validate,validate_selected,admit
    from wcomr.p_reference_same_state_execution_r1 import PROTOCOL,validate_execution,validate_post_proof
    c,*_=validate(args.project,args.stage);proof=validate_selected(c,args.stage)
    protocol=json.loads((args.stage/PROTOCOL).read_text())
    validate_execution(c,protocol,args.stage);validate_post_proof(c,protocol,args.stage)
    selection=json.loads((args.stage/'selection.json').read_text())
    if (selection['source_revision']!=args.source_revision or selection['selected_config_sha256']!=sha(args.stage/CONFIG)
            or selection['production_CPU_receipt_sha256']!=sha(args.stage/'production-CPU-receipt.json')
            or selection['selected_CPU_receipt_sha256']!=sha(args.stage/'selected-CPU-receipt.json')
            or selection['execution_protocol_sha256']!=sha(args.stage/PROTOCOL)):
        raise ValueError('Exact P-reference CPU, post and selected source required')
    output=args.project/'outputs'/RUN;assert not output.exists()
    lock=(args.project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=args.project/'reports/budget.json';before=json.loads(ledger.read_text());gpu=observe(UUID)
    remaining,limit=admit(c,before,gpu,proof,exact_above8_approval_verified=c['forecast_complete_GPUh']>8)
    output.mkdir();state={'status':'P_REFERENCE_COMPLETE_GPU_RUNNING','pid':os.getpid(),
        'source_revision':args.source_revision,'run_id':RUN,'config_sha256':sha(args.stage/CONFIG),
        'production_CPU_receipt_sha256':sha(args.stage/'production-CPU-receipt.json'),
        'started_unix':time.time(),'budget_before':before,'admission':gpu,'planned_scope':c['scope_counts'],
        'authorized_billed_GPUh_limit':limit,'legacy_seconds_deadline_active':False,
        'arms':[{'id':arm,'flow':flow,'planned_paths':4,'status':'UNSTARTED_REGISTERED_SCOPE_RETAINED'} for arm,flow in c['flow_arms'].items()]}
    start=time.monotonic();child=None
    reserved=dict(before);reserved.update(used_gpu_hours=before['cap_gpu_hours'],gpu_jobs_launched=before['gpu_jobs_launched']+1,
        status='P_REFERENCE_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT')
    reserved['wc_p_reference_same_state_inflight']={'supervisor_pid':os.getpid(),'run_id':RUN,'reserved_GPUh':remaining}
    write(ledger,reserved);write(output/'supervisor.json',state)
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=UUID,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lock.fileno()),
            HF_HUB_CACHE=str(args.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (output/'gpu-monitor.jsonl').open('x') as monitor:
            for row in state['arms']:
                live=observe(UUID)
                if live['pids'] or live['memory_used_mib']>1024:
                    state['resource_did_not_release_between_registered_model_processes']=live;break
                command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
                    str(args.stage/'scripts/run_wc_p_reference_same_state_r1.py'),'--project',str(args.project),'--stage',str(args.stage),
                    '--source-revision',args.source_revision,'--gpu-uuid',UUID,'--arm',row['id']]
                with (output/(row['id']+'.log')).open('x') as log:
                    child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',env=env,
                        pass_fds=(lock.fileno(),),start_new_session=True)
                    row.update(status='ORIGINAL_MODEL_PROCESS_RUNNING',pid=child.pid,command=command,started_unix=time.time())
                    write(output/'supervisor.json',state)
                    while child.poll() is None:
                        monitor.write(json.dumps({'arm':row['id'],**monitored(UUID)})+'\n');monitor.flush()
                        if (time.monotonic()-start)/3600>=limit-30/3600:
                            state['billed_budget_or_autonomy_limit_stop']=True;stop_own(child);break
                        time.sleep(2)
                    row.update(exit_code=child.wait(),ended_unix=time.time(),status='EXITED_RAW_AUDIT_PENDING')
                path=output/row['id']/'receipt.json'
                if path.exists():
                    receipt=json.loads(path.read_text());row.update(receipt_sha256=sha(path),runner_status=receipt['status'])
                else:receipt={}
                write(output/'supervisor.json',state)
                if state.get('billed_budget_or_autonomy_limit_stop'):break
                if row['exit_code']!=0:
                    state['unexpected_technical_failure_remaining_scope_retained']=row['id'];break
            state['complete_original_model_process_attempted']=all('exit_code' in a for a in state['arms'])
    except BaseException as error:
        state.update(supervisor_error_type=type(error).__name__,supervisor_error=str(error));raise
    finally:
        stop_own(child);state['release']=monitored(UUID);wall=time.monotonic()-start
        current=json.loads(ledger.read_text());assert current['wc_p_reference_same_state_inflight']['supervisor_pid']==os.getpid()
        after=dict(before);after.update(used_gpu_hours=before['used_gpu_hours']+wall/3600,
            gpu_jobs_launched=before['gpu_jobs_launched']+1,status='P_REFERENCE_SETTLED_RAW_AUDIT_PENDING')
        write(ledger,after);state.update(status='P_REFERENCE_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT',
            wall_seconds=wall,ended_unix=time.time(),budget_after=after)
        write(output/'supervisor.json',state);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':main()
