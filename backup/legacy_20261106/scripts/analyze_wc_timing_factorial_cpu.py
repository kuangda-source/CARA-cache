#!/usr/bin/env python3
"""Two early versus two late S interventions on the exposed fixed human mask."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from wcomr.forecast_placement import replay
from wcomr.selective_refresh_policy import SparsePlacementPolicy


def analyze(raw):
    assert hashlib.sha256(raw).hexdigest() == 'f6fb44d6b9f6133c23d7b7b291e22e53d60f55db14beb9117132b0e901d3d11c'
    r = json.loads(raw)
    assert r['status'] == 'SIX_FORECAST_PLACEMENT_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    assert r['comparison'] == 'forecast_placement' and sum(r['fixed_mask']['dense_calls']) == 38
    first, free = r['policies'][1:]
    layers = tuple(first['sparse_layers']); assert layers == tuple(free['sparse_layers'])
    common = tuple(tuple(sorted(set(a) & set(b))) for a,b in zip(first['per_cfg_eligible_ordinals'],free['per_cfg_eligible_ordinals']))
    early = tuple(tuple(sorted(set(a)-set(b))) for a,b in zip(first['per_cfg_eligible_ordinals'],free['per_cfg_eligible_ordinals']))
    late = tuple(tuple(sorted(set(b)-set(a))) for a,b in zip(first['per_cfg_eligible_ordinals'],free['per_cfg_eligible_ordinals']))
    assert common == ((4,5,6,7,8),(4,5,6,7)) and early == ((1,),(1,)) and late == ((9,),(8,))
    arms = []
    for e,l in ((0,0),(1,0),(0,1),(1,1)):
        slots = tuple(tuple(sorted(set(common[cfg]) | (set(early[cfg]) if e else set()) | (set(late[cfg]) if l else set()))) for cfg in (0,1))
        policy = SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=slots)
        observed_index = 2 if (e,l)==(1,0) else 3 if (e,l)==(0,1) else None
        events = r['measurement']['phases'][observed_index or 1]['refresh_provenance']['events']
        result = replay(events,policy,verify_actual=observed_index is not None)
        assert result['deep_calls'] == 38 and result['cache_calls'] == 34
        assert result['S_per_CFG'] == [5+e+l,4+e+l]
        if observed_index is not None:
            assert policy.to_dict() == r['measurement']['phases'][observed_index]['refresh_provenance']['selection_policy']
        arms.append({'name': 'E'+str(e)+'L'+str(l), 'early_S': bool(e), 'late_S': bool(l),
                     'policy': policy.to_dict(), 'source_replay': result,
                     'existing_GPU_phase_index': observed_index,
                     'existing_video_sha256': r['measurement']['phases'][observed_index]['artifacts'][0]['sha256'] if observed_index is not None else None,
                     'new_GPU_result': False})
    assert set(arms[1]['source_replay']['S_calls'])-set(arms[0]['source_replay']['S_calls']) == {23,24}
    assert set(arms[2]['source_replay']['S_calls'])-set(arms[0]['source_replay']['S_calls']) == {55,58}
    assert set(arms[3]['source_replay']['S_calls']) == set(arms[1]['source_replay']['S_calls']) | {55,58}
    return {'status': 'EXPOSED_EARLY_LATE_2X2_SOURCE_CPU_PLAN_TWO_EXISTING_TWO_PENDING_NOT_NEW_VIDEO',
            'CPU_only': True, 'source_raw_sha256': hashlib.sha256(raw).hexdigest(),
            'fixed_mask': r['fixed_mask'], 'common_S_calls': arms[0]['source_replay']['S_calls'],
            'early_S_calls': [23,24], 'late_S_calls': [55,58], 'arms': arms,
            'planned_new_variants': ['E0L0','E1L1'],
            'analysis_targets': {'early_conditional_total_effect': 'D(E1Lx,ref)-D(E0Lx,ref) for x=0,1',
                                 'late_conditional_total_effect': 'D(ExL1,ref)-D(ExL0,ref) for x=0,1',
                                 'interaction': 'D(E1L1,ref)-D(E1L0,ref)-D(E0L1,ref)+D(E0L0,ref)'},
            'GPU_card_selected': False, 'GPU_submitted': False, 'reserved_seconds': 0,
            'online_policy': False, 'causal_refresh_value_labels': False,
            'limits': ['Only topology is computed for the two missing arms; no latent, tensor, video or quality prediction.',
                       'S quotas9/11/11/13 and207/253/253/299 operators intentionally differ; the two factors replace D by S at specific calls.',
                       'Existing first/free11-S swap is matched in nominal count; the 2x2 conditional effects are not a matched-cost frontier claim.',
                       'Signed effects concern the entire fixed-mask intervention including downstream propagation, not isolated immediate or cache-only error.',
                       'Full schedule uses exposed future teacher mask; these are oracle mechanism controls, not online routing or RV0/RV1 labels.']}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('receipt','output','manifest'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=analyze(gzip.decompress(a.receipt.read_bytes()))
    r['analysis_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    r['replay_source_sha256']=hashlib.sha256((Path(__file__).parents[1]/'src/wcomr/forecast_placement.py').read_bytes()).hexdigest()
    a.output.write_text(json.dumps(r,indent=2)+'\n')
    a.manifest.write_text(json.dumps({'role':'EXPOSED_EARLY_LATE_FACTORIAL_DRAFT_NOT_EXECUTION_SELECTION',
        'source_raw_sha256':r['source_raw_sha256'],'fixed_mask':r['fixed_mask'],
        'common_S_calls':r['common_S_calls'],'early_S_calls':r['early_S_calls'],'late_S_calls':r['late_S_calls'],
        'arms':r['arms'],'GPU_card_selected':False,'GPU_submitted':False,'reserved_seconds':0,
        'online_policy':False,'causal_refresh_value_labels':False},indent=2)+'\n')
    print(json.dumps({'status':r['status'],'arms':[{'name':v['name'],'S_calls':v['source_replay']['S_calls'],
        'S_per_CFG':v['source_replay']['S_per_CFG'],'S_operators':v['source_replay']['S_operators'],
        'approximate_cache_calls':v['source_replay']['approximate_cache_calls'],
        'approximate_source_reads':v['source_replay']['approximate_source_reads'],
        'observed':v['existing_GPU_phase_index'] is not None} for v in r['arms']]}))
