"""Complete32 RA+A development card, actual prior and source-bound CPU admission.

Preparation and CPU checks permit a complete forecast above4. GPU selection
then needs direct authorization of this exact card; no subset can bypass it.
"""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from .cfg_ra_calibration_production import sha, binding, WC
from .cfg_ra_comparison_production_r2 import bound_prior as original_bound_prior

CARD = 'WC-RA-PLUS-A-FULL-VIDEO-R1-20261010-A'
RUN = 'wc-ra-plus-a-full-video-r1'
NAMES = ['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199',
         'misc_13398218_3840_2160_60fps', 'av_51b45829-502e-4143-9c32-c026bd6ab191']
METHODS = ['WC', 'JOINT_NATIVE', 'RA', 'W1_GLOBAL_1', 'BETA1_GLOBAL_1',
           'W1_ONE_PHASE', 'BETA1_ONE_PHASE']
COUNTS = {'requests': 4, 'complete_method_paths': 28, 'native_reference_slots': 4,
          'complete_paths': 32, 'maximum_videos': 32, 'solver_updates': 1152,
          'net_calls': 2304, 'maximum_guided_outputs': 1152,
          'maximum_final_latents': 32, 'maximum_fidelity_pairs': 28}
FINGERPRINT = '9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a'
THRESHOLD = 0.070744235098772
DESIGN = 'manifests/wc_ra_plus_a_complete_development_design_20261010.json'
PHASE = 'manifests/wc_a_single_phase_revision_design_20261010.json'


def validate_contract(c, stage):
    r = c['preregistration']
    if (r['card'] != CARD or r['run_id'] != RUN or r['scope_counts'] != COUNTS
            or r['methods'] != METHODS or r['repetitions'] != ['first']
            or r['branch_order'] != ['conditional', 'negative_prompt']
            or r['guided_weights'] != [8, -7] or r['state_steps'] != [13, 21, 33, 35, 36]
            or r['threshold_rule'] != 'PREREGISTERED_SINGLE_HALF_OF_ORIGINAL_D6_MEDIAN_AFTER_R1_DEVELOPMENT'
            or r['threshold_scale'] != .5 or r['parent_RA_threshold'] != 0.141488470197544
            or r['RA_threshold'] != THRESHOLD or r['calibration_fingerprint'] != FINGERPRINT
            or r['complete_development_design_ref'] != DESIGN
            or r['complete_development_design_sha256'] != sha(stage/DESIGN)
            or r['A_phase_design_ref'] != PHASE or r['A_phase_design_sha256'] != sha(stage/PHASE)
            or r['reference_policy'] != 'ORDINARY_NATIVE_MATCHED_INPUT_NO_REPLACEMENT'
            or r['clean_latency_claim'] or r['independent_confirmation_claim']
            or r['boundary_or_alpha_sweep'] or r['teacher_calls'] != 0
            or [x['name'] for x in r['requests']] != NAMES
            or c['execution_run_id'] != RUN or c['historical_wc_settings'] != WC
            or c['expected_real_components'] != 1216 or c['expected_real_shape'] != [1, 16, 24, 54, 96]
            or c['logical_copy_cap_bytes'] != 6*(1 << 30) or c['workspace_reserve_bytes'] != 4*(1 << 30)
            or c['paired_prefix_reserve_bytes'] != 4*(1 << 30)
            or c['cumulative_cap_GPUh'] != 77.89524658965853 or c['automatic_single_job_GPUh'] != 4
            or type(c['GPU_execution_selected']) is not bool
            or not math.isfinite(r['forecast']['forecast_complete_GPUh'])
            or not 0 < r['forecast']['forecast_complete_GPUh'] < 48
            or c['sampling_protocol']['actual_steps'] != 36 or c['sampling_protocol']['cfg_calls'] != 72
            or c['sampling_protocol']['timesteps'] != r['timesteps']):
        raise ValueError('Complete four-scene32 RA+A scope, fixed prior, phase or authority differs')
    for x in r['requests']:
        if (x['seed'] != 0 or x['guidance'] != 7 or x['num_steps'] != 35
                or x['num_output_frames'] != 93 or x['resolution'] != '432,768'):
            raise ValueError('Complete original four CAL requests required')
    actual = [json.loads(x) for x in (stage/'ra-plus-a-requests.jsonl').read_text().splitlines() if x]
    design = json.loads((stage/DESIGN).read_text())
    phase = json.loads((stage/PHASE).read_text())
    if (actual != r['requests'] or design['requests'] != actual or design['methods'] != METHODS
            or design['forecast_complete_GPUh'] != r['forecast']['forecast_complete_GPUh']
            or design['scope_counts'] != {k: COUNTS[k] for k in design['scope_counts']}
            or phase['prospective_candidates'] != r['A_candidates']
            or not phase['CFG_branches_share_alpha'] or phase['boundary_or_alpha_sweep']
            or phase['teacher_updates_deployment']
            or sha(stage/c['preregistration_ref']) != c['preregistration_sha256']
            or json.loads((stage/c['preregistration_ref']).read_text()) != r):
        raise ValueError('Full fixed development design, A candidates or registration changed')


def bound_prior(c, stage):
    # Preserve the actual eight-interval median reconstruction and original
    # quality-informed one-half revision. No new fit, threshold or Toy prior.
    prior, derived = original_bound_prior(c, stage)
    if prior.fingerprint != FINGERPRINT or derived['threshold'] != THRESHOLD:
        raise ValueError('Unchanged actual R2 prior required for all A paths')
    return prior, derived


