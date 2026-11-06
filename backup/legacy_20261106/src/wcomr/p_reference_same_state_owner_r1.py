"""Five readouts share each actual C state; only old D-scalar is deployed.

P/D birth and C4 are offline interventions. Same-state candidate and teacher
computations pay full probes/heads and restore complete state. No new online
refresh rule or fitted target is introduced here.
"""
import copy
import inspect
import time
from textwrap import dedent

import torch

from .e4c_matched_source_age_owner_r1 import MatchedSourceAgeOwner, DiagnosticSnapshot
from .source_aware_CPU_storage_sampling_r1 import CPUStorageSamplingOwner
from .partial_mlp_guided_readout import SemanticPartialReadout
from .p_working_reference_readout_r1 import WorkingReferenceReadout
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .cfg_guided_w1_outputs import guided_velocity_moments
from .light_sampling import synchronize


VERSION = 'P_REFERENCE_FIVE_READOUTS_SAME_STATE_R1'
VARIANTS = ('OFFICIAL_C', 'P_REFERENCE_SCALAR', 'D_REFERENCE_UNIT',
            'P_REFERENCE_UNIT', 'D_REFERENCE_SCALAR')


class ComparisonReadout(WorkingReferenceReadout):
    reference_variant = 'D_REFERENCE_SCALAR'

    def semantic_hidden(self, *args):
        if self.reference_variant.startswith('P_REFERENCE'):
            return super().semantic_hidden(*args)
        return SemanticPartialReadout.semantic_hidden(self, *args)


