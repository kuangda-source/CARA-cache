"""Full E2 production dependency checks, without granting a GPU submission."""
import gzip
import json
import math
from pathlib import Path

from .cfg_guided_w1_deployment_production import (
    validate as validate_old_A, bound_prior, FINGERPRINT, THRESHOLD)
from .cfg_ra_calibration_production import sha,binding,WC
from .e2_confirmation_timing_sampling_r1 import expected_matrix

CARD='WC-E2-PHASE-A-CONF40-TIMING32-PARITY4-R1-20261011-A'
RUN='wc-e2-phase-a-conf40-timing32-parity4-r1'
COUNTS={'scientific_paths':72,'confirmation_paths':40,'timing_paths':32,'parity_paths':4,
        'complete_actual_GPU_paths':76,'solver_updates':2736,'CFG_calls':5472}
BASE=Path('.sync/wc-ra-plus-a-production-cpu-r1-20261010')
BASE_SHA='a7c3fb6c69a072cf49c60e0148be05b22650621cd7c2d639fe0643592e64f126'
CONFIG='e2-config.json'
REQUESTS='e2-requests.jsonl'
POLICY='manifests/wc_current_window_execution_authorization_20261011_8gpuh.json'


def validate_contract(c,stage):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
            or c['historical_wc_settings']!=WC or c['RA_calibration_fingerprint']!=FINGERPRINT
            or c['RA_threshold']!=THRESHOLD or c['branch_order']!=['conditional','negative_prompt']
            or c['guided_weights']!=[8,-7] or c['teacher_calls'] or c['training']
            or c['boundary_or_alpha_sweep'] or c['clean_latency_claim'] or c['confirmation_accepted']
            or c['A_phase_boundary']!=25 or c['A_phase_strength']!=[1.,.5]
            or c['original_A_extra_heads_elided'] or c['base_dependency_stage']!=str(BASE)
            or c['base_dependency_config_sha256']!=BASE_SHA
            or c['expected_real_shape']!=[1,16,24,54,96]
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=77.89524658965853
            or type(c['GPU_execution_selected']) is not bool
            or c['sampling_protocol']['actual_steps']!=36 or c['sampling_protocol']['cfg_calls']!=72):
        raise ValueError('Complete E2 scope, unchanged methods, solver or authority differs')
    if sha(stage/c['inputs_ref'])!=c['inputs_sha256']:
        raise ValueError('Frozen E2 input identity changed')
    inputs=json.loads((stage/c['inputs_ref']).read_text());matrix=expected_matrix(inputs)
    actual=[json.loads(s) for s in (stage/REQUESTS).read_text().splitlines() if s]
    if (len(actual)!=10 or actual[:8]!=inputs['requests'] or len({r['name'] for r in actual})!=10
            or {r['name'] for r in actual}!={r['request_name'] for r in matrix}
            or any(r['guidance']!=7 or r['num_steps']!=35 or r['resolution']!='432,768'
                   or r['num_output_frames']!=93 for r in actual)
            or any(r['seed']!=0 for r in actual[8:])):
        raise ValueError('Actual ten complete E2 requests differ')
    forecast=json.loads((stage/c['forecast_ref']).read_text())
    if (sha(stage/c['forecast_ref'])!=c['forecast_sha256'] or forecast['complete_actual_GPU_paths']!=76
            or forecast['forecast_complete_GPUh']!=c['forecast_complete_GPUh']
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<48):
        raise ValueError('Complete E2 cost forecast changed')
    return inputs,actual


