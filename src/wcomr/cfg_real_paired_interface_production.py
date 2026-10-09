"""Complete source-bound local CFG teachers; production admission uses existing assets."""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

CARD='WC-W3-REAL-PAIRED-INTERFACE-R1-20261009-A'
RUN='wc-w3-real-paired-interface-r1'
COUNTS={'full_parents':2,'new_videos':2,'actual_state_origins':1,'same_action_comparisons':8,
 'local_CFG_velocity_pairs':16,'net_calls_in_diagnostics':32,'raw_FP32_tensors':48,
 'full_counterfactual_suffixes':0,'endpoint_labels':0,'future_cost_labels':0}
DYNAMIC={'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def binding(c):
    return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in DYNAMIC},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate_contract(c,stage):
    s=c['preregistration'];request=s['confirmation_request']
    original=json.loads((stage/'original-request.jsonl').read_text())
    if (s['card']!=CARD or s['run_id']!=RUN or s['scope_counts']!=COUNTS or s['origins']!=['S22']
            or s['modes']!=['CC','DD'] or s['orders']!=['ORIGINAL','PAIRED'] or s['observers']!=['OFF','ON']
            or s['repetitions']!=['first','second'] or s['snapshot_completed_updates']!=22 or s['snapshot_after_net_call']!=44
            or s['measurement_space']!='POST_DENOISE_BEFORE_SOLVER'
            or s['remaining_parent_policy']!='ORIGINAL_WORLDCACHE_ADAPTIVE_RESTORED_NO_TEACHER_WRITES'
            or original!=s['original_request'] or original['name']!='common_sense_6487f37f-ef57-49ca-afdc-d898922b5191' or original['seed']!=0
            or request!={**original,'name':'common_sense_6487f37f-ef57-49ca-afdc-d898922b5191_seed3','seed':3}
            or request['guidance']!=7 or request['num_steps']!=35 or request['num_output_frames']!=93 or request['resolution']!='432,768'
            or c['execution_run_id']!=RUN or c['cumulative_cap_GPUh']!=50 or c['automatic_single_job_GPUh']!=2
            or type(c['GPU_execution_selected']) is not bool or c['expected_real_components']!=1216
            or c['expected_real_shape']!=[1,16,24,54,96] or c['logical_copy_cap_bytes']!=6*(1<<30)
            or c['workspace_reserve_bytes']!=4*(1<<30) or c['paired_prefix_reserve_bytes']!=4*(1<<30)
            or c['sampling_protocol']['actual_steps']!=36 or c['sampling_protocol']['cfg_calls']!=72
            or c['sampling_protocol']['timesteps']!=s['timesteps']
            or not math.isfinite(s['forecast']['forecast_complete_GPUh']) or not 1.6487813757460874<=s['forecast']['forecast_complete_GPUh']<50
            or s['original_source']!={'path':'configs/cal_w1d8.jsonl','sha256':'7b99d44d9ec5aced6983dccbf1eb930344a84f053f185f423cecd12d94354d84'}):
        raise ValueError('Complete real paired interface scope, request or authority differs')
    if sha(stage/c['preregistration_ref'])!=c['preregistration_sha256'] or json.loads((stage/c['preregistration_ref']).read_text())!=s:
        raise ValueError('Frozen interface preregistration bytes differ')
    if json.loads((stage/'teacher-request.jsonl').read_text())!=request:
        raise ValueError('Interface request bytes/config differ')


