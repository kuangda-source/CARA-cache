"""Three saved-velocity suffixes with the SAME first physical plain-C state.

This is an offline endpoint diagnostic, not a B refresh or online accelerator.
Exactly bound, previously paid D/B outputs are reused; no current teacher is
computed, no B result enters a trusted anchor, and the original parent resumes.
"""
import copy
import time
from contextlib import contextmanager

import torch

from .pi0_readout_suffix8_r1 import Pi0ReadoutSuffixOwner
from .math_n2_sampling_owner_r1 import MathSamplingOwner
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .rv0_fork import official_suffix

VERSION = 'SAVED_SAME_STATE_B_DENSE_L2_THREE_VELOCITIES_C_STATE_R1'
LABELS = ('C_REPLAY', 'DENSE_VELOCITY', 'L2_VELOCITY')


class BlockVelocitySuffixOwner(Pi0ReadoutSuffixOwner):
    def __init__(self, *args, point, reference, writer, **kwargs):
        original = copy.deepcopy(point)
        point = dict(point, default_readout='C', alternative_readout='C')
        if reference['scene'] != original['scene'] or reference['step'] != original['chosen']['step']:
            raise ValueError('Exact saved B point identity required')
        if set(reference['vectors']) != {'DENSE_VELOCITY', 'L2_VELOCITY'}:
            raise ValueError('One Dense and one frozen L2 saved pair required')
        for values in reference['vectors'].values():
            if (not isinstance(values, tuple) or len(values) != 2
                    or any(not isinstance(t, torch.Tensor) or t.device.type != 'cpu'
                           or t.requires_grad or t.ndim != 5 or t.shape[0] != 1
                           or t.dtype not in (torch.float32, torch.float16, torch.bfloat16)
                           or not torch.isfinite(t).all() for t in values)):
                raise ValueError('Read-only finite CPU saved c/u vectors required')
        super().__init__(*args, point=point, writer=writer, **kwargs)
        self.original_point = original; self.reference = reference
        self.vector_hashes = {k: tree_digest(v) for k, v in reference['vectors'].items()}
        self.injections = {label: 0 for label in LABELS}

    def installation(self):
        return super().installation() + (VERSION, tuple(sorted(self.vector_hashes.items())))

    def ordinary_pair(self, noise, latent, timestep, conditions, choose):
        self.actual_pair_computations += 1
        values = MathSamplingOwner.pair(self, noise, latent, timestep, conditions, choose)
        branch = self.active_branch
        if branch is None:
            return values
        step = len(self.history)
        if step == self.point['chosen']['step']:
            if self.history[-1]['action'] != 'CC' or self.deployment.readout.history[-1]['readout_action'] != 'C':
                raise ValueError('All saved-velocity arms keep actual plain C on the first step')
            first = tuple(v.detach().cpu().clone() for v in values)
            branch['_first_C_velocity'] = first
            branch['first_C_velocity_sha256'] = tree_digest(first)
            branch['first_C_cache_state_sha256'] = tree_digest((
                self.net.probe_residual_cache, self.net.residual_cache,
                plain(self.deployment.working), plain([vars(d) for d in self.deployment.dense]),
                self.controller._state(), self.controller.creation_floor))
            label = branch['label']
            if label != 'C_REPLAY':
                saved = self.reference['vectors'][label]
                if (self.injections[label] or tree_digest(saved) != self.vector_hashes[label]
                        or any(v.shape != t.shape or v.dtype != t.dtype for v, t in zip(values, saved))):
                    raise ValueError('One unchanged saved c/u pair with matching shape/dtype required')
                values = tuple(t.to(device=v.device) for v, t in zip(values, saved))
                self.injections[label] += 1
            branch['first_returned_velocity_sha256'] = tree_digest(tuple(v.detach().cpu() for v in values))
        branch['guided'].append((values[0]+7*(values[0]-values[1])).detach().cpu().clone())
        branch['actions'].append(self.history[-1]['action'])
        branch['readout_actions'].append(self.deployment.readout.history[-1]['readout_action'])
        return values

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history)+1
        if self.active_branch is not None or step != self.point['chosen']['step']:
            return self.ordinary_pair(noise, latent, timestep, conditions, choose)
        if self.event_records or self.active_velocity is None or self.active_generator is None or self.suffix is None:
            raise ValueError('One complete inactive bound B prefix required')
        p=self.point; c=p['chosen']; state=self.controller._state(); scheduler=self.model.sample_scheduler
        if (state[:3] != (c['true_D_anchor'],p['source'],c['source_birth'])
                or step-state[2] != c['age'] or scheduler._step_index != step-1):
            raise ValueError('Exact B source, age, anchor and solver prefix required')
        hashes = dict(input_sha256=tree_digest((noise,latent,timestep)),
            source_state_sha256=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache)),
            true_D_state_sha256=tree_digest(plain([vars(d) for d in self.deployment.dense])))
        if any(hashes[k] != self.reference[k] for k in hashes):
            raise ValueError('Saved B outputs are from a different actual prefix')
        before=DiagnosticSnapshot(self,latent,noise,self.active_velocity,self.active_generator,self.config)
        event=dict(point=self.original_point,branches=[],status='RUNNING',complete_gate=before.gate,
            prefix_physical_sha256=before.physical_sha,prefix_owned_sha256=before.owned.origin,**hashes)
        self.event_records.append(event)
        from .clean_speed20_r1 import patched
        labels=LABELS[::-1] if self.reverse_order else LABELS
        for label in labels:
            origin=before.restore()
            branch=dict(label=label,first_readout='C',guided=[],actions=[],readout_actions=[],status='RUNNING')
            event['branches'].append(branch);self.active_branch=branch
            try:
                with self.controller.first('C'),patched(scheduler,'step',self.native_scheduler_step):
                    synchronize();start=time.perf_counter()
                    final=self.suffix(self.model,noise,origin,self.active_velocity,self.active_generator,scheduler.timesteps[step-1:])
                    synchronize();branch['instrumented_suffix_sampling_seconds']=time.perf_counter()-start
                if (scheduler._step_index != 36 or len(self.history) != 36
                        or len(branch['guided']) != 37-step or branch['actions'][0] != 'CC'
                        or branch['readout_actions'][0] != 'C'
                        or any(h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in self.history[step:])):
                    raise ValueError('Exactly one changed returned velocity and full ordinary tail required')
                branch['source_policy_tail']=copy.deepcopy(self.history[step-1:])
                tensors=dict(final_latent=final.detach().cpu().clone(),guided=branch.pop('guided'),
                             first_C_velocity=branch.pop('_first_C_velocity'))
                branch['artifact']=self.writer(step,label,tensors)
                branch['final_latent_sha256']=tree_digest(tensors['final_latent'])
                branch['guided_sha256']=[tree_digest(v) for v in tensors['guided']]
                branch['status']='COMPLETE_SAVED_VELOCITY_SUFFIX_RAW_ENDPOINT_PENDING'
            finally:
                self.active_branch=None
            # A failed branch propagates; never recover failed work into parent.
            before.restore()
        by={b['label']:b for b in event['branches']}
        if (set(by) != set(LABELS) or self.injections != dict(C_REPLAY=0,DENSE_VELOCITY=1,L2_VELOCITY=1)
                or len({b['first_C_cache_state_sha256'] for b in by.values()}) != 1
                or len({b['first_C_velocity_sha256'] for b in by.values()}) != 1
                or any(by[k]['first_returned_velocity_sha256'] != v for k,v in self.vector_hashes.items())):
            raise ValueError('First caches differ or saved intervention did not execute exactly once')
        event.update(status='COMPLETE_THREE_SUFFIXES_PARENT_ENDPOINT_PENDING',serial_restores=before.restores,
            actual_teacher_calls=0,actual_B_executor_calls=0,first_physical_action='CC',
            only_first_returned_velocity_changed=True,offline_saved_vectors_not_new_D_or_P_anchor=True)
        actual=self.ordinary_pair(noise,latent,timestep,conditions,choose)
        if self.history[-1]['action'] != 'CC':raise ValueError('Restored original B parent is not natural C')
        return actual


