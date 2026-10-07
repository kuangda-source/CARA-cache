#!/usr/bin/env python3
"""Execute only the new response-onset composition using the pinned CPU fixture."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser()
    for name in ('stage', 'runtime', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0, str(args.stage/'src'))
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a, **k):
        raise RuntimeError('New tail CPU check forbids CUDA initialization or downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)
    spec = importlib.util.spec_from_file_location('new_native_onset_fixture', args.stage/'tests/check_rv0_native_onset_cpu.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    started = time.perf_counter()
    result = module.run(args.runtime)
    result['CPU_wall_seconds'] = time.perf_counter()-started
    assert not torch.cuda.is_initialized()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status', 'CPU_wall_seconds', 'CUDA_initialized', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
