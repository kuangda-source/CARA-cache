"""Two complete flow arms; CPU readiness never grants a larger GPU card."""
import gzip
import json
import math
from pathlib import Path

from .e4c_source_age_production_r1 import sha, write, protected_capacity_failure
import hashlib

CARD = 'WC-P-REFERENCE-SAME-STATE-TWO-FLOW8-SUFFIX32-R1-20261011-A'
RUN = 'wc-p-reference-same-state-two-flow8-suffix32-r1'
CONFIG = 'p-reference-same-state-config.json'
UUID = 'GPU-cebf7119-cf03-23b9-e192-cd196332b704'
STRATEGY = 'WORKING_P_AGE_KEEP_INTERVAL'
OLD_STAGE = '.sync/wc-current-birth-full64-selected-cpu-r1-20261010'
ARMS = {'FLOW_OFF': False, 'FLOW_ON': True}
VARIANTS = ['OFFICIAL_C', 'P_REFERENCE_SCALAR', 'D_REFERENCE_UNIT',
            'P_REFERENCE_UNIT', 'D_REFERENCE_SCALAR']
COUNTS = {'flow_modes': 2, 'full_parent_paths': 8, 'events': 8,
          'suffix_branches': 32, 'age_points': 48, 'same_state_candidate_pairs': 240,
          'teacher_pairs': 48, 'total_pair_computations': 688,
          'CFG_calls': 1376, 'files': 88, 'tensors': 1160}
DYNAMIC = {'GPU_execution_selected', 'gpu_uuid', 'production_CPU_receipt_sha256',
           'single_job_exception_authority'}


