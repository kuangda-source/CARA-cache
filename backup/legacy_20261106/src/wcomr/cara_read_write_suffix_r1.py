"""In-process M1 four-corner suffix prototype for a loaded D/C PolicyOwner.

The caller owns model loading, admission, storage, billing and output scoring.
This component is CPU-integration preparation, pending production memory and
whole-entry acceptance. It neither dispatches work nor implements an adjoint.
"""
from dataclasses import dataclass
import inspect

import torch

from .cpu_owned_state_snapshot import CPUOwnedStateImage
from .mid_coverage import WC_FIELDS, tree_digest
from .partial_mlp_deployment_state import plain
from .policy_generator_r1.production_sampling import PolicyOwner
from .prepared_input import RNGState
from .rv0_fork import object_state, official_suffix


@dataclass
class _Checkpoint:
    image: CPUOwnedStateImage
    rng: RNGState
    rng_signature: dict


class ReadWriteSuffixPilot:
    """Pay C and D at one parent, then freely evolve all four complete suffixes.

The split is AFTER the current solver update. Its whole dictionary belongs
with the chosen latent; all cache windows, source history and owner counters
belong with the chosen write. No cache tensor is transplanted on its own.
"""
    @torch.no_grad()
    def __init__(self, owner, velocity_fn, latent, noise, generator, *, runtime,
                 target_update, logical_copy_cap_bytes, CPU_storage_cap_bytes):
        if (not isinstance(owner, PolicyOwner) or owner.readout.current is not None
                or any(a not in ('D', 'C') for a in owner.policy['actions'])
                or type(target_update) is not int or not 8 <= target_update <= 33
                or owner.policy['actions'][target_update-1:target_update+1] != ['C', 'C']
                or owner.model.sample_scheduler._step_index != target_update - 1
                or owner.readout.completed != target_update - 1
                or int(owner.net.cnt) != 2 * (target_update - 1)):
            raise ValueError('Healthy full36 D/C parent immediately before an eligible C/C pair required')
        cells = inspect.getclosurevars(velocity_fn).nonlocals
        if (set(cells) != {'self', 'condition', 'uncondition', 'guidance'}
                or cells['self'] is not owner.model or cells['guidance'] != 7
                or not isinstance(generator, torch.Generator)):
            raise ValueError('Original two-condition velocity closure and CFG 8/-7 required')
        self.owner, self.model, self.net = owner, owner.model, owner.net
        self.scheduler, self.velocity_fn = self.model.sample_scheduler, velocity_fn
        self.conditions = (cells['condition'], cells['uncondition'])
        self.noise, self.noise_digest = noise, tree_digest(noise)
        self.generator, self.target_update = generator, target_update
        self.logical_cap, self.CPU_cap = logical_copy_cap_bytes, CPU_storage_cap_bytes
        self.CPU_bytes = 0
        self.suffix = official_suffix(runtime / 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
        self.parameters = [(name, value, value._version) for name, value in self.net.named_parameters()]
        self.bindings = (self.net.forward, self.model.denoise, self.scheduler.step)
        self.used, self.records = False, []
        self.parent = self._capture(latent)
        self.parent_digest = self.parent.image.digest

    def _check(self):
        if (self.model.net is not self.net or self.model.sample_scheduler is not self.scheduler
                or (self.net.forward, self.model.denoise, self.scheduler.step) != self.bindings
                or tree_digest(self.noise) != self.noise_digest
                or any(module.training for module in self.net.modules())):
            raise ValueError('Pilot model, installed functions, noise or eval identity changed')
        current = list(self.net.named_parameters())
        if len(current) != len(self.parameters) or any(
                name != old_name or value is not original or value._version != version
                for (name, value), (old_name, original, version) in zip(current, self.parameters)):
            raise ValueError('Frozen model parameters changed')

    def _state(self, latent):
        owner = self.owner
        return dict(
            y=dict(latent=latent, solver=object_state(self.scheduler)),
            cache=dict(net={k: getattr(self.net, k) for k in WC_FIELDS if hasattr(self.net, k)},
                buffers=dict(self.net.named_buffers()),
                readout={k: getattr(owner.readout, k) for k in ('completed', 'history', 'current', 'poisoned')},
                calibrators=[vars(c) for c in owner.readout.calibrators],
                executor={k: getattr(owner.executor, k) for k in ('poisoned', 'running', 'last')},
                owner={k: getattr(owner, k) for k in ('history', 'fallback_reason', 'force_dense')}),
            shared=dict(conditions=[object_state(c) for c in self.conditions],
                        generator=self.generator.get_state()))

    def _capture(self, latent):
        self._check()
        image = CPUOwnedStateImage(self._state(latent), logical_copy_cap_bytes=self.logical_cap,
                                  CPU_storage_cap_bytes=self.CPU_cap - self.CPU_bytes)
        self.CPU_bytes += image.inventory['unique_storage_bytes']
        return _Checkpoint(image, RNGState(), RNGState().signatures())

    @torch.no_grad()
    def _restore(self, write, read=None):
        self._check()
        # The whole ordinary image preserves aliases for 00 and 11. Mixed
        # diagnostic states deliberately take y and cache from different images.
        data = write.image.materialize()
        if read is not None and read is not write:
            other = read.image.materialize()
            if (tree_digest(data['shared']) != tree_digest(other['shared'])
                    or write.rng_signature != read.rng_signature):
                raise ValueError('C/D conditions, RNG or generator transitions differ')
            data['y'] = other['y']
        cache = data['cache']
        for k in set(WC_FIELDS) - set(cache['net']):
            if hasattr(self.net, k):
                delattr(self.net, k)
        for k, value in cache['net'].items():
            setattr(self.net, k, value)
        for name, value in self.net.named_buffers():
            value.copy_(cache['buffers'][name])
        methods = {k: v for k, v in vars(self.scheduler).items() if callable(v)}
        vars(self.scheduler).clear()
        vars(self.scheduler).update(data['y']['solver'])
        vars(self.scheduler).update(methods)
        owner = self.owner
        for k, value in cache['readout'].items():
            setattr(owner.readout, k, value)
        for calibrator, saved in zip(owner.readout.calibrators, cache['calibrators']):
            vars(calibrator).clear()
            vars(calibrator).update(saved)
        for k, value in cache['executor'].items():
            setattr(owner.executor, k, value)
        for k, value in cache['owner'].items():
            setattr(owner, k, value)
        for condition, saved in zip(self.conditions, data['shared']['conditions']):
            for key in set(object_state(condition)) - set(saved):
                object.__delattr__(condition, key)
            for key, value in saved.items():
                object.__setattr__(condition, key, value)
        self.generator.set_state(data['shared']['generator'])
        write.rng.restore()
        self._check()
        return data['y']['latent']

    @torch.no_grad()
    def run(self):
        if self.used:
            raise ValueError('Recover the existing pilot receipt; do not repeat suffixes')
        self.used = True
        current = self.target_update - 1
        post = {}
        try:
            for action in ('C', 'D'):
                latent = self._restore(self.parent)
                self.owner.force_dense = action == 'D'
                t = self.scheduler.timesteps[current]
                try:
                    velocity = self.velocity_fn(self.noise, latent, t.reshape(1, 1))
                    updated = self.scheduler.step(velocity.unsqueeze(0), t, latent.unsqueeze(0),
                        return_dict=False, generator=self.generator)[0].squeeze(0)
                finally:
                    self.owner.force_dense = False
                if (self.owner.history[-1]['actual'] != action
                        or self.owner.history[-1]['fallback_reason'] is not None):
                    raise ValueError('Actual current C/D action differs or used a fallback')
                post[action] = self._capture(updated)
            outputs = {}
            for corner in ('00', '10', '01', '11'):
                read = post['D' if corner[0] == '1' else 'C']
                write = post['D' if corner[1] == '1' else 'C']
                latent = self._restore(write, read)
                record = dict(corner=corner, status='STARTED',
                    current_solver_state_sha256=tree_digest(self._state(latent)['y']),
                    current_cache_state_sha256=tree_digest(plain(self._state(latent)['cache'])),
                    true_D_sources=[c.receipt()['anchor_steps'] for c in self.owner.readout.calibrators],
                    source_sigmas=[[float(self.scheduler.sigmas[t-1]) for t in c.receipt()['anchor_steps']]
                                   for c in self.owner.readout.calibrators],
                    current_D_paid=True, future_updates=36-self.target_update)
                self.records.append(record)
                result = self.suffix(self.model, self.noise, latent, self.velocity_fn,
                                    self.generator, self.scheduler.timesteps[self.target_update:])
                self._check()
                if self.scheduler._step_index != 36 or self.owner.readout.completed != 36:
                    raise ValueError('Incomplete original hard suffix')
                record.update(status='COMPLETE_UNSCORED_SUFFIX',
                    final_latent_sha256=tree_digest(result), final_RNG=RNGState().signatures(),
                    future_actual_actions=[h['actual'] for h in self.owner.history[self.target_update:]])
                outputs[corner] = result.detach().clone()
            return outputs
        except BaseException as error:
            if self.records and self.records[-1]['status'] == 'STARTED':
                self.records[-1].update(status='FAILED', error_type=type(error).__name__, error=str(error))
            raise
        finally:
            latent = self._restore(self.parent)
            if tree_digest(plain(self._state(latent))) != self.parent_digest:
                raise ValueError('Parent complete state failed restoration')
            if RNGState().signatures() != self.parent.rng_signature:
                raise ValueError('Parent RNG failed restoration')
            self.parent_restored = True
