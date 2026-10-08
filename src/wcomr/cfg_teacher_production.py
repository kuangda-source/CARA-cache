"""Complete source-bound local CFG teachers; production admission uses existing assets."""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

CARD='WC-W3-CFG-GUIDED-TEACHER-R1-20261009-A'
RUN='wc-w3-cfg-guided-teacher-r1'
COUNTS={'full_parents':2,'new_videos':2,'actual_state_origins':5,'action_cells_per_origin':4,
    'strict_repeats_per_cell':2,'local_CFG_velocity_pairs':40,'net_calls_in_diagnostics':80,
    'full_counterfactual_suffixes':0,'endpoint_labels':0}
DYNAMIC={'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def binding(c):
    return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in DYNAMIC},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate_contract(c,stage):
    s=c['preregistration'];request=s['same_existing_request']
    original=json.loads((stage/'original-request.jsonl').read_text())
    if (s['card']!=CARD or s['run_id']!=RUN or s['scope_counts']!=COUNTS or s['origins']!=['S22','S23_after_CC','S23_after_DC','S23_after_CD','S23_after_DD']
            or s['modes']!=['CC','DC','CD','DD'] or s['repetitions']!=['first','second'] or s['snapshot_completed_updates']!=22
            or s['snapshot_after_net_call']!=44 or s['advance_reuses_first_measured_velocity'] is not True
            or s['measurement_space']!='POST_DENOISE_BEFORE_SOLVER' or s['teacher']!='DD_WITHIN_EACH_OWN_STATE'
            or s['remaining_parent_policy']!='ORIGINAL_WORLDCACHE_ADAPTIVE_RESTORED_NO_TEACHER_WRITES'
            or request!=original or request['name']!='human_199_seed2' or request['seed']!=2 or request['guidance']!=7
            or request['num_steps']!=35 or request['num_output_frames']!=93 or request['resolution']!='432,768'
            or c['execution_run_id']!=RUN or c['cumulative_cap_GPUh']!=50 or c['automatic_single_job_GPUh']!=2
            or type(c['GPU_execution_selected']) is not bool or c['expected_real_components']!=1216
            or c['expected_real_shape']!=[1,16,24,54,96] or c['logical_copy_cap_bytes']!=6*(1<<30)
            or c['workspace_reserve_bytes']!=4*(1<<30) or c['sampling_protocol']['actual_steps']!=36
            or c['sampling_protocol']['cfg_calls']!=72 or c['sampling_protocol']['timesteps']!=s['timesteps']
            or not 0<s['forecast']['forecast_complete_GPUh']<50):
        raise ValueError('Complete registered teacher scope, request, measurement or authority differs')
    if sha(stage/c['preregistration_ref'])!=c['preregistration_sha256'] or json.loads((stage/c['preregistration_ref']).read_text())!=s:
        raise ValueError('Frozen teacher preregistration bytes differ')
    if json.loads((stage/'teacher-request.jsonl').read_text())!=request:
        raise ValueError('Teacher request bytes/config differ')


def validate(project,stage):
    c=json.loads((stage/'teacher-config.json').read_text());validate_contract(c,stage)
    for name,digest in c['payload_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Passed staged source/evidence changed: '+name)
    for name,digest in c['project_input_sha256'].items():
        if sha(project/name)!=digest:raise ValueError('Original project identity changed: '+name)
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
    proof=json.loads((stage/c['core_independent_audit_ref']).read_text())
    receipt=json.loads(gzip.decompress((stage/c['core_receipt_ref']).read_bytes()))
    if (proof['status']!='COLLECTOR_CPU_INDEPENDENT_RAW_TENSORS_COMPLETE_SCOPE_AND_ACTION_AUDIT_PASS_NOT_GPU'
            or proof['successful_CFG_pairs']!=80 or proof['raw_tensors_reconstructed']!=240
            or len(proof['failed_attempts_retained'])!=6 or proof['CUDA_initialized'] or proof['GPU_submissions']
            or receipt['exit_code']!=0 or receipt['source_revision']!='a417fa98a5c50b36652c992935051a7f930ad323'
            or receipt['payload_after_sha256']!=core['payload_sha256']
            or receipt['budget_before_sha256']!=receipt['budget_after_sha256']):
        raise ValueError('Actual complete collector CPU evidence differs')
    spec=importlib.util.spec_from_file_location('existing_assets',stage/'scripts/run_wc_s0_profile.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.validate(project,stage,project/'runtime')
    prior=c['preregistration']['existing_BASE'];p=Path(prior['path'])
    if p.stat().st_size!=prior['bytes'] or sha(p)!=prior['sha256']:
        raise ValueError('Frozen ancillary old BASE changed')
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
    if (proof['exit_code']!=0 or proof['status']!='TEACHER_PRODUCTION_CPU_PASS_NOT_GPU'
            or proof['CUDA_initialized'] or proof['GPU_submissions'] or proof['config_binding_sha256']!=binding(c)
            or proof['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('Same-source complete production CPU proof missing')
    return proof
