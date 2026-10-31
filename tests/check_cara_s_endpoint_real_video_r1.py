"""Actual PyAV93-frame CPU media; synthetic release/old scores, no real model."""
import copy
from fractions import Fraction
import hashlib
from pathlib import Path
import shutil

from wcomr import cara_s_endpoint_artifacts_r1 as reader
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import sha
from wcomr.policy_price_terminal_r1 import record
from check_cara_s_endpoint_artifact_fixture_r1 import packet
from test_cara_budget_lifecycle_r1 import put


def write_video(path,tag,*,frames=93,fps=16,height=16,width=16,offset=0):
    import av
    import numpy as np
    seed=hashlib.sha256(tag.encode()).digest()[0]
    with av.open(str(path),'w',format='mp4') as container:
        stream=container.add_stream('libx264',rate=fps)
        stream.width=width;stream.height=height;stream.pix_fmt='yuv420p'
        stream.options={'crf':'0','preset':'ultrafast'}
        stream.codec_context.thread_count=1;stream.codec_context.time_base=Fraction(1,fps)
        for index in range(frames):
            value=((np.arange(height*width*3,dtype=np.uint16).reshape(height,width,3)+seed+index)%256).astype(np.uint8)
            frame=av.VideoFrame.from_ndarray(value,format='rgb24');frame.pts=index+offset;frame.time_base=Fraction(1,fps)
            for encoded in stream.encode(frame):container.mux(encoded)
        for encoded in stream.encode():container.mux(encoded)


def run(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    cache=root/'media-cache';cache.mkdir();cases=[];failures=[]
    def writer(path,tag):
        saved=cache/(hashlib.sha256(tag.encode()).hexdigest()+'.mp4')
        if not saved.exists():write_video(saved,tag)
        shutil.copyfile(saved,path)
    for alias in (False,True):
        args=packet(root/('alias25' if alias else 'full32'),writer,reader.decode_video,alias=alias)
        result=reader.postrelease_manifest(**args);manifest=result['manifest']
        assert len(result['decoded'])==(25 if alias else 32)
        assert len(manifest['pairs'])==(8 if alias else 12) and len(manifest['reused_rows'])==12
        assert manifest['identity_controls_passed']==9 and manifest['formal_logical_positions']==24
        cases.append(dict(alias=alias,physical_videos=manifest['physical_paths'],original_Native_reads=4,
            new_scoring_pairs=len(manifest['pairs']),logical_positions=24,reused_rows=12,identity_controls=9,
            all_frames=93,geometry=[16,16,3],manifest_sha256=digest(manifest),
            original_scopes_preserved=True,metrics_computed=0))
        if not alias:full=args
    for name,options,message in (
        ('short',dict(frames=92),'frame count'),('long',dict(frames=94),'frame count'),
        ('geometry',dict(width=32),'fps/geometry'),('fps',dict(fps=15),'fps/geometry')):
        path=root/(name+'.mp4');write_video(path,name,**options)
        artifact=dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))
        try:reader.decode_video(artifact,shape=(93,16,16,3))
        except ValueError as error:assert message in str(error)
        else:raise AssertionError('Invalid video accepted: '+name)
        failures.append(name)
    path=root/'short.mp4';artifact=dict(path=str(path),bytes=path.stat().st_size,sha256='0'*64)
    try:reader.decode_video(artifact,shape=(93,16,16,3))
    except ValueError as error:assert 'artifact bytes' in str(error)
    else:raise AssertionError('Changed video hash accepted')
    failures.append('hash')
    # Rebind the synthetic producer metadata so only the real RGB/PTS gate can
    # reject these files; no actual production artifact or receipt is altered.
    capture=full['capture'];original_collection=record(capture,'collection')
    for fault,section,message,options in (
        ('RGB_replay','REPLAY_CONTROL','RGB identity control',{}),
        ('RGB_allD','ALLD_EQUIVALENCE','RGB identity control',{}),
        ('PTS_offset','FORMAL','PTS differ',dict(offset=1))):
        collection=copy.deepcopy(original_collection)
        row=next(r for r in collection['rows'] if r['slot']['purpose']==section)
        path=Path(row['result']['video_path']);saved=path.read_bytes();write_video(path,'different RGB fixture',**options)
        row['result']['endpoint_video_artifact'].update(bytes=path.stat().st_size,sha256=sha(path))
        put(capture,'collection',collection)
        put(capture,'runner_terminal',dict(scope_sha256=full['card']['scope_sha256'],collection_sha256=digest(collection)))
        try:reader.postrelease_manifest(**full)
        except ValueError as error:assert message in str(error),(fault,str(error))
        else:raise AssertionError('Invalid replay control accepted: '+fault)
        finally:path.write_bytes(saved)
        failures.append(fault)
    assert len(failures)==8
    return dict(status='REAL_PYAV_COMPLETE_ENDPOINT_MEDIA_CPU_PASS',cases=cases,failure_controls=failures,
        complete_new_video_reads=57,complete_original_Native_reads=8,complete_frame_reads=65*93,
        actual_original_experiment_videos_read=False,model_loaded=False,metrics_computed=0,
        tensor_contents='SYNTHETIC_BYTES_FOR_FILE_INTEGRITY_ONLY',whole_GPU_card_accepted=False)
