"""Original mode-owner lifecycle bound to B36 and exact writable paths."""
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

def container_arguments(*args, **kwargs):
    command = original_container_arguments(*args, **kwargs)
    stage = args[1]
    command[command.index(str(stage/'scripts/cara_fast_worker_r2.py'))] = str(stage/'scripts/cara_fast_b36_worker_r1.py')
    return command


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.cara_fast_b36_execution_r1 import validate,read,PROFILE
    from wcomr.gpu_budget_pool_v2 import DeviceLease,atomic_json,process_identity,sha
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.policy_price_mode_guard_r1 import ModeGuard
    from wcomr.wc73_exclusive_r1 import observe
    card,registration,authority,bound=validate(args.project,args.stage)
    storage=storage_for(args.stage)
    storage.check()
    uuid=authority['gpu_uuid']
    profile=read(args.stage/PROFILE)
    cpuset=profile['hosts'][authority['host']]['cpuset_cpus']
    assert set(map(int,cpuset.split(',')))<=os.sched_getaffinity(0)
    # The credential is carried only on stdin and never written or logged.
    incoming=json.load(sys.stdin)
    password=incoming.pop('sudo_password')
    assert not incoming

    def change(selected,mode):
        if selected!=uuid or mode not in ('EXCLUSIVE_PROCESS','DEFAULT'):
            raise ValueError('Wrong selected mode change')
        result=subprocess.run(['sudo','-S','-p','','/usr/bin/nvidia-smi','-i',uuid,'-c',mode],
            input=password+'\n',capture_output=True,text=True,timeout=25)
        if result.returncode:
            raise RuntimeError('Selected-UUID mode command failed, exit '+str(result.returncode))

    guard=ModeGuard(uuid,observe,change,time.time)
    lock_path=args.project/'.sync/gpu-locks'/(uuid+'.mode-owner.lock')
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    child=None
    state=dict(status='FAST_B36_MODE_OWNER_ADMITTING',identity=process_identity(os.getpid()),
        run_id=authority['run_id'],launch_id=authority['launch_id'],gpu_uuid=uuid,
        source_revision=registration['source_revision'],started_unix=time.time())

    def save():
        storage.persist('guardian',args.stage/'pg-host-guardian.json',state,atomic_json)

    with lock_path.open('a+') as mode_lock:
        fcntl.flock(mode_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            with DeviceLease(args.project,uuid):
                state['mode_admission']=guard.acquire()
                save()
            command=container_arguments(args.project,args.stage,storage,sha(args.stage/'registration.json'),
                                         cpuset,os.getuid(),os.getgid(),uuid,profile['GPU_container']['memory_GiB'])
            atomic_json(args.stage/'GPU-command.json',command)
            with (args.stage/'pg-container.log').open('x') as log:
                child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,
                    stderr=subprocess.STDOUT,start_new_session=True)
                state.update(status='FAST_B36_ORIGINAL_CONTAINER_RUNNING',
                    container_cli_identity=process_identity(child.pid),container=args.stage.name+'-gpu')
                save()
                def interrupted(signum,frame):
                    raise KeyboardInterrupt('Own B36 mode guardian interrupted')
                signal.signal(signal.SIGTERM,interrupted)
                state['container_exit_code']=child.wait()
        except BaseException as error:
            state.update(error_type=type(error).__name__,error=str(error))
            raise
        finally:
            if child is not None and child.poll() is None:
                inspected=subprocess.run(['docker','inspect',args.stage.name+'-gpu'],capture_output=True,text=True)
                if inspected.returncode==0:
                    actual=json.loads(inspected.stdout)[0]
                    if actual['Config']['Labels'].get('wcomr.manifest')==sha(args.stage/'registration.json'):
                        subprocess.run(['docker','stop','--time','30',args.stage.name+'-gpu'],capture_output=True,timeout=45)
                child.wait(timeout=15)
            state['mode_restoration']=guard.restore()
            password=None
            state.update(status='FAST_B36_HOST_GUARDIAN_TERMINAL',ended_unix=time.time())
            save()


if __name__=='__main__':
    main()
