"""Post-terminal descriptive104 analysis. Never consumes a running prefix or dispatches."""
import itertools
import math
import numpy as np
from .historical_terminal import accept
from ..policy_price_terminal_r1 import record

COMPONENTS = ('method_install_seconds', 'guarded_pipeline_without_write_seconds',
              'video_write_seconds', 'method_cleanup_seconds')
COMPARISONS = (
    ('GRAPH_DIVERSE_ORIGINAL', 'S26_C', 'graph_vs_strong_C'),
    ('GRAPH_DIVERSE_ORIGINAL', 'S26_A_PHASE', 'graph_vs_strong_phase_A'),
    ('GRAPH_DIVERSE_ORIGINAL', 'SHARED26_C', 'graph_vs_shared_C'),
    ('SHARED26_C', 'S26_C', 'placement_at_26D_C'),
    ('S26_A_PHASE', 'S26_C', 'readout_at_26D'),
    ('S25_A_PHASE', 'S25_C', 'readout_at_25D'),
    ('S24_A_PHASE', 'S24_C', 'readout_at_24D'),
    ('S25_C', 'S26_C', 'remove_D21_C'),
    ('S24_C', 'S25_C', 'remove_D20_C'),
    ('S25_A_PHASE', 'S26_A_PHASE', 'remove_D21_phase_A'),
    ('S24_A_PHASE', 'S25_A_PHASE', 'remove_D20_phase_A'),
)


def mean(values):
    return math.fsum(values) / len(values)


def paired_summary(values, members):
    """Enumerate all4^4 prompt-cluster resamples, retaining both rounds per prompt."""
    if len(values) != len(members) or len(members) != 4 or not all(math.isfinite(v) for v in values):
        raise ValueError('Four finite independent prompt means required')
    resampled = [mean([values[i] for i in indices])
                 for indices in itertools.product(range(4), repeat=4)]
    lo, hi = np.quantile(resampled, [.025, .975], method='linear')
    return dict(mean=mean(values), per_prompt=dict(zip(members, values)),
                descriptive_prompt_bootstrap95=[float(lo), float(hi)],
                negative_prompts=sum(v < 0 for v in values), zero_prompts=sum(v == 0 for v in values),
                positive_prompts=sum(v > 0 for v in values), worst_prompt_increase=max(values),
                independent_prompts=4, independent_seeds=1, timing_repeats=2,
                resamples=256, confirmatory_significance_claim=False)


def route(timing, boundaries):
    """Preparation route, never a GPU admission or final policy selection."""
    if not timing['timing_model_validated']:
        action = 'NEW_COST_CALIBRATION_AND_INDEPENDENT_VALIDATION_REQUIRED'
    elif not any(b['planning_feasible_with_fixed_margin'] and b['validation_measured_feasible'] for b in boundaries):
        action = 'NO_TESTED_24_25D_PLANNING_HEADROOM_KEEP_BUDGET'
    else:
        action = 'PREPARE_NEW_P1_CONTRACT_WITH_VALIDATED_COST_INTERFACE'
    if not timing['timing_model_validated']:
        diagnosis = 'COST_MODEL_NOT_VALIDATED'
    elif not boundaries:
        diagnosis = 'NO_BOUNDARY_ROWS'
    elif not any(b['validation_measured_feasible'] for b in boundaries):
        diagnosis = 'TESTED_LAYOUTS_EXCEED_MEASURED_BUDGET'
    elif not any(b['planning_feasible_with_fixed_margin'] and b['validation_measured_feasible'] for b in boundaries):
        diagnosis = 'MEASURED_FEASIBLE_BUT_NO_CONSERVATIVE_PROPOSAL_HEADROOM'
    else:
        diagnosis = 'VALIDATED_MODEL_WITH_TESTED_PROPOSAL_HEADROOM'
    return dict(action=action, diagnosis=diagnosis, selected_policy=None, PG_P2_input_ready=False,
                GPU_dispatch_ready=False, additional_GPU_submissions=0,
                final_budget_relaxed=False, timing_model_refit=False,
                required_before_new_dispatch=['full exposure accounting and equal-information controls',
                    'new frozen candidate/search/SELECT contract', 'new production CPU acceptance',
                    'whole-card quote within226 pool', 'fresh idle exclusive GPU admission'])



def anchor_age_inventory(card):
    """Static mask description only; age is t minus the most recent true D."""
    rows=[]
    for role, policy in card['policies'].items():
        actions=['D']*36 if policy is None else policy['actions']
        anchor=None;reuse=[]
        for step, action in enumerate(actions,1):
            if action=='D':anchor=step
            else:
                if anchor is None:raise ValueError('Reuse before a true D anchor')
                reuse.append(dict(step=step,action=action,source_step=anchor,age=step-anchor))
        rows.append(dict(role=role,max_reuse_age=max([r['age'] for r in reuse],default=0),
                         reuse_steps=reuse,age_effect_identified=False))
    return rows


