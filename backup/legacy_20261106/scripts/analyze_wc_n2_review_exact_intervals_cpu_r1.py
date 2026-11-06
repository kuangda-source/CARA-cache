"""Exact lambda intervals, actual teacher scales and preregistered natural16."""
import hashlib,json,math
from collections import Counter
from pathlib import Path
from statistics import mean

R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def interval(price,risk,action='A'):
    lower,upper=0.,math.inf;empty=False
    for other in price:
        if other==action:continue
        dq=risk[action]-risk[other];dc=price[other]-price[action]
        if dq>0:upper=min(upper,dc/dq)
        elif dq<0:lower=max(lower,dc/dq)
        elif dc<0:empty=True
    exists=not empty and upper>=lower and upper>=0
    return {'nonempty':exists,'lower_lambda':lower if exists else None,
        'upper_lambda':upper if exists and math.isfinite(upper) else None,
        'upper_is_infinite':exists and math.isinf(upper),
        'positive_width':exists and upper>lower}

def inside(value,region):
    return region['nonempty'] and value>=region['lower_lambda'] and (
        region['upper_is_infinite'] or value<=region['upper_lambda'])

def validate_math():
    p={'C':0.,'A':1.,'D':2.};q={'C':1.,'A':.4,'D':0.}
    v=interval(p,q);assert math.isclose(v['lower_lambda'],5/3) and v['upper_lambda']==2.5
    assert not interval(p,{**q,'A':.9})['nonempty']
    assert not interval({**p,'P':1.1},{**q,'P':.1})['nonempty']
    assert not interval(p,{'C':0.,'A':0.,'D':0.})['nonempty']
    assert interval(p,{'C':1.,'A':0.,'D':0.})['upper_is_infinite']
    for lam in (0.,1.,2.,3.,100.):
        best=min(p,key=lambda a:p[a]+lam*q[a])
        assert inside(lam,v)==(best=='A')
    return 5

def fusion(point,gamma):
    m=point['related_error_moments']
    return (1-gamma)**2*m['A']+gamma**2*m['B']+2*gamma*(1-gamma)*m['C']

