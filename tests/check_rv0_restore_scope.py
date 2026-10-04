"""CPU refusals for the frozen two-scene restore card and cumulative budget."""
import copy
import importlib.util
import json
from pathlib import Path


def run():
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('restore_scope',root/'src/wcomr/rv0_restore_scope.py')
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    config=json.loads((root/'configs/wc_rv0_restore_r1.json').read_text())
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
    assert not config['gpu_execution_selected'] and not config['GPU_submitted']
    return {'status':'RESTORE_SCOPE_CPU_CONTROLS_PASS_NO_GPU_SELECTED',
            'checks':count+1,'valid_scope_and_budget':accepted,'GPU_submissions':0}


if __name__=='__main__':print(json.dumps(run()))
