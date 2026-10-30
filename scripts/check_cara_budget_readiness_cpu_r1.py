"""Bounded Linux CPU regression; no model, GPU or production ledger access."""
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
    registration = json.loads((args.stage/'registration.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert all(sha(args.stage/name) == expected for name, expected in registration['payload_sha256'].items())
    sys.path[:0] = [str(args.stage/'src'), str(args.stage/'tests')]
    rows = []
    for name, count in (('test_cara_budget_context_readiness_r1', 1),
                        ('test_cara_budget_supervisor_r1', 12),
                        ('test_cara_budget_host_guardian_r1', 13)):
        module = __import__(name)
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        rows.append(dict(module=name, tests_run=result.testsRun, failures=len(result.failures),
                         errors=len(result.errors), skipped=len(result.skipped)))
        assert result.testsRun == count and result.wasSuccessful() and not result.skipped
    proof = dict(status='READINESS_AND_ORIGINAL_LINUX_CHILD_CONTROLS_CPU_ONLY', host=args.host,
                 started_unix=started, ended_unix=time.time(), controls=rows, tests_run=26,
                 registration_sha256=sha(args.stage/'registration.json'),
                 source_revision=registration['parent_git_revision'], GPU_submissions=0,
                 ledger_written=False, complete112_numeric_matrix_exercised=False)
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    signal.alarm(60)
    print(json.dumps(proof), flush=True)


if __name__ == '__main__':
    main()
