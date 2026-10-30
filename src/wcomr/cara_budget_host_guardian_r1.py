"""Original admitted allocation: mode ownership, child closure and one wall bill.

No standalone once-dispatch/approval entry. Full admission and immutable launch
publication must precede this host component; it never reserves or settles.
"""
import fcntl
import os
from pathlib import Path
import signal
import select
import re
import subprocess
import sys
import time

from .cara_budget_guardian_journal_r1 import GuardianJournal
from .cara_budget_lifecycle_r1 import IDENTITY
from .cara_budget_lifecycle_capture_r1 import inspect_container
from .cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from .cara_budget_search_journal_r1 import create_record,read_record
from .cara_budget_supervisor_r1 import stop_original,BOOTSTRAP
from .gpu_budget_pool_v2 import DeviceLease,sha
from .policy_price_mode_guard_r1 import ModeGuard
from .policy_price_terminal_r1 import require
from .wc73_exclusive_r1 import observe

SOURCE='src/wcomr/cara_budget_host_guardian_r1.py'


def set_mode(uuid,mode,password):
    require(mode in ('EXCLUSIVE_PROCESS','DEFAULT'),'Selected mode only')
    result=subprocess.run(['sudo','-S','-p','','/usr/bin/nvidia-smi','-i',uuid,'-c',mode],
        input=password+'\n',capture_output=True,text=True,timeout=25)
    require(result.returncode==0,'Selected mode command failed, exit '+str(result.returncode))


def stop_container(name):
    subprocess.run(['docker','stop','--time','30',name],capture_output=True,check=True,timeout=45)


def stop_bound_runner(handle):
    """Stop only the recorded runner via pidfd when Docker observation fails."""
    if handle is None:return
    if observe_original_process(handle)['original_live'] is False:return
    descriptor=os.pidfd_open(handle['pid'])
    try:
        require(observe_original_process(handle)['original_live'] is True,
                'Original runner identity unknown; no fallback signal')
        signal.pidfd_send_signal(descriptor,signal.SIGTERM)
        poll=select.poll();poll.register(descriptor,select.POLLIN)
        if not poll.poll(10000):
            signal.pidfd_send_signal(descriptor,signal.SIGKILL)
            require(bool(poll.poll(10000)),'Original runner did not exit after bounded fallback stop')
    finally:os.close(descriptor)


