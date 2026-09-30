"""One hash-deployed, locked, bounded CPU fusion with durable exit receipts."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_deployment(code_root, deployment):
    required = {'scripts/supervise_l0_cpu_fusion.py', 'scripts/run_l0_cpu_fusion.py',
                'src/wcomr/__init__.py', 'src/wcomr/lora_cpu_fusion.py',
                'src/wcomr/lora_header_audit.py', 'public/merge_lora.py',
                'manifests/l0_cpu_fusion_protocol_20261001.json'}
    if not required <= deployment['source_sha256'].keys():
        raise ValueError('Incomplete source deployment lock')
    for name, digest in deployment['source_sha256'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or sha(code_root / path) != digest:
            raise ValueError('Deployment source differs: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--code-root', type=Path, required=True)
    parser.add_argument('--deployment', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--job-output', type=Path, required=True)
    parser.add_argument('--model-output', type=Path, required=True)
    parser.add_argument('--python', required=True)
    parser.add_argument('--max-wall-seconds', type=float, default=3600,
                        help='May lower, never increase, the protocol CPU cap')
    args = parser.parse_args()
    code_root, job, models = args.code_root.resolve(), args.job_output.resolve(), args.model_output.resolve()
    if job == models or job in models.parents or models in job.parents:
        raise ValueError('Job receipt and model paths must be separate')
    if job.exists() or models.exists():
        raise ValueError('Choose new job and model output identities')
    deployment_hash = sha(args.deployment)
    deployment = json.loads(args.deployment.read_text())
    validate_deployment(code_root, deployment)
    protocol_path = code_root / 'manifests/l0_cpu_fusion_protocol_20261001.json'
    protocol = json.loads(protocol_path.read_text())
    cap = args.max_wall_seconds
    if protocol['cpu_timeout_seconds'] != 3600 or not 1 <= cap <= protocol['cpu_timeout_seconds']:
        raise ValueError('CPU cap may not exceed the pinned3600 seconds')
    budget_path = args.project / 'reports/budget.json'
    budget_before = json.loads(budget_path.read_text())
    lock_path = args.project / '.sync/l0-fusion.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = lock_path.open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    job.mkdir(parents=True, exist_ok=False)
    state = {'pid': os.getpid(), 'status': 'PREPARING', 'started_unix': time.time(),
             'cpu_max_wall_seconds': cap, 'gpu_workload_started': False,
             'source_commit': deployment['source_commit'], 'source_sha256': deployment['source_sha256'],
             'deployment_sha256': deployment_hash, 'budget_before': budget_before,
             'model_output': str(models)}

    def save():
        temp = job / 'supervisor.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(job / 'supervisor.json')

    def stop(child):
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()

    def terminate(*unused):
        raise SystemExit('CPU fusion supervisor received SIGTERM')

    signal.signal(signal.SIGTERM, terminate)
    save()
    inner_cap = max(.1, cap - min(10, cap / 10))
    command = ['timeout', '--kill-after=10', str(inner_cap), args.python,
               str(code_root / 'scripts/run_l0_cpu_fusion.py'), '--protocol', str(protocol_path),
               '--base', str(args.base), '--cache', str(args.cache),
               '--upstream', str(code_root / 'public/merge_lora.py'), '--output', str(models)]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1',
               PYTHONPATH=str(code_root / 'src'), OMP_NUM_THREADS=str(protocol['cpu_threads']),
               MKL_NUM_THREADS=str(protocol['cpu_threads']))
    child = None
    started = time.monotonic()
    try:
        with (job / 'runner.log').open('x') as log:
            child = subprocess.Popen(command, cwd=code_root, env=env, stdout=log,
                                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                     start_new_session=True, pass_fds=(lock.fileno(),))
            state.update(status='RUNNING', child_pid=child.pid, command=command)
            save()
            while child.poll() is None:
                if time.monotonic() - started >= inner_cap:
                    state['stop_reason'] = 'CPU_FUSION_TIMEOUT'
                    stop(child)
                    break
                try:
                    child.wait(timeout=min(1, inner_cap))
                except subprocess.TimeoutExpired:
                    pass
    except BaseException as error:
        state.update(status='SUPERVISOR_ERROR', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        if child is not None:
            stop(child)
            state['exit_code'] = child.returncode
        state.update(ended_unix=time.time(), wall_seconds=time.monotonic() - started,
                     child_ru_maxrss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
        # A clean subprocess exit still requires tensor/artifact audit; this
        # supervisor does not certify the numerical result itself.
        if state['status'] != 'SUPERVISOR_ERROR':
            state['status'] = ('CPU_FUSION_EXIT0_REQUIRES_FULL_ARTIFACT_AUDIT'
                               if child is not None and child.returncode == 0
                               else 'CPU_FUSION_FAILED_OR_TIMEOUT_PARTIAL_NOT_READY')
        try:
            validate_deployment(code_root, deployment)
            if sha(args.deployment) != deployment_hash:
                raise ValueError('Deployment lock changed during run')
            state['source_hashes_match_after'] = True
            state['budget_after'] = json.loads(budget_path.read_text())
            state['budget_unchanged'] = state['budget_after'] == budget_before
            if not state['budget_unchanged']:
                state['status'] = 'GPU_BUDGET_CHANGED_CONCURRENTLY_REQUIRES_AUDIT'
        except Exception as error:
            state.update(status='SOURCE_OR_ACCOUNTING_AUDIT_FAILED', audit_error=str(error))
        save()


if __name__ == '__main__':
    main()
