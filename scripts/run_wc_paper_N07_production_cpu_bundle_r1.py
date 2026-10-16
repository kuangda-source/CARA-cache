#!/usr/bin/env python3
"""Stage-local source/contract controls and actual Cosmos no-weights CPU entry."""
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
    for name in ('project', 'stage'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    registration = json.loads((args.stage / 'registration.json').read_text())
    assert all(hashlib.sha256((args.stage / n).read_bytes()).hexdigest() == h
               for n, h in registration['payload_sha256'].items())
    destination = args.stage / 'CPU-bundle-result.json'
    assert not destination.exists()
    patterns = ('test_frozen_shared_production_r1.py', 'test_frozen_shared_batch_r1.py',
                'test_frozen_shared_post_r1.py', 'test_frozen_shared_acceptance_r1.py',
                'test_frozen_shared_dispatch_r1.py')
    commands = [[sys.executable, '-m', 'unittest', 'discover', '-s', str(args.stage / 'tests'),
                 '-p', name, '-v'] for name in patterns]
    commands.append([sys.executable, str(args.stage / 'scripts/run_wc_paper_N07_frozen_shared180_r1.py'),
                     '--project', str(args.project), '--stage', str(args.stage), '--cpu-check'])
    state = dict(status='N07_SHARED180_ACTUAL_PRODUCTION_CPU_RUNNING', source_revision=registration['source_revision'],
        commands=[], started_unix=time.time(), GPU_submissions=0, model_weights_loaded=0,
        ledger_written=False, shared_runtime_written=False, original_base_stage_written=False)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        PYTHONPATH=str(args.stage / 'src'), OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
        PYTHONDONTWRITEBYTECODE='1')
    try:
        for command in commands:
            code = subprocess.call(command, cwd=args.project / 'runtime', env=env)
            state['commands'].append(dict(command=command, exit_code=code))
            if code: raise RuntimeError('Original N07 production CPU command failed: ' + str(code))
        state.update(status='N07_SHARED180_ACTUAL_PRODUCTION_CPU_COMPLETE_PASS_NOT_GPU', exit_code=0)
    except BaseException as error:
        state.update(status='N07_SHARED180_ACTUAL_PRODUCTION_CPU_FAILED_NOT_GPU', exit_code=1,
                     error_type=type(error).__name__, error=str(error)); raise
    finally:
        state['wall_seconds'] = time.time() - state['started_unix']
        destination.write_text(json.dumps(state, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__': main()
