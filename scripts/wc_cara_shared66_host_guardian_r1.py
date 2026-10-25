#!/usr/bin/env python3
"""Authenticated host-side mode owner. Password is stdin-only, never stored."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts')]
    from wcomr.policy_price_mode_guard_r1 import ModeGuard
    from wcomr.policy_generator_r1.production_exclusive import observe
    from wcomr.policy_generator_r1.shared66_card import read,sha,validate
    from wcomr.gpu_budget_pool_v2 import DeviceLease,atomic_json,process_identity
    c,reg,*_=validate(a.project,a.stage)
    from wcomr.history104_storage_r2 import storage_for
    storage=storage_for(a.stage) if c.get('storage_contract_required') else None
    if storage:storage.check()
    auth=read(a.stage/'pg-GPU-authorization.json');uuid=auth['gpu_uuid']
    # Do not put this input in any receipt, command argument, environment, or log.
    incoming=json.load(sys.stdin);password=incoming.pop('sudo_password');assert not incoming
    def change(selected,mode):
        if selected!=uuid or mode not in ('EXCLUSIVE_PROCESS','DEFAULT'):raise ValueError('Wrong selected mode change')
        r=subprocess.run(['sudo','-S','-p','','/usr/bin/nvidia-smi','-i',uuid,'-c',mode],
            input=password+'\n',capture_output=True,text=True,timeout=25)
        if r.returncode:raise RuntimeError('Authenticated selected-UUID mode command failed, exit '+str(r.returncode))
    guard=ModeGuard(uuid,observe,change,time.time)
    lock_path=a.project/'.sync/gpu-locks'/(uuid+'.mode-owner.lock');lock_path.parent.mkdir(parents=True,exist_ok=True)
    child=None;state=dict(status='SHARED66_MODE_OWNER_ADMITTING',identity=process_identity(os.getpid()),
        gpu_uuid=uuid,source_revision=reg['source_revision'],started_unix=time.time())
    def save():
        if storage:storage.persist('guardian',a.stage/'pg-host-guardian.json',state,atomic_json)
        else:atomic_json(a.stage/'pg-host-guardian.json',state)
    with lock_path.open('a+') as mode_lock:
        fcntl.flock(mode_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            # The project lease guards the mode change; the container then
            # acquires its own inherited-FD lease before reserving or using GPU.
            with DeviceLease(a.project,uuid):state['mode_admission']=guard.acquire();save()
            bank=a.project/'.sync/wc-bank24-fourcard-full-execution-r3-20261022'
            sys.path.insert(0,str(bank))
            from four_card_bank24_execution_tools_r1 import process_environment
            from four_card_policy_assets_port_r1 import container_command
            command=container_command(a.project,a.stage,'supervise',sha(a.stage/'registration.json'),
                process_environment(a.project,a.stage/'GPU-caches'),os.getuid(),os.getgid(),uuid)
            if storage:
                # Exact per-run writable mounts; the control journal is on another disk.
                at=command.index('--entrypoint')
                command[at:at]=['-v',str(storage.output)+':'+str(storage.output)+':rw','-v',str(storage.journal.path)+':'+str(storage.journal.path)+':rw','-v',storage.config['image_path']+':'+storage.config['image_path']+':ro']
            old=str(a.stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py')
            command[command.index(old)]=str(a.stage/'scripts/wc_cara_shared66_worker_r1.py')
            i=command.index('--authorization');assert i==len(command)-2;command=command[:i]
            with (a.stage/'pg-container.log').open('x') as log:
                child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                state.update(status='SHARED66_ORIGINAL_CONTAINER_RUNNING',container_cli_identity=process_identity(child.pid),
                    container=a.stage.name+'-gpu');save()
                def interrupted(signum,frame):raise KeyboardInterrupt('Own price mode guardian interrupted')
                signal.signal(signal.SIGTERM,interrupted)
                # The in-container supervisor owns budgeting and active-mode monitoring.
                state['container_exit_code']=child.wait()
        except BaseException as e:
            state.update(error_type=type(e).__name__,error=str(e));raise
        finally:
            if child is not None and child.poll() is None:
                # Address only our own manifest-bound named container, never a GPU reset.
                inspect=subprocess.run(['docker','inspect',a.stage.name+'-gpu'],capture_output=True,text=True)
                if inspect.returncode==0:
                    actual=json.loads(inspect.stdout)[0]
                    if actual['Config']['Labels'].get('wcomr.manifest')==sha(a.stage/'registration.json'):
                        subprocess.run(['docker','stop','--time','30',a.stage.name+'-gpu'],capture_output=True,timeout=45)
                child.wait(timeout=15)
            state['mode_restoration']=guard.restore();password=None
            state.update(status='SHARED66_HOST_GUARDIAN_TERMINAL',ended_unix=time.time());save()

if __name__=='__main__':main()
