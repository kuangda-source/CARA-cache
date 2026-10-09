#!/usr/bin/env python3
"""Whole local-teacher card; existing autonomy/exception and cumulative50 accounting."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

INFLIGHT='wc_cfg_teacher_inflight'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def observe(uuid):
    row=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
    return {'unix':time.time(),'uuid':row[0].strip(),'name':row[1].strip(),'memory_used_mib':int(row[2]),'compute_cap':row[3].strip(),
            'pids':[int(x.split(',')[1]) for x in apps.splitlines() if x.split(',')[0].strip()==uuid]}


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-revision',required=True);args=p.parse_args()
    spec=importlib.util.spec_from_file_location('d46_validate',args.stage/'scripts/run_wc_other_scene_cfg_confirmation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);c,base=m.validate(args.project,args.stage)
    import sys
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.cfg_other_scene_teacher_production import validate_selected
    validate_selected(c,args.project,args.stage)
    execution_run=c.get('execution_run_id',c['preregistration']['run_id'])
    uuid=c['gpu_uuid'];budgetpath=args.project/'reports/budget.json';out=args.project/'outputs'/execution_run;assert not out.exists()
    lock=(args.project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    before=json.loads(budgetpath.read_text());assert before['cap_gpu_hours']==c['cumulative_cap_GPUh'] and not any('inflight' in k for k in before)
    remaining=c['cumulative_cap_GPUh']-before['used_gpu_hours'];forecast=c['preregistration']['forecast']['forecast_complete_GPUh'];assert 0<forecast<=remaining
    gpu=observe(uuid);assert gpu['uuid']==uuid and gpu['compute_cap']=='8.6' and not gpu['pids'] and gpu['memory_used_mib']<=1024
    out.mkdir();state={'status':'CFG_TEACHER_GPU_RUNNING','pid':os.getpid(),'source_revision':args.source_revision,'gpu_uuid':uuid,'run_id':execution_run,
        'config_sha256':sha(args.stage/'teacher-config.json'),'budget_before':before,'admission':gpu,'started_unix':time.time()}
    reserved=dict(before);reserved.update(used_gpu_hours=c['cumulative_cap_GPUh'],gpu_jobs_launched=before['gpu_jobs_launched']+1,status='CFG_TEACHER_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT')
    reserved[INFLIGHT]={'run_id':execution_run,'reserved_gpu_hours':remaining,'supervisor_pid':os.getpid()};write(budgetpath,reserved);write(out/'supervisor.json',state)
    start=time.monotonic();child=None
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=uuid,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lock.fileno()),PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                 HF_HUB_CACHE=str(args.project/'hfhub'),OMP_NUM_THREADS='2',
                 PYTHONPATH=str(args.stage/'src')+':.:packages/cosmos-oss:packages/cosmos-cuda')
        python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        command=[python,'-u',str(args.stage/'scripts/run_wc_other_scene_cfg_confirmation.py'),'--project',str(args.project),'--stage',str(args.stage),'--gpu-uuid',uuid,'--source-revision',args.source_revision]
        with (out/'run.log').open('x') as log,(out/'gpu-monitor.jsonl').open('x') as monitor:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',env=env,pass_fds=(lock.fileno(),),start_new_session=True)
            state['child_pid']=child.pid;write(out/'supervisor.json',state)
            while child.poll() is None:
                monitor.write(json.dumps(observe(uuid))+'\n');monitor.flush()
                if time.monotonic()-start >= min(remaining*3600-30, (7200-30 if forecast<=2 else float('inf'))):
                    state['budget_or_single_job_authorization_stop']=True;os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                    break
                time.sleep(2)
            state['exit_code']=child.wait()
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        state['release']=observe(uuid);wall=time.monotonic()-start
        current=json.loads(budgetpath.read_text());assert current[INFLIGHT]['supervisor_pid']==os.getpid()
        after=dict(before);after.update(used_gpu_hours=before['used_gpu_hours']+wall/3600,gpu_jobs_launched=before['gpu_jobs_launched']+1,status='CFG_TEACHER_SETTLED_AUDIT_PENDING')
        write(budgetpath,after);state.update(status='EXITED_REQUIRES_RESULT_AUDIT',wall_seconds=wall,budget_after=after,ended_unix=time.time(),legacy_seconds_deadline_active=False)
        write(out/'supervisor.json',state);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':main()
