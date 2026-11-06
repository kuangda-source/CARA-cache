"""Pinned real RA prior and complete six-method/two-reference card admission."""
import gzip
import importlib.util
import json
import math
from pathlib import Path

from .cfg_ra_calibration_production import sha, binding, WC

CARD = 'WC-RA-FULL-VIDEO-COMPARISON-R1-20261010-A'
RUN = 'wc-ra-full-video-comparison-r1'
NAMES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191_seed3', 'human_199_seed3']
COUNTS = {'requests': 2, 'complete_method_paths': 6, 'native_reference_slots': 2,
          'complete_paths': 8, 'maximum_videos': 8, 'solver_updates': 288,
          'net_calls': 576, 'maximum_guided_outputs': 288,
          'maximum_final_latents': 8, 'maximum_fidelity_pairs': 6}
FINGERPRINT = '9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a'
THRESHOLD = 0.141488470197544


def validate_contract(c, stage):
    r = c['preregistration']
    if (r['card'] != CARD or r['run_id'] != RUN or r['scope_counts'] != COUNTS
            or r['methods'] != ['WC', 'JOINT_NATIVE', 'RA'] or r['repetitions'] != ['first']
            or r['branch_order'] != ['conditional', 'negative_prompt'] or r['guided_weights'] != [8, -7]
            or r['state_steps'] != [13, 21, 33, 35, 36]
            or r['threshold_rule'] != 'MEDIAN_EIGHT_COMPLETE_SHARED_D6_INTERVAL_PAID_RISKS'
            or r['RA_threshold'] != THRESHOLD or r['calibration_fingerprint'] != FINGERPRINT
            or r['reference_policy'] != 'ORDINARY_NATIVE_MATCHED_INPUT_NO_REPLACEMENT'
            or r['clean_latency_claim'] or r['independent_confirmation_claim']
            or [x['name'] for x in r['requests']] != NAMES
            or c['execution_run_id'] != RUN or c['historical_wc_settings'] != WC
            or c['expected_real_components'] != 1216 or c['expected_real_shape'] != [1, 16, 24, 54, 96]
            or c['logical_copy_cap_bytes'] != 6*(1 << 30) or c['workspace_reserve_bytes'] != 4*(1 << 30)
            or c['paired_prefix_reserve_bytes'] != 4*(1 << 30)
            or c['cumulative_cap_GPUh'] != 77.89524658965853 or c['automatic_single_job_GPUh'] != 4
            or type(c['GPU_execution_selected']) is not bool
            or not math.isfinite(r['forecast']['forecast_complete_GPUh'])
            or not 0 < r['forecast']['forecast_complete_GPUh'] <= 4
            or c['sampling_protocol']['actual_steps'] != 36 or c['sampling_protocol']['cfg_calls'] != 72
            or c['sampling_protocol']['timesteps'] != r['timesteps']):
        raise ValueError('Complete RA video-comparison scope, prior or authority differs')
    for x in r['requests']:
        if (x['seed'] != 3 or x['guidance'] != 7 or x['num_steps'] != 35
                or x['num_output_frames'] != 93 or x['resolution'] != '432,768'):
            raise ValueError('Complete exposed two-request settings differ')
    actual = [json.loads(x) for x in (stage/'ra-comparison-requests.jsonl').read_text().splitlines() if x]
    if (actual != r['requests'] or sha(stage/c['preregistration_ref']) != c['preregistration_sha256']
            or json.loads((stage/c['preregistration_ref']).read_text()) != r):
        raise ValueError('Complete request or frozen comparison registration differs')


def bound_prior(c, stage):
    from .cfg_ra_calibration_table import load_table
    from .cfg_ra_baseline import threshold_from_collection
    table = json.loads(gzip.decompress((stage/c['calibration_table_ref']).read_bytes()))
    collection = json.loads(gzip.decompress((stage/c['calibration_runner_ref']).read_bytes()))
    prior = load_table(table, permit_toy=False)
    actual = threshold_from_collection(collection['batch'], prior)
    independent = json.loads((stage/c['independent_threshold_ref']).read_text())
    if (prior.fingerprint != FINGERPRINT or actual['rule'] != c['preregistration']['threshold_rule']
            or actual['threshold'] != independent['threshold'] or actual['threshold'] != THRESHOLD
            or actual['calibration_fingerprint'] != independent['calibration_fingerprint']
            or actual['endpoint_quality_used_to_choose_threshold']
            or len(actual['observed_intervals']) != 8):
        raise ValueError('Actual real-table threshold differs from independent reconstruction')
    return prior, actual


