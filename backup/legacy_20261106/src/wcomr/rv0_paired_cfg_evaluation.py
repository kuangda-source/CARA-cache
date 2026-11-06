"""Paired current-step controls: complete states, repeats and historical bridges."""
from .rv0_causal import TRACE_KEYS
from .rv0_d46_seed_evaluation import require,state_components

LABELS=['OFF1','OFF2','BASE_first','SINGLE_second','PAIRED_first','PAIRED_second','SINGLE_first','BASE_second']
ENCODED=['OFF1','BASE_first','PAIRED_first','SINGLE_first']
PIPELINE=['decode_input','decode_output','guardrail_input','guardrail_output','save_input']


def verify_paired_row(row,deep_count):
    require(row['target_call']==46 and row['slot']==1 and row['prepare_calls']==1
        and row['flags_before']==row['flags_after'] and row['sample_return_sha256']==row['final_latent_sha256'],
        'Registered paired parent/config boundary differs')
    require(all(len(row[k])==(36 if k=='solver_outputs' else 72) for k in TRACE_KEYS),'Complete paired parent missing')
    require([e['stage'] for e in row['pipeline']]==PIPELINE,'Original parent pipeline differs')
    inventory=set(row['final_components'])
    require({'output','cpu_rng','python_rng','numpy_rng','cuda_rng','explicit_generators','net.cnt','solver._step_index'}<=inventory,
        'Complete state families missing')
    state_components(row['final_components'],inventory,output=row['final_latent_sha256'])
    by={c['label']:c for c in row['children']}
    require(list(by)==LABELS and len(row['children'])==8,'Eight ordered paired suffix controls required')
    tail={k:row[k][22 if k=='solver_outputs' else 44:] for k in TRACE_KEYS}
    for label in ['OFF1','OFF2','BASE_first','BASE_second']:
        c=by[label]
        require(all(c[k]==tail[k] for k in TRACE_KEYS) and c['final_latent_sha256']==row['final_latent_sha256']
            and c['record']['final_state_components']==row['final_components'],'Native BASE/OFF differs from parent')
    for x,y in [('OFF1','OFF2'),('BASE_first','BASE_second'),('SINGLE_first','SINGLE_second'),('PAIRED_first','PAIRED_second')]:
        a,b=by[x],by[y]
        require(all(a[k]==b[k] for k in TRACE_KEYS+['final_latent_sha256','pre45','pre46'])
            and a['record']['final_state_components']==b['record']['final_state_components']
            and a['record']['action_report']==b['record']['action_report'],'Strict paired repeat differs')
    base=by['BASE_first'];single=by['SINGLE_first'];paired=by['PAIRED_first']
    require(base['pre46']==single['pre46'] and all(base[k][:1]==single[k][:1] for k in ('outputs','deep','banks')),
        'BASE/SINGLE current prefix must match')
    for label,c in by.items():
        rec=c['record'];report=rec['action_report'];events=report['suffix_events']
        require(c['status']=='COMPLETE_SUFFIX_NOT_RV_LABEL' and rec['parent_restored']
            and rec['completed_updates']==22 and rec['planned_remaining_updates']==14
            and all(len(c[k])==(14 if k=='solver_outputs' else 28) for k in TRACE_KEYS)
            and [e['call'] for e in events]==list(range(45,73)),'Full paired suffix coverage missing')
        state_components(rec['final_state_components'],inventory,fingerprint=rec['final_state_sha256'],output=c['final_latent_sha256'])
        for at in ('pre45','pre46'):
            state_components(c[at]['components'],inventory,fingerprint=c[at]['fingerprint'])
            require(all(c[at]['own_history']),'Both own-CFG histories required')
        require(c['pre45']==base['pre45'] and c['inputs'][:2]==base['inputs'][:2],
            'Same pre45 and current two model inputs required')
        mode='PAIRED' if label.startswith('PAIRED') else 'SINGLE' if label.startswith('SINGLE') else 'OFF'
        calls={'OFF':[],'SINGLE':[46],'PAIRED':[45,46]}[mode]
        require(c['action']==mode and report['plan']=={'mode':mode,'solver_step':23,'maximum_age_solver_steps':32}
            and report['requested_full_calls']==calls and report['decision_interventions']==len(calls)
            and report['remaining_policy']=='ORIGINAL_WC_ADAPTIVE' and not report['budget_matched']
            and report['current_truth_used_for_decision'] is False and report['RV_label'] is False,
            'Current step-only paired plan differs')
        require(all(d in (0,deep_count) for d in c['deep'])
            and ['C' if d==0 else 'D' for d in c['deep']]==[e['actual_action'] for e in events],
            'Actual deep work differs from action trace')
        require(events[-3]['native_cycle_reset'] and c['deep'][-2:]==[deep_count,deep_count],'Protected WC70/terminal tail differs')
        for e in events:
            require(e['cfg_slot']==(e['call']-1)%2 and e['solver_step']==(e['call']-1)//2+1
                and e['current_deep_truth_used'] is False,'CFG/grid or no-current-teacher condition differs')
            if e['call'] in calls:
                require(e['requested']=='D' and e['paid_probe'] and e['actual_action']=='D'
                    and 1<=e['age_solver_steps']<=32,'Legal paid own-CFG full action missing')
            else:
                require(e['requested'] is None and (not e['paid_probe'] or e['selected_skip']==e['native_skip']),
                    'Native continuation changed outside current actions')
    # Refreshing CFG0 may legitimately change cache state before CFG1.
    # Keep input equality; do not demand pre46 full-state equality for PAIRED.
    require(single['record']['action_report']['suffix_events'][1]['native_skip']==base['record']['action_report']['suffix_events'][1]['native_skip'],
        'Unchanged SINGLE call45 must preserve current46 proposal')
    decoded={c['label']:c for c in row['decoded_children']}
    require(list(decoded)==ENCODED,'Four ordered child encodings required')
    for c in decoded.values():
        require(c['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE' and c['flags_before']==c['flags_after']
            and [e['stage'] for e in c['pipeline']]==PIPELINE,'Child pipeline/flags incomplete')
    require(decoded['OFF1']['pipeline']==decoded['BASE_first']['pipeline']==row['pipeline']
        and decoded['OFF1']['artifact']['sha256']==decoded['BASE_first']['artifact']['sha256']==row['artifact']['sha256'],
        'Parent/OFF/BASE encoding byte bridge differs')
    return {'strict_repeat_groups':4,'pre45_shared_state':True,'current_model_inputs_equal':True,
        'paired_pre46_state_may_change':True,'parent_OFF_BASE_bridge':True,'single_action_RV_labels':False}


def verify_historical_bridges(row,original):
    require(all(row[k]==original[k] for k in TRACE_KEYS)
        and row['final_latent_sha256']==original['final_latent_sha256']
        and row['final_components']==original['final_components'],'Original seed2 parent raw-state bridge differs')
    current={c['label']:c for c in row['children']};prior={c['label']:c for c in original['children']}
    decoded={c['label']:c['artifact'] for c in row['decoded_children']}
    olddecoded={c['label']:c['artifact'] for c in original['decoded_children']}
    for name,oldname in [('BASE_first','BASE_first'),('SINGLE_first','REFRESH_first')]:
        a,b=current[name],prior[oldname]
        require(all(a[k]==b[k] for k in TRACE_KEYS+['final_latent_sha256','pre46'])
            and a['record']['final_state_components']==b['record']['final_state_components'],
            'Historical BASE/SINGLE raw-state bridge differs')
        require(decoded[name]['sha256']==olddecoded[oldname]['sha256']
            and decoded[name]['bytes']==olddecoded[oldname]['bytes'],'Historical encoded byte bridge differs')
    return {'original_parent_BASE_SINGLE_raw_state_and_encoded_bridges':True}
