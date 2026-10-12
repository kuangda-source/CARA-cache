"""One natural C/A readout intervention, then the unchanged pi0 policy.

The two endpoint suffixes are not a new online controller or free search.
Only healthy completed branches restore. The parent continues unchanged.
"""
import copy
from contextlib import contextmanager
from dataclasses import replace
import functools
import time

import torch

from .math_n2_sampling_owner_r1 import MathSamplingOwner
from .source_aware_current_birth_control_r1 import CurrentBirthCPDController
from .source_aware_phase_sampling import bind_globals
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .rv0_fork import official_suffix
from .light_sampling import synchronize
from .mid_coverage import tree_digest

VERSION='PI0_NATURAL_ONE_READOUT_TWO_FULL_SUFFIXES_R1'


class FirstReadoutController(CurrentBirthCPDController):
    def __init__(self,*args,registered_step,**kw):
        if type(registered_step) is not int or not 8<=registered_step<=35:
            raise ValueError('One registered natural nonprotected C point required')
        super().__init__(*args,**kw);self.registered_step=registered_step;self.first_readout=None

    @contextmanager
    def first(self,readout):
        if (readout not in ('C','A') or self.first_readout is not None
                or self.last_completed_step!=self.registered_step-1):
            raise ValueError('Inactive exact prefix for one C/A intervention required')
        self.first_readout=readout
        try:yield
        finally:self.first_readout=None

    def _choice(self,step,*args,**kw):
        value=super()._choice(step,*args,**kw)
        if self.first_readout is None or step!=self.registered_step:return value
        if value.action!='C' or not value.both_sources_ready or value.local_proxy is None:
            raise ValueError('Registered pi0 point ceased being a natural legal C')
        # Preserve actual C, feasible actions, costs, score and state commit.
        # The source readout already interprets MATH_EVENT_...:C/A selection.
        return replace(value,reason='MATH_EVENT_SUFFIX_FIRST:'+self.first_readout)

    def state_dict(self):
        if self.first_readout is not None:raise ValueError('Active intervention is not a snapshot boundary')
        return super().state_dict()


