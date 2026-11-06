#!/usr/bin/env python3
"""Independent scalar arithmetic audit and explicitly post-hoc equal-count check.

No refitting, new features, thresholds or outer-test-driven model selection.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

from analyze_cara_l1_loso_20261023 import ROOT, ACTIONS, SCENES, sha, read, load_assets, basis, protected_digest


def constrained_choice(losses, counts):
    slots = np.repeat(np.arange(3), counts)
    if len(slots) != len(losses):
        raise ValueError('All action counts must be preserved')
    rows, cols = linear_sum_assignment(losses[:, slots])
    chosen = np.empty(len(losses), dtype=int)
    chosen[rows] = slots[cols]
    if not np.array_equal(np.bincount(chosen,minlength=3), counts):
        raise ValueError('Assignment changed action counts')
    return chosen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = read(a.report)
    for binding in report['source_bindings']:
        if sha(ROOT / binding['path']) != binding['sha256']:
            raise ValueError('Source binding drift')
    artifact = report['prediction_artifact']
    if sha(ROOT / artifact['path']) != artifact['sha256']:
        raise ValueError('Prediction artifact drift')
    records = [json.loads(line) for line in (ROOT / artifact['path']).read_text().splitlines()]
    y, q, grid = load_assets(report['protocol'])
    b = basis(grid)
    max_prediction_diff = 0.
    max_beta_diff = 0.
    rows = []
    for mode, result in report['modes'].items():
        for i, fold in enumerate(result['folds']):
            training = [j for j in range(4) if j != i]
            rec = [r for r in records if r['mode'] == mode and r['scene'] == SCENES[i]]
            if [(r['source'],r['target']) for r in rec] != grid:
                raise ValueError('OOF coverage/order error')
            pred, base = np.array([r['L1'] for r in rec]), np.array([r['baseline'] for r in rec])
            np.testing.assert_array_equal(np.array([r['truth'] for r in rec]), y[i])
            for j, fit in enumerate(fold['fits']):
                yt = y[training,:,j]
                intercept = np.log(yt).mean(axis=0) if mode == 'log' else yt.mean(axis=0)
                response = np.log(yt)-intercept if mode == 'log' else yt/intercept-1
                qm = q[training].mean(axis=0)
                x = ((q[training]-qm)[...,None]*b).reshape(-1,3)/np.array(fit['feature_RMS'])
                z = (q[i]-qm)[:,None]*b/np.array(fit['feature_RMS'])
                beta = np.zeros(3)
                lam = fit['lambda_value']
                if lam is not None:
                    # Explicit scalar fsum bypasses platform BLAS matrix products.
                    gram = np.array([[math.fsum(float(row[k])*float(row[l]) for row in x)/len(x)
                        + (lam if k == l else 0.) for l in range(3)] for k in range(3)])
                    rhs = np.array([math.fsum(float(row[k])*float(v) for row,v in zip(x,response.ravel()))/len(x)
                        for k in range(3)])
                    beta = np.linalg.lstsq(gram,rhs,rcond=None)[0]
                max_beta_diff = max(max_beta_diff,float(np.max(np.abs(beta-fit['beta']))))
                adj = np.array([math.fsum(float(v)*float(w) for v,w in zip(row,beta)) for row in z])
                independent = np.exp(intercept+adj) if mode == 'log' else intercept*np.maximum(1e-6,1+adj)
                max_prediction_diff = max(max_prediction_diff,float(np.max(np.abs(independent-pred[:,j]))))
                np.testing.assert_allclose(independent,pred[:,j],rtol=1e-10,atol=1e-10)
            baseline_action = base.argmin(axis=1)
            counts = np.bincount(baseline_action,minlength=3)
            chosen = constrained_choice(pred,counts)
            oracle = constrained_choice(y[i],counts)
            mean = lambda action: float(y[i,np.arange(len(grid)),action].mean())
            bm,lm,om = mean(baseline_action),mean(chosen),mean(oracle)
            rows.append(dict(mode=mode,scene=SCENES[i],counts=dict(zip(ACTIONS,counts.tolist())),
                baseline_MSE=bm,L1_matched_count_MSE=lm,matched_count_oracle_MSE=om,
                baseline_regret=bm-om,L1_regret=lm-om,relative_MSE_reduction=1-lm/bm))
    totals = {}
    for mode in report['modes']:
        rr = [r for r in rows if r['mode'] == mode]
        means = {k:float(np.mean([r[k] for r in rr])) for k in
                 ('baseline_MSE','L1_matched_count_MSE','matched_count_oracle_MSE','baseline_regret','L1_regret')}
        means.update(relative_MSE_reduction=1-means['L1_matched_count_MSE']/means['baseline_MSE'],
            improved_scenes=sum(r['relative_MSE_reduction']>0 for r in rr))
        totals[mode]=means
    protected = protected_digest()
    if protected != report['protected_before']:
        raise ValueError('Protected mainline files differ from original snapshot')
    result=dict(status='INDEPENDENT_ARITHMETIC_AND_MATCHED_COUNT_AUDIT_COMPLETE',
        report_sha256=sha(a.report),source_sha256=sha(__file__),
        checked_OOF_rows=len(records),max_abs_prediction_difference=max_prediction_diff,
        max_abs_beta_difference=max_beta_diff,protected_files_unchanged=protected,
        supplemental_scope='POST_HOC_DIAGNOSTIC_AFTER_PRIMARY_RESULTS; no refit or selection; exact baseline C/A_HALF/A_ONE counts retained per scene; counterfactual cells only, not a deployable trajectory or matched runtime',
        initial_execution_notes=['First attempt stopped before fitting: existing lifecycle acceptor transitively required unavailable torch; fixed to consume and SHA-bind saved complete acceptance instead, without changing model protocol.',
            'Successful primary run emitted platform numpy matmul floating-point warnings but all outputs were finite. This audit independently recomputes every selected regression and prediction using scalar fsum products.'],
        matched_action_count_folds=rows,scene_equal_aggregate=totals,
        GPU_submissions=0,live_server_calls=0)
    with a.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
