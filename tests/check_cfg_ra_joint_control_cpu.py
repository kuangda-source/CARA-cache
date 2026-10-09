"""Independent vector geometry and deployment-history tests; synthetic only."""
import dataclasses
import json
import math
from pathlib import Path
import random
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.cfg_ra_joint_control import Calibration, JointCDController, guided_proxy


def denied(call):
    try:call()
    except ValueError:return
    raise AssertionError('Invalid protocol or causal state accepted')


def main():
    rng=random.Random(87120)
    # Compute direct vector errors independently of the scalar controller.
    comparisons=0
    for _ in range(1000):
        ec=[rng.gauss(0,1) for i in range(5)];eu=[rng.gauss(0,1) for i in range(5)]
        a=math.sqrt(math.fsum(v*v for v in ec));b=math.sqrt(math.fsum(v*v for v in eu))
        rho=math.fsum(c*u for c,u in zip(ec,eu))/(a*b)
        exact=math.sqrt(math.fsum((8*c-7*u)**2 for c,u in zip(ec,eu)))
        assert math.isclose(guided_proxy(a,b,rho),exact,rel_tol=1e-12,abs_tol=1e-12)
        comparisons+=1
    assert guided_proxy(7,8,1)==0
    assert guided_proxy(0,1,-1)==7 and guided_proxy(1,0,1)==8
    for values in [(-1,1,0),(1,1,1.001),(1,1,float('nan')),(1,float('inf'),0),(True,1,0)]:
        denied(lambda values=values:guided_proxy(*values))
    rho={(1,2):1.,(1,3):1.,(3,4):1.};gains={2:2.,3:2.,4:2.}
    cal=Calibration('SYNTHETIC_TEST_NOT_PRODUCTION',rho,gains)
    rho[(1,2)]=-1;gains[2]=100
    assert cal.rho_at[(1,2)]==1 and cal.gains[2]==2
    denied(lambda:dataclasses.replace(cal,model_family='Wan'))
    denied(lambda:dataclasses.replace(cal,guided_weights=(7,-6)))
    denied(lambda:dataclasses.replace(cal,rho_at={(1,2):1.01}))
    denied(lambda:dataclasses.replace(cal,gains={2:-1}))
    policy=JointCDController(cal,threshold=3.)
    policy.commit_protected_dense(1,actual_action='DD',pair_completed=True)
    packets=lambda step:[SimpleNamespace(slot=i,counter=2*(step-1)%70+i,delta_y=1.) for i in (0,1)]
    def fingerprint(p):return (p.anchor,p.accumulated,p.last_completed_step,p.generation,tuple(p.history))
    before=fingerprint(policy);d2=policy.decide(2,packets(2),both_sources_ready=True)
    assert d2.action=='CC' and d2.local_proxy==1 and d2.added_risk==2
    assert fingerprint(policy)==before
    assert policy.decide(2,packets(2),both_sources_ready=True)==d2
    policy.commit(d2,actual_action='CC',pair_completed=True)
    assert policy.anchor==1 and policy.accumulated==2
    before=fingerprint(policy)
    denied(lambda:policy.commit(d2,actual_action='CC',pair_completed=True))
    assert fingerprint(policy)==before
    d3=policy.decide(3,packets(3),both_sources_ready=True)
    assert d3.action=='DD' and fingerprint(policy)==before
    policy.commit(d3,actual_action='DD',pair_completed=True)
    assert policy.anchor==3 and policy.accumulated==0
    d4=policy.decide(4,packets(4),both_sources_ready=True)
    assert d4.action=='CC';policy.commit(d4,actual_action='CC',pair_completed=True)
    d5=policy.decide(5,packets(5),both_sources_ready=True)
    assert d5.action=='DD' and d5.reason=='missing_current_calibration'
    policy.commit(d5,actual_action='DD',pair_completed=True)
    denied(lambda:policy.decide(7,packets(7),both_sources_ready=True))
    # Actual sampler n continues while WC's pair counter wraps at n=36.
    for step in range(6,36):policy.commit_protected_dense(step,actual_action='DD',pair_completed=True)
    d36=policy.decide(36,packets(36),both_sources_ready=True)
    assert d36.step==36 and d36.action=='DD'
    policy.commit(d36,actual_action='DD',pair_completed=True)
    assert policy.anchor==36 and policy.last_completed_step==36 and len(policy.history)==36
    denied(lambda:policy.decide(1,packets(1),both_sources_ready=True))
    # A failed pair cannot accidentally reset dense history or keep running.
    p=JointCDController(cal,3.);p.commit_protected_dense(1,actual_action='DD',pair_completed=True)
    before=fingerprint(p);d=p.decide(2,packets(2),both_sources_ready=True)
    denied(lambda:p.commit(d,actual_action='CC',pair_completed=False))
    assert fingerprint(p)==before and p.poisoned
    denied(lambda:p.decide(2,packets(2),both_sources_ready=True))
    p=JointCDController(cal,3.);p.commit_protected_dense(1,actual_action='DD',pair_completed=True)
    before=fingerprint(p);d=p.decide(2,packets(2),both_sources_ready=True)
    denied(lambda:p.commit(d,actual_action='CD',pair_completed=True))
    assert fingerprint(p)==before and p.poisoned
    # Branch order/counter errors fall back before any branch continuation.
    p=JointCDController(cal,3.);p.commit_protected_dense(1,actual_action='DD',pair_completed=True)
    bad=packets(2);bad.reverse()
    d=p.decide(2,bad,both_sources_ready=True)
    assert d.action=='DD' and d.reason=='invalid_paid_branch_pair'
    threshold_policy=JointCDController(cal,2.)
    threshold_policy.commit_protected_dense(1,actual_action='DD',pair_completed=True)
    assert threshold_policy.decide(2,packets(2),both_sources_ready=True).action=='CC'
    print(json.dumps({'status':'RA_JOINT_CONTROLLER_GEOMETRY_AND_CAUSAL_CPU_PASS_SYNTHETIC',
        'independent_direct_vector_comparisons':comparisons,'full36_counter_wrap_history_checked':True,
        'score_only_state_unchanged':True,'failed_pair_poison_and_no_false_anchor_update':True,
        'strict_current_model_cfg_solver_contract_checked':True,'actual_Cosmos_calibration_generated':False,
        'production_policy_installed':False,'new_GPU_submissions':0}))


if __name__=='__main__':main()
