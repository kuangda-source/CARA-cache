"""Semantic C/P/D composition for teacher-free A and partial refresh.

The frozen legacy A body is reused only for actual C readout. P must bypass
its physical-nonskip D observer. PartialDeployment remains the sole owner of
real D observations; A reads that same D-only history. This core is not yet a
full sampler integration or a tested source-risk action selector.
"""
import copy

import torch

from .cfg_guided_w1_collection import signature
from .cfg_guided_w1_deployment import GuidedW1Readout, METHODS, alpha_at
from .cfg_guided_w1_outputs import shared_output_fusion
from .partial_mlp_deployment import PartialDeployment


class SemanticPartialReadout(GuidedW1Readout):
    def __init__(self, deployment, *, method):
        super().__init__(deployment.model, method=method, context=deployment.context)
        self.deployment = deployment
        # No separate observer and no duplicate D clones/fit statistics.
        self.calibrators = deployment.dense

    @torch.no_grad()
    def semantic_hidden(self, net, skipped, branch, *values):
        step = self._branch(net, branch)
        d = self.deployment
        action = d.current['action']
        if skipped != (action == 'C') or branch in self.current['branches']:
            raise ValueError('One explicit semantic C/P/D observation required')
        if action == 'C':
            self.warp, self.to_velocity = d.warp, d.to_velocity
            # The original body is correct for C on either D or P working
            # sources: its extrapolation anchors are still only actual D.
            super().hidden(net, True, branch, *values)
            self.current['branches'][branch]['working_source_kind'] = d.working[branch]['kind']
        elif action in ('D', 'P'):
            self.current['prewarp'].pop(branch, None)
            self.current['branches'][branch] = {'action': action, 'proposed_head': None,
                'status': 'ACTUAL_D_OBSERVED_BY_P0_OWNER' if action == 'D' else 'P_NOT_ACTUAL_D',
                'past_D_steps': self.calibrators[branch].receipt()['anchor_steps'],
                'extra_heads': 0, 'working_source_kind': action}
        else:
            raise ValueError('Unsupported semantic source action')

    @torch.no_grad()
    def end(self, actual, action):
        cur = self.current
        if (cur is None or action not in ('CC', 'PP', 'DD')
                or set(cur['branches']) != {0, 1}
                or ''.join(cur['branches'][b]['action'] for b in (0, 1)) != action
                or int(self.net.cnt) != 2*cur['step'] % 70
                or any(not cur['branches'][b].get('output_seen') for b in (0, 1))):
            raise ValueError('Complete actual semantic C/P/D pair required')
        if (signature((cur['noise'], cur['latent'], cur['timestep'])) != cur['input_signature']
                or signature([vars(c) for c in cur['conditions']]) != cur['condition_signature']):
            raise ValueError('Composite A changed original solver input or conditions')
        alpha = alpha_at(self.method, cur['step'])
        returned = actual
        if action == 'CC' and alpha:
            proposed = tuple(self.to_velocity(self.model, cur['noise'], cur['latent'],
                cur['timestep'], cur['conditions'][b],
                _supplied_net_output=cur['branches'][b]['proposed_head'])
                if cur['branches'][b]['proposed_head'] is not None else actual[b]
                for b in (0, 1))
            returned = shared_output_fusion(actual, proposed, alpha)
        self.history.append({'step': cur['step'], 'action': action, 'shared_alpha': alpha,
            'branch_status': [cur['branches'][b]['status'] for b in (0, 1)],
            'working_source_kind': [cur['branches'][b]['working_source_kind'] for b in (0, 1)],
            'past_D_steps': [cur['branches'][b]['past_D_steps'] for b in (0, 1)],
            'extra_heads': sum(cur['branches'][b]['extra_heads'] for b in (0, 1)),
            'extra_deep_blocks': 0, 'teacher_calls': 0, 'post_RF_fusion': True,
            'C_or_P_observation_updates_D_anchor': False})
        self.completed += 1
        self.current = None
        return returned


class GuidedPartialDeployment(PartialDeployment):
    def __init__(self, *args, a_method, **kwargs):
        if a_method not in METHODS:
            raise ValueError('Explicit existing A method required')
        super().__init__(*args, **kwargs)
        self.readout = SemanticPartialReadout(self, method=a_method)

    def begin(self, noise, latent, timestep, conditions, stack):
        super().begin(noise, latent, timestep, conditions, stack)
        self.readout.begin(noise, latent, timestep, conditions)

    def prewarp(self, net, slot, hidden):
        super().prewarp(net, slot, hidden)
        self.readout.prewarp(net, slot, hidden)

    def hidden(self, net, skipped, slot, *values):
        super().hidden(net, skipped, slot, *values)
        self.readout.semantic_hidden(net, skipped, slot, *values)

    def output(self, net, slot, head):
        super().output(net, slot, head)
        self.readout.output(net, slot, head)

    def commit(self, actual, base_last):
        # Both branches are complete before P0 owns any D observation. C/P
        # never pass through the legacy physical-nonskip D observer.
        super().commit(actual, base_last)
        row = self.history[-1]
        if row['action'] == 'DD':
            for slot in (0, 1):
                self.readout.current['branches'][slot]['past_D_steps'] = self.dense[slot].receipt()['anchor_steps']
        returned = self.readout.end(actual, row['action'])
        row['A_readout'] = copy.deepcopy(self.readout.history[-1])
        row['actual_post_RF_returned_without_substitution'] = self.readout.method == 'OFF' or row['action'] != 'CC'
        row['semantic_P_bypasses_legacy_D_observer'] = True
        return returned

    def finish(self):
        result = super().finish()
        result['A_readout'] = self.readout.finish()
        result['combined_readout_source_risk_policy_implemented'] = False
        return result
