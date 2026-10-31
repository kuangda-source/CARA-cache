"""Actual temporary-ledger transactions, never the production central ledger."""
import argparse,hashlib,json,os,signal,sys,time,unittest
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for name in ('runtime','stage','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--host',required=True);a=p.parse_args()
 assert a.host=='two_card' and os.sched_getaffinity(0)=={26} and not a.output.exists()
 assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
 signal.alarm(180);started=time.time();sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
 reg=json.loads((a.stage/'registration.json').read_text())
 assert all(sha(a.stage/p)==h for p,h in reg['payload_sha256'].items())
 assert all(sha(a.runtime/p)==h for p,h in reg['runtime_source_sha256'].items())
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests')]
 import test_cara_endpoint7_central_r1 as central
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(central))
 assert r.testsRun==13 and r.wasSuccessful() and not r.skipped
 proof=dict(status='ENDPOINT7_CENTRAL_TEMPORARY_LEDGER_CPU_PASS',host=a.host,
  started_unix=started,ended_unix=time.time(),source_revision=reg['parent_git_revision'],
  registration_sha256=sha(a.stage/'registration.json'),payload_sha256=reg['payload_sha256'],
  runtime_source_sha256=reg['runtime_source_sha256'],actual_CPU_affinity=sorted(os.sched_getaffinity(0)),tests_run=r.testsRun,
  temporary_ledger_only=True,production_ledger_accessed=False,four_card_accessed=False,
  GPU_submissions=0,ledger_written=False,work_seconds=180,exit_seconds=60)
 signal.alarm(60)
 with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)
if __name__=='__main__':main()
