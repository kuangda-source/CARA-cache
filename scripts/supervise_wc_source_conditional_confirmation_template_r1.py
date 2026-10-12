#!/usr/bin/env python3
"""One complete full24 plus12 warmup job; kernel GPU lock and whole cost."""
import argparse,fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
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


def child_command(a,uuid):
    return ['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(a.stage/'scripts/run_wc_source_conditional_confirmation_template_r1.py'),'--project',str(a.project),'--stage',str(a.stage),'--source-revision',a.source_revision,'--gpu-uuid',uuid]


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    from wcomr.source_conditional_confirmation_production_template_r1 import RUN,CONFIG,UUID,sha,write,validate,verify_admission
    c,reg,*_=validate(a.project,a.stage)
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['status']=='SOURCE_CONFIRMATION_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
    assert proof['registration_sha256']==sha(a.stage/'registration.json') and proof['config_sha256']==sha(a.stage/CONFIG)
    assert reg['source_revision']==a.source_revision
    output=a.project/'outputs'/RUN;assert not output.exists()
    lock=(a.project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=a.project/'reports/budget.json';before=json.loads(ledger.read_text());gpu=observe(UUID)
    remaining,limit=verify_admission(c,before,gpu)
    output.mkdir();state={'status':'SOURCE_CONFIRMATION_GPU_RUNNING','pid':os.getpid(),'run_id':RUN,
        'source_revision':a.source_revision,'config_sha256':sha(a.stage/CONFIG),'production_CPU_sha256':sha(a.stage/'production-CPU-result.json'),
        'budget_before':before,'admission':gpu,'started_unix':time.time(),'authorized_billed_GPUh_limit':limit,
        'planned_scientific_paths':40,'planned_warmup_paths':10,'planned_physical_pairs':1800,'model_loads':1,'legacy_seconds_deadline_active':False}
    start=time.monotonic();child=None
    reserved=dict(before);reserved.update(used_gpu_hours=before['cap_gpu_hours'],gpu_jobs_launched=before['gpu_jobs_launched']+1,status='SOURCE_CONFIRMATION_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT')
    reserved['wc_source_confirmation_inflight']={'supervisor_pid':os.getpid(),'run_id':RUN,'reserved_GPUh':remaining}
    write(ledger,reserved);write(output/'supervisor.json',state)
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=UUID,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lock.fileno()),
            HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        command=child_command(a,UUID)
        with (output/'GPU.log').open('x') as log,(output/'gpu-monitor.jsonl').open('x') as monitor:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=a.project/'runtime',env=env,pass_fds=(lock.fileno(),),start_new_session=True)
            state.update(child_pid=child.pid,command=command);write(output/'supervisor.json',state)
            while child.poll() is None:
                monitor.write(json.dumps(monitored(UUID))+'\n');monitor.flush()
                if (time.monotonic()-start)/3600>=limit-30/3600:
                    state['billed_budget_or_autonomy_limit_stop']=True;stop_own(child);break
                time.sleep(5)
            state['child_exit_code']=child.wait()
            path=output/'runner.json'
            if path.exists():state.update(runner_sha256=sha(path),runner_status=json.loads(path.read_text())['status'])
    except BaseException as e:
        state.update(supervisor_error_type=type(e).__name__,supervisor_error=str(e));raise
    finally:
        stop_own(child);wall=time.monotonic()-start
        current=json.loads(ledger.read_text());assert current['wc_source_confirmation_inflight']['supervisor_pid']==os.getpid()
        after=dict(before);after.update(used_gpu_hours=before['used_gpu_hours']+wall/3600,gpu_jobs_launched=before['gpu_jobs_launched']+1,status='SOURCE_CONFIRMATION_SETTLED_RAW_CPU_AUDIT_PENDING')
        write(ledger,after);state.update(status='SOURCE_CONFIRMATION_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',wall_seconds=wall,ended_unix=time.time(),budget_after=after,release=monitored(UUID))
        write(output/'supervisor.json',state);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
if __name__=='__main__':main()
