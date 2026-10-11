"""Complete E3 identity, immutable original inputs, source proofs and admission."""
import json
import math
from pathlib import Path

from .e1_diag8_production_r2 import (UUID,OLD_STAGE,MODE_REF,MODE_SCRIPT,MODE_SHA,
    sha,write,validate_required_assets,protected_capacity_failure)
from .e3_complete64_block_scope_r1 import validate_scope,validate_block

CARD='WC-E3-CURRENT-BIRTH-COMPLETE64-REUSE10-FRESH54-R1-20261011-A'
RUN='wc-e3-current-birth-complete64-reuse10-fresh54-r1'
CONFIG='e3-complete64-config.json'
REQUESTS='e3-complete64-requests.jsonl'
SCOPE_SHA='051e6207603372cda9253ad623d392b1718575dd07a2ea766721bdc10a580eee'
COUNTS={'scientific_positions':64,'qualified_reused_positions':10,'fresh_complete_paths':54,
    'independent_model_loads':20,'maximum_paths_per_process':3,'fresh_solver_updates':1944,'fresh_CFG_calls':3888}
DYNAMIC={'GPU_execution_selected','gpu_uuid','production_CPU_receipt_sha256','single_job_exception_authority'}


def binding(c):
    import hashlib
    return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in DYNAMIC},
        sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_contract(c,stage):
    stage=Path(stage);scope=json.loads((stage/c['scope_ref']).read_text());actual=validate_scope(scope)
    authority=json.loads((stage/c['authorization_ref']).read_text())
    cost=json.loads((stage/c['whole_cost_ref']).read_text())
    if (c['card']!=CARD or c['run_id']!=RUN or scope['card']!=CARD or scope['run_id']!=RUN
            or c['scope_sha256']!=SCOPE_SHA or sha(stage/c['scope_ref'])!=SCOPE_SHA
            or c['scope_counts']!=COUNTS or c['requests']!=scope['requests'] or c['blocks']!=scope['blocks']
            or c['parent_stage']!=OLD_STAGE or c['automatic_single_job_GPUh']!=8
            or c['cumulative_cap_GPUh']!=77.89524658965853
            or c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),
                'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}
            or c['state_steps']!=[12,30,35,36] or c['training'] or c['clean_latency_claim']
            or c['independent_confirmation_claim'] or c['empty_cache_or_gate_bypass']
            or c['continue_after_protected_failure']!='NEXT_REGISTERED_FRESH_MODEL_PROCESS_ONLY'
            or c['unexpected_failure']!='STOP_RETAIN_ALL64_AND_ALL54_GENERATION_SLOTS'
            or c['one_complete_GPU_card_not20_independent_cards'] is not True
            or type(c['GPU_execution_selected']) is not bool
            or c['authorization_sha256']!=sha(stage/c['authorization_ref'])
            or not authority['direct_user_authorization'] or authority['automatic_single_job_gpu_hours']!=8
            or authority['scope']!='CURRENT_WORLD_CACHE_E0_E5_RESEARCH_WINDOW_20261011'
            or authority['usage_reset'] or authority['cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh']
            or c['whole_cost_sha256']!=sha(stage/c['whole_cost_ref'])
            or c['forecast_complete_GPUh']!=cost['forecast_complete_GPUh']
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<48
            or (cost['scientific_positions'],cost['qualified_reused_positions'],cost['fresh_complete_paths'],
                cost['independent_model_loads'])!=(64,10,54,20)):
        raise ValueError('E3 complete scientific scope, parameters, evidence or whole cost differs')
    actual_requests=[json.loads(line) for line in (stage/REQUESTS).read_text().splitlines() if line]
    if actual_requests!=scope['requests']:raise ValueError('All four original CAL inputs and order required')
    for block in scope['blocks']:validate_block(block,scope)
    capture=json.loads((stage/c['sampling_CPU_capture_ref']).read_text())
    if (sha(stage/c['sampling_CPU_capture_ref'])!=c['sampling_CPU_capture_sha256']
            or capture['receipt']['exit_code']!=0 or capture['receipt']['child_exit_code']!=0
            or not capture['original_source_receipts_complete_scope_and_actual_vectors_independently_verified']
            or capture['receipt']['GPU_submissions'] or capture['receipt']['ledger_written']
            or capture['independent_actual_vector_reads']['actual_written_vector_files_reloaded']!=72
            or capture['independent_actual_vector_reads']['actual_written_tensors_reloaded']!=2664
            or capture['independent_actual_vector_reads']['actual_direct_tensor_comparisons']!=1184):
        raise ValueError('Complete same-source E3 affected CPU original proof required')
    registration=json.loads((stage/c['sampling_CPU_registration_ref']).read_text())
    if (sha(stage/c['sampling_CPU_registration_ref'])!=c['sampling_CPU_registration_sha256']
            or registration['payload_sha256']!=capture['receipt']['payload_after_sha256']
            or any(c['payload_sha256'].get(n)!=h for n,h in registration['payload_sha256'].items())):
        raise ValueError('E3 production does not use the accepted CPU source bytes')
    validate_required_assets(c,stage)
    return scope,actual


