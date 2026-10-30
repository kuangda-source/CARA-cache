"""GPU-hidden complete calibration plus current execution and Linux child controls."""
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
    signal.alarm(2400)
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
    card=json.loads((args.stage/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_RUN_SPEC_R1.json').read_text())
    samples={r['name']:InferenceArguments.model_validate({**{k:v for k,v in r.items() if k!='partition'},'resolution':'16,16'})
             for r in card['inputs']}
    import test_cara_fast_binding_r2
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_fast_binding_r2))
    assert tests.wasSuccessful()
    module_names=(
        'test_cara_budget_prepare_r1','test_cara_budget_central_r1',
        'test_cara_budget_dispatch_r1','test_cara_budget_runner_binding_r1',
        'test_cara_budget_lifecycle_r1','test_cara_budget_calibration_r1',
        'test_cara_budget_storage_r1','test_cara_budget_complete_r1',
        'test_cara_budget_container_r1','test_cara_budget_guardian_journal_r1',
        'test_cara_budget_supervisor_r1','test_cara_budget_host_guardian_r1')
    control_results=[]
    for name in module_names:
        module=__import__(name)
        controls=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        assert controls.wasSuccessful() and not controls.skipped
        control_results.append(dict(module=name,tests_run=controls.testsRun,
            errors=len(controls.errors),failures=len(controls.failures),skipped=len(controls.skipped),
            Linux_observations=getattr(module,'OBSERVATIONS',[]),
            Linux_diagnostics=getattr(module,'DIAGNOSTICS',[])))
    assert sum(r['tests_run'] for r in control_results)==134
    import check_cara_budget_calibration_routes_r3
    numeric=check_cara_budget_calibration_routes_r3.run(args.runtime,args.stage/'CPU-numeric',args.host,samples)
    from torch._inductor import async_compile
    assert async_compile.get_compile_threads()==1 and not async_compile._pool_set
    assert not torch.cuda.is_initialized()
    signal.alarm(60)
    faulthandler.enable()
    faulthandler.dump_traceback_later(5,repeat=True)
    from loguru import logger
    logger.complete()
    logger.remove()
    proof=dict(status='CURRENT_COMPLETE_CALIBRATION_AND_EXECUTION_CONTROLS_CPU_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),CPU_process_seconds=time.process_time()-cpu_started,
        registration_sha256=sha(args.stage/'registration.json'),scope_sha256=card['scope_sha256'],
        spec_tests=tests.testsRun,execution_control_tests=sum(r['tests_run'] for r in control_results),control_results=control_results,numeric=numeric,payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],
        actual_compile_threads=1,compile_pools=[],CUDA_initialized=False,
        Cosmos_model_weights_loaded=False,GPU_submissions=0,ledger_written=False,
        resource_bound=dict(cpus=1,memory_GiB=4,work_seconds=2400,exit_seconds=60),
        real_Docker_GPU_lifecycle_exercised=False,
        real_64GiB_storage_exercised=False,
        dispatch_child_spawn_simulated=True,
        whole_GPU_card_accepted=False)
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2,allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=proof['status'],host=args.host,wall_seconds=time.time()-started)),flush=True)


if __name__=='__main__':
    main()
