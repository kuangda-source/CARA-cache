"""Frozen old104 action coefficients, independent preceding fullD reference.

All new formal clocks validate; anchor clocks are separately charged observations,
not targets. No fitting, endpoint choice or threshold relaxation on the new card.
"""
import math
from .historical_bridge import DEPLOYMENT_LIMIT_SECONDS


def predict(card, slot, anchor_seconds):
    dD,dA=card['cost_model']['coefficients'];counts=card['policies'][slot['role']]['counts']
    return dict(anchor_id=slot['clock_anchor_id'],anchor_seconds=anchor_seconds,
                predicted_seconds=anchor_seconds+dD*(counts['D']-36)+dA*counts['A'],
                coefficients_frozen=True,created_before_target_execution=True)


def analyze(card, rows):
    expected=[s for s in card['matrix'] if s['section'] in ('ANCHOR','CALIBRATION','VALIDATION')]
    if len(rows)!=88 or len({r['id'] for r in rows})!=88 or len(expected)!=88:
        raise ValueError('All80 formal clocks and8 independent clock anchors required')
    by={r['id']:r for r in rows};clocks={}
    for s in expected:
        r=by[s['id']]
        if any(r[k]!=v for k,v in s.items()) or r['status']!='COMPLETE' or not r['complete_request_boundary'] or r['diagnostic']:
            raise ValueError('Changed cohort or timing boundary')
        if not math.isfinite(r['seconds']) or r['seconds']<=0:raise ValueError('Invalid clock')
        clocks[s['id']]=r['seconds']
    model=card['cost_model'];dD,dA=model['coefficients']
    if model['new_card_refit'] or model['training_rows']!=64 or not (dD>0 and dA>=0):raise ValueError('Frozen old training identity')
    positions={s['id']:i for i,s in enumerate(card['matrix'])};validation=[]
    native=[s for s in expected if s['role']=='NATIVE'];budget=min(DEPLOYMENT_LIMIT_SECONDS,.8*sum(clocks[s['id']] for s in native)/8)
    for s in expected:
        if s['section']=='ANCHOR' or s['role']=='NATIVE':continue
        anchor=by[s['clock_anchor_id']]
        if anchor['section']!='ANCHOR' or anchor['role']!='CLOCK_ANCHOR' or any(s[k]!=anchor[k] for k in ('member','seed','repeat')) or positions[anchor['id']]>=positions[s['id']]:raise ValueError('Anchor is not independent strict past same-input reference')
        cnt=card['policies'][s['role']]['counts'];estimate=clocks[anchor['id']]+dD*(cnt['D']-36)+dA*cnt['A'];actual=clocks[s['id']]
        validation.append(dict(id=s['id'],member=s['member'],role=s['role'],repeat=s['repeat'],anchor_id=anchor['id'],anchor_seconds=clocks[anchor['id']],predicted_seconds=estimate,actual_seconds=actual,underestimate_seconds=actual-estimate,absolute_relative_error=abs(actual-estimate)/actual))
    per=[]
    for repeat in (1,2):
        for role in card['policies']:
            if role in ('NATIVE','CLOCK_ANCHOR'):continue
            rr=[r for r in validation if r['role']==role and r['repeat']==repeat];assert len(rr)==4
            predicted=sum(r['predicted_seconds'] for r in rr)/4;actual=sum(r['actual_seconds'] for r in rr)/4
            per.append(dict(role=role,repeat=repeat,predicted_mean_seconds=predicted,observed_mean_seconds=actual,predicted_feasible=predicted+6<=budget,measured_feasible=actual<=budget))
    mae=sum(r['absolute_relative_error'] for r in validation)/72;worst=max(r['underestimate_seconds'] for r in validation);no_false=all(not r['predicted_feasible'] or r['measured_feasible'] for r in per)
    passed=mae<=.01 and worst<=2 and no_false
    return dict(status='COST112_INDEPENDENT_VALIDATION_PASS' if passed else 'COST112_INDEPENDENT_VALIDATION_FAILED',timing_model_validated=passed,fit_coefficients=dict(per_D=dD,per_A=dA),training_rows=64,validation_rows=72,independent_clock_anchors=8,fit_round='PREVIOUS_ACCEPTED104_BOTH_ROUNDS_DEVELOPMENT',validation_refit=False,validation=validation,per_role=per,mean_absolute_relative_error=mae,maximum_underestimate_seconds=worst,no_false_feasible=no_false,budget_seconds=budget,margin_seconds=6.,independent_prompt_count=4,endpoint_quality_used=False,GPU_dispatch_ready=False)
