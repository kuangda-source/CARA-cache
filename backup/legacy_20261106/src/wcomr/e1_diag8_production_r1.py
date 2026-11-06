"""E1 scope, original input and scoped8 admission; never old-card authority."""
import hashlib
import json
import math
from pathlib import Path

CARD='WC-E1-COLD-PREFIX-STORAGE-DIAG8-R1-20261011-A'
RUN='wc-e1-cold-prefix-storage-diag8-r1'
UUID='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
CONFIG='e1-diag8-config.json'
STRATEGY='WORKING_P_AGE_KEEP_INTERVAL'
OLD_STAGE='.sync/wc-current-birth-full64-selected-cpu-r1-20261010'
COUNTS={'planned_paths':8,'independent_model_loads':4,'maximum_updates':288,'maximum_CFG_calls':576}
DYNAMIC={'GPU_execution_selected','gpu_uuid','production_CPU_receipt_sha256'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
    return h.hexdigest()


def write(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def protected_capacity_failure(error_type,message):
    return error_type=='ValueError' and (message in (
        'Dynamic complete checkpoint GPU headroom unavailable',
        'Insufficient live GPU headroom before any snapshot copies',
        'Insufficient live GPU headroom for combined P0 checkpoint')
        or message.startswith('CPU-owned checkpoint next-copy GPU headroom unavailable: '))


def binding(c):
    return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in DYNAMIC},sort_keys=True,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_contract(c,stage):
    from .e1_memory_diagnostic_sampling_r1 import ARMS
    stage=Path(stage);scope=json.loads((stage/c['scope_ref']).read_text())
    authority=json.loads((stage/c['authorization_ref']).read_text())
    if (c['card']!=CARD or c['run_id']!=RUN or c['arms']!=ARMS or c['scope_counts']!=COUNTS
            or c['parent_stage']!=OLD_STAGE or c['scope_sha256']!=sha(stage/c['scope_ref'])
            or scope['card']!=CARD or scope['run_id']!=RUN
            or scope['arms']!=ARMS or scope['requests']!=c['requests']
            or scope['scope_counts']!={'independent_model_processes':4,'planned_paths':8,
                'maximum_solver_updates':288,'maximum_CFG_calls':576,'checkpoint_steps':[12,30,35,36]}
            or c['forecast_complete_GPUh']!=scope['whole_cost']['forecast_complete_GPUh']
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=77.89524658965853
            or c['working_epoch_strategy']!=STRATEGY or c['state_steps']!=[12,30,35,36]
            or c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),
                'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}
            or c['continue_after_protected_failure']!='NEXT_REGISTERED_FRESH_MODEL_PROCESS_ONLY'
            or c['empty_cache_or_gate_bypass'] or c['training'] or c['method_speed_or_quality_claim']
            or not authority['direct_user_authorization'] or authority['automatic_single_job_gpu_hours']!=8
            or authority['scope']!='CURRENT_WORLD_CACHE_E0_E5_RESEARCH_WINDOW_20261011'
            or authority['usage_reset'] or authority['cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh']
            or c['authorization_sha256']!=sha(stage/c['authorization_ref'])
            or type(c['GPU_execution_selected']) is not bool):
        raise ValueError('E1 complete8 scope, reserve or scoped8 authority differs')
    proof=json.loads((stage/c['sampling_CPU_capture_ref']).read_text())
    if (sha(stage/c['sampling_CPU_capture_ref'])!=c['sampling_CPU_capture_sha256'] or proof['exit_code']!=0
            or not proof['original_source_and_full_scope_independently_verified']
            or proof['independent_tensor_and_policy_audit']['actual_tensors_reloaded']!=888
            or proof['independent_tensor_and_policy_audit']['policy_decisions_independently_replayed']!=1008
            or proof['GPU_submissions']!=0 or proof['ledger_written']):
        raise ValueError('E1 full-scope independent CPU proof required')
    if c['GPU_execution_selected'] and c['gpu_uuid']!=UUID:
        raise ValueError('E1 selected target differs')
    return scope


def validate(project,stage):
    project,stage=Path(project),Path(stage);c=json.loads((stage/CONFIG).read_text())
    validate_contract(c,stage)
    for n,h in c['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('E1 diagnostic source changed: '+n)
    parent=project/c['parent_stage']
    if sha(parent/'current-birth-full64-config.json')!=c['parent_config_sha256']:
        raise ValueError('Immutable original full64 input config changed')
    # Only missing input-validation helpers are resolved in the original stage.
    # Its validate_selected is deliberately never used as this card's authority.
    import wcomr
    old_src=str(parent/'src/wcomr')
    if old_src not in wcomr.__path__:wcomr.__path__.append(old_src)
    from .current_birth_real_production_r1 import validate as validate_parent
    old,inputs=validate_parent(project,parent)
    for n,h in c['parent_import_source_sha256'].items():
        if sha(parent/n)!=h:raise ValueError('Read-only original input helper changed: '+n)
        new=stage/n
        if new.exists() and sha(new)!=h:raise ValueError('E1 shadows original input helper with altered source: '+n)
    requests=[r for r in old['preregistration']['requests'] if r['name'] in ('human_199',c['AV_name'])]
    requests.sort(key=lambda r:0 if r['name']==c['AV_name'] else 1)
    if requests!=c['requests'] or len(requests)!=2:
        raise ValueError('Exact original E1 AV/Human CAL requests required')
    if (old['logical_copy_cap_bytes']!=c['checkpoint_reserves']['logical_copy_cap_bytes']
            or old['workspace_reserve_bytes']!=c['checkpoint_reserves']['workspace_reserve_bytes']
            or old['paired_prefix_reserve_bytes']!=c['checkpoint_reserves']['paired_prefix_reserve_bytes']):
        raise ValueError('Original full physical reserves must remain unchanged')
    return c,old,inputs


def validate_selected(c,stage):
    if not c['GPU_execution_selected'] or c['gpu_uuid']!=UUID:
        raise ValueError('E1 GPU execution has not been selected')
    stage=Path(stage);path=stage/'production-CPU-receipt.json';r=json.loads(path.read_text())
    if (sha(path)!=c['production_CPU_receipt_sha256'] or r['exit_code']!=0
            or r['status']!='E1_DIAG8_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
            or r['config_binding_sha256']!=binding(c) or r['CUDA_initialized']
            or r['GPU_submissions'] or r['ledger_written'] or r['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('Original same-source E1 production CPU proof required')
    return r


def admit(c,ledger,gpu,proof):
    remaining=ledger['cap_gpu_hours']-ledger['used_gpu_hours']
    if (not math.isfinite(ledger['used_gpu_hours']) or not 0<=ledger['used_gpu_hours']<ledger['cap_gpu_hours']
            or ledger['cap_gpu_hours']!=c['cumulative_cap_GPUh'] or any('inflight' in k for k in ledger)
            or c['forecast_complete_GPUh']>remaining or c['forecast_complete_GPUh']>8
            or gpu['uuid']!=UUID or gpu['compute_cap']!='8.6' or gpu['memory_used_mib']>1024 or gpu['pids']
            or proof['status']!='E1_DIAG8_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' or proof['exit_code']!=0
            or proof['config_binding_sha256']!=binding(c)):
        raise ValueError('E1 fresh resource, complete budget or CPU admission failed')
    return remaining,min(8.,remaining)
