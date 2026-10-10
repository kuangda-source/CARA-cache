#!/usr/bin/env python3
"""Execute full E2 confirmation/timing fixture without CUDA or model weights."""
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
    import gzip
    spec=importlib.util.spec_from_file_location('E2_complete_CPU_fixture',args.stage/'tests/check_e2_confirmation_timing_sampling_cpu_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    inputs=json.loads((args.stage/reg['E2_inputs_ref']).read_text())
    assert sha(args.stage/reg['E2_inputs_ref'])==reg['E2_inputs_sha256']
    from wcomr.e2_confirmation_timing_sampling_r1 import expected_matrix
    assert len(expected_matrix(inputs))==76
    old_stage=Path(reg['old_A_CPU_stage'])
    old_receipt=json.loads((old_stage/'receipt.json').read_text())
    assert old_receipt['exit_code']==old_receipt['child_exit_code']==0
    assert sha(old_stage/'result.json')==reg['old_A_CPU_result_sha256']==old_receipt['result_sha256']
    old_reg=json.loads((old_stage/'registration.json').read_text())
    assert {n:sha(old_stage/n) for n in old_reg['payload_sha256']}==old_reg['payload_sha256']==old_receipt['payload_after_sha256']
    old_A_CPU_result=json.loads((old_stage/'result.json').read_text())
    prior=json.loads((args.stage/reg['calibration_batch_CPU_audit_ref']).read_text())
    assert prior['exit_code']==0 and prior['GPU_submissions']==0
    calibration_cpu_result=json.loads(gzip.decompress((args.stage/reg['calibration_batch_CPU_result_ref']).read_bytes()))
    assert calibration_cpu_result['status']=='RA_CALIBRATION_SAMPLING_CPU_NOT_REAL_MODEL'
    def own_tensor_loader(path,**kwargs):
        resolved=Path(path).resolve()
        roots=[(args.stage/'CPU-artifacts').resolve(),(old_stage/'CPU-artifacts').resolve()]
        assert any(resolved.is_relative_to(root) for root in roots) and resolved.suffix=='.pt'
        assert kwargs=={'weights_only':True,'map_location':'cpu'}
        return original_tensor_load(resolved,**kwargs)
    started=time.perf_counter()
    try:
        result=module.run(args.runtime,own_tensor_loader,args.stage/'CPU-artifacts',calibration_cpu_result,inputs,old_A_CPU_result)
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps({
            'status':'E2_FULL76_CPU_FAILED_COMPLETE_SCOPE_RETAINED','error':str(error),'error_type':type(error).__name__,
            'CPU_wall_seconds':time.perf_counter()-started,'planned_scope':reg['E2_CPU_scope'],
            'GPU_submissions':0,'CUDA_initialized':torch.cuda.is_initialized()},indent=2)+'\n')
        raise
    rows=result['checks'];good=[r for r in rows if r['status']=='PASS']
    bad=[r for r in rows if r['status']=='EXPECTED_FAILURE'];refused=[r for r in rows if r['status']=='EXPECTED_REJECTION']
    assert len(good)==len(bad)==2 and len(refused)==4
    assert all(r['verdict']['accepted']==76 and r['actual_tensor_audit']['actual_guided_reloaded']==1584
        and r['actual_tensor_audit']['actual_final_latents_reloaded']==76 and len(r['unchanged_old_A_sampler_parity'])==4
        and len(r['semantic_mutation_refusals'])==10 and r['final_timing_truncation_refused'] for r in good)
    assert all(r['all76_slots_retained'] and r['initial_full_state_restored'] for r in bad)
    assert not torch.cuda.is_initialized()
    result.update(status='E2_FULL76_SAMPLER_CPU_PASS_NOT_REAL_MODEL',CPU_wall_seconds=time.perf_counter()-started,
        actual_import_only_adapter=adapter,planned_scope=reg['E2_CPU_scope'],payload_sha256=reg['payload_sha256'],
        CUDA_initialized=False,GPU_submissions=0,successful_complete_paths=152,successful_solver_updates=5472,
        successful_CFG_calls=10944,actual_guided_reloaded=3168,actual_final_latents_reloaded=152,
        old_A_saved_all36_and_final_parity_paths=8,actual_AV28_timing_parity_paths=32,
        failed_scope_original_slots_retained=152,additional_guardrail_refusals=4,semantic_mutation_refusals=20,
        final_timing_truncation_refusals=2,actual_old_source_and_tensor_readonly=True,
        real_model_or_latency_or_endpoint_claim=False)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))


if __name__=='__main__':main()
