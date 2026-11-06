#!/usr/bin/env python3
"""Describe saved P1 proxy/endpoint alignment; never run a model or scorer."""
import argparse
import base64
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.cara_fast_spec_r1 import digest


def ranks(values):
    result = [0.]*len(values)
    for value in set(values):
        places = [i+1 for i, v in enumerate(sorted(values)) if v == value]
        rank = sum(places)/len(places)
        for i, v in enumerate(values):
            if v == value:
                result[i] = rank
    return result


def spearman(x, y):
    a, b = ranks(x), ranks(y)
    a = [v-sum(a)/len(a) for v in a]
    b = [v-sum(b)/len(b) for v in b]
    denominator = math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
    return sum(u*v for u, v in zip(a, b))/denominator if denominator else None


def proxy(mask, model, sigmas, weights, triples):
    past, values, states = [], [], []
    for t in range(1, len(weights)+1):
        if t in mask:
            past.append(t)
            continue
        a, b = past[-2:]
        s, age, gap = sigmas[t-1], abs(sigmas[t-1]-sigmas[b-1]), abs(sigmas[b-1]-sigmas[a-1])
        features = (1., s, s*s, age, age*age, s*age, gap, gap*gap, s*gap, age*gap)
        raw = math.fsum(c*x for c, x in zip(model['coefficients'], features))
        values.append(weights[t-1]*max(0., raw))
        states.append(dict(t=t, a=a, b=b, seen=(t,a,b) in triples, clamped=raw < 0))
    return dict(cost=math.fsum(values),
        unseen_fraction=sum(not s['seen'] for s in states)/len(states),
        zero_clamp_fraction=sum(s['clamped'] for s in states)/len(states))


def audit(summary, manifest, weights, returns=None):
    labels = summary['source_labels']['rows']
    if len(labels) != 64 or summary['CPU_fixture_only'] is not False:
        raise ValueError('Original complete production64 label summary required')
    triples = {(r['t'], r['a'], r['b']) for r in labels}
    sigmas = manifest['schedule']['sigmas']
    by_id, origins = {}, {}
    for family, entry in summary['models'].items():
        for budget, plans in entry['families'][0]['candidates'].items():
            for plan in plans['plans']:
                key = plan['policy']['fingerprint']
                by_id[key] = plan['dense_steps']
                origins.setdefault(key, []).append(family+'-K'+budget)
                computed = proxy(plan['dense_steps'], entry['families'][0]['full_model'], sigmas, weights, triples)
                if not math.isclose(computed['cost'], plan['proxy_cost'], rel_tol=1e-12, abs_tol=1e-12):
                    raise ValueError('Reconstructed frozen proxy or numerical scale differs')
    means = {}
    for budget, search in summary['fair_searches'].items():
        for query in search['queries']:
            if query['status'] != 'COMPLETE':
                raise ValueError('Retain non-complete query rather than omit it')
            key = query['policy_fingerprint']
            by_id[key] = query['dense']
            origins.setdefault(key, []).append('search-K'+budget+'-q'+str(query['query_id']))
            means[key] = query['input_equal_Alex']
    if returns is not None:
        expected = {k for k in summary['operations'] if k.startswith('score-')}
        if set(returns) != expected or len(expected) != 42:
            raise ValueError('Complete42 distinct original score returns required')
        for name, encoded in returns.items():
            raw = base64.b64decode(encoded, validate=True)
            if hashlib.sha256(raw).hexdigest() != summary['operations'][name]['return_sha256']:
                raise ValueError('Original score return SHA differs')
            value = json.loads(raw)
            if value['kind'] != 'COMPLETE' or digest(value['payload']) != value['payload_sha256']:
                raise ValueError('Original complete score payload differs')
            rows = value['payload']['rows']
            key = name.removeprefix('score-')
            if ({r['member'] for r in rows} != set(manifest['FIT']) or len(rows) != 2
                    or any(r['candidate_id'] != key or r['status'] != 'COMPLETE'
                           or len(r['Alex_curve']) != 93 for r in rows)):
                raise ValueError('Original complete two-FIT93 score rows differ')
            mean = math.fsum(sum(r['Alex_curve'])/93 for r in rows)/2
            if key in means and not math.isclose(means[key], mean, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError('Original search/score mean differs')
            means[key] = mean
    if len(by_id) != 42:
        raise ValueError('Complete original42 candidate identities required')
    diagnostics, rows, alignment = {}, [], []
    for family, entry in summary['models'].items():
        stored = entry['families'][0]
        diagnostics[family] = dict(in_sample_MSE=stored['in_sample']['input_equal_MSE'],
            whole_parent_held_out_MSE=stored['held_out_input_equal_MSE'],
            held_out_parents=[f['held_out_parent'] for f in stored['whole_parent_folds']],
            held_out_rows=[f['diagnostic']['rows'] for f in stored['whole_parent_folds']])
        for key, mask in by_id.items():
            prediction = proxy(mask, stored['full_model'], sigmas, weights, triples)
            rows.append(dict(family=family, budget=len(mask), candidate_id=key,
                endpoint_LPIPS=means.get(key), origins=origins[key], **prediction))
        for budget in (19, 22):
            cohort = [r for r in rows if r['family'] == family and r['budget'] == budget
                      and r['endpoint_LPIPS'] is not None]
            comparisons = [(a,b) for a,b in combinations(cohort,2)
                if a['cost'] != b['cost'] and a['endpoint_LPIPS'] != b['endpoint_LPIPS']]
            alignment.append(dict(family=family, budget=budget, candidates=len(cohort),
                Spearman=spearman([r['cost'] for r in cohort], [r['endpoint_LPIPS'] for r in cohort]),
                non_tied_pairs=len(comparisons),
                concordance=sum((a['cost']-b['cost'])*(a['endpoint_LPIPS']-b['endpoint_LPIPS']) > 0
                    for a,b in comparisons)/len(comparisons) if comparisons else None))
    return dict(status='SAVED42_AUDIT_COMPLETE' if returns is not None else 'SAVED24_SEARCH_AUDIT_COMPLETE_18_DP_ENDPOINTS_MISSING',
        labels=len(labels), unique_source_triples=len(triples),
        independent_inputs=len({r['member'] for r in labels}),
        parent_plans=len({r['parent_id'] for r in labels}), expected_query_denominator=42,
        endpoint_query_count=len(means), stored_regression_diagnostics=diagnostics,
        alignment=alignment, rows=rows, adaptive_queries_are_descriptive_only=True,
        causal_failure_attribution_proven=False, old_FIT_reselected=False,
        metric_pairs_recomputed=0, GPU_submissions=0, ledger_written=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--summary', required=True)
    p.add_argument('--accepted-analysis', required=True)
    p.add_argument('--returns')
    p.add_argument('--manifest', required=True)
    p.add_argument('--weights', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    load = lambda path: json.loads(Path(path).read_bytes())
    expected = load(args.accepted_analysis)['algorithm_summary_sha256']
    if hashlib.sha256(Path(args.summary).read_bytes()).hexdigest() != expected:
        raise ValueError('Summary differs from the original accepted analysis SHA')
    result = audit(load(args.summary), load(args.manifest), load(args.weights)['weights'],
                   load(args.returns) if args.returns else None)
    result['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['input_sha256'] = {path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for path in (args.summary, args.accepted_analysis, args.manifest, args.weights,
                     *([args.returns] if args.returns else []))}
    with Path(args.output).open('x') as out:
        out.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','labels','unique_source_triples','endpoint_query_count',
        'stored_regression_diagnostics','alignment')},indent=2))


if __name__ == '__main__':
    main()
