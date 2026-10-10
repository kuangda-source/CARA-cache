"""Actual semantic C/P/D execution with an explicit source-aware controller.

Only real two-branch completion commits policy, projection and D-only history.
The fixed P0/A implementations remain immutable; new instances carry new state.
"""
import ast
import hashlib
import inspect
import math
from textwrap import dedent

import torch

from .partial_mlp import PartialMLP
from .partial_mlp_deployment import PartialDeployment, PartialDeploymentPair
from .partial_mlp_guided_readout import GuidedPartialDeployment
from .partial_mlp_deployment_state import plain
from .source_aware_cpd_control import SourceAwareCPDController


def derive_select():
    source=dedent(inspect.getsource(PartialDeployment.select))
    changes=[("action = 'D' if step in D_STEPS else 'C'",
              "action = cur['source_choice'].action"),
             ("if self.method not in ('OFF', 'DENSE_CONTROL') and step in self.p_steps:",
              "if action == 'P':")]
    changed=source
    for old,new in changes:
        if changed.count(old)!=1:raise ValueError('Fixed P0 selector source differs')
        changed=changed.replace(old,new)
    inverse=changed
    for old,new in reversed(changes):
        if inverse.count(new)!=1:raise ValueError('Dynamic selector inverse ambiguous')
        inverse=inverse.replace(new,old)
    if inverse!=source or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(source)):
        raise ValueError('Dynamic P mask/source logic changed outside action choice')
    ns=dict(PartialDeployment.select.__globals__)
    exec(compile(changed,__file__+'#dynamic-select','exec'),ns)
    return ns['select'],{'inverse_AST_equal':True,'explicit_sites':2,
        'original_select_source_sha256':hashlib.sha256(source.encode()).hexdigest()}


SELECT,SELECT_PROOF=derive_select()


