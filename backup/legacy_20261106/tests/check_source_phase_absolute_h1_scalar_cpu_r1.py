"""Actual controller: gain-square objective, separate root state, no oracle."""
import copy,json,math
from types import SimpleNamespace
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller,VERSION,fingerprint,validate_parameters


def run():
    def params(P=1.5,ratio=.01):
        cell=lambda:{'status':'FIT','C_scale':100.,'A_ratios':{'FUSION_A':ratio},'actual_NEW_P_birth_mean':.002}
        p={'version':VERSION,'gamma':.5,'table_model':{'grouping':'SOURCE_PHASE','target':'absolute_guided_MSE',
            'current_teacher_energy_is_online_feature':False,'cells':{s+'_'+phase:cell() for s in ('D','P') for phase in ('EARLY','LATE')}},
            'cost_seconds':{'C':.1,'A':.5,'P':P,'D':2.},'source_A_cost_seconds':{'D':.3,'P':.5},
            'lambda_seconds_per_weighted_absolute_MSE':1.}
        p['fingerprint']=fingerprint(p);return p
    def controller(p=None,gain=1.,legacy_C=None):
        p=params() if p is None else p
        cal=Calibration('SYNTHETIC_SOURCE_PHASE_H1',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},
            {n:gain for n in range(1,37)})
        def no_forecast(n):raise AssertionError('H1 consulted future sigma forecast')
        c=SourcePhaseH1Controller(cal,.01,Costs('SYNTHETIC_PRICE_NOT_PRODUCTION',.1 if legacy_C is None else legacy_C,2.,p['cost_seconds']['P']),
            CreationPhasePrior('SYNTHETIC_POSITIVE_ROOT_BIRTH',.01,.3,early_creation_floor=.01,late_creation_floor=.02),
            strategy='WORKING_P_AGE_NONZERO_REBASE',table_parameters=p,math_parameters={'fingerprint':'SYNTHETIC_BASE','gamma':.5},
            horizon=1,sigma_at=no_forecast)
        for n in range(1,8):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
        return c
    def decision(c,n,delta,partial=False):
        packets=[SimpleNamespace(slot=b,counter=(2*(n-1))%70+b,delta_y=delta) for b in (0,1)]
        return c.decide(n,packets,both_sources_ready=True,partial_ready=partial)
    c=controller();d=decision(c,8,.001);assert d.action=='C' and d.reason.endswith(':C')
    c=controller(gain=3.,legacy_C=.3);d=decision(c,8,.1);assert d.action=='C' and d.reason.endswith(':A')
    table=c.predicted_actions(d);assert math.isclose(table['A']['gain_squared_risk'],9*table['A']['absolute_current_MSE'])
    expected_root=3*d.local_proxy;c.commit(d,actual_action='C',pair_completed=True)
    assert math.isclose(c.accumulated,expected_root) and not math.isclose(c.accumulated,table['A']['gain_squared_risk'])
    q=c.query_basis(d);assert q['source_before']=='D' and not q['absolute_error_written_into_root_accumulator']
    assert q['pi0_action_order_prices']['legacy_C_including_stage_A']==.3 and q['H1_semantic_plain_C_price']==.1
    snapshot=c.state_dict();c.accumulated=900.;c.restore(snapshot);assert c.state_dict()==snapshot
    tampered=copy.deepcopy(snapshot);tampered['state']=tuple(99. if i==4 else v for i,v in enumerate(tampered['state']))
    try:c.restore(tampered)
    except ValueError:pass
    else:raise AssertionError('Wrong root state accepted')
    c=controller();d=decision(c,8,1.);assert d.action=='D' and c.query_basis(d)['optimizer_selected_D']
    p=params(P=.11);c=controller(p);d=decision(c,8,1.,True);assert d.action=='P'
    c.commit(d,actual_action='P',pair_completed=True);assert c.anchor==7 and c.working_kind=='P' and c.creation_floor==.01
    assert c.query_basis(d)['source_before']=='D','Post-commit source leaked into current risk model'
    d=decision(c,9,1.,True);assert d.action=='P';c.commit(d,actual_action='P',pair_completed=True)
    d=decision(c,10,1.,True);assert 'P' not in c.predicted_actions(d) and not d.reason.endswith(':P')
    snap=c.state_dict();c.accumulated=0.;c.restore(snap);assert c.state_dict()==snap
    p=params(ratio=2.);c=controller(p);d=decision(c,8,.02);assert not d.reason.endswith(':A')
    table=c.predicted_actions(d);assert table['A']['absolute_current_MSE']>table['C']['absolute_current_MSE']
    c=controller();
    for n in range(8,14):
        d=decision(c,n,.00001);c.commit(d,actual_action=d.action,pair_completed=True)
    d=decision(c,14,.00001);assert d.action=='D' and d.local_proxy is None and d.reason=='missing_current_calibration'
    c.commit(d,actual_action='D',pair_completed=True)
    while c.last_completed_step<36:
        n=c.last_completed_step+1
        if n==36:c.commit_protected_dense(n,actual_action='D',pair_completed=True)
        else:
            d=decision(c,n,.00001);c.commit(d,actual_action=d.action,pair_completed=True)
    assert c.anchor==36 and c.accumulated==0.
    snap=c.state_dict();c.restore(snap);assert c.state_dict()==snap
    unknown=params();unknown['table_model']['cells']['D_EARLY']['status']='UNKNOWN_ZERO_FEATURE_OR_C_TARGET'
    unknown['fingerprint']=fingerprint(unknown);c=controller(unknown)
    d=decision(c,8,.00001);assert d.action=='C' and d.reason=='MATH_EVENT_TABLE_PI0_UNKNOWN_FALLBACK:A'
    refused=[]
    for mutation in ('wrong_units','fingerprint','zero_birth','negative_price'):
        bad=params()
        if mutation=='wrong_units':bad['table_model']['target']='normalized_guided_MSE'
        elif mutation=='fingerprint':bad['fingerprint']='WRONG'
        elif mutation=='zero_birth':bad['table_model']['cells']['P_EARLY']['actual_NEW_P_birth_mean']=0.
        else:bad['cost_seconds']['P']=-1.
        if mutation!='fingerprint':bad['fingerprint']=fingerprint(bad)
        try:validate_parameters(bad)
        except ValueError:refused.append(mutation)
        else:raise AssertionError('Invalid units/binding/price accepted')
    return {'status':'SOURCE_PHASE_ABSOLUTE_H1_ALL_FOUR_ACTIONS_ROOT_VS_SQUARED_GAIN_RESTORE_CPU_PASS_NOT_GPU',
        'all_actual_C_A_P_D_legal_actions_exercised':True,'gain_squared_objective_and_root_pi0_state_separated':True,
        'harmful_A_not_clipped_positive_P_source_true_D_ownership_preserved':True,
        'consecutive_P_support_age7_and_protected36_preserved':True,'no_future_forecast_or_online_teacher':True,
        'exact_snapshot_and_modified_root_refusal':True,'refusals':refused,'GPU_submissions':0,'ledger_written':False}


if __name__=='__main__':print(json.dumps(run()))
