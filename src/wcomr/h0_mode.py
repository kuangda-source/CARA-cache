"""Establish one explicit inference mode shared by both H0 comparison paths."""
import collections
import hashlib
import json

import torch


def mode_snapshot(net):
    flags = {name: bool(module.training) for name, module in net.named_modules()}
    types = collections.Counter(
        type(module).__module__ + '.' + type(module).__qualname__
        for module in net.modules()
    )
    return {
        'flags': flags,
        'flags_sha256': hashlib.sha256(
            json.dumps(flags, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest(),
        'training_modules': sum(flags.values()),
        'module_count': len(flags),
        'module_types': dict(types),
    }


def establish_shared_eval(net, expected_types=None):
    """Versioned adaptation before either arm; do not relax the shadow eval guard.

    Reject custom train() implementations rather than assuming that eval() only
    changes flags. The pinned network uses nn.Module.train throughout. This
    function does not claim train/eval output equivalence on GPU.
    """
    before = mode_snapshot(net)
    if expected_types is not None and before['module_types'] != expected_types:
        raise ValueError('H0 native mode topology differs from CPU contract')
    for name, module in net.named_modules():
        if getattr(module.train, '__func__', None) is not torch.nn.Module.train:
            raise ValueError('H0 unreviewed train override: ' + name)
    tensors = list(net.parameters()) + list(net.buffers())
    versions = [tensor._version for tensor in tensors]
    net.eval()
    after = mode_snapshot(net)
    if after['training_modules'] or after['module_types'] != before['module_types']:
        raise ValueError('H0 shared eval was not established')
    if any(a is not b for a, b in zip(tensors, list(net.parameters()) + list(net.buffers()))):
        raise ValueError('H0 eval replaced parameters or buffers')
    if versions != [tensor._version for tensor in tensors]:
        raise ValueError('H0 eval modified a parameter or buffer')
    return {
        'policy': 'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'before': before,
        'after': after,
        'all_train_implementations': 'torch.nn.Module.train',
        'parameter_and_buffer_objects_versions_unchanged': True,
        'train_eval_GPU_output_equivalence': 'NOT_CLAIMED',
    }


def verify_shared_eval(net, established):
    if mode_snapshot(net) != established['after']:
        raise ValueError('H0 mode or topology changed after shared eval setup')
