#!/usr/bin/env python3
"""Bind the preregistered R2 core/raw recovery to a full unselected job."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def build(root):
    read=lambda p:json.loads((root/p).read_text())
    sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
    base=read('configs/wc_w3_placement_approved_r1_20261007.json')
    core_manifest=read('manifests/wc_w3_placement_tail_core_cpu_r1_20261007.json')
    core=read('reports/wc_w3_placement_tail_core_cpu_r1_supervisor_native_20261007.json')
    audit=read('reports/wc_w3_placement_tail_core_cpu_r1_raw_audit_20261007.json')
    config=copy.deepcopy(base)
    frozen='configs/wc_w3_placement_tail_aligned_r2_scope_draft_20261007.json'
    registered=read(frozen)
    config['scope']=copy.deepcopy(registered['scope'])
    assert audit['status']=='R2_CORE_FROZEN_RAW_TRACE_CPU_AUDIT_PASS_ORIGINAL_SUMMARY_FAILURE_RETAINED'
    assert core['exit_code']==1 and core['native_before']==core['native_after']
    assert core['base_payload_sha256']==core['base_payload_after_sha256']
    budget_archive='reports/wc_w3_placement_tail_cost_budget_archive_20261007.json'
    assert not (root/budget_archive).exists()
    (root/budget_archive).write_bytes((root/'reports/budget.json').read_bytes())
    r1=read('reports/wc_w3_placement_failed_supervisor_native_20261007.json')
    # Retain the complete C/D-derived estimate; partial R1 cannot certify a
    # smaller complete job. Both are diagnosis costs, not deployment speed.
    cost=copy.deepcopy(base['cost'])
    for key in ['proposed_total_cap_seconds','proposed_child_cap_seconds','proposed_kill_grace_seconds']:
        cost.pop(key,None)
    cost.update(status='R2_COMPLETE_SCOPE_COST_PROXY_PRIOR_FULL_CD_AND_PARTIAL_R1_NOT_HARD_BOUND',
        partial_R1_actual_wall_seconds=r1['wall_seconds'],partial_R1_original_exit_code=1,
        partial_R1_complete_suffix_seconds=[349.3963131243363,320.85236207116395,320.8564918227494],
        partial_R1_incomplete_swap_seconds=293.7495699459687,
        complete_nominal_proxy_seconds=max(cost['complete_nominal_proxy_seconds'],
            cost['measured_two_parent_CD_inclusive_seconds']+4*349.3963131243363
            +2*cost['max_observed_child_decode_guardrail_encode_seconds']+cost['single_startup_and_flush_proxy_seconds']),
        current_remaining_GPU_seconds=(24-read(budget_archive)['used_gpu_hours'])*3600,
        GPU_execution_selected=False,GPU_submissions=0,scope_authority=None,production_entry_ready=True,
        legacy_per_card_seconds_deadline=False)
    cost['complete_planning_proxy_seconds']=1.2*cost['complete_nominal_proxy_seconds']+30
    cost['arithmetic_fits_current_24h_budget']=cost['complete_planning_proxy_seconds']+30<cost['current_remaining_GPU_seconds']
    cost['source_sha256']=copy.deepcopy(base['cost']['source_sha256'])
    cost['source_sha256']['reports/budget.json']=sha(budget_archive)
    cost['source_sha256'].update({name:sha(name) for name in [
        'reports/wc_w3_placement_failed_supervisor_native_20261007.json',
        'reports/wc_w3_placement_failed_runner_native_20261007.json.gz',
        'reports/wc_w3_placement_failed_cpu_audit_20261007.json']})
    cost_path='reports/wc_w3_placement_tail_v2_complete_cost_20261007.json'
    assert not (root/cost_path).exists();(root/cost_path).write_text(json.dumps(cost,indent=2)+'\n')
    payload=copy.deepcopy(base['payload_sha256'])
    extra=[
        'src/wcomr/rv0_fixed_mask_v2.py','src/wcomr/rv0_placement_v2_scope.py',
        'src/wcomr/rv0_placement_v2_causal.py','src/wcomr/rv0_placement_v2_evaluation.py',
        'src/wcomr/rv0_placement_v2_execution.py',
        'scripts/run_wc_w3_placement_tail_v2.py','scripts/supervise_wc_w3_placement_tail_v2.py',
        'scripts/audit_wc_w3_placement_tail_v2_terminal.py','scripts/analyze_wc_w3_placement_tail_v2_lpips_cpu.py',
        'scripts/build_wc_w3_placement_tail_v2_production_draft.py',
        'tests/check_rv0_placement_tail_v2_production_cpu.py','tests/check_rv0_placement_tail_v2_cpu.py',
        'scripts/check_wc_w3_placement_tail_v2_core_cpu.py','scripts/audit_wc_w3_placement_tail_core_raw_cpu.py',
        'manifests/wc_w3_placement_tail_alignment_r2_preregistered_20261007.json',
        'manifests/wc_w3_placement_tail_core_cpu_r1_20261007.json',
        'plans/WORLD_CACHE_PLACEMENT_TAIL_ALIGNMENT_20261007.md',frozen,
        'reports/wc_w3_placement_tail_core_cpu_r1_raw_audit_20261007.json',
        'reports/wc_w3_placement_tail_core_cpu_r1_supervisor_native_20261007.json',
        'reports/wc_w3_placement_tail_core_cpu_r1_attempts_native_20261007.json.gz',
        'reports/wc_w3_placement_tail_core_cpu_r1_log_native_20261007.txt',
        'reports/wc_w3_placement_failed_supervisor_native_20261007.json',
        'reports/wc_w3_placement_failed_runner_native_20261007.json.gz',
        'reports/wc_w3_placement_failed_cpu_audit_20261007.json',budget_archive,cost_path]
    assert set(extra).isdisjoint(payload)
    payload.update({name:sha(name) for name in extra})
    payload['tail-scope.json']=sha(frozen)
    config.update(card=registered['card'],run_id=registered['run_id'],payload_sha256=payload,
        preregistered_scope_sha256=sha(frozen),cost=cost,cost_report_ref=cost_path,
        cost_report_sha256=sha(cost_path),cost_budget_archive=budget_archive,
        tail_core_stage=core_manifest['stage'],tail_core_receipt_sha256=sha('reports/wc_w3_placement_tail_core_cpu_r1_supervisor_native_20261007.json'),
        tail_core_attempts_sha256=core['attempts_sha256'],tail_core_payload_sha256=core['new_payload_sha256'],
        GPU_execution_selected=False,gpu_uuid=None,execution_scope_authority=None,
        production_entry_ready=True,production_CPU_validation='AFFECTED_PRODUCTION_VALIDATION_PENDING',
        scientific_choice_status='PROSPECTIVE_R2_FIXED_EXECUTED_TAIL_ORIGINAL_R1_FAILURE_PRESERVED',
        note='Complete 2/16/10/4 retained. Distinct R2 run; original R1 exception consumed. CPU raw recovery retains exit1 count failure.')
    for key in ['production_cpu_stage','production_cpu_receipt_sha256','production_cpu_payload_sha256']:
        config.pop(key,None)
    config['preparation_audits']['tail_core']={'path':'reports/wc_w3_placement_tail_core_cpu_r1_raw_audit_20261007.json',
        'sha256':sha('reports/wc_w3_placement_tail_core_cpu_r1_raw_audit_20261007.json')}
    config_path='configs/wc_w3_placement_tail_v2_production_r1_draft_20261007.json'
    manifest_path='manifests/wc_w3_placement_tail_v2_production_cpu_r1_20261007.json'
    assert not (root/config_path).exists() and not (root/manifest_path).exists()
    (root/config_path).write_text(json.dumps(config,indent=2)+'\n')
    mappings={name:name for name in extra}
    mappings.update({'tail-scope.json':frozen,'placement-config.json':config_path})
    manifest={'identity':'WC_W3_PLACEMENT_TAIL_V2_PRODUCTION_CPU_R1_20261007',
        'stage':'.sync/wc-w3-placement-tail-production-cpu-r1-20261007','base_stage':'.sync/wc-w3-placement-approved-r1-20261007',
        'base_payload_sha256':base['payload_sha256'],
        'new_payload_sha256':{**{n:payload[n] for n in payload if n not in base['payload_sha256']},'placement-config.json':sha(config_path)},
        'new_source_by_stage_path':mappings,'upstream_source_sha256':config['upstream_source_sha256'],
        'budget_sha256':sha('reports/budget.json'),'GPU_execution_selected':False,'GPU_submissions':0,
        'affected_contract_test':'tests/check_rv0_placement_tail_v2_production_cpu.py',
        'full_CPU_Toy_sampling_rerun':False,'unchanged_score_and_LPIPS_resource_checks_reused':True}
    assert set(manifest['new_payload_sha256'])==set(mappings)
    (root/manifest_path).write_text(json.dumps(manifest,indent=2)+'\n')
    return {'stage_files':len(payload)+1,'full_job_nominal_GPUh':cost['complete_nominal_proxy_seconds']/3600,
        'full_job_planning_GPUh':cost['complete_planning_proxy_seconds']/3600,'GPU_selected':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    print(json.dumps(build(parser.parse_args().root)))