def allocate(project,stage,storage,password,*,cpu_validation=False,observe_gpu=observe,
             change_mode=set_mode,inspect=inspect_container,stop=stop_container,interval=2.,release_margin=600.):
    project=Path(project);stage=Path(stage)
    launch=read_record(stage/'GPU-launch.json');registration=read_record(stage/'registration.json')
    authority=read_record(stage/'GPU-authorization.json');envelope=read_record(stage/'central-reservation.json')
    require(launch['CPU_fixture_only'] is cpu_validation and authority['CPU_fixture_only'] is cpu_validation,
            'CPU fixtures cannot enter a production allocation')
    require(stage.parent==project/'.sync' and launch['stage']==str(stage)
            and launch['container']==stage.name+'-gpu'
            and launch['guardian_identity']==bind_original_process(os.getpid())
            and sha(stage/'registration.json')==launch['registration_sha256']
            and sha(stage/'GPU-authorization.json')==launch['authorization_sha256']
            and sha(stage/'central-reservation.json')==launch['central_reservation_sha256']
            and registration['payload_sha256'][SOURCE]==sha(__file__)
            and registration['payload_sha256'][BOOTSTRAP]==sha(stage/BOOTSTRAP),
            'Original admitted guardian/source/launch binding required')
    require(authority['execution_authorized'] is True and authority['authorizes_replay'] is False
            and all(authority[k]==launch[k] for k in IDENTITY)
            and envelope['central_ledger_host']=='four_card'
            and envelope['job']['status']=='RESERVED_OR_RUNNING'
            and envelope['job']['job_id']==launch['run_id']
            and all(envelope['job'][k]==launch[k] for k in IDENTITY),
            'Original whole authorization and central envelope required')
    require(0<interval<=2 and 0<release_margin<launch['billed_limit_GPUh']*3600,'Bounded guardian release margin required')
    if not cpu_validation:
        require(interval==2. and release_margin==600.,'Frozen production guardian bounds required')
        command=launch['commands']['container_cli']
        require(command[:2]==['docker','run'] and '--cidfile' in command
                and command[command.index('--cidfile')+1]==str(stage/'container.cid'),
                'Original Docker creation ID must be retained by the frozen command')
    journal=GuardianJournal(stage,launch,registration,storage,cpu_validation=cpu_validation)
    uuid=launch['gpu_uuid'];mode_lock=None;lease=DeviceLease(project,uuid)
    child=None;cli_handle=None;container_id=None;failure=None
    def change(selected,mode):
        if mode=='EXCLUSIVE_PROCESS':return journal.operation('mode_change_attempted',lambda:change_mode(selected,mode,password))
        return change_mode(selected,mode,password)
    guard=ModeGuard(uuid,observe_gpu,change,time.time)
    previous_handler=signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):raise KeyboardInterrupt('Original calibration guardian interrupted')
    def inspect_bound():
        nonlocal container_id
        actual=inspect(launch['container'])
        if actual is not None:
            cid_path=stage/'container.cid'
            require(cid_path.is_file() and not cid_path.is_symlink(),'Original Docker creation ID unavailable')
            original_cid=cid_path.read_text().strip()
            require(re.fullmatch('[0-9a-f]{64}',original_cid) and actual['id']==original_cid,
                    'Container differs from the original Docker creation ID; do not stop it')
            require(actual['name']==launch['container'] and actual['manifest_sha256']==launch['registration_sha256']
                    and actual['image']==registration['container_image'] and actual['device_ids']==[uuid]
                    and (container_id is None or actual['id']==container_id),'Original container identity differs; do not stop it')
            container_id=actual['id']
        return actual
    def collect_workers():
        for role in ('supervisor','runner'):
            path=stage/(role+'-start.json')
            if path.exists() and journal.state['original_handles'][role] is None:
                row=read_record(path)
                require(row['launch_id']==launch['launch_id'],'Worker belongs to another original launch')
                journal.bind_child(role,row['identity'])
        # The supervisor can stop its original Popen child before the bootstrap
        # writes its own start file. Preserve the already recorded parent handle;
        # an absent self-witness must not erase this failed physical child.
        parent_path=stage/'supervisor.json'
        if parent_path.exists() and not (stage/'runner-start.json').exists():
            parent=read_record(parent_path)
            require(all(parent[k]==launch[k] for k in IDENTITY)
                    and parent['identity']==journal.state['original_handles']['supervisor'],
                    'Original supervisor parent record differs')
            handle=parent.get('runner_identity')
            if handle is not None:
                if journal.state['original_handles']['runner'] is None:journal.bind_child('runner',handle)
                require(handle==journal.state['original_handles']['runner'],'Original parent runner differs')
                if (parent['status']=='BUDGET_CALIBRATION_SUPERVISOR_TERMINAL'
                        and parent['runner_dispatch_state']=='STARTED' and parent['original_runner_ended'] is True
                        and observe_original_process(handle)['original_live'] is False
                        and not (stage/'runner-start.json').exists()):
                    create_record(stage/'runner-start.json',dict(identity=handle,launch_id=launch['launch_id'],
                        witness_source='ORIGINAL_SUPERVISOR_POPEN_AFTER_CONFIRMED_EXIT',
                        parent_terminal_sha256=sha(parent_path),bootstrap_self_witness=False))
    def acquire_mode_lock():
        nonlocal mode_lock
        descriptor=os.open(project/'.sync/gpu-locks'/(uuid+'.mode-owner.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        mode_lock=os.fdopen(descriptor,'r+')
        fcntl.flock(mode_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def spawn():
        nonlocal child
        with (stage/'container-cli.log').open('x') as log:
            child=subprocess.Popen([sys.executable,str(stage/BOOTSTRAP),'--stage',str(stage),'--role','container_cli'],
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void' if cpu_validation else os.environ.get('NVIDIA_VISIBLE_DEVICES','all')))
        return child
    try:
        signal.signal(signal.SIGTERM,interrupted)
        require(password is not None,'Original launch credential delivery failed')
        storage.check();require(inspect_bound() is None,'Existing original container: recover, never dispatch again')
        journal.operation('mode_lock_attempted',acquire_mode_lock)
        journal.operation('device_lease_attempted',lease.acquire)
        try:journal.state['mode_admission']=guard.acquire();journal.save()
        finally:lease.close()
        journal.remaining_seconds(release_margin)
        journal.operation('container_dispatch_attempted',spawn)
        cli_handle=bind_original_process(child.pid);journal.bind_child('container_cli',cli_handle)
        begin=time.monotonic()
        while not (stage/'container_cli-start.json').exists():
            journal.remaining_seconds(release_margin)
            require(child.poll() is None,'Original CLI bootstrap exited before its witness')
            if time.monotonic()-begin>=30:raise TimeoutError('Original CLI bootstrap start unknown')
            time.sleep(min(interval,.02))
        require(read_record(stage/'container_cli-start.json')['identity']==cli_handle,'Original CLI bootstrap identity differs')
        create_record(stage/'container_cli-dispatch-grant.json',dict(identity=cli_handle,launch_sha256=sha(stage/'GPU-launch.json')))
        while child.poll() is None:
            journal.remaining_seconds(release_margin);collect_workers();inspect_bound();storage.check()
            time.sleep(min(interval,journal.remaining_seconds(release_margin)))
        journal.state['container_exit_code']=child.wait()
        require(child.returncode==0,'Original container CLI failed; no replay')
    except BaseException as error:
        failure=error
        if child is None and journal.state['allocation_attempts']['container_dispatch_attempted']:
            journal.state['container_dispatch_state']='SPAWN_FAILED_NO_EXEC'
    finally:
        witness=dict(complete=False,reason='Original container closure not observed')
        try:
            try:
                collect_workers()
                if not journal.state['allocation_attempts']['container_dispatch_attempted'] or child is None:
                    witness=dict(kind='NO_CONTAINER_DISPATCH',complete=True)
                else:
                    actual=inspect_bound()
                    if actual is not None and actual['state']['Running']:
                        stop(actual['id']);actual=inspect_bound()
                    if actual is None:
                        stop_original(child,cli_handle)
                        require(child.poll() is not None,'Original CLI still live')
                        witness=dict(kind='ORIGINAL_CONTAINER_NEVER_CREATED',complete=True)
                    else:
                        require(actual['state']['Status'] in ('created','exited') and actual['state']['Running'] is False
                                and actual['state']['Pid']==0,'Original container closure unknown')
                        child.wait(timeout=15)
                        witness=dict(kind='BOUND_CONTAINER_TERMINAL',complete=True,container_id=actual['id'],container=actual)
                collect_workers()
                for role,handle in journal.state['original_handles'].items():
                    if role!='guardian' and handle is not None:
                        require(observe_original_process(handle)['original_live'] is False,'Original child closure unknown')
            except Exception as error:
                witness=dict(complete=False,error_type=type(error).__name__,error=str(error))
                if failure is None:failure=error
                try:
                    stop_bound_runner(journal.state['original_handles']['runner'])
                    if child is not None:
                        try:child.wait(timeout=10)
                        except subprocess.TimeoutExpired:stop_original(child,cli_handle)
                    witness['original_runner_fallback_stop_attempted']=True
                except Exception as cleanup_error:
                    witness['cleanup_error_type']=type(cleanup_error).__name__
                    witness['cleanup_error']=str(cleanup_error)
            restoration=guard.restore()
            # The original monotonic interval includes admission, stop and restoration.
            journal.finish(container_terminal_witness=witness,mode_restoration=restoration,
                container_exit_code=child.poll() if child else None,error=failure)
        finally:
            lease.close()
            if mode_lock is not None:mode_lock.close()
            signal.signal(signal.SIGTERM,previous_handler);password=None
    if failure is not None:raise failure
    require(witness['complete'] is True,'Original closure unknown; retain original envelope')
    return journal.state
