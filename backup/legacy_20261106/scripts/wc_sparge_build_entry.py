#!/usr/bin/env python3
"""CPU-only upstream build entry; guard CUDA discovery without editing upstream."""
import json
import os
from pathlib import Path
import runpy
import sys


def main():
    source, output = map(Path, sys.argv[1:3])
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('TORCH_CUDA_ARCH_LIST') != '8.6':
        raise RuntimeError('CPU-only explicit architecture environment required')
    if os.environ.get('CUDA_HOME') != '/usr/local/cuda-12.2':
        raise RuntimeError('fixed compiler required')
    import torch
    if torch.__version__ != '2.7.1+cu128' or torch.cuda.is_initialized():
        raise RuntimeError('unexpected Torch or initialized CUDA')
    def forbidden(*args, **kwargs):
        raise RuntimeError('CUDA enumeration/initialization forbidden in CPU build')
    # cpp_extension queries availability even with explicit CUDA_HOME. Avoid that
    # driver query, and reject any actual enumeration/initialization downstream.
    torch.cuda.is_available = lambda: False
    torch.cuda.device_count = forbidden
    torch.cuda.get_device_capability = forbidden
    torch.cuda.init = forbidden
    torch.cuda._lazy_init = forbidden
    os.chdir(source)
    sys.argv = ['setup.py', 'build_ext', '--build-lib', str(output / 'lib'),
                '--build-temp', str(output / 'temp')]
    outcome = 'UNKNOWN'
    try:
        runpy.run_path(str(source / 'setup.py'), run_name='__main__')
        outcome = 'UPSTREAM_BUILD_ENTRY_COMPLETED_NOT_IMPORT_OR_KERNEL'
    finally:
        output.mkdir(parents=True, exist_ok=True)
        (output / 'cuda_guard.json').write_text(json.dumps({
            'outcome': outcome, 'torch': torch.__version__,
            'cuda_initialized_after': torch.cuda.is_initialized(),
            'guard': 'availability forced false; enumeration and lazy init rejected',
        }, indent=2) + '\n')
        if torch.cuda.is_initialized():
            raise RuntimeError('CUDA initialized during CPU build')


if __name__ == '__main__':
    main()
