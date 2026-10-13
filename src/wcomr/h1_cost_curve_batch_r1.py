"""Complete same-batch controls, frozen lambda curve and fixed-mask ablations.

All numerical methods call accepted implementations. Lambda variants alter
only the preregistered scalar and its fingerprint; the middle variant is the
already frozen H1. No confirmation input or endpoint selects a workpoint.
"""
import copy
from .source_phase_absolute_h1_control_r1 import fingerprint,validate_parameters

METHODS=('NATIVE','WC','RA','A_NO_P','P_OFF','H1_LOW','H1_MID','H1_HIGH',
         'FIXED_A','FIXED_PLAIN')


def lambda_variants(parameters):
    validate_parameters(parameters)
    values=parameters.get('curve_lambdas')
    if (not isinstance(values,list) or len(values)!=3 or values!=sorted(set(values))
            or values[1]!=parameters['lambda_seconds_per_weighted_absolute_MSE']):
        raise ValueError('Three previously frozen lambdas including exact middle H1 required')
    result={}
    for method,lam in zip(METHODS[5:8],values):
        p=copy.deepcopy(parameters)
        p['lambda_seconds_per_weighted_absolute_MSE']=lam;p['fingerprint']=fingerprint(p)
        validate_parameters(p);result[method]=p
        assert all(p[k]==v for k,v in parameters.items()
                   if k not in ('fingerprint','lambda_seconds_per_weighted_absolute_MSE'))
    if result['H1_MID']!=parameters:raise ValueError('Middle curve changed frozen candidate')
    return result


def matrix(scenes):
    if len(scenes)!=4 or len(set(scenes))!=4:raise ValueError('Complete four CAL requests required')
    rows=[]
    for repeat in (1,2):
        for method in METHODS if repeat==1 else METHODS[::-1]:
            rows.append(dict(id=f'warm_{repeat}_{method}',scene=scenes[0],method=method,
                section='WARMUP',round=repeat))
    for index,scene in enumerate(scenes):
        for method in METHODS if index%2==0 else METHODS[::-1]:
            rows.append(dict(id=f'timed_{index}_{method}',scene=scene,method=method,
                section='TIMED',round=1))
    assert len(rows)==60 and sum(r['section']=='TIMED' for r in rows)==40
    return rows


def execute(inference,sample,method,*,table_parameters,previous_parameters,**kw):
    from . import clean_speed20_r1 as clean
    from .source_phase_absolute_h1_batch_r1 import execute as accepted_execute
    from .source_phase_fixed_mask_r1 import execute_fixed,CAL_MASK_A,CAL_MASK_C
    if method not in METHODS:raise ValueError('One of all ten preregistered methods required')
    if sample.seed!=0:raise ValueError('This is the CAL cost curve, not confirmation tuning')
    variants=lambda_variants(table_parameters['SOURCE_PHASE'])
    if method=='WC':
        result=clean.execute(inference,sample,'WC',**kw)
    elif method in METHODS[:5]:
        result,_=accepted_execute(inference,sample,method,table_parameters=table_parameters,
            previous_parameters=previous_parameters,**kw)
    elif method in variants:
        tables={**table_parameters,'SOURCE_PHASE':variants[method]}
        result,_=accepted_execute(inference,sample,'TABLE_PHASE_H1',table_parameters=tables,
            previous_parameters=previous_parameters,**kw)
        result['curve_lambda']=variants[method]['lambda_seconds_per_weighted_absolute_MSE']
        result['curve_parameters_fingerprint']=variants[method]['fingerprint']
    else:
        result=execute_fixed(inference,sample,
            replay_plan=CAL_MASK_A if method=='FIXED_A' else CAL_MASK_C,
            table_parameters=table_parameters['SOURCE_PHASE'],
            previous_parameters=previous_parameters,**kw)
    result['cost_curve_bridge_method']=result['method'];result['method']=method
    result['unseen_confirmation_or_lambda_selection']=False
    return result
