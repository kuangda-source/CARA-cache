#!/usr/bin/env python3
"""One complete four-parent/eight-suffix job, single GPU lock and full cost accounting."""
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
    return ['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(a.stage/'scripts/run_wc_block_velocity_r1.py'),'--project',str(a.project),'--stage',str(a.stage),'--source-revision',a.source_revision,'--gpu-uuid',uuid]


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    from wcomr.block_velocity_production_r1 import RUN,CONFIG,UUID,sha,write,validate,verify_admission
    c,reg,*_=validate(a.project,a.stage)
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['status']=='BLOCK_SAVED_VELOCITY_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
    assert proof['registration_sha256']==sha(a.stage/'registration.json') and proof['config_sha256']==sha(a.stage/CONFIG)
    assert proof['saved_reference_CPU_sha256']==sha(a.stage/'saved-reference-CPU-result.json')
    assert reg['source_revision']==a.source_revision
    curve=a.project/'.sync/wc-h1-cost-curve-production-r2-20261013'
    assert json.loads((curve/'post-CPU-exit.json').read_text())['exit_code']==0
    curve_final=json.loads((curve/'CPU-final-results.json').read_text())
    assert curve_final['status'] in ('H1_COST_CURVE_FULL40_SCIENCE_ALL60_AUDITED_93FRAME_SCORED',
                                     'H1_COST_CURVE_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED')
    assert len(curve_final['rows'])==60
    output=a.project/'outputs'/RUN;assert not output.exists()
    lock=(a.project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=a.project/'reports/budget.json';before=json.loads(ledger.read_text());gpu=observe(UUID)
    remaining,limit=verify_admission(c,before,gpu)
    output.mkdir();state={'status':'BLOCK_SAVED_VELOCITY_GPU_RUNNING','pid':os.getpid(),'run_id':RUN,
        'source_revision':a.source_revision,'config_sha256':sha(a.stage/CONFIG),'production_CPU_sha256':sha(a.stage/'production-CPU-result.json'),
        'budget_before':before,'admission':gpu,'started_unix':time.time(),'authorized_billed_GPUh_limit':limit,
        'planned_parents':4,'planned_suffixes':12,'planned_physical_pairs':312,'planned_offline_teacher_pairs':0,'model_loads':1,'legacy_seconds_deadline_active':False}
    start=time.monotonic();child=None
    reserved=dict(before);reserved.update(used_gpu_hours=before['cap_gpu_hours'],gpu_jobs_launched=before['gpu_jobs_launched']+1,status='BLOCK_SAVED_VELOCITY_INFLIGHT_REMAINING_RESERVED_NOT_ACTUAL_SPENT')
    reserved['wc_block_saved_velocity_inflight']={'supervisor_pid':os.getpid(),'run_id':RUN,'reserved_GPUh':remaining}
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
        current=json.loads(ledger.read_text());assert current['wc_block_saved_velocity_inflight']['supervisor_pid']==os.getpid()
        after=dict(before);after.update(used_gpu_hours=before['used_gpu_hours']+wall/3600,gpu_jobs_launched=before['gpu_jobs_launched']+1,status='BLOCK_SAVED_VELOCITY_SETTLED_RAW_CPU_AUDIT_PENDING')
        write(ledger,after);state.update(status='BLOCK_SAVED_VELOCITY_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',wall_seconds=wall,ended_unix=time.time(),budget_after=after,release=monitored(UUID))
        write(output/'supervisor.json',state);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
if __name__=='__main__':main()
