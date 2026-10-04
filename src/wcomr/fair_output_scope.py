"""Frozen fourteen-output fair comparison and cumulative-cost admission, no Torch."""
import json
import math

CARD = 'WC-FAIR-CAL-R1-20261004-A'
RUN = 'wc-fair-cal-r1'
SAMPLES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191', 'human_199']
FULL = [v for v in range(2,28) if v not in (6,23,27)]
WC_SHA = {SAMPLES[0]:'fa7f466534e7e7984136dfaa9fb47794dedf0c81444229527b9722142715c379',
          SAMPLES[1]:'4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb'}
POINTS = [dict(name=n,mode=m,requested_steps=s,threshold=t) for n,m,s,t in [
    ('native35','native',35,None),('native23','native',23,None),
    ('wc004','worldcache',35,.04),('wc006','worldcache',35,.06),
    ('wc008','worldcache',35,.08),('stage_every1','stage',35,.06)]]
NATIVE = 'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'


def validate_scope(config):
    fixed = {'card':CARD,'run_id':RUN,'max_gpu_wall_seconds':6300,
        'child_timeout_seconds':6270,'kill_after_seconds':5,
        'sample_names':SAMPLES,'sample_indices':[1,2],'seed':0,
        'dense_fallback_layers':[6,23,27],'policy':{'sim':.1,'cdf':.98},
        'pv_skipping':False,'deployment_sparse':True,
        'planned_total_phases':14,'planned_output_files':14,
        'workpoints':POINTS,'expected_solver_updates':[36,24,36,36,36,36],
        'expected_CFG_calls':[72,48,72,72,72,72],
        'stage_policy':{'sparse_layers':FULL,'every':1,'first_solver_step':23,'last_solver_step':27},
        'native_forward_identity':NATIVE,'native_mode':'OFFICIAL_CLASS_FORWARD_NO_WC_EXECUTION',
        'fresh_prepare_per_phase':True,'state_steps':[13,21,33,35,36],
        'mode_policy':'EXPLICIT_EVAL_SHARED_BY_BASELINE_AND_OBSERVED_BEFORE_REQUEST',
        'scope':'TWO_EXPOSED_CAL_NATIVE_FEWER_STEP_TUNED_WC_STAGE_NOT_CONF',
        'minimum_disk_free_bytes':15000000000,
        'approximate_sources_are_true_dense_anchors':False,
        'reuse_current_or_future_shadow_truth':False,'source_replacement_on_failure':False,
        'uses_future_trace':False,'official_skip_predicate_replaced':False,
        'exact_S_quota':None,'fixed_deep_CFG_count':None,
        'expected_WC_sha256':WC_SHA,
        'pipeline_timing':'CUDA_BOUNDARY_SYNCHRONIZED_COMPLETE_GENERATE',
        'substage_timing':'UNSYNCHRONIZED_HOST_WALL_NOT_ISOLATED_CUDA_LATENCY',
        'metric_reference':'native35','planned_native_relative_pairs':10,
        'quality_evaluation':'AUTOMATIC_VIDEO_FIDELITY_MOTION_TEMPORAL_DIAGNOSTICS_AFTER_ARTIFACT_AUDIT'}
    if any(json.dumps(config.get(k),sort_keys=True) != json.dumps(v,sort_keys=True)
           for k,v in fixed.items()):
        raise ValueError('Frozen fourteen-output fair comparison scope changed')
    if any(k in config for k in ('fixed_mask','mask','dense_calls','per_cfg_eligible_ordinals')):
        raise ValueError('Fair card cannot accept future trace or oracle positions')
    if type(config.get('gpu_execution_selected')) is not bool:
        raise ValueError('Explicit independent execution selection required')


def cost_gate(config):
    validate_scope(config)
    a = config['cost_admission']
    values = [a['planning_envelope_seconds'],a['shutdown_settlement_margin_seconds']]
    if (any(type(v) not in (int,float) or not math.isfinite(v) or v <= 0 for v in values)
            or sum(values)>6300 or a['shutdown_settlement_margin_seconds']<30):
        raise ValueError('Complete fourteen-output cost must fit6300 with30 release margin')


def budget_gate(budget, seconds):
    used = budget['used_gpu_hours']
    if (type(seconds) is not int or seconds != 6300 or budget['cap_gpu_hours'] != 12
            or any(k.endswith('_inflight') for k in budget)
            or type(used) not in (int,float) or not math.isfinite(used) or used < 0
            or not budget.get('budget_authorization_ref') or (12-used)*3600 < seconds+15):
        raise ValueError('Independent6300/current12h/no-inflight/balance gate failed')
