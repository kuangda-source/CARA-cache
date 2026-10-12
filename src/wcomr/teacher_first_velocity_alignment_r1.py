"""Offline same-state teacher velocity, followed by the unchanged pi0 policy.

The teacher pair is restored before either suffix. Both first cache actions
remain physical C; only one returned c/u velocity pair is intervened on.
This diagnostic is not an online action or a cost-free candidate.
"""
import copy
from contextlib import contextmanager
from dataclasses import replace
import time

import torch

from .pi0_readout_suffix8_r1 import FirstReadoutController, Pi0ReadoutSuffixOwner
from .math_n2_sampling_owner_r1 import MathSamplingOwner
from .source_aware_phase_sampling import bind_globals
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .rv0_fork import official_suffix

VERSION = 'SAME_STATE_TEACHER_FIRST_VELOCITY_C_CACHE_TWO_SUFFIXES_R1'
LABELS = {'DEFAULT_PI0': 'C_REPLAY', 'ALTERNATIVE': 'TEACHER_FIRST'}


class TeacherFirstController(FirstReadoutController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offline_teacher = False

    @contextmanager
    def teacher(self):
        if (self.offline_teacher or self.first_readout is not None
                or self.last_completed_step != self.registered_step - 1):
            raise ValueError('One inactive registered teacher prefix required')
        self.offline_teacher = True
        try:
            yield
        finally:
            self.offline_teacher = False

    def _choice(self, step, *args, **kwargs):
        origin = super()._choice(step, *args, **kwargs)
        if not self.offline_teacher:
            return origin
        if (step != self.registered_step or origin.action != 'C'
                or not origin.both_sources_ready or origin.local_proxy is None):
            raise ValueError('Fresh teacher needs the registered natural legal C')
        return replace(origin, action='D', added_risk=0.,
            predicted_creation_floor=0., reason='MATH_EVENT_TEACHER_FIRST_OFFLINE:D')

    def state_dict(self):
        if self.offline_teacher:
            raise ValueError('Active teacher is not a snapshot boundary')
        return super().state_dict()


class TeacherFirstVelocityOwner(Pi0ReadoutSuffixOwner):
    def __init__(self, *args, point, writer, teacher_writer, **kwargs):
        # The ordinary parent stays P_OFF. Both diagnostic suffixes explicitly
        # use plain C on their first step, including D-source points.
        diagnostic_point = copy.deepcopy(point)
        diagnostic_point.update(default_readout='C', alternative_readout='C')
        def endpoint_writer(step, label, tensors):
            branch = self.active_branch
            tensors = dict(tensors, first_C_velocity=branch.pop('_first_C_velocity'))
            return writer(step, LABELS[label], tensors)
        ctor = bind_globals(Pi0ReadoutSuffixOwner.__init__,
            {'FirstReadoutController': TeacherFirstController})
        ctor(self, *args, point=diagnostic_point, writer=endpoint_writer, **kwargs)
        self.original_point = copy.deepcopy(point)
        self.teacher_writer = teacher_writer
        self.teacher_record = None
        self.teacher_velocity = None
        self.teacher_injections = 0

    def installation(self):
        return super().installation() + (VERSION,)

    def ordinary_pair(self, noise, latent, timestep, conditions, choose):
        self.actual_pair_computations += 1
        values = MathSamplingOwner.pair(self, noise, latent, timestep, conditions, choose)
        branch = self.active_branch
        if branch is None:
            return values
        step = len(self.history)
        if step == self.point['chosen']['step']:
            if self.history[-1]['action'] != 'CC' or self.deployment.readout.history[-1]['readout_action'] != 'C':
                raise ValueError('Teacher diagnostic must maintain a real plain-C cache')
            first = tuple(v.detach().cpu().clone() for v in values)
            branch['_first_C_velocity'] = first
            branch['first_C_velocity_sha256'] = tree_digest(first)
            branch['first_C_cache_state_sha256'] = tree_digest((
                self.net.probe_residual_cache, self.net.residual_cache,
                plain(self.deployment.working), plain([vars(d) for d in self.deployment.dense]),
                self.controller._state(), self.controller.creation_floor))
            branch['teacher_velocity_injected'] = branch['label'] == 'ALTERNATIVE'
            if branch['teacher_velocity_injected']:
                if self.teacher_velocity is None or self.teacher_injections:
                    raise ValueError('Exactly one fresh teacher velocity intervention required')
                if any(v.shape != t.shape or v.dtype != t.dtype for v, t in zip(values, self.teacher_velocity)):
                    raise ValueError('Fresh teacher shape/dtype differs from actual C')
                values = tuple(t.to(device=v.device) for v, t in zip(values, self.teacher_velocity))
                self.teacher_injections += 1
            branch['first_returned_velocity_sha256'] = tree_digest(tuple(v.detach().cpu() for v in values))
        branch['guided'].append((values[0] + 7 * (values[0] - values[1])).detach().cpu().clone())
        branch['actions'].append(self.history[-1]['action'])
        branch['readout_actions'].append(self.deployment.readout.history[-1]['readout_action'])
        return values

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history) + 1
        if self.active_branch is not None or step != self.point['chosen']['step']:
            return self.ordinary_pair(noise, latent, timestep, conditions, choose)
        if (self.teacher_record is not None or self.active_velocity is None
                or self.active_generator is None):
            raise ValueError('One fresh teacher at the exact bound prefix required')
        p = self.point; c = p['chosen']; state = self.controller._state()
        if (state != (c['true_D_anchor'], p['source'], c['source_birth'])
                or step-state[2] != c['age'] or self.model.sample_scheduler._step_index != step-1):
            raise ValueError('Frozen teacher prefix source/age/solver not reproduced')
        before = DiagnosticSnapshot(self, latent, noise, self.active_velocity,
            self.active_generator, self.config)
        input_sha = tree_digest((noise, latent, timestep))
        synchronize(); started = time.perf_counter()
        with self.controller.teacher():
            self.actual_pair_computations += 1
            teacher = MathSamplingOwner.pair(self, noise, latent, timestep, conditions, choose)
        synchronize(); seconds = time.perf_counter() - started
        history = copy.deepcopy(self.history[-1])
        if history['action'] != 'DD' or tree_digest((noise, latent, timestep)) != input_sha:
            raise ValueError('Fresh teacher changed its bound input or was not actual D')
        self.teacher_velocity = tuple(v.detach().cpu().clone() for v in teacher)
        # Only a completed healthy teacher may restore. Failed calls propagate.
        before.restore()
        if self.controller._state() != state:
            raise ValueError('Offline teacher remained in ordinary cache state')
        payload = {'teacher_velocity': self.teacher_velocity,
            'actual_latent': latent.detach().cpu().clone(),
            'noise': noise.detach().cpu().clone(), 'timestep': timestep.detach().cpu().clone()}
        self.teacher_record = {'point': self.original_point, 'input_sha256': input_sha,
            'teacher_velocity_sha256': tree_digest(self.teacher_velocity),
            'history': history, 'prefix_physical_sha256': before.physical_sha,
            'prefix_owned_sha256': before.owned.origin,
            'complete_gate': before.gate, 'serial_restores': before.restores,
            'research_teacher_pair_seconds': seconds,
            'artifact': self.teacher_writer(step, payload), 'teacher_committed': False}
        del before, teacher, payload
        actual = super().pair(noise, latent, timestep, conditions, choose)
        event = self.event_records[0]
        if (event['prefix_physical_sha256'] != self.teacher_record['prefix_physical_sha256']
                or event['prefix_owned_sha256'] != self.teacher_record['prefix_owned_sha256']):
            raise ValueError('Teacher restore and two-suffix prefix disagree')
        by = {b['label']: b for b in event['branches']}
        if (self.teacher_injections != 1
                or by['DEFAULT_PI0']['first_C_velocity_sha256'] != by['ALTERNATIVE']['first_C_velocity_sha256']
                or by['DEFAULT_PI0']['first_C_cache_state_sha256'] != by['ALTERNATIVE']['first_C_cache_state_sha256']
                or by['ALTERNATIVE']['first_returned_velocity_sha256'] != self.teacher_record['teacher_velocity_sha256']):
            raise ValueError('First C/cache equivalence or teacher velocity intervention failed')
        for branch in event['branches']:
            branch['internal_label'] = branch['label']; branch['label'] = LABELS[branch['label']]
        event.update(actual_teacher_calls=2, actual_teacher_pairs=1,
            teacher_record=self.teacher_record, only_first_returned_velocity_changed=True,
            physical_first_action='CC', original_pi0_point=self.original_point,
            teacher_committed_to_parent_or_suffix=False)
        return actual


