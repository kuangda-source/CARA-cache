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


def supervise(a):
    from wcomr.wc73_execution_r1 import RUN,read,sha,validate,Pool as BudgetPool,MATRIX,hold
    from wcomr.gpu_budget_pool_v2 import DeviceLease,process_identity,atomic_json
    from wcomr.wc73_exclusive_r1 import observe,verify
    card,reg,auth=validate(a.project,a.stage);phase=auth['phase']
    limit={'A':5,'B':7}[phase];COUNTS=read(a.stage/'plans/cara_wc_time_protocol_r1_20261027/EXECUTION_PLAN.json')['scope_counts']
    c=dict(billed_limit_GPUh=limit,forecast_complete_GPUh=auth['forecast_GPUh'],host=auth['host'])
    from wcomr.history104_storage_r2 import storage_for
    storage=storage_for(a.stage);storage.check()
    uuid=auth['gpu_uuid'];out=a.project/'outputs'/RUN
    lease=DeviceLease(a.project,uuid);pool=BudgetPool(a.project)
    child=None;reserved=False;start=None;state=None;monitor=[]
    def save():
        if storage:storage.persist('supervisor',out/(phase+'-supervisor.json'),state,atomic_json)
        else:atomic_json(out/'supervisor.json',state)
    try:
        lease.acquire()
        if storage:
            storage.check();assert storage.output==out and not (out/(phase+'-supervisor.json')).exists()
        else:assert not out.exists()
        snap=observe(uuid);verify(snap,uuid)
        values=subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,
            '--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip().split(',')
        gpu=dict(unix=time.time(),uuid=values[0].strip(),name=values[1].strip(),memory_used_mib=int(values[2]),
            compute_cap=values[3].strip(),pids=[])
        ident=process_identity(os.getpid())
        job=dict(job_id=RUN,run_id=RUN,launch_id=auth['launch_id'],gpu_uuid=uuid,source_revision=reg['source_revision'],
            config_sha256=sha(a.stage/MATRIX),registration_sha256=sha(a.stage/'registration.json'),
            production_CPU_sha256=sha(a.stage/'execution-CPU-proof.json'),authorization_sha256=sha(a.stage/'pg-GPU-authorization.json'),
            scope_counts=COUNTS,forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=12,
            cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,
            supervisor_pid=os.getpid(),supervisor_start_ticks=ident['start_ticks'],stage=str(a.stage),host=c['host'])
        before=pool.read()
        if phase=='A':after=pool.reserve(job,gpu)
        else:
            assert not any(k!=RUN and j['status']=='RESERVED_OR_RUNNING' and not hold(j) for k,j in before['jobs'].items()),'Another expensive owned job active'
            original=before['jobs'][RUN]
            assert original['status']=='RESERVED_OR_RUNNING' and original['billed_limit_GPUh']==7 and original['gpu_uuid']==uuid
            assert original['source_revision']==reg['source_revision'] and original['host']==auth['host']
            frozen=read(out/'frozen-selection.json');assert frozen['scope_sha256']==card['scope_sha256'] and frozen['phase_A_GPU_released']
            assert sha(out/'frozen-selection.json')==auth['frozen_selection_sha256']
            after=before
        reserved=True;start=time.monotonic()
        if not storage:out.mkdir()
        state=dict(status='WC73_GPU_RUNNING',source_revision=reg['source_revision'],run_id=RUN,
            launch_id=auth['launch_id'],gpu_uuid=uuid,scope_counts=COUNTS,supervisor_identity=ident,
            started_unix=time.time(),pool_before=before,pool_after_reservation=after,
            exclusive_monitor_accepted=False)
        save()
        def interrupted(signum,frame):raise KeyboardInterrupt('Own price supervisor interrupted')
        signal.signal(signal.SIGTERM,interrupted)
        command=[sys.executable,'-u',str(a.stage/'scripts/run_cara_wc73_r1.py'),
            '--project',str(a.project),'--stage',str(a.stage),'--source-revision',reg['source_revision'],'--gpu-uuid',uuid]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=uuid,WC_LOCK_FD=str(lease.handle.fileno()),
            WC_SUPERVISOR_PID=str(os.getpid()),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (out/(phase+'-GPU.log')).open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,
                pass_fds=(lease.handle.fileno(),),start_new_session=True)
            identity={k:process_identity(child.pid)[k] for k in ('pid','start_ticks')};identity['uid']=os.getuid()
            state.update(child_identity=identity,child_pid=child.pid);save()
            ready=a.stage/'pg-runner-context-ready.json';granted=False
            while child.poll() is None:
                if time.monotonic()-start>=c['billed_limit_GPUh']*3600-120:
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
                if not monitor or time.monotonic()-monitor[-1].get('thermal_monotonic',0)>30:
                    thermal=subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,'--query-gpu=temperature.gpu,power.draw,clocks.sm,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
                    if float(thermal.split(',')[0])>=90:raise RuntimeError('Thermal stop >=90C')
                    thermal_at=time.monotonic()
                else:thermal=monitor[-1]['thermal'];thermal_at=monitor[-1]['thermal_monotonic']
                monitor.append(dict(snapshot=snap,context_granted=granted,thermal=thermal,thermal_monotonic=thermal_at,monotonic_elapsed=time.monotonic()-start))
                if storage:
                    storage.journal.write('telemetry',dict(launch_id=auth['launch_id'],run_id=RUN,supervisor=ident,runner=identity,sample=monitor[-1]));storage.check()
                with (out/(phase+'-exclusive-monitor.jsonl')).open('a') as f:f.write(json.dumps(monitor[-1])+'\n')
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
                bill=dict(status='WC73_ACTUAL_GPU_WALL_BILL',run_id=RUN,launch_id=auth['launch_id'],
                    source_revision=reg['source_revision'],gpu_uuid=uuid,scope_counts=COUNTS,
                    wall_seconds=wall,actual_GPUh=wall/3600,billed_limit_GPUh=c['billed_limit_GPUh'],ended_unix=time.time())
                if storage:storage.journal.write('billing',bill)
                # The independent preallocated record survives output/ledger ENOSPC.
                atomic_json(out/(phase+'-billing.json'),bill);settled=pool.finish_A(wall/3600,sha(out/(phase+'-billing.json')),state['exclusive_monitor_accepted']) if phase=='A' else pool.settle(RUN,wall/3600,sha(out/(phase+'-billing.json')))
                if storage:storage.journal.write('accounting',dict(settled=True,billing_sha256=sha(out/(phase+'-billing.json')),actual_GPUh=wall/3600))
                atomic_json(out/(phase+'-exclusive-monitor-final.json'),dict(accepted=state['exclusive_monitor_accepted'],
                    observations=len(monitor),final_snapshot=final,runner=state.get('child_identity'),
                    started_unix=state['started_unix'],ended_unix=time.time(),monitor_sha256=sha(out/(phase+'-exclusive-monitor.jsonl'))
                    if (out/(phase+'-exclusive-monitor.jsonl')).exists() else None))
                atomic_json(out/(phase+'-release.json'),dict(phase=phase,scope_sha256=card['scope_sha256'],GPU_released=final is not None and final['compute_apps']==[],cost_settled=True,original_process_exited=child is not None and child.poll() is not None,numerical_GPU_equivalence_passed=state['exclusive_monitor_accepted'] and (phase=='B' or read(out/'A-collection.json').get('diagnostic_gate',{}).get('passed') is True),billing_sha256=sha(out/(phase+'-billing.json'))))
                state.update(status='WC73_GPU_RELEASED_CPU_POST_PENDING',ended_unix=time.time(),actual_GPUh=wall/3600,
                    pool_after=settled,billing_sha256=sha(out/(phase+'-billing.json')));save()
        finally:
            lease.close()
            if storage:
                failure=dict(status='ORIGINAL_GPU_LEASE_RELEASED',launch_id=auth['launch_id'],run_id=RUN,state=state)
                try:storage.journal.write('failure',failure)
                except Exception:pass
    if not state['exclusive_monitor_accepted']:raise RuntimeError('Original exclusive release failed; CPU scoring blocked')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['supervise'])
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.path[:0]=[str(a.stage/'scripts'),str(a.stage/'src')]
    os.environ['CUDA_VISIBLE_DEVICES']=''
    supervise(a)

if __name__=='__main__':main()
