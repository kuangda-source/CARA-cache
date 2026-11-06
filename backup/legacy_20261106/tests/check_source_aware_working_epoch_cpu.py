"""Complete pure-policy controls for the registered working-P hypothesis."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhaseCPDController,CreationPhasePrior
from wcomr.source_aware_working_epoch_control import WorkingEpochCPDController,STRATEGIES,DERIVATION_PROOF


def make_calibration():
    return Calibration('synthetic_working_age_six_only',
        {(a,t):.98 for a in range(1,36) for t in range(a+1,min(a+6,35)+1)},
        {t:.05 for t in range(1,37)})


def run(controller,pattern):
    states=[];queries=[];restored_P=0
    for step in range(1,37):
        if step<=7 or step==36:
            controller.commit_protected_dense(step,actual_action='D',pair_completed=True)
        else:
            value=pattern(step)
            packets=[SimpleNamespace(slot=b,counter=(2*(step-1)+b)%70,delta_y=value)
                     for b in (0,1)]
            d=controller.decide(step,packets,both_sources_ready=True,partial_ready=True)
            if isinstance(controller,WorkingEpochCPDController):queries.append(controller.query_basis(d))
            old_anchor=controller.anchor
            controller.commit(d,actual_action=d.action,pair_completed=True)
            if d.action=='P':
                assert controller.anchor==old_anchor and controller.working_step==step
                assert controller.working_kind=='P' and controller.creation_floor>0
                if isinstance(controller,WorkingEpochCPDController) and controller.strategy==STRATEGIES[1]:
                    assert controller.accumulated==d.added_risk>0
                snap=controller.state_dict();controller.accumulated+=.01
                controller.restore(snap);assert controller.state_dict()==snap;restored_P+=1
        states.append(controller._state())
    assert len(controller.history)==36 and controller.last_completed_step==36
    snap=controller.state_dict();controller.accumulated+=.01
    controller.restore(snap);assert controller.state_dict()==snap
    return {'actions':[d.action for d in controller.history], 'states':states,
            'queries':queries,'P_snapshot_restores':restored_P}


def main():
    cal=make_calibration();cost=Costs('synthetic_incremental_only',.01,1.,.6)
    prior=CreationPhasePrior('synthetic_nonzero_birth',.01,.1,
        early_creation_floor=.005,late_creation_floor=.02)
    patterns=[lambda t:.01, lambda t:1.,lambda t:1. if t%5==3 else .01,
              lambda t:.15 if t<25 else .7]
    complete_paths=0
    for pattern in patterns:
        original=CreationPhaseCPDController(cal,.16,cost,None)
        expected=run(original,pattern);complete_paths+=1
        for strategy in STRATEGIES:
            c=WorkingEpochCPDController(cal,.16,cost,None,strategy=strategy)
            actual=run(c,pattern);complete_paths+=1
            assert actual['actions']==expected['actions'] and actual['states']==expected['states']
            for a,b in zip(c.history,original.history):assert replace(a,owner=b.owner)==b
    results=[];P_restores=0;source_transfer_queries=0
    for pattern_id,pattern in enumerate(patterns[1:3]):
        controllers=[('LEGACY_D_AGE_KEEP_INTERVAL',CreationPhaseCPDController(cal,.16,cost,prior))]
        controllers += [(s,WorkingEpochCPDController(cal,.16,cost,prior,strategy=s)) for s in STRATEGIES]
        for name,c in controllers:
            result=run(c,pattern);complete_paths+=1
            assert 'P' in result['actions'] and 'D' in result['actions'] and 'C' in result['actions']
            transferred=[q for q in result['queries'] if q['working_source_kind']=='P']
            for q in transferred:
                assert q['query_anchor']==q['working_source_step'] and q['true_D_anchor']<q['query_anchor']
                assert q['rho_source']=='D_ONLY_PRIOR_TRANSFERRED_TO_WORKING_P_AGE'
                assert not q['P_future_drift_empirically_calibrated']
            source_transfer_queries+=len(transferred);P_restores+=result['P_snapshot_restores']
            results.append({'pattern':pattern_id,'strategy':name,'full36_actions':result['actions'],
                'P_source_queries':len(transferred),'P_snapshot_restores':result['P_snapshot_restores']})
    assert complete_paths==18 and source_transfer_queries>0 and P_restores>0
    # Strategy and incomplete-pair failures are part of the actual control contract.
    refused=[]
    c=WorkingEpochCPDController(cal,.16,cost,prior,strategy=STRATEGIES[1]);run(c,patterns[1])
    bad=copy.deepcopy(c.state_dict());bad['binding']=bad['binding'][:-1]+(STRATEGIES[0],)
    try:c.restore(bad)
    except ValueError:refused.append('changed_strategy_snapshot')
    else:raise AssertionError('changed strategy accepted')
    bad=copy.deepcopy(c.state_dict());bad['state']=bad['state'][:4]+(.05,)+bad['state'][5:]
    try:c.restore(bad)
    except ValueError:refused.append('changed_interval_history')
    else:raise AssertionError('changed interval accepted')
    failed=WorkingEpochCPDController(cal,.16,cost,prior)
    try:failed.commit_protected_dense(1,actual_action='D',pair_completed=False)
    except ValueError:refused.append('incomplete_pair')
    else:raise AssertionError('incomplete pair accepted')
    assert failed.poisoned
    print(json.dumps({'status':'WORKING_P_AGE_AND_NONZERO_REBASE_PURE_POLICY_CPU_PASS_SYNTHETIC',
        'complete_policy_paths':18,'complete36_updates':648,'no_P_exact_legacy_controls':12,
        'complete_P_source_controls':6,'all_P_histories_retained_and_true_D_anchor_unchanged':True,
        'source_transfer_queries':source_transfer_queries,'P_snapshot_restores':P_restores,
        'derivation_proof':DERIVATION_PROOF,'P_controls':results,'contract_refusals':refused,
        'actual_model_or_future_P_calibration_or_video_result':False,'GPU_submissions':0,'ledger_written':False}))


if __name__=='__main__':main()
