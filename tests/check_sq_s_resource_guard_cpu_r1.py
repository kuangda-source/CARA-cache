"""Affected-path composition: unchanged complete physical matrices plus guard."""
import json
from pathlib import Path
from unittest.mock import patch

from wcomr.sq_s_resource_guard_r1 import ResourceCheckedRequests

ROOT=Path(__file__).resolve().parents[1]


def run(runtime,artifacts,tiny_loader,host,retained):
    import check_sq_s_physical_cpu_r1 as original
    from wcomr import sq_s_collection_r1 as collection
    contract=json.loads((ROOT/'plans/cara_next_stage_20261028/sq/S_RESOURCE_GUARD_CPU_CONTRACT_R1.json').read_text())
    instances=[];entry_before=collection.execute
    class GuardedRequests(ResourceCheckedRequests):
        def __init__(self,**kwargs):
            super().__init__(resource_contract=contract,**kwargs)
            instances.append(self)
    with patch.object(original,'Requests',GuardedRequests):
        fixture=original.run(runtime,artifacts,tiny_loader,host,retained)
    assert collection.execute is entry_before
    instance_width=2 if host=='two_card' else 1
    assert len(instances)==2*instance_width and len(fixture['checks'])==2
    for i,row in enumerate(fixture['checks']):
        current=instances[i*instance_width:(i+1)*instance_width]
        if host=='two_card':assert len(current[0].resource_checks)==0
        active=current[-1];records=active.resource_checks
        expected=[dict(slot_id=slot['id'],prompt=slot['prompt'],parent=slot['parent'],step=step)
            for slot in active.scope['slots'] if slot['enabled']
            for step in range(8,36) if step!=24]
        assert [{k:r[k] for k in ('slot_id','prompt','parent','step')} for r in records]==expected
        assert len(records)==108 and all(r['all_eight_groups_checked']
            and r['contract_sha256']==contract['contract_sha256']
            and not r['tensor_values_read'] and r['tensor_copies_performed']==0
            and r['GPU_admission'] is False for r in records)
        row['resource_entry']=dict(status='ALL108_PRE_SNAPSHOT_GUARDS_PASS_CPU_FIXTURE',
            contract_sha256=contract['contract_sha256'],requests_including_source=len(current),
            source_OFF_resource_checks=0,records=records,original_collection_entry_restored=True,
            original_numerical_collector_and_physical_matrix_unchanged=True)
    return fixture
