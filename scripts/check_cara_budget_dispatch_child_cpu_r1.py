"""Bounded two-card Linux CPU test of the actual dispatcher child boundary."""
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
    parser = argparse.ArgumentParser()
    for name in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert args.host == 'two_card' and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
    assert os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    assert Path('/proc/self').exists()
    signal.alarm(180)
    started = time.time()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    registration = json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/n) == h for n, h in registration['payload_sha256'].items())
    sys.path[:0] = [str(args.stage/'src'), str(args.stage/'tests'), str(args.stage/'scripts')]
    import test_cara_budget_dispatch_child_r1 as child
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(child))
    assert result.testsRun == 1 and result.wasSuccessful() and not result.skipped
    assert len(child.OBSERVATIONS) == 1
    proof = dict(status='ACTUAL_DISPATCH_CHILD_CPU_COMPONENT_COMPLETE_NOT_GPU', host=args.host,
        started_unix=started, ended_unix=time.time(), tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
        registration_sha256=sha(args.stage/'registration.json'),
        source_revision=registration['parent_git_revision'], observations=child.OBSERVATIONS,
        GPU_submissions=0, ledger_written=False, whole_GPU_card_accepted=False,
        real_Docker_GPU_lifecycle_exercised=False, actual_64GiB_storage_exercised=False)
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    signal.alarm(30)
    print(json.dumps(proof), flush=True)


if __name__ == '__main__':
    main()
