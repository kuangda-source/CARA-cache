"""Full288 actual-state proxy coverage; no counterfactual model execution."""
import hashlib,json,math
from pathlib import Path
from statistics import mean

R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    capture=R/'reports/wc_math_n2_live_or_terminal_capture_20261012.json'
    paramref=R/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json'
    priorref=R/'reports/wc_real_cost_creation_phase_prior_r1_bound_20261010.json'
    c=json.loads(capture.read_text());params=json.loads(paramref.read_text());prior=json.loads(priorref.read_text())
    assert c['final']['status']=='MATH_N2_FULL36_SCIENCE_ALL54_AUDITED_93FRAME_SCORED'
    rows=[r for r in c['final']['rows'] if r['section']=='TIMED' and r['method'] in ('SOURCE_H1','SOURCE_H2')]
    assert len(rows)==8 and all(r['counts']['A']==0 and all(h['extra_heads']==0 for h in r['A_history']) for r in rows)
    floor={phase:prior['phase_priors'][step]['median_creation_floor_proxy'] for phase,step in [('early','12'),('late','30')]}
    states=[];protected=[];checks=0
    for row in rows:
        for h in row['source_history']:
            d=h['source_policy']['decision'];key={'scene':row['scene'],'method':row['method'],'step':d['step']}
            if d['local_proxy'] is None or d['gain'] is None:
                protected.append({**key,'reason':d['reason']});continue
            source=d['state_before'][1];beforefloor=d['state_before'][3];g=d['gain']
            qC=g*params['source'][source]['C_scale']*(beforefloor+d['local_proxy'])**2
            qA=qC*params['source'][source]['A_over_C']
            birth=floor['early' if d['step']<25 else 'late'];qP=g*params['source']['P']['C_scale']*birth**2
            if d['action']=='C':assert math.isclose(qC,d['added_risk'],rel_tol=1e-10,abs_tol=1e-12);checks+=1
            if d['action']=='P':
                assert birth==d['predicted_creation_floor'] and math.isclose(qP,d['added_risk'],rel_tol=1e-12,abs_tol=1e-12);checks+=1
            states.append({**key,'source':source,'actual_action':d['action'],'qC':qC,'qA':qA,'qP':qP,
                           'partial_ready':d['partial_ready'],'consecutive_P':d['state_before'][5]})
    assert len(states)+len(protected)==288
    costs=params['cost_seconds'];onehead=costs['C']+(costs['A']-costs['C'])/2
    cases=[]
    for price_mode in ('COMMON_CONSERVATIVE','SOURCE_SPECIFIC_HEADS'):
        for mult in (1,4,16,64):
            counts={m:{a:0 for a in ('C','A','P','D')} for m in ('SOURCE_H1','SOURCE_H2')};by_source={'D':0,'P':0}
            for s in states:
                Aprice=onehead if price_mode=='SOURCE_SPECIFIC_HEADS' and s['source']=='D' else costs['A']
                lam=params['lambda_seconds_per_normalized_error']*mult
                opts=[('C',costs['C']+lam*s['qC']),('A',Aprice+lam*s['qA']),('D',costs['D'])]
                if s['partial_ready'] and s['consecutive_P']<2:opts.append(('P',costs['P']+lam*s['qP']))
                action=min(opts,key=lambda t:(t[1],t[0]))[0];counts[s['method']][action]+=1
                if action=='A':by_source[s['source']]+=1
            cases.append({'price_mode':price_mode,'lambda_multiplier':mult,'one_step_choices_on_actual_states':counts,
                          'A_chosen_by_source':by_source,'full_new_policy_or_endpoint_claim':False})
    hull=[]
    for source in ('D','P'):
        for price in (costs['A'],onehead if source=='D' else costs['A']):
            r=params['source'][source]['A_over_C'];threshold=(costs['D']-price)/(costs['D']-costs['C'])
            hull.append({'source':source,'A_price':price,'r':r,'maximum_r_for_C_A_D_lower_hull':threshold,
                         'A_excluded_from_immediate_C_A_D_for_all_positive_lambda':r>=threshold,
                         'not_actual_future_error_or_video_judgment':True})
    result={'status':'ALL288_ACTUAL_DECISIONS_SOURCE_PRICE_LAMBDA_COVERAGE_CPU_AUDITED',
        'source_sha256':{str(p.relative_to(R)):sha(p) for p in (capture,paramref,priorref)},
        'full_decisions':288,'protected_or_missing_observation':len(protected),'actual_paid_states':len(states),
        'actual_C_P_squared_risk_reconstruction_checks':checks,'actual_selected_A':0,
        'A_actual_heads':0,'cases':cases,'lower_hull':hull,'states':states,'protected':protected,
        'GPU_submissions':0,'ledger_written':False,'new_video_or_policy_claim':False}
    p=R/'reports/wc_math_n2_all288_A_coverage_and_lower_hull_cpu_20261012.json';assert not p.exists()
    p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','full_decisions','actual_paid_states','actual_C_P_squared_risk_reconstruction_checks','cases','lower_hull')}))
if __name__=='__main__':main()
