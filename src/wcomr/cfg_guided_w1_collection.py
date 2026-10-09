"""Same-state branch outputs, strictly-past D calibration, score-only teachers.

The collector follows a separately fixed shared D6 trajectory. It does not
choose or improve a deployed policy, and keeps all teacher/candidate work out
of the deployment anchors. Real-model parity and complete artifacts remain
separate from the controlled CPU checks.
"""
import copy
import hashlib
import time

import torch

from .calibration import ResidualCalibrator
from .cfg_guided_w1_outputs import unit_increment_residual, guided_velocity_moments, shared_output_fusion


SELECTED_STEPS = (12, 30)
# The already validated native-policy pair controller permits step35 CC and
# checks continuation modulo70. Step36 starts a new cycle and is protected DD.
DENSE_STEPS = tuple(range(1, 8)) + (13, 19, 25, 31, 36)
CACHE_FIELDS = ('cnt', 'worldcache_step_skipped_count', 'accumulated_rel_l1_distance',
    'residual_cache', 'probe_residual_cache', 'residual_window', 'probe_residual_window',
    'previous_internal_states', 'previous_input', 'previous_output', 'resume_flag',
    'affline_scale_log_info', 'affline_emb', 'crossattn_emb')


def signature(value):
    if isinstance(value, torch.Tensor):
        return ('tensor', id(value), None if torch.is_inference(value) else value._version,
                tuple(value.shape), str(value.dtype), str(value.device))
    if isinstance(value, dict): return ('dict', tuple((k, signature(v)) for k, v in sorted(value.items())))
    if isinstance(value, (list, tuple)): return (type(value).__name__, tuple(signature(v) for v in value))
    if value is None or isinstance(value, (str, int, float, bool)): return value
    raise TypeError('Uncovered collection state signature: '+type(value).__name__)


def tensor_sha(value):
    h = hashlib.sha256(str((list(value.shape), str(value.dtype))).encode())
    h.update(value.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy().tobytes())
    return h.hexdigest()


