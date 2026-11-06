#!/usr/bin/env python3
"""Dedicated CPU stage driver. Does not acquire a GPU or write its ledger."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    p = argparse.ArgumentParser()
    for name in ('stage', 'runtime', 'project'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--source-revision', required=True)
    args = p.parse_args()
    stage = args.stage.resolve()
    reg = json.loads((stage / 'ra-coarse-cal-core-preregistration.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = stage / 'receipt.json'
    assert not receipt.exists()
    result = {'status': 'RA_COARSE_CAL_CORE_CPU_RUNNING_NOT_GPU', 'pid': os.getpid(),
        'source_revision': args.source_revision, 'started_unix': time.time(),
        'GPU_submissions': 0, 'CUDA_VISIBLE_DEVICES': '', 'planned_scope': reg['CPU_scope'],
        'budget_before_sha256': sha(args.project / 'reports/budget.json'), 'ledger_written_by_this_driver': False}
    def save():
        tmp = receipt.with_suffix('.tmp')
        tmp.write_text(json.dumps(result, indent=2) + '\n')
        tmp.replace(receipt)
    save()
    started = time.perf_counter()
    try:
        assert {n: sha(stage / n) for n in reg['payload_sha256']} == reg['payload_sha256']
        assert {n: sha(args.runtime / n) for n in reg['runtime_source_sha256']} == reg['runtime_source_sha256']
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        python = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        with (stage / 'core.log').open('x') as log:
            child = subprocess.Popen([python, str(stage / 'scripts/check_wc_ra_calibration_core_cpu.py'),
                '--stage', str(stage), '--runtime', str(args.runtime), '--output', str(stage / 'result.json')],
                stdout=log, stderr=subprocess.STDOUT, env=env)
            result['child_pid'] = child.pid
            save()
            result['child_exit_code'] = child.wait()
        if result['child_exit_code']:
            raise RuntimeError('Full CPU scope failed; no passing subset accepted')
        core = json.loads((stage / 'result.json').read_text())
        assert core['status'] == 'RA_COARSE_CAL_CORE_PINNED_FULL36_TOY_CPU_NOT_COSMOS'
        assert core['planned_scope'] == reg['CPU_scope'] and core['GPU_submissions'] == 0
        assert not core['CUDA_initialized']
        result.update(status='RA_COARSE_CAL_CORE_PINNED_FULL36_TOY_CPU_NOT_COSMOS',
                      result_sha256=sha(stage / 'result.json'), exit_code=0)
    except BaseException as error:
        result.update(status='PAIRED_PROBE_CPU_FAILED_COMPLETE_SCOPE_RETAINED', exit_code=1,
                      error=str(error), error_type=type(error).__name__)
    finally:
        result.update(CPU_wall_seconds=time.perf_counter() - started,
            budget_after_sha256=sha(args.project / 'reports/budget.json'),
            payload_after_sha256={n: sha(stage / n) for n in reg['payload_sha256']},
            runtime_after_sha256={n: sha(args.runtime / n) for n in reg['runtime_source_sha256']})
        if (result['payload_after_sha256'] != reg['payload_sha256'] or
                result['runtime_after_sha256'] != reg['runtime_source_sha256']):
            result.update(status='PAIRED_PROBE_CPU_SOURCE_CHANGED_NOT_PASS', exit_code=1)
        # The original GPU supervisor may legitimately settle while this CPU
        # runs. A ledger-byte change is recorded, never written or called a CPU
        # failure solely for that concurrent settlement.
        save()
    raise SystemExit(result['exit_code'])


if __name__ == '__main__':
    main()
