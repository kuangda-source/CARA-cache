#!/usr/bin/env python3
"""One complete N05 card; per-UUID lease and additive actual GPU accounting."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

def observe(uuid):
    values=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
    return dict(unix=time.time(),uuid=values[0].strip(),name=values[1].strip(),memory_used_mib=int(values[2]),
        compute_cap=values[3].strip(),pids=[int(r.split(',')[1]) for r in apps.splitlines() if r.split(',')[0].strip()==uuid])

def stop(child):
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage','authorization'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--gpu-uuid',required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    from wcomr.paper_baseline_production_r1 import CONFIG,RUN,COUNTS,PRODUCTION_CPU_STATUS,sha,write,validate,verify_N06_prerequisite,validate_launch_authority
    from wcomr.gpu_budget_pool_v2 import BudgetPool,DeviceLease,process_identity
    auth=json.loads(a.authorization.read_text())
    previous=verify_N06_prerequisite(a.project,auth['N06_independent_acceptance'])
    c,reg,*_=validate(a.project,a.stage)
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    validate_launch_authority(c,reg,proof,auth,revision=a.source_revision,gpu_uuid=a.gpu_uuid,
        config_sha256=sha(a.stage/CONFIG),production_sha256=sha(a.stage/'production-CPU-result.json'),registration_sha256=sha(a.stage/'registration.json'))
    pool=BudgetPool(a.project);before=pool.read()
    assert before['cap_gpu_hours']==c['cumulative_cap_GPUh']
    lease=DeviceLease(a.project,a.gpu_uuid).acquire();root=a.project/'outputs'/RUN
    child=None;reserved=False;start=None;state=None
    try:
        assert not root.exists();gpu=observe(a.gpu_uuid)
        job=dict(job_id=RUN,launch_id=auth['launch_id'],gpu_uuid=a.gpu_uuid,source_revision=a.source_revision,
            config_sha256=sha(a.stage/CONFIG),forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
            supervisor_pid=os.getpid(),supervisor_start_ticks=process_identity(os.getpid())['start_ticks'],stage=str(a.stage),scope_counts=COUNTS)
        after=pool.reserve(job,gpu);reserved=True;start=time.monotonic();root.mkdir()
        state=dict(status='N05_CORE66_GPU_RUNNING',pid=os.getpid(),supervisor_identity=process_identity(os.getpid()),
            source_revision=a.source_revision,launch_id=auth['launch_id'],run_id=RUN,gpu_uuid=a.gpu_uuid,
            scope_counts=COUNTS,config_sha256=sha(a.stage/CONFIG),started_unix=time.time(),admission=gpu,
            N06_prerequisite=previous,pool_before=before,pool_after_reservation=after,
            child_pid=None,child_exit_code=None,runner_sha256=None)
        write(root/'supervisor.json',state)
        def interrupted(signum,frame):raise KeyboardInterrupt('Own N05 supervisor interrupted: '+str(signum))
        signal.signal(signal.SIGTERM,interrupted)
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=a.gpu_uuid,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lease.handle.fileno()),
            HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        command=[sys.executable,'-u',str(a.stage/'scripts/run_wc_paper_N05_core66_r1.py'),'--project',str(a.project),
            '--stage',str(a.stage),'--source-revision',a.source_revision,'--gpu-uuid',a.gpu_uuid]
        with (root/'GPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=a.project/'runtime',env=env,
                pass_fds=(lease.handle.fileno(),),start_new_session=True)
            state.update(child_pid=child.pid,child_identity=process_identity(child.pid),command=command);write(root/'supervisor.json',state)
            while child.poll() is None:
                if (time.monotonic()-start)/3600>=c['billed_limit_GPUh']-30/3600:
                    state['own_billed_limit_stop']=True;stop(child);break
                time.sleep(10)
            state['child_exit_code']=child.wait()
    except BaseException as error:
        if state is not None:state.update(error_type=type(error).__name__,error=str(error))
        else:write(a.stage/'supervisor-admission-failure.json',dict(error_type=type(error).__name__,error=str(error),scope_counts=COUNTS,GPU_child_started=False))
        raise
    finally:
        stop(child)
        if reserved:
            wall=time.monotonic()-start;actual=wall/3600
            bill=dict(status='N05_CORE66_ACTUAL_GPU_BILL',run_id=RUN,launch_id=auth['launch_id'],source_revision=a.source_revision,
                gpu_uuid=a.gpu_uuid,wall_seconds=wall,actual_GPUh=actual,billed_limit_GPUh=c['billed_limit_GPUh'],ended_unix=time.time(),scope_counts=COUNTS)
            write(root/'billing.json',bill);settled=pool.settle(RUN,actual,sha(root/'billing.json'))
            state.update(status='N05_CORE66_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',wall_seconds=wall,actual_GPUh=actual,
                ended_unix=time.time(),billing_sha256=sha(root/'billing.json'),pool_after=settled,
                runner_sha256=sha(root/'runner.json') if (root/'runner.json').exists() else None)
            try:state['release']=observe(a.gpu_uuid)
            except Exception as error:state['release']=dict(status='TELEMETRY_UNAVAILABLE',error=str(error))
            write(root/'supervisor.json',state)
        lease.close()

if __name__=='__main__':main()
