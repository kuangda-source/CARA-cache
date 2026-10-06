"""Five-reference production authority, frozen CPU proof and inclusive cost."""
import copy
import json
import math
from pathlib import Path

from .w1_native_reference_scope import sha, validate_reference_scope, INDICES, NAMES, RUN

PROJECT = '/home/gaokuangda/data/gkd/worldcache_omr'
CARD = 'WC-W1-NATIVE-REFERENCE-CAL8-R1-20261006-A'
AUTH24 = 'manifests/budget_authorization_20261005_wc_24gpuh.json'
APPROVAL = 'manifests/wc_w1_native_reference_gpu_authorization_20261006.json'
INFLIGHT = 'wc_w1_native_reference_inflight'
LIMITS = {'timeout_seconds': 3600, 'child_timeout_seconds': 3570,
          'kill_grace_seconds': 5, 'admission_allowance_seconds': 30,
          'minimum_disk_free_bytes': 4*1024**3}


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate_config(config, *, selected=False):
    if (config['card'] != CARD or config['run_id'] != RUN or config['expected_project_root'] != PROJECT
            or config['sample_indices'] != list(INDICES) or config['sample_names'] != list(NAMES)
            or config['original_denominator'] != [8, 7, 1] or config['new_reference_phases'] != 5
            or config['execution_limits'] != LIMITS
            or any(type(config['execution_limits'][k]) is not int for k in LIMITS)
            or config['production_entry_ready'] is not True
            or config['all_seven_must_improve'] is not False or config['new_training_or_human_review'] is not False):
        raise ValueError('Complete five-reference production scope/limits differs')
    payload, core = config['payload_sha256'], config['core_cpu_payload_sha256']
    required = {'src/wcomr/w1_native_reference_execution.py', 'src/wcomr/w1_native_reference_evaluation.py',
                'src/wcomr/w1_native_reference_sampling.py', 'src/wcomr/w1_native_reference_scope.py',
                'scripts/run_w1_native_references.py', 'scripts/supervise_w1_native_references.py',
                'scripts/audit_w1_native_references_terminal.py', 'scripts/score_w1_native_references_cpu.py',
                'w1-reference-draft.json', AUTH24}
    if (len(core) != 148 or not required.issubset(payload)
            or any(payload.get(n) != d for n, d in core.items())
            or not all(digest(d) for d in payload.values())
            or len(config['upstream_source_sha256']) != 9
            or not all(digest(d) for d in config['upstream_source_sha256'].values())
            or not all(digest(config[k]) for k in ['core_cpu_receipt_sha256', 'draft_sha256',
                'cost_report_sha256', 'lpips_resource_receipt_sha256'])):
        raise ValueError('Actual complete core/source/metric proof incomplete')
    for name in payload:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts: raise ValueError('Payload escapes independent stage')
    if type(config['GPU_execution_selected']) is not bool:
        raise ValueError('GPU selection must be explicit')
    binding = config.get('execution_scope_authority')
    if binding is not None:
        expected = {'approval_ref': APPROVAL, 'approved_card': CARD, 'run_id': RUN,
                    'single_run_inclusive_cap_seconds': 3600, 'new_reference_phases': 5,
                    'original_denominator': [8, 7, 1], 'usage_reset': False}
        if (set(binding) != set(expected) | {'source_user_text', 'approval_sha256'}
                or any(type(binding.get(k)) is not type(v) or binding[k] != v for k, v in expected.items())
                or not digest(binding['approval_sha256']) or payload.get(APPROVAL) != binding['approval_sha256']
                or type(binding['source_user_text']) is not str or not binding['source_user_text'].strip()):
            raise ValueError('Separate direct five-reference scope authority differs')
    if selected:
        cpu = config.get('production_cpu_payload_sha256', {})
        if (binding is None or config['GPU_execution_selected'] is not True
                or type(config.get('gpu_uuid')) is not str or not config['gpu_uuid'].startswith('GPU-')
                or not digest(config.get('production_cpu_receipt_sha256'))
                or type(config.get('production_cpu_stage')) is not str
                or not Path(config['production_cpu_stage']).is_relative_to(Path('.sync'))
                or set(cpu) != (set(payload)-{APPROVAL}) | {'native-prod-config.json'}
                or any(payload.get(n) != d for n, d in cpu.items() if n != 'native-prod-config.json')):
            raise ValueError('Direct scope/UUID and unchanged actual production CPU proof required')
    elif config['GPU_execution_selected'] or binding is not None or config['gpu_uuid'] is not None or APPROVAL in payload:
        raise ValueError('Unselected draft cannot preclaim GPU authority')
    return {'status': 'FIVE_REFERENCE_PRODUCTION_DRAFT_CONTRACT_PASS_NOT_GPU',
            'new_reference_phases': 5, 'original_denominator': [8, 7, 1], 'selected': selected}


