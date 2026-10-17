"""N09 whole40 production contract; actual config/quote are selected after N08."""
import json
from pathlib import Path

from .balanced_repeat_production_r1 import read_reference, clean_registered_jobs
from .frozen_shared_production_r1 import fingerprint, number, sha
from .runtime_profile40_execution_r1 import bind, COUNTS

CONFIG='configs/wc_paper_N09_runtime_profile40_production_r1_20261016.json'
RUN='wc-paper-n09-runtime-profile40-r1'
CARD='WC-PAPER-N09-RUNTIME-PROFILE40-R1'
CPU_RESULT='N09-production-CPU-result.json'
CPU_STATUS='N09_FULL40_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
PROFILE_SOURCES=('src/wcomr/deployment_profile_r1.py','src/wcomr/frozen_shared_execution_r1.py',
                 'src/wcomr/paper_baseline_grid_r1.py','src/wcomr/simple26d_memory_r2.py')


def validate_contract(config,scope,protocol,freeze,shared):
    if (config['card']!=CARD or config['run_id']!=RUN or config['scope_counts']!=COUNTS
            or config['main_timing']!='SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING'
            or config['strategy']!='WORKING_P_AGE_NONZERO_REBASE'
            or config['memory_policy']!='REQUEST_BOUNDARY_GC_ONLY'
            or config['deployment_profiling'] is not True or config['guardrails_enabled'] is not True
            or config['clean_repeated_latency_claim'] is not False
            or config['autonomy_exclusive_upper_GPUh']!=12
            or any(config[k] for k in ('training','online_teachers','F_B_enabled','P_ACR','T1','head_elision'))
            or freeze['method_ids']!=shared['method_ids']):
        raise ValueError('Original full40 profile diagnostic and unchanged frozen implementation required')
    bound=bind(scope,protocol,freeze)
    if config['bound_profile_fingerprint']!=fingerprint(bound):
        raise ValueError('Original modes, order, inputs or method selection changed')
    cost,limit,cap,origin=(config[k] for k in ('forecast_complete_GPUh','billed_limit_GPUh',
        'cumulative_cap_GPUh','budget_origin_used_GPUh'))
    if (not all(number(v) for v in (cost,limit,cap,origin)) or not 0<cost<=limit
            or cap<shared['cumulative_cap_GPUh'] or origin!=shared['budget_origin_used_GPUh']):
        raise ValueError('Explicit whole diagnostic cost and the unchanged cumulative budget origin required')
    return bound


def referenced_contract(stage):
    """Bind saved completed-mainline evidence without loading physical runtime inputs."""
    from .frozen_shared_production_r1 import CONFIG as SHARED_CONFIG
    from .frozen_shared_acceptance_r1 import accept as accept_shared
    from .balanced_repeat_acceptance_r1 import accept as accept_repeated
    from .completed_shared_repair_binding_r2 import is_repair_capture, accepted_repair_identity
    stage=Path(stage);config=json.loads((stage/CONFIG).read_text());refs=config['references']
    names={'shared_config','method_freeze','timing_protocol','runtime_scope','profile_CPU_acceptance',
           'profile_CPU_capture','N07_acceptance','N08_acceptance','N07_capture','N08_capture'}
    if set(refs)!=names or refs['shared_config']['ref']!=SHARED_CONFIG:
        raise ValueError('Original shared, frozen scope, observer and completed-mainline evidence required')
    data={name:read_reference(stage,ref) for name,ref in refs.items()}
    shared=data['shared_config'];freeze=data['method_freeze']
    if refs['method_freeze']!=shared['references']['method_freeze']:
        raise ValueError('Keep the same original five-role freeze as the common test')
    bound=validate_contract(config,data['runtime_scope'],data['timing_protocol'],freeze,shared)
    a7,a8=data['N07_acceptance'],data['N08_acceptance']
    if (a7.get('terminal_receipt_audit_accepted') is not True
            or a7.get('scientific_available_cohorts_with_registered_missingness') is not True
            or a7.get('original_runner_paths')!=180
            or a8.get('terminal_receipt_audit_accepted') is not True
            or a8.get('full_raw_and_fidelity_scope_accepted') is not True
            or a8.get('own_GPU_and_finance_released') is not True
            or a8.get('original_runner_paths')!=40 or a8.get('original_CPU_post_exit_code')!=0):
        raise ValueError('Collect and accept the original complete N07/N08 before the independent diagnostic')
    c7,c8=data['N07_capture'],data['N08_capture']
    repaired=is_repair_capture(c7)
    if ((not repaired and c7['config_sha256']!=refs['shared_config']['sha256'])
            or c8['shared_config_sha256']!=refs['shared_config']['sha256'] or c8['shared_config']!=shared
            or c8['timing_protocol']!=data['timing_protocol'] or c8['method_freeze']!=freeze
            or a7['capture_sha256']!=refs['N07_capture']['sha256']
            or a7['source_revision']!=c7['launch']['source_revision']
            or a8['source_revision']!=c8['launch']['source_revision']):
        raise ValueError('The completed mainline evidence belongs to another shared config, freeze or timing scope')
    completed_repair = (accepted_repair_identity(a7,c7,capture_sha256=refs['N07_capture']['sha256'],
        original_shared_config=shared,original_shared_config_sha256=refs['shared_config']['sha256'])
        if repaired else None)
    if a8.get('offline_roundoff_bridge') is not None:
        from .balanced_repeat_roundoff_acceptance_r1 import VERSION, accept as accept_registered_bridge
        if a8['offline_roundoff_bridge'].get('version')!=VERSION:
            raise ValueError('Only the registered source-bound N08 derived-statistic bridge is supported')
        repeated_recomputed=accept_registered_bridge(c8,c8['launch'])
    else:
        repeated_recomputed=accept_repeated(c8,c8['launch'])
    originals=[(a8,repeated_recomputed)]
    if not repaired:originals.append((a7,accept_shared(c7,c7['launch'])))
    for accepted,recomputed in originals:
        if any(accepted.get(k)!=v for k,v in recomputed.items()):
            raise ValueError('Recompute the original saved mainline acceptance before profile execution')
    accepted=data['profile_CPU_acceptance'];capture=data['profile_CPU_capture']
    if (accepted['status']!='DEPLOYMENT_PROFILE_FULL102_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU_PROFILE'
            or accepted['actual_CPU_paths']!=102 or accepted['ordinary_pairs']!=3516
            or accepted['CFG_calls']!=7032 or accepted['capture_sha256']!=refs['profile_CPU_capture']['sha256']
            or accepted['source_revision']!=capture['launch']['source_revision']):
        raise ValueError('Original accepted whole102 observer proof required')
    sources={}
    for name in PROFILE_SOURCES:
        digest=sha(stage/name)
        if (digest!=data['runtime_scope']['source_bindings'][name]['sha256']
                or capture['payload_actual_sha256'].get(name)!=digest):
            raise ValueError('An actual original102 observer/numerical source changed: '+name)
        sources[name]=digest
    reused=dict(original_full102_CPU_paths=102,source_sha256=sources,new_full102_paths_run=0)
    if completed_repair is not None:reused['completed_N07_repair']=completed_repair
    return config,data,bound,reused


