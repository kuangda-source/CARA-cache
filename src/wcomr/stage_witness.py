"""Read-only pipeline witnesses. Never replay a model or replace its outputs."""
import hashlib
from contextlib import ExitStack
import functools
import numpy as np
import torch


def witness(value):
    if isinstance(value, (list, tuple)):
        return {'kind': type(value).__name__, 'items': [witness(x) for x in value]}
    if value is None:
        return {'kind': 'None'}
    if isinstance(value, torch.Tensor):
        version = None if value.is_inference() else value._version
        raw = value.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes()
        finite = bool(torch.isfinite(value).all()) if value.is_floating_point() or value.is_complex() else True
        assert version is None or value._version == version, 'Observer mutated tensor'
        dtype = str(value.dtype); shape = list(value.shape)
        kind = 'tensor'
    elif isinstance(value, np.ndarray):
        raw = np.ascontiguousarray(value).tobytes()
        finite = bool(np.isfinite(value).all())
        dtype = str(value.dtype); shape = list(value.shape)
        kind = 'array'
    else:
        raise TypeError('Unsupported pipeline value: ' + type(value).__name__)
    assert finite, 'Nonfinite pipeline value'
    return {'kind': kind, 'shape': shape, 'dtype': dtype, 'finite': finite,
            'sha256': hashlib.sha256(raw).hexdigest()}


class StageWitness:
    def __init__(self):
        self.events = []
        self._stack = ExitStack()

    def record(self, stage, value):
        cpu_rng = torch.random.get_rng_state()
        cuda_rng = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else []
        result = witness(value)
        assert torch.equal(cpu_rng, torch.random.get_rng_state()), 'Observer changed CPU RNG'
        if cuda_rng:
            assert all(torch.equal(a, b) for a, b in zip(cuda_rng, torch.cuda.get_rng_state_all())), 'Observer changed CUDA RNG'
        self.events.append({'stage': stage, 'value': result})

    def wrap(self, owner, name, before=None, after=None):
        original = getattr(owner, name)
        # Restore the original instance namespace, including a method inherited
        # from the class rather than leaving a new bound-method attribute.
        own = name in vars(owner)
        own_value = vars(owner).get(name)
        def restore():
            if own: setattr(owner, name, own_value)
            else: delattr(owner, name)
        self._stack.callback(restore)
        @functools.wraps(original)
        def wrapped(*args, **kwargs):
            if before: before(args, kwargs)
            result = original(*args, **kwargs)
            if after: after(result)
            return result
        setattr(owner, name, wrapped)

    def close(self):
        self._stack.close()


def compare_stages(left, right):
    """First different witnessed boundary; no attribution inside that interval."""
    keys = ['forward_output_sha256', 'block_counts', 'trace', 'cache_end_sha256', 'sampling', 'runtime_identity', 'encoding']
    checks = {key: left[key] == right[key] for key in keys}
    for key in keys:
        if not checks[key]:
            return {'status': 'UPSTREAM_OR_RUNTIME_MISMATCH', 'first_difference': key, 'checks': checks}
    a, b = left['events'], right['events']
    if [x['stage'] for x in a] != [x['stage'] for x in b]:
        return {'status': 'STAGE_TOPOLOGY_MISMATCH', 'checks': checks}
    previous = '72_net_outputs'
    for x, y in zip(a, b):
        if x != y:
            return {'status': 'FIRST_DIFFERING_BOUNDARY', 'first_difference': x['stage'],
                    'previous_matching_boundary': previous, 'checks': checks}
        previous = x['stage']
    for key in ['decoded_rgb', 'video_sha256']:
        if left[key] != right[key]:
            return {'status': 'FIRST_DIFFERING_BOUNDARY', 'first_difference': key,
                    'previous_matching_boundary': previous, 'checks': checks}
        previous = key
    return {'status': 'EXACT_PIPELINE_REPRODUCTION_TWO_FRESH_PROCESSES', 'checks': checks}
