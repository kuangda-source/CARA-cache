"""Once-only released endpoint scoring with original-intent recovery."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from . import cara_s_endpoint_score_capture_r1 as capture
from .cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from .cara_budget_search_journal_r1 import create_record,read_record,sync_directory
from .cara_budget_supervisor_r1 import stop_original
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_scores_r1 import bind_scorer,validate_config,WORKER
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_score_dispatch_r1.py'
BOOTSTRAP='scripts/cara_s_endpoint_score_bootstrap_r1.py'


def paths(stage,config):
    stage=Path(stage)
    require(stage.is_absolute() and stage.parent.name=='.sync'
            and Path(config['run_id']).name==config['run_id'] and config['run_id'] not in ('.','..'),
            'Isolated original stage and run paths required')
    return stage/'endpoint-score-control',stage.parents[1]/'outputs'/config['run_id']/'endpoint-score-CPU'


def verify(stage,packet,config,registration_sha256,*,cpu_validation=False):
    stage=Path(stage);project=stage.parents[1];paths(stage,config)
    validate_config(config,cpu_validation=cpu_validation)
    require(config==bind_scorer(packet,{k:config[k] for k in ('torch_home','piq_site','weights_sha256')},
                               cpu_validation=cpu_validation),'Original full artifact/score configuration required')
    prefix='cara-S-endpoint-CPU-fixture-' if cpu_validation else 'cara-S-endpoint-GPU-'
    require(stage.name.startswith(prefix) and file_sha(stage/'GPU-launch.json')==packet['release']['original_launch_sha256'],
            'Original released endpoint stage/launch required')
    registration=read_record(stage/'registration.json')
    require(file_sha(stage/'registration.json')==registration_sha256 and registration['host']=='two_card'
            and registration['payload_sha256'][SOURCE]==file_sha(__file__)
            and all(p in registration['payload_sha256'] for p in (BOOTSTRAP,capture.SOURCE,WORKER))
            and all(file_sha(stage/p)==h for p,h in registration['payload_sha256'].items())
            and all(file_sha(project/'runtime'/p)==h for p,h in registration['runtime_source_sha256'].items()),
            'Original registered score dispatcher/source/runtime differs')


def require_absent(name):
    result=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=20)
    require(result.returncode==1 and result.stderr.strip() in
            ('Error: No such object: '+name,'Error: No such container: '+name),
            'Existing or unknown original score container: recover only')


def resource_admission(stage,config,*,cpu_validation=False):
    _,out=paths(stage,config)
    affinity={26} if cpu_validation else {26,27}
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                       if line.startswith('MemAvailable:')))*1024
    free=shutil.disk_usage(out).free
    require(affinity<=os.sched_getaffinity(0) and available>=12*1024**3 and free>=2*1024**3,
            'Fresh score CPU affinity/memory/disk admission failed')
    checkpoint=Path(config['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'
    require(file_sha(checkpoint)=='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
            and (Path(config['piq_site'])/'piq/__init__.py').is_file()
            and all(file_sha(p)==h for p,h in config['weights_sha256'].items()),
            'Original offline score environment/weights required')
    return dict(observed_unix=time.time(),available_memory_bytes=available,free_disk_bytes=free,CPU_affinity=sorted(affinity))


def score_command(stage,config,manifest_sha256,*,cpu_validation=False):
    from four_card_bank24_execution_tools_r1 import process_environment
    from four_card_policy_assets_port_r1 import container_command
    stage=Path(stage);project=stage.parents[1];control,out=paths(stage,config)
    environment=process_environment(project,out/'caches')
    environment.update(TORCH_HOME=config['torch_home'],TORCHINDUCTOR_COMPILE_THREADS='1')
    command=container_command(project,stage,'cpu-worker',manifest_sha256,environment,os.getuid(),os.getgid())
    command[command.index('--name')+1]=stage.name+'-endpoint-score-cpu'
    command[command.index('--cpus')+1]=str(config['CPU_bound']['cpus'])
    command[command.index('--memory')+1]='8g'
    command[command.index(str(stage)+':'+str(stage)+':rw')]=str(stage)+':'+str(stage)+':ro'
    index=command.index('--entrypoint')
    command[index:index]=['--memory-swap','8g','--cpuset-cpus','26' if cpu_validation else '26,27',
        '--cidfile',str(control/'container.cid'),'-v',str(out)+':'+str(out)+':rw']
    end=command.index('--entrypoint')+3
    result=command[:end]+[str(stage/WORKER),'--manifest',str(out/'manifest.json'),'--output',str(out/'scores.json')]
    if cpu_validation:result.append('--cpu-validation')
    return result


def read_intent(stage):
    stage=Path(stage);control=stage/'endpoint-score-control';intent=read_record(control/'intent.json')
    config=read_record(Path(intent['manifest_path']));packet=read_record(Path(intent['packet_path']))
    _,out=paths(stage,config)
    require(intent['stage']==str(stage) and intent['command_sha256']==digest(intent['command'])
            and intent['manifest_sha256']==file_sha(Path(intent['manifest_path']))
            and intent['artifact_packet_sha256']==digest(packet)
            and intent['manifest_path']==str(out/'manifest.json') and intent['packet_path']==str(out/'artifact-packet.json')
            and 0<intent['work_seconds']<=config['CPU_bound']['wall_hours']*3600
            and (intent['CPU_fixture_only'] or intent['work_seconds']==4*3600),
            'Original frozen score intent differs')
    verify(stage,packet,config,intent['registration_sha256'],cpu_validation=intent['CPU_fixture_only'])
    return intent,packet,config


def recover(stage):
    stage=Path(stage);intent,packet,config=read_intent(stage);control,_=paths(stage,config)
    result=dict(status='ORIGINAL_SCORE_DISPATCH_UNKNOWN',intent_sha256=file_sha(control/'intent.json'),
        dispatch_allowed=False,GPU_submissions=0,ledger_written=False)
    parent=control/'supervisor-start.json'
    if not parent.exists():return result
    started=read_record(parent)
    require(started['intent_sha256']==result['intent_sha256'],'Original score supervisor binding differs')
    observed=observe_original_process(started['identity']);result['supervisor_observation']=observed
    if observed['original_live'] is not False:
        if observed['original_live'] is True:result['status']='ORIGINAL_SCORE_DISPATCH_ACTIVE'
        return result
    terminal=control/'supervisor-terminal.json'
    if not terminal.exists():return result
    ended=read_record(terminal)
    require(ended['intent_sha256']==result['intent_sha256'] and ended['identity']==started['identity'],
            'Original score supervisor terminal differs')
    result['supervisor_terminal']=ended
    if not (control/'container-cli-start.json').exists() or not (control/'container.cid').exists():return result
    cli=read_record(control/'container-cli-start.json')
    require(cli['intent_sha256']==result['intent_sha256'],'Original score CLI binding differs')
    binding=dict(intent,container_id=(control/'container.cid').read_text().strip(),cli_identity=cli['identity'])
    observed=capture.recover(binding,packet,config,cpu_validation=intent['CPU_fixture_only'])
    if observed['status']=='ORIGINAL_COMPLETE24_SCORE_ACCEPTED':
        require(ended['exit_code']==0 and ended['error'] is None and ended['cleanup_error'] is None,
                'Failed/timed-out original score supervisor cannot accept scores')
    return dict(result,status=observed['status'],score_capture=observed)


def dispatch(stage,packet,config,registration_sha256,*,cpu_validation=False,work_seconds=None):
    stage=Path(stage);control,out=paths(stage,config)
    control.mkdir(exist_ok=True)
    with (control/'dispatch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (control/'intent.json').exists():return recover(stage)
        require(not any((control/name).exists() for name in ('supervisor-start.json','container-cli-start.json','container.cid')),
                'Unbound original score handles require recovery')
        verify(stage,packet,config,registration_sha256,cpu_validation=cpu_validation)
        out.mkdir(parents=True,exist_ok=True)
        require(not any((out/name).exists() for name in ('scores.json','scores-intent.json','supervisor.log')),
                'Existing score output requires original recovery')
        require_absent(stage.name+'-endpoint-score-cpu')
        for name,value in (('manifest.json',config),('artifact-packet.json',packet)):
            target=out/name
            raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
            if target.exists():require(target.read_bytes()==raw,'Original prepared score input differs')
            else:
                with target.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
                sync_directory(out)
        maximum=config['CPU_bound']['wall_hours']*3600
        work_seconds=maximum if work_seconds is None else work_seconds
        require(work_seconds==maximum or (cpu_validation and 0<work_seconds<=maximum),
                'Only explicit CPU fixtures may shorten the score deadline')
        command=score_command(stage,config,file_sha(out/'manifest.json'),cpu_validation=cpu_validation)
        admission=resource_admission(stage,config,cpu_validation=cpu_validation)
        intent=dict(stage=str(stage),run_id=config['run_id'],launch_id=config['launch_id'],
            analysis_scope_sha256=config['analysis_scope_sha256'],original_gpu_launch_sha256=packet['release']['original_launch_sha256'],
            registration_sha256=registration_sha256,manifest_path=str(out/'manifest.json'),manifest_sha256=file_sha(out/'manifest.json'),
            packet_path=str(out/'artifact-packet.json'),artifact_packet_sha256=digest(packet),
            container=stage.name+'-endpoint-score-cpu',container_user=str(os.getuid())+':'+str(os.getgid()),
            command=command,command_sha256=digest(command),work_seconds=work_seconds,created_unix=time.time(),
            CPU_fixture_only=cpu_validation,admission=admission,no_replay=True)
        create_record(control/'intent.json',intent)
        with (out/'supervisor.log').open('x') as log:
            child=subprocess.Popen([sys.executable,str(stage/BOOTSTRAP),'supervise','--stage',str(stage)],
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1'))
        return dict(status='ORIGINAL_SCORE_INTENT_CREATED',supervisor_pid=child.pid,intent_sha256=file_sha(control/'intent.json'),
            dispatch_allowed=False,GPU_submissions=0,ledger_written=False)


def exec_cli(stage):
    stage=Path(stage);intent,_,_=read_intent(stage);control=stage/'endpoint-score-control'
    identity=bind_original_process(os.getpid())
    create_record(control/'container-cli-start.json',dict(identity=identity,intent_sha256=file_sha(control/'intent.json')))
    os.execvpe(intent['command'][0],intent['command'],dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))


def stop_container(stage,intent,config):
    control,_=paths(stage,config);cid=control/'container.cid'
    if not cid.exists():return 'ORIGINAL_CONTAINER_ID_UNAVAILABLE'
    binding=dict(intent,container_id=cid.read_text().strip())
    observed=capture.inspect_original(binding['container_id'])
    require(observed['status']=='OBSERVED','Original score container unavailable during stop')
    state,_,_=capture.validate_container(observed['container'],binding,config,cpu_validation=intent['CPU_fixture_only'])
    if state['Running']:
        subprocess.run(['docker','stop','--time','10',binding['container_id']],capture_output=True,text=True,timeout=20,check=True)
    return None


def supervise(stage):
    stage=Path(stage);intent,_,config=read_intent(stage);control,out=paths(stage,config)
    identity=bind_original_process(os.getpid());started=time.monotonic()
    record=dict(identity=identity,intent_sha256=file_sha(control/'intent.json'),started_unix=time.time())
    create_record(control/'supervisor-start.json',record)
    child=None;code=None;error=None;cleanup_error=None
    def interrupted(signum,frame):raise InterruptedError('Original score supervisor interrupted: '+str(signum))
    previous=signal.signal(signal.SIGTERM,interrupted)
    try:
        child=subprocess.Popen([sys.executable,str(stage/BOOTSTRAP),'container-cli','--stage',str(stage)],
            stdin=subprocess.DEVNULL,start_new_session=True,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1'))
        code=child.wait(timeout=max(.001,intent['work_seconds']-(time.monotonic()-started)))
        require(code==0,'Original score container CLI failed')
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught))
        try:cleanup_error=stop_container(stage,intent,config)
        except Exception as cleanup:cleanup_error=dict(type=type(cleanup).__name__,message=str(cleanup))
    finally:
        try:
            if child is not None and child.poll() is None:
                witness=control/'container-cli-start.json'
                handle=read_record(witness)['identity'] if witness.exists() else bind_original_process(child.pid)
                stop_original(child,handle)
            if child is not None:code=child.wait(timeout=10)
        except Exception as cleanup:cleanup_error=dict(type=type(cleanup).__name__,message=str(cleanup))
        signal.signal(signal.SIGTERM,previous)
        create_record(control/'supervisor-terminal.json',dict(record,ended_unix=time.time(),wall_seconds=time.monotonic()-started,
            exit_code=code,error=error,cleanup_error=cleanup_error))
    if error is not None or cleanup_error is not None:raise RuntimeError('Original score supervisor failed; recover original records')
