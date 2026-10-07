#!/usr/bin/env python3
"""Bind the prospective whole onset card and actual repaired core CPU proof."""
import copy
import hashlib
import json
from pathlib import Path


def build(root):
    read = lambda n: json.loads((root/n).read_text())
    sha = lambda n: hashlib.sha256((root/n).read_bytes()).hexdigest()
    base_ref = 'configs/wc_w3_native_tail_response_selected_20261007.json'
    base = read(base_ref)
    prereg_ref = 'manifests/wc_w3_native_response_onset_r1_preregistration_20261007.json'
    prereg = read(prereg_ref)
    core_manifest_ref = 'manifests/wc_w3_native_response_onset_core_cpu_r2_20261007.json'
    core_manifest = read(core_manifest_ref)
    core_ref = 'reports/wc_w3_native_response_onset_core_cpu_r2_native_20261007.json'
    core = read(core_ref)
    core_audit = 'reports/wc_w3_native_response_onset_core_cpu_r2_audit_20261007.json'
    audit = read(core_audit)
    assert audit['server_receipt_sha256'] == sha(core_ref)
    assert core['status'] == 'NATIVE_RESPONSE_ONSET_ACTUAL_AFFECTED_CORE_CPU_PASS_NOT_PRODUCTION_OR_GPU'
    assert audit['all3_raw_rows_and60_refusals_checked'] is True
    core_payload = audit['core_payload_sha256']
    assert all(sha(n) == d for n,d in core_payload.items())
    scope = copy.deepcopy(core_manifest['scope'])
    references = {k:copy.deepcopy(base['references']['human_199'][k])
                  for k in ('timesteps','model_and_condition_context')}
    references.update(copy.deepcopy(prereg['historical_encoded_references']))
    cost_ref = 'reports/wc_w3_native_response_onset_complete_cost_20261007.json'
    assert not (root/cost_ref).exists()
    (root/cost_ref).write_text(json.dumps(prereg['cost_forecast'],indent=2)+'\n')
    prior_score = prereg['trigger_evidence']['prior_score_ref']
    prior_GPU = 'reports/wc_w3_native_tail_response_runner_terminal_native_20261007.json.gz'
    extra = [
        'src/wcomr/rv0_native_onset_execution.py','src/wcomr/rv0_native_onset_scores.py',
        'scripts/run_wc_w3_native_response_onset.py','scripts/supervise_wc_w3_native_response_onset.py',
        'scripts/audit_wc_w3_native_response_onset_terminal.py','scripts/analyze_wc_w3_native_response_onset_lpips_cpu.py',
        'scripts/build_wc_w3_native_onset_production_draft.py','tests/check_rv0_native_onset_production_cpu.py',
        prereg_ref,core_ref,core_audit,cost_ref,prior_score,prior_GPU,core_manifest_ref,
        'plans/WORLD_CACHE_NATIVE_RESPONSE_ONSET_WINDOW_20261007.md']
    # Copy the actually checked source tree; the old alias is not needed by the
    # unchanged R2 dependency validator. The new configuration has its own alias.
    base_payload = {**core_manifest['base_payload_sha256'],**core_manifest['new_payload_sha256']}
    base_payload.pop('tail-config.json')
    assert len(extra)==len(set(extra)) and set(extra).isdisjoint(base_payload)
    payload = {**base_payload,**{n:sha(n) for n in extra}}
    placement_ref = 'configs/wc_w3_placement_tail_v2_approved_r1_20261007.json'
    assert sha(placement_ref) == payload['placement-config.json']
    config = {'card':prereg['card'],'run_id':prereg['run_id'],'sample_indices':[2],'sample_names':['human_199'],
        'scope':scope,'preregistration':prereg,'preregistration_ref':prereg_ref,'preregistration_sha256':sha(prereg_ref),
        'expected_project_root':base['expected_project_root'],'execution_limits':base['execution_limits'],
        'logical_copy_cap_bytes':6*1024**3,'workspace_reserve_bytes':4*1024**3,
        'historical_wc_settings':base['historical_wc_settings'],'f1_setup_sha256':base['f1_setup_sha256'],
        'references':{'human_199':references},'payload_sha256':payload,
        'base_config_sha256':sha(placement_ref),'base_stage':core_manifest['stage'],
        'core_cpu_stage':core_manifest['stage'],'core_cpu_receipt_sha256':sha(core_ref),
        'core_cpu_attempts_sha256':core['attempts_sha256'],'core_cpu_payload_sha256':core_payload,
        'core_cpu_audit_ref':core_audit,'core_cpu_audit_sha256':sha(core_audit),
        'lpips_resource_stage':base['lpips_resource_stage'],
        'prior_score_ref':prior_score,'prior_score_sha256':sha(prior_score),
        'prior_GPU_receipt_ref':prior_GPU,'prior_GPU_receipt_sha256':sha(prior_GPU),
        'cost':prereg['cost_forecast'],'cost_ref':cost_ref,'cost_sha256':sha(cost_ref),
        'execution_policy_authority':base['execution_policy_authority'],'execution_scope_authority':None,
        'GPU_execution_selected':False,'gpu_uuid':None,'production_entry_ready':True,
        'production_CPU_validation':'NEW_ACTUAL_PRODUCTION_CHECK_PENDING'}
    path = 'configs/wc_w3_native_response_onset_production_draft_20261007.json'
    assert not (root/path).exists();(root/path).write_text(json.dumps(config,indent=2)+'\n')
    mappings = {n:n for n in extra};mappings['onset-config.json']=path
    manifest = {'identity':'WC_W3_NATIVE_ONSET_PRODUCTION_CPU_R1_20261007',
        'stage':'.sync/wc-w3-native-response-onset-production-cpu-r1-20261007',
        'base_stage':core_manifest['stage'],'base_payload_sha256':base_payload,
        'new_source_by_stage_path':mappings,'new_payload_sha256':{n:sha(p) for n,p in mappings.items()},
        'all_payload_sha256':{**payload,'onset-config.json':sha(path)},
        'upstream_source_sha256':core_manifest['upstream_source_sha256'],'budget_sha256':sha('reports/budget.json'),
        'affected_contract_test':'tests/check_rv0_native_onset_production_cpu.py',
        'old_Toy_or_new_Toy_rerun':False,'actual_affected_core_passed':True,'GPU_submissions':0}
    out = root/'manifests/wc_w3_native_response_onset_production_cpu_r1_20261007.json'
    assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n')
    return {'status':'NATIVE_RESPONSE_ONSET_COMPLETE_PRODUCTION_DRAFT_BOUND_NOT_GPU',
        'scope_counts':[1,10,6,2],'stage_files':len(manifest['all_payload_sha256']),
        'planning_GPUh':prereg['cost_forecast']['complete_forecast_gpu_hours'],'GPU_selected':False}


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    print(json.dumps(build(p.parse_args().root)))
