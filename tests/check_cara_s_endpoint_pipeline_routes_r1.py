"""Actual tiny sampling -> full video -> released artifacts -> actual CPU scores."""
import copy
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr import cara_s_endpoint_pipeline_r1 as pipeline
from wcomr import cara_s_endpoint_score_dispatch_r1 as dispatch
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_requests_r2 import Requests
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_endpoint_artifacts_r1 import decode_video,PROPOSAL,ORIGINAL_SCORES
from wcomr.cara_s_endpoint_release_r1 import CARD,BINDING
from wcomr.cara_s_endpoint_scores_r1 import bind_scorer,SCORER_SOURCES
from wcomr.cara_s_uniform_endpoint_execution_r1 import make_requests
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr.policy_price_terminal_r1 import record
from check_cara_s_endpoint_pipeline_fixture_r1 import packet
from test_cara_budget_lifecycle_r1 import put

ROOT=Path(__file__).resolve().parents[1]


def write_video(video,path,fps):
    import av
    value=np.asarray(video)
    assert value.shape==(93,64,64,3) and value.dtype==np.uint8 and fps==16
    with av.open(str(path)+'.mp4','w',format='mp4') as container:
        stream=container.add_stream('libx264',rate=16);stream.width=stream.height=64;stream.pix_fmt='yuv420p'
        stream.options={'crf':'0','preset':'ultrafast'};stream.codec_context.thread_count=1
        for index,rgb in enumerate(value):
            frame=av.VideoFrame.from_ndarray(rgb,format='rgb24');frame.pts=index;frame.time_base=Fraction(1,16)
            for item in stream.encode(frame):container.mux(item)
        for item in stream.encode():container.mux(item)


