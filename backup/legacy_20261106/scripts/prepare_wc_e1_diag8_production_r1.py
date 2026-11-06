"""Freeze actual E1 source/input contract after complete CPU acceptance."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    ref='reports/wc_e1_diag8_sampling_cpu_r1_terminal_20261011_capture.json'
    proof=json.loads((root/ref).read_text());assert proof['exit_code']==0 and proof['original_source_and_full_scope_independently_verified']
    old=json.loads(gzip.decompress((root/proof['files']['registration.json']['local_path']).read_bytes()))
    scope_ref='manifests/wc_e1_cold_prefix_memory_diag8_r1_20261011.json'
    scope=json.loads((root/scope_ref).read_text())
    parent_ref='configs/wc_current_birth_full64_selected_r1_20261010.json';parent=json.loads((root/parent_ref).read_text())
    authority='manifests/wc_current_window_execution_authorization_20261011_8gpuh.json'
    new=['src/wcomr/e1_diag8_production_r1.py','scripts/run_wc_e1_diag8_r1.py',
        'scripts/check_wc_e1_diag8_production_cpu_r1.py','scripts/supervise_wc_e1_diag8_r1.py',
        'scripts/prepare_wc_e1_diag8_production_r1.py','scripts/deploy_wc_e1_diag8_production_cpu_r1.py',
        'scripts/select_wc_e1_diag8_r1.py','scripts/postprocess_wc_e1_diag8_cpu_r1.py',
        'scripts/supervise_wc_e1_diag8_post_cpu_r1.py',ref,
        'research/300_WC_E1_DIAG8_CPU_ACCEPTANCE_AND_ACTUAL_EXECUTION_SCOPE_20261011.md']
    new.extend(v['local_path'] for v in proof['files'].values())
    payload=dict(old['payload_sha256']);new=list(dict.fromkeys(new))
    for n in new:
        assert n not in payload;payload[n]=sha(root/n)
    inherited={n:h for n,h in parent['payload_sha256'].items() if n.startswith('src/') and n.endswith('.py')}
    for n,h in inherited.items():
        assert n not in payload or payload[n]==h,n
    cache=root/'.sync/e1-diag8-production-r1-generated';assert not cache.exists();cache.mkdir()
    requests=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in scope['requests'])
    (cache/'e1-diag8-requests.jsonl').write_text(requests)
    payload['e1-diag8-requests.jsonl']=sha(cache/'e1-diag8-requests.jsonl')
    c={'card':scope['card'],'run_id':scope['run_id'],'arms':scope['arms'],
        'scope_counts':{'planned_paths':8,'independent_model_loads':4,'maximum_updates':288,'maximum_CFG_calls':576},
        'AV_name':scope['requests'][0]['name'],'requests':scope['requests'],
        'parent_stage':'.sync/wc-current-birth-full64-selected-cpu-r1-20261010','parent_config_sha256':sha(root/parent_ref),
        'parent_import_source_sha256':inherited,'scope_ref':scope_ref,'scope_sha256':sha(root/scope_ref),
        'forecast_complete_GPUh':scope['whole_cost']['forecast_complete_GPUh'],
        'automatic_single_job_GPUh':8,'cumulative_cap_GPUh':77.89524658965853,
        'authorization_ref':authority,'authorization_sha256':sha(root/authority),
        'sampling_CPU_capture_ref':ref,'sampling_CPU_capture_sha256':sha(root/ref),
        'working_epoch_strategy':'WORKING_P_AGE_KEEP_INTERVAL','state_steps':[12,30,35,36],
        'checkpoint_reserves':{'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),
            'paired_prefix_reserve_bytes':4*(1<<30)},
        'continue_after_protected_failure':'NEXT_REGISTERED_FRESH_MODEL_PROCESS_ONLY',
        'empty_cache_or_gate_bypass':False,'training':False,'method_speed_or_quality_claim':False,
        'payload_sha256':payload,'GPU_execution_selected':False,'gpu_uuid':None,'production_CPU_receipt_sha256':None}
    cfg=root/'configs/wc_e1_diag8_production_r1_20261011.json';assert not cfg.exists()
    cfg.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n')
    reg={'identity':'E1_DIAG8_ACTUAL_PRODUCTION_CPU_AND_COMPLETE_EXECUTION_PREREGISTERED_NOT_GPU',
        'config_ref':str(cfg.relative_to(root)),'config_sha256':sha(cfg),
        'copies_readonly_sha256':old['payload_sha256'],'original_stage':'.sync/wc-e1-diag8-sampling-cpu-r1-20261011',
        'original_receipt_sha256':proof['files']['receipt.json']['sha256'],'new_local_files':new,
        'generated_requests_cache':str((cache/'e1-diag8-requests.jsonl').relative_to(root)),
        'whole_scope_paths':8,'GPU_submissions':0,'ledger_written':False}
    target=root/'manifests/wc_e1_diag8_production_cpu_r1_preregistration_20261011.json';assert not target.exists()
    target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'payload_files':len(payload),'forecast_GPUh':c['forecast_complete_GPUh']}))


if __name__=='__main__':main()
