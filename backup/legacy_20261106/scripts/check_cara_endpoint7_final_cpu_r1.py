"""Final actual Linux command/analysis/render checks; synthetic metadata, no GPU or scoring."""
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
 import test_cara_endpoint7_final_binding_r1 as binding
 import test_cara_endpoint7_analysis_r1 as analysis
 import test_cara_endpoint7_figures_r1 as figures
 suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in (binding,analysis,figures))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 assert result.testsRun==16 and result.wasSuccessful() and not result.skipped
 # Persist one labeled fixture export as evidence of the actual Linux renderer.
 from wcomr.cara_endpoint7_figures_r1 import render
 fixture=analysis.Analysis();fixture.setUp()
 try:
  report=fixture.run_analysis();directory=a.stage/'CPU-analysis-export';export=render(report,directory,cpu_validation=True)
 finally:fixture.doCleanups()
 proof=dict(status='ENDPOINT7_FINAL_AFFECTED_BINDING_ANALYSIS_CPU_PASS',host=a.host,
  started_unix=started,ended_unix=time.time(),source_revision=reg['parent_git_revision'],
  registration_sha256=sha(a.stage/'registration.json'),payload_sha256=reg['payload_sha256'],
  runtime_source_sha256=reg['runtime_source_sha256'],actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
  tests_run=result.testsRun,dispatch_storage_controls=8,analysis_controls=5,figure_controls=3,
  fixture_export={name:sha(directory/name) for name in export['files']},
  original_numeric46_rerun=False,metric_computation=False,synthetic_metadata_only=True,
  actual_GPU_or_Docker_executed=False,actual_storage_provisioned=False,whole_card_CPU_accepted=False,
  GPU_submissions=0,ledger_written=False,work_seconds=300,exit_seconds=60)
 signal.alarm(60)
 with a.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)
if __name__=='__main__':main()
