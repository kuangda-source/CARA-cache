#!/usr/bin/env python3
"""GPU-hidden actual Cosmos entry, full sampler controls, guardrails and codecs."""
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
    assert not torch.cuda.is_initialized();torch.set_num_threads(2)
    def forbidden(*a,**kw):raise RuntimeError('PG CPU forbids CUDA, model weights and network')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
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
    requests=read(a.stage/'configs/wc_policy_interval_assets_full1624_r1_20261020.json')['requests']+read(a.stage/'plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json')['requests']
    samples=[InferenceArguments(**r) for r in requests]
    assert len(samples)==6 and all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,requests))
    setup=SetupArguments(**{**read(a.stage/'configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.stage/'CPU-output')})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    spec=importlib.util.spec_from_file_location('pg_sampler_checks',a.stage/'tests/check_cara_pg_production_sampling_cpu_r1.py')
    checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    profile,plans=checks.plans()
    from wcomr.policy_generator_r1.production_sampling import execute
    from types import SimpleNamespace
    for sample in samples:
        try:execute(SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None),sample,profile=profile,policy=plans['MIXED'],runtime=runtime,wc=None,rf=None,settings={},calibration=None,specs={},inference_module=im,output=a.stage/'never',expected_shape=[])
        except ValueError as e:assert str(e)=='Ordinary guardrails required'
        else:raise AssertionError('Unguarded PG request accepted')
    from check_wc_policy_price_refresh_cpu_r1 import guardrail_codec_probe
    codec=guardrail_codec_probe(a.stage,a.project,im)
    hspec=importlib.util.spec_from_file_location('historical_sampler_checks',a.stage/'tests/check_cara_historical_bridge_sampling_cpu_r1.py')
    historical=importlib.util.module_from_spec(hspec);hspec.loader.exec_module(historical)
    numeric=historical.run(runtime,None,a.stage/'CPU-historical-numeric')
    assert numeric['actual_CPU_paths']==148
    assert {c['flow'] for c in numeric['checks']}=={False,True}
    from four_card_policy_assets_port_r1 import cpu_transport_probe
    transport=cpu_transport_probe(a.stage)
    value=dict(status='HISTORICAL_BRIDGE_ACTUAL_ENTRY_AND_FULL148_CPU_COMPLETE_NOT_GPU',source_revision=reg['source_revision'],
        registration_sha256=sha(a.stage/'registration.json'),started_unix=started,ended_unix=time.time(),
        actual_request_count=6,guard_refusal_controls=6,actual_SetupArguments=True,codec=codec,numeric=numeric,transport=transport,
        CUDA_initialized=False,model_weights_loaded=0,GPU_submissions=0,ledger_written=False)
    assert not torch.cuda.is_initialized()
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=value['status'],CPU_wall_seconds=value['ended_unix']-started)))
if __name__=='__main__':main()
