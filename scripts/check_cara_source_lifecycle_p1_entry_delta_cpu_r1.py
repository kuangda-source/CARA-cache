"""Bounded Linux CPU checks for new report/RPC/container entry paths only."""
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

TESTS=('test_cara_source_lifecycle_p1_report_r1','test_cara_source_lifecycle_p1_figures_r1',
    'test_cara_source_lifecycle_p1_settlement_r1','test_cara_source_lifecycle_p1_control_r1',
    'test_cara_source_lifecycle_p1_container_r1','test_cara_source_lifecycle_p1_supervisor_worker_r1')


def probe(stage,output,bounds):
    reg=read_record(stage/'registration.json');project=stage.parents[1];started=time.time()
    assert not output.exists() and reg['host']=='two_card'
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(file_sha(project/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
    tested=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(n) for n in TESTS))
    assert tested.testsRun==26 and tested.wasSuccessful() and not tested.skipped
    # A separate fresh metadata fixture supplies retained render previews; there
    # is no metric, generative model, GPU container or remote ledger callback.
    import test_cara_source_lifecycle_p1_figures_r1 as figures_fixture
    figures_fixture.P1FiguresTests.setUpClass()
    case=figures_fixture.P1FiguresTests('test_real_png_pdf_csv_and_idempotent_original_export')
    case._testMethodName='retained_CPU_preview';case.setUp()
    try:
        rendered=case.render();preview=stage/'figure-preview';preview.mkdir()
        for name in ('quality-latency.png','complete93-curves.png'):
            shutil.copyfile(Path(rendered['directory'])/name,preview/name)
        previews={p.name:file_sha(p) for p in preview.iterdir()}
    finally:
        case.doCleanups();figures_fixture.P1FiguresTests.tearDownClass()
    proof=dict(status='ACTUAL_P1_ENTRY_REPORT_RPC_LINUX_CPU_DELTA26_PASS',CPU_fixture_only=True,
        source_revision=reg['parent_git_revision'],registration_sha256=file_sha(stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
        host='two_card',started_unix=started,ended_unix=time.time(),parent_bounds=bounds,
        parent_identity=bind_original_process(os.getpid()),tests_run=26,test_modules=list(TESTS),
        report52_analysis_once_freeze_controls=5,actual_figures_and_CSV_controls=3,
        simulated_central_settlement_controls=5,simulated_RPC_controls=5,
        simulated_container_supervisor_entry_controls=8,
        original_liveness_refresh_keeps_analysis_and_freeze_bytes=True,
        actual_PNG_PDF_CSV_rendered=True,preview_sha256=previews,
        original_metric_pairs_recomputed=0,old_component_experiments_replayed=False,
        actual_Cosmos_weights=False,real_V1_video=False,actual_GPU_Docker_started=False,
        real_four_card_accessed=False,real_central_ledger_read=False,
        whole_GPU_entry_accepted=False,P1_GPU_authorized=False,GPU_submissions=0,ledger_written=False)
    assert all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    create_record(output,proof)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('role',choices=('probe',))
    parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();bounds=host_limits();identity=bind_original_process(os.getpid())
    create_record(args.stage/'host-start.json',dict(identity=identity,parent_bounds=bounds,
        started_unix=time.time(),CPU_fixture_only=True,GPU_submissions=0))
    error=None
    try:
        deadline=time.monotonic()+30;grant=args.stage/'host-dispatch-grant.json'
        while not grant.exists() and time.monotonic()<deadline:time.sleep(.05)
        assert grant.exists() and read_record(grant)['identity']==identity
        probe(args.stage,args.output,bounds)
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught));raise
    finally:
        create_record(args.stage/'host-terminal.json',dict(identity=identity,ended_unix=time.time(),
            error=error,CPU_fixture_only=True,GPU_submissions=0,ledger_written=False))


if __name__=='__main__':
    main()
