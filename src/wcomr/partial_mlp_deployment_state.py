"""Additional P0 deployment state; the caller also owns the physical sampler.

Healthy in-process checkpoint restoration only. This cannot unpoison a failed
pair or restore a serialized generator, decoder or complete pipeline.
"""
import copy
from dataclasses import fields, is_dataclass

import torch

from .mid_coverage import tree_digest


def plain(value):
    if is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(plain(v) for v in value)
    return value


def tensor_bytes(value):
    if isinstance(value, torch.Tensor):
        return value.numel()*value.element_size()
    if is_dataclass(value):
        return sum(tensor_bytes(getattr(value, f.name)) for f in fields(value))
    if isinstance(value, dict):
        return sum(tensor_bytes(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return sum(tensor_bytes(v) for v in value)
    return 0


class DeploymentRoundtrip:
    def __init__(self, owner, *, logical_copy_cap_bytes):
        owner.check_healthy()
        if type(logical_copy_cap_bytes) is not int or logical_copy_cap_bytes <= 0:
            raise ValueError('Explicit remaining additional-state copy cap required')
        live = owner.own_state()
        self.bytes = tensor_bytes(live)
        if self.bytes > logical_copy_cap_bytes:
            raise ValueError('P0 deployment snapshot exceeds remaining logical copy budget')
        self.owner = owner
        self.binding = owner.installation()
        self.saved = copy.deepcopy(live)
        self.origin = tree_digest(plain(self.saved))

    def restore(self):
        self.owner.check_healthy()
        if self.owner.installation() != self.binding:
            raise ValueError('Changed P0 owner, parameters or installation cannot restore')
        self.owner.restore_own_state(copy.deepcopy(self.saved))
        if self.owner.fingerprint() != self.origin:
            raise ValueError('Additional P0 deployment state failed complete restoration')
        return self.origin
