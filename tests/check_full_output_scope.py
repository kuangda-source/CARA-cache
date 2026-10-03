import copy
from wcomr.full_output_scope import validate_scope, cost_gate, budget_gate

def run(config):
    validate_scope(config);cost_gate(config)
    controls=[]
    for key,value in [("planned_total_phases",4),("planned_output_files",4),("dense_fallback_layers",[6,23]),("deployment_sparse",False),("state_steps",[13,21,33]),("max_gpu_wall_seconds",1800),("policy",{"sim":.1,"cdf":.97})]:
        wrong=copy.deepcopy(config);wrong[key]=value
        try: validate_scope(wrong)
        except ValueError: controls.append(key)
        else: raise AssertionError("Altered scope accepted: "+key)
    budget={"cap_gpu_hours":12,"used_gpu_hours":6.055044055960606,"budget_authorization_ref":"authorized"}
    budget_gate(budget,6000)
    for wrong in [dict(budget,cap_gpu_hours=4),dict(budget,used_gpu_hours=11),dict(budget,other_inflight={})]:
        try: budget_gate(wrong,6000)
        except ValueError: controls.append("budget")
        else: raise AssertionError("Invalid admission accepted")
    return {"status":"FULL_SIX_SCOPE_COST_LEDGER_CPU_PASS","refused":controls}
