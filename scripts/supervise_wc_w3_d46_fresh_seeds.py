#!/usr/bin/env python3
"""One whole-card >2h exception; fresh admission and all-wall 24GPUh accounting."""
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

INFLIGHT='wc_w3_d46_fresh_seeds_inflight'


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
    spec=importlib.util.spec_from_file_location('d46_validate',args.stage/'scripts/run_wc_w3_d46_fresh_seeds.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);c,base=m.validate(args.project,args.stage)
    authority=c.get('execution_scope_authority');assert c.get('GPU_execution_selected') is True and authority
    approval=args.stage/authority['approval_ref'];assert sha(approval)==authority['approval_sha256']
    approved=json.loads(approval.read_text());assert approved['approved_card']==c['preregistration']['card'] and approved['run_id']==c['preregistration']['run_id']
    assert approved['complete_scope']==c['preregistration']['scope_counts'] and approved['usage_reset'] is False and approved['source_user_text']
    cpu=args.project/c['production_cpu_stage']/'receipt.json';assert sha(cpu)==c['production_cpu_receipt_sha256']
    proof=json.loads(cpu.read_text());assert proof['exit_code']==0 and proof['CUDA_initialized'] is False and proof['GPU_submissions']==0
    assert proof['new_payload_sha256']==c['production_cpu_payload_sha256']
    assert all(c['payload_sha256'].get(n)==h for n,h in proof['new_payload_sha256'].items() if n!='seed-config.json')
    uuid=c['gpu_uuid'];budgetpath=args.project/'reports/budget.json';out=args.project/'outputs'/c['preregistration']['run_id'];assert not out.exists()
    lock=(args.project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    before=json.loads(budgetpath.read_text());assert before['cap_gpu_hours']==24 and not any('inflight' in k for k in before)
    remaining=24-before['used_gpu_hours'];forecast=c['preregistration']['cost']['forecast_complete_GPUh'];assert 2<forecast<=remaining
    gpu=observe(uuid);assert gpu['uuid']==uuid and gpu['compute_cap']=='8.6' and not gpu['pids'] and gpu['memory_used_mib']<=1024
    out.mkdir();state={'status':'D46_GPU_RUNNING','pid':os.getpid(),'source_revision':args.source_revision,'gpu_uuid':uuid,
        'config_sha256':sha(args.stage/'seed-config.json'),'budget_before':before,'admission':gpu,'started_unix':time.time()}
    reserved=dict(before);reserved.update(used_gpu_hours=24,gpu_jobs_launched=before['gpu_jobs_launched']+1,status='D46_SEED_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT')
    reserved[INFLIGHT]={'run_id':c['preregistration']['run_id'],'reserved_gpu_hours':remaining,'supervisor_pid':os.getpid()};write(budgetpath,reserved);write(out/'supervisor.json',state)
    start=time.monotonic();child=None
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=uuid,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lock.fileno()),PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        command=[python,'-u',str(args.stage/'scripts/run_wc_w3_d46_fresh_seeds.py'),'--project',str(args.project),'--stage',str(args.stage),'--gpu-uuid',uuid,'--source-revision',args.source_revision]
        with (out/'run.log').open('x') as log,(out/'gpu-monitor.jsonl').open('x') as monitor:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',env=env,pass_fds=(lock.fileno(),),start_new_session=True)
            state['child_pid']=child.pid;write(out/'supervisor.json',state)
            while child.poll() is None:
                monitor.write(json.dumps(observe(uuid))+'\n');monitor.flush()
                if time.monotonic()-start >= remaining*3600-30:
                    state['cumulative_budget_stop']=True;os.killpg(child.pid,signal.SIGTERM)
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
        after=dict(before);after.update(used_gpu_hours=before['used_gpu_hours']+wall/3600,gpu_jobs_launched=before['gpu_jobs_launched']+1,status='D46_SEED_SETTLED_AUDIT_PENDING')
        write(budgetpath,after);state.update(status='EXITED_REQUIRES_RESULT_AUDIT',wall_seconds=wall,budget_after=after,ended_unix=time.time(),legacy_seconds_deadline_active=False)
        write(out/'supervisor.json',state);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':main()
