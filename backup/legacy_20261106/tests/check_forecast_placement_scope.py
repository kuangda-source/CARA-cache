"""Pure scope/cost/budget rejection controls; actual mask/assets separately."""
from copy import deepcopy
from pathlib import Path
import importlib.util


def run(c):
    p=Path(__file__).parents[1]/'src/wcomr/forecast_placement_scope.py'
    spec=importlib.util.spec_from_file_location('forecast_placement_scope',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.validate_scope(c);m.cost_gate(c)
    b={'used_gpu_hours':8.215651676683272,'cap_gpu_hours':12,
       'budget_authorization_ref':'manifests/budget_authorization_20261003.json'}
    m.budget_gate(b,2400)
    checks=['exact_six_output_policy_cost_current_budget']
    for key,value in [('planned_output_files',4),('max_gpu_wall_seconds',1800),('online_policy',True),
        ('three_dense_artifacts_must_match',False),('legacy_SD_output_gate_before_new_variants',False),
        ('shared_entry_RNG_across_control_and_measurement',False),('previous_legacy_SD_sha256','0'*64),
        ('mask_source_receipt_sha256','0'*64),('deployment_sparse',False),('gpu_execution_selected','yes'),
        ('same_S_per_CFG',[5,5]),('same_S_operators_per_candidate',230),
        ('comparison','layer_cadence'),('causal_refresh_value_labels',True),
        ('placement_manifest_sha256','0'*64),('previous_selective_receipt_sha256','0'*64)]:
        q=deepcopy(c);q[key]=value
        try:m.validate_scope(q)
        except ValueError:checks.append('reject_'+key)
        else:raise AssertionError('Scope change accepted: '+key)
    for key,value in [('sparse_layers',[2,3,6]),('every',True),('name','picked_after_video')]:
        q=deepcopy(c);q['variants'][1][key]=value
        try:m.validate_scope(q)
        except ValueError:checks.append('reject_variant_'+key)
        else:raise AssertionError('Variant change accepted')
    for slots in ([[4,5,6,7,8,9],[4,5,6,7,8]], [[1,4,5,6,7],[1,4,5,6,7]], [[True,4,5,6,7,8],[1,4,5,6,7]], [[1,4,5,6,7,99],[1,4,5,6,7]]):
        q=deepcopy(c);q['variants'][1]['per_cfg_eligible_ordinals']=slots
        try:m.validate_scope(q)
        except ValueError:checks.append('reject_variant_slots_'+repr(slots))
        else:raise AssertionError('Changed placement accepted')
    for value in (2400,float('nan'),-1,1):
        q=deepcopy(c);q['cost_admission']['planning_envelope_seconds']=value
        try:m.cost_gate(q)
        except ValueError:checks.append('reject_full_cost_'+repr(value))
        else:raise AssertionError('Invalid cost accepted')
    for key,value in [('cap_gpu_hours',16),('used_gpu_hours',11.9),('used_gpu_hours',float('nan')),
                      ('some_inflight',{}),('budget_authorization_ref',None)]:
        q=deepcopy(b);q[key]=value
        try:m.budget_gate(q,2400)
        except ValueError:checks.append('reject_budget_'+key+'_'+repr(value))
        else:raise AssertionError('Invalid budget accepted')
    return {'status':'FORECAST_PLACEMENT_SIX_OUTPUT_SCOPE_COST_BUDGET_CPU_PASS_NOT_GPU',
            'CPU_only':True,'checks':checks,'actual_mask_asset_import_gate':False}
