"""Only recover the original released P1 score container and immutable result."""
from pathlib import Path
import re

from .cara_budget_original_handles_r1 import observe_original_process
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_read_write_score_capture_r1 import inspect_original,container_time,IMAGE
from .cara_source_lifecycle_p1_identity_r1 import RUN_ID,STAGE_NAME
from .cara_source_lifecycle_p1_scores_r1 import bind_post_scorer,validate_config,accept_scores,WORKER
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_source_lifecycle_p1_score_capture_r1.py'
DISPATCH='src/wcomr/cara_source_lifecycle_p1_score_dispatch_r1.py'
BOOTSTRAP='scripts/cara_source_lifecycle_p1_score_bootstrap_r1.py'


def paths(stage,config):
    stage=Path(stage);m=config['manifest']
    require(stage.is_absolute() and stage.parent.name=='.sync' and m['run_id']==RUN_ID
        and (stage.name.startswith('cara-source-lifecycle-P1-post-CPU-') if config['CPU_fixture_only'] else stage.name==STAGE_NAME),
        'Original production P1 or explicit isolated post-score CPU-fixture stage required')
    # Real host CPU probes must not occupy a future production run's output.
    output_run=RUN_ID+'-fixture-'+stage.name if config['CPU_fixture_only'] else RUN_ID
    return stage/'post-score-control',stage.parents[1]/'outputs'/output_run/'post-score-CPU'


