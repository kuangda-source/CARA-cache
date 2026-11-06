"""Bounded actual-Linux scalar collection and fixed-estimation CPU controls."""
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
    parser = argparse.ArgumentParser()
    for name in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert args.host == 'two_card' and os.sched_getaffinity(0) == {26} and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    started = time.time()
    signal.alarm(600)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    registration = json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/n) == h for n, h in registration['payload_sha256'].items())
    assert all(sha(args.runtime/n) == h for n, h in registration['runtime_source_sha256'].items())
    sys.path[:0] = [str(args.stage/'tests'), str(args.stage/'src'), str(args.stage/'scripts'),
                   str(args.runtime), str(args.runtime/'packages/cosmos-oss'),
                   str(args.runtime/'packages/cosmos-cuda')]
    os.environ.update(CARA_READ_WRITE_RUNTIME=str(args.runtime), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()

    def forbidden(*args, **kwargs):
        raise RuntimeError('Scalar CPU check forbids CUDA, pretrained weights and downloads')

    torch.cuda._lazy_init = forbidden
    torch.load = forbidden
    torch.hub.download_url_to_file = forbidden
    import triton

    class Driver:
        def get_benchmarker(self):
            return forbidden

        def __getattr__(self, name):
            raise RuntimeError('Scalar CPU check forbids Triton: '+name)

    triton.runtime.driver.active = Driver()
    import transformers.utils as utils
    from transformers.utils import import_utils
    saved = utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available, torch.cuda.current_device
    utils.is_flash_attn_2_available = import_utils.is_flash_attn_2_available = lambda: True
    torch.cuda.current_device = lambda: 0
    try:
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:
        utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available, torch.cuda.current_device = saved
    assert wc.worldcache_mini_train_dit_forward.__globals__ is vars(wc)
    assert rf.Video2WorldModelRectifiedFlow.denoise.__globals__ is vars(rf)
    estimation = importlib.import_module('test_cara_source_lifecycle_estimation_r1')
    tested = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(estimation))
    assert tested.testsRun == 11 and tested.wasSuccessful() and not tested.skipped
    scalar_math = importlib.import_module('test_cara_source_lifecycle_scalar_math_r1')
    math_tests = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(scalar_math))
    assert math_tests.testsRun == 2 and math_tests.wasSuccessful() and not math_tests.skipped
    import check_cara_source_lifecycle_scalar_cpu_r1 as collection
    assert Path(collection.__file__).resolve() == (args.stage/'tests/check_cara_source_lifecycle_scalar_cpu_r1.py').resolve()
    result = collection.run(args.runtime, args.stage/'CPU-scalar-requests', actual_modules=True)
    assert result['status'] == 'PINNED_PIPELINE_CPU_FIXTURE_EXTERNAL_EXERCISE_COMPLETE'
    assert len(result['checks']) == 2 and sum(r['complete_requests'] for r in result['checks']) == 32
    assert sum(r['scalar_rows'] for r in result['checks']) == 128
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(8, repeat=True)
    from loguru import logger
    logger.complete()
    logger.remove()
    receipt = dict(status='SOURCE_SCALAR_ACTUAL_LINUX_CPU_PASS_NOT_REAL_MODEL_METHOD',
                   source_revision=registration['parent_git_revision'],
                   started_unix=started, ended_unix=time.time(), host='two_card', actual_CPU_affinity=[26],
                   registration_sha256=sha(args.stage/'registration.json'),
                   payload_sha256=registration['payload_sha256'],
                   runtime_source_sha256=registration['runtime_source_sha256'],
                   tests_run=13, fixed_estimation_tests=11, original_CFG_pair_tests=2,
                   estimation_metrics=estimation.METRICS,
                   collection=result, complete_tiny_requests=32, synthetic_scalar_rows=128,
                   actual_WC_RF_imports_and_globals_accepted=True, CPU_import_adapters_used=True,
                   torch_version=torch.__version__, actual_Cosmos_weights=False,
                   real_source_labels_fitted=False, real_generated_plan_efficacy=False,
                   CUDA_initialized=False, GPU_submissions=0, ledger_written=False)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=receipt['status'], wall_seconds=time.time()-started)))


if __name__ == '__main__':
    main()
