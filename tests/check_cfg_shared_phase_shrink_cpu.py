"""Direct coupled-vector oracle for the registered one-parameter fit."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.action_cost_ranking import ORIGINS
from wcomr.cfg_shared_phase_shrink import MODES, fit_shared_shrink

SHA = 'a'*64


def main():
    records=[];vectors=[]
    for i,(scene,step) in enumerate(ORIGINS):
        scale=1+i/8
        ec=[scale, .8*scale];eu=[.95*scale, .75*scale]
        qc=[-.32*scale,-.29*scale];qu=[-.1*scale,-.09*scale]
        # Actual late proposal is already halved; never undo its FP32 fusion.
        a=1. if step<25 else .5
        e=[8*x-7*y for x,y in zip(ec,eu)]
        q=[a*(8*x-7*y) for x,y in zip(qc,qu)]
        vectors.append((e,q))
        records.append({'scene':scene,'state':'step'+str(step),
            'base_guided_MSE':sum(x*x for x in e)/2,
            'guided_error_update_mean_dot':sum(x*y for x,y in zip(e,q))/2,
            'guided_update_mean_square':sum(x*x for x in q)/2,
            'diagnostics':{'actual_CFG_coefficients':[8,-7]}})
    before=hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()
    results=[]
    for mode in MODES:
        result=fit_shared_shrink(records,mode=mode,source_sha256=SHA)
        k=result['shared_shrink'];assert 0<k<1
        direct=sum(sum((x+k*y)**2 for x,y in zip(e,q))/2 for e,q in vectors)/8
        assert math.isclose(direct,result['scene_and_step_equal_fitted_guided_MSE'],rel_tol=1e-12,abs_tol=1e-12)
        b=result['mean_error_update_dot'];q=result['mean_update_square']
        assert math.isclose(2*b+2*1.1*q*k,0.,abs_tol=1e-12)
        for other in (0.,.5,1.):
            value=sum(sum((x+other*y)**2 for x,y in zip(e,q))/2 for e,q in vectors)/8
            assert direct+.1*q*k*k <= value+.1*q*other*other+1e-12
        assert result['effective_shared_alpha_late']==.5*k
        assert not result['supplied_moments_same_state_teacher_proven_by_this_function']
        results.append({'mode':mode,'shared_shrink':k,'direct_CFG_vector_loss':direct})
    boundaries=[]
    for name,moment,expected in [('zero',(1.,0.,0.),0.),
                               ('harmful',(1.,.2,.04),0.),
                               ('over_unit',(1.,-.2,.04),1.)]:
        xs=copy.deepcopy(records)
        for r in xs:
            for field,value in zip(('base_guided_MSE','guided_error_update_mean_dot','guided_update_mean_square'),moment):r[field]=value
        assert fit_shared_shrink(xs,mode=MODES[0],source_sha256=SHA)['shared_shrink']==expected
        boundaries.append(name)
    refused=[]
    for kind in ('missing_origin','duplicate_origin','foreign_origin','wrong_CFG','nonfinite','negative_energy','Cauchy_violation'):
        xs=copy.deepcopy(records)
        if kind=='missing_origin':xs.pop()
        elif kind=='duplicate_origin':xs[-1]=copy.deepcopy(xs[0])
        elif kind=='foreign_origin':xs[-1]['state']='step31'
        elif kind=='wrong_CFG':xs[-1]['diagnostics']['actual_CFG_coefficients']=[7,-6]
        elif kind=='nonfinite':xs[-1]['guided_error_update_mean_dot']=float('nan')
        elif kind=='negative_energy':xs[-1]['guided_update_mean_square']=-1
        elif kind=='Cauchy_violation':xs[-1]['guided_error_update_mean_dot']=100
        try:fit_shared_shrink(xs,mode=MODES[0],source_sha256=SHA)
        except ValueError:refused.append(kind)
        else:raise AssertionError(kind)
    assert hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()==before
    print(json.dumps({'status':'SHARED_PHASE_SHRINK_CPU_DIRECT_VECTOR_ORACLE_PASS_SYNTHETIC',
        'complete_origins_per_fit':8,'readout_modes':2,'oracle_results':results,
        'bounded_and_degenerate_controls':boundaries,'refusals':refused,
        'source_moments_unchanged':True,'GPU_submissions':0,'ledger_written':False,
        'real_coefficient_fit_or_video_result':False}))


if __name__=='__main__':main()
