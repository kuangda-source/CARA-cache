#!/usr/bin/env python3
"""Independently reconstruct E2 group selection and all 72 input slots."""
from collections import Counter
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    manifest = root/'manifests/wc_e2_confirmation_full72_inputs_r1_20261011.json'
    value = json.loads(manifest.read_text())
    protocol_path = root/value['protocol_ref']
    report_path = root/value['exposure_report_ref']
    assert sha(protocol_path.read_bytes()) == value['protocol_sha256']
    assert sha(report_path.read_bytes()) == value['exposure_report_sha256']
    protocol = json.loads(protocol_path.read_text())
    exposure = json.loads(report_path.read_text())
    assert not exposure['remote']['read_errors']
    group_audit = json.loads((root/'reports/dataset_source_group_audit_20260930.json').read_text())
    records = {r['name']: r for r in group_audit['records']}
    excluded = set(group_audit['engineering_excluded_groups'])
    excluded.update(r['name'] for r in json.loads((root/'manifests/cal_v1.json').read_text())['cases'])
    excluded.update(exposure['local_identity_hits'])
    excluded.update(exposure['remote']['identity_hits'])
    for name in list(excluded):
        excluded.update(records[name]['group_members'])
    assert sorted(excluded) == value['excluded_observed_and_CAL_group_members']
    representative = {min(r['group_members']) for r in records.values()
                      if not excluded.intersection(r['group_members'])}
    reconstructed = []
    for category in protocol['categories_in_order']:
        names = [name for name in representative if records[name]['category'] == category]
        assert len(names) == value['eligible_pool_counts'][category]
        reconstructed.append(min(names, key=lambda n: sha((protocol['salt']+'|'+n).encode())))
    assert reconstructed == [r['name'] for r in value['selected_sources']]
    requests = [json.loads(line) for line in (root/value['requests_ref']).read_text().splitlines()]
    assert requests == value['requests'] and len(requests) == 8
    assert sha((root/value['requests_ref']).read_bytes()) == value['requests_sha256']
    expected_requests = []
    for seed in protocol['seeds_in_order']:
        for source in value['selected_sources']:
            raw = (root/source['path']).read_bytes()
            assert sha(raw) == source['sha256']
            original = json.loads(raw)
            assert sha(original['prompt'].encode()) == source['prompt_sha256']
            original.update(name=source['name']+'_E2_seed'+str(seed), seed=seed, num_steps=35)
            expected_requests.append(original)
    assert expected_requests == requests
    confirmation = value['confirmation_slots']; timing = value['timing_slots']
    assert [r['slot'] for r in confirmation+timing] == list(range(72))
    assert len(confirmation) == 40 and len(timing) == 32
    for index, request in enumerate(requests):
        block = confirmation[5*index:5*index+5]
        assert [r['method'] for r in block] == protocol['methods_in_order']
        assert all((r['request_name'],r['seed']) == (request['name'],request['seed']) for r in block)
    for scene_index, name in enumerate(protocol['timing_CAL_input_names']):
        block = timing[16*scene_index:16*scene_index+16]
        assert all(r['CAL_name'] == name and r['seed'] == 0 for r in block)
        for round_index, order in enumerate(protocol['timing_orders']):
            rows = block[4*round_index:4*round_index+4]
            assert [r['method'] for r in rows] == order
            assert [r['position'] for r in rows] == [1,2,3,4]
            assert all(r['round'] == round_index+1 for r in rows)
        assert set(Counter(r['method'] for r in block).values()) == {4}
    assert value['co_primary_comparisons'] == [['W1_ONE_PHASE','RA'],['BETA1_ONE_PHASE','RA']]
    assert value['complete_scope'] == {'confirmation_paths':40,'timing_paths':32,
        'complete_paths':72,'maximum_confirmation_fidelity_pairs':32,
        'solver_updates':2592,'CFG_calls':5184}
    assert value['GPU_execution_selected'] is False and value['GPU_submissions'] == 0
    result = {'status':'E2_ACTUAL_FROZEN_INPUTS_FULL72_INDEPENDENT_RECONSTRUCTION_PASS',
              'manifest_sha256':sha(manifest.read_bytes()),
              'audit_script_sha256':sha(Path(__file__).read_bytes()),
              'actual_vendor_inputs_reloaded':4,'complete_requests':8,
              'CAL_and_observed_group_members_excluded':len(excluded),
              'confirmation_slots':40,'balanced_timing_slots':32,
              'co_primary_candidates':2,'seeds':[17,43],
              'local_exposure_files':len(exposure['local_files']),
              'actual_server_receipts':len(exposure['remote']['receipts']),
              'GPU_submissions':0,'clean_sampler_or_GPU_forecast_acceptance':False,
              'recording_or_session_independence_proven':False}
    path = root/'reports/wc_e2_frozen_inputs_independent_audit_r1_20261011.json'
    assert not path.exists()
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
