#!/usr/bin/env python3
"""Stage-local full40 controls followed by the actual Cosmos no-weights entry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'): parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.stage / 'src'))
    from wcomr.balanced_repeat_cpu_acceptance_r1 import PATTERNS, BUNDLE_STATUS
    registration = json.loads((args.stage / 'registration.json').read_text())
    assert all(hashlib.sha256((args.stage / n).read_bytes()).hexdigest() == h
               for n, h in registration['payload_sha256'].items())
    destination = args.stage / 'N08-CPU-bundle-result.json'; assert not destination.exists()
    commands = [[sys.executable, '-m', 'unittest', 'discover', '-s', str(args.stage / 'tests'),
                 '-p', pattern, '-v'] for pattern in PATTERNS]
    commands.append([sys.executable, str(args.stage / 'scripts/run_wc_paper_N08_balanced_full40_r1.py'),
                     '--project', str(args.project), '--stage', str(args.stage), '--cpu-check'])
    state = dict(status='N08_FULL40_ACTUAL_PRODUCTION_CPU_RUNNING', source_revision=registration['source_revision'],
        commands=[], started_unix=time.time(), GPU_submissions=0, model_weights_loaded=0,
        ledger_written=False, shared_runtime_written=False, original_base_stage_written=False)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        PYTHONPATH=str(args.stage / 'src'), OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    try:
        for command in commands:
            code = subprocess.call(command, cwd=args.project / 'runtime', env=env)
            state['commands'].append(dict(command=command, exit_code=code))
            if code: raise RuntimeError('Original full40 production CPU command failed: ' + str(code))
        state.update(status=BUNDLE_STATUS, exit_code=0)
    except BaseException as error:
        state.update(status='N08_FULL40_ACTUAL_PRODUCTION_CPU_FAILED_NOT_GPU', exit_code=1,
                     error_type=type(error).__name__, error=str(error)); raise
    finally:
        state['wall_seconds'] = time.time() - state['started_unix']
        destination.write_text(json.dumps(state, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__': main()
