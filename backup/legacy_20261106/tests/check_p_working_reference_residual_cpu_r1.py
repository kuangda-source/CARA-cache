"""Small mathematical/source-provenance component; no full-flow acceptance."""
import copy
import json
import torch
from wcomr.calibration import ResidualCalibrator
from wcomr.p_working_reference_residual_r1 import predict_P_reference
from wcomr.mid_coverage import tree_digest
from wcomr.partial_mlp_deployment_state import plain


def run():
    context=('P_REFERENCE_COMPONENT_ONLY','model','condition')
    c=ResidualCalibrator();c.reset(context)
    p=torch.tensor([1.,2.,3.,4.]);r=torch.tensor([3.,4.,5.,6.])
    assert c.observe_full(context=context,step=2,probe=p,residual=r)
    assert c.observe_full(context=context,step=6,probe=p+2,residual=r+6)
    before=tree_digest(plain(vars(c)));rng=tree_digest(torch.get_rng_state())
    wp=p+3;wr=r+7;cp=p+4;official=r+6
    source={'kind':'P','slot':0,'context':list(context),'created_step':8,
            'creation_error':'UNKNOWN_NOT_ZERO','RA_zero_risk_reset_allowed':False}
    args=dict(calibrator=c,context=context,step=9,slot=0,working_source=source,
        current_probe=cp,working_probe=wp,working_prewarp_residual=wr,official=official)
    values=[]
    for mode in ('scalar','unit'):
        value,proof=predict_P_reference(**args,beta_mode=mode)
        beta=c.numerator/(c.denominator+c.ridge) if mode=='scalar' else 1.
        assert torch.equal(value,wr+beta*(cp-wp))
        # A different working reference must change this controlled example;
        # it cannot silently fall back to the old D-reference formula.
        assert not torch.equal(value,c.anchors[-1].residual+beta*(cp-c.anchors[-1].probe))
        assert proof['true_D_steps']==[2,6] and proof['working_age']==1
        values.append(proof)
    fallbacks=[]
    for fault in ('future_P','wrong_branch','foreign_P_context','P_as_zero_risk','wrong_geometry','missing_P','insufficient_D_fit'):
        kw=copy.copy(args);kw['working_source']=copy.deepcopy(source)
        if fault=='future_P':kw['working_source']['created_step']=9
        elif fault=='wrong_branch':kw['working_source']['slot']=1
        elif fault=='foreign_P_context':kw['working_source']['context']=['foreign']
        elif fault=='P_as_zero_risk':kw['working_source']['RA_zero_risk_reset_allowed']=True
        elif fault=='wrong_geometry':kw['working_prewarp_residual']=wr[:2]
        elif fault=='missing_P':kw['working_source']=None
        else:
            x=ResidualCalibrator();x.reset(context);x.observe_full(context=context,step=6,probe=p,residual=r);kw['calibrator']=x
        value,proof=predict_P_reference(**kw)
        assert value is official and proof['status'].endswith('fallback'),fault
        fallbacks.append(fault)
    foreign=copy.copy(args);foreign['context']=('foreign',)
    try:predict_P_reference(**foreign)
    except ValueError:foreign_refused=True
    else:raise AssertionError('Foreign true D accepted')
    assert tree_digest(plain(vars(c)))==before and tree_digest(torch.get_rng_state())==rng
    assert not torch.cuda.is_initialized()
    return {'status':'P_WORKING_REFERENCE_MATH_PROVENANCE_CPU_COMPONENT_PASS_NOT_FLOW_OR_SAMPLER',
        'successful_modes':values,'fallbacks':fallbacks,'foreign_D_refused':foreign_refused,
        'true_D_full_state_unchanged':True,'RNG_unchanged':True,'no_head_or_teacher_or_generator_call':True,
        'full_two_flow_callback_checkpoint_CPU_acceptance':False,'GPU_submissions':0}


if __name__=='__main__':print(json.dumps(run()))
