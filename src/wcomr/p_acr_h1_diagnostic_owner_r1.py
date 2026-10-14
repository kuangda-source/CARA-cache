"""Non-committing PA diagnostics on the unchanged full H1 parent trajectory.

Three same-state CAD trials and shared-prefix Pc/Pu warm/repeated trials are
restored serially. Only the original H1 pair enters ordinary UniPC. This module
does not supply a production GPU command, new source refresh or learned W3.
"""
import copy
from contextlib import contextmanager
from dataclasses import replace
import time

import torch

from .source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller
from .source_phase_absolute_h1_owner_r1 import SourcePhaseH1Owner
from .source_aware_phase_sampling import bind_globals
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .p_acr_readout_r1 import ACRReadoutExecutor
from .p_acr_history_diff_r1 import PastCFGDelta

VERSION='H1_PARENT_PA_NONCOMMITTING_DIAGNOSTICS_R1'


class ProbeH1Controller(SourcePhaseH1Controller):
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw);self.offline=None

    @contextmanager
    def action(self,step,name):
        if (self.offline is not None or name not in ('C','A','D')
                or self.last_completed_step!=step-1):
            raise ValueError('One healthy pre-action CAD diagnostic required')
        self.offline=(step,name)
        try:yield
        finally:self.offline=None

    def _choice(self,step,values,ready,partial_ready,protected=False):
        origin=super()._choice(step,values,ready,partial_ready,protected)
        if self.offline is None:return origin
        if (self.offline[0]!=step or protected or not ready
                or origin.local_proxy is None or origin.gain is None):
            raise ValueError('Diagnostics cannot force through protected/missing support')
        name=self.offline[1];physical='C' if name=='A' else name
        floor=0. if name=='D' else self.creation_floor
        added=0. if name=='D' else origin.gain*(floor+origin.local_proxy)
        return replace(origin,action=physical,added_risk=added,predicted_creation_floor=floor,
            reason='MATH_EVENT_PA_OFFLINE:'+name)

    def state_dict(self):
        if self.offline is not None:raise ValueError('No snapshot during an incomplete offline action')
        return super().state_dict()


