"""CPU H1 raw verifier, executed with injected groups/extra_snapshots.

The lifecycle auditor supplies receipt-indexed groups; this module performs no
model forward and rejects CUDA initialization. Sample/region accompany each row.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

assert not torch.cuda.is_initialized()
def forbidden(*args, **kwargs):
    raise RuntimeError('CUDA forbidden in H1 raw audit')
torch.cuda._lazy_init = forbidden
checked, recomputed = [], []

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def metric(p, t):
    assert p.shape == t.shape and p.dtype == t.dtype
    p, t = p.reshape(-1), t.reshape(-1)
    totals = [0., 0., 0., 0.]
    for start in range(0, t.numel(), 1 << 20):
        a = p[start:start + (1 << 20)].float().numpy().astype(np.float64)
        b = t[start:start + (1 << 20)].float().numpy().astype(np.float64)
        assert np.isfinite(a).all() and np.isfinite(b).all()
        error = a - b
        totals[0] += np.dot(error, error)
        totals[1] += np.dot(b, b)
        totals[2] += np.dot(a, a)
        totals[3] += np.dot(a, b)
    assert totals[1] > 0
    relative = totals[0] / totals[1]
    cosine = totals[3] / math.sqrt(totals[1] * totals[2]) if totals[2] else None
    return {'mse': totals[0] / t.numel(), 'reference_mean_square': totals[1] / t.numel(),
        'relative_mse': relative, 'relative_rmse': math.sqrt(relative),
        'direction_cosine': max(-1., min(1., cosine)) if cosine is not None else None}

def load_snapshot(snapshot):
    path = Path(snapshot['path'])
    assert sha(path) == snapshot['sha256'] and path.stat().st_size == snapshot['bytes']
    assert snapshot['role'].startswith('H1_LOCAL_FIXED_TRAJECTORY_SCORE_ONLY')
    value = torch.load(path, map_location='cpu', weights_only=True)
    assert set(value) == {'postwarp_residual', 'velocity'}
    expected = {'postwarp_residual': ('torch.bfloat16', [1, 24, 27, 48, 2048]),
                'velocity': ('torch.float32', [1, 16, 24, 54, 96])}
    for key, tensor in value.items():
        meta = snapshot['tensors'][key]
        assert (str(tensor.dtype), list(tensor.shape)) == expected[key]
        assert str(tensor.dtype) == meta['dtype'] and list(tensor.shape) == meta['shape']
        assert torch.isfinite(tensor).all()
        raw = memoryview(tensor.contiguous().reshape(-1).view(torch.uint8).numpy())
        assert hashlib.sha256(raw).hexdigest() == meta['raw_sha256']
    checked.append({'path': str(path), 'sha256': snapshot['sha256']})
    return value

for group in groups:
    truth = load_snapshot(group['truth'])
    for row in group['arms']:
        snapshot = row.get('raw_snapshot')
        if snapshot is None:
            continue
        if snapshot['path'] == group['truth']['path']:
            value = truth
        else:
            value = load_snapshot(snapshot)
        if all(key in row and row[key]['status'] == 'OK' for key in ('postwarp_residual', 'velocity')):
            errors = {}
            for key in ('postwarp_residual', 'velocity'):
                result = metric(value[key], truth[key])
                for name, number in result.items():
                    if number is None:
                        assert row[key][name] is None
                    else:
                        assert math.isclose(number, row[key][name], rel_tol=2e-6, abs_tol=1e-9), (
                            group['call'], row['arm'], key, name, number, row[key][name])
                errors[key] = result
            recomputed.append({'sample': group.get('sample'), 'region': group.get('region'),
                'scope': group['scope'], 'call': group['call'],
                'cfg_slot': group['cfg_slot'], 'age': group.get('age'), 'arm': row['arm'], 'errors': errors})
        del value
    del truth
for snapshot in extra_snapshots:
    load_snapshot(snapshot)
assert not torch.cuda.is_initialized()
print(json.dumps({'checked': checked, 'recomputed': recomputed, 'cuda_initialized': False,
    'comparison_tolerance': {'relative': 2e-6, 'absolute': 1e-9},
    'formula': 'Independent chunked float64 NumPy means/cosine versus GPU fp32 recorder'}))