def validate(project,stage):
    project,stage=Path(project),Path(stage);c=json.loads((stage/CONFIG).read_text())
    scope,_=validate_contract(c,stage)
    for n,h in c['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('E3 immutable production payload changed: '+n)
    parent=project/c['parent_stage']
    if sha(parent/'current-birth-full64-config.json')!=c['parent_config_sha256']:
        raise ValueError('E3 original full64 inputs changed')
    import wcomr
    old_src=str(parent/'src/wcomr')
    if old_src not in wcomr.__path__:wcomr.__path__.append(old_src)
    from .current_birth_real_production_r1 import validate as validate_parent
    old,inputs=validate_parent(project,parent)
    for n,h in c['parent_import_source_sha256'].items():
        if sha(parent/n)!=h or ((stage/n).exists() and sha(stage/n)!=h):
            raise ValueError('E3 original input helper changed or shadowed: '+n)
    if scope['requests']!=old['preregistration']['requests']:
        raise ValueError('E3 four original request identities differ')
    if c['checkpoint_reserves']!={k:old[k] for k in c['checkpoint_reserves']}:
        raise ValueError('E3 original logical/physical snapshot reserves differ')
    for slot in scope['all64_slots']:
        if slot['disposition']!='REUSE_QUALIFIED_DEV_OUTPUT':continue
        for kind in ('vector_artifact','video_artifact'):
            a=slot['reuse_binding'][kind];p=Path(a['path']).resolve()
            if (not p.is_relative_to((project/'outputs').resolve()) or not p.is_file()
                    or p.stat().st_size!=a['bytes'] or sha(p)!=a['sha256']):
                raise ValueError('E3 qualified reuse original missing or changed')
    return c,scope,old,inputs


def validate_selected(c,stage):
    stage=Path(stage)
    if not c['GPU_execution_selected'] or c['gpu_uuid']!=UUID:
        raise ValueError('E3 exact selected GPU and complete-card source required')
    if c['forecast_complete_GPUh']>8:
        a=c['single_job_exception_authority']
        if not isinstance(a,dict) or sha(stage/a['ref'])!=a['sha256']:
            raise ValueError('E3 complete above8 card needs exact direct approval')
        approved=json.loads((stage/a['ref']).read_text())
        if (not approved['direct_user_authorization'] or approved['card']!=CARD or approved['run_id']!=RUN
                or approved['scope_counts']!=COUNTS or approved['config_binding_sha256']!=binding(c)
                or approved['forecast_complete_GPUh']!=c['forecast_complete_GPUh']):
            raise ValueError('Approval does not cover this whole E3 card')
    elif c['single_job_exception_authority'] is not None:
        raise ValueError('Within8 uses the current scoped autonomous authority')
    path=stage/'production-CPU-receipt.json';r=json.loads(path.read_text())
    if (sha(path)!=c['production_CPU_receipt_sha256'] or r['exit_code']!=0
            or r['status']!='E3_COMPLETE64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
            or r['config_binding_sha256']!=binding(c) or r['CUDA_initialized']
            or r['GPU_submissions'] or r['ledger_written'] or r['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('E3 original production CPU proof differs')
    return r


def admit(c,ledger,gpu,proof):
    remaining=ledger['cap_gpu_hours']-ledger['used_gpu_hours']
    if (not math.isfinite(ledger['used_gpu_hours']) or not 0<=ledger['used_gpu_hours']<ledger['cap_gpu_hours']
            or ledger['cap_gpu_hours']!=c['cumulative_cap_GPUh'] or any('inflight' in k for k in ledger)
            or c['forecast_complete_GPUh']>remaining or gpu['uuid']!=UUID or gpu['compute_cap']!='8.6'
            or gpu['memory_used_mib']>1024 or gpu['pids']
            or proof['status']!='E3_COMPLETE64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' or proof['exit_code']!=0
            or proof['config_binding_sha256']!=binding(c)):
        raise ValueError('E3 fresh whole-card budget, resource or CPU admission differs')
    if c['forecast_complete_GPUh']>8 and not isinstance(c['single_job_exception_authority'],dict):
        raise ValueError('E3 whole above8 requires exact direct complete-card approval')
    return remaining,min(8.,remaining) if c['forecast_complete_GPUh']<=8 else remaining
