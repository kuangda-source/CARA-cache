"""Actual-Linux V1 source chart/DP and complete tiny point8/20 request checks."""
import argparse
import faulthandler
import hashlib
import importlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime','stage','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True)
    args=parser.parse_args()
    assert args.host=='two_card' and os.sched_getaffinity(0)=={26} and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    signal.alarm(600);started=time.time()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg=json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/p)==h for p,h in reg['payload_sha256'].items())
    assert all(sha(args.runtime/p)==h for p,h in reg['runtime_source_sha256'].items())
    # The test fixture and old CLI share a basename; select the fixture directory
    # explicitly, then bind imported WC/RF namespaces to the actual Linux files.
    sys.path[:0]=[str(args.stage/'tests'),str(args.stage/'src'),str(args.stage/'scripts'),
        str(args.runtime),str(args.runtime/'packages/cosmos-oss'),str(args.runtime/'packages/cosmos-cuda')]
    os.environ.update(CARA_READ_WRITE_RUNTIME=str(args.runtime),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()
    def forbidden(*args,**kwargs):
        raise RuntimeError('V1 CPU check forbids CUDA, pretrained-model weights and downloads')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('V1 CPU check forbids Triton: '+name)
    triton.runtime.driver.active=Driver()
    import transformers.utils as utils
    from transformers.utils import import_utils
    saved=utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device
    utils.is_flash_attn_2_available=import_utils.is_flash_attn_2_available=lambda:True
    torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:
        utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=saved
    assert wc.worldcache_mini_train_dit_forward.__globals__ is vars(wc)
    assert rf.Video2WorldModelRectifiedFlow.denoise.__globals__ is vars(rf)
    import test_cara_read_write_transition_r1 as fixture
    fixture.modules=lambda:(wc,rf);fixture.DataType=wc.DataType
    modules=[importlib.import_module(name) for name in ('test_cara_read_write_provenance_r1',
        'test_cara_source_lifecycle_planner_r1','test_cara_source_lifecycle_design_r1')]
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in modules)
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    assert tested.wasSuccessful() and tested.testsRun==15 and not tested.skipped
    import check_cara_read_write_point_cpu_r1 as point
    assert Path(point.__file__).resolve()==(args.stage/'tests/check_cara_read_write_point_cpu_r1.py').resolve()
    points=[]
    for target in (8,20):
        result=point.run(args.runtime,args.stage/('CPU-point'+str(target)),actual_modules=True,target_update=target)
        assert result['status']=='PINNED_PIPELINE_CPU_FIXTURE_EXTERNAL_EXERCISE_COMPLETE'
        assert sum(r['complete_paths'] for r in result['checks'])==12
        assert all(r['target_update']==target for r in result['checks'])
        points.append(result)
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable();faulthandler.dump_traceback_later(8,repeat=True)
    from loguru import logger
    logger.complete();logger.remove()
    receipt=dict(status='SOURCE_LIFECYCLE_V1_ACTUAL_LINUX_CPU_PASS_NOT_VIDEO_METHOD',
        host=args.host,started_unix=started,ended_unix=time.time(),actual_CPU_affinity=[26],
        source_revision=reg['parent_git_revision'],registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
        tests_run=15,metrics={m.__name__:m.METRICS for m in modules},points=points,point_tiny_paths=24,
        torch_version=torch.__version__,actual_WC_RF_imports_and_globals_accepted=True,
        CPU_import_adapters_used=True,tiny_model_weights=True,actual_Cosmos_weights=False,
        actual_Cosmos_model_VJP=False,terminal_LPIPS_VJP=False,complete_augmented_adjoint=False,
        real_source_labels_fitted=False,real_generated_plan_efficacy=False,CUDA_initialized=False,
        GPU_submissions=0,ledger_written=False,work_seconds=600,exit_seconds=60)
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=receipt['status'],wall_seconds=time.time()-started)))


if __name__=='__main__':main()
