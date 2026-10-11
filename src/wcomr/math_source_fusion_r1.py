"""Related-error output fusion and small cost/risk look-ahead primitives.

No teacher, generator, online fitting, probability guarantee or latent reset.
The fusion quadratic applies in this linear output space, not before a head.
"""
import math
from dataclasses import dataclass
from itertools import product


def fusion_gain(A, B, C, *, epsilon=1e-12):
    if (any(not math.isfinite(x) for x in (A,B,C,epsilon)) or min(A,B)<0 or epsilon<=0
            or C*C>A*B+epsilon*max(1.,A*B)):
        raise ValueError('Finite positive-semidefinite related-error moments required')
    denominator=A+B-2*C
    if denominator<=epsilon*max(1.,A+B):
        return {'gamma':0.,'status':'DEGENERATE_USE_OLD_REFERENCE','denominator':denominator}
    return {'gamma':max(0.,min(1.,(A-C)/denominator)),
            'status':'CONSTRAINED_RELATED_ERROR_MINIMUM','denominator':denominator}


def fusion_risk(A,B,C,gamma):
    if not math.isfinite(gamma) or not 0<=gamma<=1:raise ValueError('Bounded shared gain required')
    fusion_gain(A,B,C)
    return max(0.,(1-gamma)**2*A+gamma**2*B+2*gamma*(1-gamma)*C)


def cfg_risk(conditional,unconditional,cross):
    fusion_gain(conditional,unconditional,cross)
    return max(0.,64*conditional+49*unconditional-112*cross)


def fuse_outputs(old,working,gamma):
    if not math.isfinite(gamma) or not 0<=gamma<=1:raise ValueError('Bounded shared gain required')
    if gamma==0:return old
    if gamma==1:return working
    if len(old)!=2 or len(working)!=2:raise ValueError('Both CFG branches required')
    return tuple(a+gamma*(b-a) for a,b in zip(old,working))


@dataclass(frozen=True)
class EstimateState:
    source: str
    source_age: int
    true_D_age: int
    source_floor: float
    paid_cost: float=0.

    def __post_init__(self):
        if (self.source not in ('D','P') or min(self.source_age,self.true_D_age)<0
                or self.true_D_age<self.source_age or self.source_floor<0 or self.paid_cost<0
                or not math.isfinite(self.source_floor+self.paid_cost)
                or (self.source=='D' and (self.source_floor!=0 or self.true_D_age!=self.source_age))):
            raise ValueError('Consistent source estimate and separate true-D clock required')

    def after(self,action,cost,P_floor):
        if not math.isfinite(cost) or cost<0:raise ValueError('Real positive cost required')
        if action=='D':return EstimateState('D',1,1,0.,self.paid_cost+cost)
        if action=='P':
            if P_floor<=0 or not math.isfinite(P_floor):raise ValueError('P is never a zero-error D')
            return EstimateState('P',1,self.true_D_age+1,P_floor,self.paid_cost+cost)
        if action not in ('C','A'):raise ValueError('One registered action required')
        return EstimateState(self.source,self.source_age+1,self.true_D_age+1,
                             self.source_floor,self.paid_cost+cost)


def event_decision(state,*,step,horizon,costs,risk,weight,P_floor,partial_ready=True):
    """Only low-dimensional risk predictions; execute no real candidate here.

    risk(state,action,step) returns a deployable squared-error estimate.
    It must not call a generator or inspect an unobserved future measurement.
    """
    if horizon not in (1,2) or weight<=0 or not math.isfinite(weight):
        raise ValueError('Frozen H1/H2 and positive seconds-per-error weight required')
    actions=tuple(a for a in ('C','A','P','D') if a in costs and (a!='P' or partial_ready))
    if 'D' not in actions:raise ValueError('Dense fallback and explicit costs required')
    plans=[]
    for sequence in product(actions,repeat=horizon):
        s=state;objective=0.;terms=[]
        for offset,action in enumerate(sequence):
            q=risk(s,action,step+offset);c=costs[action]
            if min(q,c)<0 or not math.isfinite(q+c):raise ValueError('Finite squared-error and cost required')
            objective+=c+weight*q;terms.append({'action':action,'cost':c,'squared_error_proxy':q})
            s=s.after(action,c,P_floor)
        plans.append((objective,sequence,terms,s))
    # Deterministic tie handling, no teacher/endpoint-based tie breaking.
    best=min(plans,key=lambda p:(p[0],p[1]))
    return {'action':best[1][0],'sequence':list(best[1]),'objective':best[0],
            'terms':best[2],'plans_evaluated':len(plans),'simulated_final_state':best[3],
            'actual_candidate_computations':0,'history_cost_before':state.paid_cost}
