"""Small C/D production provenance and cumulative-cost contracts, no Torch."""
import copy
import json
import math
from pathlib import Path

from .rv0_execution import sha, digest_valid
from .rv0_small_scope import proposal, validate_scope, budget_gate

INFLIGHT = 'wc_w3_small_cd_inflight'
PROJECT = '/home/gaokuangda/data/gkd/worldcache_omr'
AUTH24 = 'manifests/budget_authorization_20261005_wc_24gpuh.json'
TEXT24 = '批准 WC-W3-SMALL-CD-R1-20261004-A，把累计 gpuh 限制提升到 24'


def budget_authority(config):
    """The frozen 13h design remains historical; direct approval overrides only cost authority."""
    binding = config.get('execution_budget_authority')
    if binding is None:
        return 13, config['scope']['budget_authorization_ref']
    expected = {'cumulative_cap_gpu_hours': 24, 'authorization_ref': AUTH24,
                'approved_card': 'WC-W3-SMALL-CD-R1-20261004-A',
                'usage_reset': False, 'single_run_inclusive_cap_seconds': 3900,
                'frozen_scope_budget_fields_are_historical': True}
    if (binding != expected or any(type(binding.get(k)) is not type(v) for k, v in expected.items())
            or config['card'] != expected['approved_card']
            or not digest_valid(config['payload_sha256'].get(AUTH24))
            or not digest_valid(config.get('previous_production_cpu_receipt_sha256'))):
        raise ValueError('Direct cumulative24 execution authority changed')
    return 24, AUTH24


def validate_config(config, *, selected=False):
    validate_scope(config['scope'])
    budget_authority(config)
    for name in ('card', 'run_id', 'sample_names', 'sample_indices', 'target_calls',
                 'maximum_age_solver_steps', 'logical_copy_cap_bytes', 'workspace_reserve_bytes'):
        value = config['scope'][name]
        if type(config.get(name)) is not type(value) or config[name] != value:
            raise ValueError('Small production scope alias differs: '+name)
    if config.get('expected_project_root') != PROJECT or config.get('production_entry_ready') is not True:
        raise ValueError('Real WorldCache ledger root and complete production entry required')
    required = {'src/wcomr/rv0_small_causal.py', 'src/wcomr/rv0_small_scope.py',
                'src/wcomr/rv0_small_execution.py', 'src/wcomr/rv0_small_evaluation.py',
                'scripts/run_wc_w3_small_cd.py', 'scripts/supervise_wc_w3_small_cd.py',
                'scripts/audit_wc_w3_small_cd_terminal.py', 'scripts/analyze_wc_w3_small_cd_lpips_cpu.py'}
    if (not required.issubset(config['payload_sha256']) or len(config['upstream_source_sha256']) != 9
            or not all(digest_valid(d) for d in config['payload_sha256'].values())
            or not all(digest_valid(d) for d in config['upstream_source_sha256'].values())):
        raise ValueError('Small production/source closure incomplete')
    cpu = config['cpu_core_payload_sha256']
    if len(cpu) != 67 or not all(config['payload_sha256'].get(n) == d for n, d in cpu.items()):
        raise ValueError('Production differs from actual 67-file small-core CPU validation')
    for name in ('cal_config_sha256', 'f1_setup_sha256', 'cpu_core_receipt_sha256'):
        if not digest_valid(config.get(name)):
            raise ValueError('Small source/CPU provenance hash missing: '+name)
    if type(config.get('GPU_execution_selected')) is not bool:
        raise ValueError('Small GPU selection must be explicit boolean')
    if selected:
        if (config['GPU_execution_selected'] is not True or type(config.get('gpu_uuid')) is not str
                or not config['gpu_uuid'].startswith('GPU-')):
            raise ValueError('Small selected UUID and independent execution decision required')
    elif not config['GPU_execution_selected'] and config.get('gpu_uuid') is not None:
        raise ValueError('Unselected small draft may not preclaim GPU')
    if set(config['references']) != set(config['sample_names']):
        raise ValueError('Both frozen historical Native/WC reference identities required')
    for name, reference in config['references'].items():
        if (reference['model_and_condition_context'][0] != 'Cosmos-Predict2.5-2B:'+config['f1_setup_sha256']
                or not digest_valid(reference['model_and_condition_context'][1])
                or len(reference['timesteps']) != 36):
            raise ValueError('Small matched model/condition/full sampler reference differs')
        for kind in ('Native35', 'official_WC'):
            item = reference[kind]
            if (not digest_valid(item['sha256']) or type(item['bytes']) is not int or item['bytes'] <= 0
                    or not Path(item['path']).is_relative_to(Path(PROJECT)/'outputs/wc-fair-cal-r1')):
                raise ValueError('Frozen historical video source reference differs')
    cost = config['cost']
    if (cost['proxies_are_hard_bounds'] is not False or cost['adaptive_CD_future_cost_measured'] is not False
            or not 0 < cost['nominal_complete_seconds'] < 3900
            or cost['stress_proxy_complete_seconds'] <= 3900):
        raise ValueError('Small complete cost assumptions or uncertainty changed')
    return {'status': 'SMALL_CD_PRODUCTION_DRAFT_CONTRACT_PASS_NOT_GPU',
            'parents': 2, 'suffixes': 12, 'new_outputs': 8, 'selected': config['GPU_execution_selected']}


