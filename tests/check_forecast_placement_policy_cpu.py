"""Pure ordinal and actual source-record corruption controls; no Torch."""
from copy import deepcopy

from wcomr.forecast_placement import replay
from wcomr.selective_refresh_policy import SparsePlacementPolicy, SparseRefreshPolicy


def run(receipt):
    layers=tuple(receipt['policies'][0]['sparse_layers'])
    assert SparseRefreshPolicy(layers,2).to_dict()==receipt['policies'][2]
    checks=['legacy_cadence_metadata_unchanged']
    valid=SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=((1,3),(2,4)))
    assert [valid.select(i,cfg=0) for i in range(1,5)]==[True,False,True,False]
    assert [valid.select(i,cfg=1) for i in range(1,5)]==[False,True,False,True]
    checks.append('distinct_CFG_positions_use_only_passed_ordinal')
    cases={
        'mutable_slots':lambda:SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=[[1],[2]]),
        'boolean_slot':lambda:SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=((True,),(2,))),
        'duplicate_slot':lambda:SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=((1,1),(2,))),
        'unsorted_slot':lambda:SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=((3,1),(2,))),
        'zero_slot':lambda:SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=((0,),(2,))),
        'extra_CFG':lambda:SparsePlacementPolicy(layers,per_cfg_eligible_ordinals=((1,),(2,),(3,))),
        'mixed_cadence':lambda:SparsePlacementPolicy(layers,2,((1,),(2,))),
        'missing_CFG':lambda:valid.select(1),
        'wrong_CFG':lambda:valid.select(1,cfg=2),
        'boolean_CFG':lambda:valid.select(1,cfg=True),
        'negative_counter':lambda:valid.select(-1,cfg=0),
    }
    for name,call in cases.items():
        try:call()
        except ValueError:checks.append('reject_'+name)
        else:raise AssertionError('Invalid explicit placement accepted: '+name)
    events=receipt['measurement']['phases'][3]['refresh_provenance']['events']
    legacy=SparseRefreshPolicy(layers,2)
    replay(events,legacy,verify_actual=True)
    checks.append('actual_legacy_source_topology_reproduced')
    for name in ('future_reference','wrong_source_kind','wrong_CFG_record','missing_reset','incomplete_events'):
        changed=deepcopy(events)
        cache=next(e for e in changed if e['action']=='cache')
        if name=='future_reference':cache['references_read'][-1]['call']=72
        elif name=='wrong_source_kind':cache['references_read'][-1]['kind']='sparse'
        elif name=='wrong_CFG_record':changed[20]['cfg']=1
        elif name=='missing_reset':changed[69]['native_cycle_reset']=False
        else:changed.pop()
        try:replay(changed,legacy,verify_actual=True)
        except (ValueError,AssertionError):checks.append('reject_'+name)
        else:raise AssertionError('Corrupted source topology accepted: '+name)
    return {'status':'EXPLICIT_PLACEMENT_POLICY_AND_ACTUAL_SOURCE_REJECTION_CPU_PASS',
        'CPU_only':True,'checks':checks,'new_GPU_submission':False,'quality_acceptance':False}