def verify(stage,packet,config,registration_sha256,*,cpu_validation=False):
    stage=Path(stage);project=stage.parents[1];paths(stage,config)
    validate_config(config,cpu_validation=cpu_validation)
    require(config==bind_post_scorer(packet,{k:config[k] for k in ('torch_home','piq_site','weights_sha256')},
        cpu_validation=cpu_validation),'Original released full146 artifact packet and score source required')
    require(file_sha(stage/'GPU-launch.json')==packet['release']['original_launch_sha256'],
        'Original released GPU launch differs')
    reg=read_record(stage/'registration.json')
    require(file_sha(stage/'registration.json')==registration_sha256 and reg['host']=='two_card'
        and all(n in reg['payload_sha256'] for n in (SOURCE,DISPATCH,BOOTSTRAP,WORKER))
        and reg['payload_sha256'][SOURCE]==file_sha(__file__)
        and all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
        and all(file_sha(project/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items()),
        'Original whole registered P1 score source/runtime differs')


def validate_container(container,binding,config,*,cpu_validation=False):
    stage=Path(binding['stage']);project=stage.parents[1];_,out=paths(stage,config)
    state,host,settings=container['State'],container['HostConfig'],container['Config']
    require(container['Id']==binding['container_id'] and container['Name']=='/'+binding['container']
        and container['Image']==IMAGE and settings['Labels']['wcomr.manifest']==binding['manifest_sha256'],
        'Original P1 score container ID/name/image/manifest differs')
    require(host['NanoCpus']==2*10**9 and host['Memory']==host['MemorySwap']==8*2**30 and host['CpusetCpus']=='26,27'
        and host['DeviceRequests'] in (None,[]) and host['Devices'] in (None,[]) and host['CapAdd'] in (None,[])
        and host['Privileged'] is False and host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True
        and host['PidMode']=='host' and host['AutoRemove'] is False and host['RestartPolicy']['Name']=='no',
        'Original bounded2CPU/8GiB/no-swap/GPU-hidden P1 score container required')
    mounts=[(m['Source'],m['Destination'],m['RW']) for m in container['Mounts'] if m['Type']=='bind']
    require(sorted(mounts)==sorted((str(p),str(p),rw) for p,rw in ((project,False),(stage,False),(out,True)))
        and all(m['Type']=='bind' or (m['Type']=='tmpfs' and m['Destination']=='/tmp') for m in container['Mounts']),
        'Only read-only P1 sources and the sole writable post-score output required')
    env=dict(v.split('=',1) for v in settings['Env'])
    command=[str(stage/WORKER),'--manifest',str(out/'manifest.json'),'--output',str(out/'scores.json')]
    if cpu_validation:command.append('--cpu-validation')
    require(env.get('CUDA_VISIBLE_DEVICES')=='' and env.get('NVIDIA_VISIBLE_DEVICES')=='void'
        and env.get('PYTHONPATH')==str(stage/'scripts')+':'+str(stage/'src')
        and settings['WorkingDir']==str(project/'runtime') and settings['User']==binding['container_user']
        and settings['Entrypoint']==[str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python')]
        and settings['Cmd']==command,'Original P1 score environment/user/command differs')
    return state,host,out


def recover(binding,packet,config,*,cpu_validation=False):
    stage=Path(binding['stage']);control,out=paths(stage,config)
    verify(stage,packet,config,binding['registration_sha256'],cpu_validation=cpu_validation)
    m=config['manifest']
    require(binding['CPU_fixture_only'] is cpu_validation and binding['container']==stage.name+'-p1-post-score-cpu'
        and re.fullmatch('[0-9a-f]{64}',binding['container_id']) is not None
        and binding['run_id']==m['run_id'] and binding['launch_id']==m['launch_id'] and binding['scope_sha256']==m['scope_sha256']
        and binding['artifact_packet_sha256']==digest(packet)
        and binding['original_gpu_launch_sha256']==packet['release']['original_launch_sha256']
        and read_record(out/'manifest.json')==config and file_sha(out/'manifest.json')==binding['manifest_sha256'],
        'Original P1 post-score intent, manifest and released scope differ')
    inspected=inspect_original(binding['container_id'])
    result=dict(status='ORIGINAL_SCORE_UNKNOWN',binding_sha256=digest(binding),inspection=inspected,
        scientific_output_read=False,dispatch_allowed=False,GPU_submissions=0,ledger_written=False)
    if inspected['status']!='OBSERVED':return result
    container=inspected['container'];state,host,out=validate_container(container,binding,config,cpu_validation=cpu_validation)
    cli=observe_original_process(binding['cli_identity']);result['cli_observation']=cli
    if cli['original_live'] is None:return result
    if state['Running'] or cli['original_live'] is True or state['Status'] in ('created','running','paused','restarting'):
        return dict(result,status='ORIGINAL_SCORE_ACTIVE')
    require(state['Status']=='exited' and state['Pid']==0,'Original score container terminal remains unknown')
    if state['ExitCode']!=0 or state['OOMKilled']:return dict(result,status='ORIGINAL_SCORE_FAILED')
    intent=read_record(out/'scores-intent.json')
    require(intent['config_sha256']==digest(config) and intent['no_replay'] is True
        and intent['CPU_fixture_only'] is cpu_validation
        and intent['registered_pairs']==[p['id'] for p in m['new_pairs']], 'Original P1 worker intent differs')
    worker=observe_original_process(intent['original_identity']);result['worker_observation']=worker
    if worker['original_live'] is not False:return result
    score=read_record(out/'scores.json');started,ended=container_time(state['StartedAt']),container_time(state['FinishedAt'])
    require(score['original_identity']==intent['original_identity'] and started<=score['started_unix']<=score['ended_unix']<=ended,
        'Original P1 score process or container interval differs')
    execution=dict(kind='ACTUAL_CPU_FIXTURE_CHILD' if cpu_validation else 'ORIGINAL_P1_POST_SCORE_CONTAINER',
        config_sha256=digest(config),result_sha256=digest(score),source_sha256=config['source_sha256'],
        original_identity=intent['original_identity'],original_observation=worker,cli_observation=cli,
        original_process_ended=True,exit_code=0,GPU_hidden=True,wall_seconds=ended-started,
        container_id=container['Id'],container_state=state,host_config=host)
    accepted=accept_scores(packet,config,score,execution,cpu_validation=cpu_validation)
    require(file_sha(out/'manifest.json')==binding['manifest_sha256'],'Original P1 manifest changed during acceptance')
    return dict(result,status='ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED',scientific_output_read=True,
        execution=execution,accepted=accepted,CPU_fixture_only=cpu_validation)
