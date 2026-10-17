#!/usr/bin/env python3
"""Four control groups plus the actual complete24 production CPU entry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('project', 'stage'): p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args(); sys.path.insert(0, str(a.stage / 'src'))
    from wcomr.drop1_window24_production_r1 import CONFIG, CPU_RESULT
    from wcomr.drop1_window24_cpu_acceptance_r1 import PATTERNS, BUNDLE, BUNDLE_STATUS, WORKER
    regpath = a.stage / 'registration.json'; reg = json.loads(regpath.read_text())
    sha = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
    assert all(sha(a.stage/n) == h for n,h in reg['payload_sha256'].items())
    assert all(sha(a.project/'runtime'/n) == h for n,h in reg['runtime_source_sha256'].items())
    dest = a.stage / BUNDLE; assert not dest.exists()
    commands = [[sys.executable, '-m', 'unittest', 'discover', '-s', str(a.stage/'tests'), '-p', n, '-v'] for n in PATTERNS]
    commands.append([sys.executable, str(a.stage/WORKER), '--project', str(a.project), '--stage', str(a.stage), '--cpu-check'])
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        PYTHONPATH=str(a.stage/'src'), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    state = dict(status='WINDOW24_COMPLETE_PRODUCTION_CPU_RUNNING', source_revision=reg['source_revision'],
        registration_sha256=sha(regpath), config_sha256=sha(a.stage/CONFIG),
        stage=str(a.stage), project=str(a.project), python_executable=sys.executable,
        bundle_worker_source_sha256=reg['payload_sha256']['scripts/run_wc_drop1_window24_cpu_bundle_r1.py'],
        control_source_sha256={'tests/'+n: reg['payload_sha256']['tests/'+n] for n in PATTERNS},
        commands=[], GPU_submissions=0, model_weights_loaded=0, ledger_written=False,
        original_stage_written=False, started_unix=time.time())
    try:
        for command in commands:
            call = subprocess.run(command, cwd=a.project/'runtime', env=env)
            state['commands'].append(dict(command=command, exit_code=call.returncode))
            if call.returncode: raise RuntimeError('Whole24 CPU command exited ' + str(call.returncode))
        state.update(status=BUNDLE_STATUS, exit_code=0, production_CPU_sha256=sha(a.stage/CPU_RESULT))
    except BaseException as e:
        state.update(status='WINDOW24_COMPLETE_CPU_FAILURE_RETAINED', exit_code=1, error_type=type(e).__name__, error=str(e))
        raise
    finally:
        state['wall_seconds'] = time.time() - state['started_unix']
        with dest.open('x') as h: json.dump(state, h, indent=2, allow_nan=False); h.write('\n')


if __name__ == '__main__':
    main()
