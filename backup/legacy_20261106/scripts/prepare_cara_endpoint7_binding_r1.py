"""Materialize the selected E1 production interfaces, without authority or remote I/O."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src')]
from wcomr.cara_endpoint7_binding_r1 import proposal,bind
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_budget_host_policy_r1 import POLICY_SHA256

def read(f):return json.loads((ROOT/f).read_text())
def write(f,v):(ROOT/f).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
    selected=read('plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json')
    choice=read('plans/cara_next_stage_20261101/e1/USER_SCOPE_SELECTION_R1.json')
    assert choice['scope_sha256']==selected['scope_sha256'] and choice['selected_physical_paths']==46
    origin='plans/cara_next_stage_20261028/mainline/r2/BUDGET_SUCCESSOR14_FROZEN_MASK_R1_20261101.json'
    raw=(ROOT/origin).read_bytes();frozen=json.loads(raw)
    accepted=read('reports/cara_budget_successor_complete_accepted_r1_20261101.json')
    captured=read('reports/cara_budget_successor_final_CPU_capture_r4_20261101.json')['result']
    assert raw==captured['frozen']['raw_utf8'].encode() and hashlib.sha256(raw).hexdigest()==captured['frozen']['sha256']==accepted['freeze_sha256']
    p=proposal(selected,read('plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json'))
    b=bind(p,accepted,frozen,accepted['freeze_sha256'])
    card=request_card(p,b,load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json'))
    assert card['physical_matrix']==selected['physical_matrix']
    for role in {s['role'] for s in card['physical_matrix']}:assert card['roles'][role]==selected['roles'][role]
    write('configs/cara_endpoint_proposal.json',p);write('configs/cara_endpoint_frozen_binding.json',b)
    write('configs/cara_endpoint_request_card.json',card)
    profile=read('plans/cara_next_stage_20261028/mainline/r2/BUDGET_CONTAINER_PROFILE_R1.json')
    profile.update(schema='CARA_ENDPOINT_CONTAINER_PROFILE_R1',scope_sha256=card['scope_sha256'],
        endpoint_binding_sha256=b['binding_sha256'],hard_GPUh=7.,physical_paths=46,new_scoring_pairs=16)
    profile['hosts']={'two_card':profile['hosts']['two_card']};profile.pop('candidate_queries')
    profile.update(endpoint7=True,design_ref='plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json')
    profile['storage'].update(minimum_output_free_bytes=8*2**30,minimum_host_free_bytes=16*2**30,minimum_host_free_before_provision_bytes=80*2**30)
    write('configs/cara_endpoint_container_profile.json',profile)
    engineering=read('plans/cara_next_stage_20261101/e1/ENDPOINT7_46_QUOTE_R1.json')
    costs=engineering['components_seconds']
    components=dict(generation=costs['generation_at_slowest_old_Native'],
        path_artifacts=costs['artifact_copy_save_hash']+costs['producer_readback'],
        admission_and_model_load=costs['admission_and_model_load'],stop_and_release=costs['stop_and_release'])
    assert abs(sum(components.values())/3600-engineering['forecast_GPUh'])<1e-12
    write('configs/cara_endpoint_whole_quote.json',dict(whole_quote_accepted=True,
        scope_sha256=card['scope_sha256'],endpoint_binding_sha256=b['binding_sha256'],
        execution_host_policy_sha256=POLICY_SHA256,
        host_quotes={'two_card':dict(physical_paths=46,new_scoring_pairs=16,hard_GPUh=7.,
            forecast_GPUh=engineering['forecast_GPUh'],components_seconds=components,
            original_component_detail_seconds=costs,
            evidence_refs=['plans/cara_next_stage_20261101/e1/ENDPOINT7_46_QUOTE_R1.json'])},
        engineering_quote_only=True,GPU_authorized=False,fresh_admission=False))
    # Reuse the exact original bytes, not a reserialized or recalculated score set.
    (ROOT/'configs/cara_endpoint_original_B36_scores.json').write_bytes((ROOT/'reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json').read_bytes())
    print('Selected46 physical rows and every executed role exactly match accepted CPU scope; raw original score bytes reused')
if __name__=='__main__':main()
