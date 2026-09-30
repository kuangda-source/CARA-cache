"""Bounded CPU fusion orchestration around a hash-pinned upstream merger.

Sharding changes storage and memory usage only. All adapter updates for a target
are passed together, in recipe order, to the original upstream merge function.
"""
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import time


def file_hash(path, git_blob=False):
    path = Path(path)
    digest = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        digest.update(('blob %d\0' % path.stat().st_size).encode())
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def check_file(path, row):
    path = Path(path)
    if path.stat().st_size != row['size']:
        raise ValueError('Input byte count differs: ' + str(path))
    git = 'lfs' not in row
    expected = row['git_blob_oid'] if git else row['lfs']['oid']
    actual = file_hash(path, git)
    if actual != expected:
        raise ValueError('Input digest differs: ' + str(path))
    return {'path': str(path), 'bytes': path.stat().st_size,
            'digest': actual, 'algorithm': 'git-blob-sha1' if git else 'sha256'}


def prepare_inputs(protocol, base, cache, upstream, output):
    """No torch import, no output writes, no reliance on a prior PASS receipt."""
    base, cache, upstream, output = map(Path, (base, cache, upstream, output))
    if output.exists() or output.is_symlink():
        raise ValueError('Choose a new output path')
    if output.resolve() == base.resolve() or base.resolve() in output.resolve().parents:
        raise ValueError('Output must be separate from base assets')
    if file_hash(upstream) != protocol['upstream_sha256']:
        raise ValueError('Upstream merger digest differs')
    records = [check_file(base / row['path'], row) for row in protocol['base_files']]
    paths = {}
    for name, row in protocol['adapters'].items():
        snapshot = cache / ('models--' + row['repo'].replace('/', '--')) / 'snapshots' / row['revision']
        paths[name] = snapshot
        records.extend(check_file(snapshot / f['path'], f) for f in row['files'])
    index = json.loads((base / protocol['index']).read_text())
    if set(index['weight_map'].values()) != set(protocol['shards']):
        raise ValueError('Index shard coverage differs')
    names = [recipe['name'] for recipe in protocol['recipes']]
    if not names or len(set(names)) != len(names) or any(n not in ('cfg_only', 'few_step_cfg') for n in names):
        raise ValueError('Invalid or duplicate recipe name')
    for recipe in protocol['recipes']:
        if not recipe['adapters']:
            raise ValueError('Empty adapter recipe')
        for item in recipe['adapters']:
            if item['name'] not in paths or not math.isfinite(item['weight']):
                raise ValueError('Invalid adapter recipe')
    return paths, index, records


def tensor_hash(tensor):
    # dtype-preserving bytes, including BF16; tensors are CPU and contiguous.
    return hashlib.sha256(tensor.detach().contiguous().view(-1).view(__import__('torch').uint8).numpy().tobytes()).hexdigest()


