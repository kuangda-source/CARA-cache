#!/usr/bin/env python3
"""Complete20 model blocks and54 fresh paths under one exact full-card budget job."""
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
    from wcomr.e3_complete64_production_r1 import RUN,UUID,CONFIG,sha,write,validate,validate_selected,admit
    c,*_=validate(args.project,args.stage);proof=validate_selected(c,args.stage)
    selection=json.loads((args.stage/'selection.json').read_text())
    if (selection['source_revision']!=args.source_revision or selection['selected_config_sha256']!=sha(args.stage/CONFIG)
            or selection['production_CPU_receipt_sha256']!=sha(args.stage/'production-CPU-receipt.json')):
        raise ValueError('Exact E3 production CPU and selected source required')
    output=args.project/'outputs'/RUN;assert not output.exists()
    lock=(args.project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=args.project/'reports/budget.json';before=json.loads(ledger.read_text());gpu=observe(UUID)
    remaining,limit=admit(c,before,gpu,proof)
    output.mkdir();state={'status':'E3_COMPLETE64_REUSE10_FRESH54_GPU_RUNNING','pid':os.getpid(),
        'source_revision':args.source_revision,'run_id':RUN,'config_sha256':sha(args.stage/CONFIG),
        'production_CPU_receipt_sha256':sha(args.stage/'production-CPU-receipt.json'),
        'started_unix':time.time(),'budget_before':before,'admission':gpu,'planned_scope':c['scope_counts'],
        'authorized_billed_GPUh_limit':limit,'legacy_seconds_deadline_active':False,
        'blocks':[{'id':a['id'],'planned_paths':len(a['paths']),'status':'UNSTARTED_REGISTERED_SCOPE_RETAINED'} for a in c['blocks']]}
    start=time.monotonic();child=None
    reserved=dict(before);reserved.update(used_gpu_hours=before['cap_gpu_hours'],gpu_jobs_launched=before['gpu_jobs_launched']+1,
        status='E3_COMPLETE64_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT')
    reserved['wc_e3_complete64_inflight']={'supervisor_pid':os.getpid(),'run_id':RUN,'reserved_GPUh':remaining}
    write(ledger,reserved);write(output/'supervisor.json',state)
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=UUID,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lock.fileno()),
            HF_HUB_CACHE=str(args.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (output/'gpu-monitor.jsonl').open('x') as monitor:
            for row in state['blocks']:
                live=observe(UUID)
                if live['pids'] or live['memory_used_mib']>1024:
                    state['resource_did_not_release_between_registered_model_processes']=live;break
                command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
                    str(args.stage/'scripts/run_wc_e3_complete64_block_r1.py'),'--project',str(args.project),'--stage',str(args.stage),
                    '--block',row['id'],'--source-revision',args.source_revision,'--gpu-uuid',UUID]
                with (output/(row['id']+'.log')).open('x') as log:
                    child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',env=env,
                        pass_fds=(lock.fileno(),),start_new_session=True)
                    row.update(status='ORIGINAL_MODEL_PROCESS_RUNNING',pid=child.pid,command=command,started_unix=time.time())
                    write(output/'supervisor.json',state)
                    while child.poll() is None:
                        monitor.write(json.dumps({'block':row['id'],**monitored(UUID)})+'\n');monitor.flush()
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
                if row['exit_code']!=0 and not receipt.get('protected_capacity_failure',False):
                    state['unexpected_technical_failure_remaining_scope_retained']=row['id'];break
            state['all20_original_processes_attempted']=all('exit_code' in a for a in state['blocks'])
    except BaseException as error:
        state.update(supervisor_error_type=type(error).__name__,supervisor_error=str(error));raise
    finally:
        stop_own(child);state['release']=monitored(UUID);wall=time.monotonic()-start
        current=json.loads(ledger.read_text());assert current['wc_e3_complete64_inflight']['supervisor_pid']==os.getpid()
        after=dict(before);after.update(used_gpu_hours=before['used_gpu_hours']+wall/3600,
            gpu_jobs_launched=before['gpu_jobs_launched']+1,status='E3_COMPLETE64_SETTLED_RAW_AUDIT_PENDING')
        write(ledger,after);state.update(status='E3_COMPLETE64_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT',
            wall_seconds=wall,ended_unix=time.time(),budget_after=after)
        write(output/'supervisor.json',state);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':main()
