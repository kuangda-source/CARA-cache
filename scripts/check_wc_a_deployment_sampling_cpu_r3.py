#!/usr/bin/env python3
"""Execute the complete three-method guarded sampler CPU fixture."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('stage', 'runtime', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.runtime),str(args.runtime/'packages/cosmos-oss'),str(args.runtime/'packages/cosmos-cuda')]
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a, **kw):
        raise RuntimeError('Paired-probe CPU fixture forbids CUDA/downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)
    import triton
    class ImportOnlyDriver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('Production CPU denies Triton execution: '+name)
    triton.runtime.driver.active=ImportOnlyDriver()
    # Same exiting-process adapters as the previously audited actual-condition
    # import checker. Installed FlashAttention metadata exists, but the HF
    # helper intentionally reports false when CUDA_VISIBLE_DEVICES is empty.
    # Restore both helpers and the unused constructor default before testing.
    import importlib.metadata
    import transformers.utils as hf_utils
    from transformers.utils import import_utils
    from packaging.version import Version
    installed=importlib.metadata.version('flash_attn')
    assert import_utils._is_package_available('flash_attn') and Version(installed)>=Version('2.1.0')
    previous=(hf_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    availability_before=bool(previous[0]())
    def metadata_only_availability():
        assert not torch.cuda.is_initialized()
        return True
    hf_utils.is_flash_attn_2_available=metadata_only_availability
    import_utils.is_flash_attn_2_available=metadata_only_availability
    torch.cuda.current_device=lambda:0
    original_tensor_load=torch.load
    torch.load=forbidden
    try:
        from cosmos_predict2._src.predict2.inference import worldcache_utils as actual_wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as actual_rf
        from cosmos_predict2._src.predict2.networks import minimal_v1_lvg_dit as actual_native
    finally:
        hf_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=previous
    assert not torch.cuda.is_initialized()
    import inspect
    native_path=args.runtime/'cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py'
    assert Path(actual_native.__file__).resolve()==native_path.resolve()
    assert Path(inspect.getsourcefile(actual_native.MinimalV1LVGDiT.forward)).resolve()==native_path.resolve()
    assert actual_native.MinimalV1LVGDiT.forward.__module__+'.'+actual_native.MinimalV1LVGDiT.forward.__qualname__=='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'
    adapter={'installed_flash_version':installed,'installed_package_present':True,
             'original_HF_availability':availability_before,'CUDA_hardware_availability_not_overridden':True,
             'original_helpers_and_current_device_restored':hf_utils.is_flash_attn_2_available is previous[0]
                 and import_utils.is_flash_attn_2_available is previous[1] and torch.cuda.current_device is previous[2],
             'weights_load_forbidden':True,'model_instantiated_by_actual_import':False,
             'GPU_runtime_adapter':False,'CUDA_initialized':False}
    reg = json.loads((args.stage / 'registration.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert {n: sha(args.stage / n) for n in reg['payload_sha256']} == reg['payload_sha256']
    assert {n: sha(args.runtime / n) for n in reg['runtime_source_sha256']} == reg['runtime_source_sha256']
    assert not args.output.exists()
    spec = importlib.util.spec_from_file_location('actual_complete_native_batch_CPU', args.stage / 'tests/check_cfg_guided_w1_deployment_sampling_cpu.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started = time.perf_counter()
    try:
        import gzip
        prior=json.loads((args.stage/reg['calibration_batch_CPU_audit_ref']).read_text())
        assert prior['exit_code']==0 and prior['full_guarded_batch_complete_scope_reconstructed']
        assert prior['actual_parent_guided_reloaded']==288 and prior['actual_child_tensors_reloaded']==96
        assert prior['GPU_submissions']==0
        calibration_cpu_result=json.loads(gzip.decompress((args.stage/reg['calibration_batch_CPU_result_ref']).read_bytes()))
        assert calibration_cpu_result['status']=='RA_CALIBRATION_SAMPLING_CPU_NOT_REAL_MODEL'
        def own_tensor_loader(path,**kwargs):
            resolved=Path(path).resolve()
            assert resolved.is_relative_to((args.stage/'CPU-artifacts').resolve()) and resolved.suffix=='.pt'
            assert kwargs=={'weights_only':True,'map_location':'cpu'}
            return original_tensor_load(resolved,**kwargs)
        result=module.run(args.runtime,own_tensor_loader,args.stage/'CPU-artifacts',calibration_cpu_result)
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps({
            'status': 'PAIRED_PROBE_CPU_FAILED_COMPLETE_SCOPE_RETAINED', 'error': str(error),
            'error_type': type(error).__name__, 'CPU_wall_seconds': time.perf_counter() - started,
            'planned_scope': reg['CPU_scope'], 'GPU_submissions': 0,
            'CUDA_initialized': torch.cuda.is_initialized()}, indent=2) + '\n')
        raise
    rows=result['checks'];assert len(rows)==4
    assert {(r['flow'],r['scenario']) for r in rows}=={(f,s) for f in (False,True) for s in ('complete','last_vector_writer_failure')}
    passed=[r for r in rows if r['status']=='PASS'];failed=[r for r in rows if r['status']=='EXPECTED_FAILURE']
    assert len(passed)==len(failed)==2
    assert all(r['actual_tensor_audit']['actual_guided_tensors_reloaded']==1008 and
        r['actual_tensor_audit']['actual_final_latents_reloaded']==28 and
        r['actual_tensor_audit']['actual_initial_7_DD_guided_direct_equal'] and
        r['actual_tensor_audit']['actual_reference_guided_reloaded']==144 and
        r['actual_tensor_audit']['actual_reference_latents_reloaded']==4 and
        r['actual_tensor_audit']['actual_reference_initial7_direct_equal'] and len(r['semantic_mutation_refusals'])==16 and r['actual_final_method_truncation_refused'] for r in passed)
    assert all(r['complete_scope_retained'] and r['initial_full_state_restored'] for r in failed)
    assert not torch.cuda.is_initialized()
    result.update(status='A_DEPLOYMENT_COMPLETE_SAMPLING_CPU_NOT_REAL_MODEL',
        CPU_wall_seconds=time.perf_counter()-started,actual_import_only_adapter=adapter,
        planned_scope=reg['CPU_scope'],payload_sha256=reg['payload_sha256'],CUDA_initialized=False,GPU_submissions=0,
        complete_successful_paths=64,complete_executed_paths_including_last_writer_failures=128,
        solver_updates=4608,net_calls=9216,actual_guided_tensors_reloaded=2304,actual_final_latents_reloaded=64,
        last_path_writer_failure_controls=2,semantic_mutation_refusals=32,actual_truncation_refusals=2,
        prior_complete_CPU_audits_reused_with_source_unchanged=True,complete_rows=4,
        real_model_or_latency_or_endpoint_claim=False,actual_real_Native_source_origin_verified_without_instantiation=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