def validate(project, stage):
    c = json.loads((stage/'ra-plus-a-config.json').read_text())
    validate_contract(c, stage)
    for name, digest in c['payload_sha256'].items():
        if sha(stage/name) != digest:
            raise ValueError('Complete RA+A payload changed: '+name)
    for name, digest in c['project_input_sha256'].items():
        if sha(project/name) != digest:
            raise ValueError('Original project input changed: '+name)
    for name, digest in c['runtime_source_sha256'].items():
        if sha(project/'runtime'/name) != digest:
            raise ValueError('Actual runtime changed: '+name)
    rows = [json.loads(x) for x in (project/'configs/cal_w1d8.jsonl').read_text().splitlines() if x]
    for request in c['preregistration']['requests']:
        if [r for r in rows if r['name'] == request['name']] != [request]:
            raise ValueError('Frozen four CAL original request differs')
    policy = json.loads((stage/'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json').read_text())
    window = json.loads((stage/'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json').read_text())
    if (policy['automatic_single_job_gpu_hours'] != 4 or policy['usage_reset']
            or not policy['legacy_per_card_seconds_caps_revoked'] or window['usage_reset']
            or not window['direct_user_authorization'] or window['authorized_remaining_gpu_hours'] != 48
            or window['new_cumulative_cap_gpu_hours'] != c['cumulative_cap_GPUh']
            or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours'] != c['cumulative_cap_GPUh']):
        raise ValueError('Current direct budget/autonomy authority differs')
    reg = json.loads((stage/c['batch_cpu_registration_ref']).read_text())
    if any(c['payload_sha256'].get(n) != v for n, v in reg['payload_sha256'].items()):
        raise ValueError('Complete A sampler CPU source changed')
    audit = json.loads((stage/c['batch_cpu_audit_ref']).read_text())
    if (audit['exit_code'] != 0 or not audit['independent_source_complete_results_and_actual_artifact_hashes_verified']
            or audit['GPU_submissions'] != 0 or audit['ledger_written']
            or len([x for x in audit['actual_CPU_artifacts'] if x['path'].endswith('.pt')]) != 126
            or len([x for x in audit['actual_CPU_artifacts'] if x['path'].endswith('.mp4')]) != 128):
        raise ValueError('Complete source-bound128-path sampler CPU proof missing')
    result = json.loads(gzip.decompress((stage/audit['files']['result.json']['local_path']).read_bytes()))
    if (result['status'] != 'A_DEPLOYMENT_COMPLETE_SAMPLING_CPU_NOT_REAL_MODEL'
            or result['payload_sha256'] != reg['payload_sha256'] or result['CUDA_initialized']
            or result['planned_scope'] != reg['CPU_scope']
            or (result['complete_executed_paths_including_last_writer_failures'], result['solver_updates'],
                result['net_calls'], result['actual_guided_tensors_reloaded'], result['actual_final_latents_reloaded'],
                result['semantic_mutation_refusals'], result['actual_truncation_refusals'],
                result['last_path_writer_failure_controls']) != (128, 4608, 9216, 2304, 64, 32, 2, 2)):
        raise ValueError('Full original A CPU results differ')
    cal = json.loads((stage/c['calibration_complete_audit_ref']).read_text())
    if (cal['GPU_exit_code'] != 0 or cal['CPU_exit_code'] != 0 or not cal['independent_checks']['success']
            or cal['independent_checks']['complete_CPU_reconstructed_real_table_fingerprint_verified'] != FINGERPRINT):
        raise ValueError('Complete real calibration proof required')
    for key, ref in [('runner', c['calibration_runner_ref']), ('calibration_table', c['calibration_table_ref'])]:
        item = cal['files'][key]; raw = gzip.decompress((stage/ref).read_bytes())
        if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Actual calibration bytes differ')
    bound_prior(c, stage)
    spec = importlib.util.spec_from_file_location('existing_resource_assets', stage/'scripts/run_wc_s0_profile.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.validate(project, stage, project/'runtime')
    return c, stage


def validate_selected(c, project, stage):
    if not c['GPU_execution_selected'] or c['gpu_uuid'] != 'GPU-cebf7119-cf03-23b9-e192-cd196332b704':
        raise ValueError('Complete current selected target required')
    authority = c['single_job_exception_authority']
    if c['preregistration']['forecast']['forecast_complete_GPUh'] > 4:
        if not isinstance(authority, dict) or sha(stage/authority['ref']) != authority['sha256']:
            raise ValueError('Above4 complete job needs exact direct human authorization')
        approved = json.loads((stage/authority['ref']).read_text())
        if (not approved['direct_user_authorization'] or approved['card'] != CARD or approved['run_id'] != RUN
                or approved['scope_counts'] != COUNTS
                or approved['preregistration_sha256'] != c['preregistration_sha256']
                or approved['forecast_complete_GPUh'] != c['preregistration']['forecast']['forecast_complete_GPUh']):
            raise ValueError('Authorization does not cover this complete32 card')
    elif authority is not None:
        raise ValueError('Within4 card must use current autonomous authority')
    path = project/c['production_cpu_stage']/'receipt.json'
    if sha(path) != c['production_cpu_receipt_sha256']:
        raise ValueError('Actual production CPU receipt differs')
    proof = json.loads(path.read_text())
    if (proof['exit_code'] != 0 or proof['status'] != 'REAL_RA_PLUS_A_PRODUCTION_CPU_PASS_NOT_GPU'
            or proof['CUDA_initialized'] or proof['GPU_submissions']
            or proof['config_binding_sha256'] != binding(c) or proof['payload_after_sha256'] != c['payload_sha256']):
        raise ValueError('Same-source complete32 production CPU proof missing')
    return proof
