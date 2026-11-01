"""Paid same-parent read/write intervention inside the ordinary full request.

The solver receives the selected real branch outputs and performs its original
update once. The selected whole cache is restored BEFORE that update, so the
result is exactly the same four-corner split as the post-update suffix pilot.
Each request repeats its prefix and pays both current actions. This trades a
small, explicit compute increase for one complete guarded pipeline per output.
"""
import copy

import torch

from . import clean_speed20_r1 as clean
from .cfg_paired_probe_velocity import compile_velocity
from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain
from .policy_generator_r1.continuation_preparation import TIME_BOUNDARY
from .policy_generator_r1.production_sampling import PolicyOwner, complete_request_seconds, validate_policy
from .cara_read_write_suffix_r1 import ReadWriteSuffixPilot
from .source_aware_phase_sampling import bind_globals


class PointPilot(ReadWriteSuffixPilot):
    @torch.no_grad()
    def run_point(self, corner):
        if self.used or corner not in ('00', '10', '01', '11'):
            raise ValueError('One registered four-corner intervention per request required')
        self.used = True
        results, post = {}, {}
        try:
            for action in ('C', 'D'):
                latent = self._restore(self.parent)
                self.owner.force_dense = action == 'D'
                try:
                    results[action] = PolicyOwner.pair(self.owner, self.noise, latent,
                        self.scheduler.timesteps[self.target_update-1].reshape(1, 1),
                        self.conditions, self.owner.choose)
                    self.owner.physical_pairs += 1
                finally:
                    self.owner.force_dense = False
                if (self.owner.history[-1]['actual'] != action
                        or self.owner.history[-1]['fallback_reason'] is not None):
                    raise ValueError('Paid actual C/D differs or entered fallback')
                post[action] = self._capture(latent)
            c, d = post['C'], post['D']
            if (tree_digest(plain(c.image.saved['y'])) != tree_digest(plain(d.image.saved['y']))
                    or tree_digest(plain(c.image.saved['shared'])) != tree_digest(plain(d.image.saved['shared']))
                    or c.rng_signature != d.rng_signature):
                raise ValueError('Current pair changed solver inputs, conditions or random transition')
            write = post['D' if corner[1] == '1' else 'C']
            read = 'D' if corner[0] == '1' else 'C'
            latent = self._restore(write)
            self.owner.point_record = dict(corner=corner, target_update=self.target_update,
                parent_state_sha256=self.parent_digest, pre_solver_sha256=tree_digest(self._state(latent)['y']),
                cache_after_sha256=tree_digest(plain(self._state(latent)['cache'])),
                actual_current_read=read, actual_current_write='D' if corner[1] == '1' else 'C',
                true_D_sources=[c.receipt()['anchor_steps'] for c in self.owner.readout.calibrators],
                source_sigmas=[[float(self.scheduler.sigmas[t-1]) for t in c.receipt()['anchor_steps']]
                               for c in self.owner.readout.calibrators],
                paid_C_pairs=1, paid_D_pairs=1, solver_update_delegated_to_original_sampler=True,
                CPU_snapshot_bytes=self.CPU_bytes, two_GPU_images_materialized_together=False,
                scientific_scores_read=False)
            return results[read]
        except BaseException:
            self._restore(self.parent)
            raise


class PointOwner(PolicyOwner):
    def __init__(self, *args, corner, logical_copy_cap_bytes, CPU_storage_cap_bytes, target_update=8, **kwargs):
        super().__init__(*args, **kwargs)
        if (corner not in ('00', '10', '01', '11') or any(a not in ('D', 'C') for a in self.policy['actions'])
                or type(target_update) is not int or not 8 <= target_update <= 33
                or self.policy['actions'][target_update-1:target_update+1] != ['C','C']):
            raise ValueError('Registered D/C four-corner scope required')
        self.corner = corner
        self.target_update = target_update
        self.logical_cap, self.CPU_cap = logical_copy_cap_bytes, CPU_storage_cap_bytes
        self.actual_velocity = self.generator = None
        self.point_record = None
        self.point_attempted = False
        self.physical_pairs = 0
        self.runtime = kwargs['runtime']

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        if self.readout.completed + 1 != self.target_update:
            result = super().pair(noise, latent, timestep, conditions, choose)
            self.physical_pairs += 1
            return result
        if self.point_attempted or self.actual_velocity is None or self.generator is None:
            raise ValueError('Recover the attempted intervention; original closure/generator required')
        self.point_attempted = True
        pilot = PointPilot(self, self.actual_velocity, latent, noise, self.generator,
            runtime=self.runtime, target_update=self.target_update, logical_copy_cap_bytes=self.logical_cap,
            CPU_storage_cap_bytes=self.CPU_cap)
        if any(a is not b for a, b in zip(conditions, pilot.conditions)) or choose is not self.choose:
            raise ValueError('Actual current conditions or selector differ')
        return pilot.run_point(self.corner)

    def close(self):
        super().close()
        self.actual_velocity = self.generator = None


def execute(inference, sample, *, profile, policy, corner,
            logical_copy_cap_bytes, CPU_storage_cap_bytes, target_update=8, **kwargs):
    """One ordinary guarded full36 request, with37 paid model pairs."""
    validate_policy(profile, policy)
    holder = {}
    scheduler = inference.pipe.model.sample_scheduler
    original_step = scheduler.step
    def remember_generator(*args, **kw):
        owner = holder['owner']
        generator = kw.get('generator')
        if owner.generator is None:
            owner.generator = generator
        elif generator is not owner.generator:
            raise ValueError('Original request generator changed')
        return original_step(*args, **kw)
    def install(model, method, context, runtime, wc, rf, settings, calibration, specs, audit=False):
        wc.apply_worldcache(model.net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
        model.net.worldcache_enabled = True
        owner = PointOwner(model, policy=policy, profile=profile, corner=corner,
            target_update=target_update,
            logical_copy_cap_bytes=logical_copy_cap_bytes, CPU_storage_cap_bytes=CPU_storage_cap_bytes,
            context=context + (policy['fingerprint'],), runtime=runtime, wc=wc, rf=rf)
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
    result.update(corner=corner, intervention=copy.deepcopy(owner.point_record),
        physical_model_pairs=owner.physical_pairs, semantic_history=copy.deepcopy(owner.history),
        timing_boundary=TIME_BOUNDARY, diagnostic_timing_only=True,
        full_request_seconds=complete_request_seconds(result) if result.get('core_seconds') else None,
        scientific_endpoint_accepted=False)
    if result['status'] == 'COMPLETE' and (owner.physical_pairs != 37 or owner.point_record is None
            or result['solver_steps'] != 36 or result['guided_pairs'] != 36):
        raise ValueError('Complete guarded four-corner path/count differs')
    return result