def summarize(card, science, requests):
    members=card['CAL_FIT_members']; roles=list(card['policies']); timing=science['timing']
    slots=[s for s in card['matrix'] if s['section'] in ('CALIBRATION','VALIDATION')]
    clocks={(s['role'],s['member'],s['repeat']):requests[s['id']]['result']['full_request_seconds'] for s in slots}
    quality={}
    for role, rows in science['quality'].items():
        keys={(r['member'],r['repeat']) for r in rows}
        if keys != {(m,k) for m in members for k in (1,2)} or len(rows)!=8:
            raise ValueError('Full same-prompt two-round quality required')
        for r in rows: quality[role,r['member'],r['repeat']]=r['LPIPS']
    role_table=[]; aggregates={}; by_prediction={r['role']:r for r in timing['per_role']}
    for role in roles:
        tm=[mean([clocks[role,m,k] for k in (1,2)]) for m in members]
        q=None if role=='NATIVE' else [mean([quality[role,m,k] for k in (1,2)]) for m in members]
        aggregates[role]=(tm,q)
        rounds=[mean([clocks[role,m,k] for m in members]) for k in (1,2)]
        row=dict(role=role, counts=None if card['policies'][role] is None else card['policies'][role]['counts'],
                 full_request_mean_seconds=mean(tm), formal_round_means_seconds=rounds,
                 prompt_mean_seconds=dict(zip(members,tm)), LPIPS_mean=None if q is None else mean(q),
                 prompt_mean_LPIPS=None if q is None else dict(zip(members,q)),
                 round2_minus_round1=paired_summary([clocks[role,m,2]-clocks[role,m,1] for m in members],members),
                 validation_measured_feasible=rounds[1]<=timing['budget_seconds'],
                 validation_headroom_seconds=timing['budget_seconds']-rounds[1],
                 round_feasibility_disagrees=(rounds[0]<=timing['budget_seconds'])!=(rounds[1]<=timing['budget_seconds']))
        if role in by_prediction:
            p=by_prediction[role];row.update(predicted_mean_seconds=p['predicted_mean_seconds'],
                planning_feasible_with_fixed_margin=p['predicted_feasible'],
                planning_headroom_seconds=timing['budget_seconds']-p['predicted_mean_seconds']-timing['margin_seconds'])
        role_table.append(row)
    comparisons=[]
    for left,right,purpose in COMPARISONS:
        lt,lq=aggregates[left];rt,rq=aggregates[right]
        dt=paired_summary([a-b for a,b in zip(lt,rt)],members)
        dq=paired_summary([a-b for a,b in zip(lq,rq)],members)
        dominates=lambda t,q:t<=0 and q<=0 and (t<0 or q<0)
        relation=('LEFT_DESCRIPTIVE_PARETO' if dominates(dt['mean'],dq['mean']) else
                  'RIGHT_DESCRIPTIVE_PARETO' if dominates(-dt['mean'],-dq['mean']) else 'TRADEOFF_OR_TIE')
        comparisons.append(dict(left=left,right=right,purpose=purpose,time_delta_seconds=dt,LPIPS_delta=dq,
            relative_LPIPS_mean_change=None if mean(rq)==0 else mean(lq)/mean(rq)-1,
            same_D_count=card['policies'][left]['counts']['D']==card['policies'][right]['counts']['D'],
            observed_relation=relation, equal_measured_time_claim=False,
            both_validation_budget_feasible=by_prediction[left]['measured_feasible'] and by_prediction[right]['measured_feasible']))
    # Components overlap with core: sum only the four disjoint request boundaries.
    component_rows=[];diagnostics=[]
    for s in card['matrix']:
        r=requests[s['id']]['result']
        if s['section']=='WARM':continue
        present=all(k in r for k in COMPONENTS)
        row=dict(id=s['id'],role=s['role'],member=s['member'],section=s['section'],repeat=s['repeat'],
                 complete_components_available=present)
        if present:
            parts={k:r[k] for k in COMPONENTS}
            if not all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in parts.values()):
                raise ValueError('Invalid component timing')
            closure=math.fsum(parts.values())-r['full_request_seconds']
            if abs(closure)>1e-6:raise ValueError('Full request components do not close')
            row.update(parts,closure_seconds=closure,core_seconds=r['core_seconds'],
                       outside_core_seconds=r['full_request_seconds']-r['core_seconds'])
        if s['section']=='DIAGNOSTIC':
            ref=next(x for x in slots if x['section']=='CALIBRATION' and x['role']==s['role'] and x['member']==s['member'])
            row.update(diagnostic_minus_clean_seconds=r['full_request_seconds']-requests[ref['id']]['result']['full_request_seconds'],
                       speed_evidence=False,causal_overhead_estimate=False)
            diagnostics.append(row)
        else:component_rows.append(row)
    component_summary=[]
    if all(r['complete_components_available'] for r in component_rows):
        for role in roles:
            rr=[r for r in component_rows if r['role']==role]
            component_summary.append(dict(role=role,**{k:mean([r[k] for r in rr]) for k in (*COMPONENTS,'core_seconds','outside_core_seconds')}))
    entry_delta=paired_summary([a-b for a,b in zip(aggregates['PG_ALL_D'][0],aggregates['NATIVE'][0])],members)
    # Native-subtracted changes reduce shared round drift; still not randomized causal effects.
    order=[]
    for role in roles[1:]:
        raw=[(clocks[role,m,2]-clocks[role,m,1])-(clocks['NATIVE',m,2]-clocks['NATIVE',m,1]) for m in members]
        order.append(dict(role=role,native_adjusted_round_shift=paired_summary(raw,members)))
    boundary=[r for r in role_table if r['role'] in ('S24_C','S24_A_PHASE','S25_C','S25_A_PHASE')]
    return dict(status='COMPLETE104_POST_ACCEPTANCE_DESCRIPTIVE_ANALYSIS',
        baseline_role_table=role_table,registered_comparisons=comparisons,budget_boundaries=boundary,
        anchor_age_inventory=anchor_age_inventory(card),
        timing=dict(frozen_result=timing,PG_allD_minus_direct_Native=entry_delta,
            order_drift_descriptive=order,formal_component_rows=component_rows,
            formal_component_means=component_summary,diagnostic_rows=diagnostics,
            decomposition_note='Components close the complete request; core overlaps guarded pipeline. Diagnostic-clean differences confound instrumentation and order.'),
        P1_continuation=route(timing,boundary),
        interpretation=dict(CAL_only=True, independent_prompts=4,independent_seeds=1,
            frames_or_repeats_are_not_independent_prompts=True,LPIPS_is_Native_fidelity_not_independent_quality=True,
            age_causal_claim=False,baseline_cherry_pick=False,heldout_claim=False,
            no_universal_D_cap_from_tested_layouts=True,
            no_age_three_effectiveness_threshold=True,
            same_D_is_ablation_not_only_contribution_criterion=True,
            planning_margin_applies_to_prediction_not_measured_budget=True,
            more_repeats_do_not_remove_systematic_bias=True,
            future_margin_change_requires_independent_validation=True,
            old_GRAPH_vs_SIMPLE_signal_is_not_strong_baseline_advantage=True,
            fewer_step_Native_requires_time_matching_and_independent_quality=True))



