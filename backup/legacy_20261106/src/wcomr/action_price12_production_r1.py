"""Whole12/944 action-price contract; no configuration selection or dispatch.

The original32-path local proof covers the sampling adapter. A later real
production CPU check must separately import the pinned Cosmos entry point.
"""
import json
from pathlib import Path

from .action_price16_cost_r1 import COUNTS, registered_plan, source_costs, estimate
from .frozen_shared_production_r1 import number, sha

CONFIG='configs/wc_paper_N09_action12_production_r1_20261016.json'
SCOPE='manifests/wc_paper_N09_action16_prices_scope_r2_20261016.json'
RUN='wc-paper-n09-current-action12-r1'
CARD='WC-PAPER-N09-CURRENT-ACTION12-FULL944-R1'
CPU_RESULT='N09-action12-production-CPU-result.json'
CPU_STATUS='N09_ACTION12_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
ADAPTER_SOURCES=('src/wcomr/action_price12_execution_r1.py',
    'src/wcomr/action_price16_collection_r1.py','src/wcomr/post_probe_action_clock_r1.py')


def read_reference(stage,binding):
    from .balanced_repeat_production_r1 import read_reference as original
    return original(stage,binding)


def clean_registered_jobs(pool,own_run):
    from .balanced_repeat_production_r1 import clean_registered_jobs as original
    return original(pool,own_run)


def validate_contract(config,scope,shared,quote):
    registered_plan(scope)
    if (config['card']!=CARD or config['run_id']!=RUN or config['scope_counts']!=COUNTS
            or config['bound_action_fingerprint']!=scope['fingerprint']
            or config['strategy']!=STRATEGY or config['parent_method']!='P_OFF'
            or config['readout']!='BETA1_ONE_PHASE'
            or config['memory_policy']!='REQUEST_BOUNDARY_GC_ONLY'
            or config['autonomy_exclusive_upper_GPUh']!=12
            or config['guardrails_enabled'] is not True
            or config['incremental_clock_boundary']!=scope['cost_boundary']
            or config['research_capture_charged_to_whole_card'] is not True
            or any(config[k] for k in ('training','online_teachers','F_B_enabled',
                'P_ACR','T1','head_elision','new_prices_deployed','clean_repeated_latency_claim'))):
        raise ValueError('Keep the complete action12 scope and unchanged guarded parent policy')
    cost,limit,cap,origin=(config[k] for k in ('forecast_complete_GPUh','billed_limit_GPUh',
        'cumulative_cap_GPUh','budget_origin_used_GPUh'))
    if (not all(number(v) for v in (cost,limit,cap,origin)) or not 0<cost<=limit
            or cap<shared['cumulative_cap_GPUh'] or origin!=shared['budget_origin_used_GPUh']
            or not 0<=origin<cap or cost!=quote['forecast_complete_GPUh']
            or limit!=quote['billed_limit_GPUh'] or quote['scope_counts']!=COUNTS
            or quote['scope_fingerprint']!=scope['fingerprint']
            or quote['new_GPU_card_selected'] or quote['actual_new_action_prices_measured']):
        raise ValueError('Explicit complete diagnostic cost and the unchanged budget origin required')
    return scope


def completed_mainline(data,refs):
    """Accept only the original completed common test and repeated timing card."""
    from .frozen_shared_acceptance_r1 import accept as accept_shared
    from .balanced_repeat_acceptance_r1 import accept as accept_repeated
    shared,freeze,protocol=(data[k] for k in ('shared_config','method_freeze','timing_protocol'))
    c7,c8=(data[k] for k in ('N07_capture','N08_capture'))
    a7,a8=(data[k] for k in ('N07_acceptance','N08_acceptance'))
    if (refs['method_freeze']!=shared['references']['method_freeze']
            or freeze['parameters_frozen_from']!='DEVELOPMENT_ONLY' or freeze['final_test_outputs_seen']
            or freeze['method_ids']!=shared['method_ids']
            or a7.get('terminal_receipt_audit_accepted') is not True
            or a7.get('scientific_available_cohorts_with_registered_missingness') is not True
            or a7.get('original_runner_paths')!=180
            or a8.get('terminal_receipt_audit_accepted') is not True
            or a8.get('full_raw_and_fidelity_scope_accepted') is not True
            or a8.get('own_GPU_and_finance_released') is not True
            or a8.get('original_runner_paths')!=40 or a8.get('original_CPU_post_exit_code')!=0):
        raise ValueError('Collect and accept the original complete N07/N08 before action-price production')
    if (c7['config_sha256']!=refs['shared_config']['sha256']
            or c8['shared_config_sha256']!=refs['shared_config']['sha256']
            or c8['shared_config']!=shared or c8['timing_protocol']!=protocol or c8['method_freeze']!=freeze
            or a7['capture_sha256']!=refs['N07_capture']['sha256']
            or a7['source_revision']!=c7['launch']['source_revision']
            or a8['source_revision']!=c8['launch']['source_revision']):
        raise ValueError('The original mainline scope, source or method freeze differs')
    for accepted,recomputed in ((a7,accept_shared(c7,c7['launch'])),
                                (a8,accept_repeated(c8,c8['launch']))):
        if any(accepted.get(k)!=v for k,v in recomputed.items()):
            raise ValueError('Recompute original mainline acceptance from its captured raw evidence')


