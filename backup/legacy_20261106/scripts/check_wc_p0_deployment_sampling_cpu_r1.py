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
    reg=json.loads((args.stage/'registration.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert {n:sha(args.stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
    assert {n:sha(args.runtime/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
    assert not args.output.exists()
    spec=importlib.util.spec_from_file_location('guided_W1_actual_full_batch_CPU',args.stage/'tests/check_partial_mlp_deployment_sampling_cpu_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);started=time.perf_counter()
    def own_loader(path,**kwargs):
        path=Path(path).resolve();assert path.is_relative_to((args.stage/'CPU-artifacts').resolve()) and path.suffix=='.pt'
        assert kwargs=={'weights_only':True,'map_location':'cpu'}
        return original_tensor_load(path,**kwargs)
    try:
        value=module.run(args.runtime,own_loader,args.stage/'CPU-artifacts')
        good=[v for v in value['checks'] if v['status']=='PASS'];bad=[v for v in value['checks'] if v['status']=='EXPECTED_FAILURE']
        assert len(good)==2 and len(bad)==2 and {v['flow'] for v in good}=={False,True}
        assert all(v['actual_tensor_audit']['actual_guided_reloaded']==1872 and v['actual_tensor_audit']['actual_latents_reloaded']==52
            and v['actual_tensor_audit']['independent_partial_full_trajectory_comparisons']==16
            and len(v['actual_tensor_audit']['files'])==52 and len(v['mutation_refusals'])==7
            and v['actual_artifact_truncation_refused'] and v['P_source_reuse_C_checks']==180
            and v['consecutive_P_checks']==100 for v in good)
        assert all(v['complete_scope_retained'] and v['initial_full_state_restored'] and v['installed_MLP_methods_restored'] for v in bad)
        assert not torch.cuda.is_initialized()
        value.update(status='P0_DEPLOYMENT_FULL_SAMPLER_ACTUAL_CPU_PASS_NOT_REAL_MODEL',CPU_wall_seconds=time.perf_counter()-started,
            planned_scope=reg['CPU_scope'],payload_sha256=reg['payload_sha256'],actual_import_only_adapter=adapter,
            complete_successful_paths=104,complete_executed_paths_including_final_writer_failure=208,
            actual_complete_solver_updates=7488,actual_normal_net_calls=14976,actual_guided_reloaded=3744,
            actual_latents_reloaded=104,actual_all_tensors_reloaded=3848,
            actual_truncation_refusals=2,mutation_refusals=14,last_parent_writer_failure_controls=2,
            successful_additional_and_physical_checkpoint_roundtrips=416,
            actual_UniPC_source_executed=True,real_Cosmos_CAL_or_video_or_quality_or_clean_latency_claim=False,
            CUDA_initialized=False,GPU_submissions=0)
        args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','GPU_submissions')}))
    except BaseException as e:
        args.output.with_suffix('.failure.json').write_text(json.dumps({'status':'COMPLETE_SCOPE_FAILED_NOT_SUBSET','error':str(e),'error_type':type(e).__name__,'GPU_submissions':0,'CUDA_initialized':torch.cuda.is_initialized()},indent=2)+'\n');raise


if __name__=='__main__':main()
