"""GPU-hidden combined B controls after changing the unique billing owner."""
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
    for key in ('runtime','stage','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--host',required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    signal.alarm(180)
    started=time.time()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert registration['host']==args.host and os.sched_getaffinity(0)=={27}
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert all(sha(args.stage/name)==expected for name,expected in registration['payload_sha256'].items())
    assert all(sha(args.runtime/name)==expected for name,expected in registration['runtime_source_sha256'].items())
    sys.path[:0]=[str(args.stage/name) for name in ('src','scripts','tests')]
    from test_cara_fast_b36_execution_r1 import BoundaryTests,SupervisorTests
    from test_cara_fast_b36_post_r1 import PostTests
    from test_cara_fast_b36_startup_r2 import StartupTests
    from test_cara_fast_b36_dispatch_r2 import DispatchTests
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(test)
        for test in (BoundaryTests,SupervisorTests,PostTests,StartupTests,DispatchTests))
    tests=unittest.TextTestRunner(verbosity=2).run(suite)
    assert tests.wasSuccessful() and not tests.skipped and tests.testsRun==22
    assert 'torch' not in sys.modules
    signal.alarm(30)
    proof=dict(status='FAST_B36_DISPATCH_AND_BILLING_CPU_R2_COMPLETE_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),tests_run=tests.testsRun,tests_skipped=0,
        registration_sha256=sha(args.stage/'registration.json'),payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],billing_clock_owner='HOST_GUARDIAN',
        pre_worker_failure_scenarios=['container_failure','busy','spawn_failure','budget','unknown','missing_credential'],
        unique_measured_allocation_bill_verified=True,missing_or_unknown_is_never_zero_cost=True,
        normal_supervisor_controls=6,post_controls=8,dispatch_controls=5,
        isolated_source_preparation_with_actual_pinned_runtime_verified=True,
        GPU_once_intent_and_no_relaunch_verified=True,CPU_once_dispatch_and_exact_receipt_recovery_verified=True,
        asset_digest_and_changed_stamp_refusal_verified=True,actual_model_assets_read=False,new_metric_computations=26,reused_accepted_A_metric_pairs=6,
        registered_scoring_positions=32,real_complete_A32_metadata_verified=True,original_A32_frozen_file_changed=False,
        real_OS_child_PID_start_ticks_inherited_FD_and_process_groups=True,
        external_GPU_and_Docker_observations_simulated=True,actual_Docker_GPU_command_executed=False,
        real_GPU_driver_called=False,real_mode_changes=0,torch_imported=False,model_weights_loaded=False,
        GPU_submissions=0,central_ledger_written=False,temporary_CPU_ledger_mutations_only=True,
        resource_bound=dict(cpus=1,memory_GiB=4,swap=False,cpuset=[27],work_seconds=180,exit_seconds=30),
        actual_CPU_affinity=sorted(os.sched_getaffinity(0)),GPU_authorized=False,GPU_dispatch_ready=False)
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=proof['status'],host=args.host,tests_run=tests.testsRun)),flush=True)


if __name__=='__main__':
    main()
