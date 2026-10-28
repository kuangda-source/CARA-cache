"""Actual Linux FD/child/container-argument controls with simulated GPU I/O."""
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
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/name)==expected for name,expected in registration['payload_sha256'].items())
    assert all(sha(args.runtime/name)==expected for name,expected in registration['runtime_source_sha256'].items())
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    sys.path[:0]=[str(args.stage/name) for name in ('src','scripts','tests')]
    import test_cara_fast_execution_r2
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_fast_execution_r2))
    assert tests.wasSuccessful() and not tests.skipped
    signal.alarm(30)
    proof=dict(status='FAST_A32_ORCHESTRATION_CPU_CONTROL_COMPLETE_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),tests_run=tests.testsRun,tests_skipped=0,
        registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=registration['payload_sha256'],runtime_source_sha256=registration['runtime_source_sha256'],
        external_GPU_observations_simulated=True,real_OS_FD_child_and_process_groups=True,
        actual_Docker_GPU_command_executed=False,real_GPU_driver_called=False,
        actual_model_constructor_executed=False,model_weights_loaded=False,
        new_GPU_submissions=0,central_ledger_written=False,real_mode_changes=0,
        temporary_CPU_ledger_mutations_only=True,actual_CPU_bound=dict(cpus=1,memory_GiB=4,work_seconds=180,exit_seconds=30),
        production_GPU_authorized=False)
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2)
        handle.write('\n')
    print(json.dumps(dict(status=proof['status'],host=args.host,tests_run=tests.testsRun)),flush=True)


if __name__=='__main__':
    main()
