"""Source-bound complete shared-anchor guided-W1 collection and resource admission."""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

CARD = 'WC-MF-A-GUIDED-W1-COLLECTION-R1-20261010-A'
RUN = 'wc-mf-a-guided-w1-collection-r1'
NAMES = ['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199','misc_13398218_3840_2160_60fps','av_51b45829-502e-4143-9c32-c026bd6ab191']
COUNTS = {'requests': 4, 'complete_parent_paths': 8, 'new_videos': 8, 'parent_solver_updates': 288, 'normal_net_calls': 576, 'same_state_origins': 8, 'score_only_deep_branch_calls': 16, 'score_only_deep_block_calls': 416, 'additional_candidate_and_teacher_heads': 48, 'post_RF_branch_tensors': 64, 'parent_guided_tensors': 288, 'parent_latents': 8, 'raw_tensor_files': 16}
DYNAMIC = {'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}
WC = {'worldcache_num_steps':35,'worldcache_rel_l1_thresh':.06,'worldcache_ret_ratio':.2,
    'probe_depth':2,'worldcache_motion_sensitivity':2.,'worldcache_flow_enabled':True,
    'worldcache_flow_scale':2.,'worldcache_saliency_enabled':True,'worldcache_saliency_weight':1.,
    'worldcache_osi_enabled':True,'worldcache_dynamic_decay':True}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def binding(c):
    return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in DYNAMIC},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate_contract(c,stage):
    reg=c['preregistration']
    if (reg['card']!=CARD or reg['run_id']!=RUN or reg['scope_counts']!=COUNTS
            or reg['collection_switches']!=['OFF','ON'] or reg['repetitions']!=['first']
            or reg['state_steps']!=[12,30,35,36] or reg['target_steps']!=[12,30]
            or reg['strictly_past_anchor_steps']!=[[6,7],[19,25]]
            or reg['dense_steps']!=list(range(1,8))+[13,19,25,31,36]
            or reg['selector']!='UNIFORM_SHARED_D6_COLLECTION'
            or reg['measurement_space']!='POST_RF_DENOISE_FP32_BCTHW'
            or reg['methods']!=['ORIGINAL','BETA1','W1','DENSE']
            or reg['shared_alpha_grid']!=[0,.5,1] or reg['alpha_lambda']!=0
            or reg['alpha_aggregation']!='SCENE_EQUAL_MEAN' or reg['alpha_tie_break']!='SMALLER_ALPHA'
            or reg['teacher_updates_deployment_anchor'] or reg['new_policy_or_clean_latency_claim']
            or [r['name'] for r in reg['requests']]!=NAMES
            or c['execution_run_id']!=RUN or c['historical_wc_settings']!=WC
            or c['expected_real_components']!=1216 or c['expected_real_shape']!=[1,16,24,54,96]
            or c['logical_copy_cap_bytes']!=6*(1<<30) or c['workspace_reserve_bytes']!=4*(1<<30)
            or c['paired_prefix_reserve_bytes']!=4*(1<<30)
            or c['cumulative_cap_GPUh']!=77.89524658965853 or c['automatic_single_job_GPUh']!=4
            or type(c['GPU_execution_selected']) is not bool
            or not math.isfinite(reg['forecast']['forecast_complete_GPUh'])
            or not 0<reg['forecast']['forecast_complete_GPUh']<=4
            or c['sampling_protocol']['actual_steps']!=36 or c['sampling_protocol']['cfg_calls']!=72
            or c['sampling_protocol']['timesteps']!=reg['timesteps']):
        raise ValueError('Complete guided-W1 four-CAL scope, objective or authority differs')
    for request in reg['requests']:
        if (request['seed']!=0 or request['guidance']!=7 or request['num_steps']!=35
                or request['num_output_frames']!=93 or request['resolution']!='432,768'
                or request['inference_type']!='text2world'):
            raise ValueError('Complete exposed four-CAL settings differ')
    actual=[json.loads(line) for line in (stage/'a-collection-requests.jsonl').read_text().splitlines() if line]
    if actual!=reg['requests'] or sha(stage/c['preregistration_ref'])!=c['preregistration_sha256']:
        raise ValueError('Complete request or frozen registration bytes differ')
    if json.loads((stage/c['preregistration_ref']).read_text())!=reg:
        raise ValueError('Complete frozen registration differs')


