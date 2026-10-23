#!/usr/bin/env python3
"""Noncausal scene-scale diagnostic; consumes accepted assets, never live jobs."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

import numpy as np

from analyze_cara_l1_loso_20261023 import ROOT, ACTIONS, SCENES, read, sha, load_assets, protected_digest

CLOSURE = 'plans/cara_probe_gate_closure_20261023.json'
VARIANTS = ('mean_log_d2', 'log_mean_RMS')


def scene_summary(q, variant):
    if variant == 'mean_log_d2':
        return np.mean(q, axis=-1)
    if variant == 'log_mean_RMS':
        half = q*.5
        top = np.max(half, axis=-1, keepdims=True)
        return np.squeeze(top, axis=-1) + np.log(np.mean(np.exp(half-top), axis=-1))
    raise ValueError(variant)


def scalar_predict(logy_train, g_train, g_test, lam):
    """Only train labels; one constant held-out log offset, fit at scene level."""
    baseline = np.mean(logy_train, axis=0)
    residual = np.mean(logy_train-baseline, axis=1)
    center = float(np.mean(g_train))
    scale = math.sqrt(math.fsum(float(v-center)**2 for v in g_train)/len(g_train))
    if scale < 1e-12:
        scale = 1.
    x = [(float(v)-center)/scale for v in g_train]
    denominator = math.fsum(v*v for v in x)/len(x)
    slope = 0.
    if lam is not None and denominator > 1e-24:
        slope = (math.fsum(v*float(r) for v,r in zip(x,residual))/len(x))/(denominator+lam)
    offset = slope*(float(g_test)-center)/scale
    return baseline, baseline+offset, dict(lambda_value=lam, slope=slope,
        summary_center=center,summary_scale=scale,constant_log_offset=offset)


def fit_scene_only(logy_train, g_train, g_test, lambdas):
    candidates = [None]+sorted(lambdas,reverse=True)
    records=[]
    for lam in candidates:
        errors=[]
        for j in range(len(g_train)):
            use=[k for k in range(len(g_train)) if k!=j]
            _,pred,_=scalar_predict(logy_train[use],g_train[use],g_train[j],lam)
            errors.append(float(np.mean((pred-logy_train[j])**2)))
        records.append(dict(lambda_value=lam,inner_losses=errors,mean_loss=float(np.mean(errors))))
    best=min(range(len(records)),key=lambda k:records[k]['mean_loss'])
    baseline,pred,fit=scalar_predict(logy_train,g_train,g_test,candidates[best])
    return baseline,pred,dict(**fit,inner_selection=records)


def decompose(log_truth, log_prediction):
    error=log_prediction-log_truth
    bias=float(np.mean(error))
    bias2=bias*bias
    centered=float(np.mean((error-bias)**2))
    loss=float(np.mean(error*error))
    if not math.isclose(bias2+centered,loss,rel_tol=1e-12,abs_tol=1e-14):
        raise ValueError('Squared-log-loss decomposition failed')
    return dict(log_MSE=loss,mean_log_error=bias,squared_mean_log_error=bias2,
        centered_log_error_MSE=centered,best_constant_offset_oracle_log_MSE=centered)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--predictions',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists() or args.predictions.exists():
        raise ValueError('Refuse to overwrite recorded results')
    closure=read(ROOT/CLOSURE)
    prior_path=closure['allowed_closeout']['prior_report']
    prior=read(ROOT/prior_path)
    for v in prior['source_bindings']:
        if sha(ROOT/v['path'])!=v['sha256']:
            raise ValueError('Original analysis source drift')
    pred_ref=prior['prediction_artifact']
    if sha(ROOT/pred_ref['path'])!=pred_ref['sha256']:
        raise ValueError('Original outer-fold prediction drift')
    old=[json.loads(line) for line in (ROOT/pred_ref['path']).read_text().splitlines()]
    old=[r for r in old if r['mode']=='log']
    protected_before=protected_digest()  # Current PG-P1 snapshot, not yesterday's file tree.
    y,q,grid=load_assets(prior['protocol'])
    logy=np.log(y)
    summaries={v:scene_summary(q,v) for v in VARIANTS}
    folds=[];oof=[]
    max_centered_change=0.
    for i,name in enumerate(SCENES):
        train=[k for k in range(4) if k!=i]
        previous=[r for r in old if r['scene']==name]
        if [(r['source'],r['target']) for r in previous]!=grid:
            raise ValueError('Original OOF grid changed')
        oldbase=np.log(np.array([r['baseline'] for r in previous]))
        oldfull=np.log(np.array([r['L1'] for r in previous]))
        fold=dict(scene=name,training_scenes=[SCENES[k] for k in train],actions={})
        for j,action in enumerate(ACTIONS):
            record=dict(baseline=decompose(logy[i,:,j],oldbase[:,j]),
                previous_cellwise_L1=decompose(logy[i,:,j],oldfull[:,j]),variants={})
            for variant in VARIANTS:
                b,pred,fit=fit_scene_only(logy[train,:,j],summaries[variant][train],
                    summaries[variant][i],prior['protocol']['ridge_lambdas'])
                np.testing.assert_allclose(b,oldbase[:,j],atol=1e-13,rtol=1e-13)
                stats=decompose(logy[i,:,j],pred)
                # A constant log-offset must preserve all within-scene ordering.
                np.testing.assert_array_equal(np.argsort(b,kind='stable'),np.argsort(pred,kind='stable'))
                change=abs(stats['centered_log_error_MSE']-record['baseline']['centered_log_error_MSE'])
                max_centered_change=max(max_centered_change,change)
                record['variants'][variant]=dict(**stats,fit=fit)
                oof.append(dict(scene=name,action=action,variant=variant,
                    summary=float(summaries[variant][i]),log_predictions=pred.tolist()))
            fold['actions'][action]=record
        folds.append(fold)
    aggregates={}
    for action in ACTIONS:
        rows=[r['actions'][action] for r in folds]
        keys=('log_MSE','squared_mean_log_error','centered_log_error_MSE')
        base={k:float(np.mean([r['baseline'][k] for r in rows])) for k in keys}
        full={k:float(np.mean([r['previous_cellwise_L1'][k] for r in rows])) for k in keys}
        gain=base['log_MSE']-full['log_MSE']
        variants={}
        for v in VARIANTS:
            means={k:float(np.mean([r['variants'][v][k] for r in rows])) for k in keys}
            means.update(relative_loss_reduction=1-means['log_MSE']/base['log_MSE'],
                fraction_of_previous_loss_reduction=(base['log_MSE']-means['log_MSE'])/gain,
                improved_scenes=sum(r['variants'][v]['log_MSE']<r['baseline']['log_MSE'] for r in rows))
            variants[v]=means
        aggregates[action]=dict(baseline=base,previous_cellwise_L1=full,variants=variants,
            previous_gain_from_mean_bias_reduction=base['squared_mean_log_error']-full['squared_mean_log_error'],
            previous_gain_from_centered_error_reduction=base['centered_log_error_MSE']-full['centered_log_error_MSE'],
            fraction_of_previous_gain_from_mean_bias=(base['squared_mean_log_error']-full['squared_mean_log_error'])/gain,
            best_constant_offset_oracle_log_MSE=base['centered_log_error_MSE'])
    protected_after=protected_digest()
    if protected_after!=protected_before:
        raise ValueError('Protected mainline files changed during closeout')
    with args.predictions.open('x') as f:
        for r in oof:f.write(json.dumps(r,allow_nan=False)+'\n')
    result=dict(status='CLOSED_WITH_CPU_SCENE_SCALE_DIAGNOSTIC',
        completed_at=datetime.now(timezone.utc).isoformat(),formal_cells=1624,scenes=4,seeds=[0],
        closure=closure,scene_summaries={v:dict(zip(SCENES,s.tolist())) for v,s in summaries.items()},
        folds=folds,scene_equal_aggregate=aggregates,
        scalar_offset_preserves_ranking=True,max_centered_MSE_change=max_centered_change,
        prediction_artifact=dict(path=str(args.predictions),sha256=sha(args.predictions)),
        source_bindings=[dict(path=v,sha256=sha(ROOT/v)) for v in
            (CLOSURE,prior_path,pred_ref['path'],str(Path(__file__).relative_to(ROOT)))]+prior['source_bindings'],
        protected_before=protected_before,protected_after=protected_after,
        GPU_submissions=0,live_server_calls=0,new_data_collection=False,PG_P1_modified=False,
        causal_online_signal=False,new_independent_validation=False)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(aggregates,indent=2))


if __name__=='__main__':main()
