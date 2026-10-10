"""New full8 R2 scope; preserve R1 load failure, fees and complete CPU evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    old=json.loads((root/'configs/wc_e1_diag8_production_r1_20261011.json').read_text())
    failed_ref='reports/wc_e1_diag8_gpu_r1_terminal_20261011_capture.json'
    failure=json.loads((root/failed_ref).read_text())
    assert failure['original_source_terminal_scope_and_cost_independently_verified']
    assert failure['complete_numeric_paths']==failure['tensor_files']==failure['video_files']==0
    accepted=json.loads((root/'reports/wc_e1_diag8_production_cpu_r1_terminal_20261011_capture.json').read_text())
    assert accepted['exit_code']==0 and accepted['original_source_actual_entry_contract_and_wrapper_independently_verified']
    parent=json.loads((root/'configs/wc_current_birth_full64_selected_r1_20261010.json').read_text())
    mode='manifests/wc_h0_eval_mode_contract_20261003.json';meta='scripts/check_wc_h0_native_mode_cpu.py'
    assert parent['payload_sha256'][mode]==sha(root/mode)
    assert (root/meta).read_bytes()==subprocess.check_output(['git','show','HEAD:'+meta],cwd=root)
    scope=json.loads((root/old['scope_ref']).read_text())
    scope.update(status='E1_PACKAGING_REPAIR_R2_SAME_COMPLETE8_PREREGISTERED_NOT_GPU',
        card='WC-E1-COLD-PREFIX-STORAGE-DIAG8-R2-20261011-A',run_id='wc-e1-cold-prefix-storage-diag8-r2',
        original_R1_scope_ref=old['scope_ref'],original_R1_scope_sha256=sha(root/old['scope_ref']),
        previous_failed_execution_capture_ref=failed_ref,previous_failed_execution_capture_sha256=sha(root/failed_ref),
        previous_failed_execution_billed_GPUh=failure['billed_GPUh'],
        repair='BIND_REQUIRED_GPU_ONLY_MODE_CONTRACT_BEFORE_LOADING_PLUS_NATIVE_META_CPU_AND_MISSING_CHANGED_CONTROLS',
        algorithm_or_controller_or_checkpoint_arithmetic_changed=False,
        additional_required_stage_assets={mode:sha(root/mode),meta:sha(root/meta)})
    scope_ref='manifests/wc_e1_cold_prefix_memory_diag8_r2_20261011.json'
    target=root/scope_ref;assert not target.exists();target.write_text(json.dumps(scope,indent=2)+'\n')
    new=['src/wcomr/e1_diag8_production_r2.py',mode,meta,
        'scripts/run_wc_e1_diag8_r2.py','scripts/check_wc_e1_diag8_production_cpu_r2.py',
        'scripts/supervise_wc_e1_diag8_r2.py','scripts/postprocess_wc_e1_diag8_cpu_r2.py',
        'scripts/supervise_wc_e1_diag8_post_cpu_r2.py','scripts/select_wc_e1_diag8_r2.py',
        'scripts/prepare_wc_e1_diag8_production_r2.py','scripts/deploy_wc_e1_diag8_production_cpu_r2.py',
        'scripts/dispatch_wc_e1_diag8_r2.py','scripts/capture_wc_e1_diag8_production_cpu_r2.py',
        scope_ref,failed_ref,'manifests/wc_e1_diag8_r2_entry_metadata_derivation_20261011.json',
        'research/303_WC_E1_REQUIRED_STARTUP_CONTRACT_FAILURE_AND_R2_REPAIR_20261011.md',
        'research/304_WC_E1_FULL8_R2_ACTUAL_CPU_SCOPE_20261011.md']
    payload=dict(old['payload_sha256'])
    for n in new:
        assert n not in payload,n;payload[n]=sha(root/n)
    c={**old,'card':scope['card'],'run_id':scope['run_id'],'scope_ref':scope_ref,'scope_sha256':sha(root/scope_ref),
        'payload_sha256':payload,'model_mode_contract_ref':mode,'model_mode_contract_sha256':sha(root/mode),
        'required_stage_assets':{mode:sha(root/mode),meta:sha(root/meta)},
        'previous_failed_execution_capture_ref':failed_ref,'GPU_execution_selected':False,'gpu_uuid':None,
        'production_CPU_receipt_sha256':None}
    cfg_ref='configs/wc_e1_diag8_production_r2_20261011.json';cfg=root/cfg_ref;assert not cfg.exists()
    cfg.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n')
    reg={'identity':'E1_DIAG8_R2_ACTUAL_PRODUCTION_META_STARTUP_CPU_PREREGISTERED_NOT_GPU',
        'config_ref':cfg_ref,'config_sha256':sha(cfg),'copies_readonly_sha256':old['payload_sha256'],
        'original_stage':'.sync/wc-e1-diag8-production-cpu-r1-20261011',
        'original_receipt_sha256':accepted['files']['production-CPU-receipt.json']['sha256'],
        'new_local_files':new,'GPU_submissions':0,'ledger_written':False,'complete_scope_paths':8,
        'no_sampling_CPU_rerun_unaffected_body':True,'new_native_meta_mode_CPU_required':True,
        'GPU_only_asset_refusal_controls':4,'forecast_complete_GPUh':c['forecast_complete_GPUh']}
    path=root/'manifests/wc_e1_diag8_production_cpu_r2_preregistration_20261011.json';assert not path.exists()
    path.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'payload_files':len(payload),'full_paths':8,'forecast_GPUh':c['forecast_complete_GPUh']}))


if __name__=='__main__':main()
