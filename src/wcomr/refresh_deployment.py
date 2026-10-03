"""Simple deployed sparse refresh with explicit native-window provenance.

The pinned WC probe, skip decision, Gamma and warp are unchanged. Only eligible
deep self-attention refreshes use S. Native forecast windows may contain S;
true-dense metadata is separate and never accepts an approximate reference.
This diagnostic adapter hashes conditions and validates references; its costs
must be included before making any runtime claim.
"""
import copy
from dataclasses import asdict, dataclass
import hashlib
import inspect
from pathlib import Path
import types

import torch

from .mid_coverage import tree_digest

WC_SOURCE_SHA256 = 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903'


@dataclass(frozen=True)
class RefreshSource:
    context: tuple
    group: tuple
    cfg: int
    epoch: int
    call: int
    solver_step: int
    counter: int
    kind: str
    probe_exact_operator: bool = True

    @property
    def is_true_dense(self):
        # Dense means actual dense computation at this trajectory's state,
        # not equality to a separate native or official-dense trajectory.
        return self.kind == 'dense'


class RefreshLedger:
    def __init__(self, context):
        if (type(context) is not tuple or len(context) != 3
                or any(not isinstance(v, str) or not v for v in context)):
            raise ValueError('Explicit request/model/condition context required')
        self.context = self.bound_context = context
        self.group = None
        self.call = self.epoch = 0
        self.windows = [[], []]
        self.true_dense_history = [[], []]
        self.condition_hashes = [None, None]
        self.bindings = [[], []]
        self.cache_bindings = [None, None]
        self.events = []

    def _bind(self, net):
        self.bindings = [[(r, p) for r, p in zip(net.residual_window[b],
                          net.probe_residual_window[b])] for b in (0, 1)]
        self.cache_bindings = [(net.residual_cache[b], net.probe_residual_cache[b])
                               if self.windows[b] else None for b in (0, 1)]

    def validate_native(self, net):
        for b in (0, 1):
            residual, probe = net.residual_window[b], net.probe_residual_window[b]
            if len(residual) != len(probe) or len(residual) != len(self.windows[b]):
                raise ValueError('Native/provenance window coverage differs')
            for source, r, p, (old_r, old_p) in zip(self.windows[b], residual, probe, self.bindings[b]):
                if (source.context != self.bound_context or source.cfg != b
                        or source.group != self.group
                        or source.epoch != self.epoch or source.call > self.call
                        or r is not old_r or p is not old_p):
                    raise ValueError('Native/provenance reference binding changed')
            if self.windows[b]:
                r, p = self.cache_bindings[b]
                if net.residual_cache[b] is not r or net.probe_residual_cache[b] is not p:
                    raise ValueError('Latest native cache binding changed')
                if residual[-1] is not r or probe[-1] is not p:
                    raise ValueError('Native latest cache/window reference differs')
            elif net.residual_cache[b] is not None or net.probe_residual_cache[b] is not None:
                raise ValueError('Untracked native cache reference')

    def enter(self, net, branch, condition):
        if self.context != self.bound_context:
            raise ValueError('Refresh request/model/condition identity changed')
        if self.group != (net.probe_depth, len(net.blocks)):
            raise ValueError('Refresh deep group changed within request')
        self.validate_native(net)
        expected_counter = self.call % net.worldcache_num_steps
        if net.cnt != expected_counter or branch != self.call % 2:
            raise ValueError('Refresh absolute-call/CFG/native-counter binding differs')
        digest = tree_digest(condition)
        if self.condition_hashes[branch] is None:
            self.condition_hashes[branch] = digest
        elif self.condition_hashes[branch] != digest:
            raise ValueError('Refresh actual condition changed within request/CFG')
        self.call += 1

    def append(self, net, branch, kind):
        if kind not in ('dense', 'sparse'):
            raise ValueError('Unsupported deployed source kind')
        source = RefreshSource(self.bound_context, self.group, branch, self.epoch, self.call,
                               (self.call + 1) // 2, net.cnt, kind)
        window = self.windows[branch]
        # Pinned native implementation retains the first entry and shifts the
        # last two once it reaches length three. Mirror that exact topology.
        if len(window) <= 2:
            window.append(source)
        else:
            window[-2], window[-1] = window[-1], source
        if source.is_true_dense:
            self.true_dense_history[branch].append(source)
            self.true_dense_history[branch] = self.true_dense_history[branch][-2:]
        self._bind(net)
        self.validate_native(net)
        return source

    def invalidate_cycle(self, net):
        if net.cnt != 0 or any(net.residual_window) or any(net.probe_residual_window):
            raise ValueError('Expected native horizon reset before provenance reset')
        self.windows, self.true_dense_history = [[], []], [[], []]
        self.epoch += 1
        self._bind(net)
        self.validate_native(net)

    def snapshot(self):
        return copy.deepcopy({key: getattr(self, key) for key in
            ['context', 'bound_context', 'group', 'call', 'epoch', 'windows',
             'true_dense_history', 'condition_hashes', 'events']})

    def restore(self, state, net):
        if state['bound_context'] != self.bound_context:
            raise ValueError('Cannot restore provenance across requests')
        for key, value in copy.deepcopy(state).items():
            setattr(self, key, value)
        self._bind(net)  # StateRoundtrip owns new copies of native tensors.
        self.validate_native(net)

    def report(self):
        return {'context': list(self.bound_context), 'call': self.call, 'epoch': self.epoch,
            'group': self.group,
            'windows': [[asdict(v) for v in w] for w in self.windows],
            'true_dense_history': [[asdict(v) for v in w] for w in self.true_dense_history],
            'events': copy.deepcopy(self.events), 'calibrator_uses_deep_targets': False,
            'probe_exact_operator_is_not_native_trajectory_equality': True}


class SimpleRefreshAdapter:
    def __init__(self, context, *, sparse=False, fallback_layers=(6, 23, 27), kernel=None):
        self.ledger = RefreshLedger(context)
        self.sparse = sparse
        self.fallback_layers = tuple(fallback_layers)
        if (any(type(v) is not int or v < 0 for v in self.fallback_layers)
                or len(set(self.fallback_layers)) != len(self.fallback_layers)):
            raise ValueError('Invalid dense fallback layers')
        self.kernel = kernel
        self.mode = 'dense'
        self.pending = None
        self.restores = []
        self.net = None
        self.attached_net = None
        self.native_forward = None

    def start(self, net, branch, condition):
        if net is not self.net:
            raise ValueError('Refresh model object changed')
        self.ledger.enter(net, branch, condition)
        self.mode = 'dense'
        self.pending = None

    def before(self, net, skipped, branch, original, probe):
        if not bool(torch.isfinite(original).all()) or not bool(torch.isfinite(probe).all()):
            raise ValueError('Nonfinite refresh input/probe refused before deep/cache write')
        warm = net.cnt < int(net.worldcache_num_steps * net.worldcache_ret_ratio)
        history = len(self.ledger.true_dense_history[branch]) >= 2
        paid_probe = bool(net.resume_flag[branch])
        allowed = (self.sparse and not skipped and not warm and history and paid_probe)
        self.mode = 'sparse' if allowed else 'dense'
        self.pending = {'call': self.ledger.call, 'solver_step': (self.ledger.call + 1) // 2,
            'cfg': branch, 'epoch': self.ledger.epoch, 'counter': net.cnt,
            'official_skipped': bool(skipped), 'action': 'cache' if skipped else self.mode,
            'warm_start': warm, 'two_past_true_dense': history, 'paid_probe': paid_probe,
            'sparse_layers': [], 'operator_metadata': [],
            'references_read': [asdict(v) for v in self.ledger.windows[branch][-2:]],
            'true_dense_before': [asdict(v) for v in self.ledger.true_dense_history[branch]]}

    def after_refresh(self, net, branch):
        kind = 'sparse' if self.pending['sparse_layers'] else 'dense'
        source = self.ledger.append(net, branch, kind)
        self.pending['source'] = asdict(source)
        self.pending['inserted_into_true_dense_history'] = source.is_true_dense

    def finish(self, net):
        if self.pending is None:
            raise ValueError('Refresh observation missing')
        self.pending['native_cycle_reset'] = net.cnt == 0
        if net.cnt == 0:
            self.ledger.invalidate_cycle(net)
        else:
            self.ledger.validate_native(net)
        self.ledger.events.append(self.pending)
        self.pending = None
        self.mode = 'dense'

    def _transform_decision(self, source, namespace):
        """Identity for deployed WC; subclasses may expose offline diagnostics."""
        return source

    def install(self, net, wc):
        if self.net is not None or hasattr(net, '_wc_refresh_adapter'):
            raise ValueError('Refresh adapter already installed')
        if (not 0 < net.probe_depth < len(net.blocks)
                or any(not net.probe_depth <= v < len(net.blocks) for v in self.fallback_layers)):
            raise ValueError('Refresh group/fallback layer geometry differs')
        original = wc.worldcache_mini_train_dit_forward
        if hashlib.sha256(Path(inspect.getfile(original)).read_bytes()).hexdigest() != WC_SOURCE_SHA256:
            raise ValueError('Pinned native WC file differs')
        source = inspect.getsource(original)
        edits = [
            ('    current_idx = self.cnt % 2',
             '    _refresh_start(self, self.cnt % 2, [crossattn_emb, fps, padding_mask, data_type, img_context_emb, condition_video_input_mask_B_C_T_H_W])\n    current_idx = self.cnt % 2'),
            ('    # --- Execution Branching ---',
             '    _refresh_before(self, skip_forward, current_idx, ori_x, test_x)\n\n    # --- Execution Branching ---'),
            ('    # --- Final Layer & Unpatchify ---',
             '    if not skip_forward:\n        _refresh_after(self, current_idx)\n\n    # --- Final Layer & Unpatchify ---'),
            ('    return x_B_C_Tt_Hp_Wp',
             '    _refresh_finish(self)\n    return x_B_C_Tt_Hp_Wp')]
        for anchor, replacement in edits:
            if source.count(anchor) != 1:
                raise ValueError('Pinned refresh injection anchor changed: ' + anchor)
            source = source.replace(anchor, replacement)
        namespace = dict(original.__globals__, _refresh_start=self.start,
            _refresh_before=self.before, _refresh_after=self.after_refresh, _refresh_finish=self.finish)
        source = self._transform_decision(source, namespace)
        exec(compile(source, '<simple-refresh-deployment>', 'exec'), namespace)
        self.net = net
        self.attached_net = net
        self.native_forward = net.forward
        self.ledger.group = (net.probe_depth, len(net.blocks))
        owned, prior = 'forward' in vars(net), vars(net).get('forward')
        self.restores.append(lambda owned=owned, prior=prior:
            setattr(net, 'forward', prior) if owned else delattr(net, 'forward'))
        net.forward = types.MethodType(namespace[original.__name__], net)
        net._wc_refresh_adapter = self
        try:
            for layer in range(net.probe_depth, len(net.blocks)):
                op = net.blocks[layer].self_attn.attn_op
                native, owned, prior = op.forward, 'forward' in vars(op), vars(op).get('forward')
                def restore(op=op, owned=owned, prior=prior):
                    if owned: op.forward = prior
                    else: delattr(op, 'forward')
                self.restores.append(restore)
                def operation(*args, _layer=layer, _native=native, **kwargs):
                    if self.mode == 'dense' or _layer in self.fallback_layers:
                        return _native(*args, **kwargs)
                    if len(args) != 3 or kwargs:
                        raise ValueError('Frozen refresh self-attention call differs')
                    q, k, v = args
                    if q.ndim != 4 or q.shape != k.shape or q.shape != v.shape:
                        raise ValueError('Refresh QKV NHD shape differs')
                    b, n, h, d = q.shape
                    if n % 128 or d != 128:
                        raise ValueError('Frozen sparse refresh geometry differs')
                    mask = torch.ones(b, h, n // 128, n // 64, device=q.device, dtype=torch.bool)
                    if self.kernel is None:
                        from .sparge_routed_no_pv import routed_no_pv
                        kernel = routed_no_pv
                    else: kernel = self.kernel
                    value, metadata = kernel(q, k, v, mask, .1, .98, False)
                    if (value.shape != (b, n, h * d) or value.dtype != q.dtype
                            or value.device != q.device or not bool(torch.isfinite(value).all())):
                        raise ValueError('Invalid sparse refresh output; no native cache write')
                    self.pending['sparse_layers'].append(_layer)
                    self.pending['operator_metadata'].append({'layer': _layer, **metadata})
                    return value
                op.forward = operation
        except BaseException:
            self.close()
            raise
        return self

    def snapshot(self):
        if self.pending is not None or self.mode != 'dense':
            raise ValueError('Provenance checkpoint is not at a completed forward boundary')
        return self.ledger.snapshot()

    def restore(self, state):
        self.ledger.restore(state, self.net)
        self.pending = None
        self.mode = 'dense'

    def report(self):
        return self.ledger.report()

    def close(self):
        for restore in reversed(self.restores): restore()
        self.restores.clear()
        if self.attached_net is not None:
            if self.attached_net.forward != self.native_forward:
                raise ValueError('Refresh close did not restore native forward')
            delattr(self.attached_net, '_wc_refresh_adapter')
        self.net = None
        self.attached_net = None
        self.native_forward = None
        self.pending = None
        self.mode = 'dense'
