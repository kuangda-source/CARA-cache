#!/usr/bin/env python3
"""One complete selected E2 GPU card, scoped8 and exact-above8 approval."""
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
    row=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap',
        '--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'],text=True,timeout=10)
    return {'unix':time.time(),'uuid':row[0].strip(),'name':row[1].strip(),'memory_used_mib':int(row[2]),
        'compute_cap':row[3].strip(),'pids':[int(v.split(',')[1]) for v in apps.splitlines() if v.split(',')[0].strip()==uuid]}


def monitored(uuid):
    try:return observe(uuid)
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError,OSError) as error:
        return {'unix':time.time(),'uuid':uuid,'status':'TELEMETRY_UNAVAILABLE_RUNNER_NOT_INTERRUPTED','error':str(error)}


def stop_own(child):
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_CACHE=str(args.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e2_execution_r1 import RUN,UUID,sha,write,validate_execution,admit
    from wcomr.e2_confirmation_production_r1 import validate,validate_selected
    c,*_=validate(args.project,args.stage);validate_selected(c,args.project,args.stage)
    p=json.loads((args.stage/'execution-protocol.json').read_text());validate_execution(c,p,args.stage)
    selected=args.stage/'selected-CPU-receipt.json';selected_CPU=json.loads(selected.read_text())
    proof=json.loads((args.stage/'selection.json').read_text())
    if (sha(selected)!=proof['selected_CPU_receipt_sha256'] or sha(args.stage/'e2-config.json')!=proof['selected_config_sha256']
            or sha(args.stage/'execution-protocol.json')!=proof['execution_protocol_sha256']
            or proof['source_revision']!=args.source_revision):
        raise ValueError('Exact source-bound selected execution CPU proof changed')
    out=args.project/'outputs'/RUN;assert not out.exists()
    lock=(args.project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=args.project/'reports/budget.json';before=json.loads(ledger.read_text());gpu=observe(UUID)
    remaining,limit=admit(c,before,gpu,selected_CPU,sha(args.stage/'execution-protocol.json'))
    out.mkdir();state={'status':'E2_FULL76_GPU_RUNNING','pid':os.getpid(),'source_revision':args.source_revision,
        'run_id':RUN,'gpu_uuid':UUID,'config_sha256':sha(args.stage/'e2-config.json'),
        'execution_protocol_sha256':sha(args.stage/'execution-protocol.json'),'selected_CPU_receipt_sha256':sha(selected),
        'budget_before':before,'admission':gpu,'started_unix':time.time(),'scope_counts':c['scope_counts'],
        'authorized_billed_GPUh_limit':limit,'legacy_seconds_deadline_active':False}
    reserved=dict(before);reserved.update(used_gpu_hours=before['cap_gpu_hours'],
        gpu_jobs_launched=before['gpu_jobs_launched']+1,status='E2_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT')
    reserved['wc_e2_full76_inflight']={'supervisor_pid':os.getpid(),'run_id':RUN,'reserved_GPUh':remaining}
    write(ledger,reserved);write(out/'supervisor.json',state);start=time.monotonic();child=None
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=UUID,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lock.fileno()),
            PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
            str(args.stage/'scripts/run_wc_e2_observed_r1.py'),'--project',str(args.project),'--stage',str(args.stage),
            '--source-revision',args.source_revision,'--gpu-uuid',UUID]
        with (out/'run.log').open('x') as log,(out/'gpu-monitor.jsonl').open('x') as monitor:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                env=env,pass_fds=(lock.fileno(),),start_new_session=True)
            state.update(child_pid=child.pid,command=command);write(out/'supervisor.json',state)
            while child.poll() is None:
                monitor.write(json.dumps(monitored(UUID))+'\n');monitor.flush()
                if (time.monotonic()-start)/3600>=limit-30/3600:
                    state['billed_budget_or_autonomy_limit_stop']=True;stop_own(child);break
                time.sleep(2)
            state['exit_code']=child.wait()
    except BaseException as error:
        state.update(supervisor_error_type=type(error).__name__,supervisor_error=str(error));raise
    finally:
        stop_own(child);state['exit_code']=child.wait() if child is not None else None
        state['release']=monitored(UUID);wall=time.monotonic()-start
        current=json.loads(ledger.read_text());assert current['wc_e2_full76_inflight']['supervisor_pid']==os.getpid()
        after=dict(before);after.update(used_gpu_hours=before['used_gpu_hours']+wall/3600,
            gpu_jobs_launched=before['gpu_jobs_launched']+1,status='E2_FULL76_SETTLED_AUDIT_PENDING')
        write(ledger,after);state.update(status='EXITED_REQUIRES_COMPLETE76_RAW_AND_SCORE_AUDIT',
            wall_seconds=wall,budget_after=after,ended_unix=time.time())
        write(out/'supervisor.json',state);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':main()
