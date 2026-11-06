#!/usr/bin/env python3
"""Audit C1 geometry against original P1 endpoints; no generation or scoring."""
import argparse
import base64
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from audit_cara_source_proxy_saved_r1 import spearman
from wcomr.cara_fast_spec_r1 import digest, policy_from_mask, profile_from
from wcomr.cara_source_coverage_r1 import DISTANCE_SCALE, TILTS, coverage_distance, normalized_sigmas


def geometry(profile, sigmas, dense, mode, tilt):
    """The generator's exact quantized (peak, squared energy) objective."""
    policy_from_mask(profile, dense)
    scales = normalized_sigmas(profile, sigmas)
    history, values = [], []
    for t in range(1, profile.horizon+1):
        if t in dense:
            history.append(t)
        else:
            a, b = history[-2:]
            values.append(round(DISTANCE_SCALE*coverage_distance(scales, t, a, b, tilt, mode)))
    peak, energy = max(values, default=0), sum(v*v for v in values)
    return dict(peak_units=peak, squared_units=energy,
                peak=peak/DISTANCE_SCALE, squared_sum=energy/DISTANCE_SCALE**2)


def coverage_rows(card):
    result = []
    for name, view in card['views'].items():
        if not name.startswith(('main8-', 'single8-')):
            continue
        for index, candidate in enumerate(view['candidates'], 1):
            early = [t for t in candidate['dense_steps'] if 8 <= t <= 16]
            result.append(dict(view=name, index=index, candidate_id=candidate['candidate_id'],
                dense_steps=candidate['dense_steps'], D_8_to_16=len(early), early_dense=early,
                origins=candidate['origins'],
                phase3_member=any(c['candidate_id']==candidate['candidate_id'] for c in
                    card['views'][name.replace('main8-', 'phase3-').replace('single8-', 'phase3-')]['candidates']),
                neutral3_member=any(c['candidate_id']==candidate['candidate_id'] for c in
                    card['views'][name.replace('main8-', 'neutral3-').replace('single8-', 'neutral3-')]['candidates'])))
    return result


def original_queries(summary, analysis, returns, fit_members):
    if (summary['CPU_fixture_only'] is not False or analysis['CPU_fixture_only'] is not False
            or summary['scope_sha256'] != analysis['scope_sha256']):
        raise ValueError('The complete original production P1 receipts are required')
    masks, origins = {}, {}
    for family, model in summary['models'].items():
        for budget, group in model['families'][0]['candidates'].items():
            for index, plan in enumerate(group['plans'], 1):
                key = plan['policy']['fingerprint']
                masks[key] = plan['dense_steps']
                origins.setdefault(key, []).append(f'{family}-K{budget}-rank{index}')
    for budget, search in summary['fair_searches'].items():
        for query in search['queries']:
            key = query['policy_fingerprint']
            masks[key] = query['dense']
            origins.setdefault(key, []).append(f'search-K{budget}-query{query["query_id"]}')
    expected = {name for name in summary['operations'] if name.startswith('score-')}
    if len(expected)!=42 or set(returns)!=expected or len(masks)!=42:
        raise ValueError('All 42 original score returns and mask identities are required')
    rows = []
    for name in sorted(expected):
        raw = base64.b64decode(returns[name], validate=True)
        if hashlib.sha256(raw).hexdigest()!=summary['operations'][name]['return_sha256']:
            raise ValueError('Original score return SHA differs: '+name)
        saved = json.loads(raw)
        if saved['kind']!='COMPLETE' or digest(saved['payload'])!=saved['payload_sha256']:
            raise ValueError('Original complete internal return differs')
        packet = saved['payload']
        scores = packet['rows']
        key = name.removeprefix('score-')
        if (len(scores)!=2 or {r['member'] for r in scores}!=set(fit_members)
                or any(r['candidate_id']!=key or r['status']!='COMPLETE' or len(r['Alex_curve'])!=93
                       for r in scores)):
            raise ValueError('Complete two-FIT / 93-frame scores differ')
        per_input = {r['member']:math.fsum(r['Alex_curve'])/93 for r in scores}
        rows.append(dict(candidate_id=key, dense_steps=masks[key], D=len(masks[key]),
            origins=origins[key], per_input_LPIPS=per_input,
            LPIPS=math.fsum(per_input.values())/2, original_query=True))
    return rows


def alignment(rows, profile, sigmas):
    result = []
    for budget in (19, 22):
        group = [r for r in rows if r['D']==budget]
        for mode in ('single', 'two'):
            for tilt in TILTS:
                values = [geometry(profile, sigmas, r['dense_steps'], mode, tilt) for r in group]
                objective = [(v['peak_units'], v['squared_units']) for v in values]
                endpoint = [r['LPIPS'] for r in group]
                pairs = [(i,j) for i,j in combinations(range(len(group)), 2)
                         if objective[i]!=objective[j] and endpoint[i]!=endpoint[j]]
                result.append(dict(D=budget, mode=mode, tilt=tilt, candidates=len(group),
                    input_count=2, Spearman_lexicographic=spearman(objective, endpoint),
                    Spearman_peak=spearman([v['peak_units'] for v in values], endpoint),
                    Spearman_energy=spearman([v['squared_units'] for v in values], endpoint),
                    non_tied_pairs=len(pairs),
                    concordance=sum((objective[i]<objective[j])==(endpoint[i]<endpoint[j]) for i,j in pairs)/len(pairs)
                        if pairs else None,
                    per_input_Spearman={member:spearman(objective, [r['per_input_LPIPS'][member] for r in group])
                        for member in group[0]['per_input_LPIPS']}))
    return result


