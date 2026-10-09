"""Teacher-free A readout at actual paired WorldCache boundaries.

The existing selector owns C/D and the unmodified WC continuation owns cache
updates. A changes the returned post-RF velocities, so subsequent solver
states are its own trajectory. Only actual D may update residual calibration.
This core is not a full video experiment or a claim about endpoint quality.
"""
import copy

import torch

from .calibration import ResidualCalibrator
from .cfg_guided_w1_collection import signature
from .cfg_guided_w1_outputs import shared_output_fusion, unit_increment_residual


METHODS = ('OFF', 'W1_GLOBAL_1', 'BETA1_GLOBAL_1',
           'W1_ONE_PHASE', 'BETA1_ONE_PHASE')


def alpha_at(method, step):
    if method not in METHODS or type(step) is not int or not 1 <= step <= 36:
        raise ValueError('Frozen method and actual full36 execution step required')
    if method == 'OFF':
        return 0
    return .5 if method.endswith('ONE_PHASE') and step >= 25 else 1


class GuidedW1Readout:
    """Implements the exact collection compiler's observation interface.

    Original and proposed heads are both paid even at alpha=1 in this version.
    No dense teacher, candidate deep block, future label or online fitting to
    endpoint scores is available here. OFF adds no calibration or tensor clone.
    """
    def __init__(self, model, *, method, context):
        if (method not in METHODS or type(context) is not tuple or not context
                or any(type(v) is not str or not v for v in context)):
            raise ValueError('Explicit registered method and immutable request context required')
        self.model, self.net = model, model.net
        self.method, self.context = method, context
        self.calibrators = [ResidualCalibrator(), ResidualCalibrator()]
        for c in self.calibrators:
            c.reset(context)
        self.warp = self.to_velocity = None
        self.completed = 0
        self.current = None
        self.history = []
        self.poisoned = False

    def begin(self, noise, latent, timestep, conditions):
        if (self.current is not None or self.poisoned or self.completed >= 36
                or torch.is_grad_enabled() or self.model.net is not self.net
                or not isinstance(conditions, tuple) or len(conditions) != 2
                or int(self.net.cnt) != 2*self.completed % 70
                or int(self.net.worldcache_num_steps) != 70):
            raise ValueError('Healthy current full36 paired origin under no_grad required')
        self.current = {'step': self.completed+1, 'noise': noise, 'latent': latent,
            'timestep': timestep, 'conditions': conditions, 'branches': {}, 'prewarp': {},
            'input_signature': signature((noise, latent, timestep)),
            'condition_signature': signature([vars(c) for c in conditions])}

    def _branch(self, net, branch):
        if (self.current is None or net is not self.net or branch not in (0, 1)
                or net.cnt != (2*(self.current['step']-1)+branch) % 70):
            raise ValueError('Current actual branch counter differs')
        return self.current['step']

    def prewarp(self, net, branch, hidden):
        self._branch(net, branch)
        if self.method == 'OFF':
            return
        if branch in self.current['prewarp']:
            raise ValueError('Duplicate original prewarp observation')
        self.current['prewarp'][branch] = hidden.detach().clone()

    @torch.no_grad()
    def hidden(self, net, skipped, branch, original, probe, hidden,
               block_kwargs, embedding, adaln):
        step = self._branch(net, branch)
        if type(skipped) is not bool or branch in self.current['branches']:
            raise ValueError('Exactly one actual C/D observation per branch required')
        entry = {'action': 'C' if skipped else 'D', 'proposed_head': None,
                 'status': 'OFF', 'past_D_steps': [], 'extra_heads': 0}
        self.current['branches'][branch] = entry
        if self.method == 'OFF':
            return
        c = self.calibrators[branch]
        if c.context != self.context:
            raise ValueError('Request context changed without a fresh A readout')
        if not skipped:
            if not c.observe_full(context=self.context, step=step,
                    probe=net.probe_residual_cache[branch], residual=net.residual_cache[branch]):
                raise ValueError('Actual D anchor invalid; complete job must fail')
            entry.update(status='ACTUAL_D_ONLY_ANCHOR', past_D_steps=c.receipt()['anchor_steps'])
            self.current['prewarp'].pop(branch, None)
            return
        if (self.warp is None or self.to_velocity is None or branch not in self.current['prewarp']
                or any(m.training for m in net.modules())):
            raise ValueError('Actual CC requires exact source helpers and eval modules')
        entry['past_D_steps'] = c.receipt()['anchor_steps']
        if not c.anchors or any(a.step >= step for a in c.anchors):
            raise ValueError('A reuse requires strictly past actual D history')
        before = copy.deepcopy(c.receipt())
        anchor = c.anchors[-1]
        if self.method.startswith('BETA1'):
            residual = unit_increment_residual(current_probe=probe-original,
                anchor_probe=anchor.probe, anchor_residual=anchor.residual)
            entry['status'] = 'BETA1'
        else:
            residual, status = c.predict(context=self.context, step=step, probe=probe-original,
                official=self.current['prewarp'][branch]-original, mode='scalar')
            entry['status'] = status
            if status != 'scalar':
                # The original readout is the explicit cheap safe fallback.
                self.current['prewarp'].pop(branch, None)
                return
        devices = ([probe.device.index if probe.device.index is not None else torch.cuda.current_device()]
                   if probe.device.type == 'cuda' else [])
        head_buffers = [(b, b.detach().clone()) for b in net.final_layer.buffers()]
        try:
            with torch.random.fork_rng(devices=devices):
                value = self.warp(net, original+residual, net.residual_cache[branch], original.shape[1])
                entry['proposed_head'] = net.unpatchify(
                    net.final_layer(value, embedding, adaln_lora_B_T_3D=adaln))
                entry['extra_heads'] = 1
        finally:
            for b, saved in head_buffers:
                b.copy_(saved)
            self.current['prewarp'].pop(branch, None)
        if c.receipt() != before:
            raise ValueError('A candidate changed actual D calibration history')

    def output(self, net, branch, head):
        self._branch(net, branch)
        entry = self.current['branches'].get(branch)
        if entry is None or entry.get('output_seen'):
            raise ValueError('Exactly one original head output after branch continuation required')
        entry['output_seen'] = True

    @torch.no_grad()
    def end(self, actual, action):
        cur = self.current
        if (cur is None or action not in ('CC', 'DD') or set(cur['branches']) != {0, 1}
                or ''.join(cur['branches'][b]['action'] for b in (0, 1)) != action
                or int(self.net.cnt) != 2*cur['step'] % 70
                or any(not cur['branches'][b].get('output_seen') for b in (0, 1))):
            raise ValueError('Complete source-executed joint C/D pair required')
        if (signature((cur['noise'], cur['latent'], cur['timestep'])) != cur['input_signature']
                or signature([vars(c) for c in cur['conditions']]) != cur['condition_signature']):
            raise ValueError('A readout changed solver inputs or conditions')
        alpha = alpha_at(self.method, cur['step'])
        if action == 'DD' or alpha == 0:
            returned = actual
        else:
            proposed = tuple(self.to_velocity(self.model, cur['noise'], cur['latent'],
                cur['timestep'], cur['conditions'][b],
                _supplied_net_output=cur['branches'][b]['proposed_head'])
                if cur['branches'][b]['proposed_head'] is not None else actual[b]
                for b in (0, 1))
            returned = shared_output_fusion(actual, proposed, alpha)
        self.history.append({'step': cur['step'], 'action': action, 'shared_alpha': alpha,
            'branch_status': [cur['branches'][b]['status'] for b in (0, 1)],
            'past_D_steps': [cur['branches'][b]['past_D_steps'] for b in (0, 1)],
            'extra_heads': sum(cur['branches'][b]['extra_heads'] for b in (0, 1)),
            'extra_deep_blocks': 0, 'teacher_calls': 0,
            'post_RF_fusion': True, 'C_readout_updates_D_anchor': False})
        self.completed += 1
        self.current = None
        return returned

    def finish(self):
        if self.current is not None or self.poisoned or self.completed != 36 or len(self.history) != 36:
            raise ValueError('Complete healthy full36 A deployment required')
        return {'method': self.method, 'completed_pairs': 36, 'history': copy.deepcopy(self.history),
            'D_only_final_history': [c.receipt() for c in self.calibrators],
            'teacher_calls': 0, 'extra_candidate_deep_blocks': 0,
            'extra_candidate_heads': sum(h['extra_heads'] for h in self.history),
            'candidate_original_head_elision_implemented': False,
            'endpoint_quality_or_clean_latency_claim': False}


class GuidedW1DeploymentPair:
    """Return A velocities through the existing source-derived CFG factory."""
    def __init__(self, executor, readout):
        if executor.model is not readout.model or executor.net is not readout.net:
            raise ValueError('One bound selector and A model required')
        self.executor, self.readout = executor, readout
        self.model, self.net, self.choose = executor.model, executor.net, executor.choose
        self.last = None

    def pair(self, noise, latent, timestep, conditions, choose):
        if choose is not self.choose:
            raise ValueError('Original bound selector required; A does not choose refreshes')
        self.readout.begin(noise, latent, timestep, conditions)
        try:
            actual = self.executor.pair(noise, latent, timestep, conditions, choose)
            returned = self.readout.end(actual, self.executor.last['action'])
            self.last = {**self.executor.last, 'A_readout': self.readout.history[-1]}
            return returned
        except BaseException:
            self.readout.poisoned = True
            # Both existing shared and RA selectors expose the underlying owner.
            self.executor.executor.poisoned = True
            raise
