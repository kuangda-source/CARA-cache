"""B36's single measured allocation bill, including pre-runner admission failures."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from cara_fast_host_guardian_r2 import container_arguments as original_container_arguments
from cara_fast_worker_r2 import stop


def container_arguments(project,stage,storage,registration_sha,cpuset,uid,gid,uuid,memory_GiB=40):
    command=original_container_arguments(project,stage,storage,registration_sha,cpuset,uid,gid,uuid,memory_GiB)
    command[command.index(str(stage/'scripts/cara_fast_worker_r2.py'))]=str(stage/'scripts/cara_fast_b36_worker_r1.py')
    return command


def set_selected_mode(uuid,mode,password):
    if mode not in ('EXCLUSIVE_PROCESS','DEFAULT'):
        raise ValueError('Wrong selected mode change')
    result=subprocess.run(['sudo','-S','-p','','/usr/bin/nvidia-smi','-i',uuid,'-c',mode],
        input=password+'\n',capture_output=True,text=True,timeout=25)
    if result.returncode:
        raise RuntimeError('Selected-UUID mode command failed, exit '+str(result.returncode))


def inspect_original(stage,registration_sha,uuid):
    """Only a definite no-such-container response proves that Docker never created it."""
    name=stage.name+'-gpu'
    inspected=subprocess.run(['docker','inspect','--type','container',name],capture_output=True,text=True,timeout=20)
    if inspected.returncode:
        missing=('Error: No such object: '+name,'Error: No such container: '+name)
        if inspected.returncode==1 and inspected.stderr.strip() in missing:
            return None
        raise RuntimeError('Original container observation unknown; retain original envelope')
    actual=json.loads(inspected.stdout)[0]
    if (actual['Config']['Labels'].get('wcomr.manifest')!=registration_sha
            or actual['HostConfig']['DeviceRequests'][0]['DeviceIDs']!=[uuid]
            or len(actual['HostConfig']['DeviceRequests'])!=1):
        raise ValueError('Container identity differs; do not stop or replace it')
    return actual


def finish_original(stage,registration_sha,uuid,child,dispatch_state):
    from wcomr.cara_fast_b36_terminal_r1 import container_record
    if dispatch_state in ('NOT_ATTEMPTED','SPAWN_FAILED_NO_EXEC'):
        return dict(kind='NO_CONTAINER_DISPATCH',complete=True,dispatch_state=dispatch_state)
    actual=inspect_original(stage,registration_sha,uuid)
    if actual is None:
        if child is not None and child.poll() is not None:
            return dict(kind='ORIGINAL_CONTAINER_NEVER_CREATED',complete=True)
        raise ValueError('Original Docker CLI still live or unknown')
    if actual['State']['Running']:
        subprocess.run(['docker','stop','--time','30',stage.name+'-gpu'],capture_output=True,check=True,timeout=45)
        actual=inspect_original(stage,registration_sha,uuid)
    if (actual is None or actual['State']['Running'] or actual['State']['Pid']!=0
            or actual['State']['Status'] not in ('created','exited')):
        raise ValueError('Original container has not reached a verified terminal state')
    if child is not None:
        child.wait(timeout=15)
    return dict(kind='BOUND_CONTAINER_TERMINAL',complete=True,container_id=actual['Id'],
                container=container_record(actual),manifest_sha256=registration_sha)


def run(args,password):
    from wcomr.cara_fast_b36_execution_r1 import validate,read,PROFILE,RUN
    from wcomr.gpu_budget_pool_v2 import DeviceLease,atomic_json,process_identity,sha
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.policy_price_mode_guard_r1 import ModeGuard
    from wcomr.wc73_exclusive_r1 import observe
    card,registration,authority,bound=validate(args.project,args.stage)
    storage=storage_for(args.stage)
    profile=read(args.stage/PROFILE)
    cpuset=profile['hosts'][authority['host']]['cpuset_cpus']
    assert set(map(int,cpuset.split(',')))<=os.sched_getaffinity(0)
    assert not (args.stage/'pg-host-guardian.json').exists(),'Original guardian exists; recover it'
    assert not (args.stage/'B-billing.json').exists(),'Original bill exists; never overwrite it'
    uuid=authority['gpu_uuid']
    guard=ModeGuard(uuid,observe,lambda selected,mode:set_selected_mode(selected,mode,password),time.time)
    start=time.monotonic()
    state=dict(status='FAST_B36_MODE_OWNER_ADMITTING',identity=process_identity(os.getpid()),
        run_id=RUN,phase='B',host=authority['host'],scope_sha256=card['scope_sha256'],
        launch_id=authority['launch_id'],gpu_uuid=uuid,source_revision=registration['source_revision'],
        started_unix=time.time(),started_monotonic=start,container_dispatch_state='NOT_ATTEMPTED',
        mode_owner_fenced=False)
    child=None
    mode_lock=None

    def save():
        storage.persist('guardian',args.stage/'pg-host-guardian.json',state,atomic_json)

    try:
        save()
        storage.check()
        if password is None:
            raise ValueError('Original launch credential delivery failed; no mode change or container dispatch')
        mode_lock=(args.project/'.sync/gpu-locks'/(uuid+'.mode-owner.lock')).open('a+')
        fcntl.flock(mode_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state['mode_owner_fenced']=True
        with DeviceLease(args.project,uuid):
            state['mode_admission']=guard.acquire()
            save()
        command=container_arguments(args.project,args.stage,storage,sha(args.stage/'registration.json'),
            cpuset,os.getuid(),os.getgid(),uuid,profile['GPU_container']['memory_GiB'])
        atomic_json(args.stage/'GPU-command.json',command)
        remaining=authority['whole_GPUh']*3600-180-(time.monotonic()-start)
        if remaining<=0:
            raise TimeoutError('Original guardian reached its own allocation release margin')
        with (args.stage/'pg-container.log').open('x') as log:
            state['container_dispatch_state']='ATTEMPTED'
            save()
            try:
                child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,
                    stderr=subprocess.STDOUT,start_new_session=True)
            except OSError:
                state['container_dispatch_state']='SPAWN_FAILED_NO_EXEC'
                raise
            state.update(status='FAST_B36_ORIGINAL_CONTAINER_RUNNING',container_dispatch_state='STARTED',
                container_cli_identity=process_identity(child.pid),container=args.stage.name+'-gpu')
            save()
            def interrupted(signum,frame):
                raise KeyboardInterrupt('Own B36 mode guardian interrupted')
            signal.signal(signal.SIGTERM,interrupted)
            state['container_exit_code']=child.wait(timeout=remaining)
    except BaseException as error:
        state.update(error_type=type(error).__name__,error=str(error))
        raise
    finally:
        try:
            try:
                state['container_terminal_witness']=finish_original(args.stage,sha(args.stage/'registration.json'),
                    uuid,child,state['container_dispatch_state'])
            except Exception as error:
                state['container_terminal_witness']=dict(complete=False,error_type=type(error).__name__,error=str(error))
            finally:
                stop(child)
            state['mode_restoration']=guard.restore()
            end=time.monotonic()
            billing=dict(status='FAST_B36_ORIGINAL_WALL_BILL',run_id=RUN,phase='B',host=authority['host'],
                launch_id=authority['launch_id'],gpu_uuid=uuid,source_revision=registration['source_revision'],
                scope_sha256=card['scope_sha256'],wall_seconds=end-start,actual_GPUh=(end-start)/3600,
                billed_limit_GPUh=authority['whole_GPUh'],ended_unix=time.time(),
                started_monotonic=start,ended_monotonic=end,billing_clock_owner='HOST_GUARDIAN',
                wall_interval_complete=state['container_terminal_witness']['complete'],central_settlement_pending=True)
            storage.persist('billing',args.stage/'B-billing.json',billing,atomic_json)
            state.update(status='FAST_B36_HOST_GUARDIAN_TERMINAL',ended_unix=billing['ended_unix'],
                         ended_monotonic=end,billing_sha256=sha(args.stage/'B-billing.json'),
                         GPU_mode_change_attempted=guard.enable_attempted)
            save()
        finally:
            password=None
            if mode_lock is not None:mode_lock.close()
    if not state['container_terminal_witness']['complete']:
        raise RuntimeError('Original container closure unknown; retain original bill/envelope and recover')


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.cara_fast_b36_dispatch_r2 import publish_launch
    publish_launch(args.project,args.stage)
    try:
        incoming=json.load(sys.stdin)
        password=incoming.pop('sudo_password')
        assert not incoming
    except (ValueError,KeyError):
        password=None
    run(args,password)


if __name__=='__main__':
    main()
