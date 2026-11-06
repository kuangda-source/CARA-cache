#!/usr/bin/env python3
"""Execute the entire preregistered H-T63 CPU-only fixture."""
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
    finally:
        hf_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=previous
    assert not torch.cuda.is_initialized()
    adapter={'installed_flash_version':installed,'installed_package_present':True,
             'original_HF_availability':availability_before,'CUDA_hardware_availability_not_overridden':True,
             'original_helpers_and_current_device_restored':hf_utils.is_flash_attn_2_available is previous[0]
                 and import_utils.is_flash_attn_2_available is previous[1] and torch.cuda.current_device is previous[2],
             'weights_load_forbidden':True,'model_instantiated_by_actual_import':False,
             'GPU_runtime_adapter':False,'CUDA_initialized':False}
    reg = json.loads((args.stage / 'ra-calibration-sampling-preregistration.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert {n: sha(args.stage / n) for n in reg['payload_sha256']} == reg['payload_sha256']
    assert {n: sha(args.runtime / n) for n in reg['runtime_source_sha256']} == reg['runtime_source_sha256']
    assert not args.output.exists()
    spec = importlib.util.spec_from_file_location('actual_complete_native_batch_CPU', args.stage / 'tests/check_cfg_ra_calibration_sampling_cpu.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started = time.perf_counter()
    try:
        prior=json.loads((args.stage/reg['core_CPU_audit_ref']).read_text())
        assert prior['exit_code']==0 and prior['full_complete_8_parent_24_suffix_scope_reconstructed']
        assert prior['source_bound_full36_parent_equality_and_history_restore_verified'] and prior['GPU_submissions']==0
        def own_tensor_loader(path,**kwargs):
            resolved=Path(path).resolve()
            assert resolved.is_relative_to((args.stage/'CPU-artifacts').resolve()) and resolved.suffix=='.pt'
            assert kwargs=={'weights_only':True,'map_location':'cpu'}
            return original_tensor_load(resolved,**kwargs)
        result=module.run(args.runtime,own_tensor_loader,args.stage/'CPU-artifacts')
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
    assert all(r['actual_tensor_audit']['actual_parent_guided_tensors_reloaded']==144 and
        r['actual_tensor_audit']['actual_parent_latents_reloaded']==4 and r['actual_tensor_audit']['actual_child_tensors_reloaded']==48 and
        len(r['semantic_mutation_refusals'])==8 and r['actual_child_truncation_refused'] for r in passed)
    assert all(r['complete_scope_retained'] and r['initial_full_state_restored'] for r in failed)
    assert not torch.cuda.is_initialized()
    result.update(status='RA_CALIBRATION_SAMPLING_CPU_NOT_REAL_MODEL',
        CPU_wall_seconds=time.perf_counter()-started,actual_import_only_adapter=adapter,
        planned_scope=reg['CPU_scope'],payload_sha256=reg['payload_sha256'],CUDA_initialized=False,GPU_submissions=0,
        complete_successful_paths=8,complete_executed_paths_including_last_writer_failures=16,
        solver_updates=1248,net_calls=2496,actual_guided_tensors_reloaded=288,actual_final_latents_reloaded=8,actual_child_tensors_reloaded=96,
        last_path_writer_failure_controls=2,semantic_mutation_refusals=16,actual_truncation_refusals=2,
        prior_complete_CPU_audits_reused_with_source_unchanged=True,complete_rows=4,
        real_model_or_latency_or_endpoint_claim=False)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