class GuidedW1Collector:
    def __init__(self, model, *, scene, context, enabled, writer):
        if (type(scene) is not str or not scene or type(context) is not tuple or not context
                or type(enabled) is not bool or not callable(writer)):
            raise ValueError('Explicit immutable scene/context, collection switch and writer required')
        self.model, self.net = model, model.net
        self.scene, self.context, self.enabled, self.writer = scene, context, enabled, writer
        self.calibrators = [ResidualCalibrator(), ResidualCalibrator()]
        for c in self.calibrators: c.reset(context)
        self.warp = self.to_velocity = None
        self.completed = 0; self.running = False; self.records = []; self.events = []
        self.current = None; self.in_diagnostic = False

    def begin(self, noise, latent, timestep, conditions):
        if (self.running or self.completed >= 36 or len(conditions) != 2
                or self.model.net is not self.net or torch.is_grad_enabled()):
            raise ValueError('One complete own-state pair at a time under no_grad')
        self.running = True
        self.current = {'step': self.completed+1, 'noise': noise, 'latent': latent,
            'timestep': timestep, 'conditions': conditions, 'branches': {}, 'prewarp': {},
            'input_signature': signature((noise, latent, timestep)),
            'condition_signature': signature([vars(c) for c in conditions])}

    def _branch(self, net, branch):
        if (not self.running or net is not self.net or branch not in (0, 1)
                or net.cnt != (2*(self.current['step']-1)+branch) % 70):
            raise ValueError('Actual monotonic pair/branch differs from source counter')
        return self.current['step']

    def prewarp(self, net, branch, hidden):
        step = self._branch(net, branch)
        if self.enabled and step in SELECTED_STEPS:
            if branch in self.current['prewarp']: raise ValueError('Duplicate original prewarp output')
            self.current['prewarp'][branch] = hidden.detach().clone()

    def state_signature(self):
        return signature({'cache': {k: getattr(self.net, k) for k in CACHE_FIELDS if hasattr(self.net, k)},
            'anchors': [[(a.step, a.probe, a.residual) for a in c.anchors] for c in self.calibrators],
            'statistics': [c.receipt() for c in self.calibrators]})

    @torch.no_grad()
    def hidden(self, net, skipped, branch, original, probe, hidden, block_kwargs, embedding, adaln):
        step = self._branch(net, branch)
        if skipped != (step not in DENSE_STEPS): raise ValueError('Registered fixed D6 action differs')
        if not self.enabled: return
        if not skipped:
            # Actual D caches, including warmup where test_x was not the probe.
            accepted = self.calibrators[branch].observe_full(context=self.context, step=step,
                probe=net.probe_residual_cache[branch], residual=net.residual_cache[branch])
            if not accepted: raise ValueError('Actual D anchor invalid; no narrowed subset')
            self.events.append({'step': step, 'branch': branch, 'kind': 'ACTUAL_D_ONLY_ANCHOR'})
            return
        if step not in SELECTED_STEPS: return
        c = self.calibrators[branch]
        if (self.warp is None or self.to_velocity is None or branch not in self.current['prewarp']
                or len(c.anchors) != 2 or any(a.step >= step for a in c.anchors)
                or c.context != self.context or any(m.training for m in net.modules())):
            raise ValueError('Selected CC requires past true D anchors and exact compiled helpers')
        before = self.state_signature(); history = copy.deepcopy(c.receipt())
        buffers = [(b, b.detach().clone()) for b in net.buffers()]
        parameters = [(p, p._version) for p in net.parameters() if not torch.is_inference(p)]
        devices = [probe.device.index if probe.device.index is not None else torch.cuda.current_device()] if probe.device.type == 'cuda' else []
        start = time.perf_counter()
        try:
            self.in_diagnostic = True
            with torch.random.fork_rng(devices=devices):
                p = probe-original; anchor = c.anchors[-1]
                beta1 = unit_increment_residual(current_probe=p, anchor_probe=anchor.probe, anchor_residual=anchor.residual)
                scalar, status = c.predict(context=self.context, step=step, probe=p,
                    official=self.current['prewarp'][branch]-original, mode='scalar')
                candidates = {}
                for name, residual in [('BETA1', beta1), ('W1', scalar)]:
                    x = self.warp(net, original+residual, net.residual_cache[branch], original.shape[1])
                    candidates[name] = net.unpatchify(net.final_layer(x, embedding, adaln_lora_B_T_3D=adaln))
                teacher = probe.detach().clone()
                for block in net.blocks[net.probe_depth:]: teacher = block(teacher, **block_kwargs)
                candidates['DENSE'] = net.unpatchify(net.final_layer(teacher, embedding, adaln_lora_B_T_3D=adaln))
                if self.state_signature() != before or any(p._version != v for p, v in parameters):
                    raise ValueError('Score-only teacher/candidate changed deployment cache or D history')
                self.current['branches'][branch] = {'head': candidates, 'W1_status': status,
                    'past_D_history': history, 'teacher_deep_blocks': len(net.blocks)-net.probe_depth,
                    'diagnostic_seconds': time.perf_counter()-start}
        finally:
            for b, saved in buffers: b.copy_(saved)
            self.in_diagnostic = False
            self.current['prewarp'].pop(branch, None)

    def output(self, net, branch, head):
        step = self._branch(net, branch)
        if self.enabled and step in SELECTED_STEPS:
            if branch not in self.current['branches']: raise ValueError('Head output precedes same-state collection')
            self.current['branches'][branch]['head']['ORIGINAL'] = head.detach().clone()

    @torch.no_grad()
    def end(self, actual, action):
        if not self.running or action != ('DD' if self.current['step'] in DENSE_STEPS else 'CC'):
            raise ValueError('Registered actual D6 pair not completed')
        cur = self.current; step = cur['step']
        try:
            if signature((cur['noise'], cur['latent'], cur['timestep'])) != cur['input_signature']:
                raise ValueError('Collection changed actual solver inputs')
            if signature([vars(c) for c in cur['conditions']]) != cur['condition_signature']:
                raise ValueError('Collection changed branch conditions')
            if self.enabled and step in SELECTED_STEPS:
                if set(cur['branches']) != {0, 1}: raise ValueError('Incomplete registered CFG origin')
                velocities = {}
                for name in ('ORIGINAL', 'BETA1', 'W1', 'DENSE'):
                    velocities[name] = tuple(self.to_velocity(self.model, cur['noise'], cur['latent'],
                        cur['timestep'], cur['conditions'][branch],
                        _supplied_net_output=cur['branches'][branch]['head'][name]) for branch in (0, 1))
                if not all(torch.equal(x, y) for x, y in zip(actual, velocities['ORIGINAL'])):
                    raise ValueError('Observed original head does not recover actual post-RF output')
                moments = {name: guided_velocity_moments(scene=self.scene, state='step'+str(step),
                    original=velocities['ORIGINAL'], proposed=velocities[name], dense=velocities['DENSE'])
                    for name in ('BETA1', 'W1')}
                for pair in velocities.values():
                    if any(not bool(torch.isfinite(v).all()) for v in pair): raise ValueError('Nonfinite collected velocity')
                fused = {str(alpha): shared_output_fusion(velocities['ORIGINAL'], velocities['W1'], alpha)
                         for alpha in (0, .5, 1)}
                tensors = {name: tuple(v.detach().cpu().clone() for v in pair) for name, pair in velocities.items()}
                artifact = self.writer(self.scene, step, tensors)
                self.records.append({'scene': self.scene, 'step': step, 'action': action,
                    'same_actual_solver_origin_sha256': [tensor_sha(v) for v in (cur['noise'],cur['latent'],cur['timestep'])],
                    'actual_post_RF_original_direct_equal': True,
                    'past_D_history': [cur['branches'][b]['past_D_history'] for b in (0,1)],
                    'W1_status': [cur['branches'][b]['W1_status'] for b in (0,1)],
                    'teacher_deep_blocks': [cur['branches'][b]['teacher_deep_blocks'] for b in (0,1)],
                    'diagnostic_seconds': sum(cur['branches'][b]['diagnostic_seconds'] for b in (0,1)),
                    'velocity_sha256': {k: [tensor_sha(v) for v in pair] for k,pair in tensors.items()},
                    'shared_alpha_output_sha256': {k: [tensor_sha(v) for v in pair] for k,pair in fused.items()},
                    'moments': moments, 'artifact': artifact,
                    'teacher_updates_deployment_anchor': False,
                    'provenance': 'ACTUAL_CURRENT_PROBE_DEEP_SCORE_ONLY_AND_ORIGINAL_SOURCE_HEAD_RF; strict past actual D',
                    'real_model_or_quality_claim': False})
            self.completed += 1
        finally:
            self.current = None; self.running = False

    def finish(self):
        if self.running or self.completed != 36 or [r['step'] for r in self.records] != (list(SELECTED_STEPS) if self.enabled else []):
            raise ValueError('Complete full36 and both preregistered origins required')
        expected = [(s,b) for s in DENSE_STEPS for b in (0,1)] if self.enabled else []
        if [(e['step'],e['branch']) for e in self.events] != expected:
            raise ValueError('Only actual D observations may populate calibrator history')
        return {'completed_pairs': self.completed, 'selected_steps': list(SELECTED_STEPS),
            'records': self.records, 'actual_D_events': self.events,
            'D_only_final_history': [c.receipt() for c in self.calibrators],
            'score_only_teachers': 2*len(self.records), 'real_model_or_quality_or_latency_claim': False}


class CollectedSchedulePairExecutor:
    """Explicit pair origin passed to read-only hooks before the shared executor."""
    def __init__(self, executor, collector):
        if executor.model is not collector.model or executor.net is not collector.net:
            raise ValueError('Collection executor model differs')
        self.executor, self.collector = executor, collector
        self.model, self.net, self.choose = executor.model, executor.net, executor.choose

    def pair(self, noise, latent, timestep, conditions, choose):
        if choose is not self.choose: raise ValueError('Bound shared D6 selector required')
        self.collector.begin(noise, latent, timestep, conditions)
        try:
            values = self.executor.pair(noise, latent, timestep, conditions, choose)
            self.collector.end(values, self.executor.last['action'])
            return values
        except BaseException:
            self.executor.executor.poisoned = True
            raise
