"""Read only the original endpoint score container; never dispatch or retry."""
import datetime
import json
from pathlib import Path
import re
import subprocess

from .cara_budget_original_handles_r1 import observe_original_process
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_scores_r1 import bind_scorer, validate_config, accept_scores, WORKER
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_score_capture_r1.py'
IMAGE='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'


def container_time(value):
    # Docker uses RFC3339Nano; Python 3.9/3.10 fromisoformat cannot parse nine digits.
    match=re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?Z',value)
    require(match is not None,'Original Docker UTC timestamp required')
    base=datetime.datetime.strptime(match[1],'%Y-%m-%dT%H:%M:%S')
    return base.replace(tzinfo=datetime.timezone.utc,microsecond=int((match[2] or '').ljust(6,'0')[:6])).timestamp()


def inspect_original(container_id):
    """Absent and transport/daemon failures are UNKNOWN, never permission to run."""
    try:
        result=subprocess.run(['docker','inspect',container_id],capture_output=True,text=True,timeout=20)
    except (OSError,subprocess.TimeoutExpired) as error:
        return dict(status='UNKNOWN',reason=type(error).__name__)
    if result.returncode:
        return dict(status='UNKNOWN',reason='ORIGINAL_CONTAINER_INSPECT_FAILED',exit_code=result.returncode)
    try:
        records=json.loads(result.stdout)
        require(isinstance(records,list) and len(records)==1 and isinstance(records[0],dict),
                'One original container inspection required')
    except (ValueError,TypeError):
        return dict(status='UNKNOWN',reason='ORIGINAL_CONTAINER_INSPECT_INVALID')
    return dict(status='OBSERVED',container=records[0])


