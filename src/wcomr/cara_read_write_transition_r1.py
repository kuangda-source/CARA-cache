"""Differentiable hard D/C transition for the pinned, pure-C WorldCache path.

This calibration adapter leaves production no_grad execution unchanged. It
keeps the original WC and RF equations, exposes cache tensors and buffers as
state, and isolates their writes. It does not differentiate a threshold policy,
implement a terminal loss, load Cosmos weights, or authorize a GPU experiment.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import types
from types import MappingProxyType

import torch

from .cfg_paired_probe_forward import (
    PREDICATE, RF_PATH, RF_SHA, WC_PATH, WC_SHA, _compile, _find_safe,
    _function, forced_reference,
)
from .cfg_paired_probe_production import _bindings, _origin
from .mid_coverage import WC_FIELDS
from .cara_read_write_provenance_r1 import CacheProvenance


def _containers(value):
    """Own mutable topology without detaching or duplicating feature tensors."""
    if isinstance(value, dict):
        return {key: _containers(part) for key, part in value.items()}
    if isinstance(value, list):
        return [_containers(part) for part in value]
    if isinstance(value, tuple):
        return tuple(_containers(part) for part in value)
    return value


def _cache_fields(fields):
    result = _containers(fields)
    # WC uses +=/-= on these scalar tensors. Cloning retains their graph while
    # preventing a later transition from modifying its input state in place.
    result['accumulated_rel_l1_distance'] = [
        part.clone() if isinstance(part, torch.Tensor) else part
        for part in result['accumulated_rel_l1_distance']]
    return result


@dataclass(frozen=True)
class WorldCacheMemory:
    fields: dict
    buffers: dict[str, torch.Tensor]
    provenance: CacheProvenance | None = None

    @classmethod
    def capture(cls, net, *, owner=None, timesteps=None, sigmas=None):
        fields = {name: getattr(net, name) for name in WC_FIELDS if hasattr(net, name)}
        provenance = (CacheProvenance.start(fields, owner=owner, timesteps=timesteps, sigmas=sigmas)
                      if owner is not None else None)
        return cls(_cache_fields(fields),
                   {name: value.clone() for name, value in net.named_buffers()}, provenance)

    def bundle(self):
        value = dict(fields=self.fields, buffers=self.buffers)
        if self.provenance is not None:
            value['provenance'] = self.provenance
        return value


def _compile_denoise(runtime, rf, net_call):
    original = _function(runtime, RF_PATH, RF_SHA, 'denoise')
    node = copy.deepcopy(original)
    target = _find_safe(node, lambda n: isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
        and n.func.value.id == 'self' and n.func.attr == 'net')
    saved = copy.deepcopy(target)

    class Replace(ast.NodeTransformer):
        def visit_Call(self, current):
            if current is target:
                return ast.Call(func=ast.Name(id='_functional_net', ctx=ast.Load()),
                    args=[copy.deepcopy(target.func)]+target.args, keywords=target.keywords)
            return self.generic_visit(current)

    node = Replace().visit(node)
    inverse = copy.deepcopy(node)

    class Restore(ast.NodeTransformer):
        def visit_Call(self, current):
            if isinstance(current.func, ast.Name) and current.func.id == '_functional_net':
                return copy.deepcopy(saved)
            return self.generic_visit(current)

    if ast.dump(Restore().visit(inverse), include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('RF calibration changed outside the explicit net call')
    function = _compile(node, dict(vars(rf), _functional_net=net_call), RF_PATH+'#read-write-functional')
    return function, _bindings(function, vars(rf), {'_functional_net': net_call})


class FunctionalWorldCache:
    """One frozen model; explicit hard actions and differentiable cache state.

