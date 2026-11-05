"""GPU-hidden production imports and complete local S1/S2 tiny paths."""
import json
import os
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
STAGE=HERE.parents[2];PROJECT=STAGE.parents[1];runtime=PROJECT/'runtime'
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',CARA_READ_WRITE_RUNTIME=str(runtime),
    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WC_SCOUT_KIND='CAL12')
sys.path[:0]=[str(STAGE),str(STAGE/'src'),str(STAGE/'scripts'),str(STAGE/'tests'),str(HERE),str(runtime),
    str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
import torch,triton
torch.set_num_threads(2)
def forbidden(*args,**kwargs):raise RuntimeError('Sparse production CPU forbids CUDA/downloads')
torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
class Driver:
    def get_benchmarker(self):return forbidden
    def __getattr__(self,name):raise RuntimeError('CPU refuses Triton: '+name)
triton.runtime.driver.active=Driver()
import transformers.utils as hu
from transformers.utils import import_utils as iu
saved=hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device
hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True
torch.cuda.current_device=lambda:0
try:
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference
    from cosmos_predict2._src.predict2.inference import worldcache_utils
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow
finally:
    hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
card=json.loads((HERE/'manifest.json').read_text())
for row in card['inputs']:InferenceArguments(**{k:v for k,v in row.items() if k!='partition'})
SetupArguments(**{**json.loads((STAGE/'configs/f1_setup.json').read_text()),
    'keep_going':True,'worldcache_enabled':True,'output_dir':str(STAGE/'CPU-output')})
runpy.run_path(str(HERE/'runner.py'),run_name='sparse_runner_import')
runpy.run_path(str(HERE/'cpu_check.py'),run_name='__main__')
runpy.run_path(str(HERE/'runtime_cpu.py'),run_name='__main__')
from wcomr.gpu_budget_pool_v2 import atomic_json
reg=json.loads((STAGE/'registration.json').read_text())
atomic_json(STAGE/'CPU-proof.json',dict(passed=True,actual_production_entry_imported=True,
    scope_sha256=card['scope_sha256'],source_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
    torch_version=torch.__version__,CUDA_initialized=torch.cuda.is_initialized(),GPU_submissions=0,
    local_checks=json.loads((HERE/'cpu_check.json').read_text()),runtime_checks=json.loads((HERE/'runtime_cpu.json').read_text())))
