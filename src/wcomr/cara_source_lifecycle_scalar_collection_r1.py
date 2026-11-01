"""Paid same-state scalar probes inside an ordinary full36 parent request.

The caller owns admission, assets, billing, storage and complete acceptance.
One CPU-owned parent image isolates a shadow D, then the original C state is
restored and freely continued. No alternative trajectory supplies the teacher.
"""
import copy
import inspect

import torch

from . import clean_speed20_r1 as clean
from .cara_read_write_suffix_r1 import ReadWriteSuffixPilot
from .cfg_paired_probe_velocity import compile_velocity
from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain
from .policy_generator_r1.continuation_preparation import TIME_BOUNDARY
from .policy_generator_r1.production_sampling import PolicyOwner, complete_request_seconds, validate_policy
from .prepared_input import RNGState
from .source_aware_phase_sampling import bind_globals


class ScalarProbe(ReadWriteSuffixPilot):
    """Reuse complete-state ownership, supporting any registered legal C.

    The four-corner pilot's C/C and point8..33 restrictions belong to its suffix
    experiment. Scalar collection also needs isolated C and the legal C35.
    Its state capture/restoration operations are shared unchanged.
    """
    @torch.no_grad()
    def __init__(self, owner, latent, noise, *, target, logical_cap, CPU_cap):
        t = target['t']
        if (not isinstance(owner, PolicyOwner) or owner.readout.current is not None
                or type(t) is not int or not 8 <= t <= 35
                or owner.policy['actions'][t-1] != 'C'
                or owner.model.sample_scheduler._step_index != t-1
                or owner.readout.completed != t-1 or int(owner.net.cnt) != 2*(t-1)):
            raise ValueError('Original healthy state immediately before a registered legal C required')
        cells = inspect.getclosurevars(owner.actual_velocity).nonlocals
        if (set(cells) != {'self', 'condition', 'uncondition', 'guidance'}
                or cells['self'] is not owner.model or cells['guidance'] != 7
                or not isinstance(owner.generator, torch.Generator)):
            raise ValueError('Original velocity closure, CFG and request generator required')
        self.owner, self.model, self.net = owner, owner.model, owner.net
        self.scheduler = owner.model.sample_scheduler
        self.conditions = cells['condition'], cells['uncondition']
        self.noise, self.noise_digest = noise, tree_digest(noise)
        self.generator, self.target_update = owner.generator, t
        self.logical_cap, self.CPU_cap, self.CPU_bytes = logical_cap, CPU_cap, 0
        self.parameters = [(name, value, value._version) for name, value in self.net.named_parameters()]
        self.bindings = self.net.forward, self.model.denoise, self.scheduler.step
        self.used = False
        sources = [c.receipt()['anchor_steps'] for c in owner.readout.calibrators]
        if sources != [[target['a'], target['b']]]*2:
            raise ValueError('Both actual latest-two D sources must match the registered parent state')
        self.sources = copy.deepcopy(sources)
        self.parent = self._capture(latent)
        self.parent_digest = self.parent.image.digest

    @torch.no_grad()
    def run(self):
        if self.used:
            raise ValueError('Original scalar probe already attempted; no repeat')
        self.used = True
        timestep = self.scheduler.timesteps[self.target_update-1].reshape(1, 1)
        try:
            latent = self._restore(self.parent)
            self.owner.force_dense = True
            try:
                self.owner.physical_pairs += 1
                dense = PolicyOwner.pair(self.owner, self.noise, latent, timestep,
                                         self.conditions, self.owner.choose)
            finally:
                self.owner.force_dense = False
            if (self.owner.history[-1]['actual'] != 'D'
                    or self.owner.history[-1]['fallback_reason'] is not None
                    or dense.dtype != torch.float32):
                raise ValueError('Actual FP32 same-state Dense teacher without fallback required')
            # Only the guided output moves to CPU. A second feature/cache image
            # is never retained on the GPU alongside the restored parent.
            dense_cpu = dense.detach().to('cpu', copy=True)
            del dense
            latent = self._restore(self.parent)
            restored = tree_digest(plain(self._state(latent)))
            if restored != self.parent_digest or RNGState().signatures() != self.parent.rng_signature:
                raise ValueError('Shadow D did not restore the complete original parent/RNG')
            self.owner.physical_pairs += 1
            cached = PolicyOwner.pair(self.owner, self.noise, latent, timestep,
                                      self.conditions, self.owner.choose)
            if (self.owner.history[-1]['actual'] != 'C'
                    or self.owner.history[-1]['fallback_reason'] is not None
                    or cached.dtype != torch.float32 or cached.shape != dense_cpu.shape):
                raise ValueError('Actual FP32 C readout of the identical parent without fallback required')
            difference = cached.detach().to('cpu', dtype=torch.float64)-dense_cpu.double()
            squared = float(difference.square().sum().item())
            if not torch.isfinite(torch.tensor(squared, dtype=torch.float64)):
                raise ValueError('Nonfinite raw same-state scalar target')
            self.record = dict(t=self.target_update, a=self.sources[0][0], b=self.sources[0][1],
                               source_steps_by_CFG=self.sources,
                               C_input_state_id=self.parent_digest,
                               shadow_D_input_state_id=self.parent_digest,
                               parent_before_shadow_id=self.parent_digest,
                               parent_after_shadow_id=restored,
                               sum_squared_error_fp64=squared, element_count=difference.numel(),
                               CPU_snapshot_bytes=self.CPU_bytes,
                               teacher_actual='D', parent_actual='C',
                               teacher_writes_parent=False, shadow_extra_pairs=1)
            # The ordinary sampler now consumes C and advances UniPC once.
            return cached
        except BaseException:
            self._restore(self.parent)
            raise


