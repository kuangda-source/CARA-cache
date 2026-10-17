#!/usr/bin/env python3
"""Run full24 CPU post once after the exact original supervisor has ended."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('project', 'stage'): p.add_argument('--'+n, type=Path, required=True)
    p.add_argument('--supervisor-pid', type=int, required=True)
    p.add_argument('--supervisor-start-ticks', type=int, required=True)
    a = p.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''; sys.path.insert(0, str(a.stage/'src'))
    from wcomr.gpu_budget_pool_v2 import process_identity, same_live_process
    from wcomr.drop1_window24_production_r1 import RUN, CONFIG, sha
    identity = dict(pid=a.supervisor_pid, start_ticks=a.supervisor_start_ticks)
    while same_live_process(identity): time.sleep(10)
    out = a.project/'outputs'/RUN
    command = [sys.executable, str(a.stage/'scripts/postprocess_wc_drop1_window24_r1.py'),
        '--project', str(a.project), '--stage', str(a.stage)]
    receipt = dict(status='WINDOW24_POST_CPU_RUNNING', original_supervisor=identity, command=command,
        source_revision=json.loads((a.stage/'registration.json').read_text())['source_revision'],
        config_sha256=sha(a.stage/CONFIG), original_observed_identity=process_identity(a.supervisor_pid),
        GPU_submissions=0, ledger_written=False)
    try:
        supervisor = json.loads((out/'supervisor.json').read_text())
        assert all(supervisor['supervisor_identity'][k] == identity[k] for k in ('pid', 'start_ticks'))
        assert supervisor['status'] == 'WINDOW24_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
        assert supervisor['source_revision'] == receipt['source_revision']
        assert supervisor['config_sha256'] == receipt['config_sha256']
        with (a.stage/'post-CPU.log').open('x') as log:
            call = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                         OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2'))
        receipt['exit_code'] = call.returncode
        final = a.stage/'CPU-final-results.json'
        if final.exists(): receipt['final_result_sha256'] = sha(final)
    except BaseException as e:
        receipt.update(exit_code=1, error_type=type(e).__name__, error=str(e)); raise
    finally:
        receipt.update(status='WINDOW24_POST_CPU_TERMINAL', ended_unix=time.time())
        with (a.stage/'post-CPU-exit.json').open('x') as h: json.dump(receipt, h, indent=2, allow_nan=False); h.write('\n')


if __name__ == '__main__':
    main()
