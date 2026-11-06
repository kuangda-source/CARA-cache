"""New Linux export/profile/source-parent delta; no old metrics or model replay."""
import argparse
import os
from pathlib import Path
import shutil
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]

from check_cara_source_lifecycle_fit_host_cpu_r1 import host_limits
from wcomr.cara_budget_original_handles_r1 import bind_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.cara_fast_fidelity_r1 import file_sha

BUNDLE='test_cara_source_lifecycle_p1_result_bundle_r1.P1BundleTests.'
TESTS=tuple(BUNDLE+n for n in (
    'test_complete_export_does_not_import_matplotlib_or_compute_metrics',
    'test_wrong_capture_hash_cpu_mode_or_local_source_refuses_before_render',
    'test_changed_original_file_or_FIT_plan_cannot_become_portable_figures',
    'test_live_unknown_failed_or_changed_export_source_cannot_export_science'))+(
    'test_cara_source_lifecycle_p1_profile_quote_r1',
    'test_cara_source_lifecycle_source_parent_r1',
    'test_cara_source_lifecycle_p1_entry_r1.P1ProductionEntryTests.test_published_unset_hard_limit_cannot_pass_admission')


def probe(stage,output,bounds):
    reg=read_record(stage/'registration.json');project=stage.parents[1];started=time.time()
    assert not output.exists() and reg['host']=='two_card'
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(file_sha(project/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
    tested=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(n) for n in TESTS))
    assert tested.testsRun==13 and tested.wasSuccessful() and not tested.skipped
    # Preserve one fresh metadata-only Linux export so local plotting can consume
    # its actual original bytes and independent export SHA after this CPU ends.
    import test_cara_source_lifecycle_p1_result_bundle_r1 as fixture
    fixture.P1BundleTests.setUpClass()
    case=fixture.P1BundleTests('test_complete_export_does_not_import_matplotlib_or_compute_metrics')
    case._testMethodName='retained_original_Linux_export';case.setUp()
    try:
        original=case.export();path=stage/'portable-result-bundle.json'
        shutil.copyfile(original['bundle_path'],path)
        assert file_sha(path)==original['bundle_sha256']
    finally:
        case.doCleanups();fixture.P1BundleTests.tearDownClass()
    proof=dict(status='ACTUAL_P1_FINAL_EXPORT_PROFILE_PARENT_LINUX_CPU13_PASS',CPU_fixture_only=True,
        source_revision=reg['parent_git_revision'],registration_sha256=file_sha(stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],host='two_card',
        started_unix=started,ended_unix=time.time(),parent_bounds=bounds,parent_identity=bind_original_process(os.getpid()),
        tests_run=13,test_modules=list(TESTS),portable_export_controls=4,final_profile_quote_controls=3,
        source_parent_controls=5,changed_null_limit_control=1,portable_original_export_receipt=original,
        portable_result_bundle_path=str(path),portable_result_bundle_sha256=file_sha(path),
        portable_result_bundle_bytes=path.stat().st_size,actual_PNG_rendered_on_Linux=False,
        local_render_source_sha256={n:file_sha(stage/n) for n in fixture.bundle.SOURCES},
        original_metric_pairs_recomputed=0,old_component_experiments_replayed=False,actual_Cosmos_weights=False,
        real_V1_video=False,whole_GPU_entry_accepted=False,P1_GPU_authorized=False,
        real_four_card_accessed=False,real_central_ledger_read=False,GPU_submissions=0,ledger_written=False)
    assert all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    create_record(output,proof)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('role',choices=('probe',))
    parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    bounds=host_limits();identity=bind_original_process(os.getpid())
    create_record(args.stage/'host-start.json',dict(identity=identity,parent_bounds=bounds,started_unix=time.time(),CPU_fixture_only=True,GPU_submissions=0))
    error=None
    try:
        deadline=time.monotonic()+30;grant=args.stage/'host-dispatch-grant.json'
        while not grant.exists() and time.monotonic()<deadline:time.sleep(.05)
        assert grant.exists() and read_record(grant)['identity']==identity
        probe(args.stage,args.output,bounds)
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught));raise
    finally:
        create_record(args.stage/'host-terminal.json',dict(identity=identity,ended_unix=time.time(),error=error,CPU_fixture_only=True,GPU_submissions=0,ledger_written=False))
