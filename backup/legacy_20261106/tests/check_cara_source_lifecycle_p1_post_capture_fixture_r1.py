"""Fresh post-score metadata fixture; Docker/processes/metrics are simulated."""
import copy
import datetime
import json
from pathlib import Path

from wcomr import cara_source_lifecycle_p1_score_capture_r1 as capture
from wcomr.cara_source_lifecycle_p1_scores_r1 import bind_post_scorer,SOURCES,WORKER
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from check_cara_source_lifecycle_p1_score_fixture_r1 import metric

ROOT=Path(__file__).resolve().parents[1]


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def timestamp(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat().replace('+00:00','Z')


def build(project,original_packet,*,with_result=True):
    stage=project/'.sync/cara-source-lifecycle-P1-post-CPU-unit';stage.mkdir(parents=True)
    packet=copy.deepcopy(original_packet)
    save(stage/'GPU-launch.json',dict(CPU_fixture_only=True,launch_id=packet['manifest']['launch_id']))
    packet['release']['original_launch_sha256']=file_sha(stage/'GPU-launch.json')
    packet['manifest']['original_launch_sha256']=packet['release']['original_launch_sha256']
    config=bind_post_scorer(packet,dict(torch_home=str(project/'offline/torch'),piq_site=str(project/'offline/piq'),weights_sha256={}),cpu_validation=True)
    names=(*SOURCES,capture.SOURCE,capture.DISPATCH,capture.BOOTSTRAP)
    for name in names:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    runtime=project/'runtime';runtime.mkdir();(runtime/'CPU-only.txt').write_text('EXPLICIT SYNTHETIC RUNTIME')
    reg=dict(host='two_card',payload_sha256={n:file_sha(stage/n) for n in names},
        runtime_source_sha256={'CPU-only.txt':file_sha(runtime/'CPU-only.txt')})
    save(stage/'registration.json',reg)
    control,out=capture.paths(stage,config);save(out/'manifest.json',config)
    worker=dict(pid=123,start_ticks=456,host_view={'EXPLICIT_CPU_NAMESPACE':True})
    cli=dict(worker,pid=124)
    m=config['manifest']
    binding=dict(CPU_fixture_only=True,stage=str(stage),run_id=m['run_id'],launch_id=m['launch_id'],scope_sha256=m['scope_sha256'],
        container=stage.name+'-p1-post-score-cpu',container_id='a'*64,container_user='1000:1000',cli_identity=cli,
        artifact_packet_sha256=digest(packet),original_gpu_launch_sha256=packet['release']['original_launch_sha256'],
        registration_sha256=file_sha(stage/'registration.json'),manifest_sha256=file_sha(out/'manifest.json'))
    if with_result:
        save(out/'scores-intent.json',dict(config_sha256=digest(config),no_replay=True,CPU_fixture_only=True,
            registered_pairs=[p['id'] for p in m['new_pairs']],original_identity=worker))
        result=dict(status='P1_COMPLETE_NEW_PAIRS_PENDING_INDEPENDENT_ACCEPTANCE',config_sha256=digest(config),
            source_sha256=config['source_sha256'],CPU_fixture_only=True,CUDA_initialized=False,GPU_submissions=0,
            original_identity=worker,registered_pairs=[p['id'] for p in m['new_pairs']],started_unix=1001.,ended_unix=1002.,
            rows=[dict(id=p['id'],**metric(p,packet['decoded'])) for p in m['new_pairs']])
        save(out/'scores.json',result)
    container=dict(Id=binding['container_id'],Name='/'+binding['container'],Image=capture.IMAGE,
        State=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False,
                   StartedAt=timestamp(1000),FinishedAt=timestamp(1003)),
        HostConfig=dict(NanoCpus=2*10**9,Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='26,27',DeviceRequests=None,
            Devices=[],CapAdd=None,Privileged=False,NetworkMode='none',ReadonlyRootfs=True,PidMode='host',AutoRemove=False,RestartPolicy={'Name':'no'}),
        Mounts=[dict(Type='bind',Source=str(p),Destination=str(p),RW=rw) for p,rw in ((project,False),(stage,False),(out,True))],
        Config=dict(Labels={'wcomr.manifest':binding['manifest_sha256']},Env=['CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void',
            'PYTHONPATH='+str(stage/'scripts')+':'+str(stage/'src')],WorkingDir=str(runtime),User=binding['container_user'],
            Entrypoint=[str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python')],
            Cmd=[str(stage/WORKER),'--manifest',str(out/'manifest.json'),'--output',str(out/'scores.json'),'--cpu-validation']))
    return dict(binding=binding,packet=packet,config=config,cpu_validation=True),container,out


def ended(handle):
    return dict(original_live=False,original_pid=handle['pid'],original_start_ticks=handle['start_ticks'],observed_host_view=handle['host_view'])
