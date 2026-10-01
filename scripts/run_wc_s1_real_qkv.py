#!/usr/bin/env python3
"""All12 real QKV; dense, vanilla full, two paired routed no-PV controls."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
import time
import traceback


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def validate(a):
    c = json.loads(a.config.read_text())
    if c['max_gpu_wall_seconds'] != 180 or c['pv_skipping'] is not False or (c['warmups'], c['repeats']) != (1, 3):
        raise ValueError('Frozen180s/no-PV/repetition scope required')
    if c['policies'] != [{'name': 'upstream_public_default', 'sim': .6, 'cdf': .98},
                         {'name': 'upstream_utils_default', 'sim': .1, 'cdf': .9}]:
        raise ValueError('Frozen existing policies required')
    if sha(a.inputs) != c['input_manifest_sha256']:
        raise ValueError('Frozen input manifest changed')
    inputs = json.loads(a.inputs.read_text())
    for key in ['source_receipt', 'source_audit']:
        if sha(inputs[key]['path']) != inputs[key]['sha256']:
            raise ValueError('Original S0 attestation changed')
    receipt = json.loads(Path(inputs['source_receipt']['path']).read_text())
    audit = json.loads(Path(inputs['source_audit']['path']).read_text())
    if audit['status'] != 'S0_FRESH_SOURCE_QKV_COST_SETTLEMENT_RELEASE_AUDIT_PASS' or receipt['phases'][1]['snapshots'] != inputs['snapshots']:
        raise ValueError('Audited actual QKV required')
    snapshots = inputs['snapshots']
    if len(snapshots) != 12 or {(x['call'], x['layer']) for x in snapshots} != {(t, l) for t in [1, 2, 71, 72] for l in [2, 14, 27]}:
        raise ValueError('All12 fixed coverage required')
    for snapshot in snapshots:
        path = Path(snapshot['path'])
        if path.stat().st_size != snapshot['bytes'] or sha(path) != snapshot['sha256']:
            raise ValueError('Actual input bytes changed')
    lock = json.loads(a.package_lock.read_text())
    imported = json.loads(a.import_receipt.read_text())
    if imported['status'] != 'ACTUAL_TWO_EXTENSION_IMPORT_AND_NO_PV_BINDING_PASS_NOT_CUDA_KERNEL' or imported['package_lock_sha256'] != sha(a.package_lock):
        raise ValueError('Accepted actual package import required')
    for name, item in lock['package_files'].items():
        if sha(a.package_root / name) != item['sha256']:
            raise ValueError('Package drift: ' + name)
    for path, expected in [(a.dense_path, c['dense_source_sha256']),
                           (a.wrapper_root / 'wcomr/sparge_no_pv.py', c['wrapper_sha256']),
                           (a.wrapper_root / 'wcomr/sparge_routed_no_pv.py', c['routing_wrapper_sha256'])]:
        if sha(path) != expected:
            raise ValueError('Dense/wrapper source changed')
    return c, inputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['config', 'inputs', 'package-root', 'package-lock', 'import-receipt', 'dense-path', 'wrapper-root', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--gpu-uuid')
    p.add_argument('--validate-only', action='store_true')
    a = p.parse_args()
    c, inputs = validate(a)
    if a.validate_only:
        print(json.dumps({'status': 'REAL12_BYTES_PACKAGE_AND_SCOPE_PASS_NO_TORCH_OR_CUDA', 'config_sha256': sha(a.config), 'inputs_sha256': sha(a.inputs)}))
        return
    if not a.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES') != a.gpu_uuid:
        raise ValueError('Supervised explicit GPU required')
    a.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    r = {'status': 'REAL_QKV_KERNEL_RUNNING', 'pid': os.getpid(), 'started_unix': time.time(),
         'gpu_uuid': a.gpu_uuid, 'config': c, 'inputs_sha256': sha(a.inputs), 'cases': [], 'quality_evaluation': False}
    def save():
        tmp = a.output / 'receipt.tmp'
        tmp.write_text(json.dumps(r, indent=2) + '\n')
        tmp.replace(a.output / 'receipt.json')
    save()
    try:
        import torch
        if torch.__version__ != '2.7.1+cu128' or torch.cuda.get_device_capability() != (8, 6):
            raise ValueError('Actual Cosmos Torch/sm86 required')
        sys.path[:0] = [str(a.package_root), str(a.wrapper_root)]
        from wcomr.sparge_no_pv import block_sparse_no_pv
        from wcomr.sparge_routed_no_pv import routed_no_pv
        spec = importlib.util.spec_from_file_location('wc_dense_reference', a.dense_path)
        dense_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dense_module)
        def relative(output, reference):
            return float(((output.float() - reference.float()).square().mean() /
                          reference.float().square().mean().clamp_min(1e-20)).sqrt().item())
        with torch.inference_mode():
            for snapshot in inputs['snapshots']:
                cpu = torch.load(snapshot['path'], map_location='cpu', weights_only=True)
                for name, tensor in cpu.items():
                    digest = hashlib.sha256(memoryview(tensor.reshape(-1).view(torch.uint8).numpy())).hexdigest()
                    if list(tensor.shape) != [1, 31104, 16, 128] or tensor.dtype != torch.bfloat16 or digest != snapshot['tensors'][name]['raw_sha256']:
                        raise ValueError('Actual tensor roundtrip differs')
                q, k, v = [cpu[name].to('cuda') for name in ['q', 'k', 'v']]
                del cpu
                full = torch.ones(1, 16, 243, 486, device='cuda', dtype=torch.bool)
                dense = lambda: (dense_module.attention(q, k, v).reshape(1, 31104, 2048), {'selected_fraction': 1.0, 'executed_fraction': 1.0})
                reference, _ = dense()
                if not bool(torch.isfinite(reference).all().item()):
                    raise ValueError('Nonfinite dense reference')
                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
                    dense(); torch.cuda.synchronize()
                dispatch = sorted({e.key for e in prof.key_averages() if 'scaled_dot_product' in e.key})
                ops = [('dense', dense), ('vanilla_full', lambda: (block_sparse_no_pv(q, k, v, full), {'selected_fraction': 1.0, 'executed_fraction': 1.0}))]
                for policy, prefix in zip(c['policies'], ['public_default', 'utils_default']):
                    for force, suffix in [(True, 'routed_full'), (False, 'sparse')]:
                        ops.append((prefix + '_' + suffix, lambda pol=policy, f=force: routed_no_pv(q, k, v, full, pol['sim'], pol['cdf'], f)))
                paired_full = {}
                for arm, op in ops:
                    r['active_case'] = {'call': snapshot['call'], 'layer': snapshot['layer'], 'arm': arm}
                    save()
                    torch.cuda.reset_peak_memory_stats()
                    for _ in range(c['warmups']):
                        output, meta = op(); torch.cuda.synchronize()
                    wall, events = [], []
                    for _ in range(c['repeats']):
                        torch.cuda.synchronize()
                        begin, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                        start = time.perf_counter(); begin.record()
                        output, meta = op(); end.record(); torch.cuda.synchronize()
                        wall.append((time.perf_counter() - start) * 1000)
                        events.append(begin.elapsed_time(end))
                    case = {'call': snapshot['call'], 'layer': snapshot['layer'], 'cfg_slot': snapshot['cfg_slot'], 'arm': arm,
                            'input_sha256': snapshot['sha256'], 'input_shape': list(q.shape), 'output_shape': list(output.shape),
                            'output_dtype': str(output.dtype), 'finite': bool(torch.isfinite(output).all().item()),
                            'relative_rmse_vs_dense': relative(output, reference), 'routing': meta, 'dense_dispatch': dispatch,
                            'wall_ms': wall, 'cuda_event_ms': events, 'median_wall_ms': statistics.median(wall),
                            'median_cuda_event_ms': statistics.median(events), 'peak_allocated_bytes': torch.cuda.max_memory_allocated()}
                    if arm.endswith('_routed_full'):
                        paired_full[arm.removesuffix('_routed_full')] = output.clone()
                    elif arm.endswith('_sparse'):
                        case['relative_rmse_vs_matched_routed_full'] = relative(output, paired_full[arm.removesuffix('_sparse')])
                    r['cases'].append(case); save()
                    if not case['finite']:
                        raise ValueError('Nonfinite output')
                del q, k, v, reference, output, full, ops, paired_full
                torch.cuda.empty_cache()
        r['full_mask_numerical_gate'] = all(x['relative_rmse_vs_dense'] <= c['full_mask_relative_rmse_gate'] for x in r['cases'] if x['arm'] == 'vanilla_full' or x['arm'].endswith('_routed_full'))
        r['status'] = 'ALL12_REAL_QKV72_CASES_COMPLETE_NOT_SPARSE_VIDEO_OR_METHOD_ACCEPTANCE'
    except BaseException as exc:
        r.update(status='TECH_BLOCKED', error_type=type(exc).__name__, error=str(exc))
        traceback.print_exc()
    finally:
        r.update(ended_unix=time.time(), wall_seconds=time.monotonic() - started)
        save()
        print(json.dumps({'status': r['status'], 'cases': len(r['cases'])}))
    if r['status'] == 'TECH_BLOCKED':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
