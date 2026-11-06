#!/usr/bin/env python3
"""Reconstruct all eligible rankings, reserved groups, and eight input requests."""
import hashlib,json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


if __name__=='__main__':
    manifest=R/'manifests/wc_source_conditional_confirmation_inputs_r1_20261013.json';m=json.loads(manifest.read_text())
    protocol=R/m['protocol_ref'];p=json.loads(protocol.read_text());exposure=R/m['exposure_report_ref'];e=json.loads(exposure.read_text())
    assert sha(protocol)==m['protocol_sha256']==e['protocol_sha256'] and sha(exposure)==m['exposure_report_sha256']
    assert e['remote']['no_endpoint_or_timing_values_extracted'] and not e['remote']['read_errors']
    for n,h in p['frozen_sources'].items():assert sha(R/n)==h
    records=json.loads((R/'reports/dataset_source_group_audit_20260930.json').read_text());lookup={r['name']:r for r in records['records']}
    old=json.loads((R/p['original_E2_inputs_ref']).read_text());reserved={r['name'] for r in old['selected_sources']}
    assert reserved==set(m['reserved_original_E2_names'])
    excluded=set(records['engineering_excluded_groups'])|reserved|set(e['local_identity_hits'])|set(e['remote']['identity_hits'])
    excluded.update(r['name'] for r in json.loads((R/'manifests/cal_v1.json').read_text())['cases'])
    full=set(excluded)
    for name in excluded:full.update(lookup[name]['group_members'])
    assert full==set(m['excluded_observed_CAL_and_reserved_E2_group_members'])
    groups={tuple(r['group_members']) for r in records['records'] if not full.intersection(r['group_members'])}
    eligible=[lookup[min(group)] for group in groups]
    winners=[];pools={}
    for category in p['categories_in_order']:
        pool=sorted((r['name'] for r in eligible if r['category']==category),key=lambda n:hashlib.sha256((p['salt']+'|'+n).encode()).hexdigest())
        assert pool;winners.append(pool[0]);pools[category]=len(pool)
    assert winners==[r['name'] for r in m['selected_sources']] and pools==m['eligible_pool_counts']
    expected=[]
    for seed in p['seeds_in_order']:
        for s in m['selected_sources']:
            assert sha(R/s['path'])==s['sha256'] and not full.intersection(s['group_members'])
            r=json.loads((R/s['path']).read_text());assert hashlib.sha256(r['prompt'].encode()).hexdigest()==s['prompt_sha256']
            r.update(name=s['name']+'_SOURCECONF_seed'+str(seed),seed=seed,num_steps=35);expected.append(r)
    requests=R/m['requests_ref'];assert sha(requests)==m['requests_sha256']
    assert expected==m['requests']==[json.loads(line) for line in requests.read_text().splitlines()]
    assert len(expected)==8 and len({r['name'] for r in expected})==8
    assert m['methods']==['NATIVE','RA','A_NO_P','P_OFF','NEW_CANDIDATE_PENDING_FREEZE'] and m['method_positions']==40 and m['warmups_planned']==10
    assert not m['candidate_frozen'] and not m['production_CPU_accepted'] and not m['GPU_execution_selected'] and not m['GPU_submissions']
    result={'status':'SOURCECONF_FOUR_PROMPT_EIGHT_REQUEST_RANK_RESERVED_E2_EXPOSURE_CPU_RECONSTRUCTION_PASS',
        'manifest_sha256':sha(manifest),'protocol_sha256':sha(protocol),'exposure_sha256':sha(exposure),
        'selected_base_names':winners,'eligible_pools':pools,'remote_receipts':len(e['remote']['receipts']),
        'original_E2_reserved_four_groups_disjoint':True,'requests':8,'planned_method_positions':40,'planned_warmups':10,
        'candidate_and_production_and_cost_pending':True,'GPU_submissions':0,'ledger_written':False}
    dest=R/'reports/wc_source_conditional_confirmation_input_independent_audit_20261013.json';assert not dest.exists()
    dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