def audit(card, summary, analysis, returns):
    profile = profile_from(card['profile'])
    rows = original_queries(summary, analysis, returns, card['FIT'])
    originals = {r['candidate_id']:r for r in rows}
    augmented = dict(originals)
    omitted = []
    for role, definition in card['roles'].items():
        policy = definition.get('policy')
        if not policy or set(policy['actions'])-{'D','C'}:
            omitted.append(dict(role=role, reason='NATIVE_OR_NON_PURE_C_NOT_A_19D22D_C_LAYOUT'))
            continue
        matching = [r for r in analysis['rows'] if r['role']==role and r['member'] in card['FIT']]
        if len(matching)!=2:
            raise ValueError('Complete original FIT reference missing: '+role)
        key = policy['fingerprint']
        per_input = {r['member']:r['metrics']['Alex'] for r in matching}
        if any(r['candidate']['candidate_id']!=key for r in matching):
            raise ValueError('Original same-batch reference mask identity differs')
        if key in augmented:
            if any(not math.isclose(per_input[m], augmented[key]['per_input_LPIPS'][m], abs_tol=1e-12, rel_tol=0)
                   for m in per_input):
                raise ValueError('Original repeated candidate endpoint differs')
            continue
        dense = [i for i,a in enumerate(policy['actions'],1) if a=='D']
        augmented[key] = dict(candidate_id=key, dense_steps=dense, D=len(dense), origins=[role],
            per_input_LPIPS=per_input, LPIPS=math.fsum(per_input.values())/2, original_query=False)
    coverage = coverage_rows(card)
    f19 = [i for i,a in enumerate(card['roles']['F19_C']['policy']['actions'],1) if a=='D']
    return dict(schema='CARA_C1_ZERO_GPU_COVERAGE_AND_ORIGINAL_ENDPOINT_AUDIT_R1',
        status='COMPLETE_ORIGINAL42_ZERO_GPU_AUDIT', original_query_count=len(rows),
        original_query_inputs=card['FIT'], independent_input_count=2,
        pure_C_augmented_unique_layouts=len(augmented), excluded_reference_roles=omitted,
        original42_alignment=alignment(rows, profile, card['schedule']['sigmas']),
        augmented_alignment=alignment(list(augmented.values()), profile, card['schedule']['sigmas']),
        endpoint_rows=list(augmented.values()), candidate_coverage=coverage,
        F19_dense_steps=f19, F19_D_8_to_16=sum(8<=t<=16 for t in f19),
        current_C1_candidates_with_existing_endpoints=[r['candidate_id'] for r in coverage if r['candidate_id'] in augmented],
        geometry_feature_definition='equal_update_sigma_distance_then_single_age_or_mean_of_two_source_ages',
        phase_weight='exp(tilt*(normalized_sigma-0.5))', phase_tilts=list(TILTS),
        phase3_first_rank_tilts=[0.,-2.,4.], local_error_labels_used_by_C1=0,
        endpoint_sensitive_weights_fitted=False, lower_geometry_and_lower_LPIPS_should_be_concordant=True,
        existing_queries_adaptive_and_development_only=True, rank_correlation_is_not_new_input_evidence=True,
        old_FIT_winners_reselected=False, metrics_recomputed=0, GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score-returns', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    refs = dict(card='plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json',
        summary='reports/cara_v1_P1_successor_original_algorithm_summary_r1_20261103.json',
        analysis='reports/cara_v1_P1_successor_original_complete_analysis_r1_20261103.json',
        returns=args.score_returns)
    raw = {k:Path(v).read_bytes() for k,v in refs.items()}
    inputs = {k:json.loads(v) for k,v in raw.items()}
    if hashlib.sha256(raw['summary']).hexdigest()!=inputs['analysis']['algorithm_summary_sha256']:
        raise ValueError('Original summary/accepted analysis SHA differs')
    result = audit(**inputs)
    result['input_sha256'] = {refs[k]:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    result['source_sha256'] = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__), ROOT/'src/wcomr/cara_source_coverage_r1.py', ROOT/'scripts/audit_cara_source_proxy_saved_r1.py']}
    with Path(args.output).open('x') as out:
        out.write(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'],queries=result['original_query_count'],
        unique_pure_C=result['pure_C_augmented_unique_layouts'],alignment=result['original42_alignment']),indent=2))


if __name__ == '__main__':
    main()
