#!/usr/bin/env python3
"""Complete the registered remaining E0 analysis using saved scalar receipts only."""
import collections
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

ROOT = Path(__file__).resolve().parents[1]
INPUTS = dict(
    N07_capture='reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz',
    N07_analysis='reports/wc_paper_N07_R2_complete_results_analysis_20261017.json',
    phase='reports/wc_w3_phase_vs_state_CPU_primary_and_sensitivity_r1_20261016.json',
    grouped='reports/wc_w3_grouped_T0_T1_T2_primary_and_raw_sensitivity_accepted_r2_20261016.json',
    drop1='manifests/wc_endpoint_budget_D_replacement_design_r1_20261017.json')
OUT = 'reports/wc_E0_remaining_seed_layout_phase_CPU_complete_20261017.json'


def read(path):
    raw = (ROOT/path).read_bytes()
    return json.loads(gzip.decompress(raw) if path.endswith('.gz') else raw)


def mean(values):
    return statistics.mean(values) if values else None


def score(row):
    v = row.get('LPIPS')
    if row.get('endpoint_audit') != 'PASS' or not v:
        return None
    frames = v['frame_distances']
    assert len(frames) == v['frames'] == 93
    result = mean(frames)
    assert math.isclose(result, v['mean_LPIPS'], abs_tol=1e-12)
    return result


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


def layout(row):
    actions = row.get('actions') or []
    if len(actions) != 36:
        return dict(available=False, status=row['status'], reason='NO_COMPLETE36_ORIGINAL_ACTION_TRACE')
    last = 0
    ages = []
    runs = []
    run = 0
    for step, action in enumerate(actions, 1):
        if action == 'DD':
            last = step
            if run: runs.append(run)
            run = 0
        else:
            run += 1
            ages.append(step-last)
    if run: runs.append(run)
    history = row.get('A_history')
    ah = history if isinstance(history, list) else []
    return dict(available=True, physical_actions=actions,
        D_positions=[i+1 for i,a in enumerate(actions) if a=='DD'],
        physical_counts=dict(collections.Counter(actions)),
        nonD_source_ages_derived_from_actual_D=ages,
        maximum_continuous_reuse=max(runs, default=0),
        maximum_source_age=max(ages, default=0),
        A_history_available=isinstance(history,list),
        A_steps=[h['step'] for h in ah if h['action']=='CC' and h.get('shared_alpha',0)>0],
        A_phase_counts=dict(collections.Counter('EARLY' if h['step']<25 else 'LATE'
            for h in ah if h['action']=='CC' and h.get('shared_alpha',0)>0)),
        explicit_branch_statuses=dict(collections.Counter(str(s) for h in ah for s in h.get('branch_status',[]))),
        missing_support_or_fallback_reason='RA physical trace has no full source/fallback decisions; not inferred as zero')


