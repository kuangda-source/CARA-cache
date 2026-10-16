"""Whole-card action-price planning from the accepted full368 diagnostic bill.

The expensive state restoration and research capture are included in observed
diagnostic-minus-parent intervals. Incremental action prices are not used as
the main whole-card cost proxy. This module is standard-library only.
"""
from collections import Counter
import hashlib
import json
import math

MODES=('BASELINE','AUDIT','LEAN')
ROUNDS=[dict(section=r,order=list(order)) for r,order in (
    ('WARMUP',('C','A','P0','D')),('FORMAL_1',('C','A','P0','D')),
    ('FORMAL_2',('D','P0','A','C')),('FORMAL_3',('A','P0','D','C')))]
COUNTS=dict(baseline_parents=4,diagnostic_parents=8,full_paths=12,distinct_states=16,
    measured_state_mode_positions=32,ordinary_pairs=432,trial_pairs=512,
    warmup_trial_pairs=128,formal_trial_pairs=384,total_pairs=944,CFG_calls=1888,
    loads=1,raw_files=32,raw_tensors=320,new_offline_dense_trials=128,online_teachers=0)
GC_ALLOWANCE_SECONDS_PER_PARENT=60.
CARD_SETUP_ALLOWANCE_SECONDS=300.
MARGIN=.20


def positive(x):return type(x) in (int,float) and math.isfinite(x) and x>0


def registered_plan(scope):
    raw={k:v for k,v in scope.items() if k!='fingerprint'}
    if (scope['version']!='N09_ACTION_PRICE16_FULL12_AUDIT_LEAN_SCOPE_R1'
            or hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':'),
                ensure_ascii=False,allow_nan=False).encode()).hexdigest()!=scope['fingerprint']
            or scope['scope_counts']!=COUNTS or scope['actions']!=['C','A','P0','D']
            or scope['action_rounds']!=ROUNDS or scope['actual_GPU_card_selected']
            or scope['new_parameters_fitted_or_deployed']):
        raise ValueError('The complete original12/944 scope, all actions and rounds are required')
    names=[r['name'] for r in scope['requests']]
    expected=[]
    for name in names:
        states=[s for s in scope['states'] if s['scene']==name]
        if (len(states)!=4 or {(s['source'],s['phase']) for s in states}!=
                {(s,p) for s in ('D','P') for p in ('EARLY','LATE')}):
            raise ValueError('Keep every old natural source/phase cell')
        for mode in MODES:
            expected.append(dict(scene=name,mode=mode,complete_updates=36,
                measured_steps=[] if mode=='BASELINE' else sorted(s['chosen']['step'] for s in states)))
    observed=[{k:p[k] for k in ('scene','mode','complete_updates','measured_steps')}
              for p in scope['complete_parent_matrix']]
    if (len(names)!=4 or len(set(names))!=4 or len(scope['states'])!=16
            or observed!=expected or len(expected)!=12
            or sum(len(p['measured_steps']) for p in observed)!=32):
        raise ValueError('Do not shorten or substitute the complete parent/state matrix')
    return expected


