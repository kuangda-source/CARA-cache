"""Bounded original-module verification of the complete read/write fourteen-request collector."""
import argparse
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time


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
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg = json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/p) == s for p, s in reg['payload_sha256'].items())
    assert all(sha(args.runtime/p) == s for p, s in reg['runtime_source_sha256'].items())
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TORCHINDUCTOR_COMPILE_THREADS='1',
                      CARA_READ_WRITE_RUNTIME=str(args.runtime))
    sys.path[:0] = [str(args.stage/'src'), str(args.stage/'scripts'), str(args.stage/'tests'),
                   str(args.runtime), str(args.runtime/'packages/cosmos-oss'), str(args.runtime/'packages/cosmos-cuda')]
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()
    def forbidden(*args, **kwargs):
        raise RuntimeError('Read/write CPU check forbids CUDA, real weights and downloads')
    torch.cuda._lazy_init = forbidden
    torch.load = forbidden
    torch.hub.download_url_to_file = forbidden
    import triton
    class Driver:
        def get_benchmarker(self):
            return forbidden
        def __getattr__(self, name):
            raise RuntimeError('Read/write CPU check forbids Triton: '+name)
    triton.runtime.driver.active = Driver()
    import transformers.utils as transformers_utils
    from transformers.utils import import_utils
    saved = (transformers_utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available,
             torch.cuda.current_device)
    transformers_utils.is_flash_attn_2_available = lambda: True
    import_utils.is_flash_attn_2_available = lambda: True
    torch.cuda.current_device = lambda: 0
    try:
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:
        (transformers_utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available,
         torch.cuda.current_device) = saved
    assert wc.worldcache_mini_train_dit_forward.__globals__ is vars(wc)
    assert rf.Video2WorldModelRectifiedFlow.denoise.__globals__ is vars(rf)
    import check_cara_read_write_collection_cpu_r1 as collection
    complete = collection.run(args.runtime, args.stage/'CPU-full14', actual_modules=True)
    assert len(complete['checks']) == 2
    assert sum(r['complete_paths'] for r in complete['checks']) == 28
    assert all(r['physical_model_pairs'] == 512 and r['actual_Cosmos_argument_class']
               for r in complete['checks'])
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(8, repeat=True)
    from loguru import logger
    logger.complete()
    logger.remove()
    proof = dict(status='READ_WRITE_FULL14_ACTUAL_LINUX_CPU_PASS_NOT_GPU',
        host=args.host, started_unix=started, ended_unix=time.time(), actual_CPU_affinity=[26],
        source_revision=reg['parent_git_revision'], registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=reg['payload_sha256'], runtime_source_sha256=reg['runtime_source_sha256'],
        collection=complete, complete_guarded_tiny_requests=28,
        per_matrix=dict(requests=14, scientific_outputs=8, logical_solver_updates=504,
                        physical_model_pairs=512, physical_CFG_calls=1024),
        actual_WC_RF_imports_and_globals_accepted=True, actual_Cosmos_argument_class=True,
        CUDA_initialized=False, actual_Cosmos_weights=False, real_encoded_video=False,
        actual_model_VJP=False, GPU_submissions=0, ledger_written=False,
        whole_GPU_card_accepted=False, work_seconds=600, exit_seconds=60)
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=proof['status'], wall_seconds=time.time()-started)))


if __name__ == '__main__':
    main()
