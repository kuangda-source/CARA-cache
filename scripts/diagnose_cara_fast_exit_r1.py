"""Bound import/exit discriminator; no numerical matrix, weights or scoring."""
import argparse
import faulthandler
import hashlib
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert args.host == 'four_card' and not args.output.exists()
    signal.alarm(300)
    started = time.time()
    cpu_started = time.process_time()
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration = json.loads((args.stage / 'registration.json').read_text())
    mode = json.loads((args.stage / 'exit-mode.json').read_text())['mode']
    assert mode in ('default', 'single')
    assert all(sha(args.stage / name) == expected
               for name, expected in registration['payload_sha256'].items())
    assert all(sha(args.runtime / name) == expected
               for name, expected in registration['runtime_source_sha256'].items())
    os.environ.update(CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void',
                      HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    if mode == 'single':
        os.environ['TORCHINDUCTOR_COMPILE_THREADS'] = '1'
    else:
        os.environ.pop('TORCHINDUCTOR_COMPILE_THREADS', None)
    sys.path[:0] = [str(args.runtime), str(args.runtime / 'packages/cosmos-oss'),
                   str(args.runtime / 'packages/cosmos-cuda')]
    progress = dict(mode=mode, phase='RUNTIME_IMPORT', started_unix=started,
                    pid=os.getpid(), GPU_submissions=0)
    (args.stage / 'progress.json').write_text(json.dumps(progress, indent=2) + '\n')
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)

    def forbidden(*positional, **keywords):
        raise RuntimeError('Exit diagnostic forbids CUDA, weights and downloads')

    torch.cuda._lazy_init = forbidden
    torch.load = forbidden
    torch.hub.download_url_to_file = forbidden
    import triton

    class Driver:
        def get_benchmarker(self):
            return forbidden

        def __getattr__(self, name):
            raise RuntimeError('Exit diagnostic forbids Triton execution: ' + name)

    triton.runtime.driver.active = Driver()
    import transformers.utils as transformers_utils
    from transformers.utils import import_utils
    saved = (transformers_utils.is_flash_attn_2_available,
             import_utils.is_flash_attn_2_available, torch.cuda.current_device)
    transformers_utils.is_flash_attn_2_available = lambda: True
    import_utils.is_flash_attn_2_available = lambda: True
    torch.cuda.current_device = lambda: 0
    try:
        from cosmos_predict2.config import InferenceArguments
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:
        (transformers_utils.is_flash_attn_2_available,
         import_utils.is_flash_attn_2_available, torch.cuda.current_device) = saved
    from torch._inductor import async_compile
    pools = []
    for pool in async_compile._pool_set:
        process = getattr(pool, 'process', None)
        pools.append(dict(type=type(pool).__name__, pid=getattr(process, 'pid', None)))
    progress.update(phase='EXPLICIT_LOG_CLEANUP', imported_unix=time.time(),
                    actual_compile_threads=async_compile.get_compile_threads(),
                    compile_pools=pools, threads=[t.name for t in threading.enumerate()])
    (args.stage / 'progress.json').write_text(json.dumps(progress, indent=2) + '\n')
    # Capture the actual Python exit wait, rather than inferring it from code142.
    faulthandler.enable()
    faulthandler.dump_traceback_later(3, repeat=True)
    signal.alarm(20)
    from loguru import logger
    logger.complete()
    logger.remove()
    assert not torch.cuda.is_initialized()
    proof = dict(status='EXIT_DIAGNOSTIC_BODY_COMPLETE_NOT_TERMINAL_ACCEPTANCE',
                 host=args.host, mode=mode, started_unix=started, ended_unix=time.time(),
                 CPU_process_seconds=time.process_time()-cpu_started,
                 actual_compile_threads=async_compile.get_compile_threads(),
                 compile_pools=pools, threads_before_exit=[t.name for t in threading.enumerate()],
                 CUDA_initialized=False, model_weights_loaded=False, numerical_paths=0,
                 old_videos_scored=0, GPU_submissions=0, ledger_written=False,
                 registration_sha256=sha(args.stage/'registration.json'),
                 runtime_source_sha256=registration['runtime_source_sha256'],
                 payload_sha256=registration['payload_sha256'],
                 resource_bound=dict(cpus=1, memory_GiB=4, import_seconds=300, exit_seconds=20))
    with args.output.open('x') as handle:
        json.dump(proof, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=proof['status'], mode=mode,
                          compile_threads=proof['actual_compile_threads'],
                          compile_pools=pools)), flush=True)


if __name__ == '__main__':
    main()
