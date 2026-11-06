"""Two-card successor identity, real exec handoff and complete control-chain CPU checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
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
    signal.alarm(300)
    started = time.time()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    registration = json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/n) == h for n, h in registration['payload_sha256'].items())
    sys.path[:0] = [str(args.stage/'src'), str(args.stage/'tests'), str(args.stage/'scripts')]
    rows = []
    for name, count in [('test_cara_budget_dispatch_r1', 15), ('test_cara_budget_prepare_r1', 9),
                        ('test_cara_budget_central_r1', 12), ('test_cara_budget_runner_binding_r1', 7),
                        ('test_cara_budget_dispatch_child_r1', 1),
                        ('test_cara_budget_lifecycle_capture_r1', 9), ('test_cara_budget_lifecycle_r1', 16),
                        ('test_cara_budget_host_guardian_r1', 13), ('test_cara_budget_supervisor_r1', 12),
                        ('test_cara_budget_complete_r1', 11)]:
        module = __import__(name)
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        rows.append(dict(module=name, tests_run=result.testsRun, failures=len(result.failures),
                         errors=len(result.errors), skipped=len(result.skipped),
                         Linux_observations=getattr(module,'OBSERVATIONS',[])))
        assert result.testsRun == count and result.wasSuccessful() and not result.skipped
    import test_cara_budget_dispatch_child_r1 as child
    assert len(child.OBSERVATIONS) == 1
    completed = subprocess.run([sys.executable, str(args.stage/'scripts/check_cara_budget_exec_handoff_cpu_r1.py'),
        '--original-stage', str(args.stage), '--candidate-runner', str(args.stage/'scripts/run_cara_budget_calibration_r1.py')],
        capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
    handoff = json.loads(completed.stdout)
    assert handoff['controls_passed'] == 8 and handoff['candidate_runner_sha256'] == sha(args.stage/'scripts/run_cara_budget_calibration_r1.py')
    proof = dict(status='TWO_CARD_SUCCESSOR_EXEC_HANDOFF_CONTROL_CHAIN_CPU_COMPLETE_NOT_GPU', host=args.host,
        started_unix=started, ended_unix=time.time(), controls=rows, tests_run=113, exec_handoff=handoff,
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