class Pi0ReadoutSuffixOwner(MathSamplingOwner):
    def __init__(self,*args,point,config,writer,reverse_order=False,**kw):
        if kw.get('horizon') is not None or kw.get('source_mode')!='P_OFF':
            raise ValueError('Unchanged exact pi0 parent required')
        ctor=bind_globals(MathSamplingOwner.__init__,{'CurrentBirthCPDController':
            functools.partial(FirstReadoutController,registered_step=point['chosen']['step'])})
        ctor(self,*args,**kw)
        self.point,self.config,self.writer=point,config,writer;self.reverse_order=reverse_order
        self.active_branch=None;self.active_velocity=self.active_generator=None
        self.suffix=official_suffix(self.runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py') if hasattr(self,'runtime') else None
        self.native_scheduler_step=None;self.event_records=[];self.actual_pair_computations=0

    def installation(self):
        return super().installation()+(VERSION,self.point['chosen']['step'],self.point['source'])

    def ordinary_pair(self,noise,latent,timestep,conditions,choose):
        self.actual_pair_computations+=1
        value=MathSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
        if self.active_branch is not None:
            b=self.active_branch;b['guided'].append((value[0]+7*(value[0]-value[1])).detach().cpu().clone())
            b['actions'].append(self.history[-1]['action'])
            b['readout_actions'].append(self.deployment.readout.history[-1]['readout_action'])
        return value

    @torch.no_grad()
    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1
        if self.active_branch is not None or step!=self.point['chosen']['step']:
            return self.ordinary_pair(noise,latent,timestep,conditions,choose)
        if self.event_records or self.active_velocity is None or self.active_generator is None or self.suffix is None or self.native_scheduler_step is None:
            raise ValueError('One exact source-derived complete suffix binding required')
        state=self.controller._state();p=self.point;c=p['chosen'];scheduler=self.model.sample_scheduler
        if (state[0]!=c['true_D_anchor'] or state[1]!=p['source'] or state[2]!=c['source_birth']
                or step-state[2]!=c['age'] or scheduler._step_index!=step-1):
            raise ValueError('Frozen natural prefix source/age/solver not reproduced')
        before=DiagnosticSnapshot(self,latent,noise,self.active_velocity,self.active_generator,self.config)
        event={'point':p,'branches':[],'complete_gate':before.gate,'prefix_physical_sha256':before.physical_sha,
            'prefix_owned_sha256':before.owned.origin,'status':'RUNNING'}
        self.event_records.append(event)
        labels=('ALTERNATIVE','DEFAULT_PI0') if self.reverse_order else ('DEFAULT_PI0','ALTERNATIVE')
        from .clean_speed20_r1 import patched
        for label in labels:
            origin=before.restore();readout=p['default_readout'] if label=='DEFAULT_PI0' else p['alternative_readout']
            branch={'label':label,'first_readout':readout,'guided':[],'actions':[],'readout_actions':[],'status':'RUNNING'}
            event['branches'].append(branch);self.active_branch=branch
            try:
                with self.controller.first(readout),patched(scheduler,'step',self.native_scheduler_step):
                    synchronize();start=time.perf_counter()
                    final=self.suffix(self.model,noise,origin,self.active_velocity,self.active_generator,scheduler.timesteps[step-1:])
                    synchronize();branch['instrumented_suffix_sampling_seconds']=time.perf_counter()-start
                if (scheduler._step_index!=36 or len(self.history)!=36 or len(branch['guided'])!=37-step
                        or branch['actions'][0]!='CC' or branch['readout_actions'][0]!=readout
                        or any(h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in self.history[step:])):
                    raise ValueError('One first readout plus complete ordinary pi0 tail required')
                branch['source_policy_tail']=copy.deepcopy(self.history[step-1:])
                final_cpu=final.detach().cpu().clone()
                branch['artifact']=self.writer(step,label,{'final_latent':final_cpu,'guided':branch['guided']})
                branch['final_latent_sha256']=tree_digest(final_cpu)
                branch['guided_sha256']=[tree_digest(v) for v in branch.pop('guided')]
                branch['status']='COMPLETE_ENDPOINT_SUFFIX_RAW_AND_VIDEO_AUDIT_PENDING'
            finally:self.active_branch=None
            # A failed suffix propagates; do not recover it into a parent.
            before.restore()
        event.update(status='COMPLETE_TWO_SUFFIXES_PARENT_ENDPOINT_PENDING',serial_restores=before.restores,
            actual_teacher_calls=0,one_step_readout_only=True)
        actual=self.ordinary_pair(noise,latent,timestep,conditions,choose)
        if self.history[-1]['action']!='CC':raise ValueError('Restored parent is not original natural C')
        return actual


@contextmanager
def pi0_readout_suffix_install(clean,scheduler,point,config,writer,parameters,holder,*,runtime,reverse_order=False):
    from .clean_speed20_r1 import patched
    original_compile=clean.compile_velocity;native_step=scheduler.step
    compiled_suffix=official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    def factory(*a,**kw):
        o=Pi0ReadoutSuffixOwner(*a,point=point,config=config,writer=writer,
            math_parameters=parameters,source_mode='P_OFF',reverse_order=reverse_order,**kw)
        o.suffix=compiled_suffix;o.native_scheduler_step=native_step;holder['owner']=o;return o
    def compile_velocity(runtime,rf,owner,choose):
        fn,proof=original_compile(runtime,rf,owner,choose)
        def bound(model,*a,**kw):
            velocity=fn(model,*a,**kw);owner.active_velocity=velocity;return velocity
        return bound,proof
    def solver_step(*a,**kw):
        owner=holder.get('owner');generator=kw.get('generator')
        if owner is not None:
            if owner.active_generator is not None and owner.active_generator is not generator:raise ValueError('Ordinary generator identity changed')
            owner.active_generator=generator
        return native_step(*a,**kw)
    with patched(clean,'CurrentBirthSamplingOwner',factory),patched(clean,'compile_velocity',compile_velocity),patched(scheduler,'step',solver_step):
        yield
