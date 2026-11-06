"""Freeze new post/selection bytes without changing the accepted449 method scope."""
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    c_ref='configs/wc_e3_complete64_production_r1_20261011.json';c=json.loads((root/c_ref).read_text())
    capture_ref='reports/wc_e3_complete64_production_cpu_r1_terminal_20261011_capture.json'
    capture=json.loads((root/capture_ref).read_text())
    assert capture['exit_code']==0 and capture['original_source_actual_entry_contract_and_wrapper_independently_verified']
    new=['src/wcomr/e3_complete64_terminal_r1.py','src/wcomr/e3_complete64_execution_r1.py',
        'src/wcomr/full64_partial_recovery_cpu.py','src/wcomr/rv0_lpips.py','src/wcomr/lpips_resource_identity.py',
        'scripts/postprocess_wc_e3_complete64_cpu_r1.py','scripts/supervise_wc_e3_complete64_post_cpu_r1.py',
        'scripts/select_and_launch_wc_e3_complete64_r1.py','scripts/check_wc_e3_complete64_execution_cpu_r1.py',
        'tests/check_e3_complete64_terminal_cpu_r1.py','scripts/prepare_wc_e3_complete64_execution_r1.py',
        'scripts/deploy_wc_e3_complete64_execution_cpu_r1.py','scripts/capture_wc_e3_complete64_execution_cpu_r1.py',
        'scripts/dispatch_wc_e3_complete64_r1.py',capture_ref,capture['files']['production-CPU-receipt.json']['local_path']]
    assert not any(n in c['payload_sha256'] for n in new)
    import sys;sys.path.insert(0,str(root/'src'))
    from wcomr.e3_complete64_production_r1 import binding
    sources={}
    for name,ref,key,remote,artifact_root in [
        ('ORIGINAL64','reports/wc_current_birth_full64_r1_terminal_20261010_capture_and_independent_audit.json',
            'runner','outputs/wc-current-birth-capd-full64-r1/diagnostic/receipt.json',
            'outputs/wc-current-birth-capd-full64-r1/diagnostic'),
        ('E1_CPU_PREFIX','reports/wc_e1_diag8_gpu_r2_terminal_20261011_capture.json',
            'CPU_PREFIX-receipt','outputs/wc-e1-cold-prefix-storage-diag8-r2/CPU_PREFIX/receipt.json',
            'outputs/wc-e1-cold-prefix-storage-diag8-r2/CPU_PREFIX')]:
        a=json.loads((root/ref).read_text())
        sources[name]={'path':remote,'sha256':a['files'][key]['sha256'],'source_revision':a['source_revision'],
            'artifact_root':artifact_root,'not_independent_confirmation':True}
    p={'identity':'E3_COMPLETE64_POST_SELECTION_PREREGISTERED_NOT_GPU','card':c['card'],'run_id':c['run_id'],
        'method_binding_sha256':binding(c),'scope_counts':c['scope_counts'],'method_payload_sha256':c['payload_sha256'],
        'execution_payload_sha256':{n:sha(root/n) for n in new},'reuse_receipts':sources,
        'production_capture_ref':capture_ref,'production_capture_sha256':sha(root/capture_ref),
        'original_method_CPU_stage':'.sync/wc-e3-complete64-production-cpu-r1-20261011',
        'original_production_CPU_receipt_sha256':capture['files']['production-CPU-receipt.json']['sha256'],
        'score_valid_prefix_even_whole_card_failed':True,'metric_frames':93,'training':False,'human_review':False,
        'clean_speed_claim':False,'above8_requires_exact_full_card_approval':True,
        'scope_not_reduced_or_split':True,'all64_status_and_contrasts_retained':True}
    proto='manifests/wc_e3_complete64_execution_protocol_r1_20261011.json'
    target=root/proto;assert not target.exists();target.write_text(json.dumps(p,indent=2)+'\n')
    reg={'identity':'E3_COMPLETE64_AFFECTED_POST_SELECTION_CPU_PREREGISTRATION_NOT_GPU',
        'config_ref':c_ref,'config_sha256':sha(root/c_ref),'protocol_ref':proto,'protocol_sha256':sha(target),
        'original_stage':p['original_method_CPU_stage'],
        'original_CPU_receipt_sha256':p['original_production_CPU_receipt_sha256'],
        'copies_readonly_sha256':c['payload_sha256'],'new_local_files':new,
        'execution_payload_sha256':p['execution_payload_sha256'],'scope_counts':c['scope_counts'],
        'forecast_complete_GPUh':c['forecast_complete_GPUh'],'GPU_submissions':0,'ledger_written':False,
        'actual_reused_files':10,'actual_tensors_to_reload':370,'actual_videos_to_decode':10,
        'unchanged_sampling_and_production_CPU_reused':True,'original_metric_CPU_resource_controls_reused':True}
    name=root/'manifests/wc_e3_complete64_execution_cpu_r1_preregistration_20261011.json';assert not name.exists()
    name.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'unchanged_method_files':len(c['payload_sha256']),
        'new_execution_files':len(new),'forecast_complete_GPUh':c['forecast_complete_GPUh']}))


if __name__=='__main__':main()
