"""Bound production CPU and real-Alex small-data controls; never old bulk scoring."""
import argparse
import hashlib
import json
import os
import signal
import sys
import time
import unittest
from pathlib import Path


def closing_guard():
    # Scientific checks retain their original 900s bound. Draining imported
    # process logging and Python atexit has a separate, bounded 30s allowance.
    signal.alarm(30)
    from loguru import logger
    logger.complete()
    logger.remove()


def scoring_controls(stage, host):
    import torch
    import numpy as np
    import av
    score_root=stage.parent/('wc-time-score-CPU-'+host+'-r1-20261027')
    sys.path.insert(0,str(score_root/'site'));os.environ['TORCH_HOME']=str(score_root/'torch')
    import lpips
    import piq
    from wcomr.cara_fast_fidelity_r1 import Fidelity,score_video_pair,file_sha
    checkpoint=score_root/'torch/hub/checkpoints/alexnet-owt-7be5be79.pth'
    assert file_sha(checkpoint)=='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
    linear=Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
    assert file_sha(linear)=='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
    alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
    x=torch.linspace(.1,.7,3*64*64).reshape(1,3,64,64)
    same=Fidelity(alex,expected_frames=3);offset=Fidelity(alex,expected_frames=3)
    variable=Fidelity(alex,expected_frames=3);permute=Fidelity(alex,expected_frames=3)
    reference=[x,x.flip(-1),x.flip(-2)]
    for i,n in enumerate(reference):
        same.add(n,n);offset.add(n+.1,n);variable.add(n+[0.,.1,.2][i],n);permute.add(reference[2-i],n)
    a,b,c,d=[m.finish() for m in (same,offset,variable,permute)]
    assert a['PSNR_video_dB']=='+inf' and a['Alex']==0 and abs(a['SSIM']-1)<1e-6
    assert a['reference_temporal_L1']==0 and a['reference_gradient_L1']==0
    assert abs(b['PSNR_video_dB']-20)<1e-4 and b['reference_temporal_L1']<1e-7
    assert b['reference_gradient_L1']<1e-7 and abs(c['MSE_video']-(.01+.04)/3)<1e-7
    assert d['reference_temporal_L1']>0
    # Frozen spatial SSIM agrees with explicit per-frame PIQ calls.
    direct=float(piq.ssim(reference[0],reference[0],kernel_size=11,kernel_sigma=1.5,data_range=1.,
                         reduction='none',full=False,k1=.01,k2=.03,downsample=False))
    assert abs(direct-a['SSIM_frames'][0])<1e-7
    flat=Fidelity(alex,expected_frames=1);flat.add(torch.zeros_like(x),torch.zeros_like(x))
    assert flat.finish()['gradient_ratio_status']=='ZERO_REFERENCE_ENERGY'
    rejected=[]
    for label,bad in [('NaN',x*float('nan')),('range',x+2),('shape',x[:,:,:32,:])]:
        try:Fidelity(alex,expected_frames=1).add(bad,x)
        except ValueError:rejected.append(label)
        else:raise AssertionError('Invalid frame accepted')
    # One native-resolution frame measures affected scoring cost, not video quality.
    large=torch.linspace(.1,.7,3*432*768).reshape(1,3,432,768)
    start=time.perf_counter();full=Fidelity(alex,expected_frames=1);full.add(large.flip(-1),large);full.finish()
    full_frame_seconds=time.perf_counter()-start
    video=stage/'CPU-fixture.avi'
    with av.open(str(video),'w') as out:
        stream=out.add_stream('ffv1',rate=16);stream.width=64;stream.height=64;stream.pix_fmt='bgr0'
        for n in reference:
            arr=(n[0].permute(1,2,0).numpy()*255).round().astype(np.uint8)
            for packet in stream.encode(av.VideoFrame.from_ndarray(arr,format='rgb24')):out.mux(packet)
        for packet in stream.encode():out.mux(packet)
    descriptor=dict(path=str(video),sha256=file_sha(video))
    decoded=score_video_pair(descriptor,descriptor,alex,expected_shape=(3,64,64,3))
    assert decoded['frames']==3 and decoded['Alex']==0 and decoded['PSNR_is_infinite']
    for label,desc,shape in [('SHA',dict(descriptor,sha256='0'*64),(3,64,64,3)),
                            ('denominator',descriptor,(4,64,64,3)),('geometry',descriptor,(3,32,64,3))]:
        try:score_video_pair(desc,descriptor,alex,expected_shape=shape)
        except ValueError:rejected.append(label)
        else:raise AssertionError('Corrupt video registration accepted')
    assert not torch.cuda.is_initialized()
    return dict(status='SYNTHETIC_FIDELITY_AND_REAL_ALEX_CPU_CONTROLS_PASS',
                package_versions=dict(torch=torch.__version__,piq=piq.__version__,lpips='0.1.4',av=av.__version__),
                checkpoint_sha256=file_sha(checkpoint),linear_sha256=file_sha(linear),
                identical_inf_and_zero=True,video_MSE_before_dB=True,constant_error_temporal_zero=True,
                SSIM_explicit_PIQ_parity=True,zero_gradient_denominator_preserved=True,
                decoded_all_frame_roundtrip=True,rejected_controls=rejected,
                full_resolution_synthetic_frames=1,full_resolution_frame_wall_seconds=full_frame_seconds,
                scientific_quality_result=False,old_videos_scored=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--host',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();signal.alarm(900);start=time.time();cpu_start=time.process_time()
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    reg=json.loads((a.stage/'registration.json').read_text())
    assert reg['host']==a.host and all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(sha(a.runtime/n)==h for n,h in reg['runtime_source_sha256'].items())
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests'),str(a.runtime),
                  str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized();original_load=torch.load
    def forbidden(*a,**k):raise RuntimeError('CPU proof forbids CUDA/Cosmos weights/downloads')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,n):raise RuntimeError('CPU refuses Triton: '+n)
    triton.runtime.driver.active=Driver()
    import transformers.utils as hu
    from transformers.utils import import_utils as iu
    saved=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
    hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import InferenceArguments
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
    card=json.loads((a.stage/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())
    samples={r['name']:InferenceArguments.model_validate({**{k:v for k,v in r.items() if k!='partition'},'resolution':'16,16'}) for r in card['inputs']}
    import test_cara_fast_spec_r1
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_fast_spec_r1))
    assert tests.wasSuccessful()
    import check_cara_fast_production_cpu_r1
    numeric=check_cara_fast_production_cpu_r1.run(a.runtime,a.stage/'CPU-numeric',a.host,samples)
    torch.load=original_load
    score=scoring_controls(a.stage,a.host)
    assert not torch.cuda.is_initialized()
    closing_guard()
    proof=dict(status='FAST_AFFECTED_PRODUCTION_AND_FIDELITY_CPU_PASS_NOT_GPU',host=a.host,
               started_unix=start,ended_unix=time.time(),CPU_process_seconds=time.process_time()-cpu_start,
               registration_sha256=sha(a.stage/'registration.json'),scope_sha256=card['scope_sha256'],
               payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
               spec_tests=tests.testsRun,numeric=numeric,fidelity=score,CUDA_initialized=False,
               Cosmos_model_weights_loaded=False,GPU_submissions=0,ledger_written=False,
               whole_GPU_card_accepted=False)
    with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=proof['status'],host=a.host,wall_seconds=time.time()-start)))


if __name__=='__main__':main()