def validate_preparation(stage, config):
    records = {}
    for name, binding in config['preparation_audits'].items():
        path = stage/binding['path']
        if not digest_valid(binding['sha256']) or sha(path) != binding['sha256']:
            raise ValueError('Small actual preparation audit changed: '+name)
        records[name] = json.loads(path.read_text())
    core, metric = records['small_core'], records['lpips_resource']
    if (core['status'] != 'SMALL_CD_CORE_CPU_ORIGINAL_AND_RAW_FULL_PIPELINE_AUDIT_PASS_NOT_GPU'
            or core['server_receipt_sha256'] != config['cpu_core_receipt_sha256']
            or (core['complete_successful_parents'], core['complete_successful_suffixes'], core['successful_mock_outputs']) != (4, 24, 16)
            or core['new_GPU_submissions'] != 0 or core['budget_unchanged'] is not True):
        raise ValueError('Small actual core CPU independent audit incomplete')
    if (metric['status'] != 'LPIPS_ISOLATED_RESOURCE_ORIGINAL_CPU_AUDIT_PASS_NOT_VIDEO_SCORE'
            or metric['server_receipt_sha256'] != config['lpips_resource_receipt_sha256']
            or metric['source_sha256'] != config['payload_sha256']['src/wcomr/rv0_lpips.py']):
        raise ValueError('Frozen isolated full-frame LPIPS resource audit differs')
    return records


def validate_stage(project, stage, runtime, config, *, selected=False):
    validate_config(config, selected=selected)
    if (project.resolve() != Path(PROJECT).resolve()
            or runtime.resolve() != (project/'runtime').resolve()
            or not stage.resolve().is_relative_to((project/'.sync').resolve())):
        raise ValueError('Production ledger/lock must use the real existing project root')
    for table, root in [('payload_sha256', stage), ('upstream_source_sha256', runtime)]:
        for name, digest in config[table].items():
            if sha(root/name) != digest:
                raise ValueError('Small frozen stage/source changed: '+name)
    for name, digest in [('configs/cal_w1d8.jsonl', config['cal_config_sha256']),
                         ('configs/f1_setup.json', config['f1_setup_sha256'])]:
        if sha(project/name) != digest:
            raise ValueError('Small frozen input/model setup changed: '+name)
    original = project/config['cpu_core_stage']/'receipt.json'
    if sha(original) != config['cpu_core_receipt_sha256']:
        raise ValueError('Actual small CPU original changed')
    receipt = json.loads(original.read_text())
    if (receipt['exit_code'] != 0 or receipt['payload_sha256'] != config['cpu_core_payload_sha256']
            or receipt['upstream_sha256'] != config['upstream_source_sha256']
            or receipt['controls']['cuda_initialized'] is not False):
        raise ValueError('Actual small CPU source/coverage receipt failed')
    records = validate_preparation(stage, config)
    if budget_authority(config)[0] == 24:
        prior_path = project/config['previous_production_cpu_stage']/'receipt.json'
        if (not prior_path.resolve().is_relative_to((project/'.sync').resolve())
                or sha(prior_path) != config['previous_production_cpu_receipt_sha256']):
            raise ValueError('Previous actual production CPU original changed')
        prior = json.loads(prior_path.read_text())
        if (prior['status'] != 'SMALL_CD_PRODUCTION_ACTUAL_CPU_SOURCE_ASSETS_IMPORT_PASS_NOT_GPU'
                or prior['exit_code'] != 0 or prior['CUDA_initialized'] is not False
                or prior['budget_unchanged'] is not True or prior['GPU_submissions'] != 0
                or prior['upstream_sha256'] != config['upstream_source_sha256']):
            raise ValueError('Previous production CPU evidence differs')
        for name, digest in prior['payload_sha256'].items():
            if name not in {'small-config.json', 'src/wcomr/rv0_small_execution.py'}:
                if config['payload_sha256'].get(name) != digest:
                    raise ValueError('Unapproved change outside cumulative budget adapter: '+name)
    metric_original = project/config['lpips_resource_stage']/'receipt.json'
    if sha(metric_original) != config['lpips_resource_receipt_sha256']:
        raise ValueError('Actual isolated metric CPU original changed')
    for name, digest in config['historical_reference_bindings'].items():
        if sha(stage/name) != digest:
            raise ValueError('Historical reference provenance changed: '+name)
    for reference in config['references'].values():
        for kind in ('Native35', 'official_WC'):
            item = reference[kind]; path = Path(item['path'])
            if path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
                raise ValueError('Historical reference original video changed')
    budget = json.loads((project/'reports/budget.json').read_text())
    cap, auth_ref = budget_authority(config)
    if budget['cap_gpu_hours'] != cap or budget['budget_authorization_ref'] != auth_ref:
        raise ValueError('Live cumulative budget authority differs')
    authorization = project/auth_ref
    if sha(authorization) != config['payload_sha256'].get(auth_ref):
        raise ValueError('Direct cumulative user budget authorization differs')
    auth = json.loads(authorization.read_text())
    if (auth['source_user_text'] != (TEXT24 if cap == 24 else '允许增加 GPUh')
            or auth['cumulative_cap_gpu_hours'] != cap
            or auth['usage_reset'] is not False):
        raise ValueError('Direct budget authorization scope differs')
    if cap == 24 and (auth['approved_card'] != config['card']
                     or auth['single_run_inclusive_cap_seconds'] != 3900):
        raise ValueError('Direct small card approval or single cap differs')
    return {'status': 'SMALL_CD_REAL_ROOT_STAGE_SOURCE_CPU_AUDITS_REFERENCES_PASS_NO_TORCH',
            'audits': {k: v['status'] for k, v in records.items()}, 'budget_snapshot': budget}


