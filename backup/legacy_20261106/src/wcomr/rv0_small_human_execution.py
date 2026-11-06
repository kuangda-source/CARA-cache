"""Independent missing-Human production provenance and actual-cost contracts."""
import copy
import json
import math
from pathlib import Path

from .rv0_execution import sha, digest_valid
from .rv0_small_execution import validate_stage as validate_original_dependencies
from .rv0_small_human_scope import validate_scope

PROJECT = '/home/gaokuangda/data/gkd/worldcache_omr'
AUTH24 = 'manifests/budget_authorization_20261005_wc_24gpuh.json'
TEXT24 = '批准 WC-W3-SMALL-CD-R1-20261004-A，把累计 gpuh 限制提升到 24'
APPROVAL = 'manifests/wc_w3_small_human_gpu_authorization_20261005.json'
INFLIGHT = 'wc_w3_small_human_complement_inflight'


def validate_config(config, *, selected=False):
    validate_scope(config['scope'])
    for name in ('card', 'run_id', 'sample_names', 'sample_indices', 'target_calls',
                 'maximum_age_solver_steps', 'logical_copy_cap_bytes', 'workspace_reserve_bytes'):
        expected = config['scope'][name]
        if type(config.get(name)) is not type(expected) or config[name] != expected:
            raise ValueError('Human production scope alias differs: '+name)
    if config.get('expected_project_root') != PROJECT or config.get('production_entry_ready') is not True:
        raise ValueError('Human real project root and complete production entry required')
    required = {'src/wcomr/rv0_small_human_causal.py', 'src/wcomr/rv0_small_human_scope.py',
                'src/wcomr/rv0_small_human_execution.py', 'src/wcomr/rv0_small_human_evaluation.py',
                'src/wcomr/rv0_small_partial.py', 'scripts/run_wc_w3_small_human.py',
                'scripts/supervise_wc_w3_small_human.py', 'scripts/audit_wc_w3_small_human_terminal.py',
                'scripts/analyze_wc_w3_small_human_lpips_cpu.py'}
    payload = config['payload_sha256']; core = config['human_core_payload_sha256']
    if (not required.issubset(payload) or len(core) != 96
            or any(payload.get(n) != d for n, d in core.items())
            or not all(digest_valid(d) for d in payload.values())
            or len(config['upstream_source_sha256']) != 9
            or not all(digest_valid(d) for d in config['upstream_source_sha256'].values())
            or any(not digest_valid(config.get(n)) for n in [
                'base_config_sha256', 'human_core_receipt_sha256', 'lpips_resource_receipt_sha256',
                'cal_config_sha256', 'f1_setup_sha256'])):
        raise ValueError('Human production/frozen actual CPU source closure incomplete')
    if set(config['references']) != {'human_199'}:
        raise ValueError('Only the original missing Human reference is allowed')
    reference = config['references']['human_199']
    if (reference['model_and_condition_context'][0] != 'Cosmos-Predict2.5-2B:'+config['f1_setup_sha256']
            or not digest_valid(reference['model_and_condition_context'][1]) or len(reference['timesteps']) != 36):
        raise ValueError('Human historical model/input/sampler identity differs')
    for kind in ['Native35', 'official_WC']:
        item = reference[kind]
        if (not digest_valid(item['sha256']) or type(item['bytes']) is not int or item['bytes'] <= 0
                or not Path(item['path']).is_relative_to(Path(PROJECT)/'outputs/wc-fair-cal-r1')):
            raise ValueError('Human matched historical video source differs')
    cost = config['cost']
    if (cost['proxies_are_hard_bounds'] is not False or cost['actual_Human_CD_future_cost_measured'] is not False
            or not 0 < cost['nominal_complete_seconds'] < cost['stress_proxy_seconds'] < 4500
            or cost['proposed_total_cap_seconds'] != 4500 or cost['proposed_child_cap_seconds'] != 4470):
        raise ValueError('Human complete cost or uncertainty differs')
    if type(config.get('GPU_execution_selected')) is not bool:
        raise ValueError('Human GPU decision must be explicit')
    binding = config.get('execution_scope_authority')
    if binding is not None:
        expected = {'approval_ref': APPROVAL, 'approved_card': config['card'], 'run_id': config['run_id'],
                    'single_run_inclusive_cap_seconds': 4500, 'usage_reset': False}
        if (set(binding) != set(expected) | {'approval_sha256', 'source_user_text'}
                or any(type(binding.get(k)) is not type(v) or binding[k] != v for k, v in expected.items())
                or not digest_valid(binding['approval_sha256'])
                or payload.get(APPROVAL) != binding['approval_sha256']
                or type(binding['source_user_text']) is not str or not binding['source_user_text'].strip()):
            raise ValueError('Human distinct single-card scope authority changed')
    if selected:
        if (binding is None or config['GPU_execution_selected'] is not True
                or type(config.get('gpu_uuid')) is not str or not config['gpu_uuid'].startswith('GPU-')):
            raise ValueError('Human card needs distinct human scope approval and selected UUID')
        production = config.get('production_cpu_payload_sha256', {})
        if (not digest_valid(config.get('production_cpu_receipt_sha256'))
                or type(config.get('production_cpu_stage')) is not str
                or not Path(config['production_cpu_stage']).is_relative_to(Path('.sync'))
                or len(production) != 109 or not all(digest_valid(d) for d in production.values())
                or any(payload.get(n) != d for n, d in production.items() if n != 'human-config.json')):
            raise ValueError('Human GPU execution needs unchanged actual production CPU source proof')
    elif config['GPU_execution_selected'] is False and config.get('gpu_uuid') is not None:
        raise ValueError('Unselected Human draft cannot preclaim GPU')
    return {'status': 'HUMAN_PRODUCTION_DRAFT_CONTRACT_PASS_NOT_GPU',
            'parents': 1, 'suffixes': 6, 'new_outputs': 4, 'science_pairs': 1,
            'selected': config['GPU_execution_selected'], 'original_failed_denominator': [2, 12, 8, 2]}


