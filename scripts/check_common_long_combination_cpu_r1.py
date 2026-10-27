"""CPU-only affected-path proof with actual immutable Cosmos request schema."""
import argparse,hashlib,importlib.util,json,os,sys,time,traceback,unittest
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);p.add_argument('--host',choices=['four_card','two_card'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists();start=time.time();reg=json.loads((a.stage/'registration.json').read_text())
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 assert reg['host']==a.host and all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
 assert all(sha(a.runtime/n)==h for n,h in reg['runtime_source_sha256'].items())
 os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests'),str(a.runtime),str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
 import torch
 assert not torch.cuda.is_initialized();torch.set_num_threads(1)
 def forbidden(*a,**k):raise RuntimeError('Paper timing CPU forbids CUDA, weights and downloads')
 torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
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
  from cosmos_predict2.config import InferenceArguments
  import cosmos_predict2._src.predict2.inference.worldcache_utils
  import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
 finally:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
 req=json.loads((a.stage/'configs/cara_DEV128_requests_r1_20261026.json').read_text())['requests'][0]
 sample=InferenceArguments.model_validate({**req,'resolution':'16,16'})
 assert sample.model_config['frozen']
 spec=importlib.util.spec_from_file_location('common_combination_numeric',a.stage/'tests/check_common_long_combination_cpu_r1.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 run=m.run
 manifest=json.loads((a.stage/'manifests/cara_common_long_newstates_scope_quote_r1_20261027.json').read_text())
 numeric=run(a.runtime,a.stage/'CPU-numeric',a.host,sample,manifest)
 from check_common_long_lifecycle_cpu_r1 import run as lifecycle
 life=lifecycle(a.stage,a.stage/'CPU-lifecycle')
 from check_common_long_storage_cpu_r1 import run as storage_test
 storage=storage_test(a.stage,a.stage/'CPU-storage')
 import test_common_long_terminal_r1
 tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_common_long_terminal_r1));assert tests.wasSuccessful()
 assert not torch.cuda.is_initialized()
 proof=dict(status='COMMON_LONG_COMBINATION_CPU_PASS_NOT_GPU',host=a.host,started_unix=start,ended_unix=time.time(),registration_sha256=sha(a.stage/'registration.json'),payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],numeric=numeric,lifecycle=life,storage=storage,terminal_tests=tests.testsRun,CUDA_initialized=False,model_weights_loaded=False,GPU_submissions=0,ledger_written=False,whole_method_card_accepted=False,original_budget_clock='full_request_seconds')
 with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=proof['status'],host=a.host,CPU_wall_seconds=time.time()-start)))
if __name__=='__main__':main()
