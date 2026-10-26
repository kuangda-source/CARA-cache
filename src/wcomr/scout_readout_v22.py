"""E1 same-state readout preparation; no sampler installation or GPU dispatch.

Caller must supply proven parent states. Metadata validation is not proof that
features came from a real model. Component outputs and common-alpha outputs
are both retained. This module never chooses a refresh or updates an anchor.
"""
import copy
import math
from dataclasses import dataclass
from types import SimpleNamespace

import torch

from .cfg_guided_w1_outputs import shared_output_fusion, unit_increment_residual
from .full_sampling import CompleteStateRoundtrip
from .mid_coverage import tree_digest, WC_FIELDS
from .policy_interval_readout_r1 import ReadoutKernel, guided
from .partial_mlp_deployment_state import plain, tensor_bytes

LABELS = ('WC_C', 'A_PHASE', 'FULL', 'R4_GLOBAL', 'R4_LONG', 'DCTA')
D_STEPS = tuple(range(1, 22)) + (24, 27, 30, 36)
STATE_STEPS = (22, 23, 25, 33, 34, 35)
DCTA_COMMIT = 'fdbe20b669c9174bbed5ec994de073fd881c8010'
PARENT_FINGERPRINT = '008d9fa12c7aad67e40440533a6e552147d79b82e44afebd8df55954f47b6e60'


class UnsupportedReadout(ValueError):
    """Keep this state in the registered denominator; never substitute a win."""


@dataclass(frozen=True)
class Anchor:
    context: tuple  # request, model/weights, parent policy fingerprint
    branch: int
    step: int
    xi: float
    probe: torch.Tensor
    residual: torch.Tensor


def validate_state(context, step, xi, anchors):
    if (not isinstance(context, tuple) or len(context) != 3
            or any(not isinstance(x, str) or not x for x in context)
            or context[-1] != PARENT_FINGERPRINT
            or type(step) is not int or step not in STATE_STEPS
            or not math.isfinite(xi) or not 0 <= xi <= 1
            or len(anchors) != 2):
        raise UnsupportedReadout('Frozen E1 state identity required')
    expected = [s for s in D_STEPS if s < step][-2:]
    coords = []
    for branch, pair in enumerate(anchors):
        if len(pair) != 2 or any(not isinstance(a, Anchor) for a in pair):
            raise UnsupportedReadout('Two explicit true-D anchors per branch required')
        if ([a.step for a in pair] != expected
                or any(a.context != context or a.branch != branch for a in pair)):
            raise UnsupportedReadout('Wrong request/model/policy/branch or true-D identity')
        older, latest = pair
        if not (0 <= older.xi < latest.xi < xi <= 1):
            raise UnsupportedReadout('Strictly past positive noise-coordinate spans required')
        coords.append((older.xi, latest.xi))
    if coords[0] != coords[1]:
        raise UnsupportedReadout('CFG branches disagree on true anchor times')
    old, last = coords[0]
    return dict(h=xi-last, H=last-old, kappa=(xi-last)/(last-old),
                age=step-expected[-1], alpha=1.0 if step < 25 else .5)


def _tensors(*values):
    first = values[0]
    if any(not isinstance(v, torch.Tensor) or not v.is_floating_point()
           or not v.numel() for v in values):
        raise UnsupportedReadout('Nonempty floating tensors required')
    if any(v.shape != first.shape or v.dtype != first.dtype or v.device != first.device
           or not bool(torch.isfinite(v).all()) for v in values):
        raise UnsupportedReadout('Finite aligned feature coordinates required')


