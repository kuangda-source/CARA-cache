#!/usr/bin/env python3
"""Execute only the new response-onset composition using the pinned CPU fixture."""
import argparse
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser()
    for name in ('stage', 'runtime', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--reuse-nonflow-attempts', type=Path)
    p.add_argument('--reuse-nonflow-sha256')
    p.add_argument('--reuse-source-revision')
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
    if args.reuse_nonflow_attempts:
        raw = args.reuse_nonflow_attempts.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == args.reuse_nonflow_sha256
        assert args.reuse_source_revision == 'f366fbfa01d7a4fda2746bb76a85a24f9435a003'
        attempts = json.loads(raw)
        assert len(attempts) == 1
        item = attempts[0]
        assert item['flow'] is False and item['failure'] is None and item['error'] is None
        item['reuse_provenance'] = {'source_revision': args.reuse_source_revision,
            'original_attempts_sha256': args.reuse_nonflow_sha256,
            'path': str(args.reuse_nonflow_attempts), 'prior_overall_CPU_exit_code': 1,
            'new_verifier_reaudit_required': True}
        module.RESUME_NONFLOW = item
    else:
        assert args.reuse_nonflow_sha256 is None and args.reuse_source_revision is None
    started = time.perf_counter()
    try:
        result = module.run(args.runtime)
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps({
            'status': 'CPU_FAILED_NOT_PASS', 'CUDA_initialized': torch.cuda.is_initialized(),
            'GPU_submissions': 0, 'error_type': type(error).__name__, 'error': str(error),
            'CPU_wall_seconds': time.perf_counter()-started}, indent=2)+'\n')
        raise
    result['CPU_wall_seconds'] = time.perf_counter()-started
    assert not torch.cuda.is_initialized()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status', 'CPU_wall_seconds', 'CUDA_initialized', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
