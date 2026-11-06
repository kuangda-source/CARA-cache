#!/usr/bin/env python3
"""Pre-register startup-only repair; preserve historical231+29 byte tables."""
import copy
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1]
    target=root/'manifests/wc_e2_startup_cpu_r2_preregistration_20261011.json';assert not target.exists()
    old_ref='manifests/wc_e2_execution_cpu_r1_preregistration_20261011.json'
    old=json.loads((root/old_ref).read_text())
    c=json.loads((root/old['method_config_ref']).read_text())
    old_protocol=root/old['generated_protocol_cache']/'execution-protocol.json'
    assert sha(old_protocol)==old['execution_protocol_sha256']
    protocol=copy.deepcopy(json.loads(old_protocol.read_text()))
    proof=json.loads((root/'reports/wc_e2_execution_cpu_r1_terminal_20261011_capture.json').read_text())
    assert proof['exit_code']==0 and proof['original_source_and_execution_protocol_independently_verified']
    assert len(c['payload_sha256'])==231 and len(old['execution_payload_sha256'])==29
    required={n:sha(root/n) for n in ('manifests/wc_h0_eval_mode_contract_20261003.json','scripts/check_wc_h0_native_mode_cpu.py')}
    assert required['manifests/wc_h0_eval_mode_contract_20261003.json']=='a990ad5c078519bc7f284139fbd3afb72b0492f60de7ebc1e327927d613fcabd'
    extras=list(required)+['scripts/check_wc_e2_startup_cpu_r2.py','scripts/prepare_wc_e2_startup_cpu_r2.py',
        'scripts/deploy_wc_e2_startup_cpu_r2.py','scripts/capture_wc_e2_startup_cpu_r2.py',
        'research/307_WC_E2_REQUIRED_STARTUP_ASSET_CPU_R2_PREREGISTRATION_20261011.md']
    new={n:sha(root/n) for n in extras};assert not set(new)&(set(c['payload_sha256'])|set(old['execution_payload_sha256']))
    protocol['execution_payload_sha256'].update(new)
    protocol['required_startup_assets']=required
    protocol['startup_wrapper_revision']='r2_assets_only_same_method_and_card'
    cache=root/'.sync/wc-e2-startup-inputs-r2';cache.mkdir(exist_ok=False)
    (cache/'execution-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    reg={'identity':'E2_REQUIRED_STARTUP_ASSETS_R2_CPU_PREREGISTRATION_NOT_GPU',
        'method_config_ref':old['method_config_ref'],'method_config_sha256':old['method_config_sha256'],
        'method_config_binding_sha256':proof['config_binding_sha256'],
        'original_execution_stage':'.sync/wc-e2-execution-cpu-r1-20261011',
        'original_execution_source_revision':proof['source_revision'],
        'original_execution_receipt_sha256':proof['files']['execution-CPU-receipt.json']['sha256'],
        'original_execution_protocol_sha256':old['execution_protocol_sha256'],
        'original_execution_payload_sha256':old['execution_payload_sha256'],
        'new_payload_sha256':new,'execution_payload_sha256':protocol['execution_payload_sha256'],
        'required_startup_assets':required,'generated_protocol_cache':str(cache.relative_to(root)),
        'execution_protocol_sha256':sha(cache/'execution-protocol.json'),
        'scope_counts':c['scope_counts'],'forecast_complete_GPUh':c['forecast_complete_GPUh'],
        'affected_CPU_controls':['unchanged_actual_entry_and_scalar_protocol','four_required_asset_refusals','native_meta_topology_and_shared_eval'],
        'sampling_arithmetic_and_method_binding_unchanged':True,'GPU_execution_selected':False,
        'GPU_submissions':0,'ledger_written':False}
    target.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':reg['identity'],'original_method_files':231,'original_execution_files':29,
        'new_files':len(new),'method_binding':reg['method_config_binding_sha256'],'GPU_submissions':0}))


if __name__=='__main__':main()
