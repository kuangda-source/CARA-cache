#!/usr/bin/env python3
"""Build C1 scope/quote and verify its CPU pipeline; no server or GPU transport."""
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'tests')]
from wcomr.cara_source_coverage_card_r1 import build,quote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory',type=Path,required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True,exist_ok=False)
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['NVIDIA_VISIBLE_DEVICES'] = 'void'
    import torch
    def forbidden(*args,**kwargs):
        raise RuntimeError('C1 CPU preparation forbids CUDA initialization and downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    started = time.monotonic()
    refs = dict(parent='plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json',
        pools='plans/cara_next_stage_20261103/source_coverage/CPU_CANDIDATE_POOLS_R4.json',
        summary='reports/cara_v1_P1_successor_original_algorithm_summary_r1_20261103.json',
        analysis='reports/cara_v1_P1_successor_original_complete_analysis_r1_20261103.json')
    load = lambda path:json.loads((ROOT/path).read_bytes())
    inputs = {k:load(p) for k,p in refs.items()}
    sha = lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if sha(ROOT/refs['summary']) != inputs['analysis']['algorithm_summary_sha256']:
        raise ValueError('Measured history differs from the original accepted summary')
    card = build(inputs['parent'],inputs['pools'])
    price = quote(card,inputs['summary'],inputs['analysis'])
    price['evidence_sha256'] = {p:sha(ROOT/p) for p in refs.values()}
    modules = [__import__(name) for name in ('test_cara_source_coverage_card_r1',
        'test_cara_source_coverage_r1','test_cara_source_lifecycle_p1_collection_r1')]
    log = io.StringIO()
    tested = unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules))
    profile = dict(schema='CARA_SOURCE_COVERAGE_C1_EXECUTION_PROFILE_DRAFT_R1',
        scope_sha256=card['scope_sha256'],host='two_card',
        gpu_uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704',
        proposed_hard_GPUh=price['proposed_hard_GPUh'],stop_release_reserve_seconds=600,
        thermal_stop_C=90,GPU_cpus='24,25',GPU_memory_GiB=40,
        initial_host_MemAvailable_GiB=50,internal_CPU_cpus='26,27',internal_CPU_memory_GiB=8,
        internal_CPU_fresh_MemAvailable_GiB=12,swap=False,network='none',
        output_volume_GiB=80,independent_journal_MiB=48,minimum_host_free_before_provision_GiB=96,
        lifecycle='REUSE_ORIGINAL_GUARDIAN_ONCE_ONLY_INTENT_RELEASE_AND_UNIQUE_BILLING_WITH_NEW_C1_BINDING',
        monitor_plan='AT_ACTUAL_START_QUARTER_HALF_AND_TERMINAL_SAME_THREAD_HEARTBEATS',
        new_GPU_authority=False,new_central_ledger_permission=False,
        four_card_experiments=False,central_cap_increase_planned=False,
        old_16_5_GPUh_liability_preserved=True,protected_inputs_accessed=False)
    sources = ['scripts/prepare_cara_source_coverage_c1_r1.py',
        'src/wcomr/cara_source_coverage_card_r1.py','src/wcomr/cara_source_coverage_collection_r1.py',
        'src/wcomr/cara_source_coverage_r1.py','tests/test_cara_source_coverage_card_r1.py',
        'tests/test_cara_source_coverage_r1.py','tests/test_cara_source_lifecycle_p1_collection_r1.py',
        'src/wcomr/cara_source_lifecycle_p1_collection_r1.py',
        'src/wcomr/cara_source_lifecycle_p1_requests_r1.py','src/wcomr/cara_source_lifecycle_p1_runner_r1.py']
    proof = dict(schema='CARA_SOURCE_COVERAGE_C1_CPU_PREPARATION_R1',
        status='CPU_ACCEPTED_PRODUCTION_BINDING_PENDING' if tested.wasSuccessful() else 'CPU_FAILED',
        scope_sha256=card['scope_sha256'],tests=tested.testsRun,failures=len(tested.failures),
        errors=len(tested.errors),skipped=len(tested.skipped),test_log=log.getvalue(),
        ended_UTC=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-started,
        system=platform.system(),machine=platform.machine(),interpreter=sys.version,
        source_sha256={p:sha(ROOT/p) for p in sources},
        input_sha256={p:sha(ROOT/p) for p in refs.values()},
        C1_pipeline_metrics=modules[0].METRICS,original_tiny_execution_metrics=modules[1].METRICS,
        actual_Cosmos_weights=False,actual_video_metric_pairs=0,CUDA_initialized=torch.cuda.is_initialized(),
        whole_GPU_entry_accepted=False,production_CPU_and_dispatch_binding_accepted=False,
        GPU_submissions=0,ledger_written=False)
    for name,value in [('C1_MANIFEST_R1.json',card),('C1_WHOLE_QUOTE_R1.json',price),
                       ('C1_EXECUTION_PROFILE_DRAFT_R1.json',profile),('C1_CPU_PROOF_R1.json',proof)]:
        with (args.output_directory/name).open('x') as out:
            out.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=proof['status'],tests=tested.testsRun,
        forecast_GPUh=price['forecast_GPUh'],proposed_hard_GPUh=price['proposed_hard_GPUh'],
        metrics=proof['C1_pipeline_metrics']),indent=2))
    if not tested.wasSuccessful():
        print(log.getvalue())
        raise SystemExit(1)


if __name__ == '__main__':
    main()