def validate(project,stage):
    from .frozen_shared_production_r1 import validate as shared_validate
    config,data,bound,reused=referenced_contract(stage)
    actual,registration,old,inputs,tables,previous,shared_bound,numeric=shared_validate(project,stage)
    if actual!=data['shared_config'] or shared_bound['method_ids']!=bound['final_shared_method_ids']:
        raise ValueError('The current shared inference binding differs from the original freeze')
    reused['shared_numeric_reuse']=numeric
    return config,registration,old,inputs,tables,previous,bound,reused


def validate_authority(config,bound,registration,proof,authority,*,revision,gpu_uuid,
                       config_sha256,proof_sha256,registration_sha256):
    if (registration['source_revision']!=revision or proof['source_revision']!=revision
            or proof['status']!=CPU_STATUS or proof['exit_code']!=0
            or proof['registration_sha256']!=registration_sha256 or proof['config_sha256']!=config_sha256
            or proof['bound_profile_fingerprint']!=fingerprint(bound) or proof['scope_counts']!=COUNTS
            or proof.get('CUDA_initialized') is not False or proof.get('GPU_submissions')!=0
            or proof.get('model_weights_loaded')!=0 or proof.get('ledger_written') is not False
            or proof.get('actual_sample_argument_variants')!=10 or proof.get('matrix')!=bound['execution_plan']
            or proof.get('guardrail_checks')!=[dict(scene=r['name'],unguarded_execution_refused=True) for r in bound['requests']]
            or not authority.get('launch_id') or authority.get('direct_user_authorization') is not True
            or not authority.get('user_reply_quote')):
        raise ValueError('Original actual N09 production CPU and whole-card authority required')
    expected=dict(source_revision=revision,config_sha256=config_sha256,production_CPU_sha256=proof_sha256,
        bound_input_fingerprint=fingerprint(bound),scope_counts=COUNTS,whole_card_run=RUN,gpu_uuid=gpu_uuid,
        forecast_complete_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
        cumulative_cap_GPUh=config['cumulative_cap_GPUh'],budget_origin_used_GPUh=config['budget_origin_used_GPUh'])
    if any(authority.get(k)!=v for k,v in expected.items()):
        raise ValueError('The full40 source, observed CPU, UUID or quoted scope differs')
    allowed=('STANDING_STRICT_UNDER12','SPECIFIC_WHOLE_CARD_APPROVAL') if config['billed_limit_GPUh']<12 else (
        'SPECIFIC_WHOLE_CARD_APPROVAL',)
    if authority.get('kind') not in allowed:raise ValueError('At or above12GPUh needs specific complete-card approval')
