"""Actual new supervisor/guardian children, full128 replay and isolated finance."""
import argparse,importlib.util,json,os,subprocess,sys,time,unittest
from pathlib import Path

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser()
 for n in ('project','stage','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();start=time.time();sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 assert os.environ['CUDA_VISIBLE_DEVICES']=='' and not list(Path('/dev').glob('nvidia*'))
 import torch
 torch.set_num_threads(1)
 from wcomr.policy_generator_r1.dev128_card import validate,read,sha,COUNTS
 from wcomr.gpu_budget_pool_v2 import atomic_json
 c,reg,card=validate(a.project,a.stage)
 prior=read(a.stage/'prior-production-proof.json');binding=read(a.stage/'prior-production-binding.json')
 assert prior['host']==c['host'] and prior['scope']==COUNTS and sha(a.stage/'prior-production-proof.json')==binding['proof_sha256']
 assert prior['status']=='DEV128_DUAL_HOST_PRODUCTION_CPU_COMPLETE_NOT_GPU'
 # Earlier real entry/numerics/models are byte-bound. Only the runner now calls
 # the separate execution authorization validator; affected whole lifecycle below.
 for n,h in binding['payload_sha256'].items():
  if n=='scripts/run_cara_dev128_r1.py':continue
  assert reg['payload_sha256'][n]==h,'Changed accepted dependency '+n
 original_runner=(a.stage/'prior-runner.py.txt').read_text();new=(a.stage/'scripts/run_cara_dev128_r1.py').read_text()
 assert new==original_runner.replace('all66 frozen historical/boundary paths','all128 frozen held-out paths').replace('policy_generator_r1.dev128_card import validate,read,sha,RUN,COUNTS,CONFIG','policy_generator_r1.dev128_execution import validate,read,sha,RUN,COUNTS,CONFIG')
 assert prior['outputs']['quality']['models_really_loaded'] and not prior['CUDA_initialized']
 from wcomr.policy_generator_r1.dev128_execution import execution_quote,validate as execution_validate
 try:execution_validate(a.project,a.stage)
 except ValueError:pass
 else:raise AssertionError('CPU stage incorrectly executable')
 quotes={h:execution_quote(card,h,a.stage/'manifests/cara_DEV128_dual_host_whole_quote_r1_20261026.json') for h in ('four_card','two_card')}
 life=load(a.stage/'tests/check_cara_dev128_lifecycle_cpu_r1.py','devlife').run(a.stage,a.stage/'CPU-dev128-lifecycle')
 storage=load(a.stage/'tests/check_dev128_storage_cpu_r1.py','devstorage').run(a.stage,a.stage/'CPU-dev128-storage')
 tests=unittest.TestSuite()
 for n in ('test_cara_dev128_terminal_r1.py','test_cara_dev128_finance_r1.py','test_cara_dev128_post_r1.py'):
  tests.addTests(unittest.defaultTestLoader.loadTestsFromModule(load(a.stage/'tests'/n,n[:-3])))
 result=unittest.TextTestRunner(verbosity=2).run(tests);assert result.wasSuccessful() and not result.skipped
 assert not torch.cuda.is_initialized()
 proof=dict(status='DEV128_FULL_LIFECYCLE_RELEASE_SCORE_FINANCE_CPU_COMPLETE',host=c['host'],source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),scope=COUNTS,
  started_unix=start,ended_unix=time.time(),reused_production_binding=binding,production_entry_CPU_accepted=True,quality_models_CPU_accepted=True,
  lifecycle=life,storage=storage,terminal_tests=result.testsRun,quotes=quotes,full_GPU_supervisor_financial_terminal_binding_CPU_accepted=True,
  actual_CUDA=False,real_nvidia_smi_calls=0,real_sudo_calls=0,authoritative_ledger_written=False,GPU_submissions=0,new_DEV_inference=False,GPU_dispatch_ready=False)
 atomic_json(a.output,proof);print(json.dumps(dict(status=proof['status'],host=c['host'],wall_seconds=time.time()-start)))
if __name__=='__main__':main()
