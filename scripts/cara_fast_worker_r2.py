"""One A32 GPU context under the original lease, exclusivity and thermal gates."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def stop(child):
    if child is None or child.poll() is not None:
        return
    os.killpg(child.pid,signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL)
        child.wait()


def read_thermal(uuid):
    fields=['temperature.gpu','power.draw','clocks.sm','utilization.gpu','memory.used',
            'fan.speed','clocks_event_reasons.active']
    values=subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,
        '--query-gpu='+','.join(fields),'--format=csv,noheader,nounits'],text=True,timeout=15).strip().split(',')
    return dict(zip(fields,[v.strip() for v in values]))


def persist_sample(path, journal, sample):
    """Retain the triggering temperature/fan/throttle observation before stopping."""
    journal.write('telemetry',sample)
    with path.open('a') as handle:
        handle.write(json.dumps(sample)+'\n')
        handle.flush()
    if float(sample['thermal']['temperature.gpu'])>=90:
        raise RuntimeError('Thermal stop >=90C; triggering observation retained')


def supervise(args):
    from wcomr.cara_fast_execution_r2 import validate,read,require,RUN,QUOTE,HARD_GPUH,check_complete_A
    from wcomr.gpu_budget_pool_v2 import DeviceLease,process_identity,atomic_json,sha
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.wc73_exclusive_r1 import observe,verify
    card,registration,authority=validate(args.project,args.stage)
    storage=storage_for(args.stage)
    storage.check()
    output=args.project/'outputs'/RUN
    require(storage.output==output and not (output/'A-supervisor.json').exists(),
            'Original A32 handle exists; recover it, never restart')
    quote=read(args.stage/QUOTE)['host_quotes'][authority['host']]['phases']['A']
    uuid=authority['gpu_uuid']
    lease=DeviceLease(args.project,uuid)
    child=None
    state=None
    start=None
    observations=0
    granted=False

    def save():
        storage.persist('supervisor',output/'A-supervisor.json',state,atomic_json)

    try:
        lease.acquire()
        verify(observe(uuid),uuid)
        started_unix=time.time()
        start=time.monotonic()
        identity=process_identity(os.getpid())
        state=dict(status='FAST_A32_RUNNING',run_id=RUN,phase='A',physical_paths=32,
            source_revision=registration['source_revision'],scope_sha256=card['scope_sha256'],
            launch_id=authority['launch_id'],gpu_uuid=uuid,host=authority['host'],
            supervisor_identity=identity,started_unix=started_unix,whole_limit_GPUh=HARD_GPUH,
            exclusive_monitor_accepted=False,central_cost_settled=False)
        save()
        atomic_json(output/'A-check-schedule.json',dict(run_id=RUN,launch_id=authority['launch_id'],
            gpu_uuid=uuid,source_revision=registration['source_revision'],started_unix=started_unix,
            halfway_unix=started_unix+quote['forecast_GPUh']*1800,
            expected_terminal_unix=started_unix+quote['forecast_GPUh']*3600,
            hard_terminal_unix=started_unix+HARD_GPUH*3600,
            midway_scope='Operational handle, progress, thermal, exclusivity and ledger only; no science scores',
            terminal_scope='Original process/container exit, complete32 or retained failures, gate, artifacts, release and central bill',
            scheduler_created=False,authorizes_retry=False,authorizes_phase_B=False))
        def interrupted(signum,frame):
            raise KeyboardInterrupt('Own A32 supervisor interrupted')
        signal.signal(signal.SIGTERM,interrupted)
        command=[sys.executable,'-u',str(args.stage/'scripts/run_cara_fast_r2.py'),
            '--project',str(args.project),'--stage',str(args.stage),
            '--source-revision',registration['source_revision'],'--gpu-uuid',uuid]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=uuid,WC_LOCK_FD=str(lease.handle.fileno()),
                 WC_SUPERVISOR_PID=str(os.getpid()),TORCHINDUCTOR_COMPILE_THREADS='1',
                 OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (output/'A-GPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,
                pass_fds=(lease.handle.fileno(),),start_new_session=True)
            runner={k:process_identity(child.pid)[k] for k in ('pid','start_ticks')}
            runner['uid']=os.getuid()
            state['child_identity']=runner
            save()
            ready=args.stage/'pg-runner-context-ready.json'
            thermal=None
            thermal_at=0
            while child.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed>=HARD_GPUH*3600-quote['stop_release_margin_seconds']:
                    raise TimeoutError('A32 reached its own release margin; no continuation or replay')
                snapshot=observe(uuid)
                if ready.exists():
                    require(read(ready)['identity']==runner, 'Context readiness identity differs')
                    if child.poll() is not None:
                        break
                    verify(snapshot,uuid,runner)
                    if not granted:
                        atomic_json(args.stage/'pg-runner-context-granted.json',dict(runner=runner,
                            gpu_uuid=uuid,observed_unix=time.time(),source_revision=registration['source_revision']))
                        granted=True
                else:
                    verify(snapshot,uuid,runner if snapshot['compute_apps'] else None)
                    if elapsed>180:
                        raise TimeoutError('No exact sole-runner GPU context')
                if thermal is None or time.monotonic()-thermal_at>=30:
                    thermal=read_thermal(uuid)
                    thermal_at=time.monotonic()
                sample=dict(snapshot=snapshot,thermal=thermal,thermal_monotonic=thermal_at,
                            context_granted=granted,monotonic_elapsed=elapsed,
                            launch_id=authority['launch_id'],run_id=RUN,runner=runner)
                persist_sample(output/'A-exclusive-monitor.jsonl',storage.journal,sample)
                observations+=1
                storage.check()
                time.sleep(2)
            state['child_exit_code']=child.wait()
            require(child.returncode==0, 'Original A32 runner failed; no replay')
            state['phase_state_sha256']=check_complete_A(card,read(output/'A-collection.json'))
            state['exclusive_monitor_accepted']=bool(granted and observations)
            require(state['exclusive_monitor_accepted'], 'No accepted continuous exclusive monitor')
    except BaseException as error:
        if state is None:
            atomic_json(args.stage/'pg-admission-failure.json',dict(error_type=type(error).__name__,
                error=str(error),GPU_child_started=False,actual_GPUh=0,
                central_envelope_must_be_reconciled=True))
        else:
            state.update(error_type=type(error).__name__,error=str(error))
        raise
    finally:
        try:
            stop(child)
            if start is not None:
                released=False
                snapshot=None
                try:
                    snapshot=observe(uuid)
                    verify(snapshot,uuid)
                    released=True
                except Exception as error:
                    state.update(exclusive_monitor_accepted=False,release_error=str(error))
                wall=time.monotonic()-start
                billing=dict(status='FAST_A32_ORIGINAL_WALL_BILL',run_id=RUN,phase='A',
                    launch_id=authority['launch_id'],gpu_uuid=uuid,host=authority['host'],
                    source_revision=registration['source_revision'],scope_sha256=card['scope_sha256'],
                    wall_seconds=wall,actual_GPUh=wall/3600,billed_limit_GPUh=HARD_GPUH,
                    ended_unix=time.time(),central_settlement_pending=True)
                storage.journal.write('billing',billing)
                atomic_json(output/'A-billing.json',billing)
                release=dict(phase='A',scope_sha256=card['scope_sha256'],run_id=RUN,
                    host=authority['host'],gpu_uuid=uuid,launch_id=authority['launch_id'],
                    GPU_released=released,original_process_exited=child is not None and child.poll() is not None,
                    cost_settled=False,technical_accepted=state['exclusive_monitor_accepted'],
                    phase_state_sha256=state.get('phase_state_sha256'),billing_sha256=sha(output/'A-billing.json'),
                    final_snapshot=snapshot,authorizes_phase_B=False)
                atomic_json(output/'A-release-pending-central.json',release)
                state.update(status='FAST_A32_TERMINAL_CENTRAL_SETTLEMENT_PENDING',ended_unix=time.time(),
                             actual_GPUh=wall/3600,observations=observations,billing_sha256=release['billing_sha256'])
                save()
        finally:
            lease.close()
    require(state['exclusive_monitor_accepted'], 'A32 technical acceptance failed; preserve original handle and costs')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['supervise'])
    for key in ('project','stage'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    os.environ['CUDA_VISIBLE_DEVICES']=''
    supervise(args)


if __name__=='__main__':
    main()
