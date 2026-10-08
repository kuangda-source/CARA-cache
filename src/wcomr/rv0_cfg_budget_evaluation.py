"""Verify full masks, per-CFG budgets, all states, two prefix bridges and five repeats."""
from .rv0_causal import TRACE_KEYS
from .rv0_d46_seed_evaluation import require,state_components
from .rv0_cfg_factorial_evaluation import validate_solver_configuration,solver_configuration,LABELS,ENCODED,PIPELINE
from .rv0_cfg_budget_actions import POLICY
from .rv0_cfg_budget_plan import CFGBudgetPlan,full_counts,mask_sha256


def verify_cfg_budget_row(row,deep_count,registered_mask):
    parent=tuple(registered_mask);CFGBudgetPlan('BASE',parent).validate()
    require(row['target_call']==46 and row['slot']==1 and row['prepare_calls']==1
        and row['flags_before']==row['flags_after'] and row['sample_return_sha256']==row['final_latent_sha256'],'Parent/prepare boundary differs')
    require(all(len(row[k])==(36 if k=='solver_outputs' else 72) for k in TRACE_KEYS),'Complete parent coverage missing')
    require(tuple('D' if x else 'C' for x in row['deep'])==parent and all(x in (0,deep_count) for x in row['deep']),'New native parent differs from registered mask')
    require([e['stage'] for e in row['pipeline']]==PIPELINE,'Parent original video pipeline missing')
    inventory=set(row['final_components']);state_components(row['final_components'],inventory,output=row['final_latent_sha256'])
    conf=validate_solver_configuration(row['final_solver_configuration'],row['final_components'])
    by={c['label']:c for c in row['children']};require(list(by)==LABELS and len(row['children'])==10,'Ten ordered controls required')
    for label,c in by.items():
        rec=c['record'];report=rec['action_report'];events=report['suffix_events']
        mode='OFF' if label.startswith('OFF') else label.split('_')[0]
        plan=None if mode=='OFF' else CFGBudgetPlan(mode,parent).validate()
        expected=parent if plan is None else plan.action_mask()
        require(c['status']=='COMPLETE_SUFFIX_NOT_RV_LABEL' and c['action']==mode and rec['parent_restored']
            and rec['completed_updates']==22 and rec['planned_remaining_updates']==14
            and all(len(c[k])==(14 if k=='solver_outputs' else 28) for k in TRACE_KEYS),'Complete restored suffix missing')
        state_components(rec['final_state_components'],inventory,fingerprint=rec['final_state_sha256'],output=c['final_latent_sha256'])
        require(validate_solver_configuration(c['final_solver_configuration'],rec['final_state_components'])==conf,'Within-card raw solver dictionary changed')
        for at in ('pre45','pre46'):
            point=c[at];state_components(point['components'],inventory,fingerprint=point['fingerprint'])
            require(all(point['own_history']) and validate_solver_configuration(point['solver_configuration'],point['components'])==conf,'Full current state/history/config missing')
        require(c['pre45']==by['BASE_first']['pre45'] and c['inputs'][:2]==by['BASE_first']['inputs'][:2],'Shared pre45/current model inputs differ')
        recorded=report['plan']
        require((recorded is None)==(plan is None),'Recorded fixed-plan role differs')
        if plan is not None:
            require(recorded['mode']==mode and tuple(recorded['parent_mask'])==parent and recorded['prefix_calls']==44
                and recorded['maximum_age_solver_steps']==32,'Frozen plan source changed')
        require(report['parent_mask_sha256']==mask_sha256(parent) and report['actual_mask_sha256']==mask_sha256(expected)
            and tuple(report['actual_actions'])==expected and report['per_CFG_full_counts']==[18,17]
            and report['quota_matched_per_CFG'] and report['budget_matched'] and report['current_truth_used_for_decision'] is False
            and report['RV_label'] is False and report['planned_action_changes']==(0 if plan is None else 2*len(plan.swaps))
            and report['remaining_policy']==('ORIGINAL_WC_ADAPTIVE_REFERENCE' if plan is None else POLICY),'Actual masks/quota/source/estimand differ')
        require([e['call'] for e in events]==list(range(45,73)),'Complete action event grid missing')
        require(all(x in (0,deep_count) for x in c['deep']) and tuple('D' if x else 'C' for x in c['deep'])==expected[44:]
            and full_counts(tuple('D' if x else 'C' for x in row['deep'][:44])+tuple('D' if x else 'C' for x in c['deep']))==(18,17),'Actual deep work differs from fixed separate-CFG quota')
        swapped=() if plan is None else tuple(x for pair in plan.swaps for x in pair)
        for e in events:
            call=e['call'];require(e['cfg_slot']==(call-1)%2 and e['solver_step']==(call-1)//2+1
                and e['actual_action']==expected[call-1] and e['current_deep_truth_used'] is False,'Actual action/CFG/source grid differs')
            if plan is None:require(e['requested'] is None and (not e['paid_probe'] or e['selected_skip']==e['native_skip']),'Original OFF continuation changed')
            elif e['paid_probe']:
                require(e['requested']==e['planned_action']==expected[call-1] and e['selected_skip']==(expected[call-1]=='C'),'Fixed masked decision differs')
            else:require(call in (71,72) and expected[call-1]=='D','Unpaid fixed decision outside full tail')
            if plan is not None and (expected[call-1]=='C' or call in swapped):
                require(e['paid_probe'] and 1<=e['age_solver_steps']<=32,'Paid legal own-CFG position decision missing')
        require(events[-3]['native_cycle_reset'] and c['deep'][-2:]==[deep_count,deep_count],'Reset/full tail changed')
        require(report['native_tail_proposal_preservation_required'] is False,'Tail proposal preservation wrongly required')
        paid_count=sum(e['paid_probe'] for e in events) if plan is not None else 0
        require(report['paid_mask_decisions']==paid_count,'Paid-mask count differs')
        require(report['tail_native_proposal_disagreements']==[e['call'] for e in events if e.get('tail_native_proposal_disagreement')],'Tail disagreement audit differs')
    tail={k:row[k][22 if k=='solver_outputs' else 44:] for k in TRACE_KEYS}
    for label in ('OFF1','OFF2','BASE_first','BASE_second'):
        c=by[label];require(all(c[k]==tail[k] for k in TRACE_KEYS) and c['final_latent_sha256']==row['final_latent_sha256']
            and c['record']['final_state_components']==row['final_components'],'Parent/OFF/BASE function bridge differs')
    for a,b in [('OFF1','OFF2')]+[(x+'_first',x+'_second') for x in ('BASE','CFG0','CFG1','PAIRED')]:
        require(all(by[a][k]==by[b][k] for k in TRACE_KEYS+['final_latent_sha256','pre45','pre46','final_solver_configuration'])
            and by[a]['record']['final_state_components']==by[b]['record']['final_state_components']
            and by[a]['record']['action_report']==by[b]['record']['action_report'],'Strict repeat differs')
    for a,b in [('BASE_first','CFG1_first'),('CFG0_first','PAIRED_first')]:
        require(by[a]['pre46']==by[b]['pre46'] and all(by[a][k][:1]==by[b][k][:1] for k in ('outputs','deep','banks')),'Current first-branch prefix bridge differs')
    decoded={c['label']:c for c in row['decoded_children']};require(list(decoded)==ENCODED,'Five ordered child encodings missing')
    for d in decoded.values():require(d['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE' and d['flags_before']==d['flags_after']
        and [e['stage'] for e in d['pipeline']]==PIPELINE,'Original guarded encoding pipeline changed')
    require(decoded['OFF1']['pipeline']==decoded['BASE_first']['pipeline']==row['pipeline']
        and decoded['OFF1']['artifact']['sha256']==decoded['BASE_first']['artifact']['sha256']==row['artifact']['sha256'],'Parent/OFF/BASE byte bridge differs')
    return {'strict_repeat_groups':5,'pre45_shared_state':True,'current_model_inputs_equal':True,'two_pre46_prefix_bridges':True,
        'per_CFG_full_counts':[18,17],'all_four_cells_total_full':35,'parent_OFF_BASE_bridge':True,
        'single_action_RV_labels':False,'clean_speed_measurement':False}
