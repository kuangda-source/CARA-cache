"""One bounded loaded-P1 algorithm/internal-score Linux CPU preparation run."""
import argparse
import faulthandler
import importlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest


def main(*, work_seconds=1800):
    parser = argparse.ArgumentParser()
    for name in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert args.host == 'two_card' and os.sched_getaffinity(0) == {26} and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    started = time.time()
    signal.alarm(work_seconds)
    os.environ['CARA_V1_P1_CPU_DEADLINE_MONOTONIC'] = str(time.monotonic()+work_seconds-120)
    reg = json.loads((args.stage/'registration.json').read_bytes())
    import hashlib
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert all(sha(args.stage/n) == h for n, h in reg['payload_sha256'].items())
    assert all(sha(args.runtime/n) == h for n, h in reg['runtime_source_sha256'].items())
    sys.path[:0] = [str(args.stage/'tests'), str(args.stage/'src'), str(args.stage/'scripts'),
                   str(args.runtime), str(args.runtime/'packages/cosmos-oss'),
                   str(args.runtime/'packages/cosmos-cuda')]
    scratch = args.stage/'CPU-P1-scratch'
    scratch.mkdir()
    tempfile.tempdir = str(scratch)
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CARA_READ_WRITE_RUNTIME=str(args.runtime))
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()

    def forbidden(*args, **kwargs):
        raise RuntimeError('P1 CPU preparation forbids CUDA, generative weights and downloads')

    load = torch.load
    def fixture_load(path, *args, **kwargs):
        assert Path(path).resolve().is_relative_to(scratch.resolve())
        return load(path, *args, **kwargs)

    torch.load = fixture_load
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    modules = [importlib.import_module(name) for name in (
        'test_cara_source_lifecycle_estimation_r1', 'test_cara_source_lifecycle_search_r1',
        'test_cara_source_lifecycle_fit_scores_r1', 'test_cara_source_lifecycle_p1_collection_r1',
        'test_cara_source_lifecycle_p1_clock_r1')]
    tested = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules))
    assert tested.testsRun == 33 and tested.wasSuccessful() and not tested.skipped
    import triton
    class Driver:
        def get_benchmarker(self):
            return forbidden
        def __getattr__(self, name):
            raise RuntimeError('P1 CPU preparation forbids Triton: '+name)
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
    import check_cara_source_lifecycle_p1_loaded_cpu_r1 as loaded
    result = loaded.run(args.runtime, scratch/'loaded')
    assert len(result['checks']) == 2
    assert all(r['semantic_positions'] == 146 and r['source_scalar_rows'] == 64 for r in result['checks'])
    assert all(r['recovery_new_physical_and_score_callbacks'] == 0 for r in result['checks'])
    assert all(r['caller_forward_binding_restored_on_success_recovery_and_failure'] for r in result['checks'])
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(8, repeat=True)
    from loguru import logger
    logger.complete()
    logger.remove()
    proof = dict(status='P1_LOADED_ALGORITHM_INTERNAL_FIT_LINUX_CPU_PASS_NOT_WHOLE_GPU_ENTRY',
        source_revision=reg['parent_git_revision'], started_unix=started, ended_unix=time.time(),
        host='two_card', actual_CPU_affinity=[26], registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=reg['payload_sha256'], runtime_source_sha256=reg['runtime_source_sha256'],
        tests_run=33, loaded=result, complete_semantic_positions=292, same_state_scalar_rows=128,
        actual_complete_loaded_tiny_requests=sum(r['actual_complete_tiny_requests'] for r in result['checks']),
        real93_frame_synthetic_metric_pairs=sum(r['actual93_frame_metric_pairs'] for r in result['checks']),
        actual_WC_RF_imports_and_globals_accepted=True, actual_Cosmos_arguments=True,
        CPU_import_adapters_used=True, synthetic_cost_ticks_not_GPU_quote=True,
        actual_Cosmos_weights=False, real_V1_labels=False, real_video_efficacy=False,
        whole_GPU_entry_accepted=False, P1_GPU_authorized=False, CUDA_initialized=False,
        work_seconds=work_seconds, exit_seconds=60, GPU_submissions=0, ledger_written=False)
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=proof['status'], wall_seconds=time.time()-started)), flush=True)


if __name__ == '__main__':
    main()
