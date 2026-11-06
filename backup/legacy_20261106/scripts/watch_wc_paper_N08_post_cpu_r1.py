#!/usr/bin/env python3
"""Run only original full40 CPU post after its exact supervisor exits."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--supervisor-pid', type=int, required=True)
    parser.add_argument('--supervisor-start-ticks', type=int, required=True)
    args = parser.parse_args(); assert args.supervisor_pid > 0 and args.supervisor_start_ticks > 0
    os.environ['CUDA_VISIBLE_DEVICES'] = ''; sys.path.insert(0, str(args.stage / 'src'))
    from wcomr.balanced_repeat_production_r1 import CONFIG, RUN
    from wcomr.balanced_repeat_post_r1 import GPU_TERMINAL_STATUS
    from wcomr.frozen_shared_production_r1 import sha, write
    from wcomr.gpu_budget_pool_v2 import same_live_process
    identity = dict(pid=args.supervisor_pid, start_ticks=args.supervisor_start_ticks)
    while same_live_process(identity): time.sleep(10)
    config = json.loads((args.stage / CONFIG).read_text()); root = args.project / 'outputs' / RUN
    receipt = dict(status='N08_FULL40_POST_CPU_TERMINAL', original_supervisor=identity,
        scope_counts=config['scope_counts'], exit_code=None, final_result_sha256=None, GPU_submissions=0, ledger_written=False)
    try:
        supervisor = json.loads((root / 'supervisor.json').read_text())
        assert supervisor['pid'] == identity['pid'] and supervisor['start_ticks'] == identity['start_ticks']
        assert supervisor['status'] == GPU_TERMINAL_STATUS
        assert not supervisor.get('child_identity') or not same_live_process(supervisor['child_identity'])
        command = [sys.executable, str(args.stage / 'scripts/postprocess_wc_paper_N08_balanced_full40_r1.py'),
                   '--project', str(args.project), '--stage', str(args.stage)]
        receipt.update(command=command, source_revision=supervisor['source_revision'],
                       config_sha256=sha(args.stage / CONFIG), started_unix=time.time())
        with (args.stage / 'N08-post-CPU.log').open('x') as log:
            receipt['exit_code'] = subprocess.call(command, stdout=log, stderr=subprocess.STDOUT,
                                                  env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
    except BaseException as error:
        receipt.update(exit_code=1, error_type=type(error).__name__, error=str(error)); raise
    finally:
        final = args.stage / 'N08-CPU-final-results.json'
        receipt.update(ended_unix=time.time(), final_result_sha256=sha(final) if final.exists() else None)
        write(args.stage / 'N08-post-CPU-exit.json', receipt)


if __name__ == '__main__': main()
