"""A complete <=2h native-tail card; reuse unchanged R2 dependencies read-only."""
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path

from .rv0_execution import sha, digest_valid
from .rv0_native_onset_scope import CARD, RUN, validate_scope
from .rv0_placement_v2_execution import (PROJECT, AUTH24, POLICY, POLICY_TEXT, LIMITS,
    validate_stage as validate_previous_stage)

INFLIGHT = 'wc_w3_native_response_onset_inflight'
COUNTS = [1, 10, 6, 2]
CORE_FILES = ['src/wcomr/rv0_native_onset.py', 'src/wcomr/rv0_native_onset_scope.py',
    'src/wcomr/rv0_native_onset_causal.py', 'src/wcomr/rv0_native_onset_evaluation.py',
    'tests/check_rv0_native_onset_cpu.py', 'scripts/check_wc_w3_native_onset_core_cpu.py']
PRODUCTION_FILES = ['src/wcomr/rv0_native_onset_execution.py', 'src/wcomr/rv0_native_onset_scores.py',
    'scripts/run_wc_w3_native_response_onset.py', 'scripts/supervise_wc_w3_native_response_onset.py',
    'scripts/audit_wc_w3_native_response_onset_terminal.py', 'scripts/analyze_wc_w3_native_response_onset_lpips_cpu.py']


def validate_config(config, *, selected=False):
    validate_scope(config['scope'], config['preregistration'])
    recovery = config.get('technical_recovery')
    expected_run = RUN
    if recovery is not None:
        expected_run = 'wc-w3-native-response-onset-r2'
        if (recovery['original_run_id'] != RUN or recovery['new_run_id'] != expected_run
                or recovery['original_source_revision'] != 'cd2d9f324d4e2d9573614b81c97c1bc043049857'
                or recovery['failed_runner_original_sha256'] != '57a0e9b922fdf31413c075ee7e2b475507c4c00df549a385b7dc43bf66d492b8'
                or recovery['scope_counts'] != COUNTS or recovery['method_scope_unchanged'] is not True
                or recovery['failure_charge_retained'] is not True
                or config['payload_sha256'].get(config['technical_recovery_ref']) != config['technical_recovery_sha256']):
            raise ValueError('Exactly registered failed-entry recovery required')
    if (config['card'] != CARD or config['run_id'] != expected_run or config['sample_indices'] != [2]
            or config['sample_names'] != ['human_199'] or config['expected_project_root'] != PROJECT
            or config['execution_limits'] != LIMITS or config['logical_copy_cap_bytes'] != 6*1024**3
            or config['workspace_reserve_bytes'] != 4*1024**3 or config['execution_scope_authority'] is not None
            or config['production_entry_ready'] is not True or type(config['GPU_execution_selected']) is not bool):
        raise ValueError('Native-tail complete production identity/limits differ')
    payload = config['payload_sha256']
    if (not set(CORE_FILES+PRODUCTION_FILES).issubset(payload)
            or any(not digest_valid(d) for d in payload.values())
            or any(payload.get(n) != d for n, d in config['core_cpu_payload_sha256'].items())
            or set(config['core_cpu_payload_sha256']) != set(CORE_FILES)
            or any(not digest_valid(config[k]) for k in ['preregistration_sha256', 'base_config_sha256',
                'core_cpu_receipt_sha256', 'core_cpu_attempts_sha256', 'core_cpu_audit_sha256',
                'prior_score_sha256', 'prior_GPU_receipt_sha256', 'cost_sha256'])
            or config['prior_score_sha256'] != config['preregistration']['trigger_evidence']['prior_score_sha256']):
        raise ValueError('Native-tail source/actual CPU/prior result closure incomplete')
    policy = config['execution_policy_authority']
    if (policy['approval_ref'] != POLICY or policy['source_user_text'] != POLICY_TEXT
            or policy['automatic_single_job_gpu_hours'] != 2 or policy['cumulative_cap_gpu_hours'] != 24
            or policy['legacy_per_card_seconds_caps_revoked'] is not True or policy['usage_reset'] is not False
            or payload.get(POLICY) != policy['approval_sha256']):
        raise ValueError('Latest direct autonomous execution policy required')
    cost = config['cost']
    if (cost != config['preregistration']['cost_forecast']
            or not 0 < cost['nominal_proxy_seconds'] < cost['complete_forecast_seconds'] <= 7200
            or not math.isfinite(cost['complete_forecast_seconds'])
            or cost['complete_forecast_gpu_hours'] != cost['complete_forecast_seconds']/3600
            or cost['estimate_not_deadline_or_bound'] is not True):
        raise ValueError('Complete registered <=2h cost estimate required; never split controls')
    reference = config['references']
    if (set(reference) != {'human_199'} or set(reference['human_199']) !=
            {'Native35','official_WC','FIXED61','LATE69','timesteps','model_and_condition_context'}):
        raise ValueError('All four frozen Human references required')
    for kind, item in config['preregistration']['historical_encoded_references'].items():
        if reference['human_199'][kind] != item or not digest_valid(item['sha256']):
            raise ValueError('Registered historical reference changed: '+kind)
    if selected or config['GPU_execution_selected']:
        if (config['GPU_execution_selected'] is not True or config['gpu_uuid'] !=
                'GPU-cebf7119-cf03-23b9-e192-cd196332b704'
                or not digest_valid(config['production_cpu_receipt_sha256'])):
            raise ValueError('Actual new production CPU proof and selected GPU required')
        proof = config['production_cpu_payload_sha256']
        if (set(proof) != set(payload)|{'onset-config.json'} or any(payload[n] != proof[n] for n in payload)
                or any(not digest_valid(d) for d in proof.values())):
            raise ValueError('Selected code must exactly match its new actual CPU payload')
    elif config.get('gpu_uuid') is not None:
        raise ValueError('Unselected native-tail draft cannot preclaim GPU')
    return {'status':'NATIVE_RESPONSE_ONSET_PRODUCTION_CONTRACT_PASS_NOT_GPU', 'scope_counts':COUNTS,
            'selected':config['GPU_execution_selected'], 'old_scope_not_rerun':True}


