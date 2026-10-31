"""GPU-hidden actual loaded endpoint runner and prospective binding validation."""
import argparse
import faulthandler
import hashlib
import json
import os
import signal
import sys
import time
import unittest
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert args.host == 'two_card' and os.sched_getaffinity(0) == {26}
    signal.alarm(1200)
    started, cpu_started = time.time(), time.process_time()
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration = json.loads((args.stage/'registration.json').read_text())
    assert registration['host']==args.host
    assert all(sha(args.stage/name)==expected for name,expected in registration['payload_sha256'].items())
    assert all(sha(args.runtime/name)==expected for name,expected in registration['runtime_source_sha256'].items())
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
                      HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TORCHINDUCTOR_COMPILE_THREADS='1')
    sys.path[:0] = [str(args.stage/'src'),str(args.stage/'scripts'),str(args.stage/'tests'),
                   str(args.runtime),str(args.runtime/'packages/cosmos-oss'),str(args.runtime/'packages/cosmos-cuda')]
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()

    def forbidden(*positional,**keywords):
        raise RuntimeError('Fast CPU binding check forbids CUDA, model weights and downloads')

    torch.cuda._lazy_init=forbidden
    torch.load=forbidden
    torch.hub.download_url_to_file=forbidden
    import triton
    class Driver:
        def get_benchmarker(self):
            return forbidden
        def __getattr__(self,name):
            raise RuntimeError('CPU binding check forbids Triton: '+name)
    triton.runtime.driver.active=Driver()
    import transformers.utils as transformers_utils
    from transformers.utils import import_utils
    saved=(transformers_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    transformers_utils.is_flash_attn_2_available=lambda:True
    import_utils.is_flash_attn_2_available=lambda:True
    torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import InferenceArguments
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:
        transformers_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=saved
    import test_cara_s_endpoint_runner_binding_r1
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_s_endpoint_runner_binding_r1))
    assert tests.wasSuccessful() and tests.testsRun==14 and not tests.skipped
    from wcomr.cara_fast_binding_r2 import load_card
    card=load_card(args.stage,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    samples={r['name']:InferenceArguments.model_validate({**{k:v for k,v in r.items() if k!='partition'},'resolution':'16,16'})
             for r in card['inputs']}
    import check_cara_s_endpoint_runner_routes_r1
    numeric=check_cara_s_endpoint_runner_routes_r1.run(args.runtime,args.stage/'CPU-endpoint',args.host,samples)
    checks=numeric['checks']
    assert len(checks)==2 and {r['flow'] for r in checks}=={False,True}
    assert sum(r['actual_complete_paths'] for r in checks)==114
    assert all(len(r['cases'])==2 and len(r['failure_controls'])==4 for r in checks)
    from torch._inductor import async_compile
    assert async_compile.get_compile_threads()==1 and not async_compile._pool_set
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(5,repeat=True)
    from loguru import logger
    logger.complete()
    logger.remove()
    proof=dict(status='ENDPOINT_LOADED_RUNNER_TINY_CPU_COMPLETE_NOT_WHOLE_GPU_CARD',
        host=args.host,started_unix=started,ended_unix=time.time(),CPU_process_seconds=time.process_time()-cpu_started,
        registration_sha256=sha(args.stage/'registration.json'),source_revision=registration['parent_git_revision'],
        numeric=numeric,actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
        payload_sha256=registration['payload_sha256'],runtime_source_sha256=registration['runtime_source_sha256'],
        actual_compile_threads=1,compile_pools=[],CUDA_initialized=False,Cosmos_model_weights_loaded=False,
        production_paths=114,failure_controls=8,complete_cases=4,metadata_controls=14,
        whole_GPU_entry_executed=False,actual_GPU_context=False,actual_Cosmos_model_load=False,
        work_seconds=1200,exit_seconds=60,
        actual_original_budget_outputs_read=False,actual_budget_policy_bound=False,
        actual_historical_RGB_accepted=False,whole_GPU_card_accepted=False,GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)


if __name__=='__main__':
    main()
