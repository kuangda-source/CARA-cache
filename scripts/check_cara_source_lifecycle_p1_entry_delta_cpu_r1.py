"""Bounded Linux CPU checks for new report/RPC/container entry paths only."""
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

TESTS=('test_cara_source_lifecycle_p1_report_r1',
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
    assert tested.testsRun==23 and tested.wasSuccessful() and not tested.skipped
    # Plotting uses the existing local plotting runtime. Do not install or alter
    # the production model/metric Python environment for a presentation backend.
    local_ref='reports/cara_v1_P1_entry_delta_packaged_local_CPU_r2_20261102.json'
    local=read_record(stage/local_ref)
    assert local['status']=='EXACT_REGISTERED_P1_ENTRY_DELTA_PAYLOAD_ISOLATED_LOCAL26_PASS' and local['tests_run']==26
    figure_sources=('src/wcomr/cara_source_lifecycle_p1_report_r1.py',
        'scripts/analyze_cara_source_lifecycle_p1_complete_r1.py',
        'src/wcomr/cara_source_lifecycle_p1_analysis_r1.py',
        'src/wcomr/cara_source_lifecycle_p1_figures_r1.py',
        'scripts/render_cara_source_lifecycle_p1_figures_r1.py',
        'tests/test_cara_source_lifecycle_p1_figures_r1.py',
        'tests/test_cara_source_lifecycle_p1_report_r1.py')
    assert all(local['payload_sha256'][n]==reg['payload_sha256'][n]==file_sha(stage/n) for n in figure_sources)
    proof=dict(status='ACTUAL_P1_ENTRY_REPORT_RPC_LINUX_CPU_DELTA23_PASS',CPU_fixture_only=True,
        source_revision=reg['parent_git_revision'],registration_sha256=file_sha(stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
        host='two_card',started_unix=started,ended_unix=time.time(),parent_bounds=bounds,
        parent_identity=bind_original_process(os.getpid()),tests_run=23,test_modules=list(TESTS),
        report52_analysis_once_freeze_controls=5,source_bound_local_figures_and_CSV_controls_reused=3,
        local_figures_CPU_ref=local_ref,local_figures_CPU_sha256=file_sha(stage/local_ref),
        local_figure_source_sha256={n:file_sha(stage/n) for n in figure_sources},
        simulated_central_settlement_controls=5,simulated_RPC_controls=5,
        simulated_container_supervisor_entry_controls=8,
        original_liveness_refresh_keeps_analysis_and_freeze_bytes=True,
        actual_PNG_PDF_CSV_rendered_in_this_Linux_job=False,
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
