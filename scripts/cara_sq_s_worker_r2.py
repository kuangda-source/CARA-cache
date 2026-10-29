"""One S context and continuous monitoring; inner time is diagnostic only."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from cara_fast_worker_r2 import stop,read_thermal


def persist_sample(path,journal,sample,maximum_bytes):
    """Retain every original sample; stop with its durable trigger at the cap."""
    journal.write('telemetry',sample)
    raw=(json.dumps(sample,allow_nan=False)+'\n').encode()
    if len(raw)>65536 or (path.stat().st_size if path.exists() else 0)+len(raw)>maximum_bytes:
        raise OSError('S monitor reached its registered byte boundary; triggering journal retained')
    with path.open('ab') as stream:stream.write(raw);stream.flush()
    temperature=float(sample['thermal']['temperature.gpu'])
    if not math.isfinite(temperature):raise RuntimeError('Invalid S temperature; triggering observation retained')
    if temperature>=90:
        raise RuntimeError('Thermal stop >=90C; triggering observation retained')


def check_collection(bundle,result,output):
    from wcomr.sq_s_data_terminal_r2 import check_result
    return check_result(result,bundle['upper'],bundle['physical'],
        identity_sha256=bundle['identity']['identity_sha256'],
        resource_contract_sha256=bundle['resource_contract']['contract_sha256'],
        expected_shape=bundle['identity']['expected_real_shape'],new_output_root=str(output/'paths'))


def supervise(args):
    from wcomr.sq_s_execution_r2 import validate,read,require,make_check_schedule
    from wcomr.sq_s_spec_r2 import RUN,QUOTES,PROFILE,LIMITS,COUNTS
    from wcomr.gpu_budget_pool_v2 import DeviceLease,process_identity,atomic_json,sha
    from wcomr.sq_control_storage_r1 import storage_for
    from wcomr.wc73_exclusive_r1 import observe,verify
    bundle,registration,authority=validate(args.project,args.stage)
    storage=storage_for(args.stage);storage.check();output=args.project/'outputs'/RUN
    require(storage.output==output and not (output/'S-supervisor.json').exists(),
            'Original S handle exists; recover it, never restart')
    quote=read(args.stage/QUOTES[authority['host']]);profile=read(args.stage/PROFILE)
    hard_limit=LIMITS[authority['host']];uuid=authority['gpu_uuid']
    guardian=read(args.stage/'pg-host-guardian.json')
    require(guardian['billing_clock_owner']=='HOST_GUARDIAN' and all(
        guardian[key]==authority[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256')),
        'Original host allocation start/identity required')
    allocation_start=guardian['started_monotonic']
    deadline=allocation_start+hard_limit*3600-max(180,profile['stop_release_margin_seconds'])
    lease=DeviceLease(args.project,uuid)
    child=None;state=None;start=None;observations=0;granted=False
    def save():storage.persist('supervisor',output/'S-supervisor.json',state,atomic_json)
    try:
        lease.acquire();verify(observe(uuid),uuid)
        started=time.time();start=time.monotonic();identity=process_identity(os.getpid())
        state=dict(status='SQ_S_RUNNING',run_id=RUN,scope_counts=COUNTS,host=authority['host'],
            source_revision=registration['source_revision'],scope_sha256=authority['scope_sha256'],
            launch_id=authority['launch_id'],gpu_uuid=uuid,supervisor_identity=identity,
            started_unix=started,started_monotonic=start,allocation_started_monotonic=allocation_start,
            whole_limit_GPUh=hard_limit,exclusive_monitor_accepted=False,
            central_cost_settled=False)
        save()
        atomic_json(output/'S-check-schedule.json',make_check_schedule(authority,guardian,quote,profile))
        def interrupted(signum,frame):raise KeyboardInterrupt('Own S supervisor interrupted')
        signal.signal(signal.SIGTERM,interrupted)
        command=[sys.executable,'-u',str(args.stage/'scripts/run_cara_sq_s_r2.py'),
            '--project',str(args.project),'--stage',str(args.stage),
            '--source-revision',registration['source_revision'],'--gpu-uuid',uuid]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=uuid,WC_LOCK_FD=str(lease.handle.fileno()),
            WC_SUPERVISOR_PID=str(os.getpid()),TORCHINDUCTOR_COMPILE_THREADS='1',
            OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (output/'S-GPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,
                pass_fds=(lease.handle.fileno(),),start_new_session=True)
            runner={key:process_identity(child.pid)[key] for key in ('pid','start_ticks')}
            runner['uid']=os.getuid();state['child_identity']=runner;save()
            ready=args.stage/'pg-runner-context-ready.json';thermal=None;thermal_at=0.
            while child.poll() is None:
                elapsed=time.monotonic()-start
                if time.monotonic()>=deadline:
                    raise TimeoutError('S reached its release margin; no continuation or replay')
                # A newly published ready file cannot reinterpret an older idle snapshot.
                ready_observed=ready.exists();snapshot=observe(uuid)
                if ready_observed:
                    require(read(ready)['identity']==runner,'S context readiness identity differs')
                    if child.poll() is not None:break
                    verify(snapshot,uuid,runner)
                    if not granted:
                        atomic_json(args.stage/'pg-runner-context-granted.json',dict(runner=runner,
                            gpu_uuid=uuid,observed_unix=time.time(),source_revision=registration['source_revision']))
                        granted=True
                else:
                    verify(snapshot,uuid,runner if snapshot['compute_apps'] else None)
                    if elapsed>180:raise TimeoutError('No exact sole-runner S CUDA context')
                if thermal is None or time.monotonic()-thermal_at>=30:
                    thermal=read_thermal(uuid);thermal_at=time.monotonic()
                sample=dict(snapshot=snapshot,thermal=thermal,thermal_monotonic=thermal_at,
                    context_granted=granted,monotonic_elapsed=elapsed,launch_id=authority['launch_id'],
                    run_id=RUN,runner=runner)
                persist_sample(output/'S-exclusive-monitor.jsonl',storage.journal,sample,
                    profile['monitor_file_MiB_max']*2**20)
                observations+=1;storage.check();time.sleep(2)
            state['child_exit_code']=child.wait()
            require(child.returncode==0,'Original S runner failed; no replay')
            state['collection_classification']=check_collection(bundle,read(output/'S-collection.json'),output)
            state['collection_sha256']=sha(output/'S-collection.json')
            state['exclusive_monitor_accepted']=bool(granted and observations)
            require(state['exclusive_monitor_accepted'],'No accepted continuous S exclusive monitor')
    except BaseException as error:
        if state is None:
            atomic_json(args.stage/'pg-admission-failure.json',dict(error_type=type(error).__name__,
                error=str(error),GPU_child_started=False,diagnostic_only=True,host_allocation_bill_required=True,
                central_envelope_must_be_reconciled=True))
        else:state.update(error_type=type(error).__name__,error=str(error))
        raise
    finally:
        try:
            stop(child)
            if start is not None:
                released=False;snapshot=None
                try:snapshot=observe(uuid);verify(snapshot,uuid);released=True
                except Exception as error:state.update(exclusive_monitor_accepted=False,release_error=str(error))
                end=time.monotonic();wall=end-start
                billing=dict(status='SQ_S_SUPERVISOR_DIAGNOSTIC_ONLY',run_id=RUN,launch_id=authority['launch_id'],
                    host=authority['host'],gpu_uuid=uuid,source_revision=registration['source_revision'],
                    scope_sha256=authority['scope_sha256'],wall_seconds=wall,actual_GPUh=wall/3600,
                    billed_limit_GPUh=hard_limit,ended_unix=time.time(),started_monotonic=start,
                    ended_monotonic=end,allocation_started_monotonic=allocation_start,
                    billing_clock_owner='SUPERVISOR_DIAGNOSTIC',diagnostic_only=True,chargeable=False)
                storage.persist('supervisor_billing_diagnostic',output/'S-supervisor-billing-diagnostic.json',billing,atomic_json)
                release=dict(run_id=RUN,host=authority['host'],gpu_uuid=uuid,launch_id=authority['launch_id'],
                    source_revision=registration['source_revision'],scope_sha256=authority['scope_sha256'],
                    GPU_released=released,original_process_exited=child is not None and child.poll() is not None,
                    cost_settled=False,technical_accepted=state['exclusive_monitor_accepted'],
                    collection_classification=state.get('collection_classification'),
                    collection_sha256=state.get('collection_sha256'),billing_sha256=sha(output/'S-supervisor-billing-diagnostic.json'),
                    final_snapshot=snapshot,authorizes_retry=False,diagnostic_only=True)
                atomic_json(output/'S-supervisor-release-diagnostic.json',release)
                state.update(status='SQ_S_TERMINAL_CENTRAL_SETTLEMENT_PENDING',ended_unix=time.time(),
                    diagnostic_wall_seconds=wall,ended_monotonic=end,observations=observations,
                    supervisor_billing_sha256=release['billing_sha256'])
                save()
        finally:lease.close()
    require(state['exclusive_monitor_accepted'],'S technical acceptance failed; preserve original bill and handle')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['supervise'])
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    os.environ['CUDA_VISIBLE_DEVICES']=''
    supervise(args)


if __name__=='__main__':main()
