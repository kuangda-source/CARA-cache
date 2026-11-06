#!/usr/bin/env python3
"""Exact source-only placement bound on the already-exposed human trace."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from wcomr.forecast_placement import optimize, replay
from wcomr.selective_refresh_policy import SparseRefreshPolicy


def analyze(receipt):
    assert receipt['status']=='SIX_SELECTIVE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    assert receipt['scope']['run_id']=='wc-selective-human-r1'
    assert receipt['planned_output_files']==receipt['planned_total_phases']==6
    phases=receipt['measurement']['phases']
    assert receipt['measurement']['variant_names']==['fixed_D','full_S','small_S','cadenced_S']
    controls=[]
    for phase,policy in zip(phases[1:],receipt['policies']):
        p=SparseRefreshPolicy(tuple(policy['sparse_layers']),policy['every'])
        assert p.to_dict()==policy==phase['refresh_provenance']['selection_policy']
        result=replay(phase['refresh_provenance']['events'],p,verify_actual=True)
        assert result['deep_calls']==38 and result['cache_calls']==34
        assert len(result['approximate_cache_calls'])==26
        controls.append(result)
    events=phases[1]['refresh_provenance']['events']
    layers=receipt['policies'][0]['sparse_layers'];quotas=controls[-1]['S_per_CFG']
    assert quotas==[6,5]
    bounded=optimize(events,layers,quotas,keep_first_S=True)
    free=optimize(events,layers,quotas,keep_first_S=False)
    for result in (bounded,free):
        assert result['replay']['deep_calls']==38 and result['replay']['cache_calls']==34
        assert result['replay']['S_per_CFG']==quotas and result['replay']['S_operators']==253
    return {'status':'EXPOSED_FIXED_BUDGET_EXACT_SOURCE_PLACEMENT_BOUND_CPU_NOT_VIDEO',
        'CPU_only':True,'new_GPU_submission':False,'quality_acceptance':False,
        'same_S_quota_per_CFG':quotas,'reproduced_actual_three_policy_topologies':controls,
        'first_S_matched_optimum':bounded,'unconstrained_optimum':free,
        'limits':['All selections use an exposed future full/cache mask; they are oracle diagnostics, not an online method.',
            'Only source topology and ages are replayed; latent/probe/Gamma/output changes are not predicted.',
            'Nominal38 deep/11 S/253 operators are matched; actual GPU wall, operator work and video fidelity remain unmeasured.',
            'Even first-S matching does not match every later S location; no unique causal attribution of final error.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    raw=gzip.decompress(a.receipt.read_bytes());r=analyze(json.loads(raw))
    r.update(input_raw_sha256=hashlib.sha256(raw).hexdigest(),
        analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        replay_source_sha256=hashlib.sha256((Path(__file__).parents[1]/'src/wcomr/forecast_placement.py').read_bytes()).hexdigest())
    a.output.write_text(json.dumps(r,indent=2)+'\n')
    manifest={'role':'EXPOSED_FUTURE_TRACE_FIXED_BUDGET_PLACEMENT_DRAFT_NOT_ONLINE',
        'sample':'human_199','seed':0,'source_raw_sha256':r['input_raw_sha256'],
        'fixed_mask':json.loads(raw)['fixed_mask'],'same_S_quota_per_CFG':r['same_S_quota_per_CFG'],
        'legacy_policy':json.loads(raw)['policies'][2],
        'first_S_matched_policy':r['first_S_matched_optimum']['policy'],
        'unconstrained_policy':r['unconstrained_optimum']['policy'],
        'GPU_card_selected':False,'GPU_submitted':False,'reserved_seconds':0,
        'quality_acceptance':False,'online_policy':False}
    a.manifest.write_text(json.dumps(manifest,indent=2)+'\n')
    def compact(result):
        return {'policy':result['policy'],'branches':result['branches'],
            'S_calls':result['replay']['S_calls'],
            'approximate_cache_calls':result['replay']['approximate_cache_calls'],
            'source_reads':result['replay']['approximate_source_reads']}
    print(json.dumps({'status':r['status'],'legacy_approximate_cache_calls':26,
        'first_matched':compact(r['first_S_matched_optimum']),
        'free':compact(r['unconstrained_optimum'])},indent=2))
