"""Full W3 input/authority contract, independent of the pending PA528 card."""
import hashlib
import json
import math
from pathlib import Path

from .p_acr_profile528_contract_r1 import H1_FP
STEPS=(10,16,23,25,29,30,32,35)

CARD='WC-W3-LABEL-EXPLDEV8-PARENT18-LOCAL64-FULL864-R1-20261015-A'
RUN='wc-w3-label-expldev8-parent18-local64-full864-r1'
SCOPE='manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json'
INPUTS='manifests/wc_w3_expl_dev8_inputs_r1_20261015.json'
REQUESTS='configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl'
CLOCK='reports/wc_w3_actual_schedule_native_CPU_replay_20261015.json'
CAP=104.97136333301378


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(scope,inputs,requests):
    from .w3_label64_post_r1 import full_matrix
    if (scope['proposed_card']!=CARD or scope['label_steps']!=list(STEPS)
            or scope['candidate_actions']!=['C','A','D']
            or scope['ordinary_parent_policy']!='ORIGINAL_H1_MID_FULL_LEGAL_ACTION_SET_INCLUDING_P0'
            or not scope['one_independent_D_teacher_each_supported_origin']
            or scope['reuse_ordinary_D_as_free_teacher']
            or not scope['all_diagnostic_and_teacher_outputs_noncommitting']
            or not scope['all36_parent_guided_actions_history_final_RGB_equality_required']
            or not scope['feature_history_only_ordinary_parent_pre_action']
            or any(scope[k] for k in ('GPU_authorized','GPU_execution_selected','GPU_submissions','ledger_written',
                'human_review_required','F_B_reopened','PA528_715cae7_stage_modified'))):
        raise ValueError('Original full W3 label policy/scope and stopped GPU authority required')
    counts=scope['scope_counts'];plan=full_matrix(requests)
    required={'formal_requests':8,'warmup_requests_reused':1,'full_paths':18,'ordinary_pairs':648,
        'formal_origins':64,'warmup_origins':8,'all_origins':72,'diagnostic_pairs':216,
        'complete_pairs':864,'CFG_calls':1728,'loads':1,'raw_files':90,'all_raw_tensors':1242,
        'formal_video_positions':16,'warmup_video_positions':2,'frames_per_accepted_video':93,
        'new_Native_reference_paths':0}
    if any(counts.get(k)!=v for k,v in required.items()):raise ValueError('Complete18/64/864/90/1242 scope required')
    if inputs['role']!='EXPL_DEV_ONLY_FOR_W3_LABELS_AND_GROUPED_DEVELOPMENT' or len(inputs['selected_sources'])!=8:
        raise ValueError('Eight EXPL_DEV inputs, not reserved paper tests, required')
    selected=inputs['selected_sources']
    names=[s['name']+'_W3EXPLDEV_seed0' for s in selected]
    if names!=[r['name'] for r in requests] or scope['warmup_request_name']!=names[0]:
        raise ValueError('Frozen identity-based request order/warm input changed')
    for r,s in zip(requests,selected):
        if (r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
                or r['resolution']!='432,768' or r['guidance']!=7
                or hashlib.sha256(r['prompt'].encode()).hexdigest()!=s['prompt_sha256']):
            raise ValueError('Frozen prompt/seed/CFG/35-request36-update geometry changed')
    return plan


def require_new_permission(scope,permission,production,*,source_revision,scope_sha256):
    counts=scope['scope_counts']
    # Under8 autonomy and an old PA approval cannot revoke the later GPU stop.
    if (not isinstance(permission,dict) or permission.get('direct_user_authorization') is not True
            or permission.get('card')!=CARD or permission.get('scope_counts')!=counts
            or permission.get('source_revision')!=source_revision or permission.get('scope_sha256')!=scope_sha256
            or permission.get('cumulative_cap_GPUh')!=CAP
            or permission.get('whole_card_not_split') is not True
            or not isinstance(production,dict)
            or production.get('status')!='W3_LABEL64_FULL18_ACTUAL_PRODUCTION_CPU_ACCEPTED'
            or production.get('source_revision')!=source_revision or production.get('scope_counts')!=counts
            or production.get('full72_collector_CPU_accepted') is not True
            or production.get('full90_post_CPU_controls_accepted') is not True
            or production.get('whole_card_supervisor_CPU_accepted') is not True):
        raise ValueError('Fresh whole W3 permission and actual full collector/production/post CPU still required')
    forecast=production.get('forecast_complete_GPUh')
    if (not isinstance(forecast,(int,float)) or not math.isfinite(forecast) or forecast<=0
            or permission.get('forecast_complete_GPUh')!=forecast
            or forecast>8 and permission.get('explicit_strictly_over8_GPUh_whole_card_approved') is not True):
        raise ValueError('Whole W3 actual forecast and over8 exception remain unapproved')


def local_inputs(stage):
    stage=Path(stage);scope=json.loads((stage/SCOPE).read_text());inputs=json.loads((stage/INPUTS).read_text())
    requests=[json.loads(line) for line in (stage/REQUESTS).read_text().splitlines()]
    if sha(stage/INPUTS)!=scope['inputs_sha256']:
        raise ValueError('Frozen complete W3 input manifest changed')
    for s in inputs['selected_sources']:
        path=stage/s['path']
        if sha(path)!=s['sha256']:raise ValueError('Original selected source prompt JSON changed')
    plan=validate(scope,inputs,requests)
    return scope,inputs,requests,plan
