"""Affected P1 host-service lifetime in a bounded GPU-hidden Linux CPU entry."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest


def main():
    parser=argparse.ArgumentParser()
    for name in ('runtime','stage','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True)
    args=parser.parse_args()
    assert args.host=='two_card' and os.sched_getaffinity(0)=={26}
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert not args.output.exists()
    started=time.time()
    signal.alarm(600)
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg=json.loads((args.stage/'registration.json').read_bytes())
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(sha(args.runtime/n)==h for n,h in reg['runtime_source_sha256'].items())
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.stage/'tests')]
    scratch=args.stage/'CPU-scratch'
    scratch.mkdir()
    tempfile.tempdir=str(scratch)
    modules=[importlib.import_module(name) for name in (
        'test_cara_source_lifecycle_p1_service_r1','test_cara_source_lifecycle_p1_guardian_fit_r1',
        'test_cara_source_lifecycle_fit_broker_r1','test_cara_source_lifecycle_fit_host_cpu_r1',
        'test_cara_read_write_entry_r1')]
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in modules)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun==34 and not result.skipped
    observations=modules[1].OBSERVATIONS
    assert {r['scenario'] for r in observations}=={'success','start_failure','service_failure','GPU_failure','cleanup_unknown'}
    assert all(r['GPU_and_CPU_originals_ended'] and r['foreign_sentinel_preserved'] and r['no_replay'] for r in observations)
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    proof=dict(status='P1_ORIGINAL_GUARDIAN_FIT_SERVICE_LINUX_CPU_COMPONENT_PASS',host=args.host,
        started_unix=started,ended_unix=time.time(),source_revision=reg['parent_git_revision'],
        registration_sha256=sha(args.stage/'registration.json'),payload_sha256=reg['payload_sha256'],
        runtime_source_sha256=reg['runtime_source_sha256'],tests_run=result.testsRun,
        original_process_scenarios=observations,actual_CPU_affinity=[26],work_seconds=600,exit_seconds=60,
        actual_original_Linux_processes=True,internal_GPU_and_Docker_simulated=True,
        prior_algorithm_or_metric_work_repeated=False,actual_Cosmos_weights=False,
        actual_central_ledger_accessed=False,whole_GPU_entry_accepted=False,P1_GPU_authorized=False,
        GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as stream:
        json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=proof['status'],tests_run=result.testsRun,wall_seconds=time.time()-started)),flush=True)
    signal.alarm(60)


if __name__=='__main__':main()
