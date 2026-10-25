#!/usr/bin/env python3
"""GPU-hidden CPU worker and one-context price supervisor inside the container."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def stop(child):
    if child is None or child.poll() is not None:return
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()


def post_limits():
    # The inference container keeps its accepted48GiB envelope. Only the post
    # child receives a stricter8GiB virtual-address-space limit and2 CPU cores.
    import resource
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    allowed=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,allowed[:2])

def supervise(a):
    from wcomr.policy_generator_r1.shared66_card import RUN,COUNTS,CONFIG,CPU_PROOF,read,sha,validate
    from wcomr.gpu_budget_pool_v2 import DeviceLease,BudgetPool,process_identity,atomic_json
    from wcomr.policy_generator_r1.production_exclusive import observe,verify
    c,reg,*_=validate(a.project,a.stage);auth=read(a.stage/'pg-GPU-authorization.json')
    from wcomr.history104_storage_r2 import storage_for
    storage=storage_for(a.stage) if c.get('storage_contract_required') else None
    if storage:storage.check()
    if (auth['source_revision']!=reg['source_revision'] or auth['registration_sha256']!=sha(a.stage/'registration.json')
            or auth['production_CPU_sha256']!=sha(a.stage/CPU_PROOF) or auth['scope_counts']!=COUNTS
            or auth['billed_limit_GPUh']!=c['billed_limit_GPUh']
            or not read(a.stage/'pg-independent-CPU-acceptance.json')['production_CPU_accepted']):
        raise ValueError('Exact new price CPU and scope authorization required')
    uuid=auth['gpu_uuid'];out=a.project/'outputs'/RUN
    lease=DeviceLease(a.project,uuid);pool=BudgetPool(a.project)
    child=None;reserved=False;start=None;state=None;monitor=[]
    def save():
        if storage:storage.persist('supervisor',out/'supervisor.json',state,atomic_json)
        else:atomic_json(out/'supervisor.json',state)
    try:
        lease.acquire()
        if storage:
            storage.check();assert storage.output==out and not any(out.iterdir())
        else:assert not out.exists()
        snap=observe(uuid);verify(snap,uuid)
        values=subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,
            '--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip().split(',')
        gpu=dict(unix=time.time(),uuid=values[0].strip(),name=values[1].strip(),memory_used_mib=int(values[2]),
            compute_cap=values[3].strip(),pids=[])
        ident=process_identity(os.getpid())
        job=dict(job_id=RUN,run_id=RUN,launch_id=auth['launch_id'],gpu_uuid=uuid,source_revision=reg['source_revision'],
            config_sha256=sha(a.stage/CONFIG),registration_sha256=sha(a.stage/'registration.json'),
            production_CPU_sha256=sha(a.stage/CPU_PROOF),authorization_sha256=sha(a.stage/'pg-GPU-authorization.json'),
            scope_counts=COUNTS,forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
            cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,
            supervisor_pid=os.getpid(),supervisor_start_ticks=ident['start_ticks'],stage=str(a.stage))
        before=pool.read();after=pool.reserve(job,gpu);reserved=True;start=time.monotonic()
        if not storage:out.mkdir()
        state=dict(status='SHARED66_GPU_RUNNING',source_revision=reg['source_revision'],run_id=RUN,
            launch_id=auth['launch_id'],gpu_uuid=uuid,scope_counts=COUNTS,supervisor_identity=ident,
            started_unix=time.time(),pool_before=before,pool_after_reservation=after,
            exclusive_monitor_accepted=False)
        save()
        def interrupted(signum,frame):raise KeyboardInterrupt('Own price supervisor interrupted')
        signal.signal(signal.SIGTERM,interrupted)
        command=[sys.executable,'-u',str(a.stage/'scripts/run_cara_shared66_r1.py'),
            '--project',str(a.project),'--stage',str(a.stage),'--source-revision',reg['source_revision'],'--gpu-uuid',uuid]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=uuid,WC_LOCK_FD=str(lease.handle.fileno()),
            WC_SUPERVISOR_PID=str(os.getpid()),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (out/'GPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,
                pass_fds=(lease.handle.fileno(),),start_new_session=True)
            identity={k:process_identity(child.pid)[k] for k in ('pid','start_ticks')};identity['uid']=os.getuid()
            state.update(child_identity=identity,child_pid=child.pid);save()
            thermal=None;thermal_at=0.
            ready=a.stage/'pg-runner-context-ready.json';granted=False
            while child.poll() is None:
                if time.monotonic()-start>=c['billed_limit_GPUh']*3600-30:
                    raise TimeoutError('Complete price card reached its own billed limit')
                snap=observe(uuid)
                if ready.exists():
                    actual=read(ready)
                    if actual['identity']!=identity:raise ValueError('Context readiness identity differs')
                    # During shutdown the process may disappear between poll and query.
                    if child.poll() is not None:break
                    verify(snap,uuid,identity)
                    if not granted:
                        atomic_json(a.stage/'pg-runner-context-granted.json',dict(runner=identity,gpu_uuid=uuid,
                            observed_unix=time.time(),source_revision=reg['source_revision']))
                        granted=True
                else:
                    apps=snap['compute_apps']
                    if apps:verify(snap,uuid,identity)
                    else:verify(snap,uuid)
                    if time.monotonic()-start>180:raise TimeoutError('Runner did not establish exact context')
                if c.get('thermal_telemetry_required') and time.monotonic()-thermal_at>=30:
                    from wcomr.policy_generator_r1.cost112_telemetry import observe as thermal_observe
                    thermal=thermal_observe(uuid);thermal_at=time.monotonic()
                monitor.append(dict(snapshot=snap,context_granted=granted,monotonic_elapsed=time.monotonic()-start))
                if thermal is not None:monitor[-1]['thermal']=thermal
                if storage:
                    storage.journal.write('telemetry',dict(launch_id=auth['launch_id'],run_id=RUN,supervisor=ident,runner=identity,sample=monitor[-1]));storage.check()
                with (out/'exclusive-monitor.jsonl').open('a') as f:f.write(json.dumps(monitor[-1])+'\n')
                time.sleep(2)
            state['child_exit_code']=child.wait()
            state['exclusive_monitor_accepted']=bool(granted and monitor and child.returncode==0)
            if child.returncode:raise RuntimeError('Original price runner failed; no replay')
    except BaseException as e:
        if state is not None:state.update(error_type=type(e).__name__,error=str(e))
        else:atomic_json(a.stage/'pg-admission-failure.json',dict(error_type=type(e).__name__,error=str(e),
            GPU_child_started=False,actual_GPUh=0))
        raise
    finally:
        try:
            stop(child)
            if reserved:
                final=None
                # Telemetry failure must never bypass actual-cost settlement.
                try:
                    final=observe(uuid);verify(final,uuid)
                except Exception as e:
                    state.update(exclusive_monitor_accepted=False,release_error=str(e))
                wall=time.monotonic()-start
                bill=dict(status='SHARED66_ACTUAL_GPU_WALL_BILL',run_id=RUN,launch_id=auth['launch_id'],
                    source_revision=reg['source_revision'],gpu_uuid=uuid,scope_counts=COUNTS,
                    wall_seconds=wall,actual_GPUh=wall/3600,billed_limit_GPUh=c['billed_limit_GPUh'],ended_unix=time.time())
                if storage:storage.journal.write('billing',bill)
                # The independent preallocated record survives output/ledger ENOSPC.
                atomic_json(out/'billing.json',bill);settled=pool.settle(RUN,wall/3600,sha(out/'billing.json'))
                if storage:storage.journal.write('accounting',dict(settled=True,billing_sha256=sha(out/'billing.json'),actual_GPUh=wall/3600))
                atomic_json(out/'exclusive-monitor-final.json',dict(accepted=state['exclusive_monitor_accepted'],
                    observations=len(monitor),final_snapshot=final,runner=state.get('child_identity'),
                    started_unix=state['started_unix'],ended_unix=time.time(),monitor_sha256=sha(out/'exclusive-monitor.jsonl')
                    if (out/'exclusive-monitor.jsonl').exists() else None))
                state.update(status='SHARED66_GPU_RELEASED_CPU_POST_PENDING',ended_unix=time.time(),actual_GPUh=wall/3600,
                    pool_after=settled,billing_sha256=sha(out/'billing.json'));save()
        finally:
            lease.close()
            if storage:
                failure=dict(status='ORIGINAL_GPU_LEASE_RELEASED',launch_id=auth['launch_id'],run_id=RUN,state=state)
                try:storage.journal.write('failure',failure)
                except Exception:pass
    if not state['exclusive_monitor_accepted']:raise RuntimeError('Original exclusive release failed; CPU scoring blocked')
    command=[sys.executable,str(a.stage/'scripts/postprocess_cara_shared66_r1.py'),
        '--project',str(a.project),'--stage',str(a.stage)]
    with (out/'post-CPU.log').open('x') as log:
        post=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'),start_new_session=True,preexec_fn=post_limits)
        state.update(post_identity=process_identity(post.pid),post_started_unix=time.time());save()
        try:code=post.wait(timeout=21600)
        except subprocess.TimeoutExpired:
            stop(post);code=124;state['post_timeout']=True
    atomic_json(out/'post-exit.json',dict(exit_code=code,CPU_only_after_UUID_release=True,ended_unix=time.time(),
        post_resource_limits=dict(address_space_bytes=8*2**30,max_affinity_cpus=2,wall_limit_seconds=21600),
        final_result_sha256=sha(out/'post-results.json') if (out/'post-results.json').exists() else None))
    state.update(status='SHARED66_CPU_POST_EXITED',post_exit_code=code);save()
    if code:raise RuntimeError('Full price postprocessing failed')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['supervise'])
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.path[:0]=[str(a.stage/'scripts'),str(a.stage/'src')]
    os.environ['CUDA_VISIBLE_DEVICES']=''
    supervise(a)

if __name__=='__main__':main()
