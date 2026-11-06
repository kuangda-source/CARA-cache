"""Pure scope/cost/asset identity admission for one six-output diagnostic."""
import hashlib
import json
import math

CARD='WC-SELECTIVE-HUMAN-R1-20261004-A'
RUN='wc-selective-human-r1'
TEACHER_SHA='29ec9b86ca70d7241349f9808057a1e5f47491b0f8b1ba689167f9f8890701ae'
PREVIOUS_SHA='9f1418d55f297f62f5ce8868759de983e0df736185bb939f06b86357eab0f4e5'
D_SHA='4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb'
S_SHA='8113659676684a91ce1e8d070e9893f7d1fa3d2f6e8e58191b1218a1f1ac90e1'
FULL=[v for v in range(2,28) if v not in (6,23,27)]
VARIANTS=[{'name':'full_S','sparse_layers':FULL,'every':1},
          {'name':'small_S','sparse_layers':[2,3,5],'every':1},
          {'name':'cadenced_S','sparse_layers':FULL,'every':2}]


def validate_scope(c):
    fixed={'card':CARD,'run_id':RUN,'max_gpu_wall_seconds':2400,
        'sample_names':['human_199'],'sample_indices':[2],'seed':0,
        'dense_fallback_layers':[6,23,27],'policy':{'sim':.1,'cdf':.98},
        'pv_skipping':False,'deployment_sparse':True,'planned_total_phases':6,'planned_output_files':6,
        'measurement_sequence':['official','candidate','candidate','candidate'],
        'measurement_sequence_policy':'reference_then_candidates','variants':VARIANTS,
        'selection_cadence':'FIRST_ELIGIBLE_THEN_EVERY_K_PER_CFG_RESET_WITH_NATIVE_CYCLE',
        'fresh_prepare_per_phase':True,'state_steps':[13,21,33,35,36],
        'mode_policy':'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope':'OFFLINE_EXPOSED_HUMAN_SIX_OUTPUT_LAYER_AND_CADENCE_ONE_FACTOR_COMPARISON',
        'minimum_disk_free_bytes':15000000000,'teacher_trace_used_offline':True,'online_policy':False,
        'approximate_sources_are_true_dense_anchors':False,'reuse_current_or_future_shadow_truth':False,
        'source_replacement_on_failure':False,'shared_entry_RNG_across_control_and_measurement':True,
        'official_fixed_DD_gate_required':True,'three_dense_artifacts_must_match':True,
        'full_S_legacy_output_gate_before_new_variants':True,'fixed_deep_CFG_calls':38,
        'mask_manifest':'manifests/wc_fixed_exposed_masks_draft_20261004.json',
        'mask_source_receipt_sha256':TEACHER_SHA,'previous_fixed_receipt_sha256':PREVIOUS_SHA,
        'previous_D_sha256':D_SHA,'previous_full_S_sha256':S_SHA,
        'pipeline_timing':'CUDA_BOUNDARY_SYNCHRONIZED_COMPLETE_GENERATE',
        'substage_timing':'UNSYNCHRONIZED_HOST_WALL_NOT_ISOLATED_CUDA_LATENCY',
        'quality_evaluation':'AUTOMATIC_VIDEO_FIDELITY_MOTION_TEMPORAL_DIAGNOSTICS_AFTER_ARTIFACT_AUDIT'}
    if any(json.dumps(c.get(k),sort_keys=True)!=json.dumps(v,sort_keys=True) for k,v in fixed.items()):
        raise ValueError('Frozen selective six-output scope changed')
    if type(c.get('gpu_execution_selected')) is not bool:
        raise ValueError('Explicit independent GPU execution selection required')


def validate_mask(c,stage,project):
    validate_scope(c)
    manifest=json.loads((stage/c['mask_manifest']).read_text())
    raw=(project/'outputs/wc-light-output-r1/diagnostic/receipt.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=TEACHER_SHA or manifest['source_receipt_sha256']!=TEACHER_SHA or manifest['execution_selected']:
        raise ValueError('Original exposed teacher or offline mask identity changed')
    original=json.loads(raw)
    row,=[r for r in manifest['masks'] if r['sample_name']=='human_199']
    q,=[q for q in original['measurements']['requests'] if q['sample_name']=='human_199']
    official=[p for p in q['phases'] if p['kind']=='official']
    context=original['reference_contexts'][original['scope']['sample_names'].index('human_199')]
    calls=row['dense_calls']
    if (len(official)!=2 or official[0]['trace']!=official[1]['trace']
            or len(calls)!=72 or any(type(v) is not bool for v in calls) or sum(calls)!=38
            or calls!=[r['deep_executed'] for r in official[0]['trace']] or not all(calls[:14]+calls[70:])
            or [row['model_id'],row['condition_id']]!=context[1:]
            or row['model_id']!='Cosmos-Predict2.5-2B:'+c['f1_setup_sha256']
            or row['source_receipt_sha256']!=TEACHER_SHA or row['horizon']!=70 or row['warm_calls']!=14
            or row['role']!='OFFLINE_FIXED_EXPOSED_TRACE_DIAGNOSTIC_NOT_DEPLOYMENT_ROUTING'):
        raise ValueError('Actual common mask/model/condition binding changed')
    previous_raw=(project/'outputs/wc-fixed-human-r1/diagnostic/receipt.json').read_bytes()
    if hashlib.sha256(previous_raw).hexdigest()!=PREVIOUS_SHA:
        raise ValueError('Previous four-output receipt changed')
    previous=json.loads(previous_raw)
    if (previous['status']!='FOUR_FIXED_DIAGNOSTIC_OUTPUTS_COMPLETE_REQUIRES_INDEPENDENT_AUDIT'
            or previous['fixed_mask']!=row or previous['reference_context'][1:]!=context[1:]):
        raise ValueError('Previous fixed comparison identity differs')
    for i,p in enumerate(previous['measurement']['phases']):
        digest=D_SHA if i==0 else S_SHA
        artifact,=p['artifacts']
        path=project/'outputs/wc-fixed-human-r1/diagnostic/measurement/human_199'/(str(i).zfill(3)+'_'+p['kind'])/'human_199.mp4'
        if artifact['sha256']!=digest or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Actual previous D or full S artifact changed')
    return row


def cost_gate(c):
    validate_scope(c)
    values=[c['cost_admission']['planning_envelope_seconds'],c['cost_admission']['shutdown_settlement_margin_seconds']]
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in values) or sum(values)>2400:
        raise ValueError('Full six-output cost does not fit independent2400 cap')


def budget_gate(b,seconds):
    used=b['used_gpu_hours']
    if (type(seconds) is not int or seconds!=2400 or b['cap_gpu_hours']!=12
            or any(k.endswith('_inflight') for k in b) or not b.get('budget_authorization_ref')
            or type(used) not in (int,float) or not math.isfinite(used) or used<0 or (12-used)*3600<seconds+15):
        raise ValueError('Current cumulative12h/no-inflight/balance admission failed')