def validate_stage(project, stage, runtime, config, *, selected=False):
    validate_config(config, selected=selected)
    project, stage, runtime = map(Path, (project, stage, runtime))
    if (project.resolve() != Path(PROJECT).resolve() or runtime.resolve() != (project/'runtime').resolve()
            or not stage.resolve().is_relative_to((project/'.sync').resolve())):
        raise ValueError('Existing canonical project/runtime and isolated stage required')
    for name, value in config['payload_sha256'].items():
        if sha(stage/name) != value: raise ValueError('Frozen production payload changed: '+name)
    for name, value in config['upstream_source_sha256'].items():
        if sha(runtime/name) != value: raise ValueError('Pinned upstream changed: '+name)
    for name, value in config['project_input_sha256'].items():
        if name == 'reports/budget.json': continue  # Usage rolls forward; direct cap authority is checked below.
        if sha(project/name) != value: raise ValueError('Original W1/root identity changed: '+name)
    draft = json.loads((stage/'w1-reference-draft.json').read_text())
    if sha(stage/'w1-reference-draft.json') != config['draft_sha256']:
        raise ValueError('Original five-reference draft changed')
    for name, value in draft['input_sha256'].items():
        if sha(stage/name) != value: raise ValueError('Original input snapshot changed: '+name)
    replay = json.loads((stage/'reports/w1_replay_r1_runner.json').read_text())
    cal = json.loads((stage/'reports/w1d_cal8_r1_runner.json').read_text())
    rows = validate_reference_scope(draft, replay, cal)
    for row in draft['rows']:
        for item in [row['official_WC'], row['W1_scalar'], row['matched_Native']]:
            if item is not None and item['path'] is not None and sha(item['path']) != item['sha256']:
                raise ValueError('Existing W1/WC/Native artifact changed')
    core_path = project/config['core_cpu_stage']/'receipt.json'
    if sha(core_path) != config['core_cpu_receipt_sha256']:
        raise ValueError('Actual core CPU original changed')
    core = json.loads(core_path.read_text())
    if (core['status'] != 'FIVE_NATIVE_REFERENCE_ACTUAL_CPU_CORE_AND_IMPORT_PASS_NOT_GPU'
            or core['exit_code'] != 0 or core['payload_sha256'] != config['core_cpu_payload_sha256']
            or core['upstream_sha256'] != config['upstream_source_sha256'] or core['CUDA_initialized']
            or not core['budget_unchanged'] or core['GPU_submissions'] != 0):
        raise ValueError('Complete actual core CPU proof failed')
    resource_path = project/config['lpips_resource_stage']/'receipt.json'
    if sha(resource_path) != config['lpips_resource_receipt_sha256']:
        raise ValueError('Frozen isolated CPU metric original changed')
    resource = json.loads((stage/config['lpips_resource_audit']['path']).read_text())
    if (sha(stage/config['lpips_resource_audit']['path']) != config['lpips_resource_audit']['sha256']
            or resource['server_receipt_sha256'] != config['lpips_resource_receipt_sha256']
            or resource['source_sha256'] != config['payload_sha256']['src/wcomr/rv0_lpips.py']):
        raise ValueError('Metric code/resource binding differs')
    if sha(stage/config['cost_report_ref']) != config['cost_report_sha256']:
        raise ValueError('Five-reference full-cost proxy changed')
    budget = json.loads((project/'reports/budget.json').read_text())
    auth = json.loads((project/AUTH24).read_text())
    if (budget.get('cap_gpu_hours') != 24 or budget.get('budget_authorization_ref') != AUTH24
            or sha(project/AUTH24) != config['payload_sha256'][AUTH24]
            or auth['cumulative_cap_gpu_hours'] != 24 or auth['usage_reset'] is not False
            or auth['source_user_text'] != '批准 WC-W3-SMALL-CD-R1-20261004-A，把累计 gpuh 限制提升到 24'):
        raise ValueError('Cumulative24 direct cap authority differs')
    if selected:
        proof_path = project/config['production_cpu_stage']/'receipt.json'
        if sha(proof_path) != config['production_cpu_receipt_sha256']:
            raise ValueError('Actual production CPU original changed')
        proof = json.loads(proof_path.read_text())
        if (proof['status'] != 'FIVE_NATIVE_REFERENCE_PRODUCTION_ACTUAL_CPU_PASS_NOT_GPU'
                or proof['exit_code'] != 0 or proof['payload_sha256'] != config['production_cpu_payload_sha256']
                or proof['CUDA_initialized'] or proof['GPU_submissions'] != 0 or not proof['budget_unchanged']):
            raise ValueError('Actual complete production CPU proof failed')
        binding = config['execution_scope_authority']
        if json.loads((stage/APPROVAL).read_text()) != {k:v for k,v in binding.items() if k not in ['approval_ref','approval_sha256']}:
            raise ValueError('Direct five-reference approval original differs')
    return {'status': 'FIVE_REFERENCE_REAL_ROOT_CPU_PROVENANCE_PASS_NO_TORCH',
            'new_reference_phases': len(rows), 'original_denominator': [8, 7, 1],
            'budget_snapshot': budget, 'new_GPU_authority_verified': selected}


