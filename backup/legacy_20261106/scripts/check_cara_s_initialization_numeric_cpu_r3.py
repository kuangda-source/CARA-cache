"""GPU-hidden affected audit-routing checks under bounded compiler resources."""
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
    from wcomr.cara_fast_binding_r2 import load_card
    contract_path=args.stage/'plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_NUMERIC_CPU_R3_20261031.json'
    contract=json.loads(contract_path.read_text())
    assert args.stage.name == contract['stage_name']
    assert sha(args.stage/contract['selector_contract_ref']) == contract['selector_contract_sha256']
    card=load_card(args.stage,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    samples={r['name']:InferenceArguments.model_validate({**{k:v for k,v in r.items() if k!='partition'},'resolution':'16,16'})
             for r in card['inputs']}
    import check_cara_s_initialization_numeric_routes_r3
    numeric=check_cara_s_initialization_numeric_routes_r3.run(args.runtime,args.stage/'CPU-numeric',args.host,samples)
    checks=numeric['checks']
    assert len(checks)==2 and {r['flow'] for r in checks}=={False,True}
    assert sum(r['production_paths'] for r in checks)==contract['expected_production_paths']==36
    assert sum(r['old_fixed_paths'] for r in checks)==contract['expected_old_fixed_paths']==12
    assert sum(len(r['failures']) for r in checks)==contract['expected_failures']==18
    from torch._inductor import async_compile
    assert async_compile.get_compile_threads()==1 and not async_compile._pool_set
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(5,repeat=True)
    from loguru import logger
    logger.complete()
    logger.remove()
    proof=dict(status='UNIFORM_INITIALIZATION_TINY_PAIRED_NUMERIC_CPU_COMPLETE_NOT_ENDPOINT',
        host=args.host,started_unix=started,ended_unix=time.time(),CPU_process_seconds=time.process_time()-cpu_started,
        registration_sha256=sha(args.stage/'registration.json'),source_revision=registration['parent_git_revision'],
        contract_sha256=sha(contract_path),numeric=numeric,actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
        payload_sha256=registration['payload_sha256'],runtime_source_sha256=registration['runtime_source_sha256'],
        actual_compile_threads=1,compile_pools=[],CUDA_initialized=False,Cosmos_model_weights_loaded=False,
        production_paths=36,old_fixed_paths=12,ordinary_pairs=1728,CFG_calls=3456,
        failure_controls=18,work_seconds=1200,exit_seconds=60,
        original_S_freeze_changed=False,free_running_or_endpoint_acceptance=False,
        whole_GPU_card_accepted=False,GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)


if __name__=='__main__':
    main()
