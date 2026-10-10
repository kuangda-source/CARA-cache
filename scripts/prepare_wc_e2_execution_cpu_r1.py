#!/usr/bin/env python3
"""Freeze complete execution/postprocessing; no GPU selection or approval."""
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1]
    target=root/'manifests/wc_e2_execution_cpu_r1_preregistration_20261011.json';assert not target.exists()
    c=json.loads((root/'configs/wc_e2_production_r1_20261011.json').read_text())
    proof_ref='reports/wc_e2_production_cpu_r1_terminal_20261011_capture.json'
    proof=json.loads((root/proof_ref).read_text());assert proof['exit_code']==0 and not c['GPU_execution_selected']
    controls_ref='reports/wc_e2_full76_execution_reporting_cpu_r1_20261011.json'
    controls=json.loads((root/controls_ref).read_text())
    assert controls['status']=='E2_COMPLETE76_EXECUTION_REPORTING_SCALAR_CPU_PASS_NOT_GPU_OR_METRIC'
    assert controls['admission_refusals']==17 and controls['scalar_refusals']==8
    assert controls['actual_memory_boundaries']==152 and controls['scalar_frame_distances']==6324
    names=['src/wcomr/e2_execution_r1.py','src/wcomr/e2_full76_reports_r1.py',
        'scripts/run_wc_e2_observed_r1.py','scripts/supervise_wc_e2_full76_r1.py',
        'scripts/postprocess_wc_e2_full76_cpu_r1.py','scripts/supervise_wc_e2_post_cpu_r1.py',
        'scripts/check_wc_e2_execution_cpu_r1.py','scripts/deploy_wc_e2_execution_cpu_r1.py',
        'scripts/prepare_wc_e2_execution_cpu_r1.py','tests/check_e2_full76_execution_cpu_r1.py',
        'src/wcomr/lpips_resource_identity.py','src/wcomr/rv0_lpips.py',
        'manifests/wc_e2_full76_execution_design_r1_20261011.json',controls_ref,proof_ref,
        'reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json',
        'reports/wc_ra_plus_a_r1_terminal_20261010_runner_native.gz',
        'reports/wc_ra_plus_a_r1_terminal_20261010_CPU_result_native.gz',
        'research/296_WC_E2_COMPLETE_EXECUTION_POSTPROCESS_CPU_SCOPE_20261011.md']
    names.extend(v['local_path'] for v in proof['files'].values())
    payload={n:sha(root/n) for n in names}
    for n,h in controls['source_sha256'].items():assert payload[n]==h
    protocol={'card':c['card'],'run_id':c['run_id'],'scope_counts':c['scope_counts'],
        'method_config_binding_sha256':proof['config_binding_sha256'],'method_payload_sha256':c['payload_sha256'],
        'method_CPU_capture_ref':proof_ref,'execution_payload_sha256':payload,'single_job_autonomy_GPUh':8,
        'maximum_available_pairs':68,'maximum_confirmation_pairs':32,'frames_per_pair':93,
        'old_capture_ref':'reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json',
        'old_runner_ref':'reports/wc_ra_plus_a_r1_terminal_20261010_runner_native.gz',
        'old_raw_ref':'reports/wc_ra_plus_a_r1_terminal_20261010_CPU_result_native.gz',
        'GPU_execution_selected':False,'GPU_submissions':0,'ledger_written':False}
    cache=root/'.sync/wc-e2-execution-inputs-r1';cache.mkdir(exist_ok=False)
    path=cache/'execution-protocol.json';path.write_text(json.dumps(protocol,indent=2)+'\n')
    reg={'identity':'E2_COMPLETE76_EXECUTION_WRAPPER_PRODUCTION_CPU_PREREGISTRATION_NOT_GPU',
        'method_config_ref':'configs/wc_e2_production_r1_20261011.json','method_config_sha256':sha(root/'configs/wc_e2_production_r1_20261011.json'),
        'method_original_stage':'.sync/wc-e2-production-cpu-r1-20261011',
        'method_source':proof['source_revision'],'method_original_receipt_sha256':proof['files']['receipt.json']['sha256'],
        'execution_payload_sha256':payload,'generated_protocol_cache':str(cache.relative_to(root)),
        'execution_protocol_sha256':sha(path),'GPU_execution_selected':False,'GPU_submissions':0,'ledger_written':False,
        'scope_counts':c['scope_counts'],'forecast_complete_GPUh':c['forecast_complete_GPUh'],
        'actual_wrapper_CPU_and_metric_assets_not_yet_checked':True}
    target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'extra_files':len(payload),'complete_paths':76,'GPU_submissions':0}))


if __name__=='__main__':main()
