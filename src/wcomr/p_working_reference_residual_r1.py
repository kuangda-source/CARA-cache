"""Scoring-only P prewarp residual candidate with coefficients from true D.

This function has no generator, controller, head or teacher access. The
caller must bind working_probe and working_prewarp_residual to its actual P
cache. Full source-hook/warp/sampler integration remains a separate CPU gate.
"""
import math

import torch


@torch.no_grad()
def predict_P_reference(*, calibrator, context, step, slot, working_source,
                        current_probe, working_probe, working_prewarp_residual,
                        official, beta_mode='scalar'):
    if beta_mode not in ('scalar','unit') or type(step) is not int or slot not in (0,1):
        raise ValueError('Registered scalar/unit mode and current branch required')
    if calibrator.context!=context:
        raise ValueError('Foreign true-D calibration context')
    if (not isinstance(working_source,dict) or working_source.get('kind')!='P'
            or working_source.get('context')!=list(context) or working_source.get('slot')!=slot
            or type(working_source.get('created_step')) is not int
            or not 1<=working_source['created_step']<step
            or working_source.get('RA_zero_risk_reset_allowed') is not False
            or working_source.get('creation_error')!='UNKNOWN_NOT_ZERO'):
        return official,{'status':'invalid_P_source_fallback','beta':None}
    values=(current_probe,working_probe,working_prewarp_residual,official)
    if (not all(isinstance(t,torch.Tensor) and t.is_floating_point() and torch.isfinite(t).all()
                and t.shape==current_probe.shape and t.device==current_probe.device
                and t.dtype==current_probe.dtype for t in values)):
        return official,{'status':'invalid_P_geometry_fallback','beta':None}
    anchors=calibrator.anchors
    if (not anchors or any(a.step>=step or a.step>=working_source['created_step'] for a in anchors)
            or not all(calibrator._valid_pair(a.probe,a.residual)
                and a.probe.shape==current_probe.shape and a.probe.device==current_probe.device
                and a.probe.dtype==current_probe.dtype for a in anchors)):
        return official,{'status':'invalid_D_history_fallback','beta':None}
    if beta_mode=='unit':
        beta=1.
    else:
        if len(anchors)<2 or not calibrator.pairs or calibrator.denominator<=calibrator.min_energy:
            return official,{'status':'insufficient_D_fit_fallback','beta':None}
        beta=calibrator.numerator/(calibrator.denominator+calibrator.ridge)
        if not math.isfinite(beta):
            return official,{'status':'nonfinite_D_beta_fallback','beta':None}
        beta=max(-calibrator.clip,min(calibrator.clip,beta))
    prediction=working_prewarp_residual+beta*(current_probe-working_probe)
    if not torch.isfinite(prediction).all():
        return official,{'status':'nonfinite_P_prediction_fallback','beta':beta}
    return prediction,{'status':'P_working_reference_'+beta_mode,'beta':beta,
        'working_created_step':working_source['created_step'],'working_age':step-working_source['created_step'],
        'true_D_steps':[a.step for a in anchors],'P_updates_D_statistics':False,
        'coordinate':'PREWARP_RESIDUAL','quality_or_full_sampler_claim':False}
