"""Reject invalid equal-budget placement scopes before preparing any phase."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from wcomr.fixed_refresh_mask import FixedRefreshMask
from wcomr.selective_output import run_selective_output
from wcomr.selective_refresh_policy import SparsePlacementPolicy, SparseRefreshPolicy


def run(manifest):
    data=manifest['fixed_mask']
    mask=FixedRefreshMask(data['sample_name'],data['model_id'],data['condition_id'],
        tuple(data['dense_calls']),data['source_receipt_sha256'])
    context=('CPU_PREFLIGHT:human_199',data['model_id'],data['condition_id'])
    layers=tuple(manifest['legacy_policy']['sparse_layers'])
    def placement(name):
        value=manifest[name]
        return SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=tuple(
            tuple(v) for v in value['per_cfg_eligible_ordinals']))
    policies=(SparseRefreshPolicy(layers,2),placement('first_S_matched_policy'),placement('unconstrained_policy'))
    net=SimpleNamespace(probe_depth=2,blocks=[None]*28)
    inference=SimpleNamespace(pipe=SimpleNamespace(model=SimpleNamespace(net=net)))
    sample=SimpleNamespace(name='human_199')
    checks=[]
    for case in ('wrong_S_quota','out_of_range_ordinal','missing_first_control','wrong_S_layers',
                 'oracle_in_legacy_comparison','unknown_comparison','bad_historical_digest','existing_identity'):
        chosen=list(policies);state={};comparison='forecast_placement';digest='4'*64
        if case=='wrong_S_quota':
            slots=chosen[1].per_cfg_eligible_ordinals
            chosen[1]=SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=(slots[0][:-1],slots[1]))
        elif case=='out_of_range_ordinal':
            slots=chosen[2].per_cfg_eligible_ordinals
            chosen[2]=SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=(slots[0][:-1]+(100,),slots[1]))
        elif case=='missing_first_control':
            slots=chosen[1].per_cfg_eligible_ordinals
            chosen[1]=SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=((2,)+slots[0][1:],slots[1]))
        elif case=='wrong_S_layers':
            chosen[2]=SparsePlacementPolicy((2,3,5),per_cfg_eligible_ordinals=chosen[2].per_cfg_eligible_ordinals)
        elif case=='oracle_in_legacy_comparison':comparison='layer_cadence'
        elif case=='unknown_comparison':comparison='unregistered'
        elif case=='bad_historical_digest':digest='not-a-SHA'
        else:state={'measurement':{'existing':'preserve'}}
        before=deepcopy(state)
        try:
            run_selective_output(inference,sample,None,{},mask,tuple(chosen),state=state,
                save=lambda:None,output=Path('/NO_GENERATION'),inference_module=None,
                context=context,mode_setup=None,comparison=comparison,expected_D_sha256=digest)
        except ValueError as error:checks.append({'case':case,'error':str(error),'no_phase_started':state==before})
        else:raise AssertionError('Invalid placement preflight accepted: '+case)
        assert state==before
    return {'status':'ACTUAL_CONTROLLER_PREFLIGHT_EIGHT_REJECTIONS_CPU_PASS',
        'CPU_only':True,'checks':checks,'actual_weights_or_video':False,
        'limits':'Actual current controller early guards, with geometry/sample stubs; this is not a GPU asset, scope or resource admission gate.'}
