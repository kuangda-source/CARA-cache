"""Full36 constant/no-P controls and actual creation-boundary state invariants."""
import copy
from dataclasses import replace
from types import SimpleNamespace

from wcomr.cfg_ra_joint_control import Calibration, JointCDController
from wcomr.source_aware_cpd_control import Costs, PartialPrior, SourceAwareCPDController
from wcomr.source_aware_phase_control import CreationPhasePrior, CreationPhaseCPDController, DERIVATION_PROOFS


def packets(step, delta):
    return [SimpleNamespace(slot=slot,counter=(2*(step-1)+slot)%70,delta_y=delta) for slot in (0,1)]


def run():
    cal=Calibration('SYNTHETIC_CREATION_PHASE_PURE_CPU',
        {(a,t):1. for a in range(1,36) for t in range(a+1,37)}, {t:1. for t in range(1,37)})
    comparisons=0
    for case,(c,p,d,threshold) in enumerate([(1.,1.5,4.,.15),(1.7,1.6,4.,.2),(2.,3.,1.,.1),(1.,1.2,4.,.07)]):
        costs=Costs('SYNTHETIC_CASE_'+str(case),C=c,P=p,D=d)
        oldprior=PartialPrior('CONSTANT_PRIOR_'+str(case),.03,.2)
        phaseprior=CreationPhasePrior('CONSTANT_PRIOR_'+str(case),.03,.2,
            early_creation_floor=.03,late_creation_floor=.03)
        old=SourceAwareCPDController(cal,threshold,costs,oldprior)
        new=CreationPhaseCPDController(cal,threshold,costs,phaseprior)
        for step in range(1,37):
            if step in (1,36):
                for controller in (old,new):controller.commit_protected_dense(step,actual_action='D',pair_completed=True)
            else:
                values=packets(step,.2 if step in (8,18,29) else .01*(case+1))
                a=old.decide(step,values,both_sources_ready=True,partial_ready=True)
                b=new.decide(step,values,both_sources_ready=True,partial_ready=True)
                assert a==replace(b,owner=id(old))
                old.commit(a,actual_action=a.action,pair_completed=True)
                new.commit(b,actual_action=b.action,pair_completed=True)
            assert old._state()==new._state()
            comparisons+=1
    no_P=0
    for threshold in (.02,.11):
        old=JointCDController(cal,threshold);new=CreationPhaseCPDController(cal,threshold,Costs('NO_P',C=1.,D=4.))
        for step in range(1,37):
            if step in (1,36):
                old.commit_protected_dense(step,actual_action='DD',pair_completed=True)
                new.commit_protected_dense(step,actual_action='D',pair_completed=True)
            else:
                values=packets(step,.025)
                a=old.decide(step,values,both_sources_ready=True)
                b=new.decide(step,values,both_sources_ready=True,partial_ready=False)
                assert b.action=={'CC':'C','DD':'D'}[a.action]
                old.commit(a,actual_action=a.action,pair_completed=True);new.commit(b,actual_action=b.action,pair_completed=True)
            assert old.anchor==new.anchor and old.accumulated==new.accumulated
            no_P+=1
    prior=CreationPhasePrior('BOUNDARY_TEST',.05,.1,early_creation_floor=.01,late_creation_floor=.09)
    early=CreationPhaseCPDController(cal,.1,Costs('BOUNDARY',C=1.,P=1.5,D=4.),prior)
    for step in range(1,24):early.commit_protected_dense(step,actual_action='D',pair_completed=True)
    choice=early.decide(24,packets(24,.2),both_sources_ready=True,partial_ready=True)
    assert choice.action=='P' and choice.predicted_creation_floor==.01
    early.commit(choice,actual_action='P',pair_completed=True)
    before=copy.deepcopy(early.state_dict())
    choice=early.decide(25,packets(25,.005),both_sources_ready=True,partial_ready=True)
    assert early.state_dict()==before and choice.action=='C' and choice.predicted_creation_floor==.01
    early.commit(choice,actual_action='C',pair_completed=True)
    assert early.creation_floor==.01 and early.anchor==23 and early.working_step==24
    saved=early.state_dict()
    choice=early.decide(26,packets(26,.2),both_sources_ready=True,partial_ready=True)
    assert choice.action=='D';early.commit(choice,actual_action='D',pair_completed=True)
    assert early.creation_floor==early.accumulated==0
    early.restore(saved);assert early.state_dict()==saved
    late=CreationPhaseCPDController(cal,.14,Costs('BOUNDARY',C=1.,P=1.5,D=4.),prior)
    for step in range(1,26):late.commit_protected_dense(step,actual_action='D',pair_completed=True)
    choice=late.decide(26,packets(26,.2),both_sources_ready=True,partial_ready=True)
    assert choice.action=='P' and choice.predicted_creation_floor==.09
    late.commit(choice,actual_action='P',pair_completed=True);assert late.creation_floor==.09 and late.anchor==25
    prior2=CreationPhasePrior('CONSECUTIVE',.01,.1,early_creation_floor=.01,late_creation_floor=.02)
    seq=CreationPhaseCPDController(cal,.25,Costs('P_CHEAPER',C=3.,P=1.,D=4.),prior2)
    seq.commit_protected_dense(1,actual_action='D',pair_completed=True)
    for step in (2,3):
        choice=seq.decide(step,packets(step,.02),both_sources_ready=True,partial_ready=True)
        assert choice.action=='P';seq.commit(choice,actual_action='P',pair_completed=True)
    assert seq.consecutive_P==2
    choice=seq.decide(4,packets(4,.02),both_sources_ready=True,partial_ready=True)
    assert choice.action=='C';seq.commit(choice,actual_action='C',pair_completed=True)
    rejects=0
    def refused(fn):
        nonlocal rejects
        try:fn()
        except ValueError:rejects+=1
        else:raise AssertionError('Modified phase state or failed pair accepted')
    invalid=copy.deepcopy(saved);state=list(invalid['state']);state[3]=.77;invalid['state']=tuple(state)
    refused(lambda:early.restore(invalid));assert early.state_dict()==saved
    choice=early.decide(26,packets(26,.01),both_sources_ready=True,partial_ready=True)
    refused(lambda:early.commit(replace(choice,predicted_creation_floor=.9),actual_action=choice.action,pair_completed=True))
    refused(lambda:late.commit(late.decide(27,packets(27,.001),both_sources_ready=True,partial_ready=True),actual_action='D',pair_completed=False))
    assert late.poisoned
    refused(lambda:late.decide(27,packets(27,.001),both_sources_ready=True,partial_ready=True))
    refused(lambda:CreationPhasePrior('BAD',.05,.1,early_creation_floor=.01,late_creation_floor=.02,boundary=26))
    refused(lambda:CreationPhasePrior('BAD',.05,.1,early_creation_floor=0.,late_creation_floor=.02))
    return {'status':'CREATION_PHASE_PURE_CPU_PASS_NOT_FULL_SAMPLER_OR_VIDEO',
        'constant_phase_complete_full36_paths':4,'constant_phase_step_comparisons':comparisons,
        'no_P_complete_full36_paths':2,'original_RA_step_comparisons':no_P,
        'total_complete_policy_steps':comparisons+no_P,'actual_creation_phase_preserved_across_boundary':True,
        'healthy_phase_snapshot_replayed':True,'only_actual_D_resets':True,'invalid_or_failed_cases_refused':rejects,
        'derivation_proofs':DERIVATION_PROOFS,'synthetic_quality_and_cost_parameters':True,
        'new_GPU_submissions':0,'ordinary_full_sampler_or_real_model_or_video_claim':False}


if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=run()
    if args.output:
        assert not args.output.exists();args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
