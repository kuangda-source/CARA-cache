"""Isolated F features and B same-state executor screen on unchanged P_OFF.

The ordinary parent and solver never consume a diagnostic arm. B runs a
separate physical DD continuation with a no-op collector, not a fake semantic
D commit in the deployed controller. Every completed trial restores the real
sampler/owned state. F reuses only exactly bound historical offline labels.
"""
import copy
import hashlib
import math
import time
from contextlib import contextmanager

import torch

from .math_n2_sampling_owner_r1 import MathSamplingOwner
from .cfg_guided_w1_forward import compile_collection
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .partial_mlp import block_indices
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .spectral_probe_r1 import (ProbeIdentity, causal_slice, probe_features,
    feature_tensors, time_device_pipeline, compile_probe_collection)
from .block_probe_r1 import ProbeHistory, BlockProbeArm, MODES

VERSION = 'ISOLATED_FB_NATURAL16_BLOCK4_R1'


class NoopCollector:
    def prewarp(self, *a): pass
    def hidden(self, *a): pass
    def output(self, *a): pass


class FBProbeOwner(MathSamplingOwner):
    def __init__(self, *args, states, config, writer, scene, **kwargs):
        if kwargs.get('horizon') is not None or kwargs.get('source_mode') != 'P_OFF':
            raise ValueError('Unchanged frozen P_OFF parent required')
        super().__init__(*args, **kwargs)
        self.scene, self.config, self.writer = scene, {**config, **config.get('checkpoint_reserves', {})}, writer
        self.states = {s['chosen']['step']: s for s in states}
        if len(self.states) != 4:
            raise ValueError('All four natural source/phase cells required')
        self.b_steps = {p['step'] for p in config['b_points'] if p['scene'] == scene}
        if not self.b_steps.issubset(self.states):
            raise ValueError('B must use registered natural F states')
        self.records = []; self.actual_pair_computations = 0
        self.active_velocity = self.active_generator = None
        self._point = None; self._features = None; self._probe_buffers = {}
        self.block_history = ProbeHistory(self.net.blocks,
            projection_owner=self.deployment.core).install()
        # Replace only this owner's generated callable, never module globals or
        # the pinned model implementation. Existing inverse proofs remain.
        _, denoise, proof = compile_probe_collection(kwargs['runtime'], kwargs['wc'],
            kwargs['rf'], self.deployment, self._observe,
            dense_context=self._parent_dense)
        self.base.denoise = denoise
        self.compiler.update(proof)
        self._runtime, self._wc, self._rf = kwargs['runtime'], kwargs['wc'], kwargs['rf']

    @contextmanager
    def _parent_dense(self, net, slot):
        d = self.deployment
        with d.dense_context(net, slot):
            cur = d.current
            if not cur.get('_fb_history_started'):
                cur['stack'].enter_context(self.block_history.pair(
                    step=cur['step'], action=cur['action'], context=self.context))
                cur['_fb_history_started'] = True
            with self.block_history.branch(slot):
                yield

    def _observe(self, net, slot, original, probe, working_probe):
        if self._point is None:
            return
        if slot in self._probe_buffers or working_probe is None:
            raise ValueError('Exactly two causal probes with real sources required')
        self._probe_buffers[slot] = (original, probe, working_probe)
        if slot == 0:
            return
        if set(self._probe_buffers) != {0, 1}:
            raise ValueError('Complete CFG observation required')
        def pipeline(mode):
            selected = [causal_slice(*self._probe_buffers[s]) for s in (0, 1)]
            return feature_tensors(tuple(v[0] for v in selected),
                                   tuple(v[1] for v in selected), mode=mode)
        timings = {m: time_device_pipeline(lambda m=m: pipeline(m),
            device=original.device, authorized_gpu=original.is_cuda)
            for m in ('RAW', 'HAAR', 'FFT')}
        for v in timings.values():
            v['boundary'] = 'BOTH_BRANCH_GATHER_DIFFERENCE_LAYOUT_TRANSFORM_AGGREGATE_NO_CPU_IO_OR_SELECTOR'
            v['requires_existing_full_working_probe_cache'] = True
        selected = [causal_slice(*self._probe_buffers[s], cpu=True) for s in (0, 1)]
        self._features = dict(current=tuple(v[0] for v in selected),
            source=tuple(v[1] for v in selected), geometry=tuple(original.shape),
            timing=timings, indices=selected[0][2])
        self._probe_buffers.clear()

    def _block_trials(self, step, noise, latent, timestep, conditions):
        if self.active_velocity is None or self.active_generator is None:
            raise ValueError('Actual sampler closure and generator required')
        before = DiagnosticSnapshot(self, latent, noise, self.active_velocity,
                                    self.active_generator, self.config)
        history = self.block_history.snapshot()
        history_sha = tree_digest(plain(history))
        tokens = math.prod(next(iter(self.block_history.mlp.values())).value.shape[:-1])
        receipts, payload = [], {}
        # All modes use the same prior source, and both branches share masks.
        # Reverse alternating timed rounds to expose order/thermal effects.
        for rep in range(4):
            modes = MODES if rep % 2 == 0 else MODES[::-1]
            for mode in modes:
                allocated_before_install = torch.cuda.memory_allocated() if latent.is_cuda else 0
                arm = BlockProbeArm(self.net.blocks, self.block_history, mode).install()
                try:
                    @contextmanager
                    def dense_context(net, slot):
                        with arm.branch(slot): yield
                    _, denoise, _ = compile_collection(self._runtime, self._wc, self._rf,
                        NoopCollector(), dense_context=dense_context)
                    trial = NativePolicyPairedExecutor(self.model, denoise, torch,
                        wc_forward=self._wc.worldcache_mini_train_dit_forward,
                        rf_denoise=self._rf.Video2WorldModelRectifiedFlow.denoise)
                    ids = None
                    if mode.startswith(('P0_', 'M8_')):
                        seed = None
                        if mode.endswith('RANDOM'):
                            key = f'FB-R1:{self.scene}:{step}'
                            seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big') % (2**63 - 1)
                        ids = block_indices(tokens, .5, block_size=128,
                            opportunity=step, random_seed=seed)
                    self.step = step
                    with self.deployment.core.readonly(), self.block_history.readonly():
                        memory_before = {'allocated': torch.cuda.memory_allocated(),
                            'reserved': torch.cuda.memory_reserved()} if latent.is_cuda else {'allocated': 0, 'reserved': 0}
                        if latent.is_cuda: torch.cuda.reset_peak_memory_stats()
                        synchronize(); start = time.perf_counter()
                        with arm.pair(step=step, context=self.context, indices=ids):
                            output = trial.pair(noise, latent, timestep, conditions, lambda packets: 'DD')
                        synchronize(); seconds = time.perf_counter() - start
                        memory_after = {'allocated': torch.cuda.memory_allocated(),
                            'reserved': torch.cuda.memory_reserved(), 'peak_allocated': torch.cuda.max_memory_allocated(),
                            'peak_reserved': torch.cuda.max_memory_reserved()} if latent.is_cuda else dict(allocated=0,reserved=0,peak_allocated=0,peak_reserved=0)
                    self.actual_pair_computations += 1
                    if trial.last['action'] != 'DD' or trial.poisoned:
                        raise ValueError('Full physical same-state continuation required')
                    key = f'{mode}_repeat{rep}'
                    payload[key] = tuple(v.detach().cpu().clone() for v in output)
                    receipts.append(dict(mode=mode, repeat=rep, warmup=rep == 0,
                        full_pair_seconds=seconds, arm=arm.receipt(),
                        token_mask_sha256=None if ids is None else tree_digest(ids),
                        parent_history_bytes=self.block_history.cache_bytes(),
                        memory=dict(before_install_allocated=allocated_before_install,
                            before=memory_before, after=memory_after,
                            diagnostic_bank_present_in_all_modes=True,
                            logical_cache_bytes_may_alias_shared_bank=True),
                        timed_boundary='TWO_PROBES_FULL_DEEP_GROUP_HEAD_RF_AND_ARM_CACHE_MAINTENANCE',
                        source='STRICTLY_PAST_NATURAL_PARENT_NOT_CURRENT_TEACHER'))
                finally:
                    arm.close()
                # Only restore a healthy completed branch, not failed work.
                before.restore()
                if tree_digest(plain(self.block_history.snapshot())) != history_sha:
                    raise ValueError('Diagnostic arm mutated actual prior history')
        truth = payload['DENSE_PLAIN_repeat0']
        for mode in MODES:
            for rep in range(4):
                value = payload[f'{mode}_repeat{rep}']
                reference = truth if mode.startswith('DENSE_') else payload[f'{mode}_repeat0']
                if any(not torch.equal(x, y) for x, y in zip(value, reference)):
                    raise ValueError('Dense/stateful parity or deterministic repeat failed: ' + mode)
        return receipts, payload, before.restores

    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history) + 1
        point = self.states.get(step)
        if point is None:
            self.actual_pair_computations += 1
            return super().pair(noise, latent, timestep, conditions, choose)
        state = self.controller._state(); chosen = point['chosen']
        if (state[0] != chosen['true_D_anchor'] or state[1] != point['source']
                or state[2] != chosen['source_birth'] or step-state[2] != chosen['age']):
            raise ValueError('Natural pre-action state not reproduced')
        input_sha = tree_digest((noise, latent, timestep))
        D_sha = tree_digest(plain([vars(c) for c in self.deployment.dense]))
        work_sha = tree_digest((self.deployment.working, self.net.probe_residual_cache, self.net.residual_cache))
        trials, payload, restores = self._block_trials(step, noise, latent, timestep, conditions) if step in self.b_steps else ([], {}, [])
        self._point = point; self._features = None; self._probe_buffers.clear()
        try:
            self.actual_pair_computations += 1
            actual = super().pair(noise, latent, timestep, conditions, choose)
        finally:
            self._point = None
        if self._features is None or self._probe_buffers:
            raise ValueError('Registered point did not collect both causal probes')
        h = copy.deepcopy(self.history[-1]); decision = h['source_policy']['decision']
        if h['action'] != chosen['actual_pi0_action'] * 2 or tree_digest((noise, latent, timestep)) != input_sha:
            raise ValueError('Parent action/state differs')
        packets = self.base.last['paid_probes']
        raw = {'local_proxy': decision['local_proxy'], 'gain': decision['gain'],
               'birth_floor': state[3]}
        for p in packets:
            slot = 'c' if p.slot == 0 else 'u'
            raw['delta_x_' + slot] = p.delta_x; raw['delta_y_' + slot] = p.delta_y
        sigmas = self.model.sample_scheduler.sigmas
        f = self._features
        identity = ProbeIdentity(self.scene, step, state[1], state[2], state[0],
            float(sigmas[step-1]), float(sigmas[state[2]-1]), float(sigmas[state[0]-1]),
            f['geometry'], f'{self.scene}:{state[1]}:{state[2]}')
        feature_row = probe_features(f['current'], f['source'], identity, raw)
        payload.update(F_current=f['current'], F_source=f['source'])
        artifact = self.writer(self.scene, step, payload)
        self.records.append(dict(scene=self.scene, step=step, point=point,
            input_sha256=input_sha, source_state_sha256=work_sha, true_D_state_sha256=D_sha,
            parent_pre_action=state, parent_continues=h['action'], feature_row=feature_row,
            feature_timing=f['timing'], artifact=artifact, b_trials=trials,
            restores=restores, offline_committed_to_parent=False))
        self._features = None
        return actual

    def close(self):
        self.block_history.close()
        super().close()