def fuse(protocol, base, paths, upstream, output, index, receipt):
    import torch
    from safetensors import safe_open
    from safetensors.torch import load_file, save_file
    from wcomr.lora_header_audit import audit_adapter, validate_tensor_table

    if torch.cuda.is_initialized() or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU-only CUDA visibility must be empty')
    torch.set_num_threads(protocol['cpu_threads'])
    spec = importlib.util.spec_from_file_location('pinned_l0_merger', upstream)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base_headers = {}
    for filename in protocol['shards']:
        p = base / filename
        with p.open('rb') as stream:
            length = int.from_bytes(stream.read(8), 'little')
            header = json.loads(stream.read(length))
        entries = validate_tensor_table(header, p.stat().st_size - 8 - length)
        if base_headers.keys() & entries.keys():
            raise ValueError('Duplicate base tensor')
        if any(index['weight_map'].get(k) != filename for k in entries):
            raise ValueError('Index tensor assignment differs')
        base_headers.update(entries)
    if set(base_headers) != set(index['weight_map']):
        raise ValueError('Index tensor coverage differs')
    configs = {}
    for name, path in paths.items():
        p = path / 'adapter_model.safetensors'
        with p.open('rb') as stream:
            length = int.from_bytes(stream.read(8), 'little')
            header = json.loads(stream.read(length))
        configs[name] = json.loads((path / 'adapter_config.json').read_text())
        if configs[name]['base_model_name_or_path'] != protocol['base_repo']:
            raise ValueError('Adapter family differs')
        audit_adapter(header, length, p.stat().st_size, configs[name], base_headers, 1.0)
    output.mkdir(parents=True, exist_ok=False)
    receipt.update(status='RUNNING', torch_version=torch.__version__, cuda_initialized=False,
                   base_tensor_count=len(base_headers), arms=[])
    write_receipt(output / 'fusion.json', receipt)
    with torch.inference_mode():
        for recipe in protocol['recipes']:
            arm = output / recipe['name']
            arm.mkdir(exist_ok=False)
            updates = [module.adapter_updates(paths[i['name']] / 'adapter_model.safetensors',
                                             i['weight'], configs[i['name']]['lora_alpha'])
                       for i in recipe['adapters']]
            targets = {item[0] for group in updates for item in group}
            result = {'name': recipe['name'], 'recipe': recipe['adapters'], 'shards': [],
                      'tensors': [], 'target_count': len(targets), 'status': 'RUNNING'}
            receipt['arms'].append(result)
            seen = set()
            for filename in protocol['shards']:
                state = load_file(str(base / filename), device='cpu')
                keys = set(state)
                if keys & seen or any(index['weight_map'].get(k) != filename for k in keys):
                    raise ValueError('Loaded shard/index coverage differs')
                seen.update(keys)
                selected = [[u for u in group if u[0] in keys] for group in updates]
                before = {k: tensor_hash(v) for k, v in state.items()}
                if any(not torch.isfinite(v).all() for v in state.values()):
                    raise ValueError('Nonfinite base tensor')
                module.merge(state, selected)
                # Independently recompute algebra per real target, with a
                # documented FP32 tolerance for fused-addmm rounding.
                with safe_open(str(base / filename), framework='pt', device='cpu') as original:
                    for key, value in state.items():
                        raw = original.get_tensor(key)
                        after = tensor_hash(value)
                        row = {'key': key, 'shape': list(value.shape), 'dtype': str(value.dtype),
                               'before_sha256': before[key], 'after_sha256': after,
                               'adapter_target': key in targets, 'bytes_changed': before[key] != after}
                        if key in targets:
                            expected = raw.float().clone()
                            for group in selected:
                                for name, a, b, scale in group:
                                    if name == key:
                                        expected.add_(torch.mm(b.float(), a.float()), alpha=scale)
                            expected = expected.to(value.dtype)
                            if not torch.allclose(value, expected, rtol=protocol['formula_rtol'],
                                                  atol=protocol['formula_atol']):
                                raise ValueError('Independent formula differs: ' + key)
                            row['max_formula_abs_error'] = float((value.float() - expected.float()).abs().max())
                            row['relative_delta_norm'] = float((value.float() - raw.float()).norm() / raw.float().norm().clamp_min(1e-30))
                            del expected
                        elif before[key] != after:
                            raise ValueError('Untargeted tensor changed: ' + key)
                        if not torch.isfinite(value).all():
                            raise ValueError('Nonfinite fused tensor')
                        result['tensors'].append(row)
                        del raw
                dest = arm / filename
                save_file(state, str(dest), metadata={'format': 'pt'})
                # Re-open serialized output; verify every actual tensor.
                with safe_open(str(dest), framework='pt', device='cpu') as saved:
                    if set(saved.keys()) != keys:
                        raise ValueError('Serialized keys differ')
                    for key in keys:
                        if tensor_hash(saved.get_tensor(key)) != tensor_hash(state[key]):
                            raise ValueError('Serialized tensor differs: ' + key)
                result['shards'].append({'path': str(dest), 'bytes': dest.stat().st_size,
                                         'sha256': file_hash(dest)})
                write_receipt(output / 'fusion.json', receipt)
                del state, selected
                gc.collect()
            if seen != set(index['weight_map']) or not targets <= seen:
                raise ValueError('Incomplete fused model coverage')
            (arm / protocol['index']).write_text(json.dumps(index, indent=2) + '\n')
            shutil.copyfile(base / 'config.json', arm / 'config.json')
            result['auxiliary_references'] = []
            for relative in protocol['auxiliary_paths']:
                source = base / relative
                (arm / relative).parent.mkdir(parents=True, exist_ok=True)
                (arm / relative).symlink_to(source.resolve())
                result['auxiliary_references'].append({'path': relative, 'source': str(source.resolve())})
            result['status'] = 'FULL_CPU_FUSION_SERIALIZATION_AND_UNTARGETED_INVARIANCE_PASS'
            write_receipt(output / 'fusion.json', receipt)
            del updates
            gc.collect()
    if torch.cuda.is_initialized():
        raise ValueError('Unexpected CUDA initialization')
    # Prove original inputs still match their pinned identities after the
    # complete merge, output serialization, and tensor re-read.
    after_records = [check_file(base / row['path'], row) for row in protocol['base_files']]
    for name, row in protocol['adapters'].items():
        after_records.extend(check_file(paths[name] / f['path'], f) for f in row['files'])
    if file_hash(upstream) != protocol['upstream_sha256']:
        raise ValueError('Upstream merger changed during fusion')
    receipt.update(status='CPU_FUSION_COMPLETE_NOT_MODEL_LOAD_TASK_OR_GPU_READY',
                   finished_unix=time.time(), cuda_initialized=False,
                   input_integrity_after=after_records)
    write_receipt(output / 'fusion.json', receipt)
    return receipt


def write_receipt(path, receipt):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)