def validate_stage(project, stage, runtime, config, *, selected=False):
    validate_config(config, selected=selected)
    if (project.resolve() != Path(PROJECT).resolve() or runtime.resolve() != (project/'runtime').resolve()
            or not stage.resolve().is_relative_to((project/'.sync').resolve())):
        raise ValueError('Existing canonical root/runtime/independent stage required')
    for name, digest in config['payload_sha256'].items():
        if sha(stage/name) != digest:
            raise ValueError('Frozen native-tail payload changed: '+name)
    base_path = stage/'placement-config.json'
    if sha(base_path) != config['base_config_sha256']:
        raise ValueError('Original executed R2 configuration changed')
    base = json.loads(base_path.read_text())
    previous = validate_previous_stage(project, stage, runtime, base, selected=True)
    if config['historical_wc_settings'] != base['historical_wc_settings'] or config['f1_setup_sha256'] != base['f1_setup_sha256']:
        raise ValueError('Original model/WC settings changed')
    for name in ('model_and_condition_context', 'timesteps', 'Native35', 'official_WC'):
        if config['references']['human_199'][name] != base['references']['human_199'][name]:
            raise ValueError('Original Human input/model/sampler binding changed')
    prereg = stage/config['preregistration_ref']
    if sha(prereg) != config['preregistration_sha256'] or json.loads(prereg.read_text()) != config['preregistration']:
        raise ValueError('Prospective native-tail hypothesis changed')
    if config.get('technical_recovery') is not None:
        recovery = stage/config['technical_recovery_ref']
        if (sha(recovery) != config['technical_recovery_sha256']
                or json.loads(recovery.read_text()) != config['technical_recovery']):
            raise ValueError('Technical recovery preregistration changed')
    cost = stage/config['cost_ref']
    if sha(cost) != config['cost_sha256'] or json.loads(cost.read_text()) != config['cost']:
        raise ValueError('Complete preregistered cost changed')
    original = project/config['core_cpu_stage']/'receipt.json'
    attempts = project/config['core_cpu_stage']/'attempts.json'
    if (sha(original) != config['core_cpu_receipt_sha256']
            or sha(attempts) != config['core_cpu_attempts_sha256']):
        raise ValueError('Actual affected core CPU receipt/raw attempts changed')
    core = json.loads(original.read_text()); audit = json.loads((stage/config['core_cpu_audit_ref']).read_text())
    if (sha(stage/config['core_cpu_audit_ref']) != config['core_cpu_audit_sha256']
            or core['status'] != 'NATIVE_RESPONSE_ONSET_ACTUAL_AFFECTED_CORE_CPU_PASS_NOT_PRODUCTION_OR_GPU'
            or core['exit_code'] != 0 or core['CUDA_initialized'] is not False or core['GPU_submissions'] != 0
            or core['budget_unchanged'] is not True or any(config['core_cpu_payload_sha256'].get(n) != d for n,d in core['payload_sha256'].items())
            or core['payload_sha256'] != core['new_payload_after_sha256']
            or core['base_payload_sha256'] != core['base_payload_after_sha256']
            or core['upstream_sha256'] != core['upstream_after_sha256']
            or core['counts'] != [3,30,18] or core['response_changes'] != 24 or core['mutation_refusals'] != 60
            or core['new_and_reused_counts'].get('new_complete_CPU_parents') != 2
            or core['new_and_reused_counts'].get('reused_complete_CPU_parents') != 1
            or audit['core_payload_sha256'] != config['core_cpu_payload_sha256']
            or audit['status'] != 'NATIVE_RESPONSE_ONSET_ACTUAL_CORE_RAW_SHA_REPEATS_RESPONSE_AND_FAILURE_AUDIT_PASS_NOT_GPU'
            or audit['server_receipt_sha256'] != config['core_cpu_receipt_sha256']):
        raise ValueError('Actual core/source/raw response controls failed')
    for name in CORE_FILES:
        if sha(project/config['core_cpu_stage']/name) != config['core_cpu_payload_sha256'][name]:
            raise ValueError('Actually executed core source changed: '+name)
    for name, digest in [(config['prior_score_ref'], config['prior_score_sha256']),
                         (config['prior_GPU_receipt_ref'], config['prior_GPU_receipt_sha256'])]:
        if sha(stage/name) != digest:
            raise ValueError('Frozen R2 scoring/trajectory artifact changed')
    prior_raw = gzip.decompress((stage/config['prior_GPU_receipt_ref']).read_bytes())
    if hashlib.sha256(prior_raw).hexdigest() != config['preregistration']['trigger_evidence']['runner_original_sha256']:
        raise ValueError('Frozen preceding real GPU original bytes differ')
    for item in config['preregistration']['historical_encoded_references'].values():
        path = Path(item['path'])
        if path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise ValueError('Registered real reference video changed')
    if selected:
        original = project/config['production_cpu_stage']/'receipt.json'
        if sha(original) != config['production_cpu_receipt_sha256']:
            raise ValueError('New production CPU receipt changed')
        production = json.loads(original.read_text())
        if (production['status'] != 'NATIVE_RESPONSE_ONSET_ACTUAL_PRODUCTION_CPU_SOURCE_ASSETS_IMPORT_PASS_NOT_GPU'
                or production['exit_code'] != 0 or production['CUDA_initialized'] is not False
                or production['budget_unchanged'] is not True or production['GPU_submissions'] != 0
                or production['payload_sha256'] != config['production_cpu_payload_sha256']):
            raise ValueError('New actual production CPU validation failed')
    return {'status':'NATIVE_RESPONSE_ONSET_REAL_SOURCE_DEPENDENCIES_CORE_REFERENCES_PASS_NO_TORCH',
            'previous_dependency_status':previous['status'], 'new_GPU_authorization_verified':selected}


