#!/usr/bin/env python3
"""Single GPU S1 probe, shared lock, prepaid bounded wall and durable settlement."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def scope_gate(budget, seconds):
    if seconds != 180 or budget['cap_gpu_hours'] != 4 or budget.get('wc_s1_inflight'):
        raise ValueError('frozen scope/current4h ledger required; existing in-flight reservation refused')
    if (budget['cap_gpu_hours'] - budget['used_gpu_hours']) * 3600 < seconds + 15:
        raise ValueError('insufficient existing balance including stop/settlement margin')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--gpu-uuid', required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    lock = (a.project / '.sync/f1.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    budget_path = a.project / 'reports/budget.json'
    budget = json.loads(budget_path.read_text())
    scope_gate(budget, 180)
    def query():
        memory = subprocess.check_output(['nvidia-smi', '-i', a.gpu_uuid, '--query-gpu=uuid,name,memory.used,compute_cap', '--format=csv,noheader,nounits'], text=True, timeout=5).strip().split(',')
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], text=True, timeout=5)
        return {'unix': time.time(), 'uuid': memory[0].strip(), 'name': memory[1].strip(), 'memory_used_mib': int(memory[2]),
                'compute_cap': memory[3].strip(), 'pids': [int(line.split(',')[1]) for line in apps.splitlines() if line.split(',')[0].strip() == a.gpu_uuid]}
    admission = query()
    if admission['pids'] or admission['memory_used_mib'] > 1024 or admission['compute_cap'] != '8.6':
        save(a.output / 'supervisor.json', {'status': 'RESOURCE_BUSY_NO_JOB_CHARGE', 'pid': os.getpid(), 'admission': admission})
        return
    python = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    args = [python, '-u', str(a.stage / 'scripts/run_wc_s1_kernel.py'), '--config', str(a.stage / 'kernel-config.json'),
            '--package-root', str(a.stage / 'build-r1/lib'), '--package-lock', str(a.stage / 'build-audit-r2.json'),
            '--import-receipt', str(a.stage / 'import-r2/receipt.json'),
            '--dense-path', str(a.project / 'runtime/cosmos_predict2/_src/predict2/networks/attention.py'),
            '--wrapper-root', str(a.stage / 'wrapper-src'), '--output', str(a.output / 'kernel'), '--gpu-uuid', a.gpu_uuid]
    # Validate before spending the reservation; no Torch/CUDA import in this mode.
    subprocess.run(args + ['--validate-only'], check=True, timeout=30)
    before = dict(budget)
    run_id = a.output.name
    budget['used_gpu_hours'] += 180 / 3600
    budget['gpu_jobs_launched'] += 1
    budget['status'] = 'WC_S1_KERNEL_RUNNING_180S_PREPAID_NOT_ACTUAL_SETTLED'
    budget['wc_s1_inflight'] = {'run_id': run_id, 'supervisor_pid': os.getpid(), 'reserved_seconds': 180}
    save(budget_path, budget)
    state = {'status': 'START_PENDING_INSPECT_SAME_OUTPUT', 'pid': os.getpid(), 'run_id': run_id,
             'admission': admission, 'budget_before': before, 'reserved_seconds': 180, 'child_pid': None}
    save(a.output / 'supervisor.json', state)
    child = None
    started = time.monotonic()
    def stop():
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL); child.wait()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('supervisor interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with (a.output / 'kernel.log').open('w') as log:
            child = subprocess.Popen(['timeout', '--kill-after=5s', '170s'] + args,
                                     env=dict(os.environ, CUDA_VISIBLE_DEVICES=a.gpu_uuid, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2'),
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True, pass_fds=(lock.fileno(),))
            state.update(status='GPU_KERNEL_RUNNING', child_pid=child.pid, child_started_unix=time.time())
            save(a.output / 'supervisor.json', state)
            with (a.output / 'gpu-monitor.jsonl').open('w') as monitor:
                while child.poll() is None:
                    if time.monotonic() - started >= 170:
                        state['stop_reason'] = 'BOUNDED_TIMEOUT'; stop(); break
                    observed = query(); monitor.write(json.dumps(observed) + '\n'); monitor.flush()
                    for pid in observed['pids']:
                        try:
                            group = os.getpgid(pid)
                        except ProcessLookupError:
                            continue
                        if group != child.pid:
                            state['stop_reason'] = 'GPU_CONFLICT'; stop(); break
                    if state.get('stop_reason'):
                        break
                    try:
                        child.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
    except BaseException as exc:
        state.update(stop_reason='SUPERVISOR_ERROR', error_type=type(exc).__name__, error=str(exc))
    finally:
        stop()
        state['exit_code'] = child.returncode if child is not None else None
        # Include release observation and failure/flush wall in settled cost.
        state['release'] = query()
        wall = time.monotonic() - started
        state['wall_seconds'] = wall
        current = json.loads(budget_path.read_text())
        if current.get('wc_s1_inflight', {}).get('run_id') != run_id:
            raise RuntimeError('reservation changed; preserve evidence and do not overwrite ledger')
        current['used_gpu_hours'] = before['used_gpu_hours'] + wall / 3600
        current.pop('wc_s1_inflight')
        current['status'] = 'WC_S1_KERNEL_SETTLED_REQUIRES_RESULT_AUDIT'
        save(budget_path, current)
        state['budget_after'] = current
        state['status'] = state.get('stop_reason') or ('EXITED_REQUIRES_RESULT_AUDIT' if state['exit_code'] == 0 else 'TECH_BLOCKED')
        state['ended_unix'] = time.time()
        save(a.output / 'supervisor.json', state)


if __name__ == '__main__':
    main()
