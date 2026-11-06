"""GPU-hidden production import and the same complete tiny CPU dry-run."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--manifest',type=Path,default=HERE/'manifest.json')
args=parser.parse_args()
STAGE=HERE.parents[2]
PROJECT=STAGE.parents[1]
runtime=PROJECT/'runtime'
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
    CARA_READ_WRITE_RUNTIME=str(runtime),CARA_SENS_MANIFEST=str(args.manifest),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WC_SCOUT_KIND='CAL12')
sys.path[:0]=[str(STAGE/'src'),str(STAGE/'scripts'),str(STAGE/'tests'),str(HERE),str(runtime),
    str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
import torch,triton
torch.set_num_threads(2)
def forbidden(*a,**kw):raise RuntimeError('Sensitivity CPU forbids CUDA/downloads')
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
card=json.loads(args.manifest.read_text())
for row in card['inputs']:
    InferenceArguments(**{k:v for k,v in row.items() if k!='partition'})
if 'reuse' in card:
    original=json.loads(Path(card['reuse']['collection']).read_text())
    for row in original['rows']:
        if row['slot']['id'] in card['reuse']['record_ids']:
            for key in ('latent_artifact','video_artifact'):
                assert Path(row['result'][key]['path']).is_file(), 'Reused artifact is outside the container mounts'
if 'carryover' in card:
    for row in card['carryover']['rows']:
        for key in ('latent_artifact','video_artifact'):
            assert Path(row['result'][key]['path']).is_file(), 'Carried artifact is outside the container mounts'
if 'inherited_outputs' in card:
    from runner import assert_inherited_hashes
    assert_inherited_hashes(card)
if card.get('host_memory_logging'):
    from runner import log_host_memory
    log_host_memory(STAGE/'CPU-host-memory.jsonl','CPU_ENTRY')
SetupArguments(**{**json.loads((STAGE/'configs/f1_setup.json').read_text()),
    'keep_going':True,'worldcache_enabled':True,'output_dir':str(STAGE/'CPU-output')})
runpy.run_path(str(HERE/'runner.py'),run_name='sensitivity_runner_import')
if 'postrelease_CPU_entry' in card:
    runpy.run_path(str(STAGE/card['postrelease_CPU_entry']),run_name='postrelease_CPU_import')
runpy.run_path(str(HERE/'cpu_dry_run.py'),run_name='__main__')
from wcomr.gpu_budget_pool_v2 import atomic_json
registration=json.loads((STAGE/'registration.json').read_text())
atomic_json(STAGE/'CPU-proof.json',dict(passed=True,actual_production_entry_imported=True,
    scope_sha256=card['scope_sha256'],source_sha256=registration['payload_sha256'],
    runtime_source_sha256=registration['runtime_source_sha256'],torch_version=torch.__version__,
    complete_tiny_requests=2*len(card['matrix']),CUDA_initialized=torch.cuda.is_initialized(),GPU_submissions=0))
