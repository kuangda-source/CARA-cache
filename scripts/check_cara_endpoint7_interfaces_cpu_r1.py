"""Bounded Linux production interface checks with complete93-frame synthetic media."""
import argparse,hashlib,json,os,signal,sys,time,unittest
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for name in ('runtime','stage','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--host',required=True);a=p.parse_args()
 assert a.host=='two_card' and os.sched_getaffinity(0)=={26} and not a.output.exists()
 assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
 def interrupted(signum,frame):raise TimeoutError('Original interface CPU deadline or stop signal '+str(signum))
 signal.signal(signal.SIGALRM,interrupted);signal.signal(signal.SIGTERM,interrupted);signal.alarm(1200)
 started=time.time();sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
 reg=json.loads((a.stage/'registration.json').read_text())
 assert reg['host']==a.host and all(sha(a.stage/p)==h for p,h in reg['payload_sha256'].items())
 assert all(sha(a.runtime/p)==h for p,h in reg['runtime_source_sha256'].items())
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 import test_cara_endpoint7_interfaces_r1 as tests
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
 assert result.wasSuccessful() and not result.skipped and result.testsRun==9
 from check_cara_s_endpoint_scoring_cli_r1 import run
 actual=run(a.stage/'CPU-interface-checks',a.stage,deadline=time.monotonic()+1050,endpoint7=True)
 assert actual['new_synthetic_pairs_scored']==16 and actual['failure_fixture_pairs_scored']==1
 assert len(actual['cases'])==1 and actual['cases'][0]['logical_positions']==28
 proof=dict(status='ENDPOINT7_ACTUAL_INTERFACE_AND_SCORE_CPU_COMPLETE_NOT_WHOLE_CARD',host=a.host,
  started_unix=started,ended_unix=time.time(),source_revision=reg['parent_git_revision'],
  registration_sha256=sha(a.stage/'registration.json'),payload_sha256=reg['payload_sha256'],
  runtime_source_sha256=reg['runtime_source_sha256'],actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
  metadata_controls=result.testsRun,actual=actual,synthetic_lifecycle_and_historical_scores=True,
  temporary_ledger_only=True,original_numeric46_rerun=False,whole_GPU_card_accepted=False,
  active_experiment_outputs_read=False,GPU_submissions=0,ledger_written=False,work_seconds=1200,exit_seconds=60)
 signal.alarm(60)
 with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)
if __name__=='__main__':main()
