"""One complete registered E4c job; original assets never confer old authority."""
import hashlib
import json
import math
from pathlib import Path

CARD = 'WC-E4C-MATCHED-P-D-AGE124-OFFON4-SUFFIX16-R1-20261011-A'
RUN = 'wc-e4c-matched-p-d-age124-offon4-suffix16-r1'
CONFIG = 'e4c-source-age-config.json'
UUID = 'GPU-cebf7119-cf03-23b9-e192-cd196332b704'
STRATEGY = 'WORKING_P_AGE_KEEP_INTERVAL'
OLD_STAGE = '.sync/wc-current-birth-full64-selected-cpu-r1-20261010'
DYNAMIC = {'GPU_execution_selected', 'gpu_uuid', 'production_CPU_receipt_sha256'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 << 20), b''): h.update(chunk)
    return h.hexdigest()


def write(path, value):
    path = Path(path); tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n'); tmp.replace(path)


def binding(c):
    return hashlib.sha256(json.dumps({k: v for k, v in c.items() if k not in DYNAMIC},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def protected_capacity_failure(error_type, message):
    return error_type == 'ValueError' and ('GPU headroom' in message or 'logical cap exceeded' in message)


def validate_contract(c, stage):
    stage = Path(stage)
    scope = json.loads((stage/c['scope_ref']).read_text())
    cost = json.loads((stage/c['cost_ref']).read_text())
    authority = json.loads((stage/c['authorization_ref']).read_text())
    proof = json.loads((stage/c['sampling_CPU_capture_ref']).read_text())
    if (c['card'] != CARD or c['run_id'] != RUN or c['parent_stage'] != OLD_STAGE
            or c['scope_sha256'] != sha(stage/c['scope_ref']) or scope['card'] != CARD
            or scope['run_id'] != RUN or scope['scope_counts'] != c['scope_counts']
            or c['scope_counts'] != {'full_parent_paths': 4, 'full_parent_updates': 144, 'events': 4,
                'suffix_branches': 16, 'suffix_updates': 80, 'same_state_C_dense_teacher_points': 24,
                'teacher_pairs': 24, 'total_pair_computations': 248, 'total_normal_and_teacher_CFG_calls': 496}
            or [e['birth_step'] for e in scope['events']] != [13, 25, 12, 27]
            or scope['suffix_arms'] != ['POLICY_REPEAT1', 'POLICY_REPEAT2', 'P_BIRTH_C4', 'D_BIRTH_C4']
            or scope['teacher_ages'] != [1, 2, 4] or scope['method'] != 'A_CPD_W1_ONE_PHASE'
            or c['working_epoch_strategy'] != STRATEGY
            or c['cost_sha256'] != sha(stage/c['cost_ref'])
            or cost['scope_sha256'] != c['scope_sha256']
            or cost['forecast_complete_GPUh'] != c['forecast_complete_GPUh']
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0 < c['forecast_complete_GPUh'] <= 8
            or c['automatic_single_job_GPUh'] != 8 or c['cumulative_cap_GPUh'] != 77.89524658965853
            or c['checkpoint_reserves'] != {'logical_copy_cap_bytes': 6*(1 << 30),
                'workspace_reserve_bytes': 4*(1 << 30), 'paired_prefix_reserve_bytes': 4*(1 << 30)}
            or c['training'] or c['human_review'] or c['method_speed_or_quality_claim']
            or c['empty_cache_or_gate_bypass'] or c['continue_after_failure'] != 'STOP_RETAIN_COMPLETE_SCOPE'
            or not authority['direct_user_authorization'] or authority['automatic_single_job_gpu_hours'] != 8
            or authority['scope'] != 'CURRENT_WORLD_CACHE_E0_E5_RESEARCH_WINDOW_20261011'
            or authority['usage_reset'] or c['authorization_sha256'] != sha(stage/c['authorization_ref'])
            or authority['cumulative_cap_gpu_hours'] != c['cumulative_cap_GPUh']
            or c['sampling_CPU_capture_sha256'] != sha(stage/c['sampling_CPU_capture_ref'])
            or proof['receipt']['exit_code'] != 0
            or not proof['original_source_receipts_complete_scope_and_actual_vectors_independently_verified']
            or proof['independent_actual_vector_reads']['actual_written_tensors_reloaded'] != 776
            or proof['independent_actual_vector_reads']['actual_direct_tensor_comparisons'] != 324
            or type(c['GPU_execution_selected']) is not bool):
        raise ValueError('Exact complete E4c scope, source proof, cost or scoped8 authority differs')
    requests = [json.loads(s) for s in (stage/'e4c-requests.jsonl').read_text().splitlines() if s]
    if requests != c['requests'] or [r['name'] for r in requests] != scope['sample_names']:
        raise ValueError('Exact two original CAL requests required')
    return scope


def validate(project, stage):
    project, stage = Path(project), Path(stage)
    c = json.loads((stage/CONFIG).read_text()); scope = validate_contract(c, stage)
    for name, h in c['payload_sha256'].items():
        if sha(stage/name) != h: raise ValueError('E4c source changed: '+name)
    parent = project/c['parent_stage']
    if sha(parent/'current-birth-full64-config.json') != c['parent_config_sha256']:
        raise ValueError('Original actual input config changed')
    import wcomr
    fallback = str(parent/'src/wcomr')
    if fallback not in wcomr.__path__: wcomr.__path__.append(fallback)
    from .current_birth_real_production_r1 import validate as validate_parent
    from .e1_diag8_production_r2 import validate_required_assets
    validate_required_assets(c, stage)
    old, inputs = validate_parent(project, parent)
    for name, h in c['parent_import_source_sha256'].items():
        if sha(parent/name) != h or (stage/name).exists() and sha(stage/name) != h:
            raise ValueError('Read-only original input helper changed: '+name)
    expected = [r for r in old['preregistration']['requests'] if r['name'] in scope['sample_names']]
    expected.sort(key=lambda r: scope['sample_names'].index(r['name']))
    if c['requests'] != expected or len(expected) != 2:
        raise ValueError('Actual original request binding differs')
    return c, old, inputs


def validate_selected(c, stage):
    stage = Path(stage); p = stage/'production-CPU-receipt.json'; r = json.loads(p.read_text())
    if (not c['GPU_execution_selected'] or c['gpu_uuid'] != UUID
            or c['production_CPU_receipt_sha256'] != sha(p) or r['exit_code'] != 0
            or r['status'] != 'E4C_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
            or r['config_binding_sha256'] != binding(c) or r['CUDA_initialized']
            or r['GPU_submissions'] or r['ledger_written'] or r['payload_after_sha256'] != c['payload_sha256']):
        raise ValueError('Same-source complete E4c actual production CPU acceptance required')
    return r


def admit(c, ledger, gpu, proof):
    remaining = ledger['cap_gpu_hours'] - ledger['used_gpu_hours']
    if (not math.isfinite(ledger['used_gpu_hours']) or not 0 <= ledger['used_gpu_hours'] < ledger['cap_gpu_hours']
            or ledger['cap_gpu_hours'] != c['cumulative_cap_GPUh'] or any('inflight' in k for k in ledger)
            or c['forecast_complete_GPUh'] > remaining or c['forecast_complete_GPUh'] > 8
            or gpu['uuid'] != UUID or gpu['compute_cap'] != '8.6' or gpu['memory_used_mib'] > 1024 or gpu['pids']
            or proof['status'] != 'E4C_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' or proof['exit_code'] != 0
            or proof['config_binding_sha256'] != binding(c)):
        raise ValueError('E4c fresh resource, complete budget or source CPU admission failed')
    return remaining, min(8., remaining)
