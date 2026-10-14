"""Isolated CAD teacher collection on the unchanged ordinary H1 trajectory.

Only ordinary pairs advance causal observations. Every extra CAD pair is
serially restored; unsupported planned points remain UNKNOWN, never replaced.
No P-ACR execution, estimator fit, source refresh or GPU launch is provided.
"""
import copy
from contextlib import contextmanager
from dataclasses import asdict,replace
import time

import torch

from .source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller
from .source_phase_absolute_h1_owner_r1 import SourcePhaseH1Owner
from .source_aware_phase_sampling import bind_globals
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .cfg_guided_w1_outputs import guided_velocity_moments
from .w3_causal_trend_r1 import CausalHistory,Observation,SameStateLabel
from .calibration import ResidualCalibrator

VERSION='W3_LABEL64_NONCOMMITTING_ORDINARY_H1_HISTORY_R1'
STEPS=(10,16,23,25,29,30,32,35)


def reset_dense_signature(context,parameters):
    banks=[]
    for values in parameters:
        c=ResidualCalibrator(**values);c.reset(context);banks.append(vars(c))
    return tree_digest(plain(banks))


def exact_native_cycle_close(owner,step,history,pre_epoch,reset_dense_sha,last_output_sha):
    """Accept only the unchanged WC 70-call clear, never a new source write."""
    net=owner.net;d=owner.deployment
    if (step!=35 or int(net.cnt)!=0 or history.get('native_cycle_reset') is not True
            or d.epoch!=pre_epoch+1 or d.working!=[None,None] or d.core.cache
            or tree_digest(plain([vars(c) for c in d.dense]))!=reset_dense_sha):return False
    if history['action']=='CC' and tuple(owner.controller._state()[:4])!=tuple(history['joint_decision']['state_before'][:4]):
        return False
    if any(getattr(net,n)!=[None,None] for n in ('residual_cache','probe_residual_cache',
            'previous_internal_states','previous_input')):return False
    # Pinned WC clears both outputs at call70, then stores the just-returned
    # unconditional network output. Match that exact actual output, not merely
    # a nonempty tensor or a generally allowed mutation at step35.
    if (net.previous_output[0] is not None or not torch.is_tensor(net.previous_output[1])
            or last_output_sha is None or tree_digest(net.previous_output[1])!=last_output_sha):return False
    return (net.residual_window==[[],[]] and net.probe_residual_window==[[],[]]
        and net.accumulated_rel_l1_distance==[0.,0.] and net.resume_flag==[False,False]
        and net.worldcache_step_skipped_count==0)


class LabelH1Controller(SourcePhaseH1Controller):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.offline=None

    @contextmanager
    def action(self,step,name):
        if self.offline is not None or name not in ('C','A','D') or self.last_completed_step!=step-1:
            raise ValueError('One complete pre-action W3 CAD diagnostic required')
        self.offline=(step,name)
        try:yield
        finally:self.offline=None

    def _choice(self,step,values,ready,partial_ready,protected=False):
        origin=super()._choice(step,values,ready,partial_ready,protected)
        if self.offline is None:return origin
        if (self.offline[0]!=step or protected or not ready or origin.local_proxy is None
                or origin.gain is None or not origin.reason.startswith('MATH_EVENT_TABLE_ABSOLUTE_H1:')):
            raise ValueError('Cannot force W3 diagnostics through original missing/protected support')
        name=self.offline[1];floor=0. if name=='D' else self.creation_floor
        added=0. if name=='D' else origin.gain*(floor+origin.local_proxy)
        return replace(origin,action='C' if name=='A' else name,added_risk=added,
            predicted_creation_floor=floor,reason='MATH_EVENT_W3_LABEL_OFFLINE:'+name)

    def state_dict(self):
        if self.offline is not None:raise ValueError('No snapshot of incomplete label action')
        return super().state_dict()


