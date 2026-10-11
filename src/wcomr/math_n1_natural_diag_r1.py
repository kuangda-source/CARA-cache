"""Twelve natural same-state comparisons; old unit-A alone continues.

Four real parents are replayed, with no forced P birth or forced C suffix.
The original D-only histories, P state and actual RF/solver remain unchanged.
"""
import copy
from contextlib import contextmanager
from dataclasses import replace
import functools
import time

import torch

from .source_aware_CPU_storage_sampling_r1 import CPUStorageSamplingOwner
from .source_aware_current_birth_sampling_r2 import CurrentBirthSamplingOwner
from .source_aware_current_birth_control_r1 import CurrentBirthCPDController
from .source_aware_phase_sampling import bind_globals
from .p_reference_same_state_owner_r1 import ComparisonReadout
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .cfg_guided_w1_outputs import guided_velocity_moments
from .math_source_fusion_r1 import fuse_outputs
from .light_sampling import synchronize

VERSION='MATH_N1_NATURAL_NONZERO_UNIT_READOUT_R1'


class NaturalTeacherController(CurrentBirthCPDController):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.teacher_step=None

    @contextmanager
    def same_state_teacher(self,step):
        if self.teacher_step is not None or self.last_completed_step!=step-1:
            raise ValueError('Inactive actual natural teacher boundary required')
        self.teacher_step=step
        try:yield
        finally:self.teacher_step=None

    def _choice(self,step,packet_values,ready,partial_ready,protected=False):
        value=super()._choice(step,packet_values,ready,partial_ready,protected)
        if self.teacher_step!=step:return value
        if protected or value.action!='C' or value.reason!='cheapest_feasible_bound_action':
            raise ValueError('Registered natural C point not reproduced; never substitute a point')
        return replace(value,action='D',added_risk=0.,predicted_creation_floor=0.,
                       reason='N1_OFFLINE_SAME_STATE_D_TEACHER')


