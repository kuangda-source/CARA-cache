"""Full Q1 control chain plus actual 48MiB journals and production actor calls."""
import io
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
import unittest

import check_cara_sq_q1_control_cpu_r1 as previous

ROOT=Path(__file__).resolve().parents[1]
CONTROL_SCOPE='plans/cara_next_stage_20261028/sq/Q1_CONTROL_JOURNAL_CPU_R1.json'


def main():
    index=sys.argv.index('--output')+1;output=Path(sys.argv[index]);prior=output.with_suffix('.prior.json')
    if output.exists() or prior.exists():raise FileExistsError('Retain original journal CPU attempt')
    started,cpu=time.monotonic(),time.process_time();children_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    sys.argv[index]=str(prior)
    try:previous.main()
    finally:sys.argv[index]=str(output)
    control=json.loads((ROOT/CONTROL_SCOPE).read_text())
    original=json.loads(prior.read_text());core=original['core_result'];wrapper=original['wrapper_checks']
    if core['tests']!=51 or wrapper['tests']!=15 or core['skipped'] or wrapper['skipped']:
        raise ValueError('The original complete51+15 control denominator changed')
    from test_sq_gpu_allocation_r1 import EVENTS as allocation_events
    before=len(allocation_events)
    if before!=14:raise ValueError('Original fourteen allocation CPU children required')
    log=io.StringIO();suite=unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromName('test_sq_control_storage_r1'),
        unittest.defaultTestLoader.loadTestsFromName('test_sq_journal_allocation_r1')])
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tests.wasSuccessful() or tests.skipped or tests.testsRun!=16:raise ValueError(log.getvalue())
    from test_sq_control_storage_r1 import EVENTS as journal_events
    children=[r['process'] for r in allocation_events]+[r['process'] for r in journal_events]
    if len(allocation_events)!=16 or len(journal_events)!=2 or any(c.poll() is None for c in children):
        raise ValueError('Every original and real-journal CPU child must be terminal')
    import torch
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.sq_q1_spec_r1 import EXECUTION_CRITICAL
    if torch.cuda.is_initialized() or platform.system()!='Linux':raise ValueError('Actual GPU-hidden Linux control run required')
    child_after=resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu=child_after.ru_utime+child_after.ru_stime-children_before.ru_utime-children_before.ru_stime
    result=dict(status='SQ_REAL_CONTROL_JOURNAL_FULL_Q1_CPU_PASS_NOT_GPU_AUTHORITY',
        control_scope=control,prior_control_result=original,prior_control_result_sha256=sha(prior),
        original_core_controls=51,original_wrapper_controls=15,real_journal_controls=12,
        real_actor_journal_controls=4,total_controls=82,errors=len(tests.errors),failures=len(tests.failures),skipped=0,
        journal_actor_log=log.getvalue(),actual_48MiB_production_journals=True,
        actual_production_actor_persist_calls=True,actual_concurrent_journal_processes=2,
        enumerated_allocation_CPU_children=16,enumerated_journal_CPU_children=2,
        all_enumerated_CPU_children_exited=True,child_exit_codes=[c.returncode for c in children],
        GPU_mode_container_and_mount_observations_synthetic=True,temporary_fixture_ledgers_only=True,
        Q1_numerical_scope_unchanged=True,actual_B1_replay=False,actual_Cosmos_weights=False,
        original_C_CUDA_parity_accepted=False,actual_GPU_or_SSD_scope_accepted=False,CUDA_initialized=False,
        critical_source_sha256={n:sha(ROOT/n) for n in EXECUTION_CRITICAL},
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        reaped_child_CPU_seconds=child_cpu,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])


if __name__=='__main__':main()
