#!/usr/bin/env python3
"""Local CPU evidence for the differentiable pinned WC/RF cache transition."""
import argparse
from datetime import datetime
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Original CPU receipt exists; use a new path')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['CARA_READ_WRITE_RUNTIME'] = str(args.runtime.resolve())
    import torch
    torch.set_num_threads(2)
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('read_write_transition_CPU',
        root/'tests/test_cara_read_write_transition_r1.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    receipt = dict(schema='CARA_READ_WRITE_TRANSITION_CPU_R1', observed_at=datetime.now().astimezone().isoformat(),
        passed=result.wasSuccessful(), tests_run=result.testsRun,
        failures=[dict(test=str(test), detail=detail) for test,detail in result.failures+result.errors],
        runtime=str(args.runtime.resolve()), torch_version=torch.__version__, metrics=module.METRICS,
        CPU_dependency_namespaces=True, tiny_model_weights=True, original_WC_RF_arithmetic=True,
        actual_Cosmos_weights=False, actual_Cosmos_model_VJP=False, terminal_LPIPS_VJP=False,
        complete_augmented_adjoint=False, GPU_submissions=0, CUDA_initialized=torch.cuda.is_initialized())
    names = ('src/wcomr/cara_read_write_transition_r1.py',
             'tests/test_cara_read_write_transition_r1.py', 'scripts/check_cara_read_write_transition_r1.py')
    receipt['payload_sha256'] = {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
    receipt['runtime_source_sha256'] = {name:hashlib.sha256((args.runtime/name).read_bytes()).hexdigest()
        for name in ('cosmos_predict2/_src/predict2/inference/worldcache_utils.py',
                     'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py',
                     'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    if not result.wasSuccessful() or torch.cuda.is_initialized():
        raise SystemExit(1)


if __name__ == '__main__':
    main()
