"""Complete12/8 synthetic pairs through the actual Alex/PIQ CPU CLI."""
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from wcomr import cara_s_endpoint_artifacts_r1 as artifacts
from wcomr import cara_s_endpoint_scores_r1 as scores
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_budget_supervisor_r1 import stop_original
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from check_cara_s_endpoint_artifact_fixture_r2 import packet,PROPOSAL
from check_cara_s_endpoint_real_video_r1 import write_video

ROOT=Path(__file__).resolve().parents[1]


def write_black(path):
    import av
    import numpy as np
    with av.open(str(path),'w',format='mp4') as container:
        stream=container.add_stream('libx264',rate=16);stream.width=stream.height=64;stream.pix_fmt='yuv420p'
        stream.options={'crf':'0','preset':'ultrafast'};stream.codec_context.thread_count=1
        for index in range(93):
            frame=av.VideoFrame.from_ndarray(np.zeros((64,64,3),dtype=np.uint8),format='rgb24')
            frame.pts=index;frame.time_base=Fraction(1,16)
            for encoded in stream.encode(frame):container.mux(encoded)
        for encoded in stream.encode():container.mux(encoded)


def run(root,stage,*,deadline):
    root=Path(root);stage=Path(stage);root.mkdir(parents=True,exist_ok=False)
    members=json.loads((ROOT/PROPOSAL).read_text())['FIT']+json.loads((ROOT/PROPOSAL).read_text())['CHECK']
    cache=root/'media-cache';cache.mkdir();cases=[]
    def writer(path,tag):
        member,role=tag.split('|')
        if member==members[1]:tag='BLACK'
        elif member==members[0] and role=='SU19_BR_DIAG_C':tag=member+'|NATIVE35'
        source=cache/(hashlib.sha256(tag.encode()).hexdigest()+'.mp4')
        if not source.exists():
            if tag=='BLACK':write_black(source)
            else:write_video(source,tag,height=64,width=64)
        shutil.copyfile(source,path)
    overlay=stage.parent/'wc-time-score-CPU-two_card-r1-20261027'
    environment=dict(torch_home=str(overlay/'torch'),piq_site=str(overlay/'site'),weights_sha256={})

    def child(manifest_path,result_path):
        command=[sys.executable,str(ROOT/scores.WORKER),'--manifest',str(manifest_path),
                 '--output',str(result_path),'--cpu-validation']
        started=time.time()
        with result_path.with_suffix('.log').open('x') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            identity=bind_original_process(process.pid)
            try:code=process.wait(timeout=min(720,deadline-time.monotonic()))
            finally:stop_original(process,identity)
        observation=observe_original_process(identity);assert observation['original_live'] is False
        result=json.loads(result_path.read_text()) if result_path.exists() else None
        return result,dict(kind='ACTUAL_CPU_FIXTURE_CHILD',exit_code=code,original_process_ended=True,GPU_hidden=True,
            original_identity=identity,original_observation=observation,manifest_sha256=sha(manifest_path),
            source_actual_sha256={p:sha(ROOT/p) for p in scores.SCORER_SOURCES},wall_seconds=time.time()-started,
            result_sha256=digest(result)),command

    def no_replay(command,result_path):
        paths=[result_path,result_path.with_name(result_path.stem+'-intent.json')]
        before={str(p):sha(p) for p in paths}
        repeated=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        assert repeated.returncode!=0 and before=={str(p):sha(p) for p in paths}
        return True

    for alias in (False,True):
        args=packet(root/('alias25' if alias else 'full32'),writer,artifacts.decode_video,alias=alias,shape=(93,64,64,3))
        saved=artifacts.postrelease_manifest(**args)
        config=scores.bind_scorer(saved,environment,cpu_validation=True)
        manifest_path=root/('alias-manifest.json' if alias else 'full-manifest.json')
        result_path=root/('alias-result.json' if alias else 'full-result.json')
        atomic_json(manifest_path,config)
        result,execution,command=child(manifest_path,result_path)
        assert execution['exit_code']==0,(result_path.with_suffix('.log').read_text()[-2500:])
        assert result['original_identity']==execution['original_identity']
        accepted=scores.accept_scores(saved,config,sha(manifest_path),result,execution,cpu_validation=True)
        assert accepted['new_scored_pairs']==(8 if alias else 12)
        assert len(accepted['positions'])==24 and accepted['reused_original_rows']==12
        assert all(accepted['source_rows'][r['id']]==r for r in config['reused_rows'])
        infinite=[r for r in result['rows'] if r['MSE_video']==0]
        undefined=[r for r in result['rows'] if r['reference_gradient_energy']==0]
        assert infinite and undefined
        assert all(r['Alex']==0 and abs(r['SSIM']-1)<1e-6 and r['PSNR_video_dB']=='+inf' for r in infinite)
        assert all(r['gradient_energy_ratio'] is None and r['gradient_ratio_status']=='ZERO_REFERENCE_ENERGY' for r in undefined)
        cases.append(dict(alias=alias,new_pairs=accepted['new_scored_pairs'],frames_per_pair=93,temporal_pairs=92,
            logical_positions=24,original_rows_unchanged=12,original_scopes_preserved=True,
            infinite_PSNR_pairs=len(infinite),undefined_gradient_pairs=len(undefined),
            no_replay=no_replay(command,result_path),execution=execution,accepted_sha256=digest(accepted),
            manifest_sha256=sha(manifest_path),result_file_sha256=sha(result_path)))
        if not alias:full=(saved,config)
    saved,config=full
    target=Path(config['pairs'][1]['candidate']['path']);original=target.read_bytes()
    manifest_path=root/'failed-manifest.json';result_path=root/'failed-result.json'
    atomic_json(manifest_path,config);target.write_bytes(b'CPU-ONLY-INTENTIONAL-CHANGED-VIDEO')
    try:result,execution,command=child(manifest_path,result_path)
    finally:target.write_bytes(original)
    assert execution['exit_code']!=0 and result['status']=='FAILED_DENOMINATOR_RETAINED'
    assert len(result['registered_pairs'])==12 and len(result['rows'])==1
    assert result['rows'][0]['frames']==93 and not result['CUDA_initialized']
    assert 'SHA differs' in result['error']
    assert no_replay(command,result_path)
    return dict(status='ACTUAL_CROSS_SCOPE_COMPLETE_SCORER_CPU_PASS',cases=cases,
        failed_case=dict(execution=execution,complete_registered_pairs=12,completed_rows=1,
            status=result['status'],no_replay=True,frame_count_of_completed_row=93),
        new_synthetic_pairs_scored=20,failure_fixture_pairs_scored=1,old_experiment_videos_rescored=0,
        original_scientific_scores_computed=0,metric_weights_loaded=True,generative_model_loaded=False,
        whole_GPU_card_accepted=False)
