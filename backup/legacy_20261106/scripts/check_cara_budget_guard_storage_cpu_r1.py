"""Bounded guardian journal and storage integration on CPU fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest


def main():
    parser=argparse.ArgumentParser()
    for name in ('stage','runtime','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True);args=parser.parse_args()
    signal.alarm(120);started=time.time()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'tests')]
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    reg=json.loads((args.stage/'registration.json').read_text())
    assert not args.output.exists() and reg['host']==args.host
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(sha(args.runtime/n)==h for n,h in reg['runtime_source_sha256'].items())
    suite=unittest.TestSuite()
    for pattern in ('test_cara_budget_lifecycle_r1.py','test_cara_budget_lifecycle_capture_r1.py',
                    'test_cara_budget_guardian_journal_r1.py','test_cara_budget_storage_r1.py'):
        suite.addTests(unittest.defaultTestLoader.discover(str(args.stage/'tests'),pattern=pattern))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun==48 and not result.skipped
    proof=dict(status='GUARDIAN_STORAGE_LINUX_CPU_CONTROLS_COMPLETE_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),registration_sha256=sha(args.stage/'registration.json'),
        source_sha256=reg['payload_sha256'],tests_run=48,tests_skipped=0,lifecycle_controls=15,capture_controls=7,guardian_journal_controls=13,storage_controls=13,
        resource_bound=dict(cpus=1,memory_GiB=4,work_seconds=120,exit_seconds=30),
        original_GPU_processes_observed=False,Docker_metadata_mocked=True,temporary_fixture_ledger_only=True,
        production_guardian_witness_emitter_implemented=True,production_GPU_dispatch_bound=False,physical_filesystem_quota_verified=False,whole_GPU_card_accepted=False,
        GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    signal.alarm(30);print(json.dumps(dict(status=proof['status'],tests_run=48)),flush=True)


if __name__=='__main__':main()
