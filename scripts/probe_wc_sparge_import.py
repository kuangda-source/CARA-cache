#!/usr/bin/env python3
"""Guarded actual extension import; no CUDA initialization, model or kernel call."""
import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cuda_denial_guard(name):
    # Dynamo builds per-object rules. Each API must have its own identity.
    def deny(*args, **kwargs):
        raise RuntimeError('CUDA API forbidden in CPU probe: ' + name)
    return deny


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['package-root', 'package-lock', 'project', 'runtime', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    r = {'status': 'CPU_IMPORT_RUNNING', 'pid': os.getpid(), 'started_unix': time.time(),
         'scope': 'actual pinned extension import/callable binding; no model or CUDA kernel'}
    def save():
        (a.output / 'receipt.json').write_text(json.dumps(r, indent=2) + '\n')
    save()
    try:
        if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
            raise ValueError('GPU must be hidden for CPU import')
        lock = json.loads(a.package_lock.read_text())
        if lock['status'] != 'FRESH80_SOURCE_2_SM86_BINARIES_AND8_PACKAGE_FILES_PASS_NOT_IMPORT_OR_KERNEL':
            raise ValueError('accepted complete package required')
        for name, item in lock['package_files'].items():
            path = a.package_root / name
            if sha(path) != item['sha256'] or path.stat().st_size != item['bytes']:
                raise ValueError('package changed: ' + name)
        r['package_lock_sha256'] = sha(a.package_lock)
        r['budget_sha256_before'] = sha(a.project / 'reports/budget.json')
        import torch
        if torch.__version__ != '2.7.1+cu128' or torch.cuda.is_initialized():
            raise ValueError('unexpected runtime or initialized CUDA')
        r['torch'] = {'version': torch.__version__, 'cpp_abi': torch._C._GLIBCXX_USE_CXX11_ABI,
                      'cuda_initialized_before': False}
        torch.cuda.is_available = lambda: False
        for name in ['device_count', 'get_device_capability', 'set_device', 'init', '_lazy_init']:
            setattr(torch.cuda, name, cuda_denial_guard(name))
        sys.path.insert(0, str(a.package_root))
        r['modules'] = {}
        for name in ['spas_sage_attn', 'spas_sage_attn._qattn', 'spas_sage_attn._fused', 'spas_sage_attn.utils']:
            module = importlib.import_module(name)
            path = Path(module.__file__).resolve()
            expected = (a.package_root / path.relative_to(a.package_root.resolve())).resolve()
            if path != expected:
                raise ValueError('unexpected module origin')
            r['modules'][name] = {'path': str(path), 'sha256': sha(path)}
        op = getattr(importlib.import_module('spas_sage_attn._qattn'),
                     'qk_int8_sv_f16_accum_f16_block_sparse_attn_inst_buf')
        if not callable(op):
            raise ValueError('no-PV binding is not callable')
        r['binding_documentation'] = op.__doc__
        dense_path = a.runtime / 'cosmos_predict2/_src/predict2/networks/attention.py'
        spec = importlib.util.spec_from_file_location('wc_dense_reference', dense_path)
        dense = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dense)
        if not callable(dense.attention):
            raise ValueError('dense reference missing')
        r['dense_source'] = {'path': str(dense_path), 'sha256': sha(dense_path)}
        r['status'] = 'ACTUAL_TWO_EXTENSION_IMPORT_AND_NO_PV_BINDING_PASS_NOT_CUDA_KERNEL'
    except BaseException as exc:
        r.update(status='TECH_BLOCKED', error_type=type(exc).__name__, error=str(exc))
    finally:
        if 'torch' in r:
            r['torch']['cuda_initialized_after'] = torch.cuda.is_initialized()
            if r['torch']['cuda_initialized_after']:
                r.update(status='TECH_BLOCKED', error='CUDA initialized during CPU probe')
        r['budget_sha256_after'] = sha(a.project / 'reports/budget.json')
        r['budget_unchanged'] = r.get('budget_sha256_before') == r['budget_sha256_after']
        if not r['budget_unchanged']:
            r.update(status='TECH_BLOCKED', error='GPU ledger changed during CPU probe')
        r['ended_unix'] = time.time()
        r['wall_seconds'] = time.monotonic() - started
        save()
        print(json.dumps({'status': r['status'], 'output': str(a.output)}))


if __name__ == '__main__':
    main()