def main():
    refs={k:R/v for k,v in {
        'N1':'reports/wc_math_n1_live_or_terminal_capture_20261012.json',
        'N2':'reports/wc_math_n2_live_or_terminal_capture_20261012.json',
        'states':'reports/wc_math_n2_all288_A_coverage_and_lower_hull_cpu_20261012.json',
        'parameters':'manifests/wc_math_n2_frozen_parameters_r1_20261012.json'}.items()}
    data={k:json.loads(p.read_text()) for k,p in refs.items()};p=data['parameters'];states=data['states']
    assert data['N1']['final']['status']=='N1_ALL4_PARENTS12_POINTS48_READOUTS180_PAIRS_CPU_AUDITED'
    assert data['N2']['final']['status']=='MATH_N2_FULL36_SCIENCE_ALL54_AUDITED_93FRAME_SCORED'
    assert states['full_decisions']==288 and len(states['states'])==200 and len(states['protected'])==88
    cost=p['cost_seconds'];D_A=cost['C']+(cost['A']-cost['C'])/2;rows=[]
    for mode in ('COMMON','SOURCE_SPECIFIC'):
        for s in states['states']:
            a_price=D_A if mode=='SOURCE_SPECIFIC' and s['source']=='D' else cost['A']
            prices={'C':cost['C'],'A':a_price,'D':cost['D']};risks={'C':s['qC'],'A':s['qA'],'D':0.}
            if s['partial_ready'] and s['consecutive_P']<2:prices['P']=cost['P'];risks['P']=s['qP']
            region=interval(prices,risks)
            rows.append({'scene':s['scene'],'method':s['method'],'step':s['step'],'source':s['source'],
                'price_mode':mode,'legal_actions':list(prices),'risk_unit':'ORIGINAL_N2_G_TIMES_NORMALIZED_MSE',
                'region':region,'old_lambda_inside':inside(p['lambda_seconds_per_normalized_error'],region)})
    summary=[]
    for mode in ('COMMON','SOURCE_SPECIFIC'):
        for source in ('D','P'):
            x=[r for r in rows if r['price_mode']==mode and r['source']==source]
            summary.append({'price_mode':mode,'source':source,'paid_states':len(x),
                'A_empty_interval':sum(not r['region']['nonempty'] for r in x),
                'A_positive_width_interval':sum(r['region']['positive_width'] for r in x),
                'old_lambda_inside':sum(r['old_lambda_inside'] for r in x)})
    teacher=[];scale=[]
    for point in data['N1']['final']['points']:
        sel=point['selection'];energy=point['teacher_guided_energy'];qC=point['losses']['OFFICIAL_C']['normalized_guided_MSE']
        qA=fusion(point,p['gamma']);source=sel['source'];price=D_A if source=='D' else cost['A']
        assert energy>1e-12 and math.isclose(qC*energy,point['losses']['OFFICIAL_C']['MSE'],rel_tol=1e-11)
        predicted_ratio=p['source'][source]['A_over_C']
        actual=interval({'C':cost['C'],'A':price,'D':cost['D']},{'C':qC,'A':qA,'D':0.})
        predicted=interval({'C':cost['C'],'A':price,'D':cost['D']},{'C':qC,'A':qC*predicted_ratio,'D':0.})
        phase='EARLY' if sel['step']<25 else 'LATE'
        teacher.append({'scene':sel['scene'],'step':sel['step'],'source':source,'phase':phase,
            'actual_ratio_A_over_C':qA/qC,'pooled_estimated_ratio':predicted_ratio,
            'teacher_C_A_D_interval':actual,'pooled_C_A_D_interval':predicted,
            'true_current_P_operator_label_available':False,'not_four_action_teacher_hull':True})
        scale.append({'scene':sel['scene'],'step':sel['step'],'source':source,'phase':phase,
            'teacher_guided_mean_square_energy':energy,'C_normalized_MSE':qC,'C_absolute_MSE':qC*energy})
    source_summary=[]
    for source in ('D','P'):
        x=[r for r in teacher if r['source']==source]
        source_summary.append({'source':source,'states':len(x),
            'actual_A_positive_interval':sum(r['teacher_C_A_D_interval']['positive_width'] for r in x),
            'pooled_A_positive_interval':sum(r['pooled_C_A_D_interval']['positive_width'] for r in x)})
    targets={('D','EARLY'):3,('D','LATE'):2,('P','EARLY'):2,('P','LATE'):1};selected=[]
    parents=[r for r in data['N2']['final']['rows'] if r['section']=='TIMED' and r['method']=='P_OFF']
    assert len(parents)==4
    for parent in parents:
        for (source,phase),target_age in targets.items():
            eligible=[]
            for h in parent['source_history']:
                d=h['source_policy']['decision'];state=d['state_before'];n=d['step'];birth=state[2]
                if state[1]!=source or ('EARLY' if n<25 else 'LATE')!=phase or h['protected'] or d['local_proxy'] is None or not d['both_sources_ready'] or birth is None:continue
                age=n-birth
                if not 1<=age<=6:continue
                eligible.append({'step':n,'age':age,'source_birth':birth,'true_D_anchor':state[0],
                    'actual_pi0_action':d['action'],'partial_ready':d['partial_ready'],
                    'state_before':state,'local_proxy':d['local_proxy'],'gain':d['gain']})
            chosen=min(eligible,key=lambda r:(abs(r['age']-target_age),r['step'])) if eligible else None
            selected.append({'scene':parent['scene'],'source':source,'phase':phase,'target_age':target_age,
                'eligible_points':len(eligible),'chosen':chosen,'selection_used_teacher_or_LPIPS':False})
    energies=[r['teacher_guided_mean_square_energy'] for r in scale]
    result={'status':'N2_REVIEW_ALL288_EXACT_INTERVALS_ALL12_SCALE_NATURAL16_CPU_AUDITED',
        'source_sha256':{str(path.relative_to(R)):sha(path) for path in refs.values()},
        'math_control_cases_passed':validate_math(),'old_full_decisions':288,
        'protected_or_missing_observation':Counter(r['reason'] for r in states['protected']),
        'paid_states':200,'exact_interval_cases':len(rows),'interval_summary':summary,'exact_intervals':rows,
        'N1_teacher_C_A_D_rows':teacher,'teacher_hull_summary':source_summary,
        'N1_scale_rows':scale,'energy_range':{'min':min(energies),'max':max(energies),'max_over_min':max(energies)/min(energies)},
        'N1_source_phase_coverage':dict(Counter(r['source']+'_'+r['phase'] for r in scale)),
        'natural16_selection':selected,'natural16_found':sum(x['chosen'] is not None for x in selected),
        'pre_action_snapshot_not_serialized_or_restored_by_this_CPU':True,
        'new_GPU_submissions':0,'new_teacher_calls':0,'ledger_written':False,'current_frozen_parameters_changed':False}
    assert result['natural16_found']==16 and result['exact_interval_cases']==400
    out=R/'reports/wc_n2_review_exact_intervals_scale_natural16_cpu_20261012.json';assert not out.exists()
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['status','interval_summary','teacher_hull_summary','energy_range','N1_source_phase_coverage','natural16_found','new_GPU_submissions']}))

if __name__=='__main__':main()