def derive_full_reference():
    source=dedent(inspect.getsource(PartialMLP._execute))
    old='fresh=original(gathered)'
    new='fresh=original(x).reshape(tokens,x.shape[-1]).index_select(0,ids)'
    if source.count(old)!=1:raise ValueError('Actual gathered MLP source differs')
    changed=source.replace(old,new)
    if changed.replace(new,old)!=source:raise ValueError('Full reference inverse differs')
    ns=dict(PartialMLP._execute.__globals__)
    exec(compile(changed,__file__+'#full-GEMM-reference','exec'),ns)
    return ns['_execute'],{'inverse_AST_equal':True,'explicit_GEMM_sites':1,
        'original_execute_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'diagnostic_full_GEMM_not_acceleration':True}


FULL_REFERENCE,FULL_REFERENCE_PROOF=derive_full_reference()


class FullGEMMPartialReference(PartialMLP):
    def _execute(self,layer,module,x):
        value=FULL_REFERENCE(self,layer,module,x)
        if not self._readonly:
            row=self.records[-1]
            row['selected_rows']=row['actual_MLP_rows']
            row['actual_MLP_rows']=math.prod(x.shape[:-1])
            row['actual_fraction']=1.
            row['full_MLP']=True
            row['diagnostic_full_GEMM_then_inactive_substitution']=True
        return value


class SourceAwarePartialDeployment(GuidedPartialDeployment):
    def __init__(self,*args,controller,reference=False,**kwargs):
        if (not isinstance(controller,SourceAwareCPDController) or controller.history
                or controller.poisoned or type(reference) is not bool):
            raise ValueError('Fresh explicitly calibrated source-aware owner required')
        super().__init__(*args,**kwargs)
        self.controller,self.reference=controller,reference
        if reference:
            layers=self.core.layers
            self.core.close()
            self.core=FullGEMMPartialReference(self.net.blocks,layers).install()

    def select(self,packets):
        cur=self.current
        if cur is None or cur.get('source_choice') is not None:
            raise ValueError('One current source-aware paid-pair decision required')
        step=cur['step']
        ready=all(v is not None and v['epoch']==self.epoch for v in self.working)
        ready=ready and all(getattr(self.net,f)[b] is not None for f in
            ('previous_input','previous_internal_states','residual_cache') for b in (0,1))
        expected={(l,b) for l in self.core.layers for b in (0,1)}
        partial_ready=set(self.core.cache)==expected and all(
            v.context==self.context and v.last_actual_D is not None
            and v.last_actual_D<step for v in self.core.cache.values())
        cur['source_choice']=self.controller.decide(step,packets,
            both_sources_ready=bool(ready),partial_ready=bool(partial_ready))
        physical=SELECT(self,packets)
        if self.reference and cur['action']=='P':
            # Independently reconstruct the rotation mask; no block_indices call.
            first=self.core.cache[(self.core.layers[0],0)]
            tokens=math.prod(first.value.shape[:-1]);full=tokens//self.block_size
            if tokens%self.block_size or full<2:
                raise ValueError('Independent reference requires complete token blocks')
            count=math.floor(full*(.5 if self.method.endswith('050') else .75))
            start=(self.opportunities-1)*count
            ids=torch.tensor(sorted(b*self.block_size+i for b in
                ((start+j)%full for j in range(count)) for i in range(self.block_size)),dtype=torch.int64)
            if not torch.equal(ids,cur['indices']):raise ValueError('Independent shared mask differs')
            cur['indices']=ids
        return physical

    def commit(self,actual,base_last):
        cur=self.current
        if cur is None:raise ValueError('Complete current source-aware pair required')
        step,choice=cur['step'],cur.get('source_choice')
        returned=super().commit(actual,base_last)
        row=self.history[-1];semantic=row['action'][0]
        if base_last['protected']:
            if choice is not None or semantic!='D':
                raise ValueError('Protected source-aware pair must actually complete D')
            self.controller.commit_protected_dense(step,actual_action='D',pair_completed=True)
        else:
            if choice is None:raise ValueError('Executed source-aware pair has no decision')
            self.controller.commit(choice,actual_action=semantic,pair_completed=True)
        row['source_policy']={'decision':plain(self.controller.history[-1]),
            'dense_anchor_after':self.controller.anchor,
            'working_kind_after':self.controller.working_kind,
            'working_created_step_after':self.controller.working_step,
            'creation_floor_proxy_after':self.controller.creation_floor,
            'accumulated_interval_proxy_after':self.controller.accumulated,
            'consecutive_P_after':self.controller.consecutive_P,
            'quality_fingerprint':None if self.controller.partial_prior is None
                else self.controller.partial_prior.fingerprint,
            'cost_fingerprint':self.controller.costs.fingerprint,
            'proxy_definition':'WC_PAID_DELTA_Y',
            'native_cycle_closed_before_next_protected_D':row['native_cycle_reset']}
        for sources in (row['working_sources'],self.working):
            for value in sources:
                if value is not None:
                    value['estimated_creation_floor_proxy']=self.controller.creation_floor
                    value['source_policy_quality_fingerprint']=row['source_policy']['quality_fingerprint']
        return returned

    def finish(self):
        result=super().finish()
        if (len(self.controller.history)!=36 or self.controller.poisoned
                or [d.action*2 for d in self.controller.history]!=[h['action'] for h in self.history]):
            raise ValueError('Complete actual dynamic policy/history required')
        result.pop('fixed_P_steps',None);result.pop('fixed_D_steps',None)
        result['source_risk_RA_policy_implemented']=True
        result['combined_readout_source_risk_policy_implemented']=True
        result['source_policy_history']=plain(self.controller.history)
        result['source_policy_final_state']=plain(self.controller.state_dict())
        result['fixed_schedule_used_for_dynamic_choice']=False
        result['diagnostic_full_GEMM_reference']=self.reference
        result['source_aware_select_proof']=SELECT_PROOF
        result['full_GEMM_reference_proof']=FULL_REFERENCE_PROOF if self.reference else None
        return result


class SourceAwarePartialPair(PartialDeploymentPair):
    def pair(self,*args,**kwargs):
        try:return super().pair(*args,**kwargs)
        except BaseException:
            self.deployment.controller.poisoned=True
            raise
