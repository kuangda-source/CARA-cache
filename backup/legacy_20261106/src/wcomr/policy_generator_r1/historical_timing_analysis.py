"""One-way fit/validation for the registered104 card; no quality-based fitting."""
import math
import numpy as np
from .historical_bridge import DEPLOYMENT_LIMIT_SECONDS


def analyze(card, rows):
    expected=[r for r in card['matrix'] if r['section'] in ('CALIBRATION','VALIDATION')]
    if len(rows)!=len(expected) or len({r['id'] for r in rows})!=len(rows):
        raise ValueError('All80 unique clean formal clocks required')
    by_id={r['id']:r for r in rows}; clocks={}
    for plan in expected:
        r=by_id.get(plan['id'])
        if r is None or any(r.get(k)!=plan[k] for k in ('section','role','member','seed','repeat')):
            raise ValueError('Clock identity or cohort differs')
        if r.get('status')!='COMPLETE' or not r.get('complete_request_boundary') or r.get('diagnostic'):
            raise ValueError('Rejected, partial or diagnostic clock is not a clean formal clock')
        t=r.get('seconds')
        if type(t) not in (float,int) or not math.isfinite(t) or t<=0:
            raise ValueError('Positive finite complete request clock required')
        clocks[r['section'],r['role'],r['member']]=float(t)
    roles=[r for r in card['policies'] if r!='NATIVE'];members=card['CAL_FIT_members']
    def features(role):
        counts=card['policies'][role]['counts']
        return [1.,counts['D']-36.,float(counts['A'])]
    x=[];y=[]
    for member in members:
        n=clocks['CALIBRATION','NATIVE',member]
        for role in roles:
            x.append(features(role));y.append(clocks['CALIBRATION',role,member]-n)
    coef,_,rank,_=np.linalg.lstsq(np.array(x),np.array(y),rcond=None)
    if rank!=3 or not np.isfinite(coef).all() or coef[1]<=0:
        raise ValueError('Calibration design/rank or positive dense cost failed')
    validation=[]
    for member in members:
        n=clocks['VALIDATION','NATIVE',member]
        for role in roles:
            estimate=n+float(np.dot(features(role),coef));actual=clocks['VALIDATION',role,member]
            if not math.isfinite(estimate) or estimate<=0:raise ValueError('Invalid predicted clock')
            validation.append(dict(member=member,role=role,predicted_seconds=estimate,
                actual_seconds=actual,underestimate_seconds=actual-estimate,absolute_relative_error=abs(actual-estimate)/actual))
    native_mean=sum(clocks[s,'NATIVE',m] for s in ('CALIBRATION','VALIDATION') for m in members)/8
    budget=min(DEPLOYMENT_LIMIT_SECONDS,.8*native_mean)
    margin=card['timing']['fixed_margin_seconds']
    per_role=[]
    for role in roles:
        rr=[r for r in validation if r['role']==role]
        predicted=sum(r['predicted_seconds'] for r in rr)/4
        observed=sum(r['actual_seconds'] for r in rr)/4
        per_role.append(dict(role=role,predicted_mean_seconds=predicted,observed_mean_seconds=observed,
            predicted_feasible=predicted+margin<=budget,measured_feasible=observed<=budget))
    mae=sum(r['absolute_relative_error'] for r in validation)/len(validation)
    worst=max(r['underestimate_seconds'] for r in validation)
    targets=card['timing']['primary_error_targets']
    no_false=all(not r['predicted_feasible'] or r['measured_feasible'] for r in per_role)
    passed=mae<=targets['mean_absolute_relative_error_max'] and worst<=targets['maximum_underestimate_seconds_max'] and no_false
    paired=[]
    for role in card['policies']:
        for member in members:
            a=clocks['CALIBRATION',role,member];b=clocks['VALIDATION',role,member]
            paired.append(dict(role=role,member=member,round1=a,round2=b,round2_minus_round1=b-a))
    return dict(status='TIMING_MODEL_VALIDATION_PASS' if passed else 'TIMING_MODEL_VALIDATION_FAILED',
        timing_model_validated=passed,fit_coefficients=dict(offset=coef[0],per_D=coef[1],per_A=coef[2]),
        training_rows=36,validation_rows=36,fit_round='CALIBRATION',validation_refit=False,
        validation=validation,per_role=per_role,paired_clock_differences=paired,
        mean_absolute_relative_error=mae,maximum_underestimate_seconds=worst,
        no_false_feasible=no_false,budget_seconds=budget,margin_seconds=margin,
        independent_prompt_count=4,endpoint_quality_used=False,GPU_dispatch_ready=False)
