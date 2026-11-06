"""Private held references for fixed-trajectory source/lifetime diagnostics."""
from dataclasses import dataclass
import copy

import torch

from .mid_coverage import tree_digest

SOURCE_KINDS = ('dense', 'matched_full', 'sparse')


@dataclass(frozen=True)
class ReferenceIdentity:
    request: str
    model: str
    condition: str
    cfg_slot: int
    group: tuple
    solver_step: int
    source_call: int
    source_kind: str

    def validate(self):
        if not all(isinstance(x, str) and x for x in (self.request, self.model, self.condition)):
            raise ValueError('Explicit request/model/condition identity required')
        if type(self.cfg_slot) is not int or self.cfg_slot not in (0, 1) or self.source_kind not in SOURCE_KINDS:
            raise ValueError('Unsupported CFG or reference source')
        if (type(self.solver_step) is not int or type(self.source_call) is not int
                or self.solver_step < 1
                or self.source_call != 2 * (self.solver_step - 1) + self.cfg_slot + 1):
            raise ValueError('Source is not a same-CFG solver call')
        if (type(self.group) is not tuple or len(self.group) != 2
                or any(type(x) is not int for x in self.group)
                or not 0 <= self.group[0] < self.group[1]):
            raise ValueError('Explicit contiguous group required')


class HeldReference:
    """Frozen refresh output; no API writes it into deployed or calibration state.

    Gamma is computed from the same exact paid shallow-probe pair for all three
    sources. The latest deep window entry alone varies by source. A sparse entry
    in this private window is approximate, never an online true-dense anchor.
    """
    def __init__(self, identity, *, prior_dense_counter, prior_residual,
                 prior_probe_residual, residual, probe_residual,
                 deployment_full_verified, max_age=4):
        identity.validate()
        counter = identity.source_call - 1
        if (type(prior_dense_counter) is not int or prior_dense_counter < 0
                or prior_dense_counter >= counter or prior_dense_counter % 2 != identity.cfg_slot):
            raise ValueError('Prior reference is not strictly past same-CFG dense')
        if (type(deployment_full_verified) is not bool
                or deployment_full_verified != (identity.source_kind == 'dense')):
            raise ValueError('Approximate source may not claim true deployed dense')
        if type(max_age) is not int or max_age < 1:
            raise ValueError('Positive integer same-CFG age cap required')
        values = (prior_residual, prior_probe_residual, residual, probe_residual)
        if any(x.ndim != 5 or not x.is_floating_point() for x in values):
            raise ValueError('Pinned BTHWD floating references required')
        if any((x.shape, x.dtype, x.device) != (residual.shape, residual.dtype, residual.device)
               or not bool(torch.isfinite(x).all()) for x in values):
            raise ValueError('Invalid reference geometry/dtype/device or finite gate')
        self.identity = identity
        self.prior_dense_counter = prior_dense_counter
        self.max_age = max_age
        # Production may enter an outer inference_mode. Keep these private
        # snapshots as normal no-grad tensors so version checks remain valid.
        with torch.inference_mode(False), torch.no_grad():
            self.values = tuple(x.detach().clone() for x in values)
        self.versions = tuple(x._version for x in self.values)
        self.initial_digest = tree_digest(self.values)
        self.policy = None

    @staticmethod
    def policy_signature(net):
        return {name: getattr(net, name, default) for name, default in (
            ('worldcache_osi_enabled', False), ('worldcache_flow_enabled', False),
            ('worldcache_flow_scale', .5))}

    def bind_policy(self, net):
        if self.policy is not None:
            raise ValueError('Held reference policy may only be bound once')
        self.policy = self.policy_signature(net)

    def check_immutable(self, *, digest=False):
        if self.versions != tuple(x._version for x in self.values):
            raise ValueError('Held reference modified during lifetime diagnostic')
        if digest and self.initial_digest != tree_digest(self.values):
            raise ValueError('Held reference raw values drifted')

    def provenance(self):
        return {
            'identity': vars(self.identity),
            'prior_true_dense_counter': self.prior_dense_counter,
            'source_kind': self.identity.source_kind,
            'source_is_approximate': self.identity.source_kind != 'dense',
            'inserted_into_online_cache_or_calibrator': False,
            'reference_values_sha256': self.initial_digest,
            'reuse_policy': self.policy,
            'mask_reused_for_future_attention': False,
        }

    @torch.no_grad()
    def predict(self, net, cached_prediction, *, original_input, probe,
                solver_step, context):
        identity = self.identity
        required = (identity.request, identity.model, identity.condition, identity.cfg_slot, identity.group)
        if context != required:
            raise ValueError('Request/model/condition/CFG/group reference mismatch')
        if type(solver_step) is not int:
            raise ValueError('Integer same-CFG solver step required')
        age = solver_step - identity.solver_step
        if (not 1 <= age <= self.max_age
                or net.cnt != 2 * (solver_step - 1) + identity.cfg_slot):
            raise ValueError('Future call is not strictly past-source same-CFG age')
        if self.policy is None or self.policy != self.policy_signature(net):
            raise ValueError('Frozen common reuse policy changed')
        if any((x.shape, x.dtype, x.device) !=
               (original_input.shape, original_input.dtype, original_input.device)
               for x in (probe, self.values[2])):
            raise ValueError('Future probe or reference geometry changed')
        self.check_immutable()
        prior, prior_probe, latest, latest_probe = self.values
        proxy = copy.copy(net)
        proxy.previous_internal_states = list(net.previous_internal_states)
        proxy.previous_input = list(net.previous_input)
        proxy.residual_cache = list(net.residual_cache)
        proxy.residual_window = [list(x) for x in net.residual_window]
        proxy.probe_residual_window = [list(x) for x in net.probe_residual_window]
        branch = identity.cfg_slot
        proxy.residual_cache[branch] = latest
        proxy.residual_window[branch] = [prior, latest]
        proxy.probe_residual_window[branch] = [prior_probe, latest_probe]
        output = cached_prediction(proxy, original_input, probe, branch)
        self.check_immutable()
        return output