def validate(project,stage):
    c=json.loads((stage/CONFIG).read_text());inputs,actual=validate_contract(c,stage)
    for n,h in c['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('E2 frozen source changed: '+n)
    for n,h in c['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('E2 actual runtime changed: '+n)
    base_stage=project/BASE
    if sha(base_stage/'ra-plus-a-config.json')!=BASE_SHA:
        raise ValueError('Read-only accepted baseline dependency changed')
    base,_=validate_old_A(project,base_stage)
    calibration,threshold=bound_prior(base,base_stage)
    if (calibration.fingerprint!=c['RA_calibration_fingerprint'] or threshold['threshold']!=c['RA_threshold']
            or base['sampling_protocol']!=c['sampling_protocol']):
        raise ValueError('Original real calibration or sampler changed')
    if any(r not in base['preregistration']['requests'] for r in actual[8:]):
        raise ValueError('Two actual CAL timing requests are not unchanged original inputs')
    policy=json.loads((stage/POLICY).read_text())
    if (not policy['direct_user_authorization'] or policy['automatic_single_job_gpu_hours']!=8
            or policy['scope']!='CURRENT_WORLD_CACHE_E0_E5_RESEARCH_WINDOW_20261011'
            or policy['usage_reset'] or policy['additional_GPU_budget_granted']
            or policy['cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh']
            or not policy['no_splitting_or_reducing_scope_to_avoid_confirmation']
            or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours']!=c['cumulative_cap_GPUh']):
        raise ValueError('Current E2 window permission or cumulative cap changed')
    proof=json.loads((stage/c['sampler_CPU_capture_ref']).read_text())
    if (proof['exit_code']!=0 or not proof['original_source_and_raw_identity_verified']
            or proof['GPU_submissions']!=0
            or proof['independent_tensor_reload'].get('guided_tensors')!=3168
            or proof['independent_tensor_reload'].get('final_latents')!=152
            or proof['independent_tensor_reload'].get('old_A_direct_parity_paths')!=8):
        raise ValueError('Actual complete E2 sampler CPU acceptance missing')
    reg=json.loads(gzip.decompress((stage/proof['files']['registration.json']['local_path']).read_bytes()))
    result=json.loads(gzip.decompress((stage/proof['files']['result.json']['local_path']).read_bytes()))
    if (result['status']!='E2_FULL76_SAMPLER_CPU_PASS_NOT_REAL_MODEL'
            or result['payload_sha256']!=reg['payload_sha256'] or result['CUDA_initialized']
            or result['successful_complete_paths']!=152 or result['actual_AV28_timing_parity_paths']!=32
            or result['semantic_mutation_refusals']!=20 or result['additional_guardrail_refusals']!=8
            or result['final_timing_truncation_refusals']!=2
            or any(c['payload_sha256'].get(n)!=h for n,h in reg['payload_sha256'].items())):
        raise ValueError('Same-source full E2 CPU proof differs')
    return c,inputs,actual,calibration,threshold


def validate_selected(c,project,stage):
    if not c['GPU_execution_selected'] or c['gpu_uuid']!='GPU-cebf7119-cf03-23b9-e192-cd196332b704':
        raise ValueError('E2 exact selected GPU identity required')
    authority=c['single_job_exception_authority']
    if c['forecast_complete_GPUh']>8:
        if not isinstance(authority,dict) or sha(stage/authority['ref'])!=authority['sha256']:
            raise ValueError('Complete E2 above8 needs direct exact authorization')
        approved=json.loads((stage/authority['ref']).read_text())
        if (not approved['direct_user_authorization'] or approved['card']!=CARD or approved['run_id']!=RUN
                or approved['scope_counts']!=COUNTS or approved['config_binding_sha256']!=binding(c)
                or approved['forecast_complete_GPUh']!=c['forecast_complete_GPUh']):
            raise ValueError('Direct approval does not cover this complete E2 card')
    elif authority is not None:raise ValueError('Within8 uses current autonomous permission')
    receipt=project/c['production_cpu_stage']/'receipt.json'
    if sha(receipt)!=c['production_cpu_receipt_sha256']:
        raise ValueError('Selected E2 actual production CPU receipt changed')
    value=json.loads(receipt.read_text())
    if (value['exit_code']!=0 or value['status']!='E2_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
            or value['config_binding_sha256']!=binding(c) or value['payload_after_sha256']!=c['payload_sha256']
            or value['CUDA_initialized'] or value['GPU_submissions']):
        raise ValueError('Selected E2 same-source production CPU proof missing')
    return value
