#!/usr/bin/env python3
"""GPU-hidden P2 all-count Native and same-trajectory history production CPU."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();runtime=a.project/'runtime';started=time.time()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WC_SCOUT_KIND='CAL12')
    sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(1)
    def forbidden(*a,**kw):raise RuntimeError('PG CPU forbids CUDA, model weights and network')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    original_load=torch.load
    def diagnostic_load(file,*args,**kwargs):
        path=Path(file if isinstance(file,(str,Path)) else file.name).resolve()
        if not path.is_relative_to((a.stage/'CPU-pg-numeric').resolve()) or path.suffix!='.pt':forbidden()
        return original_load(file,*args,**kwargs)
    torch.load=diagnostic_load
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,n):raise RuntimeError('CPU refuses Triton: '+n)
    triton.runtime.driver.active=Driver()
    import transformers.utils as hu
    from transformers.utils import import_utils as iu
    saved=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
    hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        import cosmos_predict2.inference as im
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
    from wcomr.policy_interval_assets_r1 import read,sha
    reg=read(a.stage/'registration.json')
    assert {n:sha(a.stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
    assert {n:sha(runtime/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
    original_requests=read(a.stage/'configs/wc_policy_interval_assets_full1624_r1_20261020.json')['requests']
    card=read(a.stage/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json')
    requests=[{**r,'num_steps':spec['requested_steps']} for spec in card['roles'].values() for r in original_requests]
    samples=[InferenceArguments(**r) for r in requests]
    assert len(samples)==60 and all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,requests))
    setup=SetupArguments(**{**read(a.stage/'configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.stage/'CPU-output')})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    spec=importlib.util.spec_from_file_location('pg_sampler_checks',a.stage/'tests/check_cara_cal66_sampling_cpu_r1.py')
    checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    from wcomr.policy_generator_r1.p2_native_sampling import execute
    from types import SimpleNamespace
    for sample in samples:
        try:execute(SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None,pipe=SimpleNamespace(model=SimpleNamespace(net=None))),sample,schedule=dict(requested_steps=sample.num_steps,actual_updates=1,timesteps=[1],sigmas=[1,0]),runtime=runtime,wc=None,rf=None,settings={},calibration=None,specs={},inference_module=im,output=a.stage/'never',expected_shape=[])
        except ValueError as e:assert str(e)=='Ordinary guardrails required'
        else:raise AssertionError('Unguarded P2 request accepted')
    from check_wc_policy_price_refresh_cpu_r1 import guardrail_codec_probe
    codec=guardrail_codec_probe(a.stage,a.project,im)
    import unittest
    spec2=importlib.util.spec_from_file_location('p2_batch_cpu',a.stage/'tests/test_cara_pg_p2_production_batch.py')
    batch=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(batch)
    batch_result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(batch))
    assert batch_result.wasSuccessful()
    numeric=checks.run(runtime,a.stage/'CPU-pg-numeric')
    assert {c['flow'] for c in numeric['checks']}=={False,True}
    from four_card_policy_assets_port_r1 import cpu_transport_probe
    transport=cpu_transport_probe(a.stage)
    value=dict(status='SHARED_CAL66_ACTUAL_ENTRY_CPU_COMPLETE_NOT_GPU',source_revision=reg['source_revision'],
        registration_sha256=sha(a.stage/'registration.json'),started_unix=started,ended_unix=time.time(),
        batch_controls_passed=batch_result.testsRun,actual_request_count=60,guard_refusal_controls=60,actual_SetupArguments=True,codec=codec,numeric=numeric,transport=transport,
        CUDA_initialized=False,model_weights_loaded=0,GPU_submissions=0,ledger_written=False)
    assert not torch.cuda.is_initialized()
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=value['status'],CPU_wall_seconds=value['ended_unix']-started)))
if __name__=='__main__':main()