def referenced_contract(stage):
    from .frozen_shared_production_r1 import CONFIG as SHARED_CONFIG
    stage=Path(stage);config=json.loads((stage/CONFIG).read_text());refs=config['references']
    names={'shared_config','method_freeze','timing_protocol','N07_acceptance','N08_acceptance',
        'N07_capture','N08_capture','action_scope','whole_cost','adapter_CPU_preparation',
        'adapter_CPU_raw','adapter_CPU_acceptance'}
    if (set(refs)!=names or refs['shared_config']['ref']!=SHARED_CONFIG
            or refs['action_scope']['ref']!=SCOPE):
        raise ValueError('Original shared, natural16, full-cost and complete CPU references required')
    data={name:read_reference(stage,ref) for name,ref in refs.items()}
    completed_mainline(data,refs)
    scope,quote=data['action_scope'],data['whole_cost']
    bound=validate_contract(config,scope,data['shared_config'],quote)
    values={name:read_reference(stage,ref) for name,ref in scope['references'].items()}
    if (scope['references']['current_frozen_shared_config']!=refs['shared_config']
            or scope['references']['final_five_role_freeze']!=refs['method_freeze']
            or scope['requests']!=values['old_source_phase_contract']['requests']
            or scope['states']!=values['natural_state_selection']['states']
            or values['natural_state_selection']['parent_method']!='P_OFF'
            or values['math_parameters']['gamma']!=values['H1_parameters']['gamma']):
        raise ValueError('Do not replace original four CAL, natural16 or source-aware readout parameters')
    for name,entry in scope['source_bindings'].items():
        if sha(stage/name)!=entry['sha256']:
            raise ValueError('The original action measurement source changed: '+name)
    qrefs=quote['references']
    if qrefs['scope']!=refs['action_scope'] or qrefs['historical_D_allowance']!=scope['references']['H1_parameters']:
        raise ValueError('The full cost belongs to another registered matrix or cost allowance')
    source=source_costs(read_reference(stage,qrefs['source_capture']),
        read_reference(stage,qrefs['source_acceptance']),capture_sha256=qrefs['source_capture']['sha256'])
    expected=estimate(scope,source,frozen_historical_D_incremental_seconds=values['H1_parameters']['cost_seconds']['D'])
    if any(quote.get(k)!=v for k,v in expected.items()):
        raise ValueError('Recompute every whole-card cost component before production')
    raw,accepted,prep=(data[k] for k in ('adapter_CPU_raw','adapter_CPU_acceptance','adapter_CPU_preparation'))
    if (raw['status']!='N09_ACTION12_ADAPTER_FULL32_CPU_PASS_NOT_PRODUCTION'
            or accepted['status']!='N09_ACTION12_FULL32_RAW1528_CPU_INDEPENDENTLY_ACCEPTED_NOT_PRODUCTION'
            or prep['status']!='N09_ACTION12_FULL32_RAW1528_AND_WHOLE_COST_CPU_PREPARED_NOT_PRODUCTION'
            or accepted['result_sha256']!=refs['adapter_CPU_raw']['sha256']
            or prep['original_sha256']!=refs['adapter_CPU_raw']['sha256']
            or prep['independent_acceptance_sha256']!=refs['adapter_CPU_acceptance']['sha256']
            or raw['actual_complete_CPU_paths']!=32 or accepted['registered_adapter_CPU_paths']!=24
            or accepted['additional_Toy_selection_reference_paths']!=8
            or raw['actual_pairs']!=2176 or accepted['raw_files']!=112 or accepted['raw_tensors']!=1528
            or raw['CUDA_initialized'] or raw['actual_Cosmos_production_CPU']
            or raw['final_source_verification']['passed'] is not True
            or prep['actual_GPU_card_selected'] or prep['actual_GPU_action_prices']):
        raise ValueError('Original full32/112 files/1528 tensors local CPU proof required')
    sources={}
    for name in ADAPTER_SOURCES:
        digest=sha(stage/name)
        if raw['source_sha256'].get(name)!=digest:
            raise ValueError('Current action adapter differs from the complete CPU proof: '+name)
        sources[name]=digest
    archive=prep['archive_adapter_reused_unchanged_HEAD']
    if sha(stage/archive['path'])!=archive['sha256']:
        raise ValueError('The reused full36 artifact boundary changed')
    if (len(raw['runtime_source_sha256'])!=9 or prep['runtime_source_files_verified']!=9
            or prep['original_exit']['exit_code']!=0
            or prep['original_exit']['result_sha256']!=refs['adapter_CPU_raw']['sha256']):
        raise ValueError('Original numerical CPU process did not finish complete runtime/source verification')
    reused=dict(original_complete_CPU_paths=32,registered_adapter_CPU_paths=24,
        independently_reloaded_files=112,independently_reloaded_tensors=1528,source_sha256=sources,
        archive_source=archive,new_full32_paths_run=0)
    return config,data,bound,reused