def validate(project, stage):
    c = json.loads((stage/'ra-comparison-config.json').read_text())
    validate_contract(c, stage)
    for name, digest in c['payload_sha256'].items():
        if sha(stage/name) != digest:
            raise ValueError('Complete comparison staged payload changed: '+name)
    for name, digest in c['project_input_sha256'].items():
        if sha(project/name) != digest:
            raise ValueError('Original project identity changed: '+name)
    for name, digest in c['runtime_source_sha256'].items():
        if sha(project/'runtime'/name) != digest:
            raise ValueError('Actual runtime source changed: '+name)
    rows = [json.loads(x) for x in (project/'configs/cal_w1d8.jsonl').read_text().splitlines() if x]
    for x in c['preregistration']['requests']:
        original = [r for r in rows if r['name'] == x['name'].removesuffix('_seed3')]
        if len(original) != 1 or {**original[0], 'name': x['name'], 'seed': 3} != x:
            raise ValueError('Frozen actual derived seed3 request differs')
    policy = json.loads((stage/'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json').read_text())
    window = json.loads((stage/'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json').read_text())
    if (policy['automatic_single_job_gpu_hours'] != 4 or policy['usage_reset']
            or not policy['legacy_per_card_seconds_caps_revoked'] or window['usage_reset']
            or not window['direct_user_authorization'] or window['authorized_remaining_gpu_hours'] != 48
            or window['new_cumulative_cap_gpu_hours'] != 77.89524658965853
            or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours'] != 77.89524658965853):
        raise ValueError('Direct current budget/autonomy authority differs')
    reg = json.loads((stage/c['batch_cpu_registration_ref']).read_text())
    if any(c['payload_sha256'].get(n) != v for n, v in reg['payload_sha256'].items()):
        raise ValueError('Full reference-composition CPU source changed')
    audit = json.loads((stage/c['batch_cpu_audit_ref']).read_text())
    expected = {'exit_code': 0, 'complete_executed_paths': 32, 'actual_guided_reloaded': 576,
                'actual_latents_reloaded': 16, 'semantic_mutation_refusals': 16,
                'actual_last_method_truncation_refusals': 2, 'last_writer_failure_controls': 2,
                'actual_retained_Toy_tensor_file_size_and_hash_bindings': 30}
    if (not audit['full_guarded_three_method_scope_reconstructed']
            or not audit['CPU_never_writes_ledger'] or any(audit[k] != v for k, v in expected.items())):
        raise ValueError('Complete actual eight-path composition CPU proof missing')
    cal = json.loads((stage/c['calibration_complete_audit_ref']).read_text())
    if (cal['GPU_exit_code'] != 0 or cal['CPU_exit_code'] != 0
            or not cal['independent_checks']['success']
            or cal['independent_checks']['actual_alias_path_bytes_and_sha_bindings_verified'] != 21
            or cal['independent_checks']['complete_CPU_reconstructed_real_table_fingerprint_verified'] != FINGERPRINT):
        raise ValueError('Complete real calibration proof missing')
    for key, ref in [('runner', c['calibration_runner_ref']), ('calibration_table', c['calibration_table_ref'])]:
        item = cal['files'][key]
        raw = gzip.decompress((stage/ref).read_bytes())
        import hashlib
        if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Bound actual calibration original bytes differ')
    spec = importlib.util.spec_from_file_location('existing_resource_assets', stage/'scripts/run_wc_s0_profile.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate(project, stage, project/'runtime')
    return c, stage


def validate_selected(c, project, stage):
    if (not c['GPU_execution_selected'] or c['gpu_uuid'] != 'GPU-cebf7119-cf03-23b9-e192-cd196332b704'
            or c['single_job_exception_authority'] is not None):
        raise ValueError('Fresh selected <=4GPUh complete comparison target required')
    path = project/c['production_cpu_stage']/'receipt.json'
    if sha(path) != c['production_cpu_receipt_sha256']:
        raise ValueError('Actual comparison production CPU receipt differs')
    proof = json.loads(path.read_text())
    if (proof['exit_code'] != 0 or proof['status'] != 'REAL_RA_COMPARISON_PRODUCTION_CPU_PASS_NOT_GPU'
            or proof['CUDA_initialized'] or proof['GPU_submissions']
            or proof['config_binding_sha256'] != binding(c) or proof['payload_after_sha256'] != c['payload_sha256']):
        raise ValueError('Same-source complete comparison production CPU proof missing')
    return proof
