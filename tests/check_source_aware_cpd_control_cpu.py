"""Independent source-aware action arithmetic and transactions; synthetic CPU."""
from dataclasses import replace
import copy
import json
import math
from pathlib import Path
import random
import sys
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.cfg_ra_joint_control import Calibration, JointCDController
from wcomr.source_aware_cpd_control import Costs, PartialPrior, SourceAwareCPDController


def denied(call):
    try: call()
    except ValueError: return
    raise AssertionError('Invalid source or transaction accepted')


def packets(step,value):
    return [SimpleNamespace(slot=b,counter=2*(step-1)%70+b,delta_y=value) for b in (0,1)]


def main():
    cal=Calibration('SYNTHETIC_NOT_COSMOS_CALIBRATION',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},
        {s:1. for s in range(1,37)})
    costs=Costs('SYNTHETIC_COMPLETE_PAIR_COSTS',1.,4.,2.)
    prior=PartialPrior('SYNTHETIC_SAME_PROXY_UNIT_FLOOR',.1,.2)
    comparisons=0
    # Four complete sequences, including exact threshold, burst and zero drift.
    for values in ([.4]*35,[0.]*35,[.2,1.,.01,.7,.3]*7,[.5]*35):
        old=JointCDController(cal,threshold=1.)
        new=SourceAwareCPDController(cal,1.,costs)
        old.commit_protected_dense(1,actual_action='DD',pair_completed=True)
        new.commit_protected_dense(1,actual_action='D',pair_completed=True)
        for step,value in enumerate(values,2):
            a=old.decide(step,packets(step,value),both_sources_ready=True)
            b=new.decide(step,packets(step,value),both_sources_ready=True,partial_ready=True)
            assert b.action=={'CC':'C','DD':'D'}[a.action]
            old.commit(a,actual_action=a.action,pair_completed=True)
            new.commit(b,actual_action=b.action,pair_completed=True)
            assert (new.anchor,new.accumulated)==(old.anchor,old.accumulated)
            comparisons+=1
        assert len(new.history)==36 and new.last_completed_step==36
    # A P can be feasible while C is infeasible. P retains nonzero source
    # uncertainty and the already accumulated interval score.
    p=SourceAwareCPDController(cal,1.,costs,prior)
    p.commit_protected_dense(1,actual_action='D',pair_completed=True)
    d=p.decide(2,packets(2,.5),both_sources_ready=True,partial_ready=True)
    assert d.action=='C';p.commit(d,actual_action='C',pair_completed=True)
    before=p.state_dict(); rng_before=random.getstate()
    d=p.decide(3,packets(3,1.),both_sources_ready=True,partial_ready=True)
    assert d.action=='P' and math.isclose(d.added_risk,.3)
    assert p.state_dict()==before and random.getstate()==rng_before
    assert p.decide(3,packets(3,1.),both_sources_ready=True,partial_ready=True)==d
    denied(lambda:p.commit(replace(d,added_risk=0.),actual_action='P',pair_completed=True))
    assert p.state_dict()==before
    p.commit(d,actual_action='P',pair_completed=True)
    assert p.anchor==1 and p.working_kind=='P' and p.working_step==3
    assert p.creation_floor==.1 and math.isclose(p.accumulated,.8)
    assert p.last_completed_step-p.working_step==0 and p.creation_floor>0
    # Two successive P are allowed but a third forces the feasible dense
    # alternative. Its score can stay above zero despite zero paid drift.
    p=SourceAwareCPDController(cal,10.,Costs('SYNTHETIC_P_CHEAPER',3.,4.,1.),prior)
    p.commit_protected_dense(1,actual_action='D',pair_completed=True)
    for step in (2,3):
        d=p.decide(step,packets(step,1.),both_sources_ready=True,partial_ready=True)
        assert d.action=='P';p.commit(d,actual_action='P',pair_completed=True)
    assert p.anchor==1 and math.isclose(p.accumulated,.6) and p.consecutive_P==2
    d=p.decide(4,packets(4,0.),both_sources_ready=True,partial_ready=True)
    assert d.action=='C' and math.isclose(d.added_risk,.1)
    p.commit(d,actual_action='C',pair_completed=True)
    assert p.working_step==3 and p.anchor==1 and p.creation_floor==.1
    assert math.isclose(p.accumulated,.7) and p.consecutive_P==0
    checkpoint=p.state_dict()
    p.commit_protected_dense(5,actual_action='D',pair_completed=True)
    assert p.anchor==5 and p.creation_floor==p.accumulated==0
    p.restore(checkpoint);assert p.state_dict()==checkpoint
    bad=copy.deepcopy(checkpoint);bad['state']=tuple(0 if i==3 else v for i,v in enumerate(bad['state']))
    denied(lambda:p.restore(bad));assert p.state_dict()==checkpoint
    bad=copy.deepcopy(checkpoint);bad['binding']=('OTHER',)+bad['binding'][1:]
    denied(lambda:p.restore(bad));assert p.state_dict()==checkpoint
    denied(lambda:p.commit(d,actual_action='C',pair_completed=True))
    # No assumed cost hierarchy: a faster D really is chosen.
    fast=SourceAwareCPDController(cal,100.,Costs('SYNTHETIC_FAST_D',3.,1.,2.),prior)
    fast.commit_protected_dense(1,actual_action='D',pair_completed=True)
    assert fast.decide(2,packets(2,.1),both_sources_ready=True,partial_ready=True).action=='D'
    # Missing P quality, cost or physical projection readiness excludes P.
    for pi,co,ready in [(None,costs,True),(prior,Costs('SYNTHETIC_NO_P',1.,4.),True),
                        (prior,costs,False)]:
        p=SourceAwareCPDController(cal,1.,co,pi)
        p.commit_protected_dense(1,actual_action='D',pair_completed=True)
        assert p.decide(2,packets(2,2.),both_sources_ready=True,partial_ready=ready).action=='D'
    denied(lambda:PartialPrior('INVALID_ZERO',0.,.2))
    denied(lambda:PartialPrior('INVALID_UNIT',.1,.2,proxy_definition='GUIDED_VELOCITY_MSE'))
    denied(lambda:Costs('INVALID',float('nan'),1.,2.))
    # Incomplete pair poisons without falsely advancing the source/anchor.
    p=SourceAwareCPDController(cal,10.,costs,prior)
    p.commit_protected_dense(1,actual_action='D',pair_completed=True)
    before=p.state_dict();d=p.decide(2,packets(2,1.),both_sources_ready=True,partial_ready=True)
    denied(lambda:p.commit(d,actual_action=d.action,pair_completed=False))
    assert p.anchor==before['state'][0] and p.generation==before['state'][7] and p.poisoned
    denied(lambda:p.decide(2,packets(2,1.),both_sources_ready=True,partial_ready=True))
    for value in (float('nan'),float('inf'),-1.):
        p=SourceAwareCPDController(cal,1.,costs,prior)
        p.commit_protected_dense(1,actual_action='D',pair_completed=True)
        assert p.decide(2,packets(2,value),both_sources_ready=True,partial_ready=True).action=='D'
    p=SourceAwareCPDController(Calibration('SYNTHETIC_EMPTY',{},{}),1.,costs,prior)
    p.commit_protected_dense(1,actual_action='D',pair_completed=True)
    assert p.decide(2,packets(2,.1),both_sources_ready=True,partial_ready=True).action=='D'
    p=SourceAwareCPDController(cal,1.,costs,prior)
    p.commit_protected_dense(1,actual_action='D',pair_completed=True)
    wrong=packets(2,.1);wrong.reverse()
    assert p.decide(2,wrong,both_sources_ready=True,partial_ready=True).action=='D'
    assert 'torch' not in sys.modules
    print(json.dumps({'status':'SOURCE_AWARE_CPD_SYNTHETIC_CPU_PASS',
        'no_P_complete36_RA_sequence_controls':4,'no_P_exact_decision_state_comparisons':comparisons,
        'P_creation_floor_and_no_interval_reset_checked':True,
        'P_to_C_and_consecutive_P_checked':True,'only_actual_D_resets_anchor':True,
        'inverse_cost_hierarchy_checked':True,'missing_same_unit_P_quality_excludes_P':True,
        'score_only_state_and_RNG_unchanged':True,'restore_replay_and_tamper_refusal_checked':True,
        'incomplete_actual_pair_poison_checked':True,'Torch_imported':False,
        'real_cost_or_quality_parameters_generated':False,'sampler_selector_installed':False,
        'GPU_submissions':0}))


if __name__=='__main__':main()
