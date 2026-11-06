"""GPU-hidden complete S ownership inventory and full2B meta architecture."""
import argparse
from collections import Counter
import hashlib
import io
import inspect
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'scripts')]


def meta_architecture(runtime,identity):
    """Instantiate only cfg.model.config.net on meta; never build a pipeline."""
    import importlib
    import torch
    from wcomr.runtime_config import install_core_inference_registration,MODEL,EXPERIMENT
    from wcomr.h0_mode import mode_snapshot
    from wcomr.sq_s_resources_r1 import (inventory,registered_experiment,explicit_meta_constructor,
        explicit_meta_device_resolver)
    from cosmos_predict2.config import MODEL_KEYS,MODEL_CHECKPOINTS
    from cosmos_predict2._src.imaginaire.utils.config_helper import get_config_module,override
    from cosmos_predict2._src.imaginaire.lazy_config import instantiate
    model_name=identity['model_setup']['model']
    experiment=registered_experiment(model_name,MODEL_KEYS,MODEL_CHECKPOINTS,
        expected_model=MODEL,expected_experiment=EXPERIMENT)
    install_core_inference_registration(model_name,experiment)
    module=get_config_module('cosmos_predict2/_src/predict2/configs/video2world/config.py')
    config=importlib.import_module(module).make_config()
    config=override(config,['--','experiment='+experiment,'~data_train'])
    import transformer_engine as te
    rmsnorm_ops=importlib.import_module('transformer_engine.pytorch.ops.basic.rmsnorm')
    original=te.pytorch.RMSNorm.__init__
    original_resolver=rmsnorm_ops.canonicalize_device
    constructor_path=Path(inspect.getsourcefile(original))
    expected=json.loads((ROOT/identity['shared_eval_mode_ref']).read_text())
    norm_class=te.pytorch.RMSNorm.__module__+'.'+te.pytorch.RMSNorm.__qualname__
    with explicit_meta_constructor(te.pytorch.RMSNorm) as constructor:
        with torch.device('meta'),explicit_meta_device_resolver(rmsnorm_ops) as resolver:
            net=instantiate(config.model.config.net).to(dtype=torch.bfloat16)
    if te.pytorch.RMSNorm.__init__ is not original or constructor['calls']!=expected['module_types'][norm_class]:
        raise ValueError('Exact original RMSNorm topology or constructor restoration differs')
    if rmsnorm_ops.canonicalize_device is not original_resolver or resolver['default_calls']<1:
        raise ValueError('Original TE reset-device resolver was not exercised/restored')
    parameters=list(net.named_parameters());buffers=list(net.named_buffers())
    if len(net.blocks)!=28 or len(parameters)!=569 or any(v.device.type!='meta' for _,v in parameters+buffers):
        raise ValueError('Full2B metadata architecture differs from original A32 binding')
    if Counter(str(v.dtype) for _,v in parameters)!=Counter({'torch.bfloat16':569}) or not net.use_wan_fp32_strategy:
        raise ValueError('Original BF16/Wan FP32 strategy differs')
    mode=mode_snapshot(net)
    if mode['module_types']!=expected['module_types']:raise ValueError('Actual full2B module topology differs')
    result=dict(status='FULL2B_NET_META_ARCHITECTURE_ONLY_NO_WEIGHTS_OR_FORWARD',
        resolved_experiment=experiment,checkpoint_paths_resolved=False,blocks=len(net.blocks),parameter_tensors=len(parameters),
        parameter_dtypes=dict(Counter(str(v.dtype) for _,v in parameters)),
        parameters=inventory(dict(parameters)),buffers=inventory(dict(buffers)),
        buffer_schema=[dict(name=n,shape=list(v.shape),dtype=str(v.dtype),bytes=v.numel()*v.element_size()) for n,v in buffers],
        module_types=mode['module_types'],matches_original_shared_eval_topology=True,
        constructor_adapter=dict(constructor,class_path=te.pytorch.RMSNorm.__module__+'.'+te.pytorch.RMSNorm.__qualname__,
            original_source_sha256=hashlib.sha256(constructor_path.read_bytes()).hexdigest(),
            original_class_and_body_preserved=True,restored_before_tiny_sampling=True),
        reset_device_adapter=dict(resolver,original_resolver_body_preserved=True,restored_before_tiny_sampling=True,
            original_resolver_source_sha256=hashlib.sha256(Path(inspect.getsourcefile(original_resolver)).read_bytes()).hexdigest(),
            original_operation_source_sha256=hashlib.sha256(Path(rmsnorm_ops.__file__).read_bytes()).hexdigest()),
        use_wan_fp32_strategy=net.use_wan_fp32_strategy,weights_loaded=False,
        network_forward_executed=False,full_model_GPU_memory_peak_measured=False)
    del net,parameters,buffers
    return result


