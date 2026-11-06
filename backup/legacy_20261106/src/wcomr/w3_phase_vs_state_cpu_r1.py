"""Offline phase controls on the accepted W3 states; never a rollout policy.

The step-23 override is explicitly post hoc. The per-step table and time-only
regression use whole-prompt holdouts. No old fit or teacher tensor is changed.
"""
from collections import Counter
from dataclasses import replace
import math
import numpy as np
from .w3_causal_trend_r1 import RidgeRisk, coherent_scores
from .w3_grouped_action_eval_r1 import choose, close, COHORTS

TIME_NAMES = ('step_fraction', 'log1p_sigma', 'sigma_available')
MODELS = ('T0_CAD', 'T1', 'T_TIME', 'T_STEP_TABLE',
          'STEP23_A_ONLY_POSTHOC', 'T2', 'T1_NEG_FALLBACK', 'T2_NEG_FALLBACK')


def true_scores(sample):
    target = sample['label'].target(sample['feature']['T1'])
    risks = {'C': float(target.sum()), 'A': float(target[0]), 'D': 0.}
    return {a: sample['costs'][a]+sample['lam']*risks[a] for a in risks}


def time_feature(sample):
    original = sample['feature']['T1']
    values = tuple(original.values[original.names.index(n)] for n in TIME_NAMES)
    return replace(original, names=TIME_NAMES, values=values)


def fit_phase_fold(rows, held):
    train = [r for r in rows if r['group'] != held]
    test = [r for r in rows if r['group'] == held]
    assert train and test and len(test) == 8
    forbidden = {r['feature']['T1'].observation.prompt for r in test}
    reg = RidgeRisk(model='T1', ridge=1.).fit(
        [(time_feature(r), r['label']) for r in train], forbidden_prompts=forbidden)
    assert set(reg.training_prompts).isdisjoint(forbidden)
    by_step = {}
    for step in sorted({r['step'] for r in train}):
        matched = [r for r in train if r['step'] == step]
        assert len(matched) == len({r['group'] for r in train})
        scores = {a: math.fsum(true_scores(r)[a] for r in matched)/len(matched)
                  for a in ('C', 'A', 'D')}
        by_step[str(step)] = dict(scores=scores, action=choose(scores),
                                 training_ids=[r['id'] for r in matched])
    predictions = {r['id']: reg.predict(time_feature(r)) for r in test}
    fold = dict(held_group=held, training_groups=sorted({r['group'] for r in train}),
                training_ids=[r['id'] for r in train], held_ids=[r['id'] for r in test],
                training_prompts=list(reg.training_prompts), feature_names=list(reg.names),
                mean=reg.mean.tolist(), std=reg.std.tolist(), weights=reg.weights.tolist(),
                ridge=1., time_predictions={k: v.tolist() for k, v in predictions.items()},
                step_table=by_step, held_labels_used_for_fit=False)
    return fold


def summarize(details, groups):
    summaries = []
    for model in MODELS:
        rows = [r for r in details if r['model'] == model]
        per = []
        for group in groups:
            rr = [r for r in rows if r['group'] == group]
            assert len(rr) == 8
            avg = lambda k: math.fsum(r[k] for r in rr)/len(rr) if all(r[k] is not None for r in rr) else None
            per.append(dict(group=group, mean_regret=avg('local_regret'),
                oracle_error_rate=avg('oracle_mistake'), CA_boundary_error_rate=avg('CA_boundary_misrank'),
                AD_boundary_error_rate=avg('AD_boundary_misrank'),
                raw_target_MSE=avg('raw_target_MSE'), fallback_rate=avg('fallback'),
                worst_regret=max(r['local_regret'] for r in rr),
                action_counts=dict(Counter(r['action'] for r in rr))))
        avg = lambda k: math.fsum(r[k] for r in per)/len(per) if all(r[k] is not None for r in per) else None
        base = {r['id']: r for r in details if r['model'] == 'T0_CAD'}
        t1 = {r['id']: r for r in details if r['model'] == 'T1'}
        summaries.append(dict(model=model, per_prompt=per,
            prompt_equal_mean_regret=avg('mean_regret'), prompt_equal_oracle_error_rate=avg('oracle_error_rate'),
            prompt_equal_CA_boundary_error_rate=avg('CA_boundary_error_rate'),
            prompt_equal_AD_boundary_error_rate=avg('AD_boundary_error_rate'),
            prompt_equal_raw_target_MSE=avg('raw_target_MSE'), prompt_equal_fallback_rate=avg('fallback_rate'),
            action_counts=dict(Counter(r['action'] for r in rows)),
            actions_changed_vs_T0_CAD=sum(r['action'] != base[r['id']]['action'] for r in rows),
            actions_disagree_with_T1=sum(r['action'] != t1[r['id']]['action'] for r in rows),
            worst_regret=max(r['local_regret'] for r in rows)))
    base = next(s for s in summaries if s['model'] == 'T0_CAD')
    t1 = next(s for s in summaries if s['model'] == 'T1')
    for s in summaries:
        mean = s['prompt_equal_mean_regret']; b = base['prompt_equal_mean_regret']
        s['regret_change_percent_vs_T0_CAD'] = 100*(mean/b-1)
        s['regret_difference_vs_T1'] = mean-t1['prompt_equal_mean_regret']
        s['prompt_regret_wins_vs_T0_CAD'] = sum(x['mean_regret'] < y['mean_regret'] for x, y in zip(s['per_prompt'], base['per_prompt']))
        s['prompt_regret_wins_vs_T1'] = sum(x['mean_regret'] < y['mean_regret'] for x, y in zip(s['per_prompt'], t1['per_prompt']))
    return summaries