def admission_budget(budget, config):
    validate_config(config, selected=True)
    cap, auth_ref = budget_authority(config)
    if cap == 13:
        return budget_gate(budget, config['scope'])
    used = budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours') != cap or budget.get('budget_authorization_ref') != auth_ref
            or type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= cap
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Authorized24 usage/reference/inflight state differs')
    remaining = (cap-used)*3600
    required = config['scope']['timeout_seconds']+config['scope']['admission_allowance_seconds']
    if remaining < required:
        raise ValueError('Complete small C/D cap and admission exceed remaining budget')
    return {'fits': True, 'remaining_seconds': remaining, 'required_seconds': required,
            'remaining_if_full_cap_spent': remaining-required, 'GPU_selected': True}


def reserve_budget(budget, config, supervisor_pid):
    admission_budget(budget, config)
    if type(supervisor_pid) is not int or supervisor_pid <= 0:
        raise ValueError('Small durable supervisor PID required')
    result = copy.deepcopy(budget)
    result['used_gpu_hours'] += 3900/3600
    result['gpu_jobs_launched'] += 1
    result['status'] = 'WC_W3_SMALL_CD_RUNNING_3900S_PREPAID_NOT_ACTUAL_SETTLED'
    result[INFLIGHT] = {'run_id': config['run_id'], 'supervisor_pid': supervisor_pid, 'reserved_seconds': 3900}
    return result


def settle_budget(current, before, config, wall_seconds, supervisor_pid):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0:
        raise ValueError('Small actual inclusive failure/flush/release cost required')
    expected = reserve_budget(before, config, supervisor_pid)
    if current != expected:
        raise ValueError('Small live reservation changed; do not overwrite ledger')
    settled = copy.deepcopy(current)
    settled['used_gpu_hours'] = before['used_gpu_hours']+wall_seconds/3600
    settled.pop(INFLIGHT)
    settled['status'] = 'WC_W3_SMALL_CD_SETTLED_REQUIRES_RESULT_AUDIT'
    return settled


def audit_settlement(supervisor, receipt, config, live_budget, expected_source):
    """Reconstruct the actual reservation, rather than copying settled status."""
    validate_config(config, selected=True)
    if (supervisor['status'] != 'EXITED_REQUIRES_RESULT_AUDIT' or supervisor['exit_code'] != 0
            or supervisor['source_revision'] != receipt['source_revision'] or receipt['source_revision'] != expected_source
            or supervisor['run_id'] != config['run_id'] or supervisor['config'] != config
            or supervisor['reserved_seconds'] != 3900 or supervisor['hard_wall_cap_exceeded'] is not False
            or not 0 < supervisor['wall_seconds'] <= 3900
            or (supervisor['planned_parent_phases'], supervisor['planned_suffix_controls'], supervisor['planned_encoded_outputs']) != (2, 12, 8)
            or live_budget != supervisor['budget_after'] or any(k.endswith('_inflight') for k in live_budget)
            or live_budget['cap_gpu_hours'] != budget_authority(config)[0]
            or live_budget['used_gpu_hours'] > budget_authority(config)[0]):
        raise ValueError('Small terminal identity, complete cap or live settlement differs')
    prepaid = reserve_budget(supervisor['budget_before'], config, supervisor['pid'])
    if settle_budget(prepaid, supervisor['budget_before'], config, supervisor['wall_seconds'], supervisor['pid']) != live_budget:
        raise ValueError('Small terminal actual-cost reconstruction differs')
    pids = [supervisor['pid'], supervisor['child_pid'], receipt['pid']]
    if any(type(pid) is not int or pid <= 0 for pid in pids) or len(set(pids)) != 3:
        raise ValueError('Three distinct durable supervisor/timeout/runner handles required')
    return pids
