#!/usr/bin/env python3
"""CPU proof of actual discrete pullbacks on declared tiny WC/RF/UniPC."""
import argparse
from datetime import datetime
import hashlib
import importlib.util
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
    assert not args.output.exists()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['CARA_READ_WRITE_RUNTIME'] = str(args.runtime.resolve())
    import torch
    torch.set_num_threads(2)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root/'tests'))
    spec = importlib.util.spec_from_file_location('read_write_adjoint_CPU', root/'tests/test_cara_read_write_adjoint_r1.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    names = ('src/wcomr/cara_read_write_adjoint_r1.py', 'tests/test_cara_read_write_adjoint_r1.py',
             'scripts/check_cara_read_write_adjoint_r1.py', 'src/wcomr/cara_read_write_transition_r1.py',
             'tests/test_cara_read_write_transition_r1.py', 'src/wcomr/cara_read_write_state_r1.py')
    receipt = dict(schema='CARA_READ_WRITE_ADJOINT_CPU_COMPONENT_R1',
        observed_at=datetime.now().astimezone().isoformat(), passed=result.wasSuccessful(), tests_run=result.testsRun,
        failures=[dict(test=str(test), detail=detail) for test,detail in result.failures+result.errors],
        metrics=module.METRICS, torch_version=torch.__version__,
        payload_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names},
        actual_WC_RF_UniPC_arithmetic=True, tiny_model_weights=True, CPU_dependency_namespaces=True,
        complete_tiny_adjoint=True, actual_Cosmos_weights=False, real_Cosmos_adjoint=False,
        video_terminal_VJP=False, GPU_submissions=0, CUDA_initialized=torch.cuda.is_initialized())
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write('\n')
    if not result.wasSuccessful() or torch.cuda.is_initialized():
        raise SystemExit(1)


if __name__ == '__main__':
    main()