@contextmanager
def block_velocity_suffix_install(clean,scheduler,point,reference,config,writer,parameters,holder,*,runtime,reverse_order=False):
    from .clean_speed20_r1 import patched
    original_compile=clean.compile_velocity; native_step=scheduler.step
    suffix=official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    def factory(*args,**kwargs):
        owner=BlockVelocitySuffixOwner(*args,point=point,reference=reference,config=config,
            writer=writer,math_parameters=parameters,source_mode='P_OFF',reverse_order=reverse_order,**kwargs)
        owner.suffix=suffix;owner.native_scheduler_step=native_step;holder['owner']=owner;return owner
    def compile_velocity(runtime,rf,owner,choose):
        fn,proof=original_compile(runtime,rf,owner,choose)
        def bound(model,*args,**kwargs):
            velocity=fn(model,*args,**kwargs);owner.active_velocity=velocity;return velocity
        return bound,proof
    def solver_step(*args,**kwargs):
        owner=holder.get('owner');generator=kwargs.get('generator')
        if owner is not None:
            if owner.active_generator is not None and owner.active_generator is not generator:
                raise ValueError('Original generator identity changed')
            owner.active_generator=generator
        return native_step(*args,**kwargs)
    with patched(clean,'CurrentBirthSamplingOwner',factory),patched(clean,'compile_velocity',compile_velocity),patched(scheduler,'step',solver_step):
        yield