def validate_preparation(stage, config):
    records = {}
    for name, binding in config['preparation_audits'].items():
        path = stage/binding['path']
        if not digest_valid(binding['sha256']) or sha(path) != binding['sha256']:
            raise ValueError('Human actual preparation audit changed: '+name)
        records[name] = json.loads(path.read_text())
    core, metric = records['human_core'], records['lpips_resource']
    if (core['status'] != 'HUMAN_COMPLEMENT_ACTUAL_CPU_ORIGINAL_NATIVE_HASH_AND_STRICT_ROWS_PASS_NOT_GPU'
            or core['server_receipt_sha256'] != config['human_core_receipt_sha256']
            or (core['strict_complete_CPU_parents'], core['complete_CPU_suffixes'], core['mock_outputs_not_real_video']) != (2, 12, 8)
            or core['failure_cases_retained'] != ['child_writer', 'child_guardrail', 'historical_bridge']
            or core['new_scope'] != [1, 6, 4, 1] or core['original_failed_scope'] != [2, 12, 8, 2]
            or core['budget_unchanged'] is not True or core['CUDA_initialized'] is not False or core['GPU_submissions'] != 0):
        raise ValueError('Human actual CPU strict scope and failed controls incomplete')
    if (metric['status'] != 'LPIPS_ISOLATED_RESOURCE_ORIGINAL_CPU_AUDIT_PASS_NOT_VIDEO_SCORE'
            or metric['server_receipt_sha256'] != config['lpips_resource_receipt_sha256']
            or metric['source_sha256'] != config['payload_sha256']['src/wcomr/rv0_lpips.py']):
        raise ValueError('Frozen isolated full-frame metric resource differs')
    return records


def validate_stage(project, stage, runtime, config, *, selected=False):
    validate_config(config, selected=selected)
    if (project.resolve() != Path(PROJECT).resolve() or runtime.resolve() != (project/'runtime').resolve()
            or not stage.resolve().is_relative_to((project/'.sync').resolve())):
        raise ValueError('Human ledger/lock must use the existing real project root')
    for name, digest in config['payload_sha256'].items():
        if sha(stage/name) != digest:
            raise ValueError('Human frozen production source changed: '+name)
    base_path = stage/'small-config.json'
    if sha(base_path) != config['base_config_sha256']:
        raise ValueError('Frozen original dependency config changed')
    base = json.loads(base_path.read_text())
    # This audits proven dependencies only; its old approval never authorizes this new card.
    dependencies = validate_original_dependencies(project, stage, runtime, base)
    if (config['upstream_source_sha256'] != base['upstream_source_sha256']
            or config['historical_wc_settings'] != base['historical_wc_settings']
            or config['references']['human_199'] != base['references']['human_199']
            or config['cal_config_sha256'] != base['cal_config_sha256']
            or config['f1_setup_sha256'] != base['f1_setup_sha256']):
        raise ValueError('Human original reference/model/settings binding differs')
    original = project/config['human_core_stage']/'receipt.json'
    if sha(original) != config['human_core_receipt_sha256']:
        raise ValueError('Actual Human CPU original changed')
    raw = json.loads(original.read_text())
    if (raw['status'] != 'HUMAN_COMPLEMENT_ACTUAL_CPU_PASS_NOT_PRODUCTION_OR_GPU'
            or raw['exit_code'] != 0 or raw['payload_sha256'] != config['human_core_payload_sha256']
            or raw['upstream_sha256'] != config['upstream_source_sha256']
            or raw['CUDA_initialized'] is not False or raw['budget_unchanged'] is not True or raw['GPU_submissions'] != 0):
        raise ValueError('Actual Human CPU provenance failed')
    records = validate_preparation(stage, config)
    budget = json.loads((project/'reports/budget.json').read_text())
    auth_path = project/AUTH24
    if (budget['cap_gpu_hours'] != 24 or budget['budget_authorization_ref'] != AUTH24
            or sha(auth_path) != config['payload_sha256'][AUTH24]):
        raise ValueError('Cumulative24 budget authority changed')
    auth = json.loads(auth_path.read_text())
    if auth['source_user_text'] != TEXT24 or auth['usage_reset'] is not False or auth['cumulative_cap_gpu_hours'] != 24:
        raise ValueError('Cumulative24 direct authority differs')
    if selected:
        original = project/config['production_cpu_stage']/'receipt.json'
        if not original.resolve().is_relative_to((project/'.sync').resolve()) or sha(original) != config['production_cpu_receipt_sha256']:
            raise ValueError('Human actual production CPU original changed')
        production = json.loads(original.read_text())
        if (production['status'] != 'HUMAN_PRODUCTION_ACTUAL_CPU_SOURCE_ASSETS_IMPORT_PASS_NOT_GPU'
                or production['exit_code'] != 0 or production['CUDA_initialized'] is not False
                or production['budget_unchanged'] is not True or production['GPU_submissions'] != 0
                or production['payload_sha256'] != config['production_cpu_payload_sha256']
                or production['upstream_sha256'] != config['upstream_source_sha256']):
            raise ValueError('Human actual production CPU evidence failed')
        binding = config['execution_scope_authority']; path = stage/APPROVAL
        if sha(path) != binding['approval_sha256']:
            raise ValueError('Distinct Human GPU approval original missing/changed')
        approval = json.loads(path.read_text())
        expected = {k: v for k, v in binding.items() if k not in {'approval_ref', 'approval_sha256'}}
        if approval != expected:
            raise ValueError('Distinct Human GPU approval scope differs')
    return {'status': 'HUMAN_REAL_ROOT_DEPENDENCIES_CPU_SOURCE_REFERENCES_PASS_NO_TORCH',
            'audits': {k: v['status'] for k, v in records.items()},
            'base_dependency_status': dependencies['status'], 'budget_snapshot': budget,
            'new_GPU_authorization_verified': selected}


