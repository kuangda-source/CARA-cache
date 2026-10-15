#!/usr/bin/env python3
"""One complete mainline card with a UUID lease and additive actual bill."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path

def observe(uuid):
    values=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
    return dict(unix=time.time(),uuid=values[0].strip(),name=values[1].strip(),memory_used_mib=int(values[2]),compute_cap=values[3].strip(),pids=[int(v.split(',')[1]) for v in apps.splitlines() if v.split(',')[0].strip()==uuid])

def stop(child):
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()

def child_command(a):
    return [sys.executable,'-u',str(a.stage/'scripts/run_wc_simple26d_full36_r1.py'),'--project',str(a.project),
        '--stage',str(a.stage),'--source-revision',a.source_revision,'--gpu-uuid',a.gpu_uuid]

def main():
    p=argparse.ArgumentParser()
    for k in ('project','stage','authorization'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--gpu-uuid',required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    from wcomr.simple26d_r1 import validate,CONFIG,RUN,PRODUCTION_CPU_STATUS,sha,write,COUNTS
    from wcomr.gpu_budget_pool_v2 import BudgetPool,DeviceLease,process_identity,same_live_process
    c,reg,*_=validate(a.project,a.stage);auth=json.loads(a.authorization.read_text())
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert reg['source_revision']==a.source_revision==proof['source_revision']==auth['source_revision']
    assert proof['status']==PRODUCTION_CPU_STATUS and proof['exit_code']==0
    assert proof['registration_sha256']==sha(a.stage/'registration.json') and proof['config_sha256']==sha(a.stage/CONFIG)
    assert auth['direct_user_authorization'] and auth['user_reply_quote'] and auth['launch_id']
    assert auth['config_sha256']==sha(a.stage/CONFIG) and auth['production_CPU_sha256']==sha(a.stage/'production-CPU-result.json')
    assert auth['cumulative_cap_GPUh']==c['cumulative_cap_GPUh'] and auth['autonomy_exclusive_upper_GPUh']==12
    assert auth['gpu_uuid']==a.gpu_uuid and auth['whole_card_run']==RUN
    pool=BudgetPool(a.project);before=pool.read();legacy=before['jobs'][before['legacy_job_id']]
    if legacy['status']=='RESERVED_OR_RUNNING':
        bridge=json.loads((a.stage/'legacy-bridge.json').read_text())
        ident=process_identity(bridge['pid'])
        assert ident['state'] not in (None,'Z','X') and 'bridge_wc_legacy_w3_budget_v2.py' in ident['command']
        assert legacy['gpu_uuid']!=a.gpu_uuid and bridge['original_supervisor_pid']==legacy['supervisor_pid']
    lease=DeviceLease(a.project,a.gpu_uuid).acquire();out=a.project/'outputs'/RUN
    child=None;start=None;reserved=False;state=None
    try:
        assert not out.exists();gpu=observe(a.gpu_uuid)
        job=dict(job_id=RUN,launch_id=auth['launch_id'],gpu_uuid=a.gpu_uuid,source_revision=a.source_revision,
            config_sha256=sha(a.stage/CONFIG),forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
            supervisor_pid=os.getpid(),supervisor_start_ticks=process_identity(os.getpid())['start_ticks'],stage=str(a.stage),scope_counts=COUNTS)
        after=pool.reserve(job,gpu);reserved=True;start=time.monotonic();out.mkdir()
        state=dict(status='SIMPLE26D_GPU_RUNNING',pid=os.getpid(),supervisor_identity=process_identity(os.getpid()),
            source_revision=a.source_revision,run_id=RUN,launch_id=auth['launch_id'],gpu_uuid=a.gpu_uuid,
            config_sha256=sha(a.stage/CONFIG),scope_counts=COUNTS,started_unix=time.time(),
            admission=gpu,pool_before=before,pool_after_reservation=after,child_pid=None,child_exit_code=None,
            runner_sha256=None,legacy_job_untouched=True,timing_claim=c['timing_claim'])
        write(out/'supervisor.json',state)
        def interrupted(signum,frame):raise KeyboardInterrupt('Own simple26D supervisor interrupted: '+str(signum))
        signal.signal(signal.SIGTERM,interrupted)
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=a.gpu_uuid,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(lease.handle.fileno()),
            HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (out/'GPU.log').open('x') as log:
            command=child_command(a);child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=a.project/'runtime',
                env=env,pass_fds=(lease.handle.fileno(),),start_new_session=True)
            state.update(child_pid=child.pid,child_identity=process_identity(child.pid),command=command);write(out/'supervisor.json',state)
            while child.poll() is None:
                if (time.monotonic()-start)/3600>=c['billed_limit_GPUh']-30/3600:
                    state['own_billed_limit_stop']=True;stop(child);break
                time.sleep(10)
            state['child_exit_code']=child.wait()
    except BaseException as e:
        if state is not None:state.update(error_type=type(e).__name__,error=str(e))
        raise
    finally:
        stop(child)
        if reserved:
            wall=time.monotonic()-start;actual=wall/3600
            bill=dict(status='SIMPLE26D_ACTUAL_GPU_BILL',run_id=RUN,launch_id=auth['launch_id'],gpu_uuid=a.gpu_uuid,
                source_revision=a.source_revision,wall_seconds=wall,actual_GPUh=actual,
                billed_limit_GPUh=c['billed_limit_GPUh'],ended_unix=time.time(),scope_counts=COUNTS)
            out.mkdir(exist_ok=True);write(out/'billing.json',bill)
            settled=pool.settle(RUN,actual,sha(out/'billing.json'))
            if state is None:state=dict(pid=os.getpid(),child_pid=None,child_exit_code=None,run_id=RUN,source_revision=a.source_revision)
            path=out/'runner.json'
            state.update(status='SIMPLE26D_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT',wall_seconds=wall,actual_GPUh=actual,
                ended_unix=time.time(),billing_sha256=sha(out/'billing.json'),pool_after=settled,
                runner_sha256=sha(path) if path.exists() else None)
            try:state['release']=observe(a.gpu_uuid)
            except Exception as e:state['release']=dict(status='TELEMETRY_UNAVAILABLE',error=str(e))
            write(out/'supervisor.json',state)
        lease.close()

if __name__=='__main__':main()
