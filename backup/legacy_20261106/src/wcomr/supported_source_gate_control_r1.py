"""Source-minimum readout and support-aware H1/H2; no generator/teacher.

D-source reuse is explicitly A, P-source reuse is C, with optional P-A.
This is a fixed source rule, not a claim that the optimizer learned D-A.
Both current and future support use the same actual rho grid. The source
floor remains positive for P; existing latent/solver error is never reset.
"""
import copy
from dataclasses import replace
from itertools import product
import math

from .math_n2_event_control_r1 import EventController
from .source_aware_current_birth_control_r1 import CurrentBirthCPDController
from .source_aware_cpd_control import Choice

VERSION='SUPPORTED_SOURCE_MINIMUM_SQUARED_GAIN_H1_H2_R1'

class SupportedGateController(EventController):
    def __init__(self,*args,allow_P_A=False,**kwargs):
        super().__init__(*args,**kwargs)
        if type(allow_P_A) is not bool or self.fixed_control_plan is not None:
            raise ValueError('Registered source action set and natural adaptive policy required')
        if set(self.math_parameters['source_A_cost_seconds'])!={'D','P'}:
            raise ValueError('Both actual source head prices required')
        if any(not math.isfinite(v) or v<=0 for v in self.math_parameters['source_A_cost_seconds'].values()):
            raise ValueError('Positive finite source-specific head costs required')
        self.allow_P_A=allow_P_A

    def _choice(self,step,packet_values,ready,partial_ready,protected=False):
        origin=CurrentBirthCPDController._choice(self,step,packet_values,ready,partial_ready,protected)
        if protected:return origin
        if origin.local_proxy is None:
            if origin.reason=='missing_current_calibration':
                return replace(origin,reason='MATH_EVENT_SG_SUPPORT_BOUNDARY:D')
            return origin
        p=self.math_parameters;birth=self.working_step if self.working_kind=='P' else self.anchor
        slope=origin.local_proxy/max(abs(self.sigma_at(birth)-self.sigma_at(step)),1e-12)
        actions=('C','A','P','D');H=min(self.horizon,37-step);plans=[]
        for sequence in product(actions,repeat=H):
            kind,born,floor,consecutive=self.working_kind,birth,self.creation_floor,self.consecutive_P
            total=0.;terms=[];valid=True
            for offset,action in enumerate(sequence):
                n=step+offset
                supported=(born,n) in self.calibration.rho_at and n in self.calibration.gains
                if (n==36 or not supported) and action!='D':valid=False;break
                if action=='C' and kind!='P':valid=False;break
                if action=='A' and kind=='P' and not self.allow_P_A:valid=False;break
                if action=='P' and (not partial_ready or self.partial_prior is None or self.costs.P is None
                        or consecutive>=self.partial_prior.maximum_consecutive_P):valid=False;break
                gain=self.calibration.gains.get(n)
                if gain is None and action!='D':valid=False;break
                if action=='D':q=0.;newfloor=0.;cost=self.costs.D
                elif action=='P':
                    newfloor=self.partial_prior.creation_floor_at(n)
                    q=p['source']['P']['C_scale']*newfloor**2;cost=self.costs.P
                else:
                    drift=slope*abs(self.sigma_at(born)-self.sigma_at(n));cell=p['source'][kind]
                    q=cell['C_scale']*(floor+drift)**2
                    if action=='A':q*=cell['A_over_C']
                    cost=p['source_A_cost_seconds'][kind] if action=='A' else self.costs.C
                    newfloor=floor
                weighted=0. if action=='D' else gain*gain*q
                if not math.isfinite(weighted+cost) or weighted<0:valid=False;break
                total+=cost+p['lambda_seconds_per_normalized_error']*weighted
                terms.append((action,cost,weighted,newfloor))
                if action=='D':kind,born,floor,consecutive='D',n,0.,0
                elif action=='P':kind,born,floor,consecutive='P',n,newfloor,consecutive+1
                else:consecutive=0
            if valid:plans.append((total,sequence,terms))
        if not plans:raise ValueError('Actual D must be valid throughout the known schedule')
        best=min(plans,key=lambda x:(x[0],x[1]));name,price,q,newfloor=best[2][0]
        return replace(origin,action='C' if name=='A' else name,added_risk=q,
            predicted_creation_floor=newfloor,candidates=tuple(best[2]),
            reason=f'MATH_EVENT_SG_H{self.horizon}:'+name)

    def state_dict(self):
        value=super().state_dict();value['binding']+=(VERSION,self.allow_P_A)
        return value

    def restore(self,snapshot):
        if set(snapshot)!={'binding','state','history'} or snapshot['binding']!=self.state_dict()['binding']:
            raise ValueError('Source minimum/support/gain-square binding changed')
        replay=SupportedGateController(self.calibration,self.threshold,self.costs,self.partial_prior,
            strategy=self.strategy,math_parameters=self.math_parameters,horizon=self.horizon,
            sigma_at=self.sigma_at,allow_P_A=self.allow_P_A)
        for original in snapshot['history']:
            if not isinstance(original,Choice) or original.owner!=id(self):raise ValueError('Foreign source rule history')
            d=replay._choice(original.step,original.packets,original.both_sources_ready,
                original.partial_ready,protected=original.reason=='actual_protected_dense')
            if replace(d,owner=id(self))!=original:raise ValueError('Changed support-aware decision history')
            replay.commit(d,actual_action=d.action,pair_completed=True)
        if replay._state()!=snapshot['state'] or snapshot['state'][-1]:raise ValueError('Failed/incomplete support-aware boundary')
        old=self.state_dict()
        (self.anchor,self.working_kind,self.working_step,self.creation_floor,self.accumulated,
         self.consecutive_P,self.last_completed_step,self.generation,self.poisoned)=snapshot['state']
        self.history=copy.deepcopy(snapshot['history']);return old

    def query_basis(self,choice):
        value=super().query_basis(choice)
        return {**value,'math_version':VERSION,'risk_unit':'AMPLITUDE_GAIN_SQUARED_NORMALIZED_GUIDED_MSE_PROXY',
            'fixed_source_minimum_readout':'D_A_P_C','optional_P_A':self.allow_P_A,
            'current_support_boundary':choice.reason=='MATH_EVENT_SG_SUPPORT_BOUNDARY:D',
            'optimizer_selected_D':choice.reason.startswith('MATH_EVENT_SG_H') and choice.action=='D',
            'future_support_grid_same_as_execution':True,'D_A_rule_is_learned':False}
