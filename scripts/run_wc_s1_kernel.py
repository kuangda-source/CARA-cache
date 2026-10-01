#!/usr/bin/env python3
"""Real no-PV CUDA kernel gate on synthetic QKV; no Cosmos model/quality claim."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(config, package_root, package_lock, import_receipt, dense_path, wrapper_root):
    c = json.loads(config.read_text())
    if c['max_gpu_wall_seconds'] != 180 or c['pv_skipping'] is not False:
        raise ValueError('frozen180s no-PV scope required')
    if (c['batch'], c['heads'], c['head_dim'], c['dtype']) != (1, 16, 128, 'bfloat16'):
        raise ValueError('checkpoint-derived shape/dtype contract changed')
    if c['sequence_lengths'] != [256, 31104] or c['mask_retention_targets'] != [1.0, 0.5, 0.25] or c['warmups'] != 1 or c['repeats'] != 5:
        raise ValueError('frozen coverage changed')
    lock = json.loads(package_lock.read_text())
    imported = json.loads(import_receipt.read_text())
    if imported['status'] != 'ACTUAL_TWO_EXTENSION_IMPORT_AND_NO_PV_BINDING_PASS_NOT_CUDA_KERNEL' or imported['torch']['cuda_initialized_after']:
        raise ValueError('actual guarded extension import not accepted')
    if imported['package_lock_sha256'] != sha(package_lock):
        raise ValueError('package attestation differs')
    for name, item in lock['package_files'].items():
        path = package_root / name
        if sha(path) != item['sha256'] or path.stat().st_size != item['bytes']:
            raise ValueError('package drift: ' + name)
    if sha(dense_path) != c['dense_source_sha256'] or sha(wrapper_root / 'wcomr/sparge_no_pv.py') != c['wrapper_sha256']:
        raise ValueError('dense/wrapper source drift')
    return c


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['config', 'package-root', 'package-lock', 'import-receipt', 'dense-path', 'wrapper-root', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--gpu-uuid')
    p.add_argument('--validate-only', action='store_true')
    a = p.parse_args()
    c = validate(a.config, a.package_root, a.package_lock, a.import_receipt, a.dense_path, a.wrapper_root)
    if a.validate_only:
        print(json.dumps({'status': 'CPU_VALIDATE_ONLY_PASS_NO_TORCH_IMPORT', 'config_sha256': sha(a.config)}))
        return
    if not a.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES') != a.gpu_uuid:
        raise ValueError('supervised explicit GPU UUID environment required')
    a.output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    r = {'status': 'GPU_KERNEL_RUNNING', 'pid': os.getpid(), 'started_unix': time.time(),
         'gpu_uuid': a.gpu_uuid, 'config': c, 'config_sha256': sha(a.config), 'cases': [],
         'scope': c['run_scope'], 'actual_model_qkv_hook': False, 'quality_evaluation': False}
    def save():
        tmp = a.output / 'receipt.tmp'
        tmp.write_text(json.dumps(r, indent=2) + '\n')
        tmp.replace(a.output / 'receipt.json')
    save()
    try:
        import torch
        if torch.__version__ != '2.7.1+cu128':
            raise ValueError('wrong Torch')
        torch.cuda.set_device(0)
        if torch.cuda.get_device_capability(0) != (8, 6):
            raise ValueError('sm86 required')
        r['torch'] = {'version': torch.__version__, 'cpp_abi': torch._C._GLIBCXX_USE_CXX11_ABI,
                      'device': torch.cuda.get_device_name(0)}
        sys.path[:0] = [str(a.package_root), str(a.wrapper_root)]
        from wcomr.sparge_no_pv import block_sparse_no_pv
        spec = importlib.util.spec_from_file_location('wc_dense_reference', a.dense_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        generator = torch.Generator(device='cuda').manual_seed(c['seed'])
        with torch.inference_mode():
            for n in c['sequence_lengths']:
                shape = (1, n, 16, 128)
                q, k, v = [torch.randn(shape, device='cuda', dtype=torch.bfloat16, generator=generator) for _ in range(3)]
                q = q / q.float().square().mean(-1, keepdim=True).sqrt().to(q.dtype)
                k = k / k.float().square().mean(-1, keepdim=True).sqrt().to(k.dtype)
                dense = lambda: module.attention(q, k, v).reshape(1, n, 2048)
                reference = dense()
                if not bool(torch.isfinite(reference).all().item()):
                    raise ValueError('nonfinite dense reference')
                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
                    dense(); torch.cuda.synchronize()
                dispatch = sorted({e.key for e in prof.key_averages() if 'scaled_dot_product' in e.key})
                ops = [('dense', dense, None)]
                for ratio in c['mask_retention_targets']:
                    qb, kb = n // 128, n // 64
                    retained = math.ceil(kb * ratio)
                    # Fixed circular bands test real block skipping, not mask selection quality.
                    rows = torch.arange(qb, device='cuda')[:, None] * 2
                    cols = torch.arange(kb, device='cuda')[None, :]
                    mask = ((cols - rows) % kb < retained)[None, None].expand(1, 16, -1, -1).contiguous()
                    ops.append((f'no_pv_retention_{ratio}', lambda m=mask: block_sparse_no_pv(q, k, v, m),
                                float(mask.float().mean().item())))
                for name, operation, retention in ops:
                    r['active_case'] = {'n': n, 'arm': name}; save()
                    torch.cuda.reset_peak_memory_stats()
                    for _ in range(c['warmups']):
                        output = operation(); torch.cuda.synchronize()
                    wall, events = [], []
                    for _ in range(c['repeats']):
                        torch.cuda.synchronize()
                        begin, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                        before = time.perf_counter(); begin.record()
                        output = operation(); end.record(); torch.cuda.synchronize()
                        wall.append((time.perf_counter() - before) * 1000)
                        events.append(begin.elapsed_time(end))
                    delta = output.float() - reference.float()
                    relative = (delta.square().mean() / reference.float().square().mean().clamp_min(1e-20)).sqrt().item()
                    case = {'n': n, 'arm': name, 'input_shape': list(shape), 'input_dtype': str(q.dtype),
                            'dense_dispatch': dispatch, 'retained_block_fraction': retention,
                            'relative_rmse_vs_dense': relative, 'finite': bool(torch.isfinite(output).all().item()),
                            'output_shape': list(output.shape), 'output_dtype': str(output.dtype),
                            'wall_ms': wall, 'cuda_event_ms': events, 'median_wall_ms': statistics.median(wall),
                            'median_cuda_event_ms': statistics.median(events),
                            'peak_memory_allocated_bytes': torch.cuda.max_memory_allocated()}
                    r['cases'].append(case); save()
                    if not case['finite']:
                        raise ValueError('nonfinite case')
                del q, k, v, reference, output, delta, mask, ops
                torch.cuda.empty_cache()
        r['full_mask_numerical_gate'] = all(x['relative_rmse_vs_dense'] <= c['full_mask_relative_rmse_gate'] for x in r['cases'] if x['arm'] == 'no_pv_retention_1.0')
        r['status'] = 'REAL_KERNEL_CASES_COMPLETE_NOT_MODEL_OR_END_TO_END_GAIN'
    except BaseException as exc:
        r.update(status='TECH_BLOCKED', error_type=type(exc).__name__, error=str(exc))
    finally:
        r['ended_unix'] = time.time(); r['wall_seconds'] = time.monotonic() - start
        save()
        print(json.dumps({'status': r['status'], 'cases': len(r['cases'])}))


if __name__ == '__main__':
    main()
