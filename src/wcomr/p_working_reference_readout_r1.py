"""P-reference readout; true-D coefficients and existing C/P/D actions remain.

This separate candidate binds the current physical P cache at the pinned
hidden callback. It does not change refresh selection or elide any head.
"""
import copy
import types

import torch

from .partial_mlp_guided_readout import SemanticPartialReadout, GuidedPartialDeployment
from .partial_mlp_guided_sampling import GuidedSamplingOwner
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .p_working_reference_residual_r1 import predict_P_reference


VERSION = 'P_WORKING_REFERENCE_READOUT_R1'


class WorkingReferenceReadout(SemanticPartialReadout):
    @torch.no_grad()
    def semantic_hidden(self, net, skipped, branch, original, probe, hidden,
                        block_kwargs, embedding, adaln):
        d = self.deployment
        step = self._branch(net, branch)
        source = d.working[branch]
        if (d.current['action'] != 'C' or self.method == 'OFF'
                or not isinstance(source, dict) or source.get('kind') != 'P'):
            return super().semantic_hidden(net, skipped, branch, original, probe,
                                          hidden, block_kwargs, embedding, adaln)
        if (skipped is not True or branch in self.current['branches']
                or branch not in self.current['prewarp'] or d.net is not net
                or any(m.training for m in net.modules())
                or d.warp is None or d.to_velocity is None):
            raise ValueError('Current semantic C and bound actual P source required')
        self.warp, self.to_velocity = d.warp, d.to_velocity
        c = self.calibrators[branch]
        before = tree_digest(plain(vars(c)))
        entry = {'action': 'C', 'proposed_head': None, 'status': 'OFF',
                 'past_D_steps': c.receipt()['anchor_steps'], 'extra_heads': 0,
                 'working_source_kind': 'P'}
        self.current['branches'][branch] = entry
        # These are the physical caches written by the actual D/P continuation,
        # not a saved D anchor, warped hidden state or caller-supplied proxy.
        working_probe = net.probe_residual_cache[branch]
        working_residual = net.residual_cache[branch]
        official = self.current['prewarp'][branch] - original
        residual, proof = predict_P_reference(calibrator=c, context=self.context,
            step=step, slot=branch, working_source=source, current_probe=probe-original,
            working_probe=working_probe, working_prewarp_residual=working_residual,
            official=official, beta_mode='unit' if self.method.startswith('BETA1') else 'scalar')
        entry['P_reference'] = {**proof, 'version': VERSION,
            'actual_probe_cache_field': 'probe_residual_cache',
            'actual_prewarp_residual_cache_field': 'residual_cache',
            'true_D_full_state_before_sha256': before}
        entry['status'] = proof['status']
        try:
            if proof['status'].endswith('fallback'):
                return
            devices = ([probe.device.index if probe.device.index is not None else torch.cuda.current_device()]
                       if probe.device.type == 'cuda' else [])
            head_buffers = [(b, b.detach().clone()) for b in net.final_layer.buffers()]
            try:
                with torch.random.fork_rng(devices=devices):
                    value = self.warp(net, original+residual, working_residual, original.shape[1])
                    entry['proposed_head'] = net.unpatchify(net.final_layer(
                        value, embedding, adaln_lora_B_T_3D=adaln))
                    entry['extra_heads'] = 1
            finally:
                for b, saved in head_buffers:
                    b.copy_(saved)
            if (net.probe_residual_cache[branch] is not working_probe
                    or net.residual_cache[branch] is not working_residual
                    or d.working[branch] is not source):
                raise ValueError('P readout replaced its actual working cache')
        finally:
            self.current['prewarp'].pop(branch, None)
            after = tree_digest(plain(vars(c)))
            entry['P_reference']['true_D_full_state_after_sha256'] = after
            if after != before:
                raise ValueError('P-reference readout changed full true-D statistics')

    @torch.no_grad()
    def end(self, actual, action):
        proofs = [copy.deepcopy(self.current['branches'][b].get('P_reference')) for b in (0, 1)]
        returned = super().end(actual, action)
        self.history[-1]['P_reference'] = proofs
        self.history[-1]['P_reference_version'] = VERSION
        return returned

    def finish(self):
        value = super().finish()
        value.update(P_reference_version=VERSION,
            P_reference_successful_branch_reads=sum(
                p is not None and not p['status'].endswith('fallback')
                for h in self.history for p in h['P_reference']),
            refresh_controller_changed=False, original_head_elided=False,
            actual_full_sampler_or_quality_acceptance=False)
        return value


class WorkingReferenceDeployment(GuidedPartialDeployment):
    def __init__(self, *args, a_method, **kwargs):
        super().__init__(*args, a_method=a_method, **kwargs)
        self.readout = WorkingReferenceReadout(self, method=a_method)


class WorkingReferenceSamplingOwner(GuidedSamplingOwner):
    def __init__(self, *args, **kwargs):
        original = GuidedSamplingOwner.__init__
        if original.__closure__:
            raise ValueError('Unbound owner constructor closure')
        derived = types.FunctionType(original.__code__,
            {**original.__globals__, 'GuidedPartialDeployment': WorkingReferenceDeployment},
            original.__name__, original.__defaults__)
        derived.__kwdefaults__ = original.__kwdefaults__
        derived(self, *args, **kwargs)

    def installation(self):
        return super().installation()+(VERSION,)
