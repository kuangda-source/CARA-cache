"""Bounded Linux acceptance of the distinct P0 point20 complete entry and scorer."""
import argparse
import faulthandler
import hashlib
import importlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest


def main():
    parser = argparse.ArgumentParser()
    for key in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert args.host == 'two_card' and os.sched_getaffinity(0) == {26} and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    signal.alarm(600)
    started = time.time()
    sha = lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg = json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/p) == h for p,h in reg['payload_sha256'].items())
    assert all(sha(args.runtime/p) == h for p,h in reg['runtime_source_sha256'].items())
    sys.path[:0] = [str(args.stage/'src'), str(args.stage/'scripts'), str(args.stage/'tests'),
        str(args.runtime), str(args.runtime/'packages/cosmos-oss'), str(args.runtime/'packages/cosmos-cuda')]
    scratch = args.stage/'CPU-scratch'
    scratch.mkdir(exist_ok=False)
    tempfile.tempdir = str(scratch)
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TORCHINDUCTOR_COMPILE_THREADS='1')
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()

    def forbidden(*positional, **keywords):
        raise RuntimeError('M1 CPU entry check forbids CUDA, generative weights and downloads')

    original_load = torch.load

    def tiny_tensor_load(path, *positional, **keywords):
        assert Path(path).resolve().is_relative_to(scratch.resolve()), 'Only explicit synthetic tensor fixtures may load here'
        return original_load(path, *positional, **keywords)

    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.load = tiny_tensor_load
    modules = [importlib.import_module(name) for name in ('test_cara_read_write_entry_r1', 'test_cara_read_write_central_r1',
        'test_cara_read_write_postrelease_r1', 'test_cara_read_write_score_capture_r1', 'test_cara_read_write_score_dispatch_r1', 'test_cara_source_lifecycle_p0_entry_r1')]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in modules)
    tested = unittest.TextTestRunner(verbosity=2).run(suite)
    assert tested.testsRun == 77 and tested.wasSuccessful() and not tested.skipped
    import triton

    class Driver:
        def get_benchmarker(self):
            return forbidden

        def __getattr__(self, name):
            raise RuntimeError('M1 CPU check forbids Triton: '+name)

    triton.runtime.driver.active = Driver()
    import transformers.utils as utils
    from transformers.utils import import_utils
    saved = utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available, torch.cuda.current_device
    utils.is_flash_attn_2_available = import_utils.is_flash_attn_2_available = lambda:True
    torch.cuda.current_device = lambda:0
    try:
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:
        utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available, torch.cuda.current_device = saved
    assert wc.worldcache_mini_train_dit_forward.__globals__ is vars(wc)
    assert rf.Video2WorldModelRectifiedFlow.denoise.__globals__ is vars(rf)
    import check_cara_read_write_loaded_cpu_r1 as loaded
    complete = loaded.run(args.runtime, args.stage/'CPU-loaded', actual_modules=True, target_update=20)
    assert sum(r['complete_paths'] for r in complete['checks']) == 28
    import check_cara_read_write_score_cli_r1 as scorer
    from wcomr.cara_read_write_identity_r1 import P0
    metric = scorer.run(scratch/'CPU-scoring', args.stage, deadline=time.monotonic()+300, identity=P0)
    assert metric['complete_pairs'] == 8 and metric['latent_RGB_controls'] == 4
    assert metric['target_update'] == 20 and metric['cross_point_Native_controls'] == 2
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(8, repeat=True)
    from loguru import logger
    logger.complete()
    logger.remove()
    proof = dict(status='SOURCE_LIFECYCLE_P0_POINT20_FULL_ENTRY_LINUX_CPU_PASS_NOT_GPU', target_update=20, run_id=P0.run_id, host=args.host,
        started_unix=started, ended_unix=time.time(), actual_CPU_affinity=[26], source_revision=reg['parent_git_revision'],
        registration_sha256=sha(args.stage/'registration.json'), payload_sha256=reg['payload_sha256'],
        runtime_source_sha256=reg['runtime_source_sha256'], tests_run=tested.testsRun,
        complete_loaded_tiny_requests=28, loaded=complete, scorer=metric,
        actual_WC_RF_module_globals=True, actual_Cosmos_arguments=True, generative_model_weights_loaded=False,
        actual_GPU_resources_or_storage_provisioned=False, actual_central_ledger_accessed=False,
        original_experiments_replayed=False, CUDA_initialized=False,
        whole_GPU_card_accepted=False, GPU_submissions=0, ledger_written=False, work_seconds=600, exit_seconds=60)
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=proof['status'], wall_seconds=time.time()-started)), flush=True)


if __name__ == '__main__':
    main()