def validate(project,stage):
    c=json.loads((stage/'a-collection-config.json').read_text());validate_contract(c,stage)
    for name,digest in c['payload_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Complete guided-W1 collection staged payload changed: '+name)
    for name,digest in c['project_input_sha256'].items():
        if sha(project/name)!=digest:raise ValueError('Original project identity changed: '+name)
    for name,digest in c['runtime_source_sha256'].items():
        if sha(project/'runtime'/name)!=digest:raise ValueError('Actual runtime source changed: '+name)
    rows=[json.loads(line) for line in (project/'configs/cal_w1d8.jsonl').read_text().splitlines() if line]
    for request in c['preregistration']['requests']:
        original=[r for r in rows if r['name']==request['name']]
        if len(original)!=1 or original[0]!=request:
            raise ValueError('Frozen actual four-CAL request differs')
    policy=json.loads((stage/'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json').read_text())
    authority=json.loads((stage/'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json').read_text())
    if (policy['automatic_single_job_gpu_hours']!=4 or policy['usage_reset']
            or not policy['legacy_per_card_seconds_caps_revoked']
            or authority['new_cumulative_cap_gpu_hours']!=77.89524658965853 or not authority['direct_user_authorization']
            or authority['usage_reset'] or authority['authorized_remaining_gpu_hours']!=48
            or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours']!=77.89524658965853):
        raise ValueError('Direct current budget/autonomy authority differs')
    reg=json.loads((stage/c['batch_cpu_registration_ref']).read_text())
    if any(c['payload_sha256'].get(n)!=v for n,v in reg['payload_sha256'].items()):
        raise ValueError('Actual new full batch CPU source changed')
    receipt=json.loads(gzip.decompress((stage/c['batch_cpu_receipt_ref']).read_bytes()))
    audit=json.loads((stage/c['batch_cpu_audit_ref']).read_text())
    result=json.loads(gzip.decompress((stage/c['batch_cpu_result_ref']).read_bytes()))
    if (receipt['exit_code']!=0 or receipt['child_exit_code']!=0
            or receipt['status']!='MF_A_COLLECTION_SAMPLING_ACTUAL_CPU_PASS_NOT_REAL_CAL'
            or receipt['payload_after_sha256']!=reg['payload_sha256']
            or receipt['budget_before_sha256']!=receipt['budget_after_sha256']
            or audit['exit_code']!=0 or not audit['independent_source_complete_results_and_actual_artifact_hashes_verified']
            or result['status']!='GUIDED_W1_FULL_PIPELINE_SAMPLING_ACTUAL_CPU_PASS_NOT_REAL_CAL'
            or result['planned_scope']!=reg['CPU_scope']
            or (result['actual_complete_solver_updates'],result['actual_normal_net_calls'],
                result['actual_parent_guided_reloaded'],result['actual_parent_latents_reloaded'],
                result['actual_post_RF_branch_tensors_reloaded'])!=(864,1728,576,16,128)
            or result['mutation_refusals']!=10 or result['actual_truncation_refusals']!=2
            or result['last_parent_writer_failure_controls']!=1
            or not result['actual_UniPC_source_executed'] or result['CUDA_initialized']
            or result['GPU_submissions'] or result['real_Cosmos_CAL_or_video_or_quality_or_clean_latency_claim']):
        raise ValueError('Complete actual guided-W1 sampling batch CPU proof missing')
    spec=importlib.util.spec_from_file_location('existing_resource_assets',stage/'scripts/run_wc_s0_profile.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.validate(project,stage,project/'runtime')
    return c,stage


def validate_selected(c,project,stage):
    forecast=c['preregistration']['forecast']['forecast_complete_GPUh']
    authority=c.get('single_job_exception_authority')
    if forecast>4:
        if not isinstance(authority,dict) or set(authority)!={'ref','sha256'} or sha(stage/authority['ref'])!=authority['sha256']:
            raise ValueError('Whole guided-W1 collection card >4GPUh needs direct specific approval')
        proof=json.loads((stage/authority['ref']).read_text())
        if (not proof.get('direct_user_authorization') or proof.get('card')!=CARD or proof.get('run_id')!=RUN
                or proof.get('scope_counts')!=COUNTS or proof.get('approved_forecast_GPUh')!=forecast):
            raise ValueError('Direct whole-card exception scope differs')
    elif authority is not None:raise ValueError('Unexpected per-job exception for <=4GPUh')
    if not c['GPU_execution_selected'] or c['gpu_uuid']!='GPU-cebf7119-cf03-23b9-e192-cd196332b704':
        raise ValueError('Fresh selected complete guided-W1 collection target required')
    receipt=project/c['production_cpu_stage']/'receipt.json'
    if sha(receipt)!=c['production_cpu_receipt_sha256']:
        raise ValueError('Actual complete production CPU receipt differs')
    proof=json.loads(receipt.read_text())
    if (proof['exit_code']!=0 or proof['status']!='REAL_GUIDED_W1_COLLECTION_PRODUCTION_CPU_PASS_NOT_GPU'
            or proof['CUDA_initialized'] or proof['GPU_submissions']
            or proof['config_binding_sha256']!=binding(c) or proof['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('Same-source guided-W1 collection production CPU proof missing')
    return proof
