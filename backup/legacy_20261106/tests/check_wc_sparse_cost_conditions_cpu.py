"""Reject timing-scope corruption and false measured-bound interpretation."""
import copy
import importlib.util
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sparse_cost',root/'scripts/analyze_wc_sparse_cost_conditions_cpu.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def rejects(fn):
    try:fn()
    except (ValueError,KeyError):return
    raise AssertionError('Damaged timing/scope was accepted')

# Scenarios must expose the assumed share and never claim a measured upper bound.
rows=mod.opportunity_scenarios(6,35,.05,[0,.25,.5,.75,1])
assert len(rows)==5 and rows[0]['conditional_pipeline_time_reduction_fraction']==0
assert all(r['measured_prediction_bound_or_causal_fit'] is False for r in rows)
rejects(lambda:mod.opportunity_scenarios(36,35,.05,[0,.25,.5,.75,1]))
rejects(lambda:mod.opportunity_scenarios(1,0,.05,[0,.25,.5,.75,1]))
rejects(lambda:mod.opportunity_scenarios(1,35,float('nan'),[0,.25,.5,.75,1]))
rejects(lambda:mod.opportunity_scenarios(1,35,.05,[.5]))
for case in [dict(wall_ms=[1,2],median_wall_ms=1.5),dict(wall_ms=[1,2,float('nan')],median_wall_ms=2),
             dict(wall_ms=[1,2,3],median_wall_ms=1),dict(wall_ms=[0,1,2],median_wall_ms=1)]:
    rejects(lambda case=case:mod.timed_median(case))

# Whole wall can improve while the logged host sampling interval deteriorates.
base={'CFG_calls':72,'trace':[{'deep_executed':True} for _ in range(72)],
      'block_counts':{'full_calls':72},'substage_cuda_isolated':False,'pipeline_wall_seconds':100,
      'substage_host_wall':{n:{'calls':1,'seconds':v} for n,v in zip(['prepare','sample','decode','video_guardrail','write'],[1,50,1,1,1])}}
variant=copy.deepcopy(base);variant['pipeline_wall_seconds']=99;variant['substage_host_wall']['sample']['seconds']=51
observed=mod.pipeline_observation(base,variant)
assert observed['WC_minus_sparse_pipeline_seconds']==1
assert observed['host_substages'][1]['WC_minus_sparse_seconds']==-1
assert observed['host_brackets_are_CUDA_components'] is False
for field in ['changed_actions','isolated_CUDA','repeated_host_calls']:
    damaged=copy.deepcopy(variant)
    if field=='changed_actions':damaged['trace'][0]['deep_executed']=False
    elif field=='isolated_CUDA':damaged['substage_cuda_isolated']=True
    else:damaged['substage_host_wall']['sample']['calls']=2
    rejects(lambda damaged=damaged:mod.pipeline_observation(base,damaged))
print(json.dumps({'status':'SPARSE_COST_TIMING_SCOPE_CPU_GUARDS_PASS','rejection_cases':11,
                  'conditional_scenario_and_opposite_sampling_wall_controls':True,'new_GPU_seconds':0}))
