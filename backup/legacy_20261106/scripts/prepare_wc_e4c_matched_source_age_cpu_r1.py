"""Bind accepted historical source bytes and the affected E3 CPU additions."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    refs=['reports/wc_e1_storage_full_sampler_cpu_r1_terminal_20261011_capture.json',
          'reports/wc_e1_diag8_sampling_cpu_r1_terminal_20261011_capture.json']
    old=json.loads((root/refs[0]).read_text())
    assert old['exit_code']==0 and old['independent_source_complete_results_and_actual_artifact_hashes_verified']
    item=old['files']['registration.json'];raw=gzip.decompress((root/item['local_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==item['sha256'];prior=json.loads(raw)
    payload=dict(prior['payload_sha256']);copies=dict(payload)
    new=['src/wcomr/e1_memory_diagnostic_sampling_r1.py', 'src/wcomr/prepared_input_persistence_r1.py', 'src/wcomr/source_aware_CPU_storage_sampling_r1.py', 'src/wcomr/cpu_owned_state_snapshot.py', 'src/wcomr/e4c_offline_intervention_control_r1.py', 'src/wcomr/e4c_matched_source_age_owner_r1.py', 'src/wcomr/e4c_matched_source_age_sampling_r1.py', 'src/wcomr/e4c_source_age_tensor_audit_r1.py', 'tests/check_e4c_offline_intervention_control_cpu_r1.py', 'tests/check_e4c_matched_source_age_sampling_cpu_r1.py', 'scripts/check_wc_e4c_matched_source_age_cpu_r1.py', 'scripts/prepare_wc_e4c_matched_source_age_cpu_r1.py', 'scripts/deploy_wc_e4c_matched_source_age_cpu_r1.py', 'manifests/wc_e4c_matched_source_age_complete_scope_r1_20261011.json', 'research/325_WC_E4C_MATCHED_SOURCE_AGE124_COMPLETE_SCOPE_20261011.md']
    for n in new:
        h=hashlib.sha256((root/n).read_bytes()).hexdigest()
        assert n not in payload or payload[n]==h,n
        payload[n]=h
    reg={'identity':'E4C_MATCHED_SOURCE_AGE_COMPLETE_CPU_PREREGISTRATION_NOT_GPU',
        'previous_accepted_source_revision':old['source_revision'],
        'original_accepted_CPU_stage':'.sync/wc-e1-storage-full-sampler-cpu-r1-20261011',
        'original_accepted_CPU_receipt_sha256':old['files']['receipt.json']['sha256'],
        'copies_readonly_sha256':copies,'new_local_files':new,'payload_sha256':payload,
        'runtime_source_sha256':prior['runtime_source_sha256'],
        'scientific_scope_ref':'manifests/wc_e4c_matched_source_age_complete_scope_r1_20261011.json',
        'CPU_scope':{'flows':[False,True],'full_parents':8,'events':8,'suffixes':32,
            'teacher_points':48,'total_pair_computations':496,'total_CFG_calls':992,
            'actual_files_reloaded':88,'actual_tensors_reloaded':776,
            'actual_direct_tensor_comparisons':324,'scope_refusals':12,'actual_truncation_refusals':2,
            'Toy_weights_prepare_decode_and_synthetic_policy':True,'same_live_model_original_OFF_ON_controls':True},
        'original_full128_algorithm_CPU_reused_not_rerun':True,'GPU_execution_selected':False,'GPU_submissions':0,'ledger_written':False}
    target=root/'manifests/wc_e4c_matched_source_age_full_cpu_r1_20261011.json';assert not target.exists()
    target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'payload_files':len(payload),'new_files':len(new),'GPU_submissions':0}))


if __name__=='__main__':main()
