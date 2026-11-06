"""Target Linux CPU validation of the already tested isolated Euler adapter."""
import argparse,hashlib,json,os,signal,sys,time,unittest
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for name in ('runtime','stage','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--host',required=True);a=p.parse_args()
 assert a.host=='two_card' and os.sched_getaffinity(0)=={26} and not a.output.exists()
 assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
 signal.alarm(300);started=time.time();sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
 reg=json.loads((a.stage/'registration.json').read_text())
 assert all(sha(a.stage/p)==h for p,h in reg['payload_sha256'].items())
 assert all(sha(a.runtime/p)==h for p,h in reg['runtime_source_sha256'].items())
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 import test_cara_euler_sampler_r1 as tests
 import check_cara_euler_sampler_r1 as pipeline
 from wcomr.cara_euler_protocol_r1 import reconstructed_grid
 contract=json.loads((a.stage/'plans/cara_next_stage_20261101/euler/sigma_grid_and_call_contract.json').read_text())
 assert contract['E_PAPER_reconstruction']==reconstructed_grid(35)
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
 assert result.testsRun==5 and result.wasSuccessful() and not result.skipped
 actual=pipeline.main(a.runtime)
 assert len(actual['checks'])==2 and sum(r['complete_paths'] for r in actual['checks'])==8
 proof=dict(status='EULER35_SAMPLER_LINUX_TINY_CPU_PASS_NOT_GPU',host=a.host,
  started_unix=started,ended_unix=time.time(),source_revision=reg['parent_git_revision'],
  registration_sha256=sha(a.stage/'registration.json'),payload_sha256=reg['payload_sha256'],
  runtime_source_sha256=reg['runtime_source_sha256'],actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
  tests_run=result.testsRun,actual=actual,complete_tiny_paths=8,total_updates=280,total_CFG_calls=560,
  actual_GPU_or_Docker_GPU_executed=False,model_weights_loaded=False,old_experiments_rerun=False,
  GPU_submissions=0,ledger_written=False,work_seconds=300,exit_seconds=60)
 signal.alarm(60)
 with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)
if __name__=='__main__':main()