def admission_budget(budget, config):
    validate_config(config, selected=True)
    used = budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours') != 24 or budget.get('budget_authorization_ref') != AUTH24
            or type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= 24
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Authorized24 usage/reference/inflight differs')
    remaining = (24-used)*3600; required = 4515
    if remaining < required:
        raise ValueError('Complete Human cap and admission exceed budget')
    return {'fits': True, 'remaining_seconds': remaining, 'required_seconds': required,
            'remaining_if_full_cap_spent': remaining-required, 'GPU_selected': True}


def reserve_budget(budget, config, supervisor_pid):
    admission_budget(budget, config)
    if type(supervisor_pid) is not int or supervisor_pid <= 0:
        raise ValueError('Human durable supervisor PID required')
    result = copy.deepcopy(budget); result['used_gpu_hours'] += 4500/3600
    result['gpu_jobs_launched'] += 1
    result['status'] = 'WC_W3_SMALL_HUMAN_RUNNING_4500S_PREPAID_NOT_ACTUAL_SETTLED'
    result[INFLIGHT] = {'run_id': config['run_id'], 'supervisor_pid': supervisor_pid, 'reserved_seconds': 4500}
    return result


def settle_budget(current, before, config, wall_seconds, supervisor_pid):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0:
        raise ValueError('Human actual inclusive failure/flush/release cost required')
    if current != reserve_budget(before, config, supervisor_pid):
        raise ValueError('Human live reservation changed; do not overwrite ledger')
    result = copy.deepcopy(current); result['used_gpu_hours'] = before['used_gpu_hours']+wall_seconds/3600
    result.pop(INFLIGHT); result['status'] = 'WC_W3_SMALL_HUMAN_SETTLED_REQUIRES_RESULT_AUDIT'
    return result


def audit_settlement(supervisor, receipt, config, live_budget, expected_source):
    validate_config(config, selected=True)
    if (supervisor['status'] != 'EXITED_REQUIRES_RESULT_AUDIT' or supervisor['exit_code'] != 0
            or supervisor['source_revision'] != receipt['source_revision'] or receipt['source_revision'] != expected_source
            or supervisor['run_id'] != config['run_id'] or supervisor['config'] != config
            or supervisor['reserved_seconds'] != 4500 or supervisor['hard_wall_cap_exceeded'] is not False
            or not 0 < supervisor['wall_seconds'] <= 4500
            or (supervisor['planned_parent_phases'], supervisor['planned_suffix_controls'], supervisor['planned_encoded_outputs']) != (1, 6, 4)
            or live_budget != supervisor['budget_after'] or any(k.endswith('_inflight') for k in live_budget)
            or live_budget['cap_gpu_hours'] != 24 or live_budget['used_gpu_hours'] > 24):
        raise ValueError('Human terminal identity, scope, cap or live settlement differs')
    prepaid = reserve_budget(supervisor['budget_before'], config, supervisor['pid'])
    if settle_budget(prepaid, supervisor['budget_before'], config, supervisor['wall_seconds'], supervisor['pid']) != live_budget:
        raise ValueError('Human terminal actual-cost reconstruction differs')
    pids = [supervisor['pid'], supervisor['child_pid'], receipt['pid']]
    if any(type(pid) is not int or pid <= 0 for pid in pids) or len(set(pids)) != 3:
        raise ValueError('Three distinct Human supervisor/timeout/runner PIDs required')
    return pids