def admission_budget(budget, config):
    validate_config(config, selected=True)
    used = budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours') != 24 or budget.get('budget_authorization_ref') != AUTH24
            or type(used) not in (int,float) or not math.isfinite(used) or not 0 <= used <= 24
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Current usage/cap/inflight differs')
    remaining = (24-used)*3600
    if remaining < 3630: raise ValueError('Whole five-reference cap and admission planning do not fit')
    return {'remaining_seconds': remaining, 'required_planning_seconds': 3630,
            'charged_reservation_seconds': 3600, 'admission_CPU_not_GPU_reservation': True}


def reserve_budget(budget, config, pid):
    admission_budget(budget, config)
    if type(pid) is not int or pid <= 0: raise ValueError('Durable supervisor PID required')
    result = copy.deepcopy(budget); result['used_gpu_hours'] += 1
    result['gpu_jobs_launched'] += 1
    result[INFLIGHT] = {'run_id': RUN, 'supervisor_pid': pid, 'reserved_seconds': 3600}
    result['status'] = 'W1_NATIVE_REFERENCE_RUNNING_3600S_PREPAID_NOT_ACTUAL'
    return result


def settle_budget(current, before, config, seconds, pid):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Inclusive actual failure/loading/flush/release wall required')
    if current != reserve_budget(before, config, pid):
        raise ValueError('Reservation changed; preserve rather than overwrite')
    result = copy.deepcopy(current); result['used_gpu_hours'] = before['used_gpu_hours']+seconds/3600
    result.pop(INFLIGHT); result['status'] = 'W1_NATIVE_REFERENCE_SETTLED_REQUIRES_RESULT_AUDIT'
    return result


def audit_settlement(supervisor, receipt, config, live_budget, source):
    validate_config(config, selected=True)
    if (supervisor['source_revision'] != source or receipt['source_revision'] != source
            or supervisor['run_id'] != RUN or supervisor['config'] != config
            or supervisor['reserved_seconds'] != 3600 or supervisor['hard_wall_cap_exceeded']
            or not 0 < supervisor['wall_seconds'] <= 3600 or supervisor['budget_after'] != live_budget
            or any(k.endswith('_inflight') for k in live_budget)
            or live_budget['cap_gpu_hours'] != 24 or live_budget['used_gpu_hours'] > 24
            or settle_budget(reserve_budget(supervisor['budget_before'],config,supervisor['pid']),
                             supervisor['budget_before'],config,supervisor['wall_seconds'],supervisor['pid']) != live_budget):
        raise ValueError('Terminal source/scope/cap/actual settlement differs')
    pids = [supervisor['pid'], supervisor['child_pid'], receipt['pid']]
    if len(set(pids)) != 3 or any(type(pid) is not int or pid <= 0 for pid in pids):
        raise ValueError('Three distinct original process handles required')
    return pids