def main():
    p=argparse.ArgumentParser()
    for name in ('assets','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('profile','scope','manifest-sha256'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S resource CPU attempt')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('S resource preparation must hide GPUs')
    started,cpu=time.monotonic(),time.process_time();child_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    import torch
    def forbidden(*a,**kw):raise RuntimeError('S resource CPU forbids CUDA, weight loading and downloads')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    import huggingface_hub
    huggingface_hub.hf_hub_download=forbidden;huggingface_hub.snapshot_download=forbidden
    torch.set_num_threads(2);os.nice(10)
    scope=json.loads((ROOT/args.scope).read_text());identity=json.loads((ROOT/scope['identity_ref']).read_text())
    log=io.StringIO()
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_sq_s_resources_r1'))
    if not tests.wasSuccessful() or tests.testsRun!=scope['unit_controls'] or tests.skipped:raise ValueError(log.getvalue())
    print(json.dumps(dict(status='S_RESOURCE_CPU_UNIT_CONTROLS_PASS',tests=tests.testsRun,GPU_submissions=0)),flush=True)
    runtime=ROOT/'cache/runtime'
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('S resource CPU forbids Triton execution: '+name)
    triton.runtime.driver.active=Driver()
    import transformers.utils as transformer_utils
    from transformers.utils import import_utils
    saved=(transformer_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    transformer_utils.is_flash_attn_2_available=import_utils.is_flash_attn_2_available=lambda:True
    torch.cuda.current_device=lambda:0
    try:
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:
        transformer_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=saved
    from cosmos_predict2._src.imaginaire.utils import checkpoint_db
    checkpoint_db.hf_hub_download=forbidden;checkpoint_db.snapshot_download=forbidden
    model=meta_architecture(runtime,identity)
    print(json.dumps(dict(status='FULL2B_META_ARCHITECTURE_PASS_NO_WEIGHTS_OR_FORWARD',
        parameters=model['parameter_tensors'],GPU_submissions=0)),flush=True)
    from check_sq_s_resources_cpu_r1 import run
    fixture=run(runtime,ROOT/'S-resource-CPU-artifacts');rows=fixture['checks']
    if len(rows)!=2 or {r['flow'] for r in rows}!={False,True}:raise ValueError('Both complete CPU flow settings required')
    schemas={};boundaries=[]
    for row in rows:
        if len(row['events'])!=54 or len(row['paths'])!=2:raise ValueError('Both fixed parents/all27 targets required')
        for event in row['events']:
            report=event['inventory'];report.pop('completed_parent_pairs')
            raw=json.dumps(report,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
            key=hashlib.sha256(raw).hexdigest();schemas.setdefault(key,report)
            boundaries.append(dict(flow=row['flow'],parent=event['parent'],step=event['step'],schema_sha256=key))
    if len(boundaries)!=108 or torch.cuda.is_initialized():raise ValueError('Exact CPU inventory denominator/GPU boundary differs')
    children=resource.getrusage(resource.RUSAGE_CHILDREN)
    result=dict(status='SQ_S_COMPLETE_OWNERSHIP_AND_META_ARCHITECTURE_CPU_PASS_NOT_GPU_CARD',
        scope=scope,profile=args.profile,unit_controls=dict(tests=tests.testsRun,skipped=0,log=log.getvalue()),
        full2B_meta_architecture=model,complete_tiny_CPU_paths=4,before_pair_boundaries=boundaries,schemas=schemas,
        original_deployed_copy_guard_reconciled=True,native_production_source_modified=False,
        CPU_import_probes_restored_before_metadata_and_sampling=True,model_weight_loads_forbidden=True,
        Hugging_Face_download_functions_blocked=True,
        actual_Cosmos_weights=False,real_generated_video=False,S_real_labels=0,CUDA_initialized=False,
        physical_GPU_or_RAM_peak_measured=False,complete_S_GPU_entry_accepted=False,whole_S_quote_frozen=False,
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        reaped_child_CPU_seconds=children.ru_utime+children.ru_stime-child_before.ru_utime-child_before.ru_stime,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])


if __name__=='__main__':main()
