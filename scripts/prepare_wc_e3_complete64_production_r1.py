"""Bind accepted CPU bytes and unchanged original input/runtime contracts."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    old=json.loads((root/'configs/wc_e1_diag8_production_r2_20261011.json').read_text())
    accepted_ref='reports/wc_e1_diag8_production_cpu_r2_terminal_20261011_capture.json'
    accepted=json.loads((root/accepted_ref).read_text())
    assert accepted['exit_code']==0 and accepted['original_source_actual_entry_contract_and_wrapper_independently_verified']
    scope_ref='manifests/wc_e3_complete64_reuse10_fresh54_blocks_r1_20261011.json'
    scope=json.loads((root/scope_ref).read_text())
    capture_ref='reports/wc_e3_complete64_blocks_cpu_r2_terminal_20261011_capture.json'
    capture=json.loads((root/capture_ref).read_text());assert capture['receipt']['exit_code']==0
    assert capture['original_source_receipts_complete_scope_and_actual_vectors_independently_verified']
    registration_ref='manifests/wc_e3_complete64_blocks_affected_cpu_r2_20261011.json'
    registration=json.loads((root/registration_ref).read_text())
    assert registration['payload_sha256']==capture['receipt']['payload_after_sha256']
    cost_ref='reports/wc_e3_complete64_whole_cost_r1_20261011.json';cost=json.loads((root/cost_ref).read_text())
    new=['src/wcomr/e3_complete64_production_r1.py','scripts/run_wc_e3_complete64_block_r1.py',
        'scripts/check_wc_e3_complete64_production_cpu_r1.py','scripts/supervise_wc_e3_complete64_r1.py',
        'tests/check_e3_complete64_supervisor_cpu_r1.py','scripts/prepare_wc_e3_complete64_production_r1.py',
        'scripts/deploy_wc_e3_complete64_production_cpu_r1.py','scripts/capture_wc_e3_complete64_production_cpu_r1.py',
        'scripts/forecast_wc_e3_complete64_r1.py',cost_ref,capture_ref,registration_ref,accepted_ref,
        accepted['files']['production-CPU-receipt.json']['local_path'],
        'research/319_WC_E3_AFFECTED_CPU_ACCEPTANCE_AND_FULL20_PRODUCTION_PREREGISTRATION_20261011.md']
    new.extend(n for n in registration['payload_sha256'] if n not in old['payload_sha256'])
    new.extend(v['local_path'] for v in capture['files'].values())
    new=list(dict.fromkeys(new));payload=dict(old['payload_sha256'])
    for n,h in registration['payload_sha256'].items():
        assert n not in payload or payload[n]==h,n
    for n in new:
        assert n not in payload,n;payload[n]=sha(root/n)
    assert all(payload[n]==h for n,h in registration['payload_sha256'].items())
    cache=root/'.sync/e3-complete64-production-r1-generated';assert not cache.exists();cache.mkdir()
    request_cache=cache/'e3-complete64-requests.jsonl'
    request_cache.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in scope['requests']))
    payload['e3-complete64-requests.jsonl']=sha(request_cache)
    c={'card':scope['card'],'run_id':scope['run_id'],'requests':scope['requests'],'blocks':scope['blocks'],
        'scope_counts':{'scientific_positions':64,'qualified_reused_positions':10,'fresh_complete_paths':54,
            'independent_model_loads':20,'maximum_paths_per_process':3,'fresh_solver_updates':1944,'fresh_CFG_calls':3888},
        'scope_ref':scope_ref,'scope_sha256':sha(root/scope_ref),
        'parent_stage':old['parent_stage'],'parent_config_sha256':old['parent_config_sha256'],
        'parent_import_source_sha256':old['parent_import_source_sha256'],
        'whole_cost_ref':cost_ref,'whole_cost_sha256':sha(root/cost_ref),
        'forecast_complete_GPUh':cost['forecast_complete_GPUh'],'automatic_single_job_GPUh':8,
        'cumulative_cap_GPUh':77.89524658965853,'authorization_ref':old['authorization_ref'],
        'authorization_sha256':old['authorization_sha256'],'sampling_CPU_capture_ref':capture_ref,
        'sampling_CPU_capture_sha256':sha(root/capture_ref),'sampling_CPU_registration_ref':registration_ref,
        'sampling_CPU_registration_sha256':sha(root/registration_ref),
        'startup_CPU_capture_ref':accepted_ref,'startup_CPU_capture_sha256':sha(root/accepted_ref),
        'state_steps':[12,30,35,36],'checkpoint_reserves':old['checkpoint_reserves'],
        'model_mode_contract_ref':old['model_mode_contract_ref'],'model_mode_contract_sha256':old['model_mode_contract_sha256'],
        'required_stage_assets':old['required_stage_assets'],
        'continue_after_protected_failure':'NEXT_REGISTERED_FRESH_MODEL_PROCESS_ONLY',
        'unexpected_failure':'STOP_RETAIN_ALL64_AND_ALL54_GENERATION_SLOTS',
        'one_complete_GPU_card_not20_independent_cards':True,'empty_cache_or_gate_bypass':False,
        'training':False,'clean_latency_claim':False,'independent_confirmation_claim':False,
        'payload_sha256':payload,'GPU_execution_selected':False,'gpu_uuid':None,
        'production_CPU_receipt_sha256':None,'single_job_exception_authority':None}
    cfg=root/'configs/wc_e3_complete64_production_r1_20261011.json';assert not cfg.exists()
    cfg.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n')
    reg={'identity':'E3_COMPLETE64_FULL20_ACTUAL_PRODUCTION_CPU_PREREGISTERED_NOT_GPU',
        'config_ref':str(cfg.relative_to(root)),'config_sha256':sha(cfg),
        'copies_readonly_sha256':old['payload_sha256'],
        'original_stage':'.sync/wc-e1-diag8-production-cpu-r2-20261011',
        'original_receipt_sha256':accepted['files']['production-CPU-receipt.json']['sha256'],
        'new_local_files':new,'generated_requests_cache':str(request_cache.relative_to(root)),
        'GPU_submissions':0,'ledger_written':False,'scope_counts':c['scope_counts'],
        'forecast_complete_GPUh':c['forecast_complete_GPUh'],
        'all20_actual_entry_guardrail_refusals':True,'four_isolated_supervisor_lifecycle_controls':True,
        'startup_meta_body_and_sampling_CPU_not_rerun':True,'above8_requires_exact_new_approval':True,
        'terminal_per_path_vector_and_all93_scoring_wiring_still_pending':True}
    target=root/'manifests/wc_e3_complete64_production_cpu_r1_preregistration_20261011.json';assert not target.exists()
    target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'payload_files':len(payload),'scope_counts':c['scope_counts'],
        'forecast_complete_GPUh':c['forecast_complete_GPUh'],'GPU_submissions':0}))


if __name__=='__main__':main()
