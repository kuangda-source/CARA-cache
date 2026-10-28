"""One full93 synthetic clip through the actual bounded scoring CLI."""
import argparse
import faulthandler
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--host',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    signal.alarm(600)
    started,cpu_started=time.time(),time.process_time()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/name)==expected for name,expected in registration['payload_sha256'].items())
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
                      HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TORCHINDUCTOR_COMPILE_THREADS='1')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.cara_fast_spec_r1 import digest
    from wcomr.cara_fast_scoring_manifest_r2 import comparison_input_digest
    import av
    import numpy as np
    progress=args.stage/'progress.json'
    progress.write_text(json.dumps(dict(phase='SYNTHETIC_RGB93_ENCODE',started_unix=started))+'\n')
    video=args.stage/'CPU-synthetic-rgb93.avi'
    columns=np.arange(768,dtype=np.uint16)[None,:]
    rows=np.arange(432,dtype=np.uint16)[:,None]
    with av.open(str(video),'w') as output:
        stream=output.add_stream('ffv1',rate=16)
        stream.width,stream.height,stream.pix_fmt=768,432,'bgr0'
        stream.thread_count=1
        for frame in range(93):
            red=np.broadcast_to((columns+frame)%256,(432,768))
            green=np.broadcast_to((rows+2*frame)%256,(432,768))
            blue=(rows+columns+3*frame)%256
            rgb=np.stack([red,green,blue],axis=-1).astype(np.uint8)
            for packet in stream.encode(av.VideoFrame.from_ndarray(rgb,format='rgb24')):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    native_request=dict(name='CPU_SYNTHETIC_RGB93_CONTROL',prompt='deterministic RGB ramps',
        negative_prompt='',guidance=7,seed=0,num_steps=35,resolution='432,768',num_output_frames=93)
    short_request=dict(native_request,num_steps=22)
    scope=digest(dict(control='SCORING_CLI_ONLY_NO_MODEL_METHOD_RESULT',video_sha256=sha(video)))
    shared=dict(path=str(video),sha256=sha(video),member=native_request['name'],seed=0,
        host=args.host,gpu_uuid='NO_GPU_CPU_CONTROL',model_sha256=digest('NO_GENERATIVE_MODEL_LOADED'),
        precision='RGB24_CPU_CONTROL',scope_sha256=scope,
        comparison_input_sha256=comparison_input_digest(native_request))
    pair=dict(id='CPU_SYNTHETIC_MATCHED_PAIR',
        candidate=dict(shared,role='NATIVE22',execution_request_sha256=digest(short_request)),
        reference=dict(shared,role='NATIVE35',execution_request_sha256=digest(native_request)))
    overlay=args.stage.parent/('wc-time-score-CPU-'+args.host+'-r1-20261027')
    cfg=dict(scope_sha256=scope,
        protocol_sha256=digest(json.loads((args.stage/'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json').read_text())),
        CPU_bound=dict(cpus=1,memory_GiB=8,wall_hours=.15,max_pairs=1),
        GPU_released=True,GPU_ever_used=False,CPU_SYNTHETIC_CONTROL_ONLY=True,
        torch_home=str(overlay/'torch'),piq_site=str(overlay/'site'),weights_sha256={},pairs=[pair])
    manifest=args.stage/'scoring-control-manifest.json'
    manifest.write_text(json.dumps(cfg,indent=2)+'\n')
    result_path=args.stage/'scoring-control-result.json'
    command=[sys.executable,str(args.stage/'scripts/score_cara_fast_fidelity_r1.py'),
             '--manifest',str(manifest),'--output',str(result_path)]
    progress.write_text(json.dumps(dict(phase='ACTUAL_SCORING_CLI',started_unix=started,command=command))+'\n')
    score_start=time.time()
    with (args.stage/'scoring-CLI.log').open('x') as log:
        child=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=560)
    assert child.returncode==0, 'Actual scorer subprocess failed; inspect scoring-CLI.log'
    result=json.loads(result_path.read_text())
    assert result['status']=='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED' and not result['CUDA_initialized']
    assert len(result['rows'])==1 and result['registered_pairs']==['CPU_SYNTHETIC_MATCHED_PAIR']
    row=result['rows'][0]
    assert row['frames']==93 and row['temporal_frame_pairs']==92 and row['PTS_equal']
    assert row['Alex']==0 and row['PSNR_video_dB']=='+inf' and row['PSNR_is_infinite']
    assert abs(row['SSIM']-1)<1e-6 and row['reference_temporal_L1']==row['reference_gradient_L1']==0
    assert row['decoded_RGB_sha256'][0]==row['decoded_RGB_sha256'][1]
    assert len(row['Alex_frames'])==len(row['SSIM_frames'])==93
    assert row['candidate']['execution_request_sha256']!=row['reference']['execution_request_sha256']
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(5,repeat=True)
    proof=dict(status='ACTUAL_SCORING_CLI_SYNTHETIC_FULL93_CPU_COMPLETE_NOT_SCIENCE',
        host=args.host,started_unix=started,ended_unix=time.time(),
        CPU_process_seconds=time.process_time()-cpu_started,scorer_own_CPU_seconds=result['CPU_process_seconds'],
        scorer_wall_seconds=time.time()-score_start,scorer_subprocess_exit_code=child.returncode,
        result_sha256=sha(result_path),result_path=str(result_path),manifest_sha256=sha(manifest),
        registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=registration['payload_sha256'],runtime_source_sha256=registration['runtime_source_sha256'],
        frames=93,PTS_pairs=92,synthetic_control_clips=1,real_model_videos_generated=0,old_videos_rescored=0,
        fixture_role_names_are_not_method_results=True,Native_k_distinct_execution_identity_accepted=True,
        identical_Alex0_PSNRinf_SSIM1=True,decoded_RGB_equal=True,metric_frame_curves_complete=True,
        CUDA_initialized=False,GPU_submissions=0,ledger_written=False,
        resource_bound=dict(actual_cpus=1,actual_memory_GiB=4,declared_memory_ceiling_GiB=8,
                            work_seconds=600,exit_seconds=60))
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2,allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=proof['status'],host=args.host,scorer_wall_seconds=proof['scorer_wall_seconds'])),flush=True)


if __name__=='__main__':
    main()
