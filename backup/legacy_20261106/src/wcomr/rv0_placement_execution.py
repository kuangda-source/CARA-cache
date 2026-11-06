"""Complete placement production provenance, separate authority and actual cost."""
import copy
import json
import math
from pathlib import Path

from .rv0_execution import sha, digest_valid
from .rv0_small_execution import validate_stage as validate_original_dependencies
from .rv0_placement_evaluation import validate_frozen_scope

PROJECT = '/home/gaokuangda/data/gkd/worldcache_omr'
AUTH24 = 'manifests/budget_authorization_20261005_wc_24gpuh.json'
TEXT24 = '批准 WC-W3-SMALL-CD-R1-20261004-A，把累计 gpuh 限制提升到 24'
APPROVAL = 'manifests/wc_w3_placement_gt2h_authorization_20261007.json'
POLICY = 'manifests/wc_execution_autonomy_authorization_20261007.json'
POLICY_TEXT = '取消这些时间限制，只有单次 gpuh 超过 2h 的才停下来询问，其他直接推进即可'
INFLIGHT = 'wc_w3_placement_swap_inflight'
LIMITS = {'kill_grace_seconds': 5, 'monitor_interval_seconds': 2,
          'cleanup_budget_headroom_seconds': 30, 'minimum_disk_free_bytes': 12*1024**3}
COUNTS = [2, 16, 10, 4]


def validate_config(config, *, selected=False):
    validate_frozen_scope(config['scope'])
    scope = config['scope']
    expected = {'card': scope['card'], 'run_id': scope['run_id'],
                'sample_indices': scope['sample_indices'],
                'sample_names': [s['scene'] for s in scope['scenes']],
                'maximum_age_solver_steps': 33, 'logical_copy_cap_bytes': 6*1024**3,
                'workspace_reserve_bytes': 4*1024**3}
    if any(type(config.get(k)) is not type(v) or config[k] != v for k, v in expected.items()):
        raise ValueError('Placement complete scope alias/copy capacity differs')
    if (config.get('expected_project_root') != PROJECT or config.get('production_entry_ready') is not True
            or config.get('execution_limits') != LIMITS
            or any(type(config['execution_limits'][k]) is not int for k in LIMITS)):
        raise ValueError('Placement complete production root/limits differ')
    required = {'src/wcomr/rv0_placement_causal.py', 'src/wcomr/rv0_placement_execution.py',
        'src/wcomr/rv0_placement_evaluation.py', 'src/wcomr/rv0_placement_scores.py',
        'scripts/run_wc_w3_placement.py', 'scripts/supervise_wc_w3_placement.py',
        'scripts/audit_wc_w3_placement_terminal.py', 'scripts/analyze_wc_w3_placement_lpips_cpu.py'}
    payload, core = config['payload_sha256'], config['placement_core_payload_sha256']
    if (len(core) != 117 or not required.issubset(payload)
            or any(payload.get(k) != v for k, v in core.items())
            or not all(digest_valid(d) for d in payload.values())
            or len(config['upstream_source_sha256']) != 9
            or not all(digest_valid(d) for d in config['upstream_source_sha256'].values())
            or any(not digest_valid(config.get(k)) for k in ['base_config_sha256',
                'placement_core_receipt_sha256', 'lpips_resource_receipt_sha256',
                'cal_config_sha256', 'f1_setup_sha256', 'preregistered_scope_sha256', 'cost_report_sha256'])):
        raise ValueError('Placement actual CPU/source/resource closure incomplete')
    if set(config['references']) != set(expected['sample_names']):
        raise ValueError('Both original placement Native/WC references required')
    for reference in config['references'].values():
        if (reference['model_and_condition_context'][0] != 'Cosmos-Predict2.5-2B:'+config['f1_setup_sha256']
                or not digest_valid(reference['model_and_condition_context'][1]) or len(reference['timesteps']) != 36):
            raise ValueError('Placement historical model/input/sampler identity differs')
        for kind in ['Native35', 'official_WC']:
            item = reference[kind]
            if (not digest_valid(item['sha256']) or type(item['bytes']) is not int or item['bytes'] <= 0
                    or not Path(item['path']).is_relative_to(Path(PROJECT)/'outputs/wc-fair-cal-r1')):
                raise ValueError('Placement historical video identity differs')
    cost = config['cost']
    if (cost['proxies_are_hard_bounds'] is not False or cost['fixed_mask_GPU_legality_and_cost_measured'] is not False
            or not 0 < cost['complete_nominal_proxy_seconds'] < cost['complete_planning_proxy_seconds']
            or not math.isfinite(cost['complete_planning_proxy_seconds'])):
        raise ValueError('Placement complete cost proxy/uncertainty differs')
    if type(config.get('GPU_execution_selected')) is not bool:
        raise ValueError('Placement GPU decision must be explicit')
    policy = config.get('execution_policy_authority', {})
    expected_policy = {'approval_ref': POLICY, 'source_user_text': POLICY_TEXT,
        'automatic_single_job_gpu_hours': 2, 'legacy_per_card_seconds_caps_revoked': True,
        'cumulative_cap_gpu_hours': 24, 'usage_reset': False}
    if (set(policy) != set(expected_policy) | {'approval_sha256'}
            or any(type(policy.get(k)) is not type(v) or policy[k] != v for k, v in expected_policy.items())
            or not digest_valid(policy['approval_sha256']) or payload.get(POLICY) != policy['approval_sha256']):
        raise ValueError('Latest direct execution autonomy policy required')
    binding = config.get('execution_scope_authority')
    if binding is not None:
        approved = {'approval_ref': APPROVAL, 'approved_card': config['card'], 'run_id': config['run_id'],
            'allow_single_job_above_2_gpu_hours': True, 'legacy_seconds_caps_revoked': True,
            'planning_proxy_seconds': cost['complete_planning_proxy_seconds'],
            'science_counts': COUNTS, 'usage_reset': False}
        if (set(binding) != set(approved) | {'approval_sha256', 'source_user_text'}
                or any(type(binding.get(k)) is not type(v) or binding[k] != v for k, v in approved.items())
                or not digest_valid(binding['approval_sha256']) or payload.get(APPROVAL) != binding['approval_sha256']
                or type(binding['source_user_text']) is not str or not binding['source_user_text'].strip()):
            raise ValueError('Above-2h complete-card exception authority changed')
    if selected:
        if (config['GPU_execution_selected'] is not True
                or (cost['complete_planning_proxy_seconds'] > 7200 and binding is None)
                or type(config.get('gpu_uuid')) is not str or not config['gpu_uuid'].startswith('GPU-')):
            raise ValueError('Forecast above 2 GPUh needs direct exception; smaller jobs proceed automatically')
        production = config.get('production_cpu_payload_sha256', {})
        if (not digest_valid(config.get('production_cpu_receipt_sha256'))
                or type(config.get('production_cpu_stage')) is not str
                or not Path(config['production_cpu_stage']).is_relative_to(Path('.sync'))
                or set(production) != (set(payload)-{APPROVAL}) | {'placement-config.json'}
                or not all(digest_valid(d) for d in production.values())
                or any(payload.get(n) != d for n, d in production.items() if n != 'placement-config.json')):
            raise ValueError('Unchanged actual policy production CPU source proof required')
    elif config['GPU_execution_selected'] is False and (config.get('gpu_uuid') is not None or binding is not None):
        raise ValueError('Unselected placement draft cannot preclaim UUID or >2h approval')
    return {'status': 'PLACEMENT_PRODUCTION_DRAFT_CONTRACT_PASS_NOT_GPU', 'scope': COUNTS,
            'Native_relative_losses': 6, 'signed_joint_swap_diagnostics': 4,
            'selected': config['GPU_execution_selected'], 'same_CFG_quota_not_seconds': True}


