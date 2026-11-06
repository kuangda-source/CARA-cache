#!/usr/bin/env python3
"""New full-domain price CPU: real production boundary and two complete numeric flows."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def guardrail_codec_probe(stage,project,inference_module):
    import importlib.util
    import subprocess
    import torch
    import nltk
    root=project/'runtime-resources/nltk-guardrail-d6d4bfa8-r1'
    if root.is_symlink():raise ValueError('Guardrail resources must be physical')
    nltk.data.path.insert(0,str(root))
    tokens=nltk.word_tokenize('A person walks beside a parked car.')
    assert tokens==['A','person','walks','beside','a','parked','car','.']
    # Exercise the same video writer selected by clean.execute.
    writer=inference_module.save_img_or_video
    path=stage/'CPU-production-codec.mp4'
    writer(torch.zeros(3,93,32,32),str(path.with_suffix('')),24)
    from postprocess_wc_policy_interval_assets_r1 import RGB
    frames=RGB(path);assert len(frames)==93
    probe=subprocess.run(['ffprobe','-v','error','-show_entries','stream=nb_frames',
        '-of','json',str(path)],capture_output=True,text=True,check=True,timeout=20)
    assert any(r.get('nb_frames')=='93' for r in json.loads(probe.stdout)['streams'])
    return dict(actual_NLTK_tokenization=True,ordinary_video_writer=True,RGB_frames=93,ffprobe_exit0=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['numerical','production'],required=True)
    for n in ('project','stage','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();runtime=a.project/'runtime'
    os.environ.update(CUDA_VISIBLE_DEVICES='',WC_SCOUT_KIND='CAL12',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        PYTHONDONTWRITEBYTECODE='1',WC_POLICY_ASSETS_RUNTIME=str(runtime))
    sys.path[:0]=[str(a.stage/'src'),str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import torch
    assert not torch.cuda.is_initialized()
    original_load=torch.load
    def forbidden(*a,**kw):raise RuntimeError('Assets CPU prohibits CUDA, model weights and network')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    import triton
    class ImportOnlyDriver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,n):raise RuntimeError('CPU refuses Triton execution: '+n)
    triton.runtime.driver.active=ImportOnlyDriver()
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
    from wcomr.policy_price_refresh_production_r1 import read,sha,CONFIG,COUNTS,PROFILE,CPU_PROOF,matrix
    from wcomr.gpu_budget_pool_v2 import atomic_json
    reg=read(a.stage/'registration.json')
    assert {n:sha(a.stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
    assert {n:sha(runtime/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
    start=time.perf_counter()
    if a.mode=='numerical':
        spec=importlib.util.spec_from_file_location('full_policy_assets_numeric',a.stage/'tests/check_policy_price_refresh_sampling_cpu_r1.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        root=a.stage/'CPU-policy-assets-artifacts'
        def loader(path,**kwargs):
            assert Path(path).resolve().is_relative_to(root.resolve()) and kwargs=={'map_location':'cpu','weights_only':True}
            return original_load(path,**kwargs)
        value=module.run(runtime,loader,root)
        assert value['actual_CPU_paths']==48 and value['new_price_cells']==4060 and value['new_price_readout_trials']==48720
    else:
        from wcomr.policy_price_refresh_production_r1 import validate
        from wcomr.policy_price_refresh_sampling_r1 import execute
        from wcomr.policy_interval_readout_r1 import compile_skip
        from wcomr.cfg_guided_w1_forward import compile_output_denoise
        c,_,old,inputs,tables,prior=validate(a.project,a.stage)
        _,Cproof=compile_skip(runtime,vars(wc));_,RFproof=compile_output_denoise(runtime,rf)
        samples=[InferenceArguments(**r) for r in c['requests']]
        assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['requests']))
        setup=SetupArguments(**{**read(a.stage/'configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.stage/'CPU-production-output')})
        assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
        from types import SimpleNamespace
        for sample in samples:
            for mode in ('CONTROL','PRICE'):
                try:execute(SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None),sample,mode,
                    table_parameters=tables,previous_parameters=prior,accepted_cells=[])
                except ValueError as e:assert str(e)=='Ordinary guardrails required'
                else:raise AssertionError('Unguarded production request accepted')
        value=dict(status='POLICY_PRICE_ACTUAL_ENTRY_CPU_PASS_NOT_FULL_LIFECYCLE_ACCEPTANCE',production_CPU_accepted=True,full_GPU_lifecycle_accepted=False,
            source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),config_sha256=sha(a.stage/CONFIG),
            scope_counts=COUNTS,matrix=matrix(),profile=PROFILE,actual_Cosmos_request_count=4,
            guard_refusal_controls=8,C_source_inverse=Cproof,RF_source_inverse=dict(RFproof),
            original_Cosmos_entry_imported=True,model_weights_loaded=0,CUDA_initialized=False,GPU_submissions=0,ledger_written=False)
    assert not torch.cuda.is_initialized()
    value.update(CPU_wall_seconds=time.perf_counter()-start,CUDA_initialized=False,GPU_submissions=0)
    if a.mode=='production':
        from four_card_policy_assets_port_r1 import cpu_transport_probe
        value['host_transport_CPU']=cpu_transport_probe(a.stage)
        value['actual_guardrail_and_codec']=guardrail_codec_probe(a.stage,a.project,im)
    assert not a.output.exists();atomic_json(a.output,value)
    print(json.dumps({k:value.get(k) for k in ('status','CPU_wall_seconds','actual_CPU_paths','production_CPU_accepted')}))


if __name__=='__main__':main()
