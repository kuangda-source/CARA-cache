"""Isolated, score-only partial-block executor screen.

The history observer records outputs of actual, strictly earlier parent D/P
calls. It never fills history with a same-state teacher. Projection histories
retain the existing P0 token provenance. Full-block history is a residual, so
B-L2 returns the CURRENT identity plus an earlier residual. The caller owns
restoration of net/solver/RNG and must disable the ordinary P0 during arms.

No Q2 claim is made here: the pinned interface can expose Q/K/V, but a
variable-query backend and selected-RoPE-row implementation still need their
own correctness and cost validation. This first screen has nine full modes.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import math
import types

import torch

from .partial_mlp import PartialMLP, ProjectionCache


P0_LAYERS = (4, 10, 16, 22)
M8_LAYERS = (4, 7, 10, 13, 16, 19, 22, 25)
L2_LAYERS = (13, 19)
MODES = ('DENSE_PLAIN', 'DENSE_P0_STATE', 'DENSE_M8_STATE',
         'DENSE_L2_STATE', 'P0_ROTATION', 'P0_RANDOM',
         'M8_ROTATION', 'M8_RANDOM', 'L2')


def _layers(values, count):
    values = tuple(values)
    if (not values or tuple(sorted(set(values))) != values
            or any(type(i) is not int or not 0 <= i < count for i in values)):
        raise ValueError('Explicit nonempty ordered distinct layer set required')
    return values


def _versions(module):
    return tuple((id(p), p._version) for p in module.parameters())


def _context(value):
    if (type(value) is not tuple or len(value) != 3
            or any(type(x) is not str or not x for x in value)):
        raise ValueError('Three explicit context identities required')


def _tensor(value):
    if (not isinstance(value, torch.Tensor) or value.ndim != 5
            or value.shape[0] != 1 or value.requires_grad
            or value.dtype not in (torch.float32, torch.float16, torch.bfloat16)):
        raise ValueError('Eval B1 T/H/W/D inference tensor required')


def _input_version(value):
    # Inference tensors deliberately have no version counter. The production
    # caller pins the audited Block source (no in-place input mutation); normal
    # tensors additionally retain the runtime mutation check below.
    return None if torch.is_inference(value) else value._version


@dataclass(frozen=True)
class ResidualCache:
    value: torch.Tensor
    born: int
    context: tuple
    parameter_versions: tuple
    source_kind: str
    last_actual_D: object


class ProbeHistory:
    """Transparent parent observer; inactive outside explicitly bound calls.

    Wrap only actual deep parent calls with pair/branch. C calls do not update
    this bank. A legacy PartialMLP can be passed as projection_owner; matching
    P0 layers then copy its exact mixed per-token age/source records.
    """
    def __init__(self, blocks, *, mlp_layers=M8_LAYERS,
                 residual_layers=L2_LAYERS, projection_owner=None):
        self.blocks = blocks
        self.mlp_layers = _layers(mlp_layers, len(blocks))
        self.residual_layers = _layers(residual_layers, len(blocks))
        self.projection_owner = projection_owner
        self.mlp = {}; self.residual = {}; self.records = []
        self.last_step = 0; self.poisoned = False
        self._handles = []; self._pair = None; self._slot = None
        self._seen_mlp = set(); self._seen_residual = set(); self._inputs = {}
        self._readonly = 0

    def install(self):
        if self._handles:
            raise ValueError('History already installed')
        if any(m.training for layer in set(self.mlp_layers + self.residual_layers)
               for m in self.blocks[layer].modules()):
            raise ValueError('History requires eval blocks')
        for layer in self.mlp_layers:
            def output(module, args, value, layer=layer):
                self._mlp_output(layer, module, args, value)
            self._handles.append(self.blocks[layer].mlp.register_forward_hook(output))
        for layer in self.residual_layers:
            def before(module, args, kwargs, layer=layer):
                if not self._active():
                    return
                x = args[0] if args else kwargs.get('x_B_T_H_W_D')
                _tensor(x)
                if layer in self._inputs:
                    raise ValueError('Repeated/recursive observed Block')
                self._inputs[layer] = (x, _input_version(x))
            def after(module, args, kwargs, value, layer=layer):
                self._residual_output(layer, module, value)
            block = self.blocks[layer]
            self._handles.append(block.register_forward_pre_hook(before, with_kwargs=True))
            self._handles.append(block.register_forward_hook(after, with_kwargs=True))
        return self

    def close(self):
        if self._pair is not None:
            raise ValueError('Cannot close an active history pair')
        for h in self._handles:
            h.remove()
        self._handles.clear()

    def _active(self):
        return self._pair is not None and self._slot is not None and not self._readonly

    @contextmanager
    def readonly(self):
        self._readonly += 1
        try:
            yield
        finally:
            self._readonly -= 1

    def snapshot(self):
        if self._pair is not None or self._inputs:
            raise ValueError('History snapshot needs inactive complete pair')
        # Values are detached owned immutable tensors, never updated in place.
        return (dict(self.mlp), dict(self.residual), self.last_step,
                list(self.records), self.poisoned)

    def restore(self, state):
        if self._pair is not None or self._inputs:
            raise ValueError('Cannot restore active history')
        self.mlp, self.residual = dict(state[0]), dict(state[1])
        self.last_step, self.records, self.poisoned = state[2], list(state[3]), state[4]

    @contextmanager
    def pair(self, *, step, action, context):
        _context(context)
        if (not self._handles or self._pair is not None or self.poisoned
                or torch.is_grad_enabled() or type(step) is not int
                or step <= self.last_step or action not in ('D', 'P')):
            raise ValueError('Fresh actual D/P parent pair required')
        previous = self.snapshot()
        self._pair = dict(step=step, action=action, context=context, slots=set())
        try:
            yield self
            if self._pair['slots'] != {0, 1}:
                raise ValueError('Both complete observed CFG branches required')
            self.last_step = step
        except BaseException:
            self.mlp, self.residual = previous[0], previous[1]
            self.records = previous[3]
            self.poisoned = True
            raise
        finally:
            self._pair = None; self._slot = None; self._inputs.clear()

    @contextmanager
    def branch(self, slot):
        if (self._pair is None or self._slot is not None or type(slot) is not int
                or slot not in (0, 1) or slot in self._pair['slots']):
            raise ValueError('Unique bound history branch required')
        self._slot = slot; self._seen_mlp = set(); self._seen_residual = set()
        try:
            yield
            if (self._seen_mlp != set(self.mlp_layers)
                    or self._seen_residual != set(self.residual_layers)
                    or self._inputs):
                raise ValueError('Complete registered history scope required')
            self._pair['slots'].add(slot)
        finally:
            self._slot = None

    def _mlp_output(self, layer, module, args, value):
        if not self._active():
            return
        _tensor(value)
        if layer in self._seen_mlp:
            raise ValueError('Repeated observed MLP')
        self._seen_mlp.add(layer)
        p = self._pair; key = (layer, self._slot)
        owner = self.projection_owner
        owned = owner.cache.get(key) if owner is not None and layer in owner.layers else None
        if owned is not None:
            if (owned.context != p['context'] or owned.value.shape != value.shape
                    or owned.parameter_versions != _versions(module)
                    or not torch.equal(owned.value, value)):
                raise ValueError('Parent P0 projection ownership differs')
            entry = ProjectionCache(value.detach().clone(), owned.updated_at.clone(),
                owned.source.clone(), owned.context, owned.parameter_versions, owned.last_actual_D)
        else:
            if owner is not None and layer in owner.layers:
                raise ValueError('Observed P0 layer lacks actual owner provenance')
            tokens = math.prod(value.shape[:-1])
            prior = self.mlp.get(key)
            entry = ProjectionCache(value.detach().clone(),
                torch.full((tokens,), p['step'], dtype=torch.int32, device=value.device),
                torch.full((tokens,), 1 if p['action'] == 'D' else 2,
                           dtype=torch.uint8, device=value.device),
                p['context'], _versions(module), p['step'] if p['action'] == 'D'
                else (None if prior is None or prior.context != p['context'] else prior.last_actual_D))
        self.mlp[key] = entry
        self.records.append(dict(kind='MLP', layer=layer, slot=self._slot,
            step=p['step'], source=p['action'], owns_mixed_token_provenance=owned is not None))

    def _residual_output(self, layer, module, value):
        if not self._active():
            return
        x, version = self._inputs.pop(layer)
        _tensor(value)
        if ((version is not None and _input_version(x) != version)
                or value.shape != x.shape or layer in self._seen_residual):
            raise ValueError('Block identity mutated or repeated / incompatible residual')
        self._seen_residual.add(layer)
        p = self._pair; key = (layer, self._slot); prior = self.residual.get(key)
        self.residual[key] = ResidualCache((value.detach() - x.detach()).clone(),
            p['step'], p['context'], _versions(module), p['action'],
            p['step'] if p['action'] == 'D' else (None if prior is None
                or prior.context != p['context'] else prior.last_actual_D))
        self.records.append(dict(kind='BLOCK_RESIDUAL', layer=layer, slot=self._slot,
            step=p['step'], source=p['action'], includes_actual_parent_modulation=True,
            may_include_mixed_P0_projection=p['action'] == 'P',
            is_same_state_teacher=False))

    def cache_bytes(self):
        return sum(t.numel() * t.element_size() for c in self.mlp.values()
                   for t in (c.value, c.updated_at, c.source)) + sum(
                       c.value.numel() * c.value.element_size() for c in self.residual.values())


class BlockProbeArm:
    """One independently owned same-state arm, outside the parent algorithm.

    Reset from the immutable history BEFORE each timed repetition. Patch setup
    and restoration are diagnostic; the actual projection/residual maintenance
    in pair/branch is timed. No current teacher tensor is inserted in history.
    """
    def __init__(self, blocks, history, mode, *, p0_layers=P0_LAYERS,
                 m8_layers=M8_LAYERS, residual_layers=L2_LAYERS):
        if mode not in MODES or history.blocks is not blocks:
            raise ValueError('Registered mode and matching history blocks required')
        self.blocks, self.history, self.mode = blocks, history, mode
        self.p0_layers = _layers(p0_layers, len(blocks))
        self.m8_layers = _layers(m8_layers, len(blocks))
        self.residual_layers = _layers(residual_layers, len(blocks))
        self.partial = None; self.cache = {}; self.records = []
        self.last_step = 0; self.poisoned = False
        self._original = {}; self._forward_attributes = {}; self._installed = False
        self._pair = None; self._slot = None; self._seen = set()

    def install(self):
        if self._installed:
            raise ValueError('Arm already installed')
        if self.mode.startswith(('P0_', 'M8_')) or self.mode in ('DENSE_P0_STATE', 'DENSE_M8_STATE'):
            layers = self.p0_layers if 'P0' in self.mode else self.m8_layers
            self.partial = PartialMLP(self.blocks, layers).install()
        elif self.mode in ('L2', 'DENSE_L2_STATE'):
            for layer in self.residual_layers:
                block = self.blocks[layer]
                if any(m.training for m in block.modules()):
                    raise ValueError('Eval Blocks required')
                self._original[layer] = block.forward
                self._forward_attributes[layer] = ('forward' in vars(block), vars(block).get('forward'))
                def execute(module, *args, _layer=layer, **kwargs):
                    return self._execute_residual(_layer, module, args, kwargs)
                block.forward = types.MethodType(execute, block)
        self._installed = True
        self.reset_from_history()
        return self

    def close(self):
        if self._pair is not None:
            raise ValueError('Cannot close an active arm')
        if self.partial is not None:
            self.partial.close()
        for layer in self._original:
            owned, value = self._forward_attributes[layer]
            if owned:
                self.blocks[layer].forward = value
            else:
                delattr(self.blocks[layer], 'forward')
        self._original.clear(); self._forward_attributes.clear(); self._installed = False

    def reset_from_history(self):
        if self._pair is not None or self.history._pair is not None or self.history.poisoned:
            raise ValueError('Inactive healthy parent history required')
        if self.partial is not None:
            self.partial.cache = {k: v for k, v in self.history.mlp.items() if k[0] in self.partial.layers}
            self.partial.last_step = self.history.last_step
            self.partial.records = []; self.partial.poisoned = False
        self.cache = {k: v for k, v in self.history.residual.items() if k[0] in self.residual_layers}
        self.records = []; self.last_step = self.history.last_step; self.poisoned = False

    def _validate_history(self, step, context):
        if self.partial is not None and not self.mode.startswith('DENSE_'):
            expected = {(l, s) for l in self.partial.layers for s in (0, 1)}
            if set(self.partial.cache) != expected:
                raise ValueError('Complete past MLP history required; no teacher fill')
            for (layer, _), c in self.partial.cache.items():
                if (c.context != context or int(c.updated_at.max()) >= step
                        or int(c.updated_at.min()) <= 0
                        or c.parameter_versions != _versions(self.blocks[layer].mlp)):
                    raise ValueError('Incompatible or nonpast projection provenance')
        if self.mode == 'L2':
            expected = {(l, s) for l in self.residual_layers for s in (0, 1)}
            if set(self.cache) != expected:
                raise ValueError('Complete past Block residual required; no teacher fill')
            if any(c.context != context or not 0 < c.born < step
                   or c.parameter_versions != _versions(self.blocks[layer])
                   for (layer, _), c in self.cache.items()):
                raise ValueError('Incompatible or nonpast Block history')

    @contextmanager
    def pair(self, *, step, context, indices=None):
        _context(context)
        if (not self._installed or self._pair is not None or self.poisoned
                or torch.is_grad_enabled() or type(step) is not int or step <= self.last_step):
            raise ValueError('Fresh no-grad score-only pair required')
        self._validate_history(step, context)
        is_partial = self.mode.startswith(('P0_', 'M8_'))
        if not is_partial and indices is not None:
            raise ValueError('Only partial MLP modes take a token mask')
        before = dict(self.cache)
        self._pair = dict(step=step, context=context, slots=set())
        try:
            if self.partial is not None:
                with self.partial.pair(step=step, context=context,
                        action='P' if is_partial else 'D', indices=indices):
                    yield self
                    if is_partial and any(r.get('fallback') for r in self.partial.records):
                        raise ValueError('Partial screen cannot accept a cold/incompatible full fallback')
            else:
                yield self
            if self._pair['slots'] != {0, 1}:
                raise ValueError('Both complete score-only branches required')
            self.last_step = step
        except BaseException:
            self.cache = before; self.poisoned = True
            raise
        finally:
            self._pair = None; self._slot = None; self._seen = set()

    @contextmanager
    def branch(self, slot):
        if (self._pair is None or self._slot is not None or type(slot) is not int
                or slot not in (0, 1) or slot in self._pair['slots']):
            raise ValueError('Unique bound score-only CFG branch required')
        self._slot = slot; self._seen = set()
        try:
            if self.partial is not None:
                with self.partial.branch(slot):
                    yield
            else:
                yield
            if self._original and self._seen != set(self.residual_layers):
                raise ValueError('Complete registered Block scope required')
            self._pair['slots'].add(slot)
        finally:
            self._slot = None; self._seen = set()

    def _execute_residual(self, layer, module, args, kwargs):
        if self._pair is None or self._slot is None or layer in self._seen:
            raise ValueError('Exactly one bound Block call per branch required')
        self._seen.add(layer)
        x = args[0] if args else kwargs.get('x_B_T_H_W_D')
        _tensor(x)
        p = self._pair; key = (layer, self._slot); old = self.cache.get(key)
        if self.mode == 'L2':
            if (old.value.shape != x.shape or old.value.dtype != x.dtype
                    or old.value.device != x.device):
                raise ValueError('Old Block residual layout differs; no silent full fallback')
            value = x + old.value
            born, source = old.born, old.source_kind
        else:
            version = _input_version(x)
            value = self._original[layer](*args, **kwargs)
            if ((version is not None and _input_version(x) != version)
                    or value.shape != x.shape or value.dtype != x.dtype):
                raise ValueError('Dense Block mutated identity or changed geometry')
            self.cache[key] = ResidualCache((value.detach() - x.detach()).clone(),
                p['step'], p['context'], _versions(module), 'OFFLINE_D', p['step'])
            born, source = p['step'], 'OFFLINE_D'
        self.records.append(dict(layer=layer, slot=self._slot, step=p['step'],
            mode=self.mode, born=born, age=p['step'] - born, source_kind=source,
            actual_Block_forward=self.mode != 'L2', current_identity_preserved=True,
            committed_to_parent=False))
        return value

    def cache_bytes(self):
        if self.partial is not None:
            return sum(t.numel() * t.element_size() for c in self.partial.cache.values()
                       for t in (c.value, c.updated_at, c.source))
        if self.mode in ('L2', 'DENSE_L2_STATE'):
            return sum(c.value.numel() * c.value.element_size() for c in self.cache.values())
        return 0

    def receipt(self):
        rows = list(self.partial.records) if self.partial is not None else list(self.records)
        return dict(mode=self.mode, score_only=True, cache_bytes=self.cache_bytes(),
                    records=rows, parent_history_committed=False,
                    Q2_implemented=False)