def validate_preparation(stage, config):
    records = {}
    for name, binding in config['preparation_audits'].items():
        path = stage/binding['path']
        if not digest_valid(binding['sha256']) or sha(path) != binding['sha256']:
            raise ValueError('Placement frozen preparation audit changed: '+name)
        records[name] = json.loads(path.read_text())
    core, metric = records['placement_core'], records['lpips_resource']
    if (core['status'] != 'PLACEMENT_FULL_CORE_CPU_NATIVE_SHA_RAW_TRAJECTORIES_QUOTAS_ENCODING_PASS_NOT_GPU'
            or core['server_receipt_sha256'] != config['placement_core_receipt_sha256']
            or (core['strict_complete_CPU_parents'], core['complete_CPU_suffixes'], core['mock_outputs_not_real_video']) != (4, 32, 20)
            or core['failure_cases_retained'] != ['child_writer', 'child_guardrail', 'prefix_mask', 'own_CFG_history', 'protected_native_action']
            or core['new_scope'] != COUNTS or core['budget_unchanged'] is not True
            or core['CUDA_initialized'] is not False or core['GPU_submissions'] != 0):
        raise ValueError('Placement actual CPU composition/failure controls incomplete')
    if (metric['status'] != 'LPIPS_ISOLATED_RESOURCE_ORIGINAL_CPU_AUDIT_PASS_NOT_VIDEO_SCORE'
            or metric['server_receipt_sha256'] != config['lpips_resource_receipt_sha256']
            or metric['source_sha256'] != config['payload_sha256']['src/wcomr/rv0_lpips.py']):
        raise ValueError('Frozen isolated full-frame metric differs')
    return records


