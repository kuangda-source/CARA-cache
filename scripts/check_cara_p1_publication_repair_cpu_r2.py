"""New Linux metadata-only publication/RPC and affected-boundary CPU checks."""
import argparse
import os
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts'), str(ROOT/'tests')]

from check_cara_source_lifecycle_fit_host_cpu_r1 import host_limits
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record, read_record
from wcomr.cara_fast_fidelity_r1 import file_sha

TESTS = ('test_cara_p1_publication_repair_r2', 'test_cara_source_lifecycle_fit_broker_r1',
         'test_cara_source_lifecycle_p1_control_r1', 'test_cara_source_lifecycle_p1_service_r1',
         'test_cara_source_lifecycle_p1_guardian_fit_r1')


def probe(stage, output, bounds):
    reg = read_record(stage/'registration.json')
    started = time.time()
    assert not output.exists() and reg['host'] == 'two_card'
    assert all(file_sha(stage/n) == h for n,h in reg['payload_sha256'].items())
    assert all(file_sha(stage.parents[1]/'runtime'/n) == h for n,h in reg['runtime_source_sha256'].items())
    assert sys.platform == 'linux' and os.sched_getaffinity(0) == {26,27}
    tested = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(name) for name in TESTS))
    assert tested.testsRun == 33 and tested.wasSuccessful() and not tested.skipped
    proof = dict(status='P1_PUBLICATION_RPC_REPAIR_LINUX_CPU33_PASS',CPU_fixture_only=True,
        source_revision=reg['parent_git_revision'],registration_sha256=file_sha(stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
        started_unix=started,ended_unix=time.time(),parent_bounds=bounds,
        parent_identity=bind_original_process(os.getpid()),tests_run=33,test_modules=list(TESTS),
        new_publication_and_RPC_controls=8,affected_broker_controls=10,
        permission_service_guardian_controls=15,actual_Linux_original_process_identity_used=True,
        actual_new_Docker_or_GPU_dispatch=False,real_metric_pairs_computed=0,
        old_experiments_replayed=False,old_partial_scientific_results_read=False,
        GPU_authorized=False,real_four_card_accessed=False,GPU_submissions=0,ledger_written=False)
    create_record(output, proof)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('probe',))
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bounds = host_limits()
    identity = bind_original_process(os.getpid())
    create_record(args.stage/'host-start.json', dict(identity=identity,parent_bounds=bounds,started_unix=time.time()))
    error = None
    try:
        grant = args.stage/'host-dispatch-grant.json'
        deadline = time.monotonic()+30
        while not grant.exists() and time.monotonic()<deadline:
            time.sleep(.05)
        assert grant.exists() and read_record(grant)['identity'] == identity
        probe(args.stage,args.output,bounds)
    except BaseException as caught:
        error = dict(type=type(caught).__name__,message=str(caught))
        raise
    finally:
        create_record(args.stage/'host-terminal.json', dict(identity=identity,ended_unix=time.time(),
            error=error,CPU_fixture_only=True,GPU_submissions=0,ledger_written=False))
