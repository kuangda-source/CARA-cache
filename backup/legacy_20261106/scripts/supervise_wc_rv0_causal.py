#!/usr/bin/env python3
"""One full causal batch with shared lock, bounded child and actual settlement."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.stage/'src'))
    from wcomr.rv0_execution import validate_config, admission_budget, reserve_budget, settle_budget
    config = json.loads((args.stage/'causal-config.json').read_text())
    validate_config(config, selected=True)
    if (args.output.name != config['run_id'] or args.gpu_uuid != config['gpu_uuid']
            or len(args.source_revision) != 40 or any(c not in '0123456789abcdef' for c in args.source_revision)):
        raise ValueError('Full causal identity/UUID/source differs')
    args.output.mkdir(parents=True, exist_ok=False)
    lock = (args.project/'.sync/f1.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    budget_path = args.project/'reports/budget.json'
    budget = json.loads(budget_path.read_text()); admission_budget(budget, config)
    if shutil.disk_usage(args.project).free < config['minimum_disk_free_bytes']:
        save(args.output/'supervisor.json', {'status': 'DISK_CAPACITY_BLOCKED_NO_JOB_CHARGE', 'pid': os.getpid()}); return
    def query():
        memory = subprocess.check_output(['nvidia-smi', '-i', args.gpu_uuid,
            '--query-gpu=uuid,name,memory.used,compute_cap', '--format=csv,noheader,nounits'], text=True, timeout=5).strip().split(',')
        applications = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
            '--format=csv,noheader,nounits'], text=True, timeout=5)
        return {'unix': time.time(), 'uuid': memory[0].strip(), 'name': memory[1].strip(),
                'memory_used_mib': int(memory[2]), 'compute_cap': memory[3].strip(),
                'pids': [int(line.split(',')[1]) for line in applications.splitlines()
                         if line.split(',')[0].strip() == args.gpu_uuid]}
    def allowed(observation):
        return (observation['uuid'] == args.gpu_uuid and not observation['pids']
                and observation['memory_used_mib'] <= 1024 and observation['compute_cap'] == '8.6')
    admission = query()
    if not allowed(admission):
        save(args.output/'supervisor.json', {'status': 'RESOURCE_BUSY_NO_JOB_CHARGE', 'pid': os.getpid(), 'admission': admission}); return
    python = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command = [python, '-u', str(args.stage/'scripts/run_wc_rv0_causal.py'),
               '--project', str(args.project), '--stage', str(args.stage), '--runtime', str(args.project/'runtime'),
               '--output', str(args.output/'diagnostic'), '--gpu-uuid', args.gpu_uuid,
               '--source-revision', args.source_revision]
    subprocess.run(command+['--validate-only'], check=True, timeout=120)
    admission = query()
    if not allowed(admission):
        save(args.output/'supervisor.json', {'status': 'RESOURCE_BUSY_NO_JOB_CHARGE', 'pid': os.getpid(), 'admission': admission}); return
    if json.loads(budget_path.read_text()) != budget:
        raise ValueError('Budget changed before reservation; no GPU submission')
    before = budget
    state = {'status': 'START_PENDING_INSPECT_SAME_OUTPUT', 'pid': os.getpid(), 'run_id': config['run_id'],
             'source_revision': args.source_revision, 'config': config, 'admission': admission,
             'budget_before': before, 'reserved_seconds': config['timeout_seconds'], 'child_pid': None,
             'planned_parent_phases': 8, 'planned_suffix_controls': 24, 'planned_encoded_outputs': 18}
    started = time.monotonic()
    save(budget_path, reserve_budget(before, config, os.getpid()))
    child = None
    def stop():
        if child is not None and child.poll() is None:
            try: os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: child.wait(timeout=config['kill_grace_seconds'])
            except subprocess.TimeoutExpired:
                try: os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                child.wait()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('causal supervisor interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        save(args.output/'supervisor.json', state)
        with (args.output/'causal.log').open('w') as log:
            child = subprocess.Popen(['timeout', '--kill-after='+str(config['kill_grace_seconds'])+'s',
                str(config['child_timeout_seconds'])+'s']+command,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=args.gpu_uuid, PYTHONDONTWRITEBYTECODE='1',
                         OMP_NUM_THREADS='2', PYTHONPATH=str(args.stage/'src')+':.:packages/cosmos-oss:packages/cosmos-cuda',
                         HF_HUB_CACHE=str(args.project/'hfhub')),
                stdout=log, stderr=subprocess.STDOUT, cwd=args.project/'runtime',
                start_new_session=True, pass_fds=(lock.fileno(),))
            state.update(status='GPU_RV0_CAUSAL_RUNNING', child_pid=child.pid, child_started_unix=time.time())
            save(args.output/'supervisor.json', state)
            with (args.output/'gpu-monitor.jsonl').open('w') as monitor:
                while child.poll() is None:
                    if time.monotonic()-started >= config['child_timeout_seconds']:
                        state['stop_reason'] = 'BOUNDED_TIMEOUT'; stop(); break
                    observed = query(); monitor.write(json.dumps(observed)+'\n'); monitor.flush()
                    for pid in observed['pids']:
                        try: group = os.getpgid(pid)
                        except ProcessLookupError: continue
                        if group != child.pid:
                            state['stop_reason'] = 'GPU_CONFLICT'; stop(); break
                    if state.get('stop_reason'): break
                    try: child.wait(timeout=2)
                    except subprocess.TimeoutExpired: pass
    except BaseException as error:
        state.update(stop_reason='SUPERVISOR_ERROR', error_type=type(error).__name__, error=str(error))
    finally:
        stop(); state['exit_code'] = child.returncode if child is not None else None
        try: state['release'] = query()
        except Exception as error: state['release'] = {'status': 'UNKNOWN', 'error': str(error)}
        wall = time.monotonic()-started; state['wall_seconds'] = wall
        state['hard_wall_cap_exceeded'] = wall > config['timeout_seconds']
        current = json.loads(budget_path.read_text())
        try:
            settled = settle_budget(current, before, config, wall, os.getpid())
            save(budget_path, settled); state['budget_after'] = settled
        except Exception as error:
            state['settlement_error'] = str(error)
            state['stop_reason'] = 'SETTLEMENT_BLOCKED_RESERVATION_PRESERVED'
        state['status'] = state.get('stop_reason') or ('EXITED_REQUIRES_RESULT_AUDIT' if state['exit_code'] == 0 else 'TECH_BLOCKED')
        state['ended_unix'] = time.time(); save(args.output/'supervisor.json', state)


if __name__ == '__main__': main()