def validate_stage(project, stage, runtime, config, *, selected=False):
    validate_config(config, selected=selected)
    if (project.resolve() != Path(PROJECT).resolve() or runtime.resolve() != (project/'runtime').resolve()
            or not stage.resolve().is_relative_to((project/'.sync').resolve())):
        raise ValueError('Placement ledger/lock must use existing canonical project root')
    for name, digest in config['payload_sha256'].items():
        if sha(stage/name) != digest:
            raise ValueError('Placement frozen production source changed: '+name)
    base_path = stage/'small-config.json'
    if sha(base_path) != config['base_config_sha256']:
        raise ValueError('Original dependency config changed')
    base = json.loads(base_path.read_text())
    dependencies = validate_original_dependencies(project, stage, runtime, base)
    for key in ['upstream_source_sha256', 'historical_wc_settings', 'references', 'cal_config_sha256', 'f1_setup_sha256']:
        if config[key] != base[key]:
            raise ValueError('Placement original dependency binding differs: '+key)
    prereg = stage/'configs/wc_w3_placement_scope_r1_draft.json'
    if sha(prereg) != config['preregistered_scope_sha256'] or json.loads(prereg.read_text())['scope'] != config['scope']:
        raise ValueError('Original complete preregistered scope changed')
    cost_path = stage/config['cost_report_ref']
    if sha(cost_path) != config['cost_report_sha256'] or json.loads(cost_path.read_text()) != config['cost']:
        raise ValueError('Real C/D complete cost reestimate changed')
    for name, digest in config['cost']['source_sha256'].items():
        path = stage/(config['cost_budget_archive'] if name == 'reports/budget.json' else name)
        if sha(path) != digest:
            raise ValueError('Measured cost original source changed: '+name)
    original = project/config['placement_core_stage']/'receipt.json'
    if not original.resolve().is_relative_to((project/'.sync').resolve()) or sha(original) != config['placement_core_receipt_sha256']:
        raise ValueError('Actual placement core CPU original changed')
    raw = json.loads(original.read_text())
    if (raw['status'] != 'PLACEMENT_FULL_CORE_ACTUAL_CPU_PASS_NOT_PRODUCTION_OR_GPU'
            or raw['exit_code'] != 0 or raw['payload_sha256'] != config['placement_core_payload_sha256']
            or raw['upstream_sha256'] != config['upstream_source_sha256']
            or raw['CUDA_initialized'] is not False or raw['budget_unchanged'] is not True or raw['GPU_submissions'] != 0):
        raise ValueError('Actual placement core provenance failed')
    records = validate_preparation(stage, config)
    budget = json.loads((project/'reports/budget.json').read_text()); auth_path = project/AUTH24
    if (budget['cap_gpu_hours'] != 24 or budget['budget_authorization_ref'] != AUTH24
            or sha(auth_path) != config['payload_sha256'][AUTH24]):
        raise ValueError('Cumulative24 budget authority changed')
    auth = json.loads(auth_path.read_text())
    if auth['source_user_text'] != TEXT24 or auth['usage_reset'] is not False or auth['cumulative_cap_gpu_hours'] != 24:
        raise ValueError('Cumulative24 direct authority differs')
    policy_path = stage/POLICY
    policy = json.loads(policy_path.read_text())
    if (sha(policy_path) != config['execution_policy_authority']['approval_sha256']
            or policy['source_user_text'] != POLICY_TEXT or policy['automatic_single_job_gpu_hours'] != 2
            or policy['legacy_per_card_seconds_caps_revoked'] is not True
            or policy['cumulative_cap_gpu_hours'] != 24 or policy['usage_reset'] is not False):
        raise ValueError('Direct policy original differs')
    if selected:
        original = project/config['production_cpu_stage']/'receipt.json'
        if not original.resolve().is_relative_to((project/'.sync').resolve()) or sha(original) != config['production_cpu_receipt_sha256']:
            raise ValueError('Placement actual production CPU original changed')
        production = json.loads(original.read_text())
        if (production['status'] != 'PLACEMENT_PRODUCTION_ACTUAL_CPU_SOURCE_ASSETS_IMPORT_PASS_NOT_GPU'
                or production['exit_code'] != 0 or production['CUDA_initialized'] is not False
                or production['budget_unchanged'] is not True or production['GPU_submissions'] != 0
                or production['payload_sha256'] != config['production_cpu_payload_sha256']
                or production['upstream_sha256'] != config['upstream_source_sha256']):
            raise ValueError('Actual placement production CPU proof failed')
        binding = config['execution_scope_authority']
        if binding is not None:
            path = stage/APPROVAL
            if sha(path) != binding['approval_sha256']:
                raise ValueError('Above-2h GPU approval original changed')
            if json.loads(path.read_text()) != {k: v for k, v in binding.items() if k not in {'approval_ref', 'approval_sha256'}}:
                raise ValueError('Above-2h complete GPU scope differs')
    return {'status': 'PLACEMENT_REAL_ROOT_DEPENDENCIES_CPU_SOURCE_REFERENCES_PASS_NO_TORCH',
            'audits': {k: v['status'] for k, v in records.items()},
            'base_dependency_status': dependencies['status'], 'budget_snapshot': budget,
            'new_GPU_authorization_verified': selected}


