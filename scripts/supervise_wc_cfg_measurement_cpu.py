#!/usr/bin/env python3
"""CPU-only complete collector and independent audit; no GPU submission or fee."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('project', 'stage', 'runtime'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    stage = args.stage.resolve()
    reg = json.loads((stage / 'collector-preregistration.json').read_text())
    budget = args.project / 'reports/budget.json'
    result = {'status': 'MEASUREMENT_COMPLETE_COLLECTOR_CPU_RUNNING_NOT_GPU',
              'pid': os.getpid(), 'source_revision': args.source_revision,
              'started_unix': time.time(), 'budget_before_sha256': sha(budget),
              'planned_full_scope': reg['full_scope'], 'GPU_submissions': 0,
              'CUDA_visible_devices': '', 'CPU_artifacts_retained': True}
    receipt = stage / 'receipt.json'
    assert not receipt.exists()
    def save():
        tmp = receipt.with_suffix('.tmp')
        tmp.write_text(json.dumps(result, indent=2) + '\n'); tmp.replace(receipt)
    save()
    python = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2')
    started = time.perf_counter()
    try:
        assert {name: sha(stage / name) for name in reg['payload_sha256']} == reg['payload_sha256']
        assert {name: sha(args.runtime / name) for name in reg['runtime_source_sha256']} == reg['runtime_source_sha256']
        with (stage / 'core.log').open('x') as log:
            command = [python, str(stage / 'scripts/check_wc_cfg_teacher_collection_cpu.py'),
                       '--stage', str(stage), '--runtime', str(args.runtime), '--output', str(stage / 'result.json')]
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
            result['child_pid'] = child.pid; save()
            result['core_exit_code'] = child.wait()
        if result['core_exit_code']:
            raise RuntimeError('Complete measurement collector CPU failed; preserve original full scope')
        core_receipt = dict(result, status='MEASUREMENT_CORE_CPU_COMPLETE_REQUIRES_INDEPENDENT_AUDIT',
                            exit_code=0, budget_after_sha256=sha(budget),
                            payload_after_sha256={name: sha(stage / name) for name in reg['payload_sha256']},
                            runtime_after_sha256={name: sha(args.runtime / name) for name in reg['runtime_source_sha256']})
        (stage / 'core-receipt.json').write_text(json.dumps(core_receipt, indent=2) + '\n')
        result['status'] = 'MEASUREMENT_COMPLETE_COLLECTOR_INDEPENDENT_CPU_AUDIT_RUNNING'; save()
        with (stage / 'audit.json').open('x') as out, (stage / 'audit.log').open('x') as log:
            child = subprocess.Popen([python, str(stage / 'scripts/audit_wc_cfg_teacher_collection_cpu.py'),
                                      '--stage', str(stage)], stdout=out, stderr=log, env=env)
            result['audit_child_pid'] = child.pid; save()
            result['audit_exit_code'] = child.wait()
        if result['audit_exit_code']:
            raise RuntimeError('Original collector CPU completed but independent raw audit failed')
        audit = json.loads((stage / 'audit.json').read_text())
        assert audit['successful_CFG_pairs'] == 80 and audit['raw_tensors_reconstructed'] == 240
        assert audit['separate_net_input_condition_witnesses_verified'] == 448
        assert audit['separate_solver_space_witnesses_verified'] == 152
        result.update(status='MEASUREMENT_COLLECTOR_AND_INDEPENDENT_CPU_AUDIT_COMPLETE_NOT_GPU',
                      result_sha256=sha(stage / 'result.json'), audit_sha256=sha(stage / 'audit.json'), exit_code=0)
    except BaseException as error:
        result.update(status='MEASUREMENT_CPU_FAILED_SCOPE_RETAINED_NOT_PASS', error=str(error),
                      error_type=type(error).__name__, exit_code=1)
    finally:
        result['CPU_wall_seconds'] = time.perf_counter() - started
        result['budget_after_sha256'] = sha(budget)
        result['payload_after_sha256'] = {name: sha(stage / name) for name in reg['payload_sha256']}
        result['runtime_after_sha256'] = {name: sha(args.runtime / name) for name in reg['runtime_source_sha256']}
        if (result['budget_before_sha256'] != result['budget_after_sha256']
                or result['payload_after_sha256'] != reg['payload_sha256']
                or result['runtime_after_sha256'] != reg['runtime_source_sha256']):
            result.update(status='MEASUREMENT_CPU_BINDING_CHANGED_NOT_PASS', exit_code=1)
        save()
    raise SystemExit(result['exit_code'])


if __name__ == '__main__':
    main()
