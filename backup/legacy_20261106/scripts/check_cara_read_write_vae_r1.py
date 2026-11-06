#!/usr/bin/env python3
"""CPU hard-forward and cross-time VJP controls for the Wan2.1 adapter."""
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
    os.environ.update(CUDA_VISIBLE_DEVICES='', CARA_READ_WRITE_VAE_RUNTIME=str(args.runtime.resolve()))
    import torch
    torch.set_num_threads(2)
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('read_write_VAE_CPU', root/'tests/test_cara_read_write_vae_r1.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    names = ('src/wcomr/cara_read_write_vae_r1.py', 'tests/test_cara_read_write_vae_r1.py',
             'scripts/check_cara_read_write_vae_r1.py')
    receipt = dict(schema='CARA_READ_WRITE_VAE_CPU_COMPONENT_R1',
        observed_at=datetime.now().astimezone().isoformat(), passed=result.wasSuccessful(), tests_run=result.testsRun,
        failures=[dict(test=str(test), detail=detail) for test,detail in result.failures+result.errors],
        metrics=module.METRICS, payload_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names},
        original_Wan_decode_source=True, source_sha256=hashlib.sha256((args.runtime/module.WAN_PATH).read_bytes()).hexdigest(),
        CPU_namespace=True, tiny_decoder_weights=True, actual_pretrained_VAE=False,
        actual93_GPU_memory=False, video_Alex_VJP=False, GPU_submissions=0, CUDA_initialized=torch.cuda.is_initialized())
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write('\n')
    if not result.wasSuccessful() or torch.cuda.is_initialized():
        raise SystemExit(1)


if __name__ == '__main__':
    main()