def validate(project,stage):
    c=json.loads((stage/'teacher-config.json').read_text());validate_contract(c,stage)
    for name,digest in c['payload_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Passed staged source/evidence changed: '+name)
    for name,digest in c['project_input_sha256'].items():
        if sha(project/name)!=digest:raise ValueError('Original project identity changed: '+name)
    registered=c['preregistration']
    source=project/registered['original_source']['path']
    if sha(source)!=registered['original_source']['sha256']:
        raise ValueError('Original registered Common source changed')
    rows=[json.loads(line) for line in source.read_text().splitlines() if line]
    matched=[row for row in rows if row.get('name')==registered['original_request']['name']]
    if matched!=[registered['original_request']]:
        raise ValueError('Original complete Common request differs or is ambiguous')
    for name,digest in c['runtime_source_sha256'].items():
        if sha(project/'runtime'/name)!=digest:raise ValueError('Actual runtime source changed: '+name)
    policy=json.loads((stage/'manifests/wc_execution_autonomy_authorization_20261007.json').read_text())
    authority=json.loads((stage/'manifests/budget_authorization_20261008_wc_50gpuh.json').read_text())
    if (policy['automatic_single_job_gpu_hours']!=2 or policy['usage_reset'] or not policy['legacy_per_card_seconds_caps_revoked']
            or authority['new_cumulative_cap_gpu_hours']!=50 or not authority['direct_user_authorization']
            or authority['usage_reset'] or authority['automatic_single_job_gpu_hours']!=2
            or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours']!=50):
        raise ValueError('Actual direct budget/autonomy authority differs')
    core=json.loads((stage/c['core_registration_ref']).read_text())
    if any(c['payload_sha256'].get(name)!=digest for name,digest in core['payload_sha256'].items()):
        raise ValueError('Passed collector CPU implementation changed')
    proof=json.loads(gzip.decompress((stage/c['core_independent_audit_ref']).read_bytes()))
    receipt=json.loads(gzip.decompress((stage/c['core_receipt_ref']).read_bytes()))
    if (proof['status']!='COLLECTOR_CPU_INDEPENDENT_RAW_TENSORS_COMPLETE_SCOPE_AND_ACTION_AUDIT_PASS_NOT_GPU'
            or proof['successful_CFG_pairs']!=80 or proof['raw_tensors_reconstructed']!=240
            or len(proof['failed_attempts_retained'])!=6 or proof['CUDA_initialized'] or proof['GPU_submissions']
            or proof['separate_net_input_condition_witnesses_verified']!=448
            or proof['separate_solver_space_witnesses_verified']!=152
            or receipt['status']!='MEASUREMENT_COLLECTOR_AND_INDEPENDENT_CPU_AUDIT_COMPLETE_NOT_GPU'
            or receipt['core_exit_code']!=0 or receipt['audit_exit_code']!=0
            or receipt['exit_code']!=0 or receipt['source_revision']!='7dc74962326971683bd26cc00fd0aa8f49524379'
            or receipt['payload_after_sha256']!=core['payload_sha256']
            or receipt['budget_before_sha256']!=receipt['budget_after_sha256']):
        raise ValueError('Actual complete collector CPU evidence differs')
    spec=importlib.util.spec_from_file_location('existing_assets',stage/'scripts/run_wc_s0_profile.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.validate(project,stage,project/'runtime')
    paired=json.loads((stage/c['paired_cpu_registration_ref']).read_text())
    if any(c['payload_sha256'].get(n)!=v for n,v in paired['payload_sha256'].items()):
        raise ValueError('Passed actual paired batch CPU source changed')
    paired_receipt=json.loads(gzip.decompress((stage/c['paired_cpu_receipt_ref']).read_bytes()))
    paired_result=json.loads(gzip.decompress((stage/c['paired_cpu_result_ref']).read_bytes()))
    paired_audit=json.loads((stage/c['paired_cpu_audit_ref']).read_text())
    if (paired_receipt['exit_code']!=0 or paired_receipt['child_exit_code']!=0
            or paired_receipt['status']!='PAIRED_INTERFACE_ACTUAL_BATCH_CPU_NOT_REAL_MODEL'
            or paired_receipt['source_revision']!=c['paired_cpu_source_revision']
            or paired_receipt['payload_after_sha256']!=paired['payload_sha256']
            or paired_receipt['budget_before_sha256']!=paired_receipt['budget_after_sha256']
            or paired_result['planned_scope']!=paired['CPU_scope'] or paired_result['CUDA_initialized'] or paired_result['GPU_submissions']
            or len(paired_result['checks'])!=68 or paired_audit['exit_code']!=0
            or paired_audit['actual_new_batch_pairs']!=32 or paired_audit['actual_Toy_raw_tensors_reloaded']!=96
            or paired_audit['actual_new_batch_writer_failures']!=2 or paired_audit['actual_new_batch_semantic_mutation_refusals']!=20):
        raise ValueError('Complete actual new paired batch CPU evidence missing')
    return c,stage


def validate_selected(c,project,stage):
    forecast=c['preregistration']['forecast']['forecast_complete_GPUh'];authority=c.get('single_job_exception_authority')
    if forecast>2:
        if not isinstance(authority,dict) or set(authority)!={'ref','sha256'} or sha(stage/authority['ref'])!=authority['sha256']:
            raise ValueError('Whole teacher card >2GPUh needs direct specific approval')
        proof=json.loads((stage/authority['ref']).read_text())
        if (not proof.get('direct_user_authorization') or proof.get('card')!=CARD or proof.get('run_id')!=RUN
                or proof.get('scope_counts')!=COUNTS or proof.get('approved_forecast_GPUh')!=forecast):
            raise ValueError('Teacher direct exception scope differs')
    elif authority is not None:raise ValueError('Unexpected single job exception for <=2GPUh')
    if not c['GPU_execution_selected'] or c['gpu_uuid']!='GPU-cebf7119-cf03-23b9-e192-cd196332b704':
        raise ValueError('Fresh selected teacher target required')
    p=project/c['production_cpu_stage']/'receipt.json'
    if sha(p)!=c['production_cpu_receipt_sha256']:raise ValueError('Actual production CPU receipt changed')
    proof=json.loads(p.read_text())
    if (proof['exit_code']!=0 or proof['status']!='REAL_PAIRED_INTERFACE_PRODUCTION_CPU_PASS_NOT_GPU'
            or proof['CUDA_initialized'] or proof['GPU_submissions'] or proof['config_binding_sha256']!=binding(c)
            or proof['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('Same-source complete production CPU proof missing')
    return proof