def exposure_inventory(card, old_analysis):
    old={r['fingerprint'] for r in old_analysis['candidates']}
    registered={v['fingerprint'] for role,v in card['policies'].items() if v is not None and role!='PG_ALL_D'}
    return dict(old_P1_scored_unique_policies=len(old), registered104_nontrivial_unique_policies=len(registered),
                overlap=len(old & registered), cumulative_unique_if104_quality_used=len(old | registered),
                fingerprints=sorted(old | registered), repeated_rounds_are_not_new_policies=True,
                prospective_search_Q_limit=8, cumulative_development_Q_is_not_reset=True,
                equal_preexposure_for_comparators_required=True)


def analyze_accepted(capture, accepted, *, capture_sha256, expected_launch):
    if not accepted.get('full_protocol_accepted') or accepted.get('capture_sha256')!=capture_sha256:
        raise ValueError('Bound full terminal acceptance required; no prefixes')
    if capture['launch']!=expected_launch:
        raise ValueError('Expected unique original launch differs')
    replay=accept(capture)
    original={k:v for k,v in accepted.items() if k not in ('capture_ref','capture_sha256')}
    if replay!=original:raise ValueError('Independent full104 acceptance does not reproduce')
    result=summarize(record(capture,'card'),replay['scientific'],capture['requests'])
    result.update(launch_id=replay['launch_id'],execution_source_revision=replay['source_revision'],
                  original_capture_sha256=capture_sha256,actual_GPUh=replay['actual_GPUh'],
                  full_protocol_accepted=True,GPU_submissions=0,ledger_written=False)
    return result