def validate_container(container,binding,config,*,cpu_validation=False):
    stage=Path(binding['stage']);project=stage.parents[1]
    out=project/'outputs'/config['run_id']/'endpoint-score-CPU'
    state,host,settings=container['State'],container['HostConfig'],container['Config']
    require(container['Id']==binding['container_id'] and container['Name']=='/'+binding['container']
            and container['Image']==IMAGE and settings['Labels']['wcomr.manifest']==binding['manifest_sha256'],
            'Original container ID/name/image/manifest differs')
    cores='26' if cpu_validation else '26,27'
    require(host['NanoCpus']==config['CPU_bound']['cpus']*10**9
            and host['Memory']==host['MemorySwap']==8*1024**3 and host['CpusetCpus']==cores
            and host['DeviceRequests'] in (None,[]) and host['Devices'] in (None,[])
            and host['Privileged'] is False and host['NetworkMode']=='none'
            and host['ReadonlyRootfs'] is True and host['PidMode']=='host'
            and host['AutoRemove'] is False and host['RestartPolicy']['Name']=='no'
            and host['CapAdd'] in (None,[]),'Original bounded non-restarting CPU container differs')
    expected=[(str(project),str(project),False),(str(stage),str(stage),False),(str(out),str(out),True)]
    mounts=[(r['Source'],r['Destination'],r['RW']) for r in container['Mounts'] if r['Type']=='bind']
    require(sorted(mounts)==sorted(expected)
            and all(r['Type']=='bind' or (r['Type']=='tmpfs' and r['Destination']=='/tmp') for r in container['Mounts']),
            'Exact read-only sources and sole writable score output required')
    environment=dict(item.split('=',1) for item in settings['Env'])
    require(environment.get('CUDA_VISIBLE_DEVICES')=='' and environment.get('NVIDIA_VISIBLE_DEVICES')=='void'
            and environment.get('PYTHONPATH')==str(stage/'scripts')+':'+str(stage/'src')
            and settings['WorkingDir']==str(project/'runtime')
            and settings['User']==binding['container_user'], 'Original CPU environment/user differs')
    command=[str(stage/WORKER),'--manifest',str(out/'manifest.json'),'--output',str(out/'scores.json')]
    if cpu_validation:command.append('--cpu-validation')
    require(settings['Entrypoint']==[str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python')]
            and settings['Cmd']==command,'Original scorer entrypoint/command differs')
    return state,host,out


def recover(binding,packet,config,*,cpu_validation=False):
    """A terminal result is opened only after container and CLI have exited.

    The caller supplies the saved launch binding, not a newly inferred identity.
    This reader does not create a missing launch binding or consume a once intent.
    """
    validate_config(config,cpu_validation=cpu_validation)
    expected=bind_scorer(packet,{k:config[k] for k in ('torch_home','piq_site','weights_sha256')},
                         cpu_validation=cpu_validation)
    require(expected==config and binding['CPU_fixture_only'] is cpu_validation,
            'Original complete artifact packet and fixture mode required')
    stage=Path(binding['stage']);project=stage.parents[1]
    prefix='cara-S-endpoint-CPU-fixture-' if cpu_validation else 'cara-S-endpoint-GPU-'
    require(stage.is_absolute() and stage.parent==project/'.sync' and stage.name.startswith(prefix)
            and Path(config['run_id']).name==config['run_id'] and config['run_id'] not in ('.','..')
            and binding['container']==stage.name+'-endpoint-score-cpu'
            and re.fullmatch('[0-9a-f]{64}',binding['container_id']) is not None,
            'Original isolated endpoint stage/container binding required')
    require(binding['launch_id']==config['launch_id'] and binding['run_id']==config['run_id']
            and binding['analysis_scope_sha256']==config['analysis_scope_sha256']
            and binding['artifact_packet_sha256']==digest(packet)
            and binding['original_gpu_launch_sha256']==packet['release']['original_launch_sha256']
            and file_sha(stage/'GPU-launch.json')==binding['original_gpu_launch_sha256'],
            'Original released GPU launch and score binding differ')
    registration=read_record(stage/'registration.json')
    require(file_sha(stage/'registration.json')==binding['registration_sha256']
            and registration['host']=='two_card'
            and registration['payload_sha256'][SOURCE]==file_sha(__file__)
            and all(file_sha(stage/name)==value for name,value in registration['payload_sha256'].items())
            and all(file_sha(project/'runtime'/name)==value for name,value in registration['runtime_source_sha256'].items()),
            'Original registered score source/runtime differs')
    out=project/'outputs'/config['run_id']/'endpoint-score-CPU'
    manifest=out/'manifest.json'
    require(read_record(manifest)==config and file_sha(manifest)==binding['manifest_sha256'],
            'Original scoring manifest bytes differ')
    inspection=inspect_original(binding['container_id'])
    operational=dict(status='ORIGINAL_SCORE_UNKNOWN',binding_sha256=digest(binding),inspection=inspection,
        scoring_dispatch_allowed=False,GPU_submissions=0,ledger_written=False,scientific_output_read=False)
    if inspection['status']=='UNKNOWN':return operational
    container=inspection['container'];state,host,out=validate_container(container,binding,config,cpu_validation=cpu_validation)
    cli=observe_original_process(binding['cli_identity']);operational['cli_observation']=cli
    if cli['original_live'] is None:return operational
    if state['Running'] or state['Status'] in ('created','running','restarting','paused') or cli['original_live']:
        operational['status']='ORIGINAL_SCORE_ACTIVE';return operational
    require(state['Status']=='exited' and state['Pid']==0,'Original score container terminal state unresolved')
    if state['ExitCode']!=0 or state['OOMKilled']:
        operational['status']='ORIGINAL_SCORE_FAILED';return operational
    intent=read_record(out/'scores-intent.json')
    require(intent['manifest_sha256']==binding['manifest_sha256'] and intent['no_replay'] is True
            and intent['CPU_fixture_only'] is cpu_validation
            and intent['registered_pairs']==[p['id'] for p in config['pairs']]
            and intent['worker_sha256']==config['scorer_source_sha256'][WORKER], 'Original score intent differs')
    worker=observe_original_process(intent['original_identity']);operational['worker_observation']=worker
    if worker['original_live'] is not False:return operational
    result=read_record(out/'scores.json')
    require(result['original_identity']==intent['original_identity'],'Original scorer process replaced')
    started,ended=container_time(state['StartedAt']),container_time(state['FinishedAt'])
    require(started<=result['started_unix']<=result['ended_unix']<=ended,
            'Original scoring interval is outside the container lifetime')
    execution=dict(kind='ORIGINAL_ENDPOINT_SCORE_CONTAINER',container_id=container['Id'],container_state=state,
        host_config=host,manifest_sha256=binding['manifest_sha256'],manifest_label_sha256=container['Config']['Labels']['wcomr.manifest'],
        launch_id=config['launch_id'],source_actual_sha256=config['scorer_source_sha256'],wall_seconds=ended-started,
        result_sha256=digest(result),original_identity=intent['original_identity'],original_observation=worker,
        cli_observation=cli,exit_code=0,original_process_ended=True,GPU_hidden=True)
    if cpu_validation:execution['kind']='ACTUAL_CPU_FIXTURE_CHILD'
    accepted=accept_scores(packet,config,binding['manifest_sha256'],result,execution,cpu_validation=cpu_validation)
    require(file_sha(manifest)==binding['manifest_sha256'],'Original manifest changed during acceptance')
    return dict(operational,status='ORIGINAL_COMPLETE24_SCORE_ACCEPTED',scientific_output_read=True,
        CPU_fixture_only=cpu_validation,execution=execution,accepted=accepted)