@torch.no_grad()
def proposal(label, current_probe, older, latest, *, kappa, age):
    """Raw prewarp residual; DCTA follows pinned Wan [1,2], no hidden epsilon."""
    if label not in LABELS[1:] or not math.isfinite(kappa) or kappa <= 0:
        raise UnsupportedReadout('Supported readout and positive span ratio required')
    p, po, pb, ro, rb = current_probe, older.probe, latest.probe, older.residual, latest.residual
    _tensors(p, po, pb, ro, rb)
    info = dict(raw_formula=label, kappa=kappa, dtype=str(p.dtype))
    if label == 'A_PHASE' or (label == 'R4_LONG' and age < 3):
        result = unit_increment_residual(current_probe=p, anchor_probe=pb, anchor_residual=rb)
        info['raw_formula'] = 'A_PHASE'
    elif label in ('R4_GLOBAL', 'R4_LONG'):
        result = p + (rb-pb) + kappa*((rb-pb)-(ro-po))
    elif label == 'FULL':
        result = rb + kappa*(rb-ro)
    else:
        numerator = (p-po).abs().mean()
        denominator = (pb-po).abs().mean()
        if not bool(torch.isfinite(numerator)) or not bool(torch.isfinite(denominator)) or denominator <= 0:
            raise UnsupportedReadout('DCTA zero/nonfinite denominator; no silent epsilon or fallback')
        ratio = numerator/denominator
        if not bool(torch.isfinite(ratio)):
            raise UnsupportedReadout('DCTA ratio overflow outside audited finite support')
        gamma = ratio.clamp(1, 2)
        result = ro + gamma*(rb-ro)
        info.update(gamma=float(gamma), numerator=float(numerator), denominator=float(denominator),
                    component_source=DCTA_COMMIT, component='WAN_FIXED_MASK_READOUT_ONLY')
    if not bool(torch.isfinite(result).all()):
        raise UnsupportedReadout('Nonfinite proposed residual')
    return result, info


def spatial_gradient_diagnostics(candidate, teacher):
    """BCTHW FP32 velocity, forward H/W differences, valid edges, FP64 sums."""
    _tensors(candidate, teacher)
    if candidate.ndim != 5 or min(candidate.shape[-2:]) < 2:
        raise ValueError('BCTHW spatial dimensions >=2 required')
    a, b = candidate.double(), teacher.double()
    da = (a[..., 1:, :]-a[..., :-1, :], a[..., :, 1:]-a[..., :, :-1])
    db = (b[..., 1:, :]-b[..., :-1, :], b[..., :, 1:]-b[..., :, :-1])
    n = sum(v.numel() for v in da)
    e = sum((x-y).square().sum() for x, y in zip(da, db))/n
    ea = sum(x.square().sum() for x in da)/n
    eb = sum(x.square().sum() for x in db)/n
    return dict(gradient_residual_MSE=float(e), candidate_gradient_energy=float(ea),
                teacher_gradient_energy=float(eb), energy_ratio=float(ea/(eb+1e-12)),
                epsilon=1e-12, zero_teacher_gradient=bool(eb == 0), quality_gate=False)


