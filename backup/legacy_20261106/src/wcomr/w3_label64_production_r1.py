"""Read-only actual H1 assets plus separately frozen eight W3 requests."""
import gzip
import json
from pathlib import Path

from .w3_label64_production_contract_r1 import *
from .p_acr_profile528_production_r1 import validate as original_H1_resources,write,MODE_REF

CPU_STATUS='W3_LABEL64_FULL18_ACTUAL_PRODUCTION_CPU_ACCEPTED'
COLLECTOR_PROOF='reports/wc_w3_label64_h1_collector_CPU_r3_independent_acceptance_20261015.json'
COST='manifests/wc_w3_label64_full864_provisional_cost_r1_20261015.json'


def validate_assets(project,stage):
    project,stage=Path(project),Path(stage)
    base_config,reg,old,original_inputs,values=original_H1_resources(project,stage)
    scope,inputs,requests,plan=local_inputs(stage)
    for name,digest in scope['clock_sources'].items():
        if sha(stage/name)!=digest:raise ValueError('Actual frozen W3 clock/H1 source changed')
    proof=json.loads((stage/COLLECTOR_PROOF).read_text())
    if (proof['status']!='W3_FULL72_288_ORIGINS3456_PAIRS_INDEPENDENT_CPU_ACCEPTED_NOT_REAL_LABELS'
            or proof['full_CPU_paths']!=72 or proof['origins']!=288 or proof['complete_pairs']!=3456
            or proof['extra_pairs']!=864 or proof['GPU_submissions'] or proof['real_teacher_labels']
            or not proof['all36_parent_guided_actions_Ahistory_final_mock_equal']):
        raise ValueError('Complete accepted W3 collector CPU required before production closure')
    capture_path=stage/proof['capture_ref']
    if sha(capture_path)!=proof['capture_sha256']:raise ValueError('Original W3 collector capture changed')
    capture=json.loads(gzip.decompress(capture_path.read_bytes()))['capture']
    result=capture['result'];numeric=result['jobs'][0]['result']
    if (result['status']!='W3_LABEL64_FULL_H1_CPU_BUNDLE_ACCEPTED_NOT_GPU_READY'
            or numeric['original_support_guard_tests']!=3 or numeric['exact_native_cycle_guard_tests']!=2):
        raise ValueError('Original complete sampler and exact support/cycle CPU guards required')
    for name,digest in numeric['payload_sha256'].items():
        if name.startswith('src/wcomr/') and reg['payload_sha256'].get(name)!=digest:
            raise ValueError('W3/H1 physical core differs from full72 numerical CPU: '+name)
    clock=json.loads((stage/CLOCK).read_text())['result']
    from .w3_actual_clock_replay_r1 import validate_clock
    validate_clock(clock)
    cost=json.loads((stage/COST).read_text())
    if (cost['scope_sha256']!=sha(stage/SCOPE) or cost['full_paths']!=18
            or cost['complete_pairs_maximum']!=864 or cost['GPU_submissions']):
        raise ValueError('Complete whole W3 cost draft/source binding changed')
    return scope,reg,base_config,old,original_inputs,values,requests,plan,proof,cost
