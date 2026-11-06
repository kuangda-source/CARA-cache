"""Signed same-state diagnostics, with scene and missingness boundaries."""
import math


def summarize(receipt,config):
    from .own_state_sampling import historical_bridge
    # Caller independently supplies hash-bound original rows in the receipt.
    cases=receipt['cases'];rows=[]
    if [r['name'] for r in cases]!=config['sample_names'][:len(cases)]:raise ValueError('Case order differs')
    for case in cases:
        if not case.get('bridge_pass'):
            rows.append({'name':case['name'],'status':'MISSING_OR_INVALID_BRIDGE_NOT_ZERO'});continue
        records=case['observed']['shadow_records']
        if [r['call'] for r in records]!=config['fixed_CFG_calls']:raise ValueError('Observations incomplete')
        errors={}
        for kind in ['prewarp_residual','postwarp_residual','velocity']:
            values={m:[] for m in ['official','scalar']}
            for r in records:
                if not r['shared_teacher'] or r['cfg_branch']!=(r['call']-1)%2:raise ValueError('Observation identity differs')
                for m in values:
                    metric=r['candidates'][m][kind]
                    if (metric['status']!='OK' or any(v is not None and not math.isfinite(v)
                        for k,v in metric.items() if k not in ['status','groups'])
                            or metric['mse']<0):raise ValueError('Invalid finite diagnostic')
                    values[m].append(metric['mse'])
            a,b=[sum(values[m])/4 for m in values]
            errors[kind]={'official_mean_MSE':a,'scalar_mean_MSE':b,'official_minus_scalar':a-b,
                'scalar_over_official':b/a if a>0 else None,'individual_signed_deltas':[x-y for x,y in zip(values['official'],values['scalar'])]}
        for a,b in zip(records[::2],records[1::2]):
            if a['actual_input_identity']!=b['actual_input_identity']:raise ValueError('CFG pair inputs differ')
        rows.append({'name':case['name'],'status':'VALID_SAME_STATE_DIAGNOSTIC','within_scene_observations':4,'errors':errors})
    complete=len(cases)==3 and all(r['status']=='VALID_SAME_STATE_DIAGNOSTIC' for r in rows)
    return {'status':'COMPLETE_THREE_SCENE_DIAGNOSTIC' if complete else 'PARTIAL_DIAGNOSTIC_NOT_FULL_CARD',
        'planned_scenes':3,'planned_observations':12,'valid_scene_count':sum(r['status']=='VALID_SAME_STATE_DIAGNOSTIC' for r in rows),
        'rows':rows,'independent_confirmation':False,'formal_W3_training_labels':False,
        'quality_or_clean_speed_decision':False,'scope':'Four dependent observations reduced within each exposed CAL scene; signed failures retained, no all-positive gate'}
