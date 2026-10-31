"""Original child supervision under an admitted host guardian.

No standalone dispatch CLI or budget reservation. The enclosing once-dispatch
entry owns approval, full CPU/source/asset admission and the container command.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from .cara_s_endpoint_lifecycle_r1 import IDENTITY
from .cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from .cara_budget_search_journal_r1 import create_record,read_record
from .gpu_budget_pool_v2 import DeviceLease,atomic_json,sha
from .policy_price_terminal_r1 import require
from .wc73_exclusive_r1 import observe,verify

SOURCE='src/wcomr/cara_s_endpoint_supervisor_r1.py'
BOOTSTRAP='scripts/cara_budget_process_bootstrap_r1.py'


def read_thermal(uuid):
    fields=['temperature.gpu','power.draw','clocks.sm','utilization.gpu','memory.used','fan.speed','clocks_event_reasons.active']
    values=subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,'--query-gpu='+','.join(fields),
        '--format=csv,noheader,nounits'],text=True,timeout=15).strip().split(',')
    return dict(zip(fields,[v.strip() for v in values]))


def stop_original(child,identity):
    if child is None or child.poll() is not None:return
    observation=observe_original_process(identity)
    require(observation['original_live'] is True,'Original child identity unknown; do not signal another process')
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        # Popen still owns the unreaped child, so its PID cannot have been reused.
        os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)


def supervise(project,stage,storage,*,cpu_validation=False,observe_gpu=observe,thermal=read_thermal,
              interval=2.,context_timeout=180.,release_margin=600.,thermal_period=30.,monotonic=time.monotonic):
    stage=Path(stage);project=Path(project)
    launch=read_record(stage/'GPU-launch.json');registration=read_record(stage/'registration.json')
    require(launch['CPU_fixture_only'] is cpu_validation,'CPU fixtures cannot supervise a production GPU allocation')
    require(launch['stage']==str(stage) and stage.parent==project/'.sync'
            and sha(stage/'registration.json')==launch['registration_sha256']
            and registration['payload_sha256'][SOURCE]==sha(__file__)
            and registration['payload_sha256'][BOOTSTRAP]==sha(stage/BOOTSTRAP),
            'Original registered supervisor and bootstrap required')
    if not cpu_validation:
        require(interval==2. and context_timeout==180. and release_margin==600. and thermal_period==30.,'Frozen production monitor bounds required')
    require(0<interval<=2 and 0<context_timeout<=180 and 0<thermal_period<=30 and 0<release_margin<launch['billed_limit_GPUh']*3600,
            'Bounded monitoring and original release margin required')
    guardian=read_record(stage/'guardian.json')
    require(all(guardian[k]==launch[k] for k in IDENTITY)
            and guardian['original_handles']['guardian']==launch['guardian_identity'],
            'Original allocation guardian differs')
    started=guardian['started_monotonic'];uuid=launch['gpu_uuid']
    identity=bind_original_process(os.getpid())
    require(identity['host_view']==launch['guardian_identity']['host_view']
            and (identity['pid'],identity['start_ticks'])!=(launch['guardian_identity']['pid'],launch['guardian_identity']['start_ticks']),
            'Distinct supervisor must share the original host PID view')
    create_record(stage/'supervisor-start.json',dict(identity=identity,launch_id=launch['launch_id'],started_unix=time.time()))
    state={k:launch[k] for k in IDENTITY}
    state.update(status='CARA_ENDPOINT_SUPERVISOR_RUNNING_R1',identity=identity,
        started_unix=time.time(),runner_dispatch_state='NOT_ATTEMPTED',observations=0,context_granted=False,
        complete_endpoint_accepted=False,CPU_fixture_only=cpu_validation)
    child=None;handle=None;lease=DeviceLease(project,uuid);failure=None
    previous_handler=signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):raise KeyboardInterrupt('Original endpoint supervisor interrupted')
    def save():storage.persist('supervisor',stage/'supervisor.json',state,atomic_json)
    def remaining():
        value=launch['billed_limit_GPUh']*3600-release_margin-(monotonic()-started)
        if value<=0:raise TimeoutError('Original guardian allocation reached release margin')
        return value
    try:
        save();remaining();storage.check();lease.acquire();verify(observe_gpu(uuid),uuid)
        initial_thermal=thermal(uuid)
        storage.journal.write('telemetry',dict(thermal=initial_thermal,launch_id=launch['launch_id'],before_dispatch=True))
        require(float(initial_thermal['temperature.gpu'])<90,'Thermal stop >=90C before original dispatch')
        signal.signal(signal.SIGTERM,interrupted)
        create_record(stage/'runner-intent.json',dict(launch_id=launch['launch_id'],source_revision=launch['source_revision'],
            command=launch['commands']['runner'],supervisor_identity=identity,no_replay=True))
        state['runner_dispatch_state']='INTENT_WRITTEN';save()
        environment=dict(os.environ,CUDA_VISIBLE_DEVICES='' if cpu_validation else uuid,
            WC_LOCK_FD=str(lease.handle.fileno()),WC_SUPERVISOR_PID=str(os.getpid()),
            TORCHINDUCTOR_COMPILE_THREADS='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        if cpu_validation:environment['NVIDIA_VISIBLE_DEVICES']='void'
        with (stage/'runner.log').open('x') as log:
            child=subprocess.Popen([sys.executable,str(stage/BOOTSTRAP),'--stage',str(stage),'--role','runner'],
                env=environment,pass_fds=(lease.handle.fileno(),),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        handle=bind_original_process(child.pid)
        state.update(runner_dispatch_state='STARTED',runner_identity=handle);save()
        # The bootstrap writes its start witness before exec, then waits for us.
        begin=monotonic()
        while not (stage/'runner-start.json').exists():
            remaining()
            if child.poll() is not None:raise RuntimeError('Original runner bootstrap exited before its witness')
            if monotonic()-begin>=30:raise TimeoutError('Original runner start witness unavailable')
            time.sleep(min(interval,.02))
        require(read_record(stage/'runner-start.json')['identity']==handle,'Original bootstrap identity differs')
        create_record(stage/'runner-dispatch-grant.json',dict(identity=handle,launch_sha256=sha(stage/'GPU-launch.json')))
        runner=dict(pid=handle['pid'],start_ticks=handle['start_ticks'],uid=os.getuid())
        ready=stage/'pg-runner-context-ready.json';last_thermal=initial_thermal;thermal_at=monotonic()
        while child.poll() is None:
            remaining()
            # A newly published readiness witness cannot validate an older GPU sample.
            context_ready=ready.exists()
            snapshot=observe_gpu(uuid)
            if context_ready:
                require(read_record(ready)['identity']==runner,'Original GPU context readiness differs')
                if child.poll() is not None:break
                verify(snapshot,uuid,runner)
                if not state['context_granted']:
                    create_record(stage/'pg-runner-context-granted.json',dict(runner=runner,gpu_uuid=uuid,
                        observed_unix=time.time(),source_revision=launch['source_revision']))
                    state['context_granted']=True
            else:
                verify(snapshot,uuid,runner if snapshot['compute_apps'] else None)
                if monotonic()-begin>=context_timeout:raise TimeoutError('No original sole-runner GPU context')
            if monotonic()-thermal_at>=thermal_period:
                last_thermal=thermal(uuid);thermal_at=monotonic()
            sample=dict(snapshot=snapshot,thermal=last_thermal,thermal_monotonic=thermal_at,
                launch_id=launch['launch_id'],runner=runner,context_granted=state['context_granted'],
                original_allocation_elapsed=monotonic()-started)
            storage.journal.write('telemetry',sample)
            with (stage/'exclusive-monitor.jsonl').open('a') as stream:stream.write(json.dumps(sample)+'\n');stream.flush()
            state['observations']+=1
            require(float(last_thermal['temperature.gpu'])<90,'Thermal stop >=90C; triggering record retained')
            storage.check();time.sleep(min(interval,remaining()))
        state['runner_exit_code']=child.wait()
        require(child.returncode==0,'Original runner failed; no replay')
        require(state['context_granted'] and state['observations']>0,'No complete original exclusivity monitoring')
    except BaseException as error:
        failure=error;state.update(error_type=type(error).__name__,error=str(error))
    finally:
        try:
            stop_original(child,handle)
            if handle is not None:
                require(observe_original_process(handle)['original_live'] is False,'Original runner closure unknown')
            snapshot=None;released=False
            try:snapshot=observe_gpu(uuid);verify(snapshot,uuid);released=True
            except Exception as error:state['release_error']=str(error)
            pending={k:launch[k] for k in IDENTITY}
            pending.update(final_snapshot=snapshot,GPU_released=released,original_process_exited=child is None or child.poll() is not None,
                cost_settled=False,billing_clock_owner='HOST_GUARDIAN',complete_endpoint_accepted=False)
            storage.persist('accounting',stage/'release-pending-central.json',pending,atomic_json)
            state.update(status='CARA_ENDPOINT_SUPERVISOR_TERMINAL_R1',ended_unix=time.time(),
                original_runner_ended=child is None or child.poll() is not None)
            save()
        finally:
            lease.close();signal.signal(signal.SIGTERM,previous_handler)
    if failure is not None:raise failure
    return state
