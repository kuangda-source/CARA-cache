"""Frozen full-causal execution contract and dependency gates, no Torch."""
import hashlib
import json
import math
import copy
from pathlib import Path

from .rv0_causal_scope import proposal, validate_scope, budget_gate

RUN = 'wc-rv0-causal-r1'
CARD = 'WC-RV0-CAUSAL-R1-20261004-A'
AUDITS = ['causal_cpu_original', 'lpips_resource_original']


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def digest_valid(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate_config(config, *, selected=False):
    validate_scope(config['scope'])
    fixed = {'run_id': RUN, 'card': CARD, 'sample_names': proposal()['sample_names'],
             'sample_indices': [1, 2], 'logical_copy_cap_bytes': 6*(1 << 30),
             'workspace_reserve_bytes': 4*(1 << 30), 'minimum_disk_free_bytes': 15000000000,
             'timeout_seconds': 6900, 'child_timeout_seconds': 6870,
             'kill_grace_seconds': 5, 'release_allowance_seconds': 30,
             'admission_allowance_seconds': 15, 'GPU_submitted': False,
             'budget_reserved_seconds': 0, 'RV_labels': 0,
             'full_RV0_acceptance': False, 'clean_speed_measurement': False,
             'CPU_scoring_after_GPU_release': True}
    for name, value in fixed.items():
        if type(config.get(name)) is not type(value) or config[name] != value:
            raise ValueError('Full causal execution contract differs: '+name)
    if set(config['preparation_audits']) != set(AUDITS):
        raise ValueError('Both server original preparation audits required')
    for name in ['cal_config_sha256', 'f1_setup_sha256', 'cost_report_sha256']:
        if not digest_valid(config.get(name)):
            raise ValueError('Execution provenance hash missing: '+name)
    required = {'src/wcomr/rv0_causal.py', 'src/wcomr/rv0_lpips.py',
                'src/wcomr/rv0_causal_scope.py', 'src/wcomr/rv0_execution.py',
                'scripts/run_wc_rv0_causal.py', 'scripts/supervise_wc_rv0_causal.py',
                'scripts/audit_wc_rv0_causal_cpu.py', 'scripts/audit_wc_rv0_lpips_resource.py',
                'scripts/analyze_wc_rv0_causal_lpips_cpu.py', 'src/wcomr/rv0_video_reader.py',
                'src/wcomr/rv0_evaluation_plan.py', 'scripts/audit_wc_rv0_causal_terminal.py'}
    if not required.issubset(config['payload_sha256']) or len(config['upstream_source_sha256']) != 9:
        raise ValueError('Causal current production/source closure incomplete')
    for table in ['payload_sha256', 'upstream_source_sha256', 'cpu_control_payload_sha256']:
        if not config[table] or not all(digest_valid(v) for v in config[table].values()):
            raise ValueError('Invalid source table: '+table)
    if len(config['cpu_control_payload_sha256']) != 40:
        raise ValueError('Actual CPU control closure differs')
    if not all(config['payload_sha256'].get(n) == v for n, v in config['cpu_control_payload_sha256'].items()):
        raise ValueError('Production core differs from actual CPU controls')
    if type(config['gpu_execution_selected']) is not bool:
        raise ValueError('Execution selection must be explicit bool')
    if selected:
        if not config['gpu_execution_selected'] or not isinstance(config['gpu_uuid'], str) or not config['gpu_uuid'].startswith('GPU-'):
            raise ValueError('Fresh selected UUID and independent execution decision required')
        for entry in config['preparation_audits'].values():
            if not digest_valid(entry['sha256']):
                raise ValueError('Server original audit SHA missing; draft cannot launch')
    elif not config['gpu_execution_selected'] and config['gpu_uuid'] is not None:
        raise ValueError('Unselected draft must not preclaim a GPU')
    return {'status': 'FULL_CAUSAL_DRAFT_SCOPE_SOURCE_CONTRACT_PASS_NOT_DEPLOYMENT',
            'parents': 8, 'suffixes': 24, 'outputs': 18, 'GPU_selected': config['gpu_execution_selected']}


def validate_preparation_audits(project, config):
    records = {}
    for name, binding in config['preparation_audits'].items():
        path = project/binding['path']
        if not digest_valid(binding['sha256']) or sha(path) != binding['sha256']:
            raise ValueError('Preparation original audit missing/changed: '+name)
        records[name] = json.loads(path.read_text())
    causal, resource = (records[name] for name in AUDITS)
    if (causal['status'] != 'FULL_CAUSAL_CPU_RETURNED_RECEIPT_AUDIT_PASS_NOT_GPU'
            or causal['remote_original_and_stage_files_rechecked'] is not True
            or causal['server_receipt_sha256'] != config['cpu_control_receipt_sha256']
            or causal['payload_sha256'] != config['cpu_control_payload_sha256']
            or (causal['completed_mock_parents'], causal['complete_mock_suffixes'], causal['mock_encoded_outputs']) != (16, 48, 36)):
        raise ValueError('Actual original full causal CPU audit incomplete')
    if (resource['status'] != 'LPIPS_ISOLATED_RESOURCE_ORIGINAL_CPU_AUDIT_PASS_NOT_VIDEO_SCORE'
            or resource['server_receipt_sha256'] != config['lpips_resource_receipt_sha256']
            or resource['source_sha256'] != config['payload_sha256']['src/wcomr/rv0_lpips.py']
            or resource['real_C_D_video_scores'] != 0):
        raise ValueError('Isolated LPIPS original resources audit incomplete')
    for record in records.values():
        if record['GPU_submissions'] != 0:
            raise ValueError('Preparation audit unexpectedly submitted a GPU task')
    return records


def validate_stage(project, stage, runtime, config, *, selected=False):
    validate_config(config, selected=selected)
    for table, root in [('payload_sha256', stage), ('upstream_source_sha256', runtime)]:
        for name, digest in config[table].items():
            if sha(root/name) != digest:
                raise ValueError('Frozen causal deployment/source changed: '+name)
    for name, digest in [('configs/cal_w1d8.jsonl', config['cal_config_sha256']),
                         ('configs/f1_setup.json', config['f1_setup_sha256'])]:
        if sha(project/name) != digest:
            raise ValueError('Frozen input/model settings changed: '+name)
    cost_path = stage/config['cost_report_ref']
    if sha(cost_path) != config['cost_report_sha256']:
        raise ValueError('Complete cost proposal changed')
    cost = json.loads(cost_path.read_text())
    if cost['scope'] != config['scope'] or cost['cost']['estimate_is_GPU_upper_bound'] is not False:
        raise ValueError('Scope/cost assumptions differ')
    original = project/config['cpu_control_stage']/'receipt.json'
    if sha(original) != config['cpu_control_receipt_sha256']:
        raise ValueError('Actual CPU original receipt changed')
    receipt = json.loads(original.read_text())
    if (receipt['exit_code'] != 0 or receipt['payload_sha256'] != config['cpu_control_payload_sha256']
            or receipt['upstream_sha256'] != config['upstream_source_sha256']):
        raise ValueError('Actual CPU control receipt failed or source drifted')
    records = validate_preparation_audits(project, config)
    budget = json.loads((project/'reports/budget.json').read_text())
    authorization_path = project/budget['budget_authorization_ref']
    if sha(authorization_path) != config['payload_sha256'].get(budget['budget_authorization_ref']):
        raise ValueError('Direct user authorization original SHA differs from frozen stage')
    authorization = json.loads(authorization_path.read_text())
    if (authorization['source_user_text'] != '允许增加 GPUh'
            or authorization['user_message_id'] != 'Sentinel_861e63a87d8c819180ec9a8bcfa6dc92'
            or authorization['cumulative_cap_gpu_hours'] != 13 or authorization['usage_reset'] is not False):
        raise ValueError('Cumulative13 direct user authorization changed')
    # Prepaid runners are checked by their supervising lock holder. The GPU
    # child validates provenance without attempting a second budget admission.
    return {'status': 'FULL_CAUSAL_STAGE_PREPARATION_SOURCE_AUDITS_PASS_NO_TORCH',
            'config_sha256': sha(stage/'causal-config.json'),
            'audits': {name: value['status'] for name, value in records.items()},
            'budget_snapshot': budget}


def admission_budget(budget, config):
    validate_config(config, selected=True)
    return budget_gate(budget, config['scope'])


def reserve_budget(budget, config, supervisor_pid):
    admission_budget(budget, config)
    if type(supervisor_pid) is not int or supervisor_pid <= 0:
        raise ValueError('Durable supervisor PID required')
    reserved = copy.deepcopy(budget)
    reserved['used_gpu_hours'] += config['timeout_seconds']/3600
    reserved['gpu_jobs_launched'] += 1
    reserved['status'] = 'WC_RV0_CAUSAL_RUNNING_6900S_PREPAID_NOT_ACTUAL_SETTLED'
    reserved['wc_rv0_causal_inflight'] = {'run_id': config['run_id'], 'supervisor_pid': supervisor_pid,
                                        'reserved_seconds': config['timeout_seconds']}
    return reserved


def settle_budget(current, before, config, wall_seconds, supervisor_pid):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0:
        raise ValueError('Actual positive finite failure/flush/release cost required')
    expected = reserve_budget(before, config, supervisor_pid)
    if (current.get('wc_rv0_causal_inflight') != expected['wc_rv0_causal_inflight']
            or current['gpu_jobs_launched'] != expected['gpu_jobs_launched']
            or current['cap_gpu_hours'] != before['cap_gpu_hours']
            or current['budget_authorization_ref'] != before['budget_authorization_ref']
            or not math.isclose(current['used_gpu_hours'], expected['used_gpu_hours'], abs_tol=1e-10)):
        raise ValueError('Reservation changed; preserve evidence and do not overwrite ledger')
    settled = copy.deepcopy(current)
    settled['used_gpu_hours'] = before['used_gpu_hours']+wall_seconds/3600
    settled.pop('wc_rv0_causal_inflight')
    settled['status'] = 'WC_RV0_CAUSAL_SETTLED_REQUIRES_RESULT_AUDIT'
    return settled
