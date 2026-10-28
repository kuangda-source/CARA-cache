"""S/Q host allocation clock and bounded original-container closure.

The caller must first validate its own source, authority, CPU proof and central
envelope. This module neither reserves nor settles a ledger. GPU operations
are isolated in SystemOperations so Linux CPU controls can substitute them
while retaining actual subprocesses, locks and monotonic timing.
"""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from .gpu_budget_pool_v2 import DeviceLease, atomic_json, process_identity, sha


def require(value,message):
    if not value:raise ValueError(message)


def container_record(actual):
    config=actual['HostConfig']
    return dict(state=actual['State'],image=actual['Image'],
        manifest_sha256=actual['Config']['Labels'].get('wcomr.manifest'),
        device_requests=config['DeviceRequests'],readonly_root=config['ReadonlyRootfs'],
        pid_mode=config['PidMode'],network=config['NetworkMode'],cpus=config['NanoCpus']/1e9,
        memory_GiB=config['Memory']/2**30)


def bound_container(actual,registration_sha,uuid):
    require(actual['Config']['Labels'].get('wcomr.manifest')==registration_sha
            and len(actual['HostConfig']['DeviceRequests'])==1
            and actual['HostConfig']['DeviceRequests'][0]['DeviceIDs']==[uuid],
            'Container identity differs; never stop or replace it')
    return actual


class SystemOperations:
    def mode_guard(self,uuid,password,clock):
        from .policy_price_mode_guard_r1 import ModeGuard
        from .wc73_exclusive_r1 import observe
        def change(selected,mode):
            require(selected==uuid and mode in ('EXCLUSIVE_PROCESS','DEFAULT'),'Selected mode identity differs')
            result=subprocess.run(['sudo','-S','-p','','/usr/bin/nvidia-smi','-i',uuid,'-c',mode],
                input=password+'\n',capture_output=True,text=True,timeout=25)
            require(result.returncode==0,'Selected mode command failed, exit '+str(result.returncode))
        return ModeGuard(uuid,observe,change,clock.time)

    def inspect_container(self,stage,registration_sha,uuid):
        name=stage.name+'-gpu'
        inspected=subprocess.run(['docker','inspect','--type','container',name],capture_output=True,text=True,timeout=20)
        if inspected.returncode:
            missing=('Error: No such object: '+name,'Error: No such container: '+name)
            if inspected.returncode==1 and inspected.stderr.strip() in missing:return None
            raise RuntimeError('Original container observation is unknown; recover only')
        actual=json.loads(inspected.stdout)[0]
        return bound_container(actual,registration_sha,uuid)

    def stop_container(self,stage):
        subprocess.run(['docker','stop','--time','30',stage.name+'-gpu'],capture_output=True,check=True,timeout=45)

    def spawn(self,command,log):
        return subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)

    def wait(self,child,remaining):return child.wait(timeout=remaining)

    def stop_own_cli(self,child):
        if child is None or child.poll() is not None:return
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)


def finish_original(ops,stage,registration_sha,uuid,child,dispatch_state):
    if dispatch_state in ('NOT_ATTEMPTED','SPAWN_FAILED_NO_EXEC'):
        return dict(kind='NO_CONTAINER_DISPATCH',complete=True,dispatch_state=dispatch_state)
    actual=ops.inspect_container(stage,registration_sha,uuid)
    if actual is None:
        require(child is not None and child.poll() is not None,'Original CLI still live or unknown')
        return dict(kind='ORIGINAL_CONTAINER_NEVER_CREATED',complete=True)
    bound_container(actual,registration_sha,uuid)
    if actual['State']['Running']:
        ops.stop_container(stage)
        actual=ops.inspect_container(stage,registration_sha,uuid)
        if actual is not None:bound_container(actual,registration_sha,uuid)
    require(actual is not None and not actual['State']['Running'] and actual['State']['Pid']==0
            and actual['State']['Status'] in ('created','exited'),'Original container terminal is not proven')
    if child is not None:child.wait(timeout=15)
    return dict(kind='BOUND_CONTAINER_TERMINAL',complete=True,container_id=actual['Id'],
                container=container_record(actual),manifest_sha256=registration_sha)


