"""Current source-aware C/A/P0/D prices on all16 frozen development states.

Four old P_OFF parents continue unchanged; all trial state is restored outside
the action clock. No new policy, source, sparse method or fitted price is used.
"""
import copy
from contextlib import contextmanager

import torch

from .source_phase16_calibration_r1 import SourcePhase16Owner,calibration16_install
from .source_aware_phase_sampling import bind_globals
from .math_n2_sampling_owner_r1 import MathSamplingOwner
from .e4c_matched_source_age_owner_r1 import DiagnosticSnapshot
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .post_probe_action_clock_r1 import observe_post_probe_action

VERSION='N09_CURRENT_ACTION_PRICE16_POST_PAID_PROBE_R1'
ACTIONS=('C','A','P0','D')
ROUNDS=(('WARMUP',('C','A','P0','D')),('FORMAL_1',('C','A','P0','D')),
        ('FORMAL_2',('D','P0','A','C')),('FORMAL_3',('A','P0','D','C')))
COUNTS=dict(baseline_parents=4,diagnostic_parents=8,full_paths=12,distinct_states=16,
    measured_state_mode_positions=32,ordinary_pairs=432,trial_pairs=512,
    warmup_trial_pairs=128,formal_trial_pairs=384,total_pairs=944,CFG_calls=1888,
    loads=1,raw_files=32,raw_tensors=320,new_offline_dense_trials=128,online_teachers=0)


class ActionPrice16Owner(SourcePhase16Owner):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.price_mode=self.config['action_price_observation_mode']
        if self.price_mode not in ('AUDIT','LEAN'):
            raise ValueError('Separate complete audit and lean action-price modes required')
        # This is exactly the existing clean.install(audit=False) hook policy.
        # Algorithm projection/cache hooks are separately owned and retained.
        if self.price_mode=='LEAN':
            for handle in self.hooks:handle.remove()
            self.hooks.clear()

    def installation(self):return super().installation()+(VERSION,ROUNDS,self.price_mode)

    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1;point=self.states.get(step)
        if point is None:
            self.actual_pair_computations+=1
            return MathSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
        if self.active_velocity is None or self.active_generator is None:
            raise ValueError('Ordinary velocity/UniPC generator identity required')
        before=DiagnosticSnapshot(self,latent,noise,self.active_velocity,self.active_generator,self.config)
        state=self.controller._state();chosen=point['chosen']
        if (state[0]!=chosen['true_D_anchor'] or state[1]!=point['source']
                or state[2]!=chosen['source_birth'] or step-state[2]!=chosen['age']
                or ('EARLY' if step<25 else 'LATE')!=point['phase']):
            raise ValueError('Reproduce every frozen natural source/phase/age state')
        input_sha=tree_digest((noise,latent,timestep))
        D_sha=tree_digest(plain([vars(c) for c in self.deployment.dense]))
        work_sha=tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))
        payload={};trials=[];expected_packets=None
        for round_name,order in ROUNDS:
            for label in order:
                action='P' if label=='P0' else label;heads=len(self.head_calls)
                with self.controller.action(step,action):
                    with observe_post_probe_action(self,synchronize=synchronize) as timer:
                        self.actual_pair_computations+=1
                        output=MathSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
                        interval=timer.finish()
                # All validation/copy/digest/write costs are outside the interval,
                # included in the complete diagnostic card's actual GPU wall bill.
                history=copy.deepcopy(self.history[-1]);extra=len(self.head_calls)-heads
                if (history['action']!=('C' if action=='A' else action)*2
                        or tree_digest((noise,latent,timestep))!=input_sha):
                    raise ValueError('Actual primitive or current input changed')
                if action!='D' and tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha:
                    raise ValueError('C/A/P0 trial wrote into trusted D history')
                if action in ('C','A') and tree_digest((self.deployment.working,
                        self.net.probe_residual_cache,self.net.residual_cache))!=work_sha:
                    raise ValueError('Readout changed its working source')
                if action=='P' and (history['source_policy']['creation_floor_proxy_after']<=0
                        or any(s['kind']!='P' or s['created_step']!=step or s['RA_zero_risk_reset_allowed']
                               for s in history['working_sources'])):
                    raise ValueError('P0 is an approximate source with positive birth error')
                if expected_packets is None:expected_packets=interval['paid_packets']
                if interval['paid_packets']!=expected_packets:
                    raise ValueError('Replayed paid prefixes changed within the same actual state')
                pair=tuple(v.detach().cpu().clone() for v in output)
                if any(not bool(torch.isfinite(v).all()) for v in pair):
                    raise ValueError('Nonfinite actual post-RF output')
                if round_name=='WARMUP':
                    payload[label+'_conditional'],payload[label+'_unconditional']=pair
                elif any(not torch.equal(v,payload[label+'_'+branch])
                         for v,branch in zip(pair,('conditional','unconditional'))):
                    raise ValueError('A formal action trial differs from its full warmup result')
                trials.append(dict(round=round_name,action=label,actual_action=history['action'],
                    interval=interval,actual_heads=extra if self.price_mode=='AUDIT' else None,
                    heads_observed=self.price_mode=='AUDIT',observation_mode=self.price_mode,
                    output_tree_sha256=tree_digest(pair),
                    A_readout=history['A_readout'],source_history=history['source_policy']))
                before.restore()
                if self.controller._state()!=state:raise ValueError('Trial remained in parent policy')
        payload.update(actual_latent=latent.detach().cpu().clone(),timestep=timestep.detach().cpu().clone())
        artifact=self.writer(step,payload)
        self.actual_pair_computations+=1
        actual=MathSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
        natural=copy.deepcopy(self.history[-1])
        if natural['action']!=chosen['actual_pi0_action']*2:
            raise ValueError('Original parent decision changed')
        label='P0' if natural['action']=='PP' else 'D' if natural['action']=='DD' else 'A' if point['source']=='D' else 'C'
        if any(not torch.equal(v.detach().cpu(),payload[label+'_'+branch])
               for v,branch in zip(actual,('conditional','unconditional'))):
            raise ValueError('Restored ordinary parent differs from its actual trial action')
        self.records.append(dict(point=point,trials=trials,observation_mode=self.price_mode,
            artifact=artifact,input_sha256=input_sha,
            true_D_state_sha256=D_sha,working_state_sha256=work_sha,restores=before.restores,
            complete_gate=before.gate,parent_continues=natural['action'],
            new_prices_used_in_parent=False,offline_trial_committed_to_parent=False,
            each_trial_pays_two_real_probes_outside_incremental_clock=True,
            online_teacher_or_clean_latency_claim=False))
        return actual


# Preserve the existing installation body, with one explicit owner binding.
price16_install=contextmanager(bind_globals(calibration16_install.__wrapped__,
    {'SourcePhase16Owner':ActionPrice16Owner}))
