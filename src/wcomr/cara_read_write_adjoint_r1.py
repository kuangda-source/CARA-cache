"""Explicit-state discrete pullbacks and signed hard-action contractions.

This is calibration math, separate from GPU dispatch and the terminal objective.
It differentiates actual supplied transitions; it supplies neither an Euler
Jacobian nor a gradient through discrete cache metadata. A real-model bridge
must bind source/provenance, a video objective and bounded checkpoint storage.
"""
from dataclasses import replace
import math

import torch

from .cara_read_write_state_r1 import PostUpdateState


def _map_cache(value, path, tensor):
    if isinstance(value, torch.Tensor) and value.is_floating_point():
        return tensor(path, value)
    if isinstance(value, dict):
        return {key:_map_cache(part, path+(key,), tensor) for key,part in value.items()}
    if isinstance(value, list):
        return [_map_cache(part, path+(index,), tensor) for index,part in enumerate(value)]
    if isinstance(value, tuple):
        return tuple(_map_cache(part, path+(index,), tensor) for index,part in enumerate(value))
    return value


def map_coordinates(state, tensor):
    """Map every continuous state coordinate, preserving discrete metadata.

Solver timesteps, orders and indices are fixed, not differentiable coordinates.
Repeated tensor references in different cache fields are separate coordinates;
their producer VJP sums both uses on the previous transition. No feature is
silently omitted because it happens to alias another field.
"""
    history = tuple(tensor(('solver', 'model_outputs', index), value) if value is not None else None
                    for index,value in enumerate(state.memory.model_outputs))
    last = state.memory.last_sample
    memory = replace(state.memory, model_outputs=history,
        last_sample=None if last is None else tensor(('solver', 'last_sample'), last))
    return PostUpdateState(tensor(('latent',), state.latent), memory,
                           _map_cache(state.cache, ('cache',), tensor))


def coordinates(state):
    result = {}
    def collect(path, value):
        result[path] = value
        return value
    map_coordinates(state, collect)
    return result


def _leaves(state):
    values = {}
    def leaf(path, value):
        # Detach only at an explicit adjoint checkpoint boundary. The supplied
        # transition is recomputed with all within-transition edges intact.
        values[path] = value.detach().requires_grad_()
        return values[path]
    return map_coordinates(state, leaf), values


def _validate_cotangent(values, cotangent):
    if values.keys() != cotangent.keys():
        raise ValueError('Complete matching continuous-state cotangent required')
    for path,value in values.items():
        weight = cotangent[path]
        if (not isinstance(weight, torch.Tensor) or weight.shape != value.shape
                or weight.dtype != value.dtype or weight.device != value.device
                or not bool(torch.isfinite(weight).all())):
            raise ValueError('Cotangent shape, precision, device or finiteness differs: '+repr(path))


def terminal_cotangent(state, objective):
    """Return the terminal scalar and its complete explicit-state gradient."""
    with torch.enable_grad():
        terminal, inputs = _leaves(state)
        loss = objective(terminal)
        if not isinstance(loss, torch.Tensor) or loss.numel() != 1 or not bool(torch.isfinite(loss)):
            raise ValueError('One finite scalar terminal objective required')
        gradients = (torch.autograd.grad(loss, tuple(inputs.values()), allow_unused=True)
                     if loss.requires_grad else [None]*len(inputs))
    return float(loss.detach()), {path:torch.zeros_like(value) if gradient is None else gradient
        for (path,value),gradient in zip(inputs.items(), gradients)}


def pullback(state, transition, cotangent):
    """Recompute one actual discrete step, then apply its VJP to p_next.

No complete Jacobian is materialized. The caller owns the saved trajectory and
its resource limit; this primitive does not retain a full Cosmos graph/tape.
"""
    with torch.enable_grad():
        checkpoint, inputs = _leaves(state)
        output = coordinates(transition(checkpoint))
        _validate_cotangent(output, cotangent)
        active = [(value, cotangent[path]) for path,value in output.items() if value.requires_grad]
        gradients = (torch.autograd.grad(tuple(value for value,_ in active), tuple(inputs.values()),
                     grad_outputs=tuple(weight for _,weight in active), allow_unused=True)
                     if active else [None]*len(inputs))
    result = {path:torch.zeros_like(value) if gradient is None else gradient
              for (path,value),gradient in zip(inputs.items(), gradients)}
    if any(not bool(torch.isfinite(value).all()) for value in result.values()):
        raise ValueError('Nonfinite actual transition pullback')
    return result


def hard_action_value(cached, dense, cotangent, *, incumbent):
    """Contract p_after with F_D-F_C, grouped into read and cache write.

Both states must be real same-parent actions AFTER the solver update. This
function does not certify their provenance. It rejects changed populated slot
layouts instead of inventing a continuous value for None or source indices.
The original accumulator's literal reset zero is the sole scalar/Tensor case.
"""
    if incumbent not in ('C', 'D'):
        raise ValueError('The co-state must name its actual incumbent action')
    provenance = cached.cache.get('provenance')
    other = dense.cache.get('provenance')
    if ((provenance is None) != (other is None)
            or (provenance is not None and not provenance.same_parent_chart(other))):
        raise ValueError('Same request/grid and complete hard-action source chart required')
    if (cached.memory.step_index != dense.memory.step_index
            or cached.memory.begin_index != dense.memory.begin_index
            or cached.memory.this_order != dense.memory.this_order
            or cached.memory.lower_order_nums != dense.memory.lower_order_nums
            or len(cached.memory.timestep_list) != len(dense.memory.timestep_list)
            or any(a is not b and (a is None or b is None or not torch.equal(a, b))
                   for a,b in zip(cached.memory.timestep_list, dense.memory.timestep_list))
            or cached.cache['fields']['cnt'] != dense.cache['fields']['cnt']):
        raise ValueError('Aligned same-update hard action states required')
    c, d = coordinates(cached), coordinates(dense)
    base = c if incumbent == 'C' else d
    _validate_cotangent(base, cotangent)

    def value_at(state, values, path, template):
        if path in values:
            value = values[path]
        elif path[:3] == ('cache', 'fields', 'accumulated_rel_l1_distance'):
            value = state.cache['fields']['accumulated_rel_l1_distance'][path[3]]
            if type(value) not in (float, int) or value != 0:
                raise ValueError('Only the exact WC accumulator reset zero may be aligned')
            value = torch.zeros_like(template)
        else:
            raise ValueError('Hard action continuous slot layout differs: '+repr(path))
        if value.shape != template.shape or value.dtype != template.dtype or value.device != template.device:
            raise ValueError('Hard action coordinate shape or precision differs: '+repr(path))
        return value

    # Inspect the union even where one endpoint's zero accumulator is literal.
    # All other coordinates must be populated on both hard endpoints.
    for path in c.keys() | d.keys():
        template = c.get(path, d.get(path))
        value_at(cached, c, path, template)
        value_at(dense, d, path, template)
    read, write = [], []
    with torch.no_grad():
        for path,weight in cotangent.items():
            delta = value_at(dense, d, path, weight)-value_at(cached, c, path, weight)
            term = float((weight*delta).sum())
            if not math.isfinite(term):
                raise ValueError('Nonfinite hard-action contraction')
            (write if path[0] == 'cache' else read).append(term)
    gr, gw = math.fsum(read), math.fsum(write)
    return dict(read=gr, write=gw, total=gr+gw, incumbent=incumbent,
                continuous_coordinates=len(cotangent), discrete_metadata_gradient=False,
                exact_hard_endpoint_gain=False)
