"""Actual subprocess/lock/termination tests; no model, network or GPU."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/supervise_l0_cpu_fusion.py'


def fixture(tmp_path, delay=0, exit_code=0):
    project = tmp_path / 'project'
    (project / 'reports').mkdir(parents=True)
    budget = {'cap_gpu_hours': 4, 'used_gpu_hours': 3.6512467238638138, 'gpu_jobs_launched': 22}
    (project / 'reports/budget.json').write_text(json.dumps(budget))
    code = tmp_path / 'code'
    files = {'scripts/supervise_l0_cpu_fusion.py': SCRIPT.read_text(),
             'src/wcomr/__init__.py': '', 'src/wcomr/lora_cpu_fusion.py': '',
             'src/wcomr/lora_header_audit.py': '', 'public/merge_lora.py': '',
             'manifests/l0_cpu_fusion_protocol_20261001.json': json.dumps({'cpu_timeout_seconds': 3600, 'cpu_threads': 1}),
             'scripts/run_l0_cpu_fusion.py':
                 "import json,os,time,sys\nfrom pathlib import Path\n"
                 "out=Path(sys.argv[sys.argv.index('--output')+1]);out.mkdir()\n"
                 "(out/'fixture.json').write_text(json.dumps({'pid':os.getpid(),'cuda':os.environ['CUDA_VISIBLE_DEVICES'],'offline':os.environ['HF_HUB_OFFLINE']}))\n"
                 f"time.sleep({delay!r})\nsys.exit({exit_code!r})\n"}
    for name, text in files.items():
        p = code / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    deployment = code / 'deployment.json'
    deployment.write_text(json.dumps({'source_commit': 'test-only-fixture',
        'source_sha256': {p: hashlib.sha256(t.encode()).hexdigest() for p, t in files.items()}}))
    binary = tmp_path / 'bin'; binary.mkdir()
    # On macOS this shim executes the child; the parent enforces the deadline.
    timeout = binary / 'timeout'
    timeout.write_text('#!/usr/bin/env python3\nimport os,sys\nos.execv(sys.argv[3],sys.argv[3:])\n')
    timeout.chmod(0o755)
    env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'])
    job, models = tmp_path / 'job', tmp_path / 'models'
    cmd = [sys.executable, str(SCRIPT), '--project', str(project), '--code-root', str(code),
           '--deployment', str(deployment), '--base', str(tmp_path / 'unused-base'),
           '--cache', str(tmp_path / 'unused-cache'), '--job-output', str(job),
           '--model-output', str(models), '--python', sys.executable]
    return project, code, job, models, cmd, env, budget


def test_success_records_exit_source_and_cpu_environment_without_budget_charge(tmp_path):
    project, code, job, models, cmd, env, budget = fixture(tmp_path)
    subprocess.run(cmd, env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((job / 'supervisor.json').read_text())
    assert state['status'] == 'CPU_FUSION_EXIT0_REQUIRES_FULL_ARTIFACT_AUDIT'
    assert state['exit_code'] == 0 and state['source_hashes_match_after'] and state['budget_unchanged']
    assert json.loads((models / 'fixture.json').read_text())['cuda'] == ''
    assert json.loads((models / 'fixture.json').read_text())['offline'] == '1'
    assert json.loads((project / 'reports/budget.json').read_text()) == budget
    assert subprocess.run(cmd, env=env, capture_output=True, timeout=10).returncode != 0


def test_failure_retains_partial_and_exit_code(tmp_path):
    project, code, job, models, cmd, env, budget = fixture(tmp_path, exit_code=7)
    subprocess.run(cmd, env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((job / 'supervisor.json').read_text())
    assert state['exit_code'] == 7 and state['status'] == 'CPU_FUSION_FAILED_OR_TIMEOUT_PARTIAL_NOT_READY'
    assert (models / 'fixture.json').exists() and state['budget_unchanged']


def test_deadline_terminates_owned_child_and_releases_lock(tmp_path):
    project, code, job, models, cmd, env, budget = fixture(tmp_path, delay=30)
    subprocess.run(cmd + ['--max-wall-seconds', '1'], env=env, check=True, capture_output=True, timeout=10)
    state = json.loads((job / 'supervisor.json').read_text())
    assert state['exit_code'] != 0 and state['stop_reason'] == 'CPU_FUSION_TIMEOUT'
    pid = json.loads((models / 'fixture.json').read_text())['pid']
    with pytest.raises(ProcessLookupError): os.kill(pid, 0)
    with (project / '.sync/l0-fusion.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert state['budget_unchanged']


def test_existing_lock_prevents_second_job_before_outputs(tmp_path):
    project, code, job, models, cmd, env, budget = fixture(tmp_path)
    (project / '.sync').mkdir()
    with (project / '.sync/l0-fusion.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run(cmd, env=env, capture_output=True, timeout=10)
    assert result.returncode != 0 and not job.exists() and not models.exists()


def test_changed_source_refused_before_any_child(tmp_path):
    project, code, job, models, cmd, env, budget = fixture(tmp_path)
    (code / 'scripts/run_l0_cpu_fusion.py').write_text('raise RuntimeError("never execute")')
    result = subprocess.run(cmd, env=env, capture_output=True, timeout=10)
    assert result.returncode != 0 and not job.exists() and not models.exists()
