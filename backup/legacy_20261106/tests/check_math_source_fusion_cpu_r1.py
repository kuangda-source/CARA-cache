"""Independent scalar-vector checks of fusion and event-allocation contracts."""
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.math_source_fusion_r1 import (fusion_gain,fusion_risk,cfg_risk,
                                        fuse_outputs,EstimateState,event_decision)

def run():
    checks=[]
    old=(1.,1.);working=(-1.,1.)
    A=sum(x*x for x in old);B=sum(x*x for x in working);C=sum(x*y for x,y in zip(old,working))
    g=fusion_gain(A,B,C)['gamma'];assert g==.5
    for value in (0.,.5,1.):
        actual=sum(((1-value)*x+value*y)**2 for x,y in zip(old,working))
        assert actual==fusion_risk(A,B,C,value)
    checks.append('QUADRATIC_INDEPENDENT_VECTOR_AND_INTERIOR_OPTIMUM')
    assert fusion_gain(4.,1.,1.5)['gamma']==1.
    checks.append('CORRELATED_GAIN_DIFFERS_FROM_INDEPENDENT_NOISE_FORMULA')
    assert fusion_gain(3.,3.,3.)['gamma']==0.
    checks.append('IDENTICAL_PREDICTIONS_USE_OLD_REFERENCE')
    assert cfg_risk(49.,64.,56.)==0.
    assert cfg_risk(1.,1.,1.)==1.
    checks.append('CFG_8_MINUS7_CROSS_TERM_PRESERVED')
    assert fuse_outputs(old,working,0.) is old and fuse_outputs(old,working,1.) is working
    assert fuse_outputs(old,working,.5)==(0.,1.)
    checks.append('EXACT_GAIN_ENDPOINTS_AND_SHARED_BRANCH_GAIN')
    for args in ((1.,1.,2.),(float('nan'),1.,0.),(1.,1.,float('inf'))):
        try:fusion_gain(*args)
        except ValueError:pass
        else:raise AssertionError('Invalid moments accepted')
    checks.append('INVALID_MOMENTS_REFUSED')
    s=EstimateState('D',8,8,0.,paid_cost=7.)
    p=s.after('P',.8,.1);assert p.source=='P' and p.source_age==1 and p.true_D_age==9 and p.paid_cost==7.8
    d=p.after('D',1.,.1);assert d.source=='D' and d.source_floor==0 and d.paid_cost==8.8
    checks.append('P_TRUE_D_CLOCKS_AND_PAID_HISTORY_REMAIN_SEPARATE')
    try:s.after('P',.8,0.)
    except ValueError:pass
    else:raise AssertionError('P mislabeled zero-error D')
    checks.append('ZERO_BIRTH_P_REFUSED')
    # A deliberately constructed estimate problem, not video evidence.
    def risk(state,action,step):
        if action=='D':return 0.
        return .4 if state.source_age==8 else (1.2 if state.source_age>8 else .01)
    kw=dict(step=10,costs={'C':.2,'D':1.},risk=risk,weight=1.,P_floor=.1)
    h1=event_decision(s,horizon=1,**kw);h2=event_decision(s,horizon=2,**kw)
    assert h1['action']=='C' and h2['action']=='D' and h2['sequence']==['D','C']
    assert h1['actual_candidate_computations']==h2['actual_candidate_computations']==0
    checks.append('H2_USES_SOURCE_VALUE_WITHOUT_REAL_CANDIDATE_COMPUTATION')
    assert s.paid_cost==7. and s.source_age==8
    checks.append('PLANNING_DOES_NOT_MUTATE_DEPLOYMENT_STATE')
    return {'status':'MATH_FUSION_AND_H1_H2_NUMERICAL_CPU_PASS_NOT_GPU','checks':checks,
            'GPU_submissions':0,'generator_calls':0,'video_or_method_benefit_claim':False}

if __name__=='__main__':
    import json
    print(json.dumps(run()))