def admission_budget(budget, config):
    validate_config(config, selected=True)
    used = budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours') != 24 or budget.get('budget_authorization_ref') != AUTH24
            or type(used) not in (int,float) or not math.isfinite(used) or not 0 <= used < 24
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Existing24 budget/usage/inflight differs')
    required = config['cost']['complete_forecast_seconds']+LIMITS['cleanup_budget_headroom_seconds']
    if (24-used)*3600 < required:
        raise ValueError('Complete native-tail job exceeds remaining cumulative budget')
    return {'fits':True, 'required_seconds':required, 'remaining_seconds':(24-used)*3600}


def reserve_budget(budget, config, supervisor_pid):
    admission_budget(budget, config)
    if type(supervisor_pid) is not int or supervisor_pid <= 0:
        raise ValueError('Actual durable supervisor PID required')
    result = copy.deepcopy(budget); result['used_gpu_hours'] = 24
    result['gpu_jobs_launched'] += 1
    result['status'] = 'WC_W3_NATIVE_RESPONSE_ONSET_RUNNING_RESERVED_NOT_ACTUAL_SPENT'
    result[INFLIGHT] = {'run_id':config['run_id'], 'supervisor_pid':supervisor_pid,
                       'reserved_seconds':(24-budget['used_gpu_hours'])*3600}
    return result


def settle_budget(current, before, config, wall_seconds, supervisor_pid):
    if (type(wall_seconds) not in (int,float) or not math.isfinite(wall_seconds) or wall_seconds <= 0
            or current != reserve_budget(before, config, supervisor_pid)):
        raise ValueError('Actual inclusive cost and unchanged native-tail reservation required')
    result = copy.deepcopy(current)
    result['used_gpu_hours'] = before['used_gpu_hours']+wall_seconds/3600
    result.pop(INFLIGHT); result['status'] = 'WC_W3_NATIVE_RESPONSE_ONSET_SETTLED_REQUIRES_RESULT_AUDIT'
    return result


def audit_settlement(supervisor, receipt, config, live_budget, expected_source):
    validate_config(config, selected=True)
    if (supervisor['status'] != 'EXITED_REQUIRES_RESULT_AUDIT' or supervisor['exit_code'] != 0
            or supervisor['source_revision'] != receipt['source_revision'] or receipt['source_revision'] != expected_source
            or supervisor['run_id'] != config['run_id'] or supervisor['config'] != config
            or not 0 < supervisor['wall_seconds'] <= min(7200, supervisor['reserved_seconds'])
            or supervisor['cumulative_budget_exceeded'] is not False
            or [supervisor['planned_parent_phases'],supervisor['planned_suffix_controls'],supervisor['planned_encoded_outputs']] != COUNTS[:3]
            or live_budget != supervisor['budget_after'] or live_budget['used_gpu_hours'] > 24
            or any(k.endswith('_inflight') for k in live_budget)):
        raise ValueError('Native-tail terminal source/scope/cost/cap differs')
    expected = settle_budget(reserve_budget(supervisor['budget_before'],config,supervisor['pid']),
        supervisor['budget_before'],config,supervisor['wall_seconds'],supervisor['pid'])
    pids = [supervisor['pid'],supervisor['child_pid']]
    if expected != live_budget or len(set(pids)) != 2 or receipt['pid'] != supervisor['child_pid']:
        raise ValueError('Native-tail actual settlement or direct child identity differs')
    return pids
