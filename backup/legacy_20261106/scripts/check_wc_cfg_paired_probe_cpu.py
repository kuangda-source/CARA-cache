#!/usr/bin/env python3
"""Execute the entire preregistered H-T50 CPU-only fixture."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('stage', 'runtime', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(args.stage / 'src'))
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a, **kw):
        raise RuntimeError('Paired-probe CPU fixture forbids CUDA/downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)
    reg = json.loads((args.stage / 'paired-probe-preregistration.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert {n: sha(args.stage / n) for n in reg['payload_sha256']} == reg['payload_sha256']
    assert {n: sha(args.runtime / n) for n in reg['runtime_source_sha256']} == reg['runtime_source_sha256']
    assert not args.output.exists()
    spec = importlib.util.spec_from_file_location('actual_paired_probe_CPU', args.stage / 'tests/check_cfg_paired_probe_cpu.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started = time.perf_counter()
    try:
        result = module.run(args.runtime)
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps({
            'status': 'PAIRED_PROBE_CPU_FAILED_COMPLETE_SCOPE_RETAINED', 'error': str(error),
            'error_type': type(error).__name__, 'CPU_wall_seconds': time.perf_counter() - started,
            'planned_scope': reg['CPU_scope'], 'GPU_submissions': 0,
            'CUDA_initialized': torch.cuda.is_initialized()}, indent=2) + '\n')
        raise
    rows = result['checks']
    assert len([r for r in rows if r['kind'] == 'main_pair']) == 8
    assert len([r for r in rows if r['kind'] == 'protected_initialization']) == 2
    assert len([r for r in rows if r['kind'] == 'failure_control']) == 8
    assert len([r for r in rows if r['kind'] == 'source_contract']) == 2
    assert not torch.cuda.is_initialized()
    result.update(status='PAIRED_PROBE_COMPLETE_PINNED_CPU_INTERFACE_NOT_MODEL_OR_POLICY',
        CPU_wall_seconds=time.perf_counter() - started, pid=os.getpid(), GPU_submissions=0,
        CUDA_initialized=False, planned_scope=reg['CPU_scope'], payload_sha256=reg['payload_sha256'],
        real_model_output_or_latency_claim=False, risk_policy_or_calibration_claim=False,
        arbitrary_fault_full_rollback_claim=False)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
