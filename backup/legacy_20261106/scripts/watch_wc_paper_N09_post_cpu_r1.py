#!/usr/bin/env python3
"""Run the original N09 CPU post once, after its exact GPU supervisor exits."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def run(project, stage, identity):
    from wcomr.runtime_profile40_production_r1 import CONFIG, RUN
    from wcomr.runtime_profile40_post_r1 import GPU_TERMINAL_STATUS
    from wcomr.frozen_shared_production_r1 import sha, write
    from wcomr.gpu_budget_pool_v2 import process_identity, same_live_process
    root = project / 'outputs' / RUN
    if (stage / 'N09-CPU-final-results.json').exists() or (stage / 'N09-post-CPU-exit.json').exists():
        raise FileExistsError('Original CPU result already exists; preserve it without a new watcher')
    fence = stage / 'N09-post-CPU-request.json'
    with fence.open('x') as handle:
        json.dump(dict(original_supervisor=identity, watcher_identity=process_identity(os.getpid())), handle)
        handle.flush(); os.fsync(handle.fileno())
    receipt = dict(status='N09_FULL40_POST_CPU_TERMINAL', original_supervisor=identity,
        exit_code=None, final_result_sha256=None, GPU_submissions=0, ledger_written=False)
    try:
        while same_live_process(identity):time.sleep(10)
        config = json.loads((stage / CONFIG).read_text())
        registration = json.loads((stage / 'registration.json').read_text())
        supervisor = json.loads((root / 'supervisor.json').read_text())
        if (supervisor['pid'] != identity['pid'] or supervisor['start_ticks'] != identity['start_ticks']
                or supervisor['status'] != GPU_TERMINAL_STATUS or supervisor['run_id'] != RUN
                or supervisor['source_revision'] != registration['source_revision']
                or supervisor['registration_sha256'] != sha(stage / 'registration.json')
                or supervisor['config_sha256'] != sha(stage / CONFIG)
                or supervisor['scope_counts'] != config['scope_counts']
                or (supervisor.get('child_identity') and same_live_process(supervisor['child_identity']))):
            raise ValueError('Only the exact original terminal full40 supervisor can trigger CPU post')
        final = stage / 'N09-CPU-final-results.json'
        if final.exists() or (stage / 'N09-post-CPU-exit.json').exists():
            raise FileExistsError('Original CPU result already exists; no automatic post rerun')
        command = [sys.executable, str(stage / 'scripts/postprocess_wc_paper_N09_runtime_profile40_r1.py'),
                   '--project', str(project), '--stage', str(stage)]
        receipt.update(command=command, source_revision=supervisor['source_revision'],
            config_sha256=sha(stage / CONFIG), scope_counts=config['scope_counts'],
            registration_sha256=sha(stage / 'registration.json'), started_unix=time.time())
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                   OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        with (stage / 'N09-post-CPU.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, env=env, start_new_session=True)
            receipt['child_identity'] = process_identity(child.pid)
            write(stage / 'N09-post-CPU-child.json', receipt)
            receipt['exit_code'] = child.wait()
    except BaseException as error:
        receipt.update(exit_code=1, error_type=type(error).__name__, error=str(error))
        raise
    finally:
        final = stage / 'N09-CPU-final-results.json'
        receipt.update(ended_unix=time.time(), final_result_sha256=sha(final) if final.exists() else None)
        write(stage / 'N09-post-CPU-exit.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'):parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--supervisor-pid', type=int, required=True)
    parser.add_argument('--supervisor-start-ticks', type=int, required=True)
    args = parser.parse_args()
    if args.supervisor_pid <= 0 or args.supervisor_start_ticks <= 0:
        raise ValueError('Original positive PID and start ticks required')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(args.stage.resolve() / 'src'))
    receipt = run(args.project.resolve(), args.stage.resolve(),
        dict(pid=args.supervisor_pid, start_ticks=args.supervisor_start_ticks))
    raise SystemExit(receipt['exit_code'])


if __name__ == '__main__':main()