def run_allocation(project,stage,authority,registration,storage,profile,prefix,command_builder,password,
                   *,ops=None,clock=time):
    """Bill admission through verified closure/restoration once, including failures."""
    project,stage=Path(project),Path(stage);ops=ops or SystemOperations()
    require(prefix in ('Q1','S') and authority['direct_user_authorization'] is True,
            'Separately validated S/Q authority required')
    uuid=authority['gpu_uuid'];output=storage.output
    state_path=stage/'pg-host-guardian.json';bill_path=output/(prefix+'-billing.json')
    require(not state_path.exists() and not bill_path.exists(),'Original allocation exists; recover only')
    start=clock.monotonic();identity=process_identity(os.getpid())
    common={key:authority[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256')}
    require(registration['source_revision']==common['source_revision'],'Validated source identity differs')
    state=dict(common,status='SQ_'+prefix+'_MODE_OWNER_ADMITTING',identity=identity,
        started_unix=clock.time(),started_monotonic=start,container_dispatch_state='NOT_ATTEMPTED',
        mode_owner_fenced=False,billing_clock_owner='HOST_GUARDIAN')
    child=mode_lock=guard=None
    previous_signal=signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):raise KeyboardInterrupt('Own S/Q allocation guardian interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    def save():storage.persist('guardian',state_path,state,atomic_json)
    try:
        guard=ops.mode_guard(uuid,password,clock)
        save();storage.check()
        require(password is not None,'Credential delivery failed before mode/container dispatch')
        lock=project/'.sync/gpu-locks'/(uuid+'.mode-owner.lock');lock.parent.mkdir(parents=True,exist_ok=True)
        mode_lock=lock.open('a+')
        fcntl.flock(mode_lock,fcntl.LOCK_EX|fcntl.LOCK_NB);state['mode_owner_fenced']=True
        with DeviceLease(project,uuid):state['mode_admission']=guard.acquire();save()
        command=command_builder();atomic_json(stage/'GPU-command.json',command)
        margin=profile.get('guardian_release_margin_seconds',180)
        require(margin>=180,'Whole host allocation needs the complete180-second release margin')
        remaining=authority['whole_GPUh']*3600-margin-(clock.monotonic()-start)
        require(remaining>0,'Allocation deadline reached during admission; no container dispatch')
        with (stage/'pg-container.log').open('x') as log:
            state['container_dispatch_state']='ATTEMPTED';save()
            try:child=ops.spawn(command,log)
            except OSError:state['container_dispatch_state']='SPAWN_FAILED_NO_EXEC';raise
            state.update(status='SQ_'+prefix+'_ORIGINAL_CONTAINER_RUNNING',container_dispatch_state='STARTED',
                container_cli_identity=process_identity(child.pid),container=stage.name+'-gpu')
            save()
            state['container_exit_code']=ops.wait(child,remaining)
    except BaseException as error:
        state.update(error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try:
            try:
                state['container_terminal_witness']=finish_original(ops,stage,sha(stage/'registration.json'),
                    uuid,child,state['container_dispatch_state'])
            except Exception as error:
                state['container_terminal_witness']=dict(complete=False,error_type=type(error).__name__,error=str(error))
            finally:ops.stop_own_cli(child)
            try:state['mode_restoration']=(guard.restore() if guard else dict(restored=True,changed=False,mode_guard_never_created=True))
            except Exception as error:
                state['mode_restoration']=dict(restored=False,error_type=type(error).__name__,error=str(error))
            end=clock.monotonic()
            complete=state['container_terminal_witness']['complete'] and state['mode_restoration']['restored']
            billing=dict(common,status='SQ_'+prefix+'_ORIGINAL_WALL_BILL',started_monotonic=start,
                ended_monotonic=end,wall_seconds=end-start,actual_GPUh=(end-start)/3600,
                billed_limit_GPUh=authority['whole_GPUh'],started_unix=state['started_unix'],ended_unix=clock.time(),
                billing_clock_owner='HOST_GUARDIAN',wall_interval_complete=complete,
                central_settlement_pending=True,supervisor_bill_is_diagnostic_only=True)
            storage.persist('billing',bill_path,billing,atomic_json)
            release=dict(common,billing_sha256=sha(bill_path),allocation_release_accepted=complete,
                container_terminal_witness=state['container_terminal_witness'],
                mode_restoration=state['mode_restoration'],cost_settled=False,authorizes_retry=False)
            storage.persist('allocation_release',output/(prefix+'-allocation-release.json'),release,atomic_json)
            state.update(status='SQ_'+prefix+('_HOST_GUARDIAN_TERMINAL' if complete else '_ALLOCATION_RECOVERY_PENDING'),
                ended_unix=billing['ended_unix'],ended_monotonic=end,billing_sha256=sha(bill_path))
            save()
        finally:
            password=None
            if mode_lock is not None:mode_lock.close()
            signal.signal(signal.SIGTERM,previous_signal)
    require(state['container_terminal_witness']['complete'] and state['mode_restoration']['restored'],
            'Original allocation closure unknown; retain bill/envelope and recover')
    return state
