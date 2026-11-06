"""Support, squared gain, action coverage and healthy/poisoned restore."""
import copy,math,random
from dataclasses import replace
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.supported_source_gate_control_r1 import SupportedGateController

def run():
    cal=Calibration('DECLARED_AGE6',{(a,n):.99 for a in range(1,36)
        for n in range(a+1,min(a+6,36)+1)},{n:2. for n in range(1,37)})
    base={'fingerprint':'DECLARED_SCALAR_ONLY','gamma':.5,'lambda_seconds_per_normalized_error':1.,
        'A_pair_cost_seconds':.4,'source_A_cost_seconds':{'D':.3,'P':.4},
        'source':{'D':{'C_scale':1.,'A_over_C':.9},'P':{'C_scale':2.,'A_over_C':.1}}}
    costs=Costs('DECLARED',.2,4.,1.)
    prior=CreationPhasePrior('DECLARED',.01,.3,early_creation_floor=.01,late_creation_floor=.02)
    make=lambda h=1,pa=False,p=base:SupportedGateController(cal,2.,costs,prior,
        strategy='WORKING_P_AGE_NONZERO_REBASE',math_parameters=p,horizon=h,sigma_at=lambda n:float(37-n),allow_P_A=pa)
    packets=lambda n,x:((0,2*(n-1)%70,x),(1,2*(n-1)%70+1,x))
    c=make();d=c._choice(1,(),False,False,True);c.commit(d,actual_action='D',pair_completed=True)
    d=c._choice(2,packets(2,.001),True,True)
    assert d.reason.endswith(':A') and d.candidates[0][1]==.3
    assert math.isclose(d.added_risk,4*d.local_proxy**2*.9,rel_tol=1e-12)
    c.commit(d,actual_action=d.action,pair_completed=True)
    # A supported age-six prefix explicitly forecasts the next forced D.
    for n in range(3,7):
        d=c._choice(n,packets(n,.001),True,True);c.commit(d,actual_action=d.action,pair_completed=True)
    h2=make(2)
    for old in c.history:
        d=h2._choice(old.step,old.packets,old.both_sources_ready,old.partial_ready,old.reason=='actual_protected_dense')
        h2.commit(d,actual_action=d.action,pair_completed=True)
    d=h2._choice(7,packets(7,.001),True,True)
    assert d.reason.endswith(':P') and d.candidates[1][0]=='C'
    without_P=h2._choice(7,packets(7,.001),True,False)
    assert without_P.reason.endswith(':D') and without_P.candidates[1][0]=='A'
    current=c._choice(7,packets(7,.001),True,True);assert current.reason.endswith(':A')
    c.commit(current,actual_action=current.action,pair_completed=True)
    d=c._choice(8,packets(8,.001),True,True)
    assert d.reason=='MATH_EVENT_SG_SUPPORT_BOUNDARY:D' and d.action=='D'
    # Real optimizer-selected D, source P-C and optional P-A in declared regimes.
    high={**base,'lambda_seconds_per_normalized_error':1e8}
    c=make(p=high);c.commit_protected_dense(1,actual_action='D',pair_completed=True)
    d=c._choice(2,packets(2,1.),True,False);assert d.reason.endswith(':D')
    for pa,want in ((False,'C'),(True,'A')):
        p={**base,'lambda_seconds_per_normalized_error':100.}
        c=make(pa=pa,p=p);c.commit_protected_dense(1,actual_action='D',pair_completed=True)
        d=c._choice(2,packets(2,1.),True,True);assert d.action=='P'
        c.commit(d,actual_action='P',pair_completed=True)
        d=c._choice(3,packets(3,.01),True,True);assert d.reason.endswith(':'+want)
        if pa:assert d.candidates[0][1]==.4
    # All ordinary steps, exact replay and negative provenance controls.
    before=random.getstate();c=make(2,True)
    for n in range(1,37):
        d=c._choice(n,packets(n,.02),n>7,n>7,protected=n<=7 or n==36)
        c.commit(d,actual_action=d.action,pair_completed=True)
    snapshot=c.state_dict();c.accumulated=999;c.restore(snapshot);assert c.state_dict()==snapshot
    for bad in (dict(snapshot,binding=()),dict(snapshot,history=[replace(snapshot['history'][0],owner=-1)]+snapshot['history'][1:])):
        try:c.restore(bad)
        except ValueError:pass
        else:raise AssertionError('Foreign history accepted')
    broken=make();d=broken._choice(1,(),False,False,True)
    try:broken.commit(d,actual_action='D',pair_completed=False)
    except ValueError:pass
    assert broken.poisoned and random.getstate()==before
    return {'status':'SUPPORTED_GATE_SCALAR_CPU_PASS','age6_future_boundary':'D',
        'squared_gain_exact':True,'D_A_fixed_rule_not_learned':True,'optimizer_D_exercised':True,
        'optional_P_A_exercised_in_declared_regime':True,'full36_restore_pass':True,
        'GPU_submissions':0,'online_teacher_calls':0,'RNG_unchanged':True}

if __name__=='__main__':
    import json;print(json.dumps(run()))
