"""Planted source/phase mechanisms, held-scene isolation and scalar geometry."""
import copy,math
from wcomr.source_phase_table_fit_r1 import analyze,fit,predict,intervals,choose,validate_complete


def run():
    parameters={'cost_seconds':{'C':.1,'A':.5,'P':1.1,'D':2.}}
    mechanism={('D','EARLY'):(2.,.1,.02),('D','LATE'):(20.,1.8,.03),
        ('P','EARLY'):(.3,.4,.025),('P','LATE'):(3.,2.,.04)}
    points=[]
    for i in range(4):
        for (source,phase),(scale,ratio,birth) in mechanism.items():
            delta=.1+.02*i;floor=.02 if source=='P' else 0.;x=(delta+floor)**2;q=scale*x
            step=10 if phase=='EARLY' else 30;energy=.4+i
            loss={'C':q,'D_REFERENCE_A':q*ratio,'FUSION_A':q*ratio,'NEW_P':birth}
            points.append({'selection':{'scene':'S'+str(i),'source':source,'phase':phase,'chosen':{'step':step}},
                'parent_pre_action':[7,source,7,floor,0.,0,step-1,step-1,False],
                'actual_C_paid_proxy':{'local_proxy':delta,'gain':.5},
                'losses':{a:{'absolute_guided_MSE':v,'normalized_guided_MSE':v/energy} for a,v in loss.items()}})
    result=analyze(points,parameters)
    assert len(result['leave_one_scene_out'])==len(result['cell_summaries'])==4
    for fold in result['leave_one_scene_out']:
        assert fold['held_scene'] not in fold['training_scenes'] and len(fold['held_rows'])==4
        for p in fold['held_rows']:
            new=next(x for x in p['predictions'] if x['grouping']=='SOURCE_PHASE')
            assert all(v<1e-24 for v in new['squared_prediction_errors'].values())
            assert all(v['regret_seconds_plus_weighted_local_MSE']<1e-12 for v in new['lambda_decisions'])
    # Pooled C scale must fail to represent deliberately different early/late
    # mechanisms, while the four-cell model preserves r>1 harmful A states.
    assert any(any(v>1e-4 for v in next(x for x in p['predictions'] if x['grouping']=='SOURCE')['squared_prediction_errors'].values()) for f in result['leave_one_scene_out'] for p in f['held_rows'])
    assert result['models']['SOURCE_PHASE']['cells']['D_LATE']['A_ratios']['FUSION_A']>1
    for scene in ('S0','S1','S2','S3'):
        train=[p for p in points if p['selection']['scene']!=scene]
        held=next(p for p in points if p['selection']['scene']==scene)
        model=fit(train);before=predict(model,held)
        mutated=copy.deepcopy(held);mutated['losses']['C']['absolute_guided_MSE']*=1e6
        assert predict(model,mutated)==before,'Current teacher entered prediction'
    prices={'C':0.,'A':1.,'D':2.};risk={'C':1.,'A':.4,'D':0.};region=intervals(prices,risk)['A']
    assert math.isclose(region['lower'],5/3) and region['upper']==2.5
    for lam in (0.,1.,2.,3.):
        assert (choose(prices,risk,lam)=='A')==(region['lower']<=lam<=region['upper'])
        assert choose(prices,risk,lam)==choose(prices,{a:3*v for a,v in risk.items()},lam/3)
    bad=copy.deepcopy(points);bad.pop()
    try:validate_complete(bad)
    except ValueError:pass
    else:raise AssertionError('Partial16 incorrectly fit')
    zero=copy.deepcopy(points)
    for p in zero:p['actual_C_paid_proxy']['local_proxy']=0.;p['parent_pre_action'][3]=0.
    assert predict(fit(zero),zero[0]) is None,'Missing feature fabricated as known error'
    return {'status':'SOURCE_PHASE_TABLE_PLANTED16_LOSO_SCOPE_UNITS_CPU_PASS_NOT_REAL_LABELS',
        'synthetic_points':16,'held_scene_folds':4,'four_cells_each4':True,
        'harmful_A_ratios_retained':True,'held_teacher_not_prediction_input':True,
        'lambda_inverse_scale_identity':True,'missing_state_or_feature_not_fitted':True,
        'GPU_submissions':0,'ledger_written':False}
