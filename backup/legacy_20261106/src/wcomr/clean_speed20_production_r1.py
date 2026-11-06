"""Frozen speed20 contract and immutable deployment inputs, no GPU admission mutation."""
import json, math
from pathlib import Path
from .e1_diag8_production_r2 import UUID, MODE_REF, sha, write
from .clean_speed20_r1 import CARD, RUN, METHODS, SCENES, A_METHOD, STRATEGY, matrix
CONFIG='configs/wc_clean_speed20_r1_20261012.json'

def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['methods']!=list(METHODS) or c['scenes']!=list(SCENES)
        or [r['name'] for r in c['requests']]!=list(SCENES)
        or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93 or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])
        or c['A_method']!=A_METHOD or c['A_boundary']!=25 or c['A_strength']!=[1.,.5]
        or c['early_head_elision'] or c['working_epoch_strategy']!=STRATEGY
        or (c['timed_runs'],c['warmup_runs'],c['total_complete_paths'],c['model_loads'],c['warmups_per_scene_method'])!=(20,20,40,1,2)
        or c['round_orders']!=['forward','reverse'] or c['training'] or c['parameter_sweep']
        or c['per_step_tensor_copies_hashes_checkpoints_files_in_clean_timer']
        or not c['algorithm_caches_anchors_projection_and_candidate_heads_paid']
        or not c['guardrails_retained_outside_main_timer'] or not c['video_write_outside_main_timer']
        or not c['P_mechanism_full_card_remains_deferred'] or not c['E2_original_card_unchanged']
        or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=77.89524658965853
        or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
        or len(c['old_audit_endpoint_and_action_bindings'])!=10):
        raise ValueError('Exact frozen complete speed20 scope required')
    return matrix()

def validate(project,stage,require_CPU=True):
    stage=Path(stage);project=Path(project);reg=json.loads((stage/'registration.json').read_text())
    for n,h in reg['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('Speed20 immutable payload changed: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Frozen runtime changed: '+n)
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    from .e3_complete64_production_r1 import validate as old_validate
    _,_,old,inputs=old_validate(project,project/c['original_parent_stage'])
    if c['requests']!=old['preregistration']['requests'][:2]:raise ValueError('Two original requests changed')
    authority=json.loads((stage/c['authority_ref']).read_text())
    if authority['automatic_single_job_gpu_hours']!=8 or authority['cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh'] or not authority['direct_user_authorization']:
        raise ValueError('Current scoped8 authority missing')
    if require_CPU:
        cp=json.loads((stage/'sampling-CPU-result.json').read_text())
        if cp['status']!='CLEAN_SPEED20_CPU_PASS_NOT_GPU' or cp['actual_CPU_paths']!=60 or cp['CUDA_initialized'] or cp['GPU_submissions']:
            raise ValueError('Accepted complete CPU sampling proof missing')
        for n,h in cp['payload_sha256'].items():
            if reg['payload_sha256'].get(n)!=h:raise ValueError('Production source differs from tested sampling source: '+n)
    return c,reg,old,inputs

def verify_admission(c,ledger,gpu):
    rem=ledger['cap_gpu_hours']-ledger['used_gpu_hours']
    if (ledger['cap_gpu_hours']!=c['cumulative_cap_GPUh'] or not 0<rem<=48
        or any('inflight' in k for k in ledger) or c['forecast_complete_GPUh']>rem
        or gpu['uuid']!=UUID or gpu['compute_cap']!='8.6' or gpu['memory_used_mib']>1024 or gpu['pids']):
        raise ValueError('Fresh complete speed20 GPU/budget admission unavailable')
    return rem,min(8.,rem)