class W3LabelOwner(SourcePhaseH1Owner):
    def __init__(self,*args,diagnostic_config,writer,label_provenance,**kwargs):
        if label_provenance not in ('REAL_SAME_STATE_POST_RF','SYNTHETIC_CPU_INTERFACE'):
            raise ValueError('Explicit actual or declared synthetic label provenance required')
        constructor=bind_globals(SourcePhaseH1Owner.__init__,{'SourcePhaseH1Controller':LabelH1Controller})
        constructor(self,*args,**kwargs)
        self.diagnostic_config,self.writer=diagnostic_config,writer
        self.label_provenance=label_provenance;self.records=[];self.feature_rows=[]
        self.causal=CausalHistory(self.context[0],0,window=4)
        self.active_velocity=self.active_generator=None;self.actual_pair_computations=0

    def installation(self):
        return super().installation()+(VERSION,STEPS,self.label_provenance)

    def _preflight(self,step):
        if step<=7 or step==36:return 'ORIGINAL_PROTECTED'
        c=self.controller;d=self.deployment;state=c._state()
        if c.anchor is None or state[1] not in ('D','P') or state[2] is None:return 'NO_ORIGINAL_SOURCE'
        if not 1<=step-state[2]<=6:return 'ORIGINAL_AGE_SUPPORT'
        if (c.anchor,step) not in c.calibration.rho_at or step not in c.calibration.gains:return 'ORIGINAL_CALIBRATION_MISSING'
        source=state[1];group=c.table_parameters['table_model']['grouping'];key=source+('_EARLY' if step<25 else '_LATE') if group=='SOURCE_PHASE' else source
        if c.table_parameters['table_model']['cells'].get(key,{}).get('status')!='FIT':return 'ORIGINAL_TABLE_UNKNOWN'
        ready=all(v is not None and v['epoch']==d.epoch for v in d.working)
        ready=ready and all(getattr(self.net,f)[b] is not None for f in ('previous_input','previous_internal_states','residual_cache') for b in (0,1))
        if not ready:return 'ORIGINAL_BOTH_SOURCES_NOT_READY'
        return None

    def _ordinary_observation(self,step,input_sha,pre_state):
        h=self.history[-1];choice=self.controller.history[-1];packets=choice.packets
        paid=len(packets)==2
        if packets and (not paid or tuple(v[:2] for v in packets)!=((0,2*(step-1)%70),(1,2*(step-1)%70+1))):
            raise ValueError('Ordinary paid pair counter identity changed')
        scheduler=self.model.sample_scheduler;raw_index=scheduler._step_index
        # UniPC initializes the first index in step(), after the first RF call.
        index=0 if step==1 and raw_index is None else raw_index
        if index!=step-1 or len(scheduler.sigmas)!=37:raise ValueError('Actual ordinary36 sigma index required')
        if choice.state_before!=pre_state:raise ValueError('Causal observation does not describe parent pre-action source')
        source=pre_state[1];supported=choice.reason.startswith('MATH_EVENT_TABLE_ABSOLUTE_H1:')
        o=Observation(self.context[0],0,step,input_sha+':'+str(pre_state),float(scheduler.sigmas[index]),
            source,source+':'+str(pre_state[2]) if source else None,step-pre_state[2] if source else None,
            pre_state[3],packets[0][2] if paid else None,packets[1][2] if paid else None,
            choice.local_proxy,choice.gain,choice.reason=='actual_protected_dense',supported)
        fs=self.causal.push(o)
        self.feature_rows.append({'step':step,'observation':asdict(o),
            'scheduler_pre_step_index':raw_index,'sigma_from_actual_first_grid_before_init':raw_index is None,
            'features':{m:{'names':f.names,'values':f.values,'prefix_steps':f.prefix_steps} for m,f in fs.items()},
            'ordinary_parent_only':True,'teacher_or_candidate_history_used':False})
        return fs

    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1;pre_state=self.controller._state();input_sha=tree_digest((noise,latent,timestep))
        payload=None;snapshot=None;trials=[];reason=self._preflight(step) if step in STEPS else None
        if step in STEPS and reason is None:
            if self.active_velocity is None or self.active_generator is None:raise ValueError('Original RF closure and generator required')
            snapshot=DiagnosticSnapshot(self,latent,noise,self.active_velocity,self.active_generator,self.diagnostic_config)
            owned=snapshot.owned.origin;physical=snapshot.physical_sha
            D_sha=tree_digest(plain([vars(c) for c in self.deployment.dense]))
            work_sha=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))
            pre_epoch=self.deployment.epoch
            parameters=[{key:getattr(c,key) for key in ('ridge','clip','decay','min_energy','shrinkage')}
                for c in self.deployment.dense]
            reset_sha=reset_dense_signature(self.context,parameters)
            work_parts_before={'ledger':tree_digest(self.deployment.working),
                'probe':tree_digest(self.net.probe_residual_cache),'residual':tree_digest(self.net.residual_cache)}
            payload={}
            try:
                for name in ('C','A','D'):
                    last_output=[]
                    def observe_cycle_output(module,args,head):
                        if int(self.net.cnt)==69:
                            last_output[:]=[tree_digest(self.net.unpatchify(head))]
                    hook=self.net.final_layer.register_forward_hook(observe_cycle_output) if step==35 else None
                    try:
                        with self.controller.action(step,name):
                            synchronize();start=time.perf_counter();self.actual_pair_computations+=1
                            value=SourcePhaseH1Owner.pair(self,noise,latent,timestep,conditions,choose)
                            synchronize();seconds=time.perf_counter()-start
                    finally:
                        if hook is not None:hook.remove()
                    h=copy.deepcopy(self.history[-1])
                    if h['A_readout']['readout_action']!=name:raise ValueError('Actual W3 candidate readout differs')
                    cycle_close=exact_native_cycle_close(self,step,h,pre_epoch,reset_sha,
                        last_output[-1] if last_output else None)
                    if name!='D' and (tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha
                            or tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))!=work_sha) and not cycle_close:
                        raise ValueError('C/A changed true D or working source: '+repr({'step':step,'action':name,
                            'source_before':pre_state,'true_D_changed':tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha,
                            'working_parts_before':work_parts_before,'working_parts_after':{
                                'ledger':tree_digest(self.deployment.working),'probe':tree_digest(self.net.probe_residual_cache),
                                'residual':tree_digest(self.net.residual_cache)}}))
                    payload[name]=tuple(v.detach().cpu().clone() for v in value)
                    trials.append({'kind':name,'actual_readout':h['A_readout']['readout_action'],
                        'actual_action':h['action'],'full_pair_seconds':seconds,
                        'exact_original_70_call_cycle_clear':cycle_close})
                    snapshot.restore()
                if (self.fingerprint()!=owned or snapshot.physical.fingerprint()!=physical
                        or self.controller._state()!=pre_state or tree_digest((noise,latent,timestep))!=input_sha):
                    raise ValueError('Complete W3 parent failed serial CAD restore')
            except BaseException:
                self.base.poisoned=self.controller.poisoned=self.deployment.poisoned=True;raise
            payload.update(actual_latent=latent.detach().cpu().clone(),timestep=timestep.detach().cpu().clone())
            artifact=self.writer(step,payload)
        self.actual_pair_computations+=1
        actual=SourcePhaseH1Owner.pair(self,noise,latent,timestep,conditions,choose)
        features=self._ordinary_observation(step,input_sha,pre_state)
        if step in STEPS:
            record={'step':step,'pre_action_state':pre_state,'input_sha256':input_sha,
                'sigma':features['T1'].observation.sigma,'feature_state_id':features['T1'].observation.state_id,
                'parent_action':self.history[-1]['action'],'parent_readout':self.history[-1]['A_readout']['readout_action'],
                'label_provenance':self.label_provenance,'candidate_or_teacher_committed_to_parent':False}
            if payload is None:
                record.update(status='UNKNOWN_ORIGINAL_SUPPORT_NOT_RELAXED',reason=reason,label=None,artifact=None,extra_pairs=0)
            else:
                semantic=record['parent_readout']
                if semantic in payload and any(not torch.equal(v.detach().cpu(),w) for v,w in zip(actual,payload[semantic])):
                    raise ValueError('Restored original H1 differs from same-state CAD output')
                moments=guided_velocity_moments(scene=self.context[0],state=record['feature_state_id'],
                    original=payload['C'],proposed=payload['A'],dense=payload['D'])
                qC=moments['base_guided_MSE']
                ec,eu=(a-d for a,d in zip(payload['A'],payload['D']))
                qA=(8*ec-7*eu).double().square().mean().item()
                label=SameStateLabel(self.context[0],0,step,record['feature_state_id'],qC,qA,self.label_provenance)
                target=label.target(features['T1'])
                record.update(status='COMPLETE_SAME_STATE_CAD_LABEL_NOT_ONLINE_VALUE',label=asdict(label),
                    gain_squared_targets=target.tolist(),teacher_moments=moments,artifact=artifact,trials=trials,
                    extra_pairs=3,serial_restores=snapshot.restores,complete_gate=snapshot.gate,
                    same_state_snapshot_and_parent_restore_verified=True,teacher_never_used_in_feature_inputs=True)
            self.records.append(record)
        return actual


@contextmanager
def install_w3_labels(clean,batch,scheduler,*,config,writer,holder,label_provenance):
    from .clean_speed20_r1 import patched
    original_compile=clean.compile_velocity;original_step=scheduler.step
    def factory(*args,**kwargs):
        owner=W3LabelOwner(*args,diagnostic_config=config,writer=writer,label_provenance=label_provenance,**kwargs)
        holder['owner']=owner;return owner
    def compile_velocity(runtime,rf,owner,choose):
        fn,proof=original_compile(runtime,rf,owner,choose)
        def bound(model,*args,**kwargs):
            velocity=fn(model,*args,**kwargs);owner.active_velocity=velocity;return velocity
        return bound,proof
    def solver_step(*args,**kwargs):
        owner=holder.get('owner');generator=kwargs.get('generator')
        if owner is not None:
            if owner.active_generator is not None and owner.active_generator is not generator:raise ValueError('Original W3 generator identity changed')
            owner.active_generator=generator
        return original_step(*args,**kwargs)
    with patched(batch,'SourcePhaseH1Owner',factory),patched(clean,'compile_velocity',compile_velocity),patched(scheduler,'step',solver_step):
        yield