class PADiagnosticOwner(SourcePhaseH1Owner):
    def __init__(self,*args,states,diagnostics_enabled,diagnostic_config,writer,coefficients,**kw):
        if (type(diagnostics_enabled) is not bool or len(states)!=3
                or len({s['step'] for s in states})!=3
                or any(not 8<=s['step']<=34 for s in states)):
            raise ValueError('All three preselected per-parent PA states required')
        self._acr_runtime,self._acr_wc,self._acr_rf=kw['runtime'],kw['wc'],kw['rf']
        self.past_delta=None
        constructor=bind_globals(SourcePhaseH1Owner.__init__,{'SourcePhaseH1Controller':ProbeH1Controller})
        constructor(self,*args,**kw)
        self.states={s['step']:copy.deepcopy(s) for s in states}
        self.diagnostics_enabled=diagnostics_enabled;self.diagnostic_config=diagnostic_config
        self.writer,self.coefficients=writer,copy.deepcopy(coefficients)
        self.records=[];self.actual_pair_computations=0
        self.active_velocity=self.active_generator=None

    def installation(self):
        return super().installation()+(VERSION,tuple(sorted(self.states)),self.coefficients['fingerprint'],self.diagnostics_enabled)

    def own_state(self):
        value=super().own_state();value['PA_past_actual_DD_difference']=self.past_delta;return value

    def restore_own_state(self,value):
        super().restore_own_state({k:v for k,v in value.items() if k!='PA_past_actual_DD_difference'})
        self.past_delta=value['PA_past_actual_DD_difference']

    def _observe_ordinary_pair(self,step,value):
        action=self.history[-1]['action']
        if self.net.cnt==0:self.past_delta=None
        elif action=='DD':
            self.past_delta=PastCFGDelta.from_actual_DD(context=self.context,step=step,pair=value,
                semantic_action=action,diagnostic_only=False)
        return value

    def _check_preselected(self,step,point,state):
        if (point.get('expected_source') is not None and state[1]!=point['expected_source']
                or point.get('expected_source_birth') is not None and state[2]!=point['expected_source_birth']
                or point.get('expected_source_age') is not None and step-state[2]!=point['expected_source_age']):
            raise ValueError('Preselected actual H1 state/source clock differs; do not substitute')

    def _poison_parent(self):
        self.base.poisoned=self.controller.poisoned=self.deployment.poisoned=True

    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1;point=self.states.get(step)
        if point is None or not self.diagnostics_enabled:
            self.actual_pair_computations+=1
            return self._observe_ordinary_pair(step,super().pair(noise,latent,timestep,conditions,choose))
        if self.active_velocity is None or self.active_generator is None:
            raise ValueError('Actual original RF closure/generator needed for complete snapshot')
        state=self.controller._state();self._check_preselected(step,point,state)
        snapshot=DiagnosticSnapshot(self,latent,noise,self.active_velocity,self.active_generator,self.diagnostic_config)
        physical_before=snapshot.physical_sha;owned_before=snapshot.owned.origin
        input_sha=tree_digest((noise,latent,timestep));D_sha=tree_digest(plain([vars(c) for c in self.deployment.dense]))
        work_sha=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))
        payload={};trials=[]
        try:
            for name in ('C','A','D'):
                start_heads=len(self.head_calls)
                with self.controller.action(step,name):
                    synchronize();start=time.perf_counter();self.actual_pair_computations+=1
                    value=SourcePhaseH1Owner.pair(self,noise,latent,timestep,conditions,choose)
                    synchronize();elapsed=time.perf_counter()-start
                history=copy.deepcopy(self.history[-1])
                if name!='D' and tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha:
                    raise ValueError('CAD readout modified actual true-D bank')
                if name in ('C','A') and tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))!=work_sha:
                    raise ValueError('CAD readout modified its working source')
                payload[name]=tuple(v.detach().cpu().clone() for v in value)
                trials.append({'kind':name,'section':'LOCAL_REFERENCE','full_pair_seconds':elapsed,
                    'actual_heads':len(self.head_calls)-start_heads,'actual_action':history['action'],
                    'actual_readout':history['A_readout']['readout_action']})
                snapshot.restore()
            cell=state[1]+('_EARLY' if step<25 else '_LATE')
            gains=self.coefficients['cells'][cell]
            for direction in ('Pc','Pu'):
                coefficient=gains['Pc_eta' if direction=='Pc' else 'Pu_zeta']
                for repetition in range(4):  # one complete warmup plus three formal trials
                    self.step=step  # Algorithm-independent actual head/Linear observers use this step.
                    start_heads=len(self.head_calls)
                    executor=ACRReadoutExecutor(self.model,runtime=self._acr_runtime,wc=self._acr_wc,rf=self._acr_rf,
                        context=self.context,dense=self.deployment.dense,working=self.deployment.working,
                        gamma=self.controller.table_parameters['gamma'],direction=direction,coefficient=coefficient,
                        step=step,projection_readonly=self.deployment.core.readonly)
                    synchronize();start=time.perf_counter();self.actual_pair_computations+=1
                    output,base_A,one_D=executor.execute(noise,latent,timestep,conditions)
                    synchronize();elapsed=time.perf_counter()-start
                    actual_heads=len(self.head_calls)-start_heads
                    side=0 if direction=='Pc' else 1
                    if (any(not torch.equal(a.detach().cpu(),b) for a,b in zip(base_A,payload['A']))
                            or not torch.equal(one_D.detach().cpu(),payload['D'][side])):
                        raise ValueError('Asymmetric actual A or single D differs at the identical H1 state')
                    if (tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha
                            or tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))!=work_sha):
                        raise ValueError('ACR updated true-D/working source during diagnostics')
                    key=direction+'_REP'+str(repetition)
                    payload[key]=tuple(v.detach().cpu().clone() for v in output)
                    if self.past_delta is None:raise ValueError('Full PA comparison requires a strictly-past real DD difference')
                    history_value=self.past_delta.readout(one_D,context=self.context,step=step,direction=direction)
                    payload['FC_STYLE_'+key]=tuple(v.detach().cpu().clone() for v in history_value)
                    trials.append({'kind':direction,'section':'WARMUP' if repetition==0 else 'TIMED','repetition':repetition,
                        'coefficient':coefficient,'full_pair_seconds':elapsed,'actual_heads':actual_heads,
                        'actual_dense_branches':1,'paid_prefixes':2,'source_refresh':False})
                    snapshot.restore()
            if (self.controller._state()!=state or self.fingerprint()!=owned_before
                    or snapshot.physical.fingerprint()!=physical_before or tree_digest((noise,latent,timestep))!=input_sha):
                raise ValueError('Complete H1 parent state was not restored after all11 trials')
        except BaseException:
            self._poison_parent();raise
        payload.update(actual_latent=latent.detach().cpu().clone(),timestep=timestep.detach().cpu().clone())
        artifact=self.writer(step,payload)
        self.actual_pair_computations+=1
        actual=super().pair(noise,latent,timestep,conditions,choose)
        natural=copy.deepcopy(self.history[-1]);semantic=natural['A_readout']['readout_action']
        if semantic in ('C','A','D') and any(not torch.equal(v.detach().cpu(),w) for v,w in zip(actual,payload[semantic])):
            raise ValueError('Ordinary restored H1 parent differs from same-state actual CAD action')
        if point.get('expected_H1_readout') is not None and semantic!=point['expected_H1_readout']:
            raise ValueError('Preselected H1 action changed; no alternative state is substituted')
        sch=self.model.sample_scheduler;index=sch._step_index
        self.records.append({'point':point,'parent_pre_action':state,'input_sha256':input_sha,
            'source_state_sha256':work_sha,'true_D_state_sha256':D_sha,
            'sigma_index':index,'sigma':float(sch.sigmas[index]),'parent_action':natural['action'],
            'parent_readout':semantic,'complete_gate':snapshot.gate,'serial_restores':snapshot.restores,
            'trials':trials,'artifact':artifact,'all11_trials_restored':True,
            'candidate_or_teacher_committed_to_parent':False,'coefficients_fingerprint':self.coefficients['fingerprint'],
            'timing_scope':'FULL_PAIR_PROBES_A_HEADS_SINGLE_D_RF_COMPENSATION_NOT_CLEAN_VIDEO_LATENCY'})
        return self._observe_ordinary_pair(step,actual)


@contextmanager
def install_pa_diagnostics(clean,batch,scheduler,*,states,config,writer,coefficients,holder):
    """Keep original full inference/velocity/UniPC body, bind only new owner."""
    from .clean_speed20_r1 import patched
    original_compile=clean.compile_velocity;original_step=scheduler.step
    def factory(*a,**kw):
        owner=PADiagnosticOwner(*a,states=states,diagnostics_enabled=True,diagnostic_config=config,
            writer=writer,coefficients=coefficients,**kw)
        holder['owner']=owner;return owner
    def compile_velocity(runtime,rf,owner,choose):
        fn,proof=original_compile(runtime,rf,owner,choose)
        def bound(model,*a,**kw):
            velocity=fn(model,*a,**kw);owner.active_velocity=velocity;return velocity
        return bound,proof
    def solver_step(*a,**kw):
        owner=holder.get('owner');generator=kw.get('generator')
        if owner is not None:
            if owner.active_generator is not None and owner.active_generator is not generator:raise ValueError('Original solver generator identity changed')
            owner.active_generator=generator
        return original_step(*a,**kw)
    with patched(batch,'SourcePhaseH1Owner',factory),patched(clean,'compile_velocity',compile_velocity),patched(scheduler,'step',solver_step):
        yield
