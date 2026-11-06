"""Bind accepted complete CPU bytes, actual immutable inputs and whole cost."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    proof_ref = 'reports/wc_e4c_matched_source_age_cpu_r3_terminal_20261011_capture.json'
    proof = json.loads((root/proof_ref).read_text())
    assert proof['receipt']['exit_code'] == 0 and proof['original_source_receipts_complete_scope_and_actual_vectors_independently_verified']
    old = json.loads(gzip.decompress((root/proof['files']['registration.json']['local_path']).read_bytes()))
    scope_ref = 'manifests/wc_e4c_matched_source_age_complete_scope_r1_20261011.json'
    cost_ref = 'manifests/wc_e4c_matched_source_age_whole_cost_r1_20261011.json'
    scope = json.loads((root/scope_ref).read_text()); cost = json.loads((root/cost_ref).read_text())
    parent_ref = 'configs/wc_current_birth_full64_selected_r1_20261010.json'
    parent = json.loads((root/parent_ref).read_text())
    evidence = json.loads((root/'reports/wc_e1_diag8_gpu_r2_terminal_20261011_capture.json').read_text())
    meta = evidence['files']['production-CPU-receipt']
    assert hashlib.sha256(gzip.decompress((root/meta['local_path']).read_bytes())).hexdigest() == meta['sha256']
    authority = 'manifests/wc_current_window_execution_authorization_20261011_8gpuh.json'
    mode = 'manifests/wc_h0_eval_mode_contract_20261003.json'; mode_script = 'scripts/check_wc_h0_native_mode_cpu.py'
    names = ['src/wcomr/e4c_source_age_production_r1.py', 'src/wcomr/e1_diag8_production_r2.py',
        'scripts/run_wc_e4c_source_age_r1.py', 'scripts/supervise_wc_e4c_source_age_r1.py',
        'scripts/check_wc_e4c_source_age_production_cpu_r1.py',
        'scripts/deploy_wc_e4c_source_age_production_cpu_r1.py',
        'scripts/prepare_wc_e4c_source_age_production_r1.py', cost_ref, proof_ref,
        meta['local_path'], mode, mode_script, authority,
        'research/329_WC_E4C_PHYSICAL_CPU_ACCEPTANCE_AND_ACTUAL_ENTRY_SCOPE_20261011.md']
    names += [a['local_path'] for a in proof['files'].values()]
    payload = dict(old['payload_sha256']); new = []
    for name in dict.fromkeys(names):
        h = sha(root/name)
        if name in payload: assert payload[name] == h, name
        else: payload[name] = h; new.append(name)
    requests = [r for r in parent['preregistration']['requests'] if r['name'] in scope['sample_names']]
    requests.sort(key=lambda r: scope['sample_names'].index(r['name']))
    cache = root/'.sync/e4c-source-age-production-r1-generated'; assert not cache.exists(); cache.mkdir()
    request_file = cache/'e4c-requests.jsonl'
    request_file.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in requests))
    payload['e4c-requests.jsonl'] = sha(request_file)
    c = {'card': scope['card'], 'run_id': scope['run_id'], 'scope_counts': scope['scope_counts'],
        'scope_ref': scope_ref, 'scope_sha256': sha(root/scope_ref), 'cost_ref': cost_ref,
        'cost_sha256': sha(root/cost_ref), 'forecast_complete_GPUh': cost['forecast_complete_GPUh'],
        'requests': requests, 'parent_stage': '.sync/wc-current-birth-full64-selected-cpu-r1-20261010',
        'parent_config_sha256': sha(root/parent_ref), 'parent_import_source_sha256': {
            n: h for n, h in parent['payload_sha256'].items() if n.startswith('src/') and n.endswith('.py')},
        'sampling_CPU_capture_ref': proof_ref, 'sampling_CPU_capture_sha256': sha(root/proof_ref),
        'authorization_ref': authority, 'authorization_sha256': sha(root/authority),
        'automatic_single_job_GPUh': 8, 'cumulative_cap_GPUh': 77.89524658965853,
        'working_epoch_strategy': 'WORKING_P_AGE_KEEP_INTERVAL',
        'checkpoint_reserves': {'logical_copy_cap_bytes': 6*(1 << 30),
            'workspace_reserve_bytes': 4*(1 << 30), 'paired_prefix_reserve_bytes': 4*(1 << 30)},
        'model_mode_contract_ref': mode, 'model_mode_contract_sha256': sha(root/mode),
        'required_stage_assets': {mode: sha(root/mode), mode_script: sha(root/mode_script)},
        'native_meta_CPU_receipt_ref': meta['local_path'], 'native_meta_CPU_receipt_raw_sha256': meta['sha256'],
        'continue_after_failure': 'STOP_RETAIN_COMPLETE_SCOPE', 'empty_cache_or_gate_bypass': False,
        'training': False, 'human_review': False, 'method_speed_or_quality_claim': False,
        'payload_sha256': payload, 'GPU_execution_selected': False, 'gpu_uuid': None,
        'production_CPU_receipt_sha256': None}
    cfg_ref = 'configs/wc_e4c_source_age_production_r1_20261011.json'
    target = root/cfg_ref; assert not target.exists(); target.write_text(json.dumps(c, indent=2)+'\n')
    reg = {'identity': 'E4C_COMPLETE_SOURCE_AGE_ACTUAL_ENTRY_CPU_PREREGISTRATION_NOT_GPU',
        'config_ref': cfg_ref, 'config_sha256': sha(target),
        'copies_readonly_sha256': old['payload_sha256'], 'original_stage': '.sync/wc-e4c-matched-source-age-cpu-r3-20261011',
        'original_receipt_sha256': proof['files']['receipt.json']['sha256'], 'new_local_files': new,
        'generated_requests_cache': str(request_file.relative_to(root)),
        'forecast_complete_GPUh': c['forecast_complete_GPUh'], 'GPU_submissions': 0, 'ledger_written': False,
        'full_sampler_CPU_or_unchanged_native_meta_not_rerun': True}
    target = root/'manifests/wc_e4c_source_age_production_cpu_r1_preregistration_20261011.json'
    assert not target.exists(); target.write_text(json.dumps(reg, indent=2)+'\n')
    print(json.dumps({'status': reg['identity'], 'payload_files': len(payload), 'forecast_GPUh': c['forecast_complete_GPUh']}))


if __name__ == '__main__': main()