Only pure C (alpha=0) and D are supported. A-readout calibrators/selector logs
do not feed this restricted operator and are not represented as differentiable
state. A production bridge must additionally carry their discrete provenance.
The actual source's OSI clamps, abs, min/max, warp and cycle reset remain intact;
derivatives are local to their realized branches. No straight-through action
gate or stop-gradient approximation is introduced.
"""
    def __init__(self, model, *, runtime, wc, rf):
        _origin(wc, runtime, WC_PATH, WC_SHA)
        _origin(rf, runtime, RF_PATH, RF_SHA)
        net = model.net
        if any(module.training for module in net.modules()) or any(p.requires_grad for p in net.parameters()):
            raise ValueError('Frozen eval model required for input/cache calibration')
        if (net.worldcache_num_steps != 70 or not net.worldcache_enabled
                or net.probe_depth < 1):
            raise ValueError('Initialized original full36 / 70-call WorldCache required')
        self.model, self.net = model, net
        self.parameters = dict(net.named_parameters())
        self.buffer_names = set(dict(net.named_buffers()))
        self.forwards = {action: forced_reference(runtime, vars(wc), action*2) for action in ('C', 'D')}
        def net_call(bound, *args, **kwargs):
            return torch.func.functional_call(bound,
                (self.parameters, bound._read_write_buffers), args, kwargs, strict=True)
        self.denoise, rf_bindings = _compile_denoise(runtime, rf, net_call)
        wc_bindings = {action: _bindings(function, vars(wc), {})
                       for action, function in self.forwards.items()}
        # Check the only WC replacement independently; the source compiler also
        # verifies the SHA and rejects decorated or ambiguous source functions.
        original = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
        _find_safe(original, lambda n: isinstance(n, ast.If) and ast.unparse(n.test) == PREDICATE)
        self.proof = MappingProxyType(dict(WC_source_sha256=WC_SHA, RF_source_sha256=RF_SHA,
            WC_change='one hard action predicate', RF_net_call_inverse_AST_equal=True,
            WC_global_bindings=wc_bindings, RF_global_bindings=rf_bindings,
            actual_WC_arithmetic_unchanged=True, original_RF_condition_arithmetic_unchanged=True,
            pure_C_alpha=0, model_parameters_frozen=True, cache_and_buffer_gradients_retained=True,
            real_Cosmos_weights_or_terminal_loss_verified=False))

    def pair(self, memory, noise, latent, timestep, conditions, *, action):
        if action not in ('C', 'D') or not isinstance(conditions, tuple) or len(conditions) != 2:
            raise ValueError('One hard joint C/D action and both CFG conditions required')
        if torch.is_inference_mode_enabled():
            raise ValueError('Inference tensors cannot define the calibration graph')
        if (self.model.net is not self.net or any(m.training for m in self.net.modules())
                or any(p.requires_grad for p in self.net.parameters())):
            raise ValueError('Calibration model changed from frozen eval')
        fields = _cache_fields(memory.fields)
        if memory.provenance is not None:
            memory.provenance.slots(fields)
        if int(fields['cnt']) % 2 or set(memory.buffers) != self.buffer_names:
            raise ValueError('Aligned original CFG cache and complete buffers required')
        if action == 'C' and (fields['cnt'] < int(self.net.worldcache_num_steps*self.net.worldcache_ret_ratio)
                or any(fields[key][branch] is None for key in
                       ('previous_input', 'previous_internal_states', 'residual_cache') for branch in (0, 1))):
            raise ValueError('Hard C requires the original warmup and both cache histories')
        # Share frozen weights/modules, own the top-level instance and all
        # mutable cache topology. functional_call isolates every module buffer.
        net = copy.copy(self.net)
        net._modules = dict(self.net._modules)
        for name in WC_FIELDS:
            if name in fields:
                setattr(net, name, fields[name])
            else:
                vars(net).pop(name, None)
        net.forward = types.MethodType(self.forwards[action], net)
        buffers = {name: value.clone() for name, value in memory.buffers.items()}
        net._read_write_buffers = buffers
        model = copy.copy(self.model)
        if '_modules' in vars(model):
            model._modules = dict(model._modules)
        model.net = net
        values = tuple(self.denoise(model, noise, latent, timestep, condition) for condition in conditions)
        # Preserve Cosmos's FP32 arithmetic order, rather than rewriting it as
        # 8*conditional - 7*unconditional and changing finite precision results.
        guided = values[0]+7*(values[0]-values[1])
        after = _cache_fields({name: getattr(net, name) for name in WC_FIELDS if hasattr(net, name)})
        provenance = (memory.provenance.advance(memory.fields, after, action=action, timestep=timestep)
                      if memory.provenance is not None else None)
        return guided, WorldCacheMemory(after, buffers, provenance)
