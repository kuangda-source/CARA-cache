"""Run the source-pinned80-case ACR primitive fixture, CPU only, fresh receipt."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback


def main():
    ap = argparse.ArgumentParser()
    for name in ('stage', 'runtime', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise ValueError('New receipt required, failures are never overwritten')
    sys.path.insert(0, str(a.stage / 'src'))
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    started = time.perf_counter()
    result = {'status': 'RUNNING', 'real_model_loaded': False, 'GPU_submissions': 0,
              'runtime': str(a.runtime.resolve()), 'new_teacher_calls': 0}
    try:
        import torch
        torch.set_num_threads(2)
        assert not torch.cuda.is_initialized()
        def forbidden(*args, **kw): raise RuntimeError('CPU fixture forbids CUDA, weight load and downloads')
        torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden; torch.load = forbidden
        path = a.stage / 'tests/check_p_acr_readout_shared_prefix_cpu_r1.py'
        spec = importlib.util.spec_from_file_location('shared_prefix_ACR_CPU', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        result.update(module.run(a.runtime), CUDA_initialized=torch.cuda.is_initialized())
        result['code_sha256'] = {n: hashlib.sha256((a.stage / n).read_bytes()).hexdigest() for n in
            ('src/wcomr/p_acr_readout_r1.py', 'tests/check_p_acr_readout_shared_prefix_cpu_r1.py',
             'scripts/check_wc_p_acr_shared_prefix_cpu_r1.py')}
    except BaseException as exc:
        result.update(status='ACR_SHARED_PREFIX_CPU_FAILED_FULL_SCOPE_RETAINED', error_type=type(exc).__name__,
                      error=str(exc), traceback=traceback.format_exc())
    result['CPU_wall_seconds'] = time.perf_counter() - started
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'traceback', 'code_sha256')}))
    if 'error' in result:
        print(result['traceback']); raise SystemExit(1)


if __name__ == '__main__': main()
