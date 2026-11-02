"""Successor namespace/profile/full-readers CPU delta; no model or metric replay."""
import argparse
import os
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
from check_cara_source_lifecycle_fit_host_cpu_r1 import host_limits
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.cara_fast_fidelity_r1 import file_sha

TESTS=('test_cara_p1_successor_identity_r2','test_cara_source_lifecycle_p1_profile_quote_r1',
 'test_cara_source_lifecycle_p1_entry_r1','test_cara_source_lifecycle_p1_central_r1',
 'test_cara_source_lifecycle_p1_dispatch_r1.P1DispatchTests',
 'test_cara_source_lifecycle_p1_dispatch_r1.P1Memory50BoundaryTests.test_current50_admits_and49_refuses_without_changing_caps',
 'test_cara_source_lifecycle_p1_container_r1','test_cara_source_lifecycle_p1_capture_r1',
 'test_cara_source_lifecycle_p1_post_capture_r1','test_cara_source_lifecycle_p1_post_probe_packet_r1',
 'test_cara_source_lifecycle_p1_report_r1')+tuple(
 'test_cara_source_lifecycle_p1_result_bundle_r1.P1BundleTests.'+name for name in (
 'test_changed_original_file_or_FIT_plan_cannot_become_portable_figures',
 'test_complete_export_does_not_import_matplotlib_or_compute_metrics',
 'test_live_unknown_failed_or_changed_export_source_cannot_export_science',
 'test_wrong_capture_hash_cpu_mode_or_local_source_refuses_before_render'))


def probe(stage,output,bounds):
    reg=read_record(stage/'registration.json');started=time.time()
    assert sys.platform=='linux' and os.sched_getaffinity(0)=={26,27}
    assert all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(file_sha(stage.parents[1]/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(n) for n in TESTS))
    assert result.testsRun==56 and result.wasSuccessful() and not result.skipped
    create_record(output,dict(status='P1_SUCCESSOR_IDENTITY_FULL_READERS_CPU_PASS',CPU_fixture_only=True,
        source_revision=reg['parent_git_revision'],registration_sha256=file_sha(stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
        tests_run=result.testsRun,test_modules=list(TESTS),parent_bounds=bounds,
        parent_identity=bind_original_process(os.getpid()),started_unix=started,ended_unix=time.time(),
        original_metric_pairs_recomputed=0,old_experiments_replayed=False,actual_Cosmos_weights=False,
        actual_GPU_or_Docker_dispatch=False,GPU_authorized=False,GPU_submissions=0,ledger_written=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('probe',))
    parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();bounds=host_limits();identity=bind_original_process(os.getpid())
    create_record(args.stage/'host-start.json',dict(identity=identity,parent_bounds=bounds,started_unix=time.time()))
    error=None
    try:
        grant=args.stage/'host-dispatch-grant.json';deadline=time.monotonic()+30
        while not grant.exists() and time.monotonic()<deadline:time.sleep(.05)
        assert grant.exists() and read_record(grant)['identity']==identity
        probe(args.stage,args.output,bounds)
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught));raise
    finally:
        create_record(args.stage/'host-terminal.json',dict(identity=identity,ended_unix=time.time(),
            error=error,CPU_fixture_only=True,GPU_submissions=0,ledger_written=False))
