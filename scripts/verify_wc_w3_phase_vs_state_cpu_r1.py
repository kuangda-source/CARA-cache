#!/usr/bin/env python3
"""Scalar reconstruction of train-only phase controls, without evaluator imports."""
import argparse, collections, gzip, hashlib, json, math, runpy, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ORDER = {'C': 0, 'A': 1, 'D': 2}
TIME_NAMES = ['step_fraction', 'log1p_sigma', 'sigma_available']
def near(a, b): return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-11)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def choose(scores): return min(scores, key=lambda a: (scores[a], ORDER[a]))

def verify(value):
    prior_path = ROOT/value['prior_ref']; assert sha(prior_path) == value['prior_sha256']
    previous = json.loads(prior_path.read_text())
    old_check = runpy.run_path(str(ROOT/'scripts/verify_wc_w3_grouped_action_receipt_r1.py'))['verify'](previous)
    assert old_check['new_GPU_submissions'] == 0
    assert all(sha(ROOT/p) == s for p, s in value['code_sha256'].items())
    assert value['GPU_submissions'] == value['SSH_queries'] == 0 and not value['ledger_written']
    original = json.loads(gzip.decompress((ROOT/previous['original_capture_ref']).read_bytes()))['capture']
    runner = next(v['data'] for k, v in original['receipts'].items() if k.endswith('/runner.json'))
    features = {r['id']+':'+str(p['step']): r['feature_rows'][p['step']-1]['features']['T1']
                for r in runner['runs'] for p in r.get('diagnostic_points', [])}
    output = []
    for cohort, old_cohort in zip(value['cohorts'], previous['cohorts']):
        assert cohort['cohort'] == old_cohort['cohort']
        assert cohort['groups'] == old_cohort['groups']
        groups = cohort['groups']; old = {(r['model'], r['id']): r for r in old_cohort['point_predictions']}
        base = {r['id']: r for r in old_cohort['point_predictions'] if r['model'] == 'T0_CAD'}
        folds = {f['held_group']: f for f in cohort['folds']}
        assert set(folds) == set(groups) and len(base) == cohort['points'] == len(groups)*8
        for held, f in folds.items():
            train = [r for r in base.values() if r['group'] != held]
            test = [r for r in base.values() if r['group'] == held]
            assert set(f['training_ids']) == {r['id'] for r in train}
            assert set(f['held_ids']) == {r['id'] for r in test}
            assert f['training_groups'] == sorted(set(groups)-{held})
            assert not f['held_labels_used_for_fit'] and f['ridge'] == 1 and f['feature_names'] == TIME_NAMES
            def time_x(row):
                feat = features[row['id']]
                return [feat['values'][feat['names'].index(n)] for n in TIME_NAMES]
            xs = [time_x(r) for r in train]
            mean = [statistics.fmean(x[i] for x in xs) for i in range(3)]
            std = [math.sqrt(statistics.fmean((x[i]-mean[i])**2 for x in xs)) for i in range(3)]
            std = [1. if s < 1e-12 else s for s in std]
            assert all(near(a, b) for a, b in zip(mean, f['mean']))
            assert all(near(a, b) for a, b in zip(std, f['std']))
            z = lambda x: [1.]+[(a-b)/s for a, b, s in zip(x, f['mean'], f['std'])]
            for i in range(4):
                for j in range(2):
                    residual = math.fsum(z(x)[i]*(math.fsum(a*w[j] for a, w in zip(z(x), f['weights']))-r['weighted_targets'][j])
                                         for x, r in zip(xs, train))
                    residual += f['weights'][i][j] if i else 0.
                    assert abs(residual) < 1e-8, 'Time ridge normal equation must use training labels only'
            for r in test:
                expected = [math.fsum(a*w[j] for a, w in zip(z(time_x(r)), f['weights'])) for j in (0, 1)]
                assert all(near(a, b) for a, b in zip(expected, f['time_predictions'][r['id']]))
            for step in cohort['sampled_steps']:
                rr = [r for r in train if r['step'] == step]; table = f['step_table'][str(step)]
                scores = {a: statistics.fmean(r['true_scores'][a] for r in rr) for a in ORDER}
                assert set(table['training_ids']) == {r['id'] for r in rr}
                assert all(near(scores[a], table['scores'][a]) for a in ORDER)
                assert table['action'] == choose(scores)
        rows = cohort['point_predictions']; assert len(rows) == 8*len(base)
        assert len({(r['model'], r['id']) for r in rows}) == len(rows)
        for r in rows:
            b = base[r['id']]; f = folds[r['group']]; model = r['model']
            assert all(near(r['true_scores'][a], b['true_scores'][a]) for a in ORDER)
            assert r['oracle'] == choose(b['true_scores'])
            if model in ('T0_CAD', 'T1', 'T2'):
                p = old[model, r['id']]; action = p['action']; scores = p['predicted_scores']
                assert r['raw_prediction'] == p['raw_prediction']
            elif model == 'T_TIME':
                p = f['time_predictions'][r['id']]; assert r['raw_prediction'] == p
                risk = {'C': max(0., sum(p)), 'A': max(0., p[0]), 'D': 0.}
                # Recover quoted costs from the independently verified old score table.
                oldp = old['T0_CAD', r['id']]['raw_prediction']
                oldrisk = {'C': max(0., sum(oldp)), 'A': max(0., oldp[0]), 'D': 0.}
                costs = {a: b['predicted_scores'][a]-cohort['lambda_frozen']*oldrisk[a] for a in ORDER}
                scores = {a: costs[a]+cohort['lambda_frozen']*risk[a] for a in ORDER}; action = choose(scores)
            elif model == 'T_STEP_TABLE':
                p = f['step_table'][str(r['step'])]; scores, action = p['scores'], p['action']
            elif model == 'STEP23_A_ONLY_POSTHOC':
                action = 'A' if r['step'] == 23 else b['action']; scores = None
                assert r['raw_prediction'] is None
            else:
                assert model in ('T1_NEG_FALLBACK', 'T2_NEG_FALLBACK')
                p = old[model[:2], r['id']]; raw = p['raw_prediction']
                trigger = raw[0] < 0 or sum(raw) < 0
                assert r['fallback'] == trigger and r['raw_prediction'] == raw
                p = b if trigger else p; scores, action = p['predicted_scores'], p['action']
            assert r['action'] == action
            assert (scores is None) == (r['predicted_scores'] is None)
            if scores is not None: assert all(near(scores[a], r['predicted_scores'][a]) for a in ORDER)
            assert near(r['local_regret'], b['true_scores'][action]-b['true_scores'][r['oracle']])
        summaries = {s['model']: s for s in cohort['models']}
        for model, summary in summaries.items():
            rr = [r for r in rows if r['model'] == model]
            means = [statistics.fmean(r['local_regret'] for r in rr if r['group'] == g) for g in groups]
            mean = statistics.fmean(means)
            assert near(summary['prompt_equal_mean_regret'], mean)
            assert near(summary['prompt_equal_oracle_error_rate'], statistics.fmean(r['action'] != r['oracle'] for r in rr))
            assert summary['action_counts'] == dict(collections.Counter(r['action'] for r in rr))
            assert near(summary['worst_regret'], max(r['local_regret'] for r in rr))
            assert near(summary['regret_change_percent_vs_T0_CAD'], 100*(mean/summaries['T0_CAD']['prompt_equal_mean_regret']-1))
            assert all(near(m, p['mean_regret']) for m, p in zip(means, summary['per_prompt']))
        b = summaries['T0_CAD']['prompt_equal_mean_regret']; t = summaries['T1']['prompt_equal_mean_regret']
        output.append(dict(cohort=cohort['cohort'], groups=len(groups), points=len(base),
            train_only_ridge_normal_equations_and_step_choices_verified=True,
            all_point_actions_costs_regrets_and_aggregate_metrics_verified=True,
            fraction_of_T1_local_gain_from_time_only=(b-summaries['T_TIME']['prompt_equal_mean_regret'])/(b-t),
            fraction_of_T1_local_gain_from_posthoc_step23=(b-summaries['STEP23_A_ONLY_POSTHOC']['prompt_equal_mean_regret'])/(b-t)))
    return dict(status='W3_PHASE_CONTROLS_INDEPENDENT_SCALAR_VERIFICATION_PASS', cohorts=output,
                prior_scalar_verification_status=old_check['status'], new_GPU_submissions=0,
                new_policy_video_or_speed_claim=False)

def main():
    p = argparse.ArgumentParser(); p.add_argument('--input', type=Path, required=True); p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    assert not a.output.exists(); result = verify(json.loads(a.input.read_text()))
    result.update(input_ref=str(a.input), input_sha256=sha(a.input))
    a.output.write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result))

if __name__ == '__main__': main()
