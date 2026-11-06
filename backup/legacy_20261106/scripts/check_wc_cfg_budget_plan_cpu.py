#!/usr/bin/env python3
"""Observed-parent mask/age preflight, not actual model/router or GPU readiness."""
import copy
import gzip
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.rv0_cfg_budget_plan import CFGBudgetPlan, MODES, full_counts, mask_sha256


def main():
    reg_path=Path('manifests/wc_w3_cfg_budget_matched_cpu_preregistration_20261008.json');reg=json.loads(reg_path.read_text())
    for n,h in reg['input_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
    original=json.loads(gzip.decompress(Path(reg['runner_ref']).read_bytes()));row=original['cases'][0]['WC']['requests'][0]
    parent=tuple('D' if n else 'C' for n in row['deep']);assert list(parent)==reg['parent_action_mask']
    initial=next(x for x in row['children'] if x['label']=='BASE_first')['pre45']['own_history'];cases=[]
    for mode in MODES:
        plan=CFGBudgetPlan(mode,parent).validate();mask=plan.action_mask();history=copy.deepcopy(initial);age_records=[]
        for call in range(45,73):
            slot=(call-1)%2;step=(call-1)//2+1
            if mask[call-1]=='C' or call in (45,46,47,48):
                assert len(history[slot])>=2;age=step-history[slot][-1];assert 1<=age<=32
                age_records.append({'call':call,'CFG':slot,'planned_action':mask[call-1],'age_solver_steps':age})
            if mask[call-1]=='D':history[slot].append(step)
            if call==70:history=[[],[]]
        assert full_counts(mask)==(18,17) and all(mask[c-1]==parent[c-1] for c in range(49,73))
        cases.append({'mode':mode,'swaps':[list(p) for p in plan.swaps],'mask':list(mask),'mask_sha256':mask_sha256(mask),'per_CFG_full_counts':list(full_counts(mask)),'current_actions':list(mask[44:46]),'donor_actions':list(mask[46:48]),'historical_structural_age_records':age_records,'maximum_historical_age':max(x['age_solver_steps'] for x in age_records)})
    valid=CFGBudgetPlan('BASE',parent);mutants={'bad_mode':replace(valid,mode='BAD'),'mutable_mask':replace(valid,parent_mask=list(parent)),'truncated_mask':replace(valid,parent_mask=parent[:-1]),'wrong_prefix':replace(valid,prefix_calls=43),'wrong_age_cap':replace(valid,maximum_age_solver_steps=33),'noninteger_age':replace(valid,maximum_age_solver_steps=32.0)}
    for name,index,value in [('invalid_action',45,'X'),('current_not_reuse',44,'D'),('donor_not_full',46,'C'),('initialization_changed',0,'C'),('terminal_full_removed',70,'C')]:
        m=list(parent);m[index]=value;mutants[name]=replace(valid,parent_mask=tuple(m))
    refusals=[]
    for name,plan in mutants.items():
        try:plan.validate()
        except ValueError:refusals.append(name)
        else:raise AssertionError('Unsafe registered position plan accepted: '+name)
    assert len(refusals)==11 and [x['current_actions'] for x in cases]==[['C','C'],['D','C'],['C','D'],['D','D']]
    out={'status':'CFG_BUDGET_MATCHED_OBSERVED_MASK_AND_HISTORICAL_AGE_STRUCTURAL_CPU_PASS_NOT_ROUTER_NOT_GPU','preregistration_ref':str(reg_path),'parent_mask_sha256':mask_sha256(parent),'cases':cases,'mutation_refusals':refusals,'two_CFG_full_counts':[18,17],'all_four_cells_total_full':35,'original_prefix_and_calls49_to72_unchanged':True,'current_donor_source':'Nearest following true-full call of each CFG branch; no candidate endpoint selection','model_or_router_integration_verified':False,'real_cache_finiteness_or_gpu_legality_verified':False,'forecast_finalized':False,'GPU_execution_selected':False,'CUDA_initialized':False,'GPU_submissions':0}
    p=Path('reports/wc_w3_cfg_budget_matched_mask_structural_cpu_20261008.json')
    with p.open('x') as f:f.write(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','two_CFG_full_counts','all_four_cells_total_full','mutation_refusals','GPU_submissions')}))

if __name__=='__main__':main()
