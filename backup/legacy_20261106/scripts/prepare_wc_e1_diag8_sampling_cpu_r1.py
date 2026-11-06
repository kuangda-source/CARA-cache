"""Freeze fixed diagnostic scope and accepted365 CPU sources without GPU."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    target=root/'manifests/wc_e1_diag8_sampling_cpu_r1_preregistration_20261011.json';assert not target.exists()
    proof_ref='reports/wc_e1_storage_full_sampler_cpu_r1_terminal_20261011_capture.json'
    proof=json.loads((root/proof_ref).read_text())
    assert proof['exit_code']==0 and proof['independent_source_complete_results_and_actual_artifact_hashes_verified']
    raw=gzip.decompress((root/proof['files']['registration.json']['local_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==proof['files']['registration.json']['sha256']
    old=json.loads(raw)
    scope_ref='manifests/wc_e1_cold_prefix_memory_diag8_r1_20261011.json';scope=json.loads((root/scope_ref).read_text())
    assert scope['scope_counts']['planned_paths']==8 and scope['whole_cost']['forecast_complete_GPUh']<8
    payload=dict(old['payload_sha256'])
    new=['src/wcomr/e1_memory_diagnostic_sampling_r1.py','tests/check_e1_memory_diagnostic_sampling_cpu_r1.py',
        'scripts/check_wc_e1_diag8_sampling_cpu_r1.py','scripts/prepare_wc_e1_diag8_sampling_cpu_r1.py',
        'scripts/deploy_wc_e1_diag8_sampling_cpu_r1.py',scope_ref,proof_ref,
        'research/299_WC_E1_DIAG8_SELECTOR_AND_COMPLETE_CPU_SCOPE_20261011.md']
    new.extend(n for n in scope['source_sha256'] if n not in payload)
    new=list(dict.fromkeys(new))
    for n in new:
        value=hashlib.sha256((root/n).read_bytes()).hexdigest()
        assert n not in payload or payload[n]==value,n
        payload[n]=value
    for n,h in scope['source_sha256'].items():assert payload[n]==h,n
    reg={'identity':'E1_DIAG8_SELECTED_SAMPLER_COMPLETE_CPU_PREREGISTRATION_NOT_GPU',
        'previous_complete_E1_CPU_capture_ref':proof_ref,'previous_complete_E1_CPU_source':proof['source_revision'],
        'original_E1_CPU_receipt_sha256':proof['files']['receipt.json']['sha256'],
        'original_E1_CPU_stage':'.sync/wc-e1-storage-full-sampler-cpu-r1-20261011',
        'copies_readonly_sha256':old['payload_sha256'],'new_local_files':new,
        'payload_sha256':payload,'runtime_source_sha256':old['runtime_source_sha256'],
        'diagnostic_scope_ref':scope_ref,'diagnostic_scope_sha256':payload[scope_ref],
        'CPU_scope':{'arms':['ORIGINAL_COLD','CPU_COLD','ORIGINAL_PREFIX','CPU_PREFIX'],'flows':[False,True],
            'successful_complete_paths':16,'last_writer_failure_attempted_paths':12,
            'complete_solver_updates':1008,'CFG_calls':2016,'success_guided_reloaded':576,'success_final_reloaded':16,
            'state_mutation_refusals':72,'arm_mutation_refusals':12,'truncation_refusals':8,'metadata_events':336,
            'Toy_model_reused_between_CPU_arms':True,'actual_four_model_loads_or_GPU_capacity_claim':False},
        'GPU_execution_selected':False,'GPU_submissions':0,'ledger_written':False}
    target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'payload_files':len(payload),'new_files':len(new),'GPU_submissions':0}))


if __name__=='__main__':main()