class NaturalUnitOwner(CPUStorageSamplingOwner):
    def __init__(self,*args,states,config,writer,**kwargs):
        if (kwargs['method']!='A_CPD_BETA1_ONE_PHASE'
                or kwargs['spec']['working_epoch_strategy']!='WORKING_P_AGE_NONZERO_REBASE'):
            raise ValueError('Exact original natural NONZERO phase-unit parent required')
        # Bind the original Dynamic constructor directly; every source/body
        # remains unchanged outside the two registered factory bindings.
        from .source_aware_partial_sampling import DynamicSamplingOwner
        from .source_aware_current_birth_sampling_r2 import CurrentBirthDeployment
        constructor=bind_globals(DynamicSamplingOwner.__init__,{
            'SourceAwareCPDController':functools.partial(NaturalTeacherController,
                strategy=kwargs['spec']['working_epoch_strategy']),
            'SourceAwarePartialDeployment':CurrentBirthDeployment})
        constructor(self,*args,**kwargs)
        old=self.deployment.readout
        new=ComparisonReadout(self.deployment,method=old.method)
        new.warp,new.to_velocity=old.warp,old.to_velocity
        new.reference_variant='D_REFERENCE_UNIT';self.deployment.readout=new
        self.states={s['step']:s for s in states};self.config,self.writer=config,writer
        self.records=[];self.active_velocity=self.active_generator=None
        self.actual_pair_computations=0

    def installation(self):
        return super().installation()+(VERSION,tuple(sorted(self.states)),
                                        self.deployment.readout.reference_variant)

    def check_healthy(self):
        super().check_healthy()
        if self.deployment.readout.reference_variant!='D_REFERENCE_UNIT':
            raise ValueError('Only original unit-A is a restorable parent boundary')

    def _read(self,variant,noise,latent,timestep,conditions,choose):
        r=self.deployment.readout;method,old=r.method,r.reference_variant
        r.method='OFF' if variant=='OFFICIAL_C' else 'BETA1_ONE_PHASE'
        r.reference_variant=variant
        try:
            self.actual_pair_computations+=1
            return CPUStorageSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
        finally:r.method,r.reference_variant=method,old

    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1;point=self.states.get(step)
        if point is None:
            self.actual_pair_computations+=1
            return super().pair(noise,latent,timestep,conditions,choose)
        if self.active_velocity is None or self.active_generator is None:
            raise ValueError('Actual ordinary RF closure and previous solver generator required')
        before=DiagnosticSnapshot(self,latent,noise,self.active_velocity,self.active_generator,self.config)
        inputs=tree_digest((noise,latent,timestep));control=self.controller._state()
        if (control[:3]!=(point['true_D_reference_step'],point['source'],point['working_created_step'])
                or [c.receipt()['anchor_steps'] for c in self.deployment.dense]!=point['true_D_history']):
            raise ValueError('Registered natural source and true-D clocks not reproduced')
        D_state=tree_digest(plain([vars(c) for c in self.deployment.dense]))
        source_state=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))
        teacher_head_begin=len(self.head_calls)
        synchronize();started=time.perf_counter()
        try:
            with self.controller.same_state_teacher(step):
                self.actual_pair_computations+=1
                teacher=CPUStorageSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
            synchronize();teacher_seconds=time.perf_counter()-started
            teacher=tuple(v.detach().cpu().clone() for v in teacher)
            teacher_heads=len(self.head_calls)-teacher_head_begin
        finally:before.restore()
        assert self.controller._state()==control and teacher_heads==2
        variants=('OFFICIAL_C','P_REFERENCE_UNIT','D_REFERENCE_UNIT')
        candidates={};records=[];actual=None
        for i,variant in enumerate(variants):
            heads=len(self.head_calls);synchronize();started=time.perf_counter()
            value=self._read(variant,noise,latent,timestep,conditions,choose)
            synchronize();seconds=time.perf_counter()-started
            h=copy.deepcopy(self.history[-1])
            if (h['action']!='CC' or h['working_sources'][0]['kind']!=point['source']
                    or tree_digest((noise,latent,timestep))!=inputs
                    or D_state!=tree_digest(plain([vars(c) for c in self.deployment.dense]))
                    or source_state!=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))):
                raise ValueError('Same-state candidate changed source/input/D history or natural action')
            candidates[variant]=tuple(v.detach().cpu().clone() for v in value)
            records.append({'variant':variant,'full_pair_seconds':seconds,
                            'actual_head_calls':len(self.head_calls)-heads,
                            'A_readout':h['A_readout']})
            if i!=2:before.restore()
            else:actual=value
        t=time.perf_counter()
        candidates['FUSION_HALF_UNIT']=fuse_outputs(candidates['D_REFERENCE_UNIT'],candidates['P_REFERENCE_UNIT'],.5)
        fusion_seconds=time.perf_counter()-t
        if point['source']=='D' and any(not torch.equal(a,b) for a,b in zip(
                candidates['D_REFERENCE_UNIT'],candidates['P_REFERENCE_UNIT'])):
            raise ValueError('P-reference altered true-D source control')
        payload={**candidates,'DENSE_SAME_STATE':teacher,'actual_latent':latent.detach().cpu().clone(),
                 'timestep':timestep.detach().cpu().clone()}
        artifact=self.writer(step,payload)
        sched=self.model.sample_scheduler;idx=sched._step_index
        result={'point':point,'step':step,'sigma_index':idx,'sigma':float(sched.sigmas[idx]),
                'input_sha256':inputs,'true_D_state_sha256':D_state,'source_state_sha256':source_state,
                'teacher_seconds':teacher_seconds,'teacher_head_calls':teacher_heads,
                'candidate_records':records,'fusion_arithmetic_CPU_seconds':fusion_seconds,
                'artifact':artifact,'serial_restores':before.restores,'complete_gate':before.gate,
                'deployed_variant':'D_REFERENCE_UNIT','teacher_committed_to_parent':False,
                'guided_moments':{name:guided_velocity_moments(scene=point['scene'],
                     state=VERSION+':'+str(step)+':'+name,original=value,proposed=value,dense=teacher)
                     for name,value in candidates.items()}}
        self.records.append(result)
        return actual


@contextmanager
def natural_diagnostic_install(clean,scheduler,states,config,writer,holder):
    """Only this request's factories; preserve every original source byte."""
    from .clean_speed20_r1 import patched
    original_compile=clean.compile_velocity;old_step=scheduler.step
    def factory(*args,**kwargs):
        owner=NaturalUnitOwner(*args,states=states,config=config,writer=writer,**kwargs)
        holder['owner']=owner;return owner
    def compile_velocity(runtime,rf,owner,choose):
        value,proof=original_compile(runtime,rf,owner,choose)
        def bound(model,*args,**kwargs):
            velocity=value(model,*args,**kwargs);owner.active_velocity=velocity;return velocity
        return bound,proof
    def solver_step(*args,**kwargs):
        generator=kwargs.get('generator')
        owner=holder.get('owner')
        if owner is not None:
            if owner.active_generator is not None and generator is not owner.active_generator:
                raise ValueError('Ordinary solver generator identity changed')
            owner.active_generator=generator
        return old_step(*args,**kwargs)
    with patched(clean,'CurrentBirthSamplingOwner',factory),patched(clean,'compile_velocity',compile_velocity),\
         patched(scheduler,'step',solver_step):
        yield