class SameStateReferenceOwner(MatchedSourceAgeOwner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        old = self.deployment.readout
        new = ComparisonReadout(self.deployment, method=old.method)
        new.warp, new.to_velocity = old.warp, old.to_velocity
        self.deployment.readout = new

    def installation(self):
        return super().installation()+(VERSION,self.deployment.readout.reference_variant)

    def check_healthy(self):
        super().check_healthy()
        r=self.deployment.readout
        if r.reference_variant!='D_REFERENCE_SCALAR' or r.method!=self.a_method:
            raise ValueError('Inactive snapshot requires the original deployed readout')

    def _read(self, variant, noise, latent, timestep, conditions, choose):
        if variant not in VARIANTS:
            raise ValueError('Registered five-way same-state readout required')
        r = self.deployment.readout
        old_method, old_variant = r.method, r.reference_variant
        r.method = ('OFF' if variant == 'OFFICIAL_C' else
                    'BETA1_ONE_PHASE' if variant.endswith('UNIT') else 'W1_ONE_PHASE')
        r.reference_variant = variant
        try:
            return CPUStorageSamplingOwner.pair(self, noise, latent, timestep, conditions, choose)
        finally:
            r.method, r.reference_variant = old_method, old_variant

    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history)+1
        active = self.active_suffix
        age = step-active['birth_step'] if active else None
        if not (active and active['source'] in ('P','D') and age in (1,2,4)):
            return super().pair(noise, latent, timestep, conditions, choose)
        before = DiagnosticSnapshot(self, latent, noise, self.active_velocity,
                                     self.active_generator, self.config)
        input_sha = tree_digest((noise,latent,timestep))
        control_state = self.controller._state()
        full_D = tree_digest(plain([vars(c) for c in self.deployment.dense]))
        source_sha = tree_digest((self.deployment.working, self.net.probe_residual_cache,
                                  self.net.residual_cache))
        beta_stats = [copy.deepcopy(c.receipt()) for c in self.deployment.dense]
        raw_beta = [c.numerator/(c.denominator+c.ridge)
                    if c.pairs and c.denominator>c.min_energy else None for c in self.deployment.dense]
        clipped_beta = [None if b is None else max(-c.clip,min(c.clip,b))
                        for c,b in zip(self.deployment.dense,raw_beta)]
        try:
            synchronize(); started=time.perf_counter()
            teacher_heads_before=len(self.head_calls)
            with self.controller.same_state_teacher(step):
                teacher=CPUStorageSamplingOwner.pair(self,noise,latent,timestep,conditions,choose)
            synchronize(); teacher_seconds=time.perf_counter()-started
            teacher_head_events=copy.deepcopy(self.head_calls[teacher_heads_before:])
            if len(teacher_head_events)!=2:
                raise ValueError('Actual complete teacher head calls differ')
            teacher=tuple(v.detach().clone() for v in teacher)
        finally:
            before.restore()
        candidates={};records=[]
        # The deployed D-reference scalar is last. Earlier candidate histories,
        # caches, solver/RNG and head counts are restored before every next call.
        for index,variant in enumerate(VARIANTS):
            if (self.controller._state()!=control_state
                    or tree_digest((noise,latent,timestep))!=input_sha
                    or tree_digest(plain([vars(c) for c in self.deployment.dense]))!=full_D
                    or tree_digest((self.deployment.working,self.net.probe_residual_cache,
                                    self.net.residual_cache))!=source_sha):
                raise ValueError('Candidate did not start from the same actual full source state')
            synchronize(); started=time.perf_counter()
            candidate_heads_before=len(self.head_calls)
            value=self._read(variant,noise,latent,timestep,conditions,choose)
            synchronize(); seconds=time.perf_counter()-started
            h=copy.deepcopy(self.history[-1])
            head_events=copy.deepcopy(self.head_calls[candidate_heads_before:])
            if (h['action']!='CC' or h['working_source_ages']!=[age,age]
                    or any(s['kind']!=active['source'] or s['created_step']!=active['birth_step']
                           for s in h['working_sources'])
                    or tree_digest(plain([vars(c) for c in self.deployment.dense]))!=full_D
                    or tree_digest((self.deployment.working,self.net.probe_residual_cache,
                                    self.net.residual_cache))!=source_sha
                    or tree_digest((noise,latent,timestep))!=input_sha
                    or len(head_events)!=2+h['A_readout']['extra_heads']):
                raise ValueError('Scoring changed source caches, true D, inputs or C action')
            candidates[variant]=tuple(v.detach().cpu().clone() for v in value)
            records.append({'variant':variant,'step':step,'source':active['source'],'age':age,
                'input_sha256':input_sha,'true_D_full_state_sha256':full_D,
                'source_cache_sha256':source_sha,'readout':h['A_readout'],
                'complete_pair_seconds':seconds,'actual_head_calls':len(head_events),
                'actual_head_events':head_events,
                'guided_moments':guided_velocity_moments(scene=self.context[0],
                    state=active['event_id']+'-'+active['source']+'-age'+str(age)+'-'+variant,
                    original=value,proposed=value,dense=teacher),
                'deployed_after_scoring':variant=='D_REFERENCE_SCALAR'})
            if index<len(VARIANTS)-1:before.restore()
        actual=value
        if active['source']=='D':
            for left,right in (('P_REFERENCE_SCALAR','D_REFERENCE_SCALAR'),
                               ('P_REFERENCE_UNIT','D_REFERENCE_UNIT')):
                if not all(torch.equal(a,b) for a,b in zip(candidates[left],candidates[right])):
                    raise ValueError('P-reference candidate changed the D-source control')
        guided=actual[0]+7*(actual[0]-actual[1])
        active['guided'].append(guided.detach().cpu().clone())
        active['actions'].append(self.history[-1]['action'])
        active['realized_full_pair_wall_seconds'].append(records[-1]['complete_pair_seconds'])
        h=copy.deepcopy(self.history[-1]);scheduler=self.model.sample_scheduler
        payload={'C':candidates['D_REFERENCE_SCALAR'],
            'DENSE_SAME_STATE':tuple(v.detach().cpu().clone() for v in teacher),
            'candidate_latent':latent.detach().cpu().clone(),'timestep':timestep.detach().cpu().clone(),
            **{k:v for k,v in candidates.items() if k!='D_REFERENCE_SCALAR'}}
        artifact=self.writer(active['event_id'],active['source'],age,payload)
        point={'event_id':active['event_id'],'source':active['source'],'age':age,'step':step,
            'sigma_index':scheduler._step_index,'sigma':float(scheduler.sigmas[scheduler._step_index]),
            'timestep':timestep.detach().cpu().tolist(),'input_sha256':input_sha,
            'candidate_latent_sha256':tree_digest(payload['candidate_latent']),
            'true_D_steps_before':[c['anchor_steps'] for c in beta_stats],
            'D_statistics_before_C':beta_stats,'fitted_beta_from_actual_D_statistics':clipped_beta,
            'A_status':h['A_readout']['branch_status'],'actual_shared_alpha':h['A_readout']['shared_alpha'],
            'actual_source_and_decision_history':h,'same_state_guided_moments':records[-1]['guided_moments'],
            'actual_C_full_pair_seconds':records[-1]['complete_pair_seconds'],
            'research_teacher_full_pair_seconds':teacher_seconds,
            'research_teacher_actual_head_events':teacher_head_events,
            'teacher_state_restored_before_actual_C':True,'teacher_updates_final_deployment_anchors':False,
            'birth_source_P_not_promoted_to_D':True,'complete_gate':before.gate,
            'serial_restore_guards':before.restores,'artifact':artifact,
            'five_reference_readouts':records,'all_candidates_same_actual_input_and_full_source':True,
            'deployed_reference_unchanged':'D_REFERENCE_SCALAR',
            'total_research_pair_wall_seconds':teacher_seconds+sum(r['complete_pair_seconds'] for r in records),
            'cost_boundary':'ALL_SIX_FULL_PAIRS_AND_RESTORES_NOT_ONLINE_OR_CLEAN_LATENCY'}
        active['age_points'].append(point)
        return actual


# Windows retain their originally registered ON positions in both flow modes.
# In OFF the original policy's first action may differ; both natural repeats
# must still exactly match that mode's original parent slice. Forced births are
# explicitly interventions, never represented as naturally selected OFF P.
_source=dedent(inspect.getsource(MatchedSourceAgeOwner.run_event))
_old="                if not source and branch['actions'][0] != 'PP':\n                    raise ValueError('The registered natural parent P event was not reproduced')"
_new="                if not source:\n                    branch['natural_first_action'] = branch['actions'][0]"
if _source.count(_old)!=1:raise ValueError('Original natural-event observation site differs')
_edited=_source.replace(_old,_new)
if _edited.replace(_new,_old)!=_source:raise ValueError('Unregistered suffix implementation edit')
_namespace=dict(inspect.unwrap(MatchedSourceAgeOwner.run_event).__globals__)
if _namespace.get("torch") is not torch:raise ValueError("Original unwrapped method globals differ")
exec(compile(_edited,__file__+'#explicit-fixed-window-natural-action-observation','exec'),_namespace)
SameStateReferenceOwner.run_event=_namespace['run_event']
