"""Affected full46 video entry with actual frozen Cosmos argument schema."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True);p.add_argument('--artifacts',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and not a.artifacts.exists()
    import torch
    torch.set_num_threads(1)
    def forbid(*args,**kwargs):raise RuntimeError('CPU check forbids CUDA and downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    runtime=ROOT/'cache/runtime';start=time.monotonic();actual_request=None
    try:
        assert (ROOT/'registration.json').exists(),'Host-bound check requires original source registration'
        sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        import triton
        class Driver:
            def get_benchmarker(self):return forbid
            def __getattr__(self,name):raise RuntimeError('CPU refuses Triton '+name)
        triton.runtime.driver.active=Driver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        saved=hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device
        hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
        try:from cosmos_predict2.config import InferenceArguments
        finally:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
        raw=json.loads((ROOT/'configs/wc_scout_cal12_production_entry_r1_20261018.json').read_text())['requests']
        samples={r['name']:InferenceArguments.model_validate(r) for r in raw}
        assert len(samples)==4 and InferenceArguments.model_config['frozen'] is True
        def actual_request(name):
            return InferenceArguments.model_validate({**samples[name].model_dump(mode='python',round_trip=True),
                                                      'resolution':'16,16'})
        from check_innovation_gain_video_cpu_r1 import run
        result=run(runtime,a.artifacts,actual_request=actual_request)
        assert result['actual_Cosmos_request_class'] and sum(c['paths'] for c in result['checks'])==92
        value=dict(status='IG_B2_BOUND_CPU_PASS_NOT_REAL_MODEL',video_entry=result,
            actual_frozen_request_class=InferenceArguments.__module__+'.'+InferenceArguments.__qualname__,
            validated_production_requests=4,declared_small_CPU_resolution='16,16',GPU_submissions=0)
    except BaseException:
        value=dict(status='CPU_FAILED',traceback=traceback.format_exc(),GPU_submissions=0)
    names=['src/wcomr/innovation_gain_video_r1.py','src/wcomr/innovation_gain_deployment_r1.py',
           'src/wcomr/innovation_gain_r1.py','src/wcomr/policy_generator_r1/p2_native_sampling.py',
           'src/wcomr/policy_generator_r1/production_sampling.py','src/wcomr/policy_generator_r1/exploration_requests.py',
           'src/wcomr/policy_generator_r1/frozen_request_arguments.py','tests/check_innovation_gain_video_cpu_r1.py',
           'scripts/check_cara_ig_b2_cpu_r1.py','manifests/cara_IG_B2_predeclared_matrix_r1_20261027.json']
    value.update(source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},
                 cuda_initialized=torch.cuda.is_initialized(),wall_seconds=time.monotonic()-start)
    assert not value['cuda_initialized']
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value[k] for k in ('status','wall_seconds')}))
    if value['status']=='CPU_FAILED':print(value['traceback']);raise SystemExit(1)


if __name__=='__main__':main()
