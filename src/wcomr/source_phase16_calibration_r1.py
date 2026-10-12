"""Pre-action natural source/phase calibration; only pi0 continues.

Offline primitive C/A/P/D trials share one complete current state, including
the two natural parent-P points. Candidate actions are not policy decisions.
No shadow candidate changes a deployed anchor or the ordinary UniPC update.
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
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize

VERSION='SOURCE_PHASE16_PRE_ACTION_PI0_CALIBRATION_R1'

class Offline16Controller(CurrentBirthCPDController):
    def __init__(self,*args,registered_steps,**kwargs):
        super().__init__(*args,**kwargs)
        self.registered_steps=tuple(registered_steps);self.offline=None
        if len(set(self.registered_steps))!=4 or any(type(n) is not int or not 8<=n<=35 for n in self.registered_steps):
            raise ValueError('Four preregistered natural nonprotected points required')

    @contextmanager
    def action(self,step,name):
        if self.offline is not None or step not in self.registered_steps or name not in ('C','A','P','D'):
            raise ValueError('One registered offline primitive pair required')
        if self.last_completed_step!=step-1:raise ValueError('Offline action needs pre-action state')
        self.offline=(step,name)
        try:yield
        finally:self.offline=None

    def _choice(self,step,values,ready,partial_ready,protected=False):
        origin=super()._choice(step,values,ready,partial_ready,protected)
        if self.offline is None:return origin
        if self.offline[0]!=step or protected or not ready or origin.local_proxy is None or origin.gain is None:
            raise ValueError('Cannot force through protected/missing/invalid paid source')
        name=self.offline[1];physical='C' if name=='A' else name
        if physical=='P':
            if not partial_ready or self.partial_prior is None or self.costs.P is None or self.consecutive_P>=self.partial_prior.maximum_consecutive_P:
                raise ValueError('Offline P needs actual compatible past projections')
            floor=self.partial_prior.creation_floor_at(step);risk=origin.gain*floor
        elif physical=='C':floor=self.creation_floor;risk=origin.gain*(floor+origin.local_proxy)
        else:floor=risk=0.
        return replace(origin,action=physical,added_risk=risk,predicted_creation_floor=floor,
            reason='MATH_EVENT_CAL16_OFFLINE:'+name)

    def state_dict(self):
        if self.offline is not None:raise ValueError('Active offline pair is not a snapshot boundary')
        return super().state_dict()


class SourcePhase16Owner(MathSamplingOwner):
    def __init__(self,*args,states,config,writer,**kwargs):
        if kwargs.get('horizon') is not None or kwargs.get('source_mode')!='P_OFF':
            raise ValueError('Exact unchanged pi0 P_OFF parent required')
        self.states={s['chosen']['step']:s for s in states}
        if len(self.states)!=4:raise ValueError('Complete four-source/phase request scope required')
        ctor=bind_globals(MathSamplingOwner.__init__,{'CurrentBirthCPDController':
            functools.partial(Offline16Controller,registered_steps=tuple(sorted(self.states)))})
        ctor(self,*args,**kwargs)
        self.config,self.writer=config,writer;self.records=[];self.actual_pair_computations=0
        self.active_velocity=self.active_generator=None

    def installation(self):
        return super().installation()+(VERSION,tuple(sorted(self.states)))

    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1;point=self.states.get(step)
        if point is None:
            self.actual_pair_computations+=1
            return super().pair(noise,latent,timestep,conditions,choose)
        if self.active_velocity is None or self.active_generator is None:
            raise ValueError('Actual RF closure and previous solver generator required')
        before=DiagnosticSnapshot(self,latent,noise,self.active_velocity,self.active_generator,self.config)
        state=self.controller._state();chosen=point['chosen']
        if (state[0]!=chosen['true_D_anchor'] or state[1]!=point['source'] or state[2]!=chosen['source_birth']
                or step-state[2]!=chosen['age'] or ('EARLY' if step<25 else 'LATE')!=point['phase']):
            raise ValueError('Frozen pre-action source/phase/age not reproduced')
        input_sha=tree_digest((noise,latent,timestep));D_sha=tree_digest(plain([vars(c) for c in self.deployment.dense]))
        work_sha=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))
        readout=self.deployment.readout;gamma,mode=readout.gamma,readout.mode
        trial_specs=(('DENSE_SAME_STATE','D',gamma),('C','C',gamma),('D_REFERENCE_A','A',0.),
                     ('FUSION_A','A',gamma),('NEW_P','P',gamma))
        payload={};receipts=[]
        for label,action,gain in trial_specs:
            heads=len(self.head_calls)
            try:
                readout.gamma,readout.mode=gain,'FUSION'
                with self.controller.action(step,action):
                    synchronize();start=time.perf_counter();self.actual_pair_computations+=1
                    output=MathSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
                    synchronize();seconds=time.perf_counter()-start
                h=copy.deepcopy(self.history[-1]);extra=len(self.head_calls)-heads
                if h['action']!=('C' if action=='A' else action)*2 or tree_digest((noise,latent,timestep))!=input_sha:
                    raise ValueError('Actual offline pair or input changed')
                if action!='D' and tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha:
                    raise ValueError('C/A/P wrote a teacher into trusted D history')
                if action in ('C','A') and tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))!=work_sha:
                    raise ValueError('Readout mutated its real working source')
                if action=='P' and (h['source_policy']['creation_floor_proxy_after']<=0
                        or any(s['kind']!='P' or s['created_step']!=step or s['RA_zero_risk_reset_allowed'] for s in h['working_sources'])):
                    raise ValueError('Actual newborn P is not a positive-error working source')
                payload[label]=tuple(v.detach().cpu().clone() for v in output)
                receipts.append({'label':label,'primitive':action,'actual_action':h['action'],
                    'full_pair_research_seconds':seconds,'actual_heads':extra,'history':h})
            finally:
                readout.gamma,readout.mode=gamma,mode
            # Restore completed healthy trials only. A failed pair propagates
            # its original cause; the shared guard forbids poisoned recovery.
            before.restore()
            if self.controller._state()!=state:raise ValueError('Offline pair remained in parent policy')
        if point['source']=='D' and any(not torch.equal(x,y) for x,y in zip(payload['D_REFERENCE_A'],payload['FUSION_A'])):
            raise ValueError('D-source fusion changed identical true-D references')
        payload.update(actual_latent=latent.detach().cpu().clone(),timestep=timestep.detach().cpu().clone())
        artifact=self.writer(step,payload)
        self.actual_pair_computations+=1
        actual=super().pair(noise,latent,timestep,conditions,choose)
        natural=copy.deepcopy(self.history[-1])
        if natural['action']!=chosen['actual_pi0_action']*2:raise ValueError('Original pi0 action not reproduced')
        expected='NEW_P' if natural['action']=='PP' else 'DENSE_SAME_STATE' if natural['action']=='DD' else 'D_REFERENCE_A' if point['source']=='D' else 'C'
        if any(not torch.equal(v.detach().cpu(),w) for v,w in zip(actual,payload[expected])):
            raise ValueError('Restored parent differs from its same-state actual action')
        scheduler=self.model.sample_scheduler;index=scheduler._step_index
        self.records.append({'point':point,'sigma_index':index,'sigma':float(scheduler.sigmas[index]),
            'input_sha256':input_sha,'source_state_sha256':work_sha,'true_D_state_sha256':D_sha,
            'parent_pre_action':state,'parent_continues':natural['action'],'trial_receipts':receipts,
            'restores':before.restores,'complete_gate':before.gate,'artifact':artifact,
            'offline_teacher_or_candidates_committed_to_parent':False,
            'cost_boundary':'FULL_PAIR_BOTH_PROBES_RESEARCH_INSTRUMENTED_NOT_CLEAN_VIDEO_OR_OLD_POST_PROBE_PRICE'})
        return actual


@contextmanager
def calibration16_install(clean,scheduler,states,config,writer,parameters,holder):
    from .clean_speed20_r1 import patched
    original_compile=clean.compile_velocity;old_step=scheduler.step
    def factory(*a,**kw):
        owner=SourcePhase16Owner(*a,states=states,config=config,writer=writer,
            math_parameters=parameters,source_mode='P_OFF',**kw)
        holder['owner']=owner;return owner
    def compile_velocity(runtime,rf,owner,choose):
        fn,proof=original_compile(runtime,rf,owner,choose)
        def bound(model,*a,**kw):
            velocity=fn(model,*a,**kw);owner.active_velocity=velocity;return velocity
        return bound,proof
    def solver_step(*a,**kw):
        owner=holder.get('owner');generator=kw.get('generator')
        if owner is not None:
            if owner.active_generator is not None and owner.active_generator is not generator:
                raise ValueError('Ordinary generator identity changed')
            owner.active_generator=generator
        return old_step(*a,**kw)
    with patched(clean,'CurrentBirthSamplingOwner',factory),patched(clean,'compile_velocity',compile_velocity),patched(scheduler,'step',solver_step):
        yield
