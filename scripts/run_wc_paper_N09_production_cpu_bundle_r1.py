#!/usr/bin/env python3
"""All same-source N09 controls and the real no-weights Cosmos CPU entry."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def run(project, stage):
    from wcomr.runtime_profile40_cpu_acceptance_r1 import PATTERNS, WORKER, BUNDLE_WORKER, BUNDLE_STATUS
    from wcomr.runtime_profile40_production_r1 import CONFIG, CPU_RESULT
    from wcomr.frozen_shared_production_r1 import sha, write
    from wcomr.gpu_budget_pool_v2 import process_identity
    registration = json.loads((stage / 'registration.json').read_text())
    if not all(sha(stage / n) == h for n, h in registration['payload_sha256'].items()):
        raise ValueError('Original complete N09 production payload required')
    destination = stage / 'N09-CPU-bundle-result.json'
    exit_path = stage / 'N09-production-CPU-exit.json'
    if any(p.exists() for p in (destination, exit_path, stage / CPU_RESULT)):
        raise FileExistsError('Preserve the original complete CPU job and proof')
    commands = [[sys.executable, '-m', 'unittest', 'discover', '-s', str(stage / 'tests'), '-p', name, '-v']
                for name in PATTERNS]
    commands.append([sys.executable, str(stage / WORKER), '--project', str(project), '--stage', str(stage), '--cpu-check'])
    controls = {'tests/' + n: registration['payload_sha256']['tests/' + n] for n in PATTERNS}
    state = dict(status='N09_FULL40_ACTUAL_PRODUCTION_CPU_RUNNING', source_revision=registration['source_revision'],
        stage=str(stage), project=str(project), python_executable=sys.executable, commands=[], started_unix=time.time(),
        original_CPU_identity=process_identity(os.getpid()), registration_sha256=sha(stage / 'registration.json'),
        config_sha256=sha(stage / CONFIG), bundle_source_sha256=sha(stage / BUNDLE_WORKER),
        control_source_sha256=controls, production_CPU_sha256=None,
        GPU_submissions=0, model_weights_loaded=0, ledger_written=False,
        shared_runtime_written=False, original_base_stage_written=False)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        PYTHONPATH=str(stage / 'src') + os.pathsep + str(stage / 'tests'), OMP_NUM_THREADS='2',
        OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    try:
        for command in commands:
            code = subprocess.call(command, cwd=project / 'runtime', env=env)
            state['commands'].append(dict(command=command, exit_code=code))
            if code:raise RuntimeError('Original N09 complete CPU command failed: ' + str(code))
        state.update(status=BUNDLE_STATUS, exit_code=0, production_CPU_sha256=sha(stage / CPU_RESULT))
    except BaseException as error:
        state.update(status='N09_FULL40_ACTUAL_PRODUCTION_CPU_FAILED_NOT_GPU', exit_code=1,
                     error_type=type(error).__name__, error=str(error))
        raise
    finally:
        state['wall_seconds'] = time.time() - state['started_unix']
        write(destination, state)
        write(exit_path, dict(status='N09_PRODUCTION_CPU_ORIGINAL_TERMINAL', exit_code=state.get('exit_code', 1),
            source_revision=state['source_revision'], registration_sha256=state['registration_sha256'],
            original_CPU_identity=state['original_CPU_identity'], production_CPU_sha256=state['production_CPU_sha256'],
            bundle_result_sha256=sha(destination), ended_unix=time.time()))
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'):parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(args.stage.resolve() / 'src'))
    run(args.project.resolve(), args.stage.resolve())


if __name__ == '__main__':main()
