#!/usr/bin/env python3
"""Registered post-result CPU diagnostics; no new rollout, fitting or routing labels."""
import gzip
import hashlib
import json
import math
from pathlib import Path

REG='manifests/wc_w3_cfg_factorial_followup_cpu_preregistration_20261008.json'


def main():
    reg=json.loads(Path(REG).read_text())
    for name,digest in reg['input_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
    runner=json.loads(gzip.decompress(Path(reg['runner_ref']).read_bytes()))
    score=json.loads(gzip.decompress(Path(reg['score_ref']).read_bytes()))
    row=runner['cases'][0]['WC']['requests'][0];cells={n:next(x for x in row['children'] if x['label']==n+'_first') for n in ('BASE','CFG0','CFG1','PAIRED')}
    ref=cells['BASE'];schedules={}
    for name,cell in cells.items():
        events=cell['record']['action_report']['suffix_events']
        schedules[name]={'current':[e['call'] for e in events[:2] if e['actual_action']=='D'],'future_by_CFG':[[e['call'] for e in events[2:] if e['cfg_slot']==slot and e['actual_action']=='D'] for slot in (0,1)],'next_step_actual_actions':[e['actual_action'] for e in events[2:4]]}
        schedules[name]['future_removed_vs_BASE']=[[n for n in schedules['BASE']['future_by_CFG'][slot] if n not in schedules[name]['future_by_CFG'][slot]] for slot in (0,1)]
        schedules[name]['future_added_vs_BASE']=[[n for n in schedules[name]['future_by_CFG'][slot] if n not in schedules['BASE']['future_by_CFG'][slot]] for slot in (0,1)]
    signal_fields=['age_solver_steps','paid_input_drift','paid_probe_drift','dynamic_threshold','accumulator_before_action','native_skip','paid_probe']
    a=cells['CFG1']['record']['action_report']['suffix_events'][1];b=cells['PAIRED']['record']['action_report']['suffix_events'][1]
    signals={n:{k:cell['record']['action_report']['suffix_events'][1].get(k) for k in signal_fields} for n,cell in cells.items() if n in ('CFG1','PAIRED')}
    changed=[k for k in sorted(ref['pre46']['components']) if ref['pre46']['components'][k]!=cells['CFG0']['pre46']['components'][k]]
    losses=score['losses'];counts=score['factorial_summary']['actual_counts'];costs=score['factorial_summary']['control_costs']
    effects=[]
    for name,left,right in [('CFG1_given_CFG0_reuse','BASE','CFG1'),('CFG1_given_CFG0_full','CFG0','PAIRED')]:
        changes=[x-y for x,y in zip(losses[left]['frame_distances'],losses[right]['frame_distances'])]
        effects.append({'context':name,'comparison':right+'_vs_'+left,'signed_quality':math.fsum(changes)/93,'relative_fidelity_improvement_percent':100*math.fsum(changes)/93/losses[left]['mean_LPIPS'],'whole_full_saved':sum(counts[left]['whole_CFG'])-sum(counts[right]['whole_CFG']),'diagnostic_seconds_saved':math.fsum(costs[left])/2-math.fsum(costs[right])/2,'formal_RV_training_label':False})
    trace_pairs={}
    for name,cell in cells.items():
        trace_pairs[name]={'first_model_input_difference_vs_BASE':next((45+i for i,(x,y) in enumerate(zip(ref['inputs'],cell['inputs'])) if x!=y),None),'first_model_output_difference_vs_BASE':next((45+i for i,(x,y) in enumerate(zip(ref['outputs'],cell['outputs'])) if x!=y),None),'first_solver_update_difference_vs_BASE':next((23+i for i,(x,y) in enumerate(zip(ref['solver_outputs'],cell['solver_outputs'])) if x!=y),None)}
    out={'status':'EXISTING_EXPOSED_FACTORIAL_CONTEXT_AND_ROUTE_CPU_DIAGNOSIS_COMPLETE_NOT_CAUSAL_MEDIATION','preregistration_ref':REG,'all_inputs_verified':True,'current_two_model_inputs_equal_all_cells':all(x['inputs'][:2]==ref['inputs'][:2] for x in cells.values()),'CFG1_requested_D_paid_own_CFG_signals':signals,'CFG1_paid_signal_projection_equal':signals['CFG1']==signals['PAIRED'],'pre46_changed_component_names_after_CFG0_full':changed,'CFG1_full_output_at46_equal_given_CFG0_C_or_D':cells['CFG1']['outputs'][1]==cells['PAIRED']['outputs'][1],'pre46_solver_components_equal':all(ref['pre46']['components'][k]==cells['CFG0']['pre46']['components'][k] for k in ref['pre46']['components'] if k.startswith('solver.')),'pre46_current_latent_equal':ref['pre46']['components']['output']==cells['CFG0']['pre46']['components']['output'],'own_history_pre46':{n:x['pre46']['own_history'] for n,x in cells.items()},'conditional_total_effects':effects,'future_full_call_sets':schedules,'first_divergence':trace_pairs,'all_four_cell_denominators_retained':True,'post_result_exploratory_not_independent_confirmation':True,'no_proxy_sufficiency_claim_or_gate_fit':True,'CUDA_initialized':False,'GPU_submissions':0}
    p=Path('reports/wc_w3_cfg_factorial_context_cpu_results_20261008.json')
    with p.open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:out[k] for k in ('status','CFG1_paid_signal_projection_equal','CFG1_full_output_at46_equal_given_CFG0_C_or_D','pre46_changed_component_names_after_CFG0_full','conditional_total_effects')}))

if __name__=='__main__':main()
