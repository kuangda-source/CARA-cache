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
    child.write_text('#!/usr/bin/env python3\nimport time,json,os\n'
                     'from pathlib import Path\n'
                     'Path(%r).write_text(json.dumps({k:os.environ.get(k) for k in [\"HF_HUB_CACHE\",\"HF_HUB_OFFLINE\",\"TRANSFORMERS_OFFLINE\"]}))\n'
                     'time.sleep(%r)\n' % (str(project / 'reports/child_env.json'), delay))
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
    child_env = json.loads((project / 'reports/child_env.json').read_text())
    assert child_env == {'HF_HUB_CACHE':str(project / 'hfhub'), 'HF_HUB_OFFLINE':'1', 'TRANSFORMERS_OFFLINE':'1'}


def test_same_state_runs_one_budgeted_gate_with_distinct_receipt(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=.02)
    subprocess.run(cmd + ['--w1-same-state'], env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((output / 'supervisor.json').read_text())
    assert state['status'] == 'W1_SAME_STATE_EXITED_REQUIRES_REVIEW'
    assert [a['mode'] for a in state['arms']] == ['w1_same_state']
    assert '--same-state' in state['command']
    assert str(output / 'w1-same-state.json') in state['command']
    assert int(state['command'][2]) <= 890
    assert json.loads((project / 'reports/budget.json').read_text())['gpu_jobs_launched'] == 1
    child_env = json.loads((project / 'reports/child_env.json').read_text())
    assert child_env == {'HF_HUB_CACHE':str(project / 'hfhub'), 'HF_HUB_OFFLINE':'1', 'TRANSFORMERS_OFFLINE':'1'}


def test_recent_revision_uses_same_bounded_single_job_and_explicit_runner_flag(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=.02)
    subprocess.run(cmd+['--w1-same-state','--w1-recent-calibration'],env=env,check=True,capture_output=True,timeout=10)
    state=json.loads((output/'supervisor.json').read_text())
    assert len(state['arms'])==1
    assert '--same-state-recent' in state['command']
    assert int(state['command'][2])<=890


def test_stage_gate_uses_two_fresh_children_and_shared_remaining_deadline(tmp_path):
    project, output, cmd, env = fixture(tmp_path, delay=1.1)
    child=Path(cmd[cmd.index('--python')+1])
    child.write_text(child.read_text()+
        'import sys\nreceipt=Path(sys.argv[sys.argv.index("--receipt")+1])\n'
        'receipt.parent.mkdir(parents=True,exist_ok=False)\n'
        '(receipt.parent/"video").mkdir(exist_ok=False)\nreceipt.write_text("{}")\n')
    subprocess.run(cmd+['--stage-witness'],env=env,check=True,capture_output=True,timeout=10)
    state=json.loads((output/'supervisor.json').read_text())
    assert state['status']=='STAGE_WITNESS_EXITED_REQUIRES_REVIEW'
    assert [arm['mode'] for arm in state['arms']]==['stage_a','stage_b']
    assert len({arm['pid'] for arm in state['arms']})==2
    assert str(project/'scripts/check_stage_witness.py') in state['command']
    assert str(output/'stage_b'/'witness.json') in state['command']
    assert all((output/mode/'witness.json').exists() for mode in ['stage_a','stage_b'])
    assert int(state['command'][2])<=888  # Remaining gate time includes first child.
    budget=json.loads((project/'reports/budget.json').read_text())
    assert budget['gpu_jobs_launched']==2
    assert abs(budget['used_gpu_hours']-sum(a['wall_seconds'] for a in state['arms'])/3600)<1e-9


def test_decoder_policy_requires_stage_gate_and_passes_explicit_flag(tmp_path):
    project,output,cmd,env=fixture(tmp_path,delay=.02)
    rejected=subprocess.run(cmd+['--deterministic-decode'],env=env,capture_output=True,timeout=10)
    assert rejected.returncode!=0 and not output.exists()
    subprocess.run(cmd+['--stage-witness','--deterministic-decode'],env=env,check=True,capture_output=True,timeout=10)
    state=json.loads((output/'supervisor.json').read_text())
    assert len(state['arms'])==2 and '--deterministic-decode' in state['command']