def materialize_cpu_stage(args):
    """Publish the CPU-only lifecycle fixture's exact source and config files."""
    capture=args['capture'];launch=record(capture,'launch');stage=Path(launch['stage']);project=stage.parents[1]
    shutil.copytree(ROOT/'src',stage/'src',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT/'scripts',stage/'scripts',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    protocol='plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json'
    (stage/protocol).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/protocol,stage/protocol)
    for key,name in (('endpoint_card',CARD),('endpoint_binding',BINDING),('endpoint_proposal',PROPOSAL),('original_scores',ORIGINAL_SCORES)):
        (stage/name).parent.mkdir(parents=True,exist_ok=True);(stage/name).write_text(capture['files'][key]['raw_utf8'])
    registration=record(capture,'registration')
    sources=set(registration['payload_sha256'])|set(SCORER_SOURCES)|{pipeline.SOURCE,dispatch.SOURCE,dispatch.BOOTSTRAP,
                                                                 dispatch.capture.SOURCE,protocol}
    registration['payload_sha256']={name:sha(stage/name) for name in sources}
    (project/'runtime').mkdir();(project/'runtime/CPU-runtime.txt').write_text('Explicit CPU lifecycle stand-in\n')
    registration['runtime_source_sha256']={'CPU-runtime.txt':sha(project/'runtime/CPU-runtime.txt')}
    capture['payload_actual_sha256']=registration['payload_sha256'].copy()
    capture['runtime_actual_sha256']=registration['runtime_source_sha256'].copy()
    reg_sha=put(capture,'registration',registration)
    job=args['CPU_job'];job['registration_sha256']=reg_sha
    reserve_sha=put(capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
    launch.update(registration_sha256=reg_sha,central_reservation_sha256=reserve_sha)
    args['expected_launch_sha256']=put(capture,'launch',launch)
    capture['container']['manifest_sha256']=reg_sha
    guardian=record(capture,'guardian');guardian['container_terminal_witness']['container']=copy.deepcopy(capture['container'])
    put(capture,'guardian',guardian)
    for name,key in (('registration.json','registration'),('GPU-launch.json','launch')):
        (stage/name).write_text(capture['files'][key]['raw_utf8'])
    pool=args['CPU_pool'];initial=pool.read();initial['jobs'][job['job_id']]=job
    initial.update(pool.accounting(initial));atomic_json(pool.path,initial)
    return stage,launch


def score_container_fixture(stage,config,manifest_sha):
    project=stage.parents[1];_,out=dispatch.paths(stage,config)
    return dict(Id='a'*64,Name='/'+stage.name+'-endpoint-score-cpu',Image=dispatch.capture.IMAGE,
        State=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False),
        HostConfig=dict(NanoCpus=10**9,Memory=8*1024**3,MemorySwap=8*1024**3,CpusetCpus='26',DeviceRequests=None,
            Devices=[],Privileged=False,NetworkMode='none',ReadonlyRootfs=True,PidMode='host',AutoRemove=False,
            RestartPolicy={'Name':'no'},CapAdd=None),
        Mounts=[dict(Type='bind',Source=str(p),Destination=str(p),RW=rw) for p,rw in ((project,False),(stage,False),(out,True))],
        Config=dict(Labels={'wcomr.manifest':manifest_sha},Env=['CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void',
            'PYTHONPATH='+str(stage/'scripts')+':'+str(stage/'src')],WorkingDir=str(project/'runtime'),
            User=str(os.getuid())+':'+str(os.getgid()),Entrypoint=[str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python')],
            Cmd=[str(stage/dispatch.WORKER),'--manifest',str(out/'manifest.json'),'--output',str(out/'scores.json'),'--cpu-validation']))


def once_actual_score(stage,saved,environment):
    from test_cara_s_endpoint_score_capture_r1 import save
    import check_cara_s_endpoint_score_dispatch_process_r1 as process_fixture
    config=bind_scorer(saved,environment,cpu_validation=True)
    _,out=dispatch.paths(stage,config);out.mkdir()
    atomic_json(out/'manifest.json',config)
    save(stage/'CPU-container-template.json',score_container_fixture(stage,config,sha(out/'manifest.json')))
    save(stage/'CPU-scenario.json',dict(scenario='complete',CPU_fixture_only=True))
    shutil.copyfile(ROOT/'tests/check_cara_s_endpoint_pipeline_process_r1.py',stage/'CPU-fixture.py')
    shutil.copyfile(ROOT/'tests/check_cara_s_endpoint_score_dispatch_process_r1.py',stage/'CPU-process-base.py')
    popen=subprocess.Popen;children=[]
    def spawn(command,**kwargs):
        assert command[1:3]==[str(stage/dispatch.BOOTSTRAP),'supervise']
        child=popen([sys.executable,str(stage/'CPU-fixture.py'),'supervise',str(stage)],
            **dict(kwargs,env=dict(kwargs['env'],PYTHONPATH=str(stage/'src')+':'+str(stage/'scripts'))))
        children.append(child);return child
    command=[sys.executable,str(stage/'CPU-fixture.py'),'cli',str(stage)]
    with patch.object(dispatch,'require_absent'),patch.object(dispatch,'score_command',return_value=command), \
         patch.object(dispatch.subprocess,'Popen',side_effect=spawn):
        dispatch.dispatch(stage,saved,config,sha(stage/'registration.json'),cpu_validation=True,work_seconds=180.)
    child=children[0];handle=bind_original_process(child.pid)
    try:code=child.wait(timeout=210)
    except subprocess.TimeoutExpired:
        from wcomr.cara_budget_supervisor_r1 import stop_original
        stop_original(child,handle);raise
    assert code==0,(out/'supervisor.log').read_text()[-5000:]
    with patch.object(dispatch.capture,'inspect_original',side_effect=lambda cid:process_fixture.inspect(stage,cid)):
        result=dispatch.recover(stage)
        assert result['status']=='ORIGINAL_COMPLETE24_SCORE_ACCEPTED'
        before={p.name:sha(p) for p in out.iterdir() if p.is_file()}
        with patch.object(dispatch.subprocess,'Popen',side_effect=AssertionError('Repeated endpoint scorer')):
            assert dispatch.dispatch(stage,saved,config,sha(stage/'registration.json'),cpu_validation=True)['status']==result['status']
        assert before=={p.name:sha(p) for p in out.iterdir() if p.is_file()}
    return result['score_capture']


def body(inference,selected,wc,rf,common,unused_initial,profile,root,native,flow,inference_module,host,samples):
    import check_wc_time_card_r1 as fixture
    model,net=inference.pipe.model,inference.pipe.model.net
    net.__class__=fixture.load('check_fair_sampling_cpu').native_toy_class(Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale=.001
    base=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    for item in base['inputs']:item['resolution']='16,16'
    base['roles']['ALLD']['settings']['worldcache_flow_enabled']=flow
    base['scope_sha256']=digest({k:v for k,v in base.items() if k!='scope_sha256'})
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));origin=initial.fingerprint()
    ra=json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    kwargs=dict(inference=inference,samples=samples,common=common,ra_binding=ra,host=host)
    originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
    def before(slot):
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)==originals
        initial.restore();assert initial.fingerprint()==origin
    def decoder(latent):
        value=latent.mean().tanh().reshape(1,1,1,1,1)
        return (value+torch.linspace(-.1,.1,93).reshape(1,1,93,1,1)).expand(1,3,93,64,64).clone()
    historical=Requests(card=base,frozen=dict(scope_sha256=base['scope_sha256'],phase_A_GPU_released=True,selected={}),
                        cpu_validation=True,**kwargs)
    cached={};cases=[]
    overlay=ROOT.parent/'wc-time-score-CPU-two_card-r1-20261027'
    environment=dict(torch_home=str(overlay/'torch'),piq_site=str(overlay/'site'),weights_sha256={})
    def historical_writer(path,tag):
        member,role=tag.split('|');key=(member,role)
        if key not in cached:
            slot=next(s for s in base['physical_matrix'] if s['section']=='B_QUALITY' and s['member']==member and s['role']==role)
            before(slot);result=historical(slot,path.parent)
            assert result['status']=='COMPLETE' and result['video_path']==str(path)
            cached[key]=path
        else:
            for suffix in ('.mp4','.json'):shutil.copyfile(cached[key].with_suffix(suffix),path.with_suffix(suffix))
    try:
        with clean.patched(model.tokenizer,'decode',decoder),clean.patched(inference_module,'save_img_or_video',write_video):
            for alias in (False,True):
                project=root/('pipeline-alias25' if alias else 'pipeline-full32')
                args=packet(project,historical_writer,decode_video,alias=alias,flow=flow)
                stage,launch=materialize_cpu_stage(args);card,bound=args['card'],args['bound']
                output=project/'outputs'/launch['run_id'];output.mkdir(parents=True)
                context=dict(launch,physical_paths=len(card['physical_matrix']),endpoint_binding_sha256=bound['binding_sha256'])
                adapter=make_requests(card,bound,cpu_validation=True,**kwargs)
                collection=pipeline.collect(adapter,output,context,before_request=before,precision=record(args['capture'],'precision'))
                recovered=pipeline.recover_collection(card,output,cpu_validation=True)
                assert recovered['counts']['COMPLETE']==(25 if alias else 32)
                try:pipeline.collect(make_requests(card,bound,cpu_validation=True,**kwargs),output,context,before_request=before,precision={})
                except ValueError:pass
                else:raise AssertionError('Complete collection replayed')
                pool=args['CPU_pool'];before_ledger=pool.read()
                after=pool.settle(launch['run_id'],.05,args['capture']['files']['billing']['sha256'])
                settlement=dict(central_ledger_host='four_card',launch_id=launch['launch_id'],billing_sha256=args['capture']['files']['billing']['sha256'],
                                central_before=before_ledger,central_after=after)
                saved=pipeline.released_artifacts(args['capture'],args['expected_launch_sha256'],settlement,cpu_validation=True,cpu_shape=(93,64,64,3))
                assert saved['manifest']['identity_controls_passed']==9
                scored=once_actual_score(stage,saved,environment);accepted=scored['accepted']
                assert accepted['formal_logical_positions']==24 and accepted['new_scored_pairs']==(8 if alias else 12)
                assert all(accepted['source_rows'][r['id']]==r for r in saved['manifest']['reused_rows'])
                cases.append(dict(status='PASS',flow=flow,alias=alias,physical_paths=len(collection['rows']),
                    new_pairs=accepted['new_scored_pairs'],logical_positions=24,reused_rows_unchanged=12,
                    RGB_controls=9,full_frames_per_video=93,collection_sha256=digest(collection),
                    artifact_packet_sha256=digest(saved),accepted_score_sha256=digest(accepted),
                    score_execution=scored['execution'],replay_refused=True,temporary_ledger_only=True,
                    actual_Cosmos_weights=False,original_experiment_outputs_read=False))
    finally:initial.restore()
    assert len(cached)==16
    return [dict(status='PASS',flow=flow,cases=cases,actual_collection_paths=57,historical_tiny_paths=16,
                 actual_new_metric_pairs=20,original_experiment_pairs_rescored=0)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    previous=fixture.body;fixture.body=body
    try:return fixture.run(runtime,artifact_root,host,samples)
    finally:fixture.body=previous
