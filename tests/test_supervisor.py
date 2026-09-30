"""Exercise real subprocess/receipt/budget behavior with a fake GPU executable.

No nvidia-smi on the host, model, or GPU is used by these tests.
"""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/supervise_f1.py'


def fixture(tmp_path, delay, cap=1):
    project = tmp_path / 'project'
    (project / 'reports').mkdir(parents=True)
    (project / 'reports/budget.json').write_text(json.dumps({
        'cap_gpu_hours': cap, 'used_gpu_hours': 0, 'gpu_jobs_launched': 0}))
    runtime = tmp_path / 'runtime'; runtime.mkdir()
    binary = tmp_path / 'bin'; binary.mkdir()
    nvidia = binary / 'nvidia-smi'
    nvidia.write_text('#!/usr/bin/env python3\nimport sys\n'
                      'if any("query-gpu=" in arg for arg in sys.argv): print("24, 0")\n')
    nvidia.chmod(0o755)
    child = binary / 'fake-python'
    child.write_text('#!/usr/bin/env python3\nimport time\ntime.sleep(%r)\n' % delay)
    child.chmod(0o755)
    output = tmp_path / 'output'
    command = [sys.executable, str(SCRIPT), '--project', str(project), '--runtime', str(runtime),
               '--python', str(child), '--gpu-uuid', 'GPU-FAKE', '--output', str(output)]
    env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'])
    # GNU timeout is required by the Linux runner. On macOS a small test-only
    # shim executes the child; the budget-stop test exercises the supervisor.
    timeout = binary / 'timeout'
    timeout.write_text('#!/usr/bin/env python3\nimport os,sys\nos.execv(sys.argv[3],sys.argv[3:])\n')
    timeout.chmod(0o755)
    return project, output, command, env


def test_serial_arms_have_exit_receipts_and_accounting(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=.02)
    subprocess.run(cmd, env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((output / 'supervisor.json').read_text())
    budget = json.loads((project / 'reports/budget.json').read_text())
    assert state['status'] == 'PAIR_EXITED_AWAITING_RECEIPT_AND_VIDEO_REVIEW'
    assert [a['mode'] for a in state['arms']] == ['native', 'worldcache']
    assert all(a['exit_code'] == 0 for a in state['arms'])
    assert budget['gpu_jobs_launched'] == 2
    assert abs(budget['used_gpu_hours'] - sum(a['wall_seconds'] for a in state['arms']) / 3600) < 1e-9


def test_budget_stop_does_not_launch_second_arm(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=30, cap=.001)
    start = time.monotonic()
    subprocess.run(cmd, env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((output / 'supervisor.json').read_text())
    assert state['status'] == 'BUDGET_STOP'
    assert len(state['arms']) == 1
    assert state['arms'][0]['exit_code'] != 0
    assert time.monotonic() - start < 5


def test_existing_lock_refuses_duplicate_launch(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=.02)
    (project / '.sync').mkdir()
    with (project / '.sync/f1.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run(cmd, env=env, capture_output=True, timeout=10)
    assert result.returncode != 0
    assert not output.exists()
    assert json.loads((project / 'reports/budget.json').read_text())['gpu_jobs_launched'] == 0


def test_probe_mode_launches_one_load_only_command(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=.02)
    subprocess.run(cmd + ['--probe-only'], env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((output / 'supervisor.json').read_text())
    assert state['status'] == 'CORE_LOAD_EXITED_REQUIRES_STATE_REVIEW'
    assert [a['mode'] for a in state['arms']] == ['core_model_load']
    assert str(project / 'scripts/check_model_load.py') in state['command']
    assert '--mode' not in state['command']
    assert int(state['command'][2]) <= 410


def test_w1_parity_is_one_bounded_job_not_two_f1_arms(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=.02)
    subprocess.run(cmd + ['--w1-parity'], env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((output / 'supervisor.json').read_text())
    assert state['status'] == 'W1_PARITY_EXITED_REQUIRES_REVIEW'
    assert [a['mode'] for a in state['arms']] == ['w1_parity']
    assert str(project / 'scripts/check_w1_parity.py') in state['command']
    assert int(state['command'][2]) <= 890
    assert json.loads((project / 'reports/budget.json').read_text())['gpu_jobs_launched'] == 1
