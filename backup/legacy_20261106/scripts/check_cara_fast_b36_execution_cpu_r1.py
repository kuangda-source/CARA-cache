"""Bounded Linux control of B's new outer boundary; no model or metric execution."""
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
    import test_cara_fast_b36_execution_r1
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_fast_b36_execution_r1))
    assert tests.wasSuccessful() and not tests.skipped and tests.testsRun==7
    assert 'torch' not in sys.modules, 'This affected-path control must not load any model library'
    signal.alarm(30)
    proof=dict(status='FAST_B36_OUTER_EXECUTION_CPU_COMPLETE_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),tests_run=tests.testsRun,tests_skipped=0,
        registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=registration['payload_sha256'],runtime_source_sha256=registration['runtime_source_sha256'],
        real_complete_A32_metadata_verified=True,original_A32_frozen_file_changed=False,
        real_OS_child_PID_start_ticks_inherited_FD_and_process_groups=True,
        supervisor_scenarios=['complete','runner_failure','partial','thermal','budget','foreign_context'],
        external_GPU_observations_simulated=True,actual_Docker_GPU_command_executed=False,
        real_GPU_driver_called=False,real_mode_changes=0,torch_imported=False,model_weights_loaded=False,
        GPU_submissions=0,central_ledger_written=False,temporary_CPU_ledger_mutations_only=True,
        resource_bound=dict(cpus=1,memory_GiB=4,swap=False,cpuset=[27],work_seconds=180,exit_seconds=30),
        actual_CPU_affinity=sorted(os.sched_getaffinity(0)),GPU_authorized=False,GPU_dispatch_ready=False)
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=proof['status'],host=args.host,tests_run=tests.testsRun)),flush=True)


if __name__=='__main__':
    main()
