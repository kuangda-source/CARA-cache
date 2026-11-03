#!/usr/bin/env python3
"""Strong-reference ranks, Uniform-distance sensitivity and new single-source pools."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from audit_cara_source_coverage_saved_r1 import geometry
from audit_cara_source_proxy_saved_r1 import ranks,spearman
from wcomr.cara_fast_spec_r1 import digest,profile_from
from wcomr.cara_phase_coverage_topk_r1 import seven_candidate_pool


def hamming(a,b):
    return len(set(a)^set(b))


def objective(profile,sigmas,row,tilt):
    cost=geometry(profile,sigmas,row['dense_steps'],'single',tilt)
    return cost['peak_units'],cost['squared_units']


def audit(card,previous,pools):
    rows=previous['endpoint_rows'];profile=profile_from(card['profile']);sigmas=card['schedule']['sigmas']
    if len(rows)!=44 or previous['original_query_count']!=42:
        raise ValueError('Complete original42 plus two strong pure-C references required')
    reference_ranks=[]
    for tilt in (0.,-2.,2.,4.):
        keys=[objective(profile,sigmas,row,tilt) for row in rows]
        global_ranks=ranks(keys)
        for i,row in enumerate(rows):
            if row['origins'] not in (['F19_C'],['BUDGET_SEARCH19_C']):
                continue
            indices=[j for j,r in enumerate(rows) if r['D']==row['D']]
            reference_ranks.append(dict(role=row['origins'][0],D=row['D'],tilt=tilt,
                rank_all44=global_ranks[i],rank_same_D=ranks([keys[j] for j in indices])[indices.index(i)],
                same_D_denominator=len(indices),LPIPS=row['LPIPS']))
    sensitivity=[];distance_histograms={}
    for budget in (19,22):
        uniform=[i for i,a in enumerate(card['roles'][f'UNIFORM{budget}_C']['policy']['actions'],1) if a=='D']
        for corpus in ('ORIGINAL_QUERY_ONLY','WITH_STRONG_REFERENCES'):
            cohort=[dict(r,uniform_hamming=hamming(r['dense_steps'],uniform)) for r in rows
                if r['D']==budget and (corpus!='ORIGINAL_QUERY_ONLY' or r['original_query'])]
            distance_histograms[f'{corpus}-K{budget}']={str(h):sum(r['uniform_hamming']==h for r in cohort)
                for h in sorted({r['uniform_hamming'] for r in cohort})}
            for cutoff in (0,2,4,6,8,10,12):
                group=[r for r in cohort if r['uniform_hamming']>=cutoff]
                for tilt in (0.,-2.,2.,4.):
                    values=[objective(profile,sigmas,row,tilt) for row in group]
                    sensitivity.append(dict(corpus=corpus,D=budget,min_uniform_hamming=cutoff,
                        min_swaps=cutoff/2,candidates=len(group),tilt=tilt,
                        Spearman=spearman(values,[r['LPIPS'] for r in group]) if len(group)>=3 else None,
                        per_input_Spearman={member:spearman(values,[r['per_input_LPIPS'][member] for r in group])
                            for member in previous['original_query_inputs']} if len(group)>=3 else {},
                        status='DESCRIPTIVE_ONLY' if len(group)>=3 else 'TOO_FEW_PLANS_NOT_ESTIMATED'))
    f19=[i for i,a in enumerate(card['roles']['F19_C']['policy']['actions'],1) if a=='D']
    optima=[]
    for budget in (16,17,19,22):
        for tilt in (2.,4.):
            candidate=next(c for c in pools[str(budget)]['candidates']
                if any(o['tilt']==tilt and o['rank']==1 for o in c['origins']))
            optima.append(dict(D=budget,tilt=tilt,candidate_id=candidate['candidate_id'],
                dense_steps=candidate['dense_steps'],hamming_to_F19=hamming(candidate['dense_steps'],f19),
                D_8_to_16=sum(8<=t<=16 for t in candidate['dense_steps']),
                max_C_run=max(b-a-1 for a,b in zip(candidate['dense_steps'],candidate['dense_steps'][1:]+[37])),
                same_D_as_F19=budget==19))
    ids={r['candidate_id'] for r in rows}
    return dict(schema='CARA_PHASE_COVERAGE_ZERO_GPU_ROBUSTNESS_R1',
        status='ZERO_GPU_STRONG_REFERENCES_AND_UNIFORM_DISTANCE_CHECKS_COMPLETE',
        original_unique_queries=42,augmented_pure_C_layouts=44,independent_inputs=2,
        reference_ranks=reference_ranks,Uniform_distance_histograms=distance_histograms,
        Uniform_distance_sensitivity=sensitivity,geometric_optima=optima,
        first_lambda_order_fixed_before_audit=[0.,-2.,2.,4.],all_four_lambdas_reported=True,
        primary_far_from_Uniform_threshold=dict(hamming=6,refresh_swaps=3),
        mixed_D_all44_rank_is_secondary_to_same_D_rank=True,
        new_pool_existing_endpoint_overlap={k:[r['candidate_id'] for r in p['candidates'] if r['candidate_id'] in ids]
            for k,p in pools.items()},
        inference_scope='DEVELOPMENT_SCREEN_NOT_INDEPENDENT_PAPER_EVIDENCE',
        P0_does_not_identify_phase_causality=True,metrics_recomputed=0,
        old_FIT_reselected=False,models_loaded=False,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--pools-output',required=True)
    args=parser.parse_args()
    refs=dict(card='plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json',
        previous='reports/cara_source_coverage_C1_zero_GPU_audit_r1_20261103.json')
    raw={k:(ROOT/p).read_bytes() for k,p in refs.items()};loaded={k:json.loads(v) for k,v in raw.items()}
    for name,expected in loaded['previous']['input_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Original endpoint audit input SHA changed: '+name)
    card=loaded['card'];profile=profile_from(card['profile'])
    pools={str(k):seven_candidate_pool(profile,k,card['schedule']['sigmas']) for k in (16,17,19,22)}
    bundle=dict(schema='CARA_PHASE_SINGLE_SOURCE_CANDIDATE_POOLS_R3',pools=pools,
        basis='DEVELOPMENT_DESIGN_AFTER_ORIGINAL42_AUDIT',
        main19_requested_slots='lambda2_top3_lambda4_top3_lambda0_top1',
        global_topk_includes_higher_peak_runners_up=True,
        old_strict_minimum_peak_pool_changed=False,new_video_evaluated=False,
        GPU_authorized=False,GPU_submissions=0,ledger_written=False)
    bundle['bundle_sha256']=digest(bundle)
    result=audit(**loaded,pools=pools)
    sources=[Path(__file__),ROOT/'src/wcomr/cara_phase_coverage_topk_r1.py',
        ROOT/'src/wcomr/cara_source_coverage_r1.py',ROOT/'scripts/audit_cara_source_coverage_saved_r1.py']
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    result['input_sha256']={refs[k]:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    result['new_pools_bundle_sha256']=bundle['bundle_sha256']
    for name,value in ((args.pools_output,bundle),(args.output,result)):
        with Path(name).open('x') as out:out.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'],reference_ranks=result['reference_ranks'],
        pool_sizes={k:p['unique_candidates'] for k,p in pools.items()},optima=result['geometric_optima']),indent=2))


if __name__=='__main__':
    main()
