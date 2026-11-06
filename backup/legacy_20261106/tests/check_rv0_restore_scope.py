"""CPU refusals for the frozen two-scene restore card and cumulative budget."""
import copy
import importlib.util
import json
from pathlib import Path


def run(config=None):
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('restore_scope',root/'src/wcomr/rv0_restore_scope.py')
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    if config is None:config=json.loads((root/'configs/wc_rv0_restore_r1.json').read_text())
    gate.validate_scope(config)
    budget={'cap_gpu_hours':12,'used_gpu_hours':10.713586944445915,'gpu_jobs_launched':44}
    accepted=gate.budget_gate(budget,config);count=0
    for name,value in [('sample_names',config['sample_names'][:1]),('suffix_labels',['A']),
                       ('snapshot_step',21),('action_interventions',1),('complete_RV0_acceptance',True),
                       ('logical_copy_cap_bytes',12*(1<<30)),('transient_copy_factor',1),
                       ('workspace_reserve_bytes',0),('timeout_seconds',4500),('RV_labels',True)]:
        changed=copy.deepcopy(config);changed[name]=value
        try:gate.validate_scope(changed)
        except ValueError:count+=1
        else:raise AssertionError('Changed restore scope accepted: '+name)
    for changed in [{**budget,'cap_gpu_hours':4},{**budget,'used_gpu_hours':11},
                    {**budget,'used_gpu_hours':float('nan')},{**budget,'other_inflight':{}},
                    {**budget,'used_gpu_hours':-1}]:
        try:gate.budget_gate(changed,config)
        except ValueError:count+=1
        else:raise AssertionError('Changed budget accepted')
    cost=gate.cost_gate(config)
    for name,value in [('conditional_estimated_seconds',float('nan')),
                       ('conditional_estimated_seconds',3901),('full_video_proxy_equivalents',5),
                       ('incremental_allowance_seconds',0),('complete_cost_bound_validated',True)]:
        changed=copy.deepcopy(config);changed['cost_admission'][name]=value
        try:gate.cost_gate(changed)
        except ValueError:count+=1
        else:raise AssertionError('Changed cost admitted: '+name)
    assert type(config['gpu_execution_selected']) is bool and not config['GPU_submitted']
    assert config['budget_reserved_seconds']==0
    return {'status':'RESTORE_SCOPE_COST_CPU_CONTROLS_PASS_NO_GPU_SUBMITTED',
            'checks':count+2,'valid_scope_and_budget':accepted,'cost_admission':cost,
            'GPU_submissions':0}


if __name__=='__main__':print(json.dumps(run()))
