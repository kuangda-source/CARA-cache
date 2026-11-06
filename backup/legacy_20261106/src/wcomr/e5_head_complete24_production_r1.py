"""Exact E5 whole24 scope and current-window admission, not old-card authority."""
import json
import math
from pathlib import Path

from .e4c_source_age_production_r1 import sha,write,binding,STRATEGY,UUID,OLD_STAGE

CARD='WC-E5-NATIVE-WRAPPED-HEAD-FULL24-R1-20261011-A'
RUN='wc-e5-native-wrapped-head-full24-r1'
CONFIG='e5-head-complete24-config.json'
COUNTS={'complete_paths':24,'independent_model_loads':4,'solver_updates':864,
    'CFG_calls':1728,'teacher_calls':0,'checkpoint_roundtrips':96,
    'written_tensor_files':24,'written_tensors':888,'old_new_tensor_equalities':444}


def validate_contract(c,stage):
    from .e5_head_complete24_sampling_r1 import ARMS,AV
    stage=Path(stage)
    cost=json.loads((stage/c['cost_ref']).read_text())
    authority=json.loads((stage/c['authorization_ref']).read_text())
    proof=json.loads((stage/c['sampling_CPU_capture_ref']).read_text())
    if (c['card']!=CARD or c['run_id']!=RUN or c['arms']!=list(ARMS) or c['scope_counts']!=COUNTS
            or c['parent_stage']!=OLD_STAGE or c['working_epoch_strategy']!=STRATEGY
            or c['cost_sha256']!=sha(stage/c['cost_ref'])
            or cost['card']!=CARD or cost['run_id']!=RUN
            or cost['complete_paths']!=24 or cost['independent_model_loads']!=4
            or cost['forecast_complete_GPUh']!=c['forecast_complete_GPUh']
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=77.89524658965853
            or c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),
                'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}
            or c['training'] or c['human_review'] or c['clean_latency_or_quality_frontier_claim']
            or c['empty_cache_or_gate_bypass'] or c['continue_after_failure']!='STOP_RETAIN_COMPLETE_SCOPE'
            or not authority['direct_user_authorization'] or authority['automatic_single_job_gpu_hours']!=8
            or authority['scope']!='CURRENT_WORLD_CACHE_E0_E5_RESEARCH_WINDOW_20261011'
            or authority['usage_reset'] or c['authorization_sha256']!=sha(stage/c['authorization_ref'])
            or authority['cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh']
            or c['sampling_CPU_capture_sha256']!=sha(stage/c['sampling_CPU_capture_ref'])
            or proof['status']!='E5_COMPLETE_SAMPLER_R6_INDEPENDENT_FULL_WRITTEN_EQUIVALENCE_PASS_NOT_GPU'
            or proof['actual_loaded_tensors']!=888 or proof['actual_direct_equalities']!=444
            or proof['driver_recorded_complete_physical_owned_restores']!=96
            or proof['payload_files_unchanged']!=434 or proof['exit_code']!=0 or proof['GPU_submissions']!=0
            or not proof['native_Meta_guard_evidence']['AdaLN_LoRA']
            or not proof['native_Meta_guard_evidence']['Wan_FP32']
            or proof['native_Meta_guard_evidence']['unpatchify']!='PINNED_NATIVE_UNPATCHIFY'
            or proof['native_Meta_guard_evidence']['checkpoint_wrapper_contract']!='PINNED_NATIVE_NON_REENTRANT_SELECTIVE'
            or type(c['GPU_execution_selected']) is not bool):
        raise ValueError('Complete E5 numerical proof, whole cost, scope or current authority differs')
    requests=[json.loads(line) for line in (stage/'e5-head-requests.jsonl').read_text().splitlines() if line]
    if requests!=c['requests'] or [r['name'] for r in requests]!=[AV,'human_199']:
        raise ValueError('Exact two original CAL requests required')
    return cost


def validate(project,stage):
    project,stage=Path(project),Path(stage)
    c=json.loads((stage/CONFIG).read_text());validate_contract(c,stage)
    for n,h in c['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('E5 bound source changed: '+n)
    parent=project/c['parent_stage']
    if sha(parent/'current-birth-full64-config.json')!=c['parent_config_sha256']:
        raise ValueError('Original actual input config changed')
    import wcomr
    fallback=str(parent/'src/wcomr')
    if fallback not in wcomr.__path__:wcomr.__path__.append(fallback)
    from .current_birth_real_production_r1 import validate as validate_parent
    from .e1_diag8_production_r2 import validate_required_assets
    validate_required_assets(c,stage);old,inputs=validate_parent(project,parent)
    for n,h in c['parent_import_source_sha256'].items():
        if sha(parent/n)!=h or (stage/n).exists() and sha(stage/n)!=h:
            raise ValueError('Original immutable input helper changed: '+n)
    expected=[r for r in old['preregistration']['requests'] if r['name'] in [q['name'] for q in c['requests']]]
    expected.sort(key=lambda r:[q['name'] for q in c['requests']].index(r['name']))
    if expected!=c['requests'] or len(expected)!=2:
        raise ValueError('Original actual CAL input binding differs')
    # Verify the original proof against the original terminal CPU stage,
    # rather than treating a local summary alone as numerical acceptance.
    source=project/c['sampling_CPU_stage'];receipt=json.loads((source/'receipt.json').read_text())
    proof=json.loads((stage/c['sampling_CPU_capture_ref']).read_text())
    if (receipt['exit_code']!=0 or sha(source/'receipt.json')!=proof['original_files']['receipt.json']['sha256']
            or any(Path('/proc/'+str(pid)).exists() for pid in proof['original_PIDs_absent'])
            or sha(source/'CPU-artifacts/result.json')!=receipt['result_sha256']
            or any(sha(source/n)!=h for n,h in receipt['payload_after_sha256'].items())
            or any(c['payload_sha256'].get(n)!=h for n,h in receipt['payload_after_sha256'].items())):
        raise ValueError('Original complete CPU source/result identity differs')
    return c,old,inputs


def validate_selected(c,stage):
    stage=Path(stage);p=stage/'production-CPU-receipt.json';r=json.loads(p.read_text())
    if (not c['GPU_execution_selected'] or c['gpu_uuid']!=UUID
            or c['production_CPU_receipt_sha256']!=sha(p) or r['exit_code']!=0
            or r['status']!='E5_COMPLETE24_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
            or r['config_binding_sha256']!=binding(c) or r['CUDA_initialized']
            or r['GPU_submissions'] or r['ledger_written'] or r['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('Same-source whole24 actual production CPU proof required')
    return r


def admit(c,ledger,gpu,proof):
    remaining=ledger['cap_gpu_hours']-ledger['used_gpu_hours']
    if (not math.isfinite(ledger['used_gpu_hours']) or not 0<=ledger['used_gpu_hours']<ledger['cap_gpu_hours']
            or ledger['cap_gpu_hours']!=c['cumulative_cap_GPUh'] or any('inflight' in k for k in ledger)
            or c['forecast_complete_GPUh']>remaining or c['forecast_complete_GPUh']>8
            or gpu['uuid']!=UUID or gpu['compute_cap']!='8.6' or gpu['memory_used_mib']>1024 or gpu['pids']
            or proof['status']!='E5_COMPLETE24_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' or proof['exit_code']!=0
            or proof['config_binding_sha256']!=binding(c)):
        raise ValueError('E5 complete cost, fresh resources or CPU source proof admission failed')
    return remaining,min(8.,remaining)
