"""CPU fixture process roles. No real GPU, Docker or mode commands."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import hashlib

from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_budget_search_journal_r1 import read_record,create_record
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr.history104_storage_r2 import FixedJournal


def storage_for(stage):
    class Storage:
        journal=FixedJournal(stage/'CPU-control.journal')
        def check(self):return {}
        def persist(self,key,path,value,writer):self.journal.write(key,value);writer(path,value)
    return Storage()


def observe(stage,uuid):
    launch=read_record(stage/'GPU-launch.json');scenario=read_record(stage/'CPU-scenario.json')['scenario'];apps=[]
    runner=stage/'runner-start.json'
    if runner.exists() and (stage/'pg-runner-context-ready.json').exists():
        h=read_record(runner)['identity']
        if observe_original_process(h)['original_live'] is True:
            apps=[dict(pid=h['pid'],start_ticks=h['start_ticks'],uid=os.getuid(),gpu_uuid=uuid)]
    state=stage/'CPU-container-state.json'
    if scenario=='busy' or (scenario=='restore_busy' and state.exists() and read_record(state)['state']['Running'] is False):
        foreign=read_record(stage/'CPU-foreign.json')
        apps.append(dict(pid=foreign['pid'],start_ticks=foreign['start_ticks'],uid=os.getuid(),gpu_uuid=uuid))
    return dict(gpu_uuid=uuid,compute_mode=read_record(stage/'CPU-mode.json')['mode'],compute_apps=apps,
                mps_processes=[],observed_unix=time.time())


def inspect(stage,name):
    scenario=read_record(stage/'CPU-scenario.json')['scenario'];path=stage/'CPU-container-state.json'
    if not path.exists():return None
    row=read_record(path)
    if (stage/'pg-runner-context-granted.json').exists():
        if scenario=='unknown':raise RuntimeError('CPU fixture Docker observation unknown')
        if scenario=='wrong_container':row['id']='f'*64
    return row


def stop_container(stage,name):
    h=read_record(stage/'CPU-container-process.json')['identity']
    if observe_original_process(h)['original_live'] is True:
        os.kill(h['pid'],signal.SIGTERM)
    until=time.monotonic()+10
    while read_record(stage/'CPU-container-state.json')['state']['Running']:
        if time.monotonic()>until:raise TimeoutError('CPU fixture original container stop')
        time.sleep(.01)


def guardian(stage):
    from wcomr.cara_budget_host_guardian_r1 import allocate
    template=read_record(stage/'CPU-launch-template.json');template['guardian_identity']=bind_original_process(os.getpid())
    create_record(stage/'GPU-launch.json',template)
    scenario=read_record(stage/'CPU-scenario.json')['scenario'];changes=[]
    def change(uuid,mode,password):
        assert uuid==template['gpu_uuid'] and password=='CPU-ONLY-NO-CREDENTIAL'
        changes.append(mode);atomic_json(stage/'CPU-mode-changes.json',changes)
        if scenario=='mode_failure' and mode=='EXCLUSIVE_PROCESS':raise RuntimeError('CPU fixture mode command failed')
        atomic_json(stage/'CPU-mode.json',dict(mode={'EXCLUSIVE_PROCESS':'Exclusive_Process','DEFAULT':'Default'}[mode]))
    try:
        allocate(stage.parent.parent,stage,storage_for(stage),None if scenario=='missing_credential' else 'CPU-ONLY-NO-CREDENTIAL',
            cpu_validation=True,observe_gpu=lambda uuid:observe(stage,uuid),change_mode=change,
            inspect=lambda name:inspect(stage,name),stop=lambda name:stop_container(stage,name),interval=.01,release_margin=.5)
    except BaseException as error:
        atomic_json(stage/'CPU-guardian-error.json',dict(type=type(error).__name__,error=str(error)))
        raise


def cli(stage):
    scenario=read_record(stage/'CPU-scenario.json')['scenario'];launch=read_record(stage/'GPU-launch.json')
    if scenario=='no_container':raise SystemExit(7)
    cid=hashlib.sha256((launch['launch_id']+'CPU-container').encode()).hexdigest()
    with (stage/'container.cid').open('x') as stream:stream.write(cid+'\n')
    row=dict(id=cid,name=launch['container'],image=read_record(stage/'registration.json')['container_image'],
        manifest_sha256=launch['registration_sha256'],device_ids=[launch['gpu_uuid']],
        state=dict(Status='exited',Running=False,Pid=0,ExitCode=7,OOMKilled=False))
    if scenario=='init_failure':atomic_json(stage/'CPU-container-state.json',row);raise SystemExit(7)
    child=subprocess.Popen([sys.executable,str(stage/'CPU-fixture.py'),'supervisor',str(stage)],start_new_session=True)
    h=bind_original_process(child.pid);create_record(stage/'CPU-container-process.json',dict(identity=h))
    row['state'].update(Status='running',Running=True,Pid=child.pid,ExitCode=0)
    atomic_json(stage/'CPU-container-state.json',row)
    code=child.wait();row['state'].update(Status='exited',Running=False,Pid=0,ExitCode=code)
    atomic_json(stage/'CPU-container-state.json',row);raise SystemExit(code)


def supervise(stage):
    from wcomr import cara_budget_supervisor_r1 as supervisor
    if read_record(stage/'CPU-scenario.json')['scenario']=='bootstrap_failure':
        # Real original Popen child fails before executing its bootstrap witness.
        # Only this explicit CPU fixture substitutes the child command.
        popen=supervisor.subprocess.Popen
        def fail_before_witness(command,**kwargs):
            return popen([sys.executable,'-c','import time;time.sleep(.2);raise SystemExit(7)'],**kwargs)
        supervisor.subprocess.Popen=fail_before_witness
    supervisor.supervise(stage.parent.parent,stage,storage_for(stage),cpu_validation=True,
        observe_gpu=lambda uuid:observe(stage,uuid),thermal=lambda uuid:{'temperature.gpu':'50'},
        interval=.01,release_margin=.2,context_timeout=5.,thermal_period=.03)


def runner(stage):
    from wcomr.gpu_budget_pool_v2 import process_identity
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    h=process_identity(os.getpid());identity={k:h[k] for k in ('pid','start_ticks')};identity['uid']=os.getuid()
    create_record(stage/'pg-runner-context-ready.json',dict(identity=identity,CPU_fixture_only=True))
    until=time.monotonic()+5
    while not (stage/'pg-runner-context-granted.json').exists():
        if time.monotonic()>until:raise TimeoutError('CPU fixture no context grant')
        time.sleep(.01)
    scenario=read_record(stage/'CPU-scenario.json')['scenario']
    if scenario in ('hard_limit','unknown','wrong_container'):time.sleep(20)
    if scenario=='runner_failure':raise SystemExit(7)
    time.sleep(.05)


if __name__=='__main__':
    role=sys.argv[1];stage=Path(sys.argv[2])
    assert read_record(stage/'CPU-scenario.json')['CPU_fixture_only'] is True
    {'guardian':guardian,'cli':cli,'supervisor':supervise,'runner':runner}[role](stage)