@contextmanager
def teacher_first_alignment_install(clean, scheduler, point, config, writer,
        teacher_writer, parameters, holder, *, runtime, reverse_order=False):
    from .clean_speed20_r1 import patched
    original_compile = clean.compile_velocity; native_step = scheduler.step
    compiled_suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    def factory(*a, **kwargs):
        owner = TeacherFirstVelocityOwner(*a, point=point, config=config,
            writer=writer, teacher_writer=teacher_writer, math_parameters=parameters,
            source_mode='P_OFF', reverse_order=reverse_order, **kwargs)
        owner.suffix = compiled_suffix; owner.native_scheduler_step = native_step
        holder['owner'] = owner
        return owner
    def compile_velocity(runtime, rf, owner, choose):
        fn, proof = original_compile(runtime, rf, owner, choose)
        def bound(model, *a, **kwargs):
            velocity = fn(model, *a, **kwargs); owner.active_velocity = velocity
            return velocity
        return bound, proof
    def solver_step(*a, **kwargs):
        owner = holder.get('owner'); generator = kwargs.get('generator')
        if owner is not None:
            if owner.active_generator is not None and owner.active_generator is not generator:
                raise ValueError('Ordinary generator identity changed')
            owner.active_generator = generator
        return native_step(*a, **kwargs)
    with patched(clean, 'CurrentBirthSamplingOwner', factory), patched(clean, 'compile_velocity', compile_velocity), patched(scheduler, 'step', solver_step):
        yield
