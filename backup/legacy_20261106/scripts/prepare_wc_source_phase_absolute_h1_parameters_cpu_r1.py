#!/usr/bin/env python3
"""Freeze four-cell and pooled H1 tables with four actual action crossings."""
import hashlib,itertools,json,math,sys
from pathlib import Path
from statistics import median
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from wcomr.source_phase_table_fit_r1 import fit,predict,validate_complete,action_prices,squared_gain
from wcomr.source_phase_absolute_h1_control_r1 import VERSION,fingerprint,validate_parameters


if __name__=='__main__':
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    ref=R/'reports/wc_source_phase16_live_or_terminal_capture_20261012.json';v=json.loads(ref.read_text());points=v['final']['points']
    assert v['final']['status']=='SOURCE_PHASE16_ALL8_PARENTS16_POINTS64_LABELS368_PAIRS192_TENSORS_CPU_AUDITED'
    assert v['post_exit']['exit_code']==v['supervisor']['child_exit_code']==0 and all(v['payload_verified'].values())
    assert all(p['all_candidate_and_teacher_tensors_read'] for p in points)
    scenes=validate_complete(points);oldref=R/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json';old=json.loads(oldref.read_text())
    models={group:fit(points,group) for group in ('SOURCE_PHASE','SOURCE')};crossings=[];rows=[]
    for point in points:
        pred=predict(models['SOURCE_PHASE'],point);prices=action_prices(old,point['selection']['source']);g2=squared_gain(point)
        q={'C':pred['C']*g2,'A':pred['FUSION_A']*g2,'P':pred['NEW_P']*g2,'D':0.}
        c={'C':prices['C'],'A':prices['FUSION_A'],'P':prices['NEW_P'],'D':prices['D']};cuts=[]
        for a,b in itertools.combinations(q,2):
            if q[a]==q[b]:continue
            cut=(c[b]-c[a])/(q[a]-q[b])
            if math.isfinite(cut) and cut>0:cuts.append({'actions':[a,b],'lambda':cut});crossings.append(cut)
        rows.append({'selection':point['selection'],'actual_four_action_prices':c,'predicted_weighted_absolute_MSE':q,'positive_crossings':cuts})
    assert crossings;center=median(crossings);grid=[center*.25,center,center*4.]
    result={'status':'SOURCE_PHASE_ABSOLUTE_H1_FOUR_ACTION_TABLE_AND_LAMBDA_CPU_FROZEN_NOT_GPU_POLICY_RESULT',
        'source_complete_cal16_ref':str(ref.relative_to(R)),'source_complete_cal16_sha256':sha(ref),'calibration_scenes':scenes,
        'crossings_used_no_undeployed_old_D_reference':rows,'positive_crossings':len(crossings),'primary_lambda':center,
        'curve_lambdas':grid,'no_endpoint_or_unexposed_input_used_for_lambda':True,'models':{},'GPU_submissions':0,'ledger_written':False}
    for group,model in models.items():
        p={'version':VERSION,'gamma':old['gamma'],'old_math_parameters_fingerprint':old['fingerprint'],
            'table_model':model,'cost_seconds':old['cost_seconds'],
            'source_A_cost_seconds':{source:action_prices(old,source)['FUSION_A'] for source in ('D','P')},
            'lambda_seconds_per_weighted_absolute_MSE':center,'curve_lambdas':grid,
            'sources':{str(ref.relative_to(R)):sha(ref),str(oldref.relative_to(R)):sha(oldref)},
            'prices_scope':'OLD_COMPLETE_CFG_PAIR_AFTER_PAID_PROBE_WITH_HEAD_TRANSFER_NOT_NEW_CLEAN_PROFILE',
            'root_floor_and_uncovered_age_transfer_retained':True,'no_future_forecast_or_teacher':True,
            'not_terminal_action_value_or_optimality_guarantee':True}
        p['fingerprint']=fingerprint(p);validate_parameters(p)
        name='manifests/wc_source_'+('phase' if group=='SOURCE_PHASE' else 'pooled')+'_absolute_h1_parameters_r1_20261013.json'
        path=R/name;assert not path.exists();path.write_text(json.dumps(p,indent=2,allow_nan=False)+'\n')
        result['models'][group]={'ref':name,'sha256':sha(path),'fingerprint':p['fingerprint']}
    dest=R/'reports/wc_source_phase_absolute_h1_parameter_freeze_cpu_20261013.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','positive_crossings','primary_lambda','curve_lambdas','GPU_submissions')}))