def evaluate_phase(phase, grouped):
    results = []
    for cohort in phase['cohorts']:
        source = next(c for c in grouped['cohorts'] if c['cohort']==cohort['cohort'])
        metadata = {(r['group'],r['id']):r for r in source['point_predictions'] if r['model']=='T0_CAD'}
        rows = cohort['point_predictions']
        by_model = collections.defaultdict(dict)
        for r in rows:
            by_model[r['model']][(r['group'],r['id'])] = r
        baseline = by_model['T0_CAD']
        assert len(baseline)==cohort['points']
        for model, points in by_model.items():
            assert set(points)==set(baseline)
            for key,row in points.items():
                assert row['true_scores']==baseline[key]['true_scores']
                assert set(row['true_scores'])=={'C','A','D'}
        controlled = {}
        learned = ['T1','T2','T_TIME']
        for name in learned:
            points = copy.deepcopy(by_model[name])
            for key,row in points.items():
                raw = row['raw_prediction']
                invalid = (any(not math.isfinite(t) for t in raw) or raw[0]<0 or sum(raw)<0)
                row['common_fallback'] = invalid
                if invalid: row['action']=baseline[key]['action']
                true = row['true_scores']
                row['local_regret'] = true[row['action']]-min(true.values())
                row['model']=name+'_COMMON_FALLBACK'
            controlled[name+'_COMMON_FALLBACK']=points
        all_models = dict(by_model, **controlled)
        aggregate = []
        for name,points in all_models.items():
            for exclude23 in (False,True):
                selected = [r for r in points.values() if not exclude23 or r['step']!=23]
                per_prompt = []
                for group in cohort['groups']:
                    rr=[r for r in selected if r['group']==group]
                    per_prompt.append(dict(group=group,points=len(rr),mean_regret=mean([r['local_regret'] for r in rr]),
                        action_counts=dict(collections.Counter(r['action'] for r in rr)),
                        fallback_rate=mean([float(r.get('common_fallback',r.get('fallback',False))) for r in rr])))
                aggregate.append(dict(model=name,exclude_step23=exclude23,points=len(selected),
                    prompt_equal_mean_regret=mean([r['mean_regret'] for r in per_prompt]),
                    worst_state_regret=max(r['local_regret'] for r in selected),per_prompt=per_prompt))
        for name in ['T1','T2']:
            expected=by_model[name+'_NEG_FALLBACK']
            assert all(controlled[name+'_COMMON_FALLBACK'][k]['action']==expected[k]['action'] for k in expected)
        strata=collections.defaultdict(list)
        margins=[]
        for key,row in baseline.items():
            meta=metadata[key]
            strata[(row['step'],meta['source'],meta['source_age'])].append(row)
        spaces=[]
        for (step,source_kind,age),rr in sorted(strata.items()):
            means={a:mean([r['true_scores'][a] for r in rr]) for a in ['C','A','D']}
            shared=min(means,key=means.get)
            oracle=mean([min(r['true_scores'].values()) for r in rr])
            gap=means[shared]-oracle
            assert gap>=-1e-12
            spaces.append(dict(step=step,source=source_kind,source_age=age,points=len(rr),
                best_shared_action=shared,shared_mean_objective=means[shared],
                per_state_oracle_mean_objective=oracle,descriptive_state_information_gap=max(0,gap),
                oracle_action_counts=dict(collections.Counter(r['oracle'] for r in rr)),
                finite_sample_oracle_is_optimistic=True))
        for name,points in all_models.items():
            for key,row in points.items():
                values=row.get('predicted_scores')
                finite=isinstance(values,dict) and bool(values) and all(math.isfinite(v) for v in values.values())
                ordered=sorted(values.values()) if finite else []
                margins.append(dict(id=row['id'],group=row['group'],step=row['step'],model=name,
                    predicted_top_two_gap=(ordered[1]-ordered[0] if finite else None),
                    applied_action=row['action'],original_predicted_best=(min(values,key=values.get) if finite else None),
                    common_fallback=row.get('common_fallback',row.get('fallback',False)),
                    source=metadata[key]['source'],source_age=metadata[key]['source_age']))
        results.append(dict(cohort=cohort['cohort'],groups=cohort['groups'],full_points=cohort['points'],
            aggregate=aggregate,within_step_source_age_oracle_space=spaces,
            decision_margins=margins,controlled_point_predictions={k:list(v.values()) for k,v in controlled.items()},
            targets_are_original_J_scores_g_squared_not_reapplied=True,
            no_teacher_future_or_old_score_as_new_model_input=True,
            refit_or_new_model=False))
    return results


