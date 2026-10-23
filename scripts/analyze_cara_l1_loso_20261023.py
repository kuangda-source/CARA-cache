#!/usr/bin/env python3
"""CPU-only nested scene-held-out conditional L1 analysis of accepted assets."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.policy_interval_assets_r1 import cells, SCENES, sha

ACTIONS = ('C', 'A_HALF', 'A_ONE')
PROTOCOL = 'plans/cara_L1_LOSO_offline_protocol_20261023.json'


def read(path):
    return json.loads(Path(path).read_text())


def protected_digest():
    prefixes = ('src', 'configs', 'manifests', 'docs', 'paper/experiment_master_table.json',
                'paper/internal_to_paper_mapping.json', 'plans/cara_policy_generator_20261020',
                'EXPERIMENT_REPORT.md', 'research/02_CURRENT_STATE.md',
                'research/09_NEXT_ACTIONS.md', 'memory/handoffs/LATEST.md')
    names = subprocess.check_output(['git', 'ls-files', '-z', '--', *prefixes], cwd=ROOT).decode().split('\0')
    records = [(p, sha(ROOT / p)) for p in names if p]
    return dict(files=len(records), sha256=hashlib.sha256(json.dumps(records).encode()).hexdigest())


def load_assets(protocol):
    capture = read(ROOT / protocol['capture'])
    accepted = read(ROOT / protocol['accepted'])
    # Consume the immutable completed acceptance; do not re-enter the GPU
    # lifecycle/finance stack merely to analyze already accepted scalar labels.
    if (accepted.get('status') != 'POLICY_INTERVAL_ASSETS_FULL_ORIGINALS_AND_FINANCE_ACCEPTED' or
            accepted.get('full_protocol_accepted') is not True or
            accepted.get('formal_source_time_cells') != 1624 or
            accepted.get('registered_paths') != 14 or accepted.get('missing_or_rejected_paths') != [] or
            accepted.get('source_revision') != capture['launch']['source_revision'] or
            accepted.get('registration_sha256') != capture['registration_sha256'] or
            accepted.get('capture_ref') != protocol['capture'] or
            accepted['capture_sha256'] != sha(ROOT / protocol['capture']) or
            not accepted['container_binding_accepted']):
        raise ValueError('Original complete asset acceptance/hash mismatch')
    groups = [r for r in capture['runner']['runs'] if r['section'] == 'FORMAL' and r['mode'] == 'COLLECT']
    if len(groups) != 4 or {r['scene'] for r in groups} != set(SCENES):
        raise ValueError('Exactly the original four CAL scenes required')
    grid = cells()
    ys, qs = [], []
    for name in SCENES:
        r = next(r for r in groups if r['scene'] == name)
        ps = r['interval_cells']
        if r['status'] != 'COMPLETE' or len(ps) != 406 or {(p['source'], p['target']) for p in ps} != set(grid):
            raise ValueError('Missing, duplicated or incomplete original cells')
        indexed = {(p['source'], p['target']): p for p in ps}
        yy, qq = [], []
        for s, t in grid:
            p = indexed[s, t]
            if (p['label_basis'] != 'TEACHER_CONDITIONED_PROPOSAL' or p['free_policy_history_truth']
                    or p['source_anchor_steps'] != [s-1, s] or p['actual_parent_action'] != 'DD'):
                raise ValueError('Original teacher-conditioned provenance required')
            v = p['statistics']
            yy.append([v['e2'], v['actual_half_MSE'], v['e2']+2*v['ed']+v['d2']])
            qq.append(v['d2'])
        ys.append(yy); qs.append(qq)
    y, d2 = np.array(ys), np.array(qs)
    if not np.isfinite(y).all() or not np.isfinite(d2).all() or np.any(y <= 0) or np.any(d2 <= 0):
        raise ValueError('Finite positive real losses and L1 magnitudes required')
    return y, np.log(d2), grid


def basis(grid):
    return np.array([[1., (t-21.5)/13.5, (t-s-14.5)/13.5] for s, t in grid])


def fit_predict(y_train, q_train, q_test, grid, mode, lam):
    """Test labels cannot enter this API; all centering/scaling is train-only."""
    if mode == 'log':
        base = np.log(y_train).mean(axis=0)
        response = np.log(y_train) - base
    elif mode == 'relative':
        base = y_train.mean(axis=0)
        response = y_train/base - 1
    else:
        raise ValueError(mode)
    qm = q_train.mean(axis=0)
    b = basis(grid)
    x = ((q_train-qm)[..., None]*b).reshape(-1, 3)
    xt = (q_test-qm)[:, None]*b
    scale = np.sqrt(np.mean(x*x, axis=0))
    scale = np.where(scale > 1e-12, scale, 1.)
    x, xt = x/scale, xt/scale
    beta = np.zeros(3)
    if lam is not None:
        beta = np.linalg.lstsq(x.T@x/len(x) + lam*np.eye(3),
                               x.T@response.ravel()/len(x), rcond=None)[0]
    adjustment = xt@beta
    baseline = np.exp(base) if mode == 'log' else base
    prediction = np.exp(base+adjustment) if mode == 'log' else base*np.maximum(1e-6, 1+adjustment)
    if not np.isfinite(prediction).all():
        raise ValueError('Nonfinite prediction')
    return baseline, prediction, dict(beta=beta.tolist(), feature_RMS=scale.tolist(),
        lambda_value=lam, positivity_clip_count=int(np.sum(1+adjustment < 1e-6)) if mode == 'relative' else 0)


def select_lambda(y_train, q_train, grid, mode, lambdas):
    # No-signal candidate first, larger regularization preferred on exact ties.
    candidates = [None] + sorted(lambdas, reverse=True)
    scores = []
    for lam in candidates:
        fold_scores = []
        for k in range(len(y_train)):
            use = [j for j in range(len(y_train)) if j != k]
            _, pred, _ = fit_predict(y_train[use], q_train[use], q_train[k], grid, mode, lam)
            err = ((np.log(pred)-np.log(y_train[k]))**2 if mode == 'log'
                   else ((pred-y_train[k])/y_train[use].mean())**2)
            fold_scores.append(float(err.mean()))
        scores.append(dict(lambda_value=lam, mean_score=float(np.mean(fold_scores)), inner_scores=fold_scores))
    best = min(range(len(scores)), key=lambda i: scores[i]['mean_score'])
    return candidates[best], scores


def predict_fold(y_train, q_train, q_test, grid, mode, lambdas):
    baselines, predictions, fits = [], [], []
    for j, action in enumerate(ACTIONS):
        lam, scores = select_lambda(y_train[:, :, j], q_train, grid, mode, lambdas)
        b, p, fit = fit_predict(y_train[:, :, j], q_train, q_test, grid, mode, lam)
        baselines.append(b); predictions.append(p)
        fits.append(dict(action=action, inner_selection=scores, **fit))
    return np.array(baselines).T, np.array(predictions).T, fits


def rank_score(y, p, grid):
    values = []
    for t in range(10, 36):
        ii = [i for i, (_, tt) in enumerate(grid) if tt == t]
        if len(ii) >= 3 and np.ptp(p[ii]) > 0 and np.ptp(y[ii]) > 0:
            values.append(float(spearmanr(y[ii], p[ii]).statistic))
    return dict(mean=float(np.mean(values)) if values else None, groups=len(values))


def refresh(y, predicted, grid, fraction):
    mask = np.zeros(len(grid), dtype=bool)
    oracle = np.zeros(len(grid), dtype=bool)
    for t in sorted({t for _, t in grid}):
        ii = np.array([i for i, (_, tt) in enumerate(grid) if tt == t])
        k = math.ceil(fraction*len(ii))
        mask[ii[np.argsort(-predicted[ii], kind='stable')[:k]]] = True
        oracle[ii[np.argsort(-y[ii], kind='stable')[:k]]] = True
    remaining = float(np.where(mask, 0., y).mean())
    oracle_remaining = float(np.where(oracle, 0., y).mean())
    return dict(hypothetical_D_cells=int(mask.sum()), residual_C_MSE=remaining,
                oracle_residual_C_MSE=oracle_remaining, regret=remaining-oracle_remaining)


def evaluate(y, predicted, grid, fractions):
    metrics = {}
    for j, a in enumerate(ACTIONS):
        truth, p = y[:, j], predicted[:, j]
        metrics[a] = dict(MSLE=float(np.mean((np.log(p)-np.log(truth))**2)),
            MAE=float(np.mean(np.abs(p-truth))), MSE=float(np.mean((p-truth)**2)),
            within_target_spearman=rank_score(truth, p, grid))
    action = np.argmin(predicted, axis=1)
    chosen = y[np.arange(len(y)), action]
    best = y.min(axis=1)
    choice = dict(actual_MSE=float(chosen.mean()), oracle_MSE=float(best.mean()),
        regret=float((chosen-best).mean()), counts={a:int(np.sum(action == j)) for j,a in enumerate(ACTIONS)},
        oracle_agreement=float(np.mean(action == np.argmin(y, axis=1))))
    return dict(prediction=metrics, action_choice=choice,
        refresh_proxy={str(f):refresh(y[:, 0], predicted[:, 0], grid, f) for f in fractions})


def aggregate(folds):
    result = {}
    for variant in ('baseline', 'L1'):
        m = [f[variant] for f in folds]
        result[variant] = dict(prediction={a:{k:float(np.mean([v['prediction'][a][k] for v in m]))
            for k in ('MSLE','MAE','MSE')} for a in ACTIONS},
            action_choice={k:float(np.mean([v['action_choice'][k] for v in m]))
                for k in ('actual_MSE','oracle_MSE','regret','oracle_agreement')},
            refresh_proxy={frac:{k:float(np.mean([v['refresh_proxy'][frac][k] for v in m]))
                for k in ('residual_C_MSE','oracle_residual_C_MSE','regret')}
                for frac in m[0]['refresh_proxy']})
    return result


def run_analysis(y, q, grid, protocol):
    modes = {}
    oof = []
    for mode in ('log', 'relative'):
        folds = []
        for holdout, name in enumerate(SCENES):
            train = [i for i in range(4) if i != holdout]
            b, p, fits = predict_fold(y[train], q[train], q[holdout], grid, mode, protocol['ridge_lambdas'])
            folds.append(dict(held_out=name, training_scenes=[SCENES[i] for i in train],
                train_cells=1218, held_out_cells=406, fits=fits,
                baseline=evaluate(y[holdout], b, grid, protocol['refresh_fractions']),
                L1=evaluate(y[holdout], p, grid, protocol['refresh_fractions'])))
            for i, (s, t) in enumerate(grid):
                oof.append(dict(mode=mode, scene=name, source=s, target=t, age=t-s,
                    log_d2=float(q[holdout,i]), truth=y[holdout,i].tolist(),
                    baseline=b[i].tolist(), L1=p[i].tolist()))
        modes[mode] = dict(folds=folds, scene_equal_aggregate=aggregate(folds))
    return modes, oof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.predictions.exists():
        raise ValueError('Refuse to replace previous analysis')
    protocol = read(ROOT / PROTOCOL)
    before = protected_digest()
    y, q, grid = load_assets(protocol)
    modes, oof = run_analysis(y, q, grid, protocol)
    after = protected_digest()
    if before != after:
        raise ValueError('Protected files changed during analysis')
    with args.predictions.open('x') as f:
        for row in oof:
            f.write(json.dumps(row, allow_nan=False)+'\n')
    result = dict(status='COMPLETE_CPU_EXPLORATORY_NESTED_SCENE_LOSO',
        completed_at=datetime.now(timezone.utc).isoformat(), formal_cells=1624, scenes=4, seeds=[0],
        source_bindings=[dict(path=p, sha256=sha(ROOT/p)) for p in
            (PROTOCOL, protocol['capture'], protocol['accepted'], str(Path(__file__).relative_to(ROOT)))],
        prediction_artifact=dict(path=str(args.predictions), sha256=sha(args.predictions), rows=len(oof)),
        protocol=protocol, protected_before=before, protected_after=after,
        GPU_submissions=0, live_server_calls=0, PG_P1_modified=False, price_data_used=False,
        independent_new_scenes=False, endpoint_or_speed_result=False, modes=modes,
        input_acceptance='Existing complete acceptance and its capture SHA verified; no repeat raw-tensor or finance acceptance',
        runtime=dict(python=sys.version.split()[0], numpy=np.__version__))
    with args.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({k:v['scene_equal_aggregate'] for k,v in modes.items()}, indent=2))


if __name__ == '__main__':
    main()