def admission_budget(budget, config):
    validate_config(config, selected=True); used = budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours') != 24 or budget.get('budget_authorization_ref') != AUTH24
            or type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= 24
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Authorized24 usage/reference/inflight differs')
    remaining = (24-used)*3600
    required = config['cost']['complete_planning_proxy_seconds']+LIMITS['cleanup_budget_headroom_seconds']
    if remaining < required:
        raise ValueError('Complete placement planning estimate exceeds remaining cumulative budget')
    return {'fits': True, 'remaining_seconds': remaining, 'required_seconds': required,
            'forecast_is_deadline': False, 'GPU_selected': True}


def reserve_budget(budget, config, supervisor_pid):
    admission_budget(budget, config)
    if type(supervisor_pid) is not int or supervisor_pid <= 0:
        raise ValueError('Placement durable supervisor PID required')
    result = copy.deepcopy(budget); result['used_gpu_hours'] = 24
    result['gpu_jobs_launched'] += 1
    result['status'] = 'WC_W3_PLACEMENT_RUNNING_REMAINING_BUDGET_RESERVED_NOT_ACTUAL_SPENT'
    result[INFLIGHT] = {'run_id': config['run_id'], 'supervisor_pid': supervisor_pid, 'reserved_seconds': (24-budget['used_gpu_hours'])*3600}
    return result


def settle_budget(current, before, config, wall_seconds, supervisor_pid):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0:
        raise ValueError('Actual inclusive failure/flush/release cost required')
    if current != reserve_budget(before, config, supervisor_pid):
        raise ValueError('Placement reservation changed; do not overwrite ledger')
    result = copy.deepcopy(current); result['used_gpu_hours'] = before['used_gpu_hours']+wall_seconds/3600
    result.pop(INFLIGHT); result['status'] = 'WC_W3_PLACEMENT_SETTLED_REQUIRES_RESULT_AUDIT'
    return result


def audit_settlement(supervisor, receipt, config, live_budget, expected_source):
    validate_config(config, selected=True)
    if (supervisor['status'] != 'EXITED_REQUIRES_RESULT_AUDIT' or supervisor['exit_code'] != 0
            or supervisor['source_revision'] != receipt['source_revision'] or receipt['source_revision'] != expected_source
            or supervisor['run_id'] != config['run_id'] or supervisor['config'] != config
            or supervisor['reserved_seconds'] != (24-supervisor['budget_before']['used_gpu_hours'])*3600
            or supervisor.get('cumulative_budget_exceeded') is not False
            or not 0 < supervisor['wall_seconds'] <= supervisor['reserved_seconds']
            or (config['execution_scope_authority'] is None and supervisor['wall_seconds'] > 7200)
            or [supervisor['planned_parent_phases'], supervisor['planned_suffix_controls'], supervisor['planned_encoded_outputs']] != COUNTS[:3]
            or live_budget != supervisor['budget_after'] or any(k.endswith('_inflight') for k in live_budget)
            or live_budget['cap_gpu_hours'] != 24 or live_budget['used_gpu_hours'] > 24):
        raise ValueError('Placement terminal source/scope/cap/live settlement differs')
    prepaid = reserve_budget(supervisor['budget_before'], config, supervisor['pid'])
    if settle_budget(prepaid, supervisor['budget_before'], config, supervisor['wall_seconds'], supervisor['pid']) != live_budget:
        raise ValueError('Placement actual-cost reconstruction differs')
    pids = [supervisor['pid'], supervisor['child_pid']]
    if (any(type(pid) is not int or pid <= 0 for pid in pids) or len(set(pids)) != 2
            or receipt['pid'] != supervisor['child_pid']):
        raise ValueError('Direct supervised runner identity required; no timeout intermediary')
    return pids