def main():
    started=time.monotonic()
    bindings={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS.values()}
    data={k:read(p) for k,p in INPUTS.items()}
    capture=data['N07_capture']
    rows=[r for r in capture['final']['rows'] if r['section']=='TIMED']
    cases={r['id']:r for r in capture['runner']['cases']}
    lookup={(r['case_id'],r['method']):r for r in rows}
    seeds_by_prompt=collections.defaultdict(list)
    for case_id,case in cases.items():
        rr=[lookup.get((case_id,m)) for m in ['FRONT_DENSE_C','FRONT_DENSE_A']]
        if all(rr) and all(score(r) is not None for r in rr):
            lc,la=[score(r) for r in rr]
            seeds_by_prompt[case['prompt_id']].append(dict(case_id=case_id,seed=case['seed'],C=lc,A=la,gain_C_minus_A=lc-la))
    prompt_readout=[]
    for prompt, rr in sorted(seeds_by_prompt.items()):
        if sorted(r['seed'] for r in rr)!=[17,43]:continue
        gains=[r['gain_C_minus_A'] for r in rr]
        prompt_readout.append(dict(prompt=prompt,seeds=rr,prompt_equal_gain=mean(gains),
            two_seed_direction_consistent=sign(gains[0])==sign(gains[1]),
            both_seeds_improve=all(t>0 for t in gains),both_seeds_worsen=all(t<0 for t in gains)))
    gains=[r['prompt_equal_gain'] for r in prompt_readout]
    gain_mean=mean(gains)
    influence=[dict(removed_prompt=q['prompt'],remaining_prompt_mean_gain=mean([r['prompt_equal_gain'] for r in prompt_readout if r is not q]),
        removed_gain=q['prompt_equal_gain'],not_a_sample_exclusion_rule=True) for q in prompt_readout]
    divergences=[]
    for case_id,case in sorted(cases.items()):
        ra,corrected=[lookup.get((case_id,m)) for m in ['RA_DEFAULT','A_NO_P']]
        if not ra or not corrected:continue
        r,a=layout(ra),layout(corrected)
        both=r['available'] and a['available']
        disagreements=[i+1 for i,(x,y) in enumerate(zip(r.get('physical_actions',[]),a.get('physical_actions',[]))) if x!=y]
        divergences.append(dict(case_id=case_id,prompt=case['prompt_id'],seed=case['seed'],
            RA_status=ra['status'],A_status=corrected['status'],RA=r,A=a,
            comparable_complete36=both,first_physical_action_divergence=(disagreements[0] if disagreements else None),
            physical_disagreement_positions=disagreements,
            physical_layouts_identical=(not disagreements if both else None),
            first_explicit_A_readout=(a.get('A_steps') or [None])[0],
            shared_quality_available=score(ra) is not None and score(corrected) is not None))
    plans=data['drop1']['plans'];static=[]
    for name,plan in plans.items():
        last=0;ages=[]
        for n,action in enumerate(plan,1):
            if action=='D':last=n
            else:ages.append(n-last)
        assert len(plan)==36 and max(ages)<=6 and all(plan[n-1]=='D' for n in [1,2,3,4,5,6,7,36])
        static.append(dict(name=name,counts={a:plan.count(a) for a in ['C','A','D']},maximum_static_age=max(ages)))
    phase=evaluate_phase(data['phase'],data['grouped'])
    result=dict(status='E0_REMAINING_SAVED_RECEIPT_CPU_ANALYSIS_COMPLETE_NOT_VIDEO_EVIDENCE',input_sha256=bindings,
        common_cohort_tables_reused=INPUTS['N07_analysis'],readout_seed_stability=dict(prompts=prompt_readout,
            complete_double_seed_prompts=len(prompt_readout),prompt_equal_mean_gain=gain_mean,
            both_seed_improve_prompts=sum(q['both_seeds_improve'] for q in prompt_readout),
            both_seed_worsen_prompts=sum(q['both_seeds_worsen'] for q in prompt_readout),
            mixed_seed_prompts=sum(not q['two_seed_direction_consistent'] for q in prompt_readout),
            leave_one_prompt_influence=influence),
        RA_A_layout_divergences=divergences,phase_state_remaining=phase,drop1_static_plan_checks=static,
        missing_fields=['Full RA source/support/fallback logs are not present in the saved generation rows; physical ages are derived from DD only.',
            'No hidden/probe directions reconstructed from videos or scalar data.',
            'The new18-path production CPU is separate and not accepted by this analysis.'],
        original_results_or_thresholds_overwritten=False,new_teacher_computations=0,
        model_weights_loaded=0,GPU_submissions=0,SSH_queries=0,ledger_written=False,
        CPU_wall_seconds=time.monotonic()-started)
    assert len(prompt_readout)==6
    assert mean([q['prompt_equal_gain'] for q in prompt_readout])==gain_mean
    for p,digest in bindings.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest
    out=ROOT/OUT
    if out.exists():raise ValueError('Preserve the original analysis')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'],output=OUT,readout_prompt_count=len(prompt_readout),
        seed_consistency={k:v for k,v in result['readout_seed_stability'].items() if k not in ['prompts','leave_one_prompt_influence']},
        complete_layout_pairs=sum(q['comparable_complete36'] for q in divergences),
        phase_cohorts=[dict(cohort=c['cohort'],without23=[{k:q[k] for k in ['model','points','prompt_equal_mean_regret','worst_state_regret']} for q in c['aggregate'] if q['exclude_step23']]) for c in phase],
        CPU_wall_seconds=result['CPU_wall_seconds'],GPU_submissions=0),ensure_ascii=False))

if __name__=='__main__':main()

