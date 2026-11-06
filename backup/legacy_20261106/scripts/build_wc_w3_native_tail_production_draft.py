#!/usr/bin/env python3
"""Bind the complete native-tail preregistration and actual affected CPU proof."""
import copy
import hashlib
import json
from pathlib import Path


def build(root):
    read = lambda n:json.loads((root/n).read_text())
    sha = lambda n:hashlib.sha256((root/n).read_bytes()).hexdigest()
    base_ref = 'configs/wc_w3_placement_tail_v2_approved_r1_20261007.json'
    base = read(base_ref)
    prereg_ref = 'manifests/wc_w3_native_tail_response_r1_preregistration_20261007.json'
    prereg = read(prereg_ref)
    core_manifest = read('manifests/wc_w3_native_tail_response_core_cpu_r1_20261007.json')
    core_ref = 'reports/wc_w3_native_tail_response_core_cpu_r1_native_20261007.json'
    core = read(core_ref)
    core_audit = 'reports/wc_w3_native_tail_response_core_cpu_r1_audit_20261007.json'
    assert read(core_audit)['server_receipt_sha256'] == sha(core_ref)
    assert core['status'] == 'NATIVE_TAIL_ACTUAL_AFFECTED_CORE_CPU_PASS_NOT_PRODUCTION_OR_GPU'
    scope = {'card':prereg['card'], 'run_id':prereg['run_id'], 'scope_counts':[1,10,6,2],
        'scenes':[{'scene':'human_199','sample_index':2,'parent_action_mask':prereg['parent_action_mask'],
            'parent_mask_sha256':prereg['parent_mask_sha256'],'parent_full_counts_per_CFG':[20,18],
            'cases':prereg['cases']}], 'maximum_age_solver_steps':33,
        'order':prereg['order'], 'encoded':prereg['encoded'], 'responsive_calls_only':[69,70]}
    references = copy.deepcopy(base['references']['human_199'])
    references.update(copy.deepcopy(prereg['references']))
    cost_ref = 'reports/wc_w3_native_tail_response_complete_cost_20261007.json'
    assert not (root/cost_ref).exists()
    (root/cost_ref).write_text(json.dumps(prereg['cost_proxy'],indent=2)+'\n')
    prior_score = 'reports/wc_w3_placement_tail_v2_lpips_score_native_20261007.json'
    prior_GPU = 'reports/wc_w3_placement_tail_v2_runner_terminal_native_20261007.json.gz'
    extra = list(core_manifest['new_payload_sha256'])+[
        'src/wcomr/rv0_native_tail_execution.py','src/wcomr/rv0_native_tail_scores.py',
        'scripts/run_wc_w3_native_tail_response.py','scripts/supervise_wc_w3_native_tail_response.py',
        'scripts/audit_wc_w3_native_tail_response_terminal.py','scripts/analyze_wc_w3_native_tail_response_lpips_cpu.py',
        'scripts/build_wc_w3_native_tail_production_draft.py','tests/check_rv0_native_tail_production_cpu.py',
        prereg_ref,core_ref,core_audit,cost_ref,prior_score,prior_GPU,
        'manifests/wc_w3_native_tail_response_core_cpu_r1_20261007.json',
        'plans/WORLD_CACHE_POST_PLACEMENT_WINDOW_20261007.md']
    assert len(extra)==len(set(extra)) and set(extra).isdisjoint(base['payload_sha256'])
    payload = {**base['payload_sha256'], **{n:sha(n) for n in extra}, 'placement-config.json':sha(base_ref)}
    config = {'card':prereg['card'],'run_id':prereg['run_id'],'sample_indices':[2],'sample_names':['human_199'],
        'scope':scope,'preregistration':prereg,'preregistration_ref':prereg_ref,'preregistration_sha256':sha(prereg_ref),
        'expected_project_root':base['expected_project_root'], 'execution_limits':base['execution_limits'],
        'logical_copy_cap_bytes':6*1024**3,'workspace_reserve_bytes':4*1024**3,
        'historical_wc_settings':base['historical_wc_settings'],'f1_setup_sha256':base['f1_setup_sha256'],
        'references':{'human_199':references},'payload_sha256':payload,
        'base_config_sha256':sha(base_ref),'base_stage':core_manifest['base_stage'],
        'core_cpu_stage':core_manifest['stage'],'core_cpu_receipt_sha256':sha(core_ref),
        'core_cpu_attempts_sha256':core['attempts_sha256'],'core_cpu_payload_sha256':core_manifest['new_payload_sha256'],
        'core_cpu_audit_ref':core_audit,'core_cpu_audit_sha256':sha(core_audit),
        'lpips_resource_stage':base['lpips_resource_stage'],
        'prior_score_ref':prior_score,'prior_score_sha256':sha(prior_score),
        'prior_GPU_receipt_ref':prior_GPU,'prior_GPU_receipt_sha256':sha(prior_GPU),
        'cost':prereg['cost_proxy'],'cost_ref':cost_ref,'cost_sha256':sha(cost_ref),
        'execution_policy_authority':base['execution_policy_authority'],'execution_scope_authority':None,
        'GPU_execution_selected':False,'gpu_uuid':None,'production_entry_ready':True,
        'production_CPU_validation':'NEW_ACTUAL_PRODUCTION_CHECK_PENDING'}
    path = 'configs/wc_w3_native_tail_response_production_draft_20261007.json'
    assert not (root/path).exists(); (root/path).write_text(json.dumps(config,indent=2)+'\n')
    mappings = {n:n for n in extra}
    mappings.update({'placement-config.json':base_ref,'tail-config.json':path})
    manifest = {'identity':'WC_W3_NATIVE_TAIL_PRODUCTION_CPU_R1_20261007',
        'stage':'.sync/wc-w3-native-tail-response-production-cpu-r1-20261007',
        'base_stage':core_manifest['base_stage'],'base_payload_sha256':base['payload_sha256'],
        'new_source_by_stage_path':mappings,
        'new_payload_sha256':{n:sha(p) for n,p in mappings.items()},
        'all_payload_sha256':{**payload,'tail-config.json':sha(path)},
        'upstream_source_sha256':base['upstream_source_sha256'], 'budget_sha256':sha('reports/budget.json'),
        'affected_contract_test':'tests/check_rv0_native_tail_production_cpu.py',
        'old_Toy_or_new_Toy_rerun':False,'actual_affected_core_passed':True,'GPU_submissions':0}
    out = root/'manifests/wc_w3_native_tail_response_production_cpu_r1_20261007.json'
    assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n')
    return {'status':'NATIVE_TAIL_COMPLETE_PRODUCTION_DRAFT_BOUND_NOT_GPU',
        'scope_counts':[1,10,6,2],'stage_files':len(manifest['all_payload_sha256']),
        'planning_GPUh':prereg['cost_proxy']['complete_planning_proxy_GPUh'],'GPU_selected':False}


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    print(json.dumps(build(p.parse_args().root)))
