"""Separate post/selection payload preserves the accepted459 method bytes."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(root/'src'))
    from wcomr.p_reference_same_state_production_r1 import binding
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    config_ref = 'configs/wc_p_reference_same_state_production_r2_20261011.json'
    c = json.loads((root/config_ref).read_text())
    capture_ref = 'reports/wc_p_reference_same_state_production_cpu_r2_terminal_20261011_capture.json'
    proof = json.loads((root/capture_ref).read_text())
    assert proof['status'] == 'P_REFERENCE_TWO_FLOW_ACTUAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU'
    assert proof['complete_frozen_files_unchanged'] == 459
    names = ['src/wcomr/p_reference_same_state_execution_r1.py',
        'src/wcomr/p_reference_same_state_terminal_r1.py',
        'src/wcomr/p_reference_same_state_tensor_audit_r2.py',
        'src/wcomr/e4c_source_age_tensor_audit_r2.py',
        'scripts/supervise_wc_p_reference_same_state_r1.py',
        'scripts/supervise_wc_p_reference_same_state_post_cpu_r1.py',
        'scripts/postprocess_wc_p_reference_same_state_cpu_r1.py',
        'scripts/select_and_launch_wc_p_reference_same_state_r1.py',
        'scripts/dispatch_wc_p_reference_same_state_r1.py',
        'scripts/check_wc_p_reference_same_state_execution_cpu_r1.py',
        'scripts/prepare_wc_p_reference_same_state_execution_cpu_r1.py',
        'scripts/deploy_wc_p_reference_same_state_execution_cpu_r1.py',
        'tests/check_p_reference_same_state_terminal_cpu_r1.py',
        'tests/check_p_reference_same_state_supervisor_cpu_r1.py',
        capture_ref, 'research/362_WC_P_REFERENCE_COMPLETE_POST_SELECTION_CPU_PREREGISTRATION_20261011.md']
    names += [item['local_path'] for item in proof['originals'].values()]
    files = {}
    for name in names:
        ref = str((root/name).resolve().relative_to(root)); h = sha(root/ref)
        if ref in c['payload_sha256']:
            assert c['payload_sha256'][ref] == h
        else: files[ref] = h
    protocol = {'identity': 'P_REFERENCE_COMPLETE_POST_SELECTION_PREREGISTERED_NOT_GPU',
        'card': c['card'], 'run_id': c['run_id'], 'scope_counts': c['scope_counts'],
        'method_binding_sha256': binding(c), 'method_payload_sha256': c['payload_sha256'],
        'execution_payload_sha256': files, 'production_capture_ref': capture_ref,
        'production_capture_sha256': sha(root/capture_ref),
        'original_production_CPU_receipt_sha256': proof['originals']['production-CPU-receipt.json']['sha256'],
        'retain_complete_denominators_after_any_failure': True,
        'read_all_available_point_and_video_artifacts': True,
        'parent_video_frames': 93, 'above8_requires_exact_full_card_approval': True,
        'training': False, 'human_review': False, 'quality_or_clean_speed_claim': False,
        'original_CPU_sampler_reuse_stage': '.sync/wc-p-reference-same-state-cpu-r3-20261011',
        'old_real_video_reader_input_run': 'wc-e4c-matched-p-d-age124-offon4-suffix16-r1'}
    ref = root/'manifests/wc_p_reference_same_state_execution_protocol_r1_20261011.json'
    assert not ref.exists(); ref.write_text(json.dumps(protocol, indent=2)+'\n')
    reg = {'identity': 'P_REFERENCE_COMPLETE_EXECUTION_CPU_PREREGISTRATION_NOT_GPU',
        'config_ref': config_ref, 'config_sha256': sha(root/config_ref),
        'protocol_ref': str(ref.relative_to(root)), 'protocol_sha256': sha(ref),
        'original_stage': '.sync/wc-p-reference-same-state-production-cpu-r2-20261011',
        'original_production_CPU_receipt_sha256': protocol['original_production_CPU_receipt_sha256'],
        'method_payload_sha256': c['payload_sha256'], 'new_payload_sha256': files,
        'forecast_complete_GPUh': c['forecast_complete_GPUh'],
        'complete_scope_counts': c['scope_counts'], 'GPU_submissions': 0, 'ledger_written': False,
        'exact_P_card_approval_not_received': True, 'approved_E3_has_queue_priority': True}
    ref = root/'manifests/wc_p_reference_same_state_execution_cpu_r1_preregistration_20261011.json'
    assert not ref.exists(); ref.write_text(json.dumps(reg, indent=2)+'\n')
    print(json.dumps({'status': reg['identity'], 'method_files': len(c['payload_sha256']),
        'execution_files': len(files), 'forecast_complete_GPUh': c['forecast_complete_GPUh']}))


if __name__ == '__main__': main()