def validate(project,stage):
    from .frozen_shared_production_r1 import validate as shared_validate
    config,data,bound,reused=referenced_contract(stage)
    shared,registration,old,inputs,tables,previous,shared_bound,numeric=shared_validate(project,stage)
    params=read_reference(stage,bound['references']['math_parameters'])
    baseline=read_reference(stage,bound['references']['old_parent_endpoint_bindings'])
    if (shared!=data['shared_config'] or params!=previous
            or set(baseline['bindings'])!={r['name'] for r in bound['requests']}):
        raise ValueError('Original physical parameters or all four parent endpoint bindings differ')
    runtime=Path(project)/'runtime'
    for name,digest in data['adapter_CPU_raw']['runtime_source_sha256'].items():
        if sha(runtime/name)!=digest:raise ValueError('Pinned full32 local runtime differs: '+name)
    reused['shared_numeric_reuse']=numeric
    return config,registration,old,inputs,params,baseline,bound,reused


def validate_authority(config,bound,registration,proof,authority,*,revision,gpu_uuid,
                       config_sha256,proof_sha256,registration_sha256):
    if (registration['source_revision']!=revision or proof['source_revision']!=revision
            or proof['status']!=CPU_STATUS or proof['exit_code']!=0
            or proof['registration_sha256']!=registration_sha256 or proof['config_sha256']!=config_sha256
            or proof['bound_action_fingerprint']!=bound['fingerprint'] or proof['scope_counts']!=COUNTS
            or proof.get('CUDA_initialized') is not False or proof.get('GPU_submissions')!=0
            or proof.get('model_weights_loaded')!=0 or proof.get('ledger_written') is not False
            or proof.get('actual_sample_argument_variants')!=4
            or proof.get('matrix')!=bound['complete_parent_matrix']
            or proof.get('guardrail_checks')!=[dict(scene=r['name'],unguarded_execution_refused=True) for r in bound['requests']]
            or not authority.get('launch_id') or authority.get('direct_user_authorization') is not True
            or not authority.get('user_reply_quote')):
        raise ValueError('Original actual action12 production CPU and complete-card authority required')
    expected=dict(source_revision=revision,config_sha256=config_sha256,production_CPU_sha256=proof_sha256,
        bound_input_fingerprint=bound['fingerprint'],bound_action_fingerprint=bound['fingerprint'],
        scope_counts=COUNTS,whole_card_run=RUN,gpu_uuid=gpu_uuid,
        forecast_complete_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
        cumulative_cap_GPUh=config['cumulative_cap_GPUh'],budget_origin_used_GPUh=config['budget_origin_used_GPUh'])
    if any(authority.get(k)!=v for k,v in expected.items()):
        raise ValueError('Full12 source, actual CPU, cost or selected UUID differs')
    allowed=('STANDING_STRICT_UNDER12','SPECIFIC_WHOLE_CARD_APPROVAL') if config['billed_limit_GPUh']<12 else (
        'SPECIFIC_WHOLE_CARD_APPROVAL',)
    if authority.get('kind') not in allowed:raise ValueError('At or above12GPUh needs specific complete-card approval')