def binding(c):
    return hashlib.sha256(json.dumps({k: v for k, v in c.items() if k not in DYNAMIC},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_contract(c, stage):
    stage = Path(stage)
    scope = json.loads((stage/c['scope_ref']).read_text())
    cost = json.loads((stage/c['cost_ref']).read_text())
    authority = json.loads((stage/c['authorization_ref']).read_text())
    proof = json.loads((stage/c['sampling_CPU_capture_ref']).read_text())
    if (c['card'] != CARD or c['run_id'] != RUN or c['parent_stage'] != OLD_STAGE
            or sha(stage/c['scope_ref']) != c['scope_sha256']
            or scope['card'] != CARD or scope['run_id'] != RUN
            or c['scope_counts'] != COUNTS or scope['whole_scope_counts'] != COUNTS
            or c['flow_arms'] != ARMS or scope['flow_modes'] != [False, True]
            or c['candidate_variants'] != VARIANTS or scope['candidate_variants'] != VARIANTS
            or scope['scope_counts']['total_pair_computations'] != 344
            or [e['birth_step'] for e in scope['events']] != [13, 25, 12, 27]
            or scope['suffix_arms'] != ['POLICY_REPEAT1', 'POLICY_REPEAT2', 'P_BIRTH_C4', 'D_BIRTH_C4']
            or scope['teacher_ages'] != [1, 2, 4] or scope['method'] != 'A_CPD_W1_ONE_PHASE'
            or c['working_epoch_strategy'] != STRATEGY
            or sha(stage/c['cost_ref']) != c['cost_sha256']
            or cost['scope_sha256'] != c['scope_sha256']
            or cost['forecast_complete_GPUh'] != c['forecast_complete_GPUh']
            or not math.isfinite(c['forecast_complete_GPUh']) or c['forecast_complete_GPUh'] <= 0
            or cost['whole_pair_computations'] != 688 or cost['whole_CFG_calls'] != 1376
            or cost['actual_model_loads_planned'] != 2
            or c['automatic_single_job_GPUh'] != 8 or c['cumulative_cap_GPUh'] != 77.89524658965853
            or c['checkpoint_reserves'] != {'logical_copy_cap_bytes': 6*(1 << 30),
                'workspace_reserve_bytes': 4*(1 << 30), 'paired_prefix_reserve_bytes': 4*(1 << 30)}
            or c['training'] or c['human_review'] or c['method_speed_or_quality_claim']
            or c['empty_cache_or_gate_bypass'] or c['native_head_elision_combined']
            or c['continue_after_failure'] != 'STOP_RETAIN_COMPLETE_SCOPE'
            or not authority['direct_user_authorization'] or authority['automatic_single_job_gpu_hours'] != 8
            or authority['scope'] != 'CURRENT_WORLD_CACHE_E0_E5_RESEARCH_WINDOW_20261011'
            or authority['usage_reset'] or sha(stage/c['authorization_ref']) != c['authorization_sha256']
            or authority['cumulative_cap_gpu_hours'] != c['cumulative_cap_GPUh']
            or sha(stage/c['sampling_CPU_capture_ref']) != c['sampling_CPU_capture_sha256']
            or proof['status'] != 'P_REFERENCE_SAME_STATE_COMPLETE_CPU_INDEPENDENTLY_AUDITED_NOT_GPU'
            or proof['frozen_source_files_unchanged'] != 444
            or proof['actual_reloaded_files'] != 88 or proof['actual_reloaded_tensors'] != 1160
            or proof['actual_direct_tensor_comparisons'] != 420 or proof['same_state_points'] != 48
            or proof['candidate_restore_operations'] != 240 or proof['D_source_control_equalities'] != 96
            or proof['CUDA_initialized'] or proof['GPU_submissions'] or proof['ledger_written']
            or type(c['GPU_execution_selected']) is not bool):
        raise ValueError('Exact complete two-flow five-readout scope or source proof differs')
    requests = [json.loads(s) for s in (stage/'p-reference-requests.jsonl').read_text().splitlines() if s]
    if requests != c['requests'] or [r['name'] for r in requests] != scope['sample_names']:
        raise ValueError('Exact two original CAL requests required')
    return scope


def validate(project, stage):
    project, stage = Path(project), Path(stage)
    c = json.loads((stage/CONFIG).read_text()); scope = validate_contract(c, stage)
    for n, h in c['payload_sha256'].items():
        if sha(stage/n) != h: raise ValueError('P-reference production source changed: '+n)
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
    for n, h in c['parent_import_source_sha256'].items():
        if sha(parent/n) != h or (stage/n).exists() and sha(stage/n) != h:
            raise ValueError('Read-only original input helper changed: '+n)
    expected = [r for r in old['preregistration']['requests'] if r['name'] in scope['sample_names']]
    expected.sort(key=lambda r: scope['sample_names'].index(r['name']))
    if c['requests'] != expected or len(expected) != 2:
        raise ValueError('Actual original request binding differs')
    return c, old, inputs


def exact_exception(c, stage):
    stage = Path(stage); ref = c['single_job_exception_authority']
    if not isinstance(ref, dict): raise ValueError('Exact complete above8 P-reference approval required')
    path = stage/ref['ref']; approved = json.loads(path.read_text())
    if (sha(path) != ref['sha256'] or not approved['direct_user_authorization']
            or approved['card'] != CARD or approved['run_id'] != RUN
            or approved['scope_counts'] != COUNTS or approved['config_binding_sha256'] != binding(c)
            or approved['forecast_complete_GPUh'] != c['forecast_complete_GPUh']):
        raise ValueError('Different approval cannot authorize this whole P-reference card')


def validate_selected(c, stage):
    stage = Path(stage); path = stage/'production-CPU-receipt.json'; r = json.loads(path.read_text())
    if (not c['GPU_execution_selected'] or c['gpu_uuid'] != UUID
            or c['production_CPU_receipt_sha256'] != sha(path) or r['exit_code'] != 0
            or r['status'] != 'P_REFERENCE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
            or r['config_binding_sha256'] != binding(c) or r['CUDA_initialized']
            or r['GPU_submissions'] or r['ledger_written'] or r['payload_after_sha256'] != c['payload_sha256']):
        raise ValueError('Same-source complete actual production CPU acceptance required')
    if c['forecast_complete_GPUh'] > 8: exact_exception(c, stage)
    return r


def admit(c, ledger, gpu, proof, *, exact_above8_approval_verified=False):
    remaining = ledger['cap_gpu_hours']-ledger['used_gpu_hours']
    if (not math.isfinite(ledger['used_gpu_hours']) or not 0 <= ledger['used_gpu_hours'] < ledger['cap_gpu_hours']
            or ledger['cap_gpu_hours'] != c['cumulative_cap_GPUh'] or any('inflight' in k for k in ledger)
            or c['forecast_complete_GPUh'] > remaining
            or c['forecast_complete_GPUh'] > 8 and not exact_above8_approval_verified
            or gpu['uuid'] != UUID or gpu['compute_cap'] != '8.6' or gpu['memory_used_mib'] > 1024 or gpu['pids']
            or proof['status'] != 'P_REFERENCE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' or proof['exit_code'] != 0
            or proof['config_binding_sha256'] != binding(c)):
        raise ValueError('P-reference fresh resource, full cost, source CPU or exact approval admission failed')
    return remaining, remaining if c['forecast_complete_GPUh'] > 8 else min(8., remaining)
