"""Cost plus calibrated squared guided-error proxy, H1/H2 look-ahead.

No candidate model evaluation or endpoint label. Future drift is a declared
transfer of current paid-probe slope over the known sigma schedule. Source
floor and incurred trajectory error are different state variables.
"""
import copy
from dataclasses import replace
from itertools import product
import math

from .source_aware_current_birth_control_r1 import CurrentBirthCPDController
from .source_aware_cpd_control import Choice, SourceAwareCPDController

VERSION='MATH_N2_SQUARED_GUIDED_RISK_SIGMA_H1_H2_R1'


class EventController(CurrentBirthCPDController):
    def __init__(self,*args,math_parameters,horizon,sigma_at,fixed_control_plan=None,**kwargs):
        super().__init__(*args,**kwargs)
        if horizon not in (1,2) or not callable(sigma_at):raise ValueError('Frozen H1/H2 and real schedule required')
        p=copy.deepcopy(math_parameters)
        if (not p.get('fingerprint') or p['lambda_seconds_per_normalized_error']<=0
                or p['A_pair_cost_seconds']<=0
                or set(p['source'])!={'D','P'}):raise ValueError('Bound squared-error units and complete costs required')
        for source in ('D','P'):
            cell=p['source'][source]
            if any(not math.isfinite(cell[k]) or cell[k]<0 for k in ('C_scale','A_over_C')):
                raise ValueError('Nonnegative source-specific calibrated error required')
        self.math_parameters,self.horizon,self.sigma_at=p,horizon,sigma_at
        if fixed_control_plan is not None:
            if (len(fixed_control_plan)!=36 or any(a not in ('C','A','D') for a in fixed_control_plan)
                    or fixed_control_plan[:7]!=['D']*7 or fixed_control_plan[-1]!='D'):
                raise ValueError('Complete H2 mask with all P replaced by D required')
        self.fixed_control_plan=copy.deepcopy(fixed_control_plan)

    def _choice(self,step,packet_values,ready,partial_ready,protected=False):
        origin=super()._choice(step,packet_values,ready,partial_ready,protected)
        if self.fixed_control_plan is not None and not protected:
            name=self.fixed_control_plan[step-1]
            if name!='D' and (not ready or origin.local_proxy is None):
                raise ValueError('Fixed H2 mask lost required paid-source readiness')
            return replace(origin,action='C' if name=='A' else name,added_risk=0.,
                predicted_creation_floor=0. if name=='D' else self.creation_floor,
                candidates=(),reason='MATH_EVENT_FIXED_P_TO_D_CONTROL:'+name)
        if origin.local_proxy is None or protected:return origin
        p=self.math_parameters
        basis=self.working_step if self.working_kind=='P' else self.anchor
        interval=abs(self.sigma_at(basis)-self.sigma_at(step))
        slope=origin.local_proxy/max(interval,1e-12)
        costs={'C':self.costs.C,'A':p['A_pair_cost_seconds'],'D':self.costs.D}
        if partial_ready and self.partial_prior is not None and self.costs.P is not None:
            costs['P']=self.costs.P
        actions=tuple(costs);H=min(self.horizon,37-step);plans=[]
        for sequence in product(actions,repeat=H):
            kind,birth,floor,consecutive=self.working_kind,basis,self.creation_floor,self.consecutive_P
            total=0.;terms=[];valid=True
            for offset,action in enumerate(sequence):
                n=step+offset
                if n==36 and action!='D':valid=False;break
                if action=='P' and consecutive>=self.partial_prior.maximum_consecutive_P:valid=False;break
                gain=self.calibration.gains.get(n)
                if gain is None:valid=False;break
                if action=='D':q=0.;newfloor=0.
                elif action=='P':
                    newfloor=self.partial_prior.creation_floor_at(n)
                    q=p['source']['P']['C_scale']*newfloor**2
                else:
                    drift=slope*abs(self.sigma_at(birth)-self.sigma_at(n))
                    cell=p['source'][kind]
                    q=cell['C_scale']*(floor+drift)**2
                    if action=='A':q*=cell['A_over_C']
                    newfloor=floor
                weighted=gain*q;c=costs[action]
                if not math.isfinite(weighted+c) or weighted<0:valid=False;break
                total+=c+p['lambda_seconds_per_normalized_error']*weighted
                terms.append((action,c,weighted,newfloor))
                if action=='D':kind,birth,floor,consecutive='D',n,0.,0
                elif action=='P':kind,birth,floor,consecutive='P',n,newfloor,consecutive+1
                else:consecutive=0
            if valid:plans.append((total,sequence,terms))
        if not plans:raise ValueError('Dense fallback must remain a valid finite plan')
        best=min(plans,key=lambda x:(x[0],x[1]));name,c,q,floor=best[2][0]
        # A is a semantic C execution with an explicit readout choice. The
        # physical pair interface remains C/P/D, preserving true-D ownership.
        semantic='C' if name=='A' else name
        return replace(origin,action=semantic,added_risk=q,predicted_creation_floor=floor,
            candidates=tuple((t[0],t[1],t[2],t[3]) for t in best[2]),
            reason=f'MATH_EVENT_H{self.horizon}:'+name)

    def commit(self,choice,*,actual_action,pair_completed):
        # Accumulated squared proxy is a diagnostic history. Neither source
        # refresh nor planning claims to erase existing latent/solver error.
        return SourceAwareCPDController.commit(self,choice,actual_action=actual_action,pair_completed=pair_completed)

    def state_dict(self):
        value=SourceAwareCPDController.state_dict(self)
        value['binding']+=(VERSION,self.math_parameters['fingerprint'],self.horizon,self.strategy,
                           None if self.fixed_control_plan is None else tuple(self.fixed_control_plan))
        return value

    def restore(self,snapshot):
        if set(snapshot)!={'binding','state','history'} or snapshot['binding']!=self.state_dict()['binding']:
            raise ValueError('Exact cost/risk/horizon/source binding required for restore')
        replay=EventController(self.calibration,self.threshold,self.costs,self.partial_prior,
            strategy=self.strategy,math_parameters=self.math_parameters,horizon=self.horizon,sigma_at=self.sigma_at,
            fixed_control_plan=self.fixed_control_plan)
        for original in snapshot['history']:
            if not isinstance(original,Choice) or original.owner!=id(self):raise ValueError('Foreign event history')
            d=replay._choice(original.step,original.packets,original.both_sources_ready,
                original.partial_ready,protected=original.reason=='actual_protected_dense')
            if replace(d,owner=id(self))!=original:raise ValueError('Modified event-history decision')
            replay.commit(d,actual_action=d.action,pair_completed=True)
        if replay._state()!=snapshot['state'] or snapshot['state'][-1]:raise ValueError('Incomplete/poisoned event restore')
        old=self.state_dict()
        (self.anchor,self.working_kind,self.working_step,self.creation_floor,self.accumulated,
         self.consecutive_P,self.last_completed_step,self.generation,self.poisoned)=snapshot['state']
        self.history=copy.deepcopy(snapshot['history']);return old

    def query_basis(self,choice):
        value=super().query_basis(choice)
        return {**value,'math_version':VERSION,'risk_unit':'NORMALIZED_GUIDED_OUTPUT_SQUARED_ERROR',
                'next_sigma_known_not_next_latent':'KNOWN_SCHEDULE_CURRENT_SLOPE_TRANSFER',
                'actual_online_candidate_evaluations':0,'horizon':self.horizon}