def evaluate_phase_controls(data, previous):
    name = previous['cohort']; assert name in COHORTS
    rows = [r for r in data if r['primary']] if name == COHORTS[0] else list(data)
    groups = sorted({r['group'] for r in rows})
    assert groups == previous['groups'] and len(rows) == previous['points'] == 8*len(groups)
    old = {(r['model'], r['id']): r for r in previous['point_predictions']}
    folds = [fit_phase_fold(rows, held) for held in groups]
    fold_index = {f['held_group']: f for f in folds}
    details = []
    for s in rows:
        truth = true_scores(s); oracle = choose(truth)
        original = {m: old[m, s['id']] for m in ('T0_CAD', 'T1', 'T2')}
        assert s['original_H1_action'] == original['T0_CAD']['action']
        for r in original.values():
            assert all(close(r['true_scores'][a], truth[a]) for a in truth)
        f = fold_index[s['group']]
        for model in MODELS:
            raw = None; scores = None; fallback = False
            if model in original:
                p = original[model]; raw = p['raw_prediction']; scores = p['predicted_scores']; action = p['action']
            elif model == 'T_TIME':
                raw = f['time_predictions'][s['id']]
                decision = coherent_scores(raw, s['feature']['T1'].observation, costs=s['costs'], lam=s['lam'])
                scores, action = decision['scores'], decision['action']
            elif model == 'T_STEP_TABLE':
                table = f['step_table'][str(s['step'])]; scores, action = table['scores'], table['action']
            elif model == 'STEP23_A_ONLY_POSTHOC':
                action = 'A' if s['step'] == 23 else original['T0_CAD']['action']
            else:
                source = original[model[:2]]; raw = source['raw_prediction']
                fallback = raw[0] < 0 or raw[0]+raw[1] < 0
                chosen = original['T0_CAD'] if fallback else source
                scores, action = chosen['predicted_scores'], chosen['action']
            target = s['label'].target(s['feature']['T1']).tolist()
            details.append(dict(id=s['id'], group=s['group'], step=s['step'], model=model,
                action=action, oracle=oracle, true_scores=truth, predicted_scores=scores,
                raw_prediction=raw, weighted_targets=target,
                local_regret=max(0., truth[action]-truth[oracle]), oracle_mistake=action != oracle,
                CA_boundary_misrank=None if scores is None else (scores['C'] <= scores['A']) != (truth['C'] <= truth['A']),
                AD_boundary_misrank=None if scores is None else (scores['A'] <= scores['D']) != (truth['A'] <= truth['D']),
                raw_target_MSE=None if raw is None else math.fsum((a-b)**2 for a, b in zip(raw, target))/2,
                fallback=fallback, RGB_complete=s['RGB_complete'], teacher_used_as_online_feature=False))
    summaries = summarize(details, groups)
    for model in ('T0_CAD', 'T1', 'T2'):
        a = next(x for x in summaries if x['model'] == model)
        b = next(x for x in previous['models'] if x['model'] == model)
        assert close(a['prompt_equal_mean_regret'], b['prompt_equal_mean_regret'])
        assert a['action_counts'] == b['action_counts']
    attribution = []
    base = {r['id']: r for r in details if r['model'] == 'T0_CAD'}
    for model in MODELS:
        by_step = []
        for step in sorted({r['step'] for r in rows}):
            ss = [r for r in details if r['model'] == model and r['step'] == step]
            by_step.append(dict(step=step, sum_regret_reduction=math.fsum(base[r['id']]['local_regret']-r['local_regret'] for r in ss),
                action_counts=dict(Counter(r['action'] for r in ss)),
                mean_regret=math.fsum(r['local_regret'] for r in ss)/len(ss)))
        attribution.append(dict(model=model, steps=by_step))
    return dict(cohort=name, groups=groups, points=len(rows), models=summaries, folds=folds,
        point_predictions=details, step_attribution=attribution, lambda_frozen=rows[0]['lam'],
        sampled_steps=sorted({r['step'] for r in rows}),
        step23_rule_status='POSTHOC_FIXED_CANDIDATE_EVALUATED_ON_EXPOSED_DATA',
        independent_final_test=False, policy_rollout_or_latency_claim=False)
