#!/usr/bin/env python3
"""Bounded isolated upstream compilation with durable PID/log/terminal receipts."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source', 'source-lock', 'project-root', 'output', 'entry']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--max-wall-seconds', type=int, default=900)
    args = p.parse_args()
    if not 1 <= args.max_wall_seconds <= 900:
        raise ValueError('bounded CPU build cap must be <=900s')
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = args.output / 'receipt.json'
    log = args.output / 'build.log'
    started = time.monotonic()
    r = {'status': 'CPU_BUILD_PREFLIGHT', 'pid': os.getpid(), 'started_unix': time.time(),
         'scope': 'upstream build_ext in isolated directory; no installation/import/kernel/GPU',
         'max_wall_seconds': args.max_wall_seconds, 'source': str(args.source),
         'source_lock_sha256': sha(args.source_lock), 'entry_sha256': sha(args.entry),
         'runner_sha256': sha(Path(__file__)), 'child_pid': None}
    def save():
        temp = receipt.with_suffix('.tmp')
        temp.write_text(json.dumps(r, indent=2) + '\n')
        temp.replace(receipt)
    def check_source(lock):
        for name, item in lock['files'].items():
            path = args.source / name
            if sha(path) != item['sha256'] or path.stat().st_size != item['bytes']:
                raise ValueError('source drift: ' + name)
    save()
    child = None
    lock_handle = None
    def interrupted(signum, frame):
        raise KeyboardInterrupt('build supervisor interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        lock_handle = (args.project_root / '.sync/wc-sparse-build.lock').open('a+')
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock = json.loads(args.source_lock.read_text())
        if lock['status'] != 'COMPLETE_GIT_BLOB_AND_SHA_SOURCE_PASS_NOT_BUILD_OR_INSTALL':
            raise ValueError('full source lock required')
        check_source(lock)
        free = shutil.disk_usage(args.project_root).free
        available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))) * 1024
        r['resources_before'] = {'disk_free_bytes': free, 'memory_available_bytes': available}
        if free < 20 * 1024**3 or available < 16 * 1024**3:
            raise ValueError('insufficient bounded compilation resources')
        r['upstream_commit'] = lock['commit']
        r['source_files_verified_before'] = len(lock['files'])
        budget = args.project_root / 'reports/budget.json'
        r['budget_sha256_before'] = sha(budget)
        if r['budget_sha256_before'] != '26d0cdb74628d57458fea05a51f5fe062e2dcd0cd1a2f06d1d8e7c34ea40da41':
            raise ValueError('unexpected GPU ledger')
        runtime = args.project_root / 'runtime/cosmos_predict2/_src/predict2'
        r['runtime_sha256_before'] = {name: sha(runtime / name) for name in
            ['networks/minimal_v4_dit.py', 'inference/worldcache_utils.py']}
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', CUDA_HOME='/usr/local/cuda-12.2',
                   TORCH_CUDA_ARCH_LIST='8.6', MAX_JOBS='2', OMP_NUM_THREADS='2',
                   OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
        python = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        env['PATH'] = str(Path(python).parent) + ':/usr/local/cuda-12.2/bin:' + env['PATH']
        r['build_environment'] = {k: env[k] for k in ['CUDA_VISIBLE_DEVICES', 'CUDA_HOME', 'TORCH_CUDA_ARCH_LIST', 'MAX_JOBS', 'OMP_NUM_THREADS']}
        with log.open('w') as stream:
            child = subprocess.Popen([python, '-u', str(args.entry), str(args.source), str(args.output)],
                                     env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            r.update(status='CPU_BUILD_RUNNING', child_pid=child.pid)
            save()
            while child.poll() is None:
                if time.monotonic() - started >= args.max_wall_seconds:
                    r['timeout'] = True
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                    break
                time.sleep(2)
        r['exit_code'] = child.returncode
        check_source(lock)
        r['source_files_verified_after'] = len(lock['files'])
        r['budget_sha256_after'] = sha(budget)
        r['runtime_sha256_after'] = {name: sha(runtime / name) for name in r['runtime_sha256_before']}
        if r['budget_sha256_after'] != r['budget_sha256_before'] or r['runtime_sha256_after'] != r['runtime_sha256_before']:
            raise ValueError('baseline or ledger changed')
        guard = args.output / 'cuda_guard.json'
        r['cuda_guard'] = json.loads(guard.read_text()) if guard.exists() else None
        artifacts = list((args.output / 'lib').rglob('*.so'))
        r['artifacts'] = {str(path.relative_to(args.output)): {'sha256': sha(path), 'bytes': path.stat().st_size} for path in artifacts}
        if child.returncode == 0 and len(artifacts) == 2 and r['cuda_guard'] and r['cuda_guard']['cuda_initialized_after'] is False:
            r['status'] = 'CPU_UPSTREAM_TWO_EXTENSIONS_BUILT_NOT_IMPORT_OR_KERNEL'
        else:
            r['status'] = 'CPU_BUILD_TIMEOUT' if r.get('timeout') else 'TECH_BLOCKED'
    except BaseException as exc:
        r.update(status='TECH_BLOCKED', error_type=type(exc).__name__, error=str(exc))
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    finally:
        r['ended_unix'] = time.time()
        r['wall_seconds'] = time.monotonic() - started
        if log.exists():
            r['log_sha256'] = sha(log)
            r['log_bytes'] = log.stat().st_size
            r['diagnostic_excerpt'] = log.read_text(errors='replace')[-5000:]
        if lock_handle is not None:
            lock_handle.close()
        save()
        print(json.dumps({'status': r['status'], 'receipt': str(receipt)}))


if __name__ == '__main__':
    main()