@contextmanager
def fb_install(clean, scheduler, states, config, writer, parameters, holder):
    from .clean_speed20_r1 import patched
    original_compile = clean.compile_velocity; old_step = scheduler.step
    scenes = {s['scene'] for s in states}
    if len(scenes) != 1: raise ValueError('One full natural parent scene required')
    def factory(*a, **kw):
        owner = FBProbeOwner(*a, states=states, config=config, writer=writer,
            scene=next(iter(scenes)), math_parameters=parameters, source_mode='P_OFF', **kw)
        holder['owner'] = owner; return owner
    def compile_velocity(runtime, rf, owner, choose):
        fn, proof = original_compile(runtime, rf, owner, choose)
        def bound(model, *a, **kw):
            velocity = fn(model, *a, **kw); owner.active_velocity = velocity; return velocity
        return bound, proof
    def solver_step(*a, **kw):
        owner = holder.get('owner'); generator = kw.get('generator')
        if owner is not None:
            if owner.active_generator is not None and owner.active_generator is not generator:
                raise ValueError('Original generator identity changed')
            owner.active_generator = generator
        return old_step(*a, **kw)
    with patched(clean, 'CurrentBirthSamplingOwner', factory), patched(clean, 'compile_velocity', compile_velocity), patched(scheduler, 'step', solver_step):
        yield
