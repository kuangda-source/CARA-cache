"""Explicit projection-state roundtrip for paid, score-only P0 diagnostics.

This is only the additional P0 inventory. Callers must separately preserve the
actual net, solver, latent, conditions, RNG and buffers. It is not a complete
Cosmos-state checkpoint and is excluded from deployment latency measurements.
"""
from dataclasses import replace
import copy

import torch

from .partial_mlp import PartialMLP
from .mid_coverage import tree_digest


class ProjectionRoundtrip:
    def __init__(self, executor, *, logical_copy_cap_bytes):
        if (not isinstance(executor, PartialMLP) or not executor._original
                or executor._pair is not None or executor._slot is not None
                or executor.poisoned or torch.is_grad_enabled()
                or type(logical_copy_cap_bytes) is not int or logical_copy_cap_bytes <= 0):
            raise ValueError('Inactive healthy no-grad P0 executor and explicit copy budget required')
        expected = {(layer, slot) for layer in executor.layers for slot in (0, 1)}
        if set(executor.cache) != expected or executor.last_step <= 0:
            raise ValueError('Complete initialized two-branch projection inventory required')
        self.executor = executor
        self.bytes = sum(t.numel()*t.element_size() for c in executor.cache.values()
                         for t in (c.value, c.updated_at, c.source))
        if self.bytes > logical_copy_cap_bytes:
            raise ValueError('Additional projection snapshot exceeds explicit logical copy budget')
        self._installed = dict(executor._original)
        self._parameters = {layer: tuple((id(p), p._version) for p in executor.blocks[layer].mlp.parameters())
                            for layer in executor.layers}
        self._cache = {key: replace(c, value=c.value.detach().clone(),
                                   updated_at=c.updated_at.detach().clone(),
                                   source=c.source.detach().clone()) for key, c in executor.cache.items()}
        self._records = copy.deepcopy(executor.records)
        self._last_step = executor.last_step
        self._poisoned = executor.poisoned
        self.origin = self.components()

    def components(self):
        e = self.executor
        return {'last_step': e.last_step, 'poisoned': e.poisoned, 'records': copy.deepcopy(e.records),
                'layers': list(e.layers), 'projection_state': {
                    str(layer)+':'+str(slot): {
                        'value': tree_digest(c.value), 'updated_at': tree_digest(c.updated_at),
                        'source': tree_digest(c.source), 'context': list(c.context),
                        'parameter_versions': [list(v) for v in c.parameter_versions],
                        'last_actual_D': c.last_actual_D}
                    for (layer, slot), c in sorted(e.cache.items())}}

    def restore(self):
        e = self.executor
        if (e._pair is not None or e._slot is not None or torch.is_grad_enabled()
                or e._original != self._installed
                or {layer: tuple((id(p), p._version) for p in e.blocks[layer].mlp.parameters())
                    for layer in e.layers} != self._parameters):
            raise ValueError('P0 restore cannot cover an active pair, changed installation or parameters')
        # Fresh clones keep the saved checkpoint independent of every later arm.
        e.cache = {key: replace(c, value=c.value.detach().clone(),
                               updated_at=c.updated_at.detach().clone(),
                               source=c.source.detach().clone()) for key, c in self._cache.items()}
        e.records = copy.deepcopy(self._records)
        e.last_step, e.poisoned = self._last_step, self._poisoned
        e._seen = set()
        if self.components() != self.origin:
            e.poisoned = True
            raise ValueError('Complete additional P0 physical inventory did not restore')
        return self.origin