class ScoutReadoutKernel(ReadoutKernel):
    """Source-pinned C/head/RF adapter with isolated candidate cache views.

This is a readout entry, not a parent-state collector. Full sampler hooks and
real-weight/device evidence are separate mandatory production acceptance.
"""
    def __init__(self, *args, max_logical_copy_bytes, **kwargs):
        if type(max_logical_copy_bytes) is not int or max_logical_copy_bytes <= 0:
            raise ValueError('Explicit state-copy budget required before cloning')
        super().__init__(*args, **kwargs)
        self.max_logical_copy_bytes = max_logical_copy_bytes

    @torch.no_grad()
    def evaluate(self, label, *, context, step, xi, anchors, current, pair_inputs):
        if label not in LABELS or len(current) != 2 or len(pair_inputs) != 4 or len(pair_inputs[3]) != 2:
            raise UnsupportedReadout('One registered label and complete CFG pair required')
        spans = validate_state(context, step, xi, anchors)
        if any(m.training for m in self.net.modules()):
            raise UnsupportedReadout('All readout modules must be in eval mode')
        for row, (older, latest) in zip(current, anchors):
            _tensors(row['original'], row['probe'], older.probe, older.residual,
                     latest.probe, latest.residual)
        logical_bytes = tensor_bytes(plain((anchors, current, pair_inputs[:3],
            [vars(c) for c in pair_inputs[3]],
            {k:getattr(self.net,k) for k in WC_FIELDS if hasattr(self.net,k)},
            {k:v for k,v in vars(self.model.sample_scheduler).items() if not callable(v)},
            list(self.net.buffers()))))
        if logical_bytes > self.max_logical_copy_bytes:
            raise UnsupportedReadout('State-copy budget exceeded before allocation')
        def input_digest():
            return tree_digest(plain((anchors, current, pair_inputs[:3],
                                      [vars(c) for c in pair_inputs[3]])))
        before = input_digest()
        snapshot = CompleteStateRoundtrip(self.net, self.model.sample_scheduler, pair_inputs[1])
        state_before = snapshot.fingerprint()
        parameters = [(p, p._version) for p in self.net.parameters()]
        try:
            result = self._evaluate(label, spans, copy.deepcopy(anchors),
                                    copy.deepcopy(current), copy.deepcopy(pair_inputs))
            # Outputs must not alias buffers restored below.
            result = copy.deepcopy(result)
        finally:
            snapshot.restore()
            if snapshot.fingerprint() != state_before or input_digest() != before:
                raise RuntimeError('Candidate changed protected parent state or inputs')
            if any(p._version != version for p, version in parameters):
                raise RuntimeError('Candidate mutated weights; discard this engineering attempt')
        result['state_roundtrip'] = dict(before=state_before, after=state_before,
            input_sha256=before, scope='KNOWN_WC_CACHE_SOLVER_BUFFERS_MODES_RNG',
            logical_copy_bytes=logical_bytes, logical_copy_cap_bytes=self.max_logical_copy_bytes,
            logical_copy_is_not_device_peak=True, full_parent_collector_accepted=False)
        return result

    def _evaluate(self, label, spans, anchors, current, pair_inputs):
        source = [dict(probe=b.probe, residual=b.residual,
                       residual_window=[o.residual, b.residual], probe_window=[o.probe, b.probe])
                  for o, b in anchors]
        C, _, _ = super().run('C', source=source, current=current, pair_inputs=pair_inputs)
        shared_output_fusion(C,C,0)
        if label == 'WC_C':
            return dict(outputs=C, component_outputs=C, alpha=spans['alpha'], formulas=[])
        noise, latent, timestep, conditions = pair_inputs
        raw, formulas = [], []
        for branch, (older, latest) in enumerate(anchors):
            row = current[branch]
            p = row['probe'] - row['original']
            residual, detail = proposal(label, p, older, latest, kappa=spans['kappa'], age=spans['age'])
            # Same isolated post-C context as the accepted A path.
            proxy = SimpleNamespace(cnt=branch, previous_input=[None, None],
                previous_internal_states=[None, None], worldcache_flow_enabled=self.net.worldcache_flow_enabled,
                worldcache_flow_scale=self.net.worldcache_flow_scale)
            proxy.previous_input[branch] = row['original']
            proxy.previous_internal_states[branch] = row['probe']
            hidden = self.warp(proxy, row['original']+residual, latest.residual, row['original'].shape[1])
            head = self.net.unpatchify(self.net.final_layer(hidden, row['embedding'], adaln_lora_B_T_3D=row['adaln']))
            raw.append(self.to_velocity(self.model, noise, latent, timestep, conditions[branch], _supplied_net_output=head))
            formulas.append(detail)
        raw = tuple(raw)
        return dict(outputs=shared_output_fusion(C, raw, spans['alpha']), component_outputs=raw,
                    alpha=spans['alpha'], formulas=formulas)


def actual_guided_error(outputs, dense):
    # Validate branch shape/precision even when no blend is needed.
    shared_output_fusion(outputs, dense, 0)
    a, b = guided(outputs), guided(dense)
    return dict(MSE=float((a.double()-b.double()).square().mean()),
                **spatial_gradient_diagnostics(a, b))