def source_costs(value,accepted,*,capture_sha256):
    runner,supervisor,final=value['runner'],value['supervisor'],value['final']
    if (accepted['status']!='SOURCE_PHASE16_COMPLETE64_LABELS_CELL_LOSO_INTERVAL_COST_UNITS_CPU_ANALYZED_NOT_NEW_POLICY'
            or accepted['raw_checked_receipt_sha256']!=capture_sha256
            or accepted['all8_parent_controls_pass'] is not True
            or supervisor['status']!='SOURCE_PHASE16_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
            or supervisor['child_exit_code']!=0 or value['post_exit']['exit_code']!=0
            or final['status']!='SOURCE_PHASE16_ALL8_PARENTS16_POINTS64_LABELS368_PAIRS192_TENSORS_CPU_AUDITED'
            or runner['source_revision']!=supervisor['source_revision']
            or final['source_revision']!=supervisor['source_revision']
            or accepted['source_revision']!=supervisor['source_revision']
            or len(runner['runs'])!=8 or len(final['parents'])!=8 or len(final['points'])!=16
            or final['scope_counts']['pairs']!=368 or final['scope_counts']['offline_pairs']!=80
            or final['scope_counts']['ordinary_pairs']!=288
            or not positive(runner['load_seconds']) or not positive(supervisor['wall_seconds'])
            or not math.isclose(accepted['GPU_cost_hours']*3600,supervisor['wall_seconds'],rel_tol=1e-11)):
        raise ValueError('Original full368, all8 accepted parents and actual complete GPU bill required')
    if any(not p['all36_guided_final_actions_equal_to_new_baseline']
           or not p['old_final_actions_and93RGB_equal'] for p in final['parents']):
        raise ValueError('Historical controls must be accepted before their cost is reused')
    durations={};rows=runner['runs']
    for row in rows:
        key=(row['scene'],row['kind']);seconds=row['ended_unix']-row['started_unix']
        if (key in durations or row['status']!='COMPLETE' or row['solver_steps']!=36
                or row['guided_pairs']!=36 or not positive(seconds)
                or row['actual_pair_computations']!=(36 if row['kind']=='BASELINE' else 56)
                or not row['old_final_equal'] or not row['old_actions_equal']):
            raise ValueError('Use successful full parent intervals, not rejected or truncated paths')
        durations[key]=seconds
    scenes=sorted({r['scene'] for r in rows});paired=[]
    if len(scenes)!=4 or set(durations)!={(s,k) for s in scenes for k in ('BASELINE','DIAGNOSTIC')}:
        raise ValueError('All four paired source scenes required')
    for scene in scenes:
        base,diagnostic=(durations[(scene,k)] for k in ('BASELINE','DIAGNOSTIC'))
        extra=diagnostic-base
        if not positive(extra):raise ValueError('The historical extra20 pairs have no positive cost interval')
        paired.append(dict(scene=scene,baseline_seconds=base,diagnostic_seconds=diagnostic,
            additional_pairs=20,extra_diagnostic_seconds=extra,
            inclusive_extra_per_pair_planning_seconds=extra/20))
    residual=supervisor['wall_seconds']-runner['load_seconds']-sum(durations.values())
    if residual < -1.:raise ValueError('Original load and complete request intervals exceed the whole bill')
    return dict(source_revision=supervisor['source_revision'],capture_sha256=capture_sha256,
        old_complete_scope=final['scope_counts'],actual_old_GPUh=supervisor['wall_seconds']/3600,
        old_whole_bill_seconds=supervisor['wall_seconds'],load_seconds=runner['load_seconds'],
        source_scenes=scenes,paired_parent_observations=paired,
        maximum_baseline_seconds=max(p['baseline_seconds'] for p in paired),
        maximum_inclusive_extra_pair_seconds=max(p['inclusive_extra_per_pair_planning_seconds'] for p in paired),
        original_unattributed_seconds=residual,unattributed_per_old_path_seconds=max(0.,residual)/8,
        interval_contains_snapshots_restores_observers_artifacts_and_trial_probes=True,
        diagnostic_difference_is_not_a_pure_action_price=True)


def estimate(scope,source,*,frozen_historical_D_incremental_seconds):
    plan=registered_plan(scope);dense=frozen_historical_D_incremental_seconds
    if not positive(dense) or set(source['source_scenes'])!={r['scene'] for r in plan}:
        raise ValueError('Bound historical dense quote and the same original four scenes required')
    parent_seconds=len(plan)*source['maximum_baseline_seconds']
    # Old cal16 ran C, two A arms, P and D equally. The new four arms have
    # 1/2 versus2/5 expensive refreshes; explicitly allow that extra 1/10 D.
    mixture_allowance_per_trial=(2/4-2/5)*dense
    trial_seconds=COUNTS['trial_pairs']*(source['maximum_inclusive_extra_pair_seconds']+mixture_allowance_per_trial)
    parts=dict(one_resident_load_seconds=source['load_seconds'],complete12_parent_seconds=parent_seconds,
        complete512_extra_trial_seconds=trial_seconds,
        whole_bill_unattributed_seconds=len(plan)*source['unattributed_per_old_path_seconds'],
        request_boundary_GC_headroom_seconds=len(plan)*GC_ALLOWANCE_SECONDS_PER_PARENT,
        additional_card_setup_headroom_seconds=CARD_SETUP_ALLOWANCE_SECONDS)
    subtotal=sum(parts.values());quote=math.ceil(subtotal*(1+MARGIN))/3600
    return dict(status='N09_ACTION_PRICE_FULL12_944_HISTORICAL_WHOLE_COST_PREVIEW_NOT_ADMITTED',
        scope_counts=COUNTS,scope_fingerprint=scope['fingerprint'],complete_parent_positions=len(plan),
        planned_positions=[dict(p,planning_baseline_seconds=source['maximum_baseline_seconds'],
            additional_trial_pairs=len(p['measured_steps'])*16) for p in plan],
        original_source=source,old_extra_pairs_per_diagnostic_parent=20,
        maximum_observed_extra_pair_planning_seconds=source['maximum_inclusive_extra_pair_seconds'],
        old_expensive_refresh_fraction=2/5,new_expensive_refresh_fraction=2/4,
        historical_D_incremental_seconds_for_mixture_planning=dense,
        action_mix_headroom_seconds_per_trial=mixture_allowance_per_trial,
        components=parts,subtotal_before_margin_seconds=subtotal,whole_card_margin_fraction=MARGIN,
        forecast_complete_GPUh=quote,billed_limit_GPUh=quote,
        specific_complete_card_approval_required=quote>=12,current_balance_verified=False,
        current_GPU_UUID_verified=False,actual_new_action_prices_measured=False,
        actual_new_GPU_cost_measured=False,new_GPU_card_selected=False,
        current_caps_or_frozen_parameters_changed=False,estimate_is_upper_bound_guarantee=False,
        GPU_submissions=0,ledger_written=False)
