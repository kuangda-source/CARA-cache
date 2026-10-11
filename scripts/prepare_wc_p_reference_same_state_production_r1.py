"""Bind exact accepted444, actual inputs and a complete two-flow cost forecast."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    proof_ref = 'reports/wc_p_reference_same_state_cpu_r3_terminal_20261011_capture.json'
    proof = json.loads((root/proof_ref).read_text())
    assert proof['status'] == 'P_REFERENCE_SAME_STATE_COMPLETE_CPU_INDEPENDENTLY_AUDITED_NOT_GPU'
    assert (proof['actual_reloaded_files'], proof['actual_reloaded_tensors'],
            proof['actual_direct_tensor_comparisons']) == (88, 1160, 420)
    item = proof['originals']['registration.json']
    raw = gzip.decompress((root/item['local_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    original = json.loads(raw)
    inherited = {**original['inherited_payload_sha256'], **original['new_payload_sha256']}
    assert len(inherited) == 444
    scope_ref = 'manifests/wc_p_reference_same_state_complete_scope_r1_20261011.json'
    scope = json.loads((root/scope_ref).read_text())
    prior_ref = 'manifests/wc_e4c_matched_source_age_whole_cost_r1_20261011.json'
    prior = json.loads((root/prior_ref).read_text())
    # Two complete old E4c cost envelopes already include the original parents,
    # suffixes, teachers, event snapshots and 48 teacher-state restores. The
    # four additional C readouts at each of 48 points require 192 extra pairs
    # and 192 additional restores, plus new full-source hashing and larger IO.
    base_seconds = 2*prior['forecast_complete_seconds']
    extra_pair_seconds = 192*(prior['max_observed_instrumented_full36_pipeline_seconds']
        +prior['additional_A_head_allowance_per36'])/36*prior['whole_pair_and_load_multiplier']
    extra_restores = 192*120.
    full_source_hash_allowance = 48*30.
    larger_artifact_allowance = 48*10.
    complete = base_seconds+extra_pair_seconds+extra_restores+full_source_hash_allowance+larger_artifact_allowance
    cost_ref = 'manifests/wc_p_reference_same_state_whole_cost_r1_20261011.json'
    cost = {'identity': 'P_REFERENCE_TWO_FLOW_FULL688_COST_PLANNING_NOT_RUNTIME_GUARANTEE',
        'scope_ref': scope_ref, 'scope_sha256': sha(root/scope_ref),
        'prior_cost_ref': prior_ref, 'prior_cost_sha256': sha(root/prior_ref),
        'whole_pair_computations': 688, 'whole_CFG_calls': 1376,
        'actual_model_loads_planned': 2, 'conservative_load_allowance': 4,
        'two_complete_old_E4c_envelopes_seconds': base_seconds,
        'extra_same_state_C_pairs': 192, 'extra_same_state_C_pairs_seconds': extra_pair_seconds,
        'complete_same_state_restores': 240,
        'extra192_same_state_restores_seconds': extra_restores,
        'new48_full_source_hash_seconds': full_source_hash_allowance,
        'larger48_artifact_IO_seconds': larger_artifact_allowance,
        'forecast_complete_seconds': complete, 'forecast_complete_GPUh': complete/3600,
        'measured_original_pipeline_is_instrumented_not_clean_latency': True,
        'new_restore_hash_IO_allowances_are_not_measured_GPU_cost': True,
        'includes_full_heads_copy_restore_transport_hash_failure_and_cleanup': True,
        'whole_scope_cannot_be_split_or_reduced_for_8_GPUh': True,
        'automatic_single_job_GPUh': 8, 'GPU_execution_selected': False,
        'GPU_submissions': 0, 'ledger_written': False,
        'E3_exact_authorization_not_reused_for_this_card': True}
    assert not (root/cost_ref).exists()
    (root/cost_ref).write_text(json.dumps(cost, indent=2)+'\n')
    parent_ref = 'configs/wc_current_birth_full64_selected_r1_20261010.json'
    parent = json.loads((root/parent_ref).read_text())
    old_config = json.loads((root/'configs/wc_e4c_source_age_production_r1_20261011.json').read_text())
    authority = 'manifests/wc_current_window_execution_authorization_20261011_8gpuh.json'
    mode = old_config['model_mode_contract_ref']; mode_script = 'scripts/check_wc_h0_native_mode_cpu.py'
    meta_ref = old_config['native_meta_CPU_receipt_ref']
    assert hashlib.sha256(gzip.decompress((root/meta_ref).read_bytes())).hexdigest() == old_config['native_meta_CPU_receipt_raw_sha256']
    names = ['src/wcomr/p_reference_same_state_production_r1.py',
        'src/wcomr/e4c_source_age_production_r1.py', 'src/wcomr/e1_diag8_production_r2.py',
        'scripts/run_wc_e4c_source_age_r1.py', 'scripts/run_wc_p_reference_same_state_r1.py',
        'scripts/check_wc_p_reference_same_state_production_cpu_r1.py',
        'scripts/deploy_wc_p_reference_same_state_production_cpu_r1.py',
        'scripts/prepare_wc_p_reference_same_state_production_r1.py',
        cost_ref, proof_ref, meta_ref, mode, mode_script, authority,
        'research/359_WC_P_REFERENCE_TWO_FLOW_ACTUAL_ENTRY_PREREGISTRATION_20261011.md']
    names += [x['local_path'] for x in proof['originals'].values()]
    payload = dict(inherited); new = []
    for n in dict.fromkeys(names):
        h = sha(root/n)
        if n in payload: assert payload[n] == h, n
        else: payload[n] = h; new.append(n)
    requests = [r for r in parent['preregistration']['requests'] if r['name'] in scope['sample_names']]
    requests.sort(key=lambda r: scope['sample_names'].index(r['name']))
    cache = root/'.sync/p-reference-same-state-production-r1-generated'
    assert not cache.exists(); cache.mkdir()
    request = cache/'p-reference-requests.jsonl'
    request.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in requests))
    payload['p-reference-requests.jsonl'] = sha(request)
    c = {'card': scope['card'], 'run_id': scope['run_id'], 'scope_counts': scope['whole_scope_counts'],
        'flow_arms': {'FLOW_OFF': False, 'FLOW_ON': True}, 'candidate_variants': scope['candidate_variants'],
        'scope_ref': scope_ref, 'scope_sha256': sha(root/scope_ref),
        'cost_ref': cost_ref, 'cost_sha256': sha(root/cost_ref), 'forecast_complete_GPUh': complete/3600,
        'requests': requests, 'parent_stage': '.sync/wc-current-birth-full64-selected-cpu-r1-20261010',
        'parent_config_sha256': sha(root/parent_ref),
        'parent_import_source_sha256': {n: h for n, h in parent['payload_sha256'].items()
            if n.startswith('src/') and n.endswith('.py')},
        'sampling_CPU_capture_ref': proof_ref, 'sampling_CPU_capture_sha256': sha(root/proof_ref),
        'authorization_ref': authority, 'authorization_sha256': sha(root/authority),
        'automatic_single_job_GPUh': 8, 'cumulative_cap_GPUh': 77.89524658965853,
        'admission_fixture_budget': {'cap_gpu_hours': 77.89524658965853,
            'used_gpu_hours': 41.90868894585461, 'jobs_launched': 78},
        'admission_fixture_is_not_live_resource_observation_or_budget_reset': True,
        'working_epoch_strategy': scope['working_epoch_strategy'],
        'checkpoint_reserves': old_config['checkpoint_reserves'],
        'model_mode_contract_ref': mode, 'model_mode_contract_sha256': sha(root/mode),
        'required_stage_assets': {mode: sha(root/mode), mode_script: sha(root/mode_script)},
        'native_meta_CPU_receipt_ref': meta_ref,
        'native_meta_CPU_receipt_raw_sha256': old_config['native_meta_CPU_receipt_raw_sha256'],
        'continue_after_failure': 'STOP_RETAIN_COMPLETE_SCOPE', 'empty_cache_or_gate_bypass': False,
        'training': False, 'human_review': False, 'method_speed_or_quality_claim': False,
        'native_head_elision_combined': False, 'payload_sha256': payload,
        'GPU_execution_selected': False, 'gpu_uuid': None, 'production_CPU_receipt_sha256': None,
        'single_job_exception_authority': None}
    cfg_ref = 'configs/wc_p_reference_same_state_production_r1_20261011.json'
    assert not (root/cfg_ref).exists(); (root/cfg_ref).write_text(json.dumps(c, indent=2)+'\n')
    reg = {'identity': 'P_REFERENCE_COMPLETE_TWO_FLOW_ACTUAL_ENTRY_CPU_PREREGISTRATION_NOT_GPU',
        'config_ref': cfg_ref, 'config_sha256': sha(root/cfg_ref),
        'copies_readonly_sha256': inherited,
        'original_stage': '.sync/wc-p-reference-same-state-cpu-r3-20261011',
        'original_receipt_sha256': proof['originals']['receipt.json']['sha256'],
        'new_local_files': new, 'generated_requests_cache': str(request.relative_to(root)),
        'forecast_complete_GPUh': complete/3600, 'GPU_submissions': 0, 'ledger_written': False,
        'full_sampler_CPU_and_unchanged_native_meta_not_rerun': True,
        'E3_original_GPU_queue_has_priority': True}
    ref = root/'manifests/wc_p_reference_same_state_production_cpu_r1_preregistration_20261011.json'
    assert not ref.exists(); ref.write_text(json.dumps(reg, indent=2)+'\n')
    print(json.dumps({'status': reg['identity'], 'payload_files': len(payload),
        'forecast_complete_GPUh': complete/3600, 'GPU_submissions': 0}))


if __name__ == '__main__': main()
