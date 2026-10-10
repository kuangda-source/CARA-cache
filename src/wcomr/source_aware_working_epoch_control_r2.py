"""Experimental working-P age transfer, with explicit nonzero P rebaselining.

Both choices borrow the old D-only rho table; neither claims measured future
P drift. True D calibration anchors remain separate from working P epochs.
The optional rebase changes a heuristic interval, not latent/solver history.
"""
import ast
import copy
from dataclasses import replace
import hashlib
import inspect
import textwrap

from . import source_aware_cpd_control as base
from .source_aware_phase_control import CreationPhaseCPDController,CreationPhasePrior

STRATEGIES = ('WORKING_P_AGE_KEEP_INTERVAL','WORKING_P_AGE_NONZERO_REBASE')


class WorkingEpochCPDController(CreationPhaseCPDController):
    def __init__(self,calibration,threshold,costs,partial_prior=None,*,strategy=STRATEGIES[0]):
        if strategy not in STRATEGIES:
            raise ValueError('Explicit registered P age/interval transfer strategy required')
        self.strategy = strategy
        super().__init__(calibration,threshold,costs,partial_prior)

    def query_basis(self,choice):
        if not isinstance(choice,base.Choice) or choice.owner!=id(self):
            raise ValueError('Own scalar decision required')
        anchor,kind,working_step=choice.state_before[:3]
        query_anchor=working_step if kind=='P' else anchor
        return {'true_D_anchor':anchor,'working_source_kind':kind,
            'working_source_step':working_step,'query_anchor':query_anchor,
            'query_age':choice.step-query_anchor if query_anchor is not None else None,
            'rho_source':'D_ONLY_PRIOR_TRANSFERRED_TO_WORKING_P_AGE' if kind=='P' else 'D_ONLY_PRIOR',
            'P_future_drift_empirically_calibrated':False,'strategy':self.strategy}

    def commit(self,choice,*,actual_action,pair_completed):
        super().commit(choice,actual_action=actual_action,pair_completed=pair_completed)
        if actual_action=='P' and self.strategy==STRATEGIES[1]:
            # The current P contribution includes its positive calibrated birth
            # prior. Never reclassify P as D or assign it a zero source floor.
            self.accumulated=choice.added_risk

    def state_dict(self):
        value=super().state_dict()
        value['binding']=value['binding']+(self.strategy,)
        return value

    def restore(self,snapshot):
        expected=(self.calibration.fingerprint,self.threshold,self.costs,self.partial_prior,self.strategy)
        if (set(snapshot)!={'binding','state','history'} or snapshot['binding']!=expected
                or type(snapshot['state']) is not tuple or len(snapshot['state'])!=9
                or type(snapshot['history']) is not list):
            raise ValueError('Working-source strategy or healthy snapshot layout differs')
        old=self.state_dict()
        replay=WorkingEpochCPDController(self.calibration,self.threshold,self.costs,
            self.partial_prior,strategy=self.strategy)
        for original in snapshot['history']:
            if not isinstance(original,base.Choice) or original.owner!=id(self):
                raise ValueError('Foreign working-source history')
            d=replay._choice(original.step,original.packets,original.both_sources_ready,
                original.partial_ready,protected=original.reason=='actual_protected_dense')
            if replace(d,owner=id(self))!=original:
                raise ValueError('Changed working-source decision or retained interval history')
            replay.commit(d,actual_action=d.action,pair_completed=True)
        if replay._state()!=snapshot['state'] or snapshot['state'][-1]:
            raise ValueError('Working-source state differs from complete healthy history')
        (self.anchor,self.working_kind,self.working_step,self.creation_floor,
         self.accumulated,self.consecutive_P,self.last_completed_step,
         self.generation,self.poisoned)=snapshot['state']
        self.history=copy.deepcopy(snapshot['history'])
        return old


original=textwrap.dedent(inspect.getsource(base.SourceAwareCPDController._choice))
sites=[('p.creation_floor_proxy','p.creation_floor_at(step)',2),
       ('cell = (self.anchor, step)',
        "query_anchor = self.working_step if self.working_kind == 'P' else self.anchor\n        cell = (query_anchor, step)",1)]
changed=original
for before,after,count in sites:
    if changed.count(before)!=count:raise ValueError('Pinned source-choice sites changed')
    changed=changed.replace(before,after)
inverse=changed
for before,after,count in reversed(sites):inverse=inverse.replace(after,before)
if inverse!=original or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(original)):
    raise ValueError('Source control changed beyond the registered age and birth-prior sites')
namespace=vars(base).copy()
exec(compile(changed,__file__+'#working-source-query', 'exec'),namespace)
WorkingEpochCPDController._choice=namespace['_choice']
DERIVATION_PROOF={'original_source_choice_sha256':hashlib.sha256(original.encode()).hexdigest(),
    'inverse_AST_and_original_bytes_equal':True,'query_epoch_sites':1,
    'existing_phase_birth_prior_sites':2,'true_D_anchor_or_floor_not_zeroed_by_P':True}