class ScalarOwner(PolicyOwner):
    def __init__(self, *args, label_states, logical_cap, CPU_cap, **kwargs):
        super().__init__(*args, **kwargs)
        self.targets = {s['t']: copy.deepcopy(s) for s in label_states}
        if (len(self.targets) != 8 or len(label_states) != 8
                or any(self.policy['actions'][t-1] != 'C' for t in self.targets)
                or any(a not in ('D', 'C') for a in self.policy['actions'])):
            raise ValueError('Eight distinct registered C states on one pure D/C parent required')
        self.logical_cap, self.CPU_cap = logical_cap, CPU_cap
        self.actual_velocity = self.generator = None
        self.attempted, self.labels, self.physical_pairs = set(), [], 0

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        t = self.readout.completed+1
        if t not in self.targets:
            self.physical_pairs += 1
            return super().pair(noise, latent, timestep, conditions, choose)
        if t in self.attempted or self.actual_velocity is None or self.generator is None:
            raise ValueError('Original scalar state already attempted or unbound; no repeat')
        self.attempted.add(t)
        probe = ScalarProbe(self, latent, noise, target=self.targets[t],
                            logical_cap=self.logical_cap, CPU_cap=self.CPU_cap)
        if any(a is not b for a, b in zip(conditions, probe.conditions)) or choose is not self.choose:
            raise ValueError('Actual parent conditions/selector differ')
        result = probe.run()
        self.labels.append(probe.record)
        return result

    def close(self):
        super().close()
        self.actual_velocity = self.generator = None


def execute(inference, sample, *, profile, policy, label_states, member, parent_id,
            logical_copy_cap_bytes, CPU_storage_cap_bytes, **kwargs):
    """One complete36 parent with exactly eight additional shadow-D pairs."""
    validate_policy(profile, policy)
    holder = {}
    scheduler = inference.pipe.model.sample_scheduler
    original_step = scheduler.step

    def remember_generator(*args, **kw):
        owner = holder['owner']
        generator = kw.get('generator')
        if owner.generator is None:
            owner.generator = generator
        elif owner.generator is not generator:
            raise ValueError('Original parent request generator changed')
        return original_step(*args, **kw)

    def install(model, method, context, runtime, wc, rf, settings, calibration, specs, audit=False):
        wc.apply_worldcache(model.net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
        model.net.worldcache_enabled = True
        owner = ScalarOwner(model, policy=policy, profile=profile, label_states=label_states,
                            logical_cap=logical_copy_cap_bytes, CPU_cap=CPU_storage_cap_bytes,
                            context=context+(policy['fingerprint'],), runtime=runtime, wc=wc, rf=rf)
        holder['owner'] = owner
        factory, _ = compile_velocity(runtime, rf, owner, owner.choose)

        def capture_velocity(bound, *args, **kw):
            value = factory(bound, *args, **kw)
            owner.actual_velocity = value
            return value

        return capture_velocity, owner, None, owner.readout

    runner = bind_globals(clean.execute, {'install': install})
    with clean.patched(scheduler, 'step', remember_generator):
        result = runner(inference, sample, 'KEEP_A_P', **kwargs)
    owner = holder['owner']
    labels = [dict(row, member=member, parent_id=parent_id,
                   parent_fingerprint=policy['fingerprint']) for row in owner.labels]
    if result['status'] == 'COMPLETE' and (owner.physical_pairs != 44 or len(labels) != 8
            or result['solver_steps'] != 36 or result['guided_pairs'] != 36
            or [r['actual'] for r in owner.history] != policy['actions']
            or any(r['fallback_reason'] is not None for r in owner.history)):
        raise ValueError('Complete36 parent/eight-shadow denominator or free trajectory differs')
    result.update(scalar_labels=labels, physical_model_pairs=owner.physical_pairs,
                  semantic_history=copy.deepcopy(owner.history), timing_boundary=TIME_BOUNDARY,
                  diagnostic_timing_only=True, scientific_endpoint_accepted=False,
                  full_request_seconds=complete_request_seconds(result) if result.get('core_seconds') else None)
    return result
