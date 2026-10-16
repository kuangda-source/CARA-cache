"""Bind a complete diagnostic scope, with no production configuration or launch."""
import json
from pathlib import Path

from .action_price16_collection_r1 import ACTIONS,COUNTS,ROUNDS
from .frozen_shared_production_r1 import sha,fingerprint,verify_sampling_sources
from .balanced_repeat_production_r1 import read_reference
from .post_probe_action_clock_r1 import BOUNDARY

OLD='configs/wc_source_phase16_full368_production_r1_20261012.json'
CURRENT='configs/wc_paper_N07_frozen_shared_production_r1_20261016.json'


def scope(root):
    root=Path(root);old=json.loads((root/OLD).read_text());current=json.loads((root/CURRENT).read_text())
    names={
        'old_source_phase_contract':OLD,'current_frozen_shared_config':CURRENT,
        'natural_state_selection':old['selection_ref'],'math_parameters':old['parameters_ref'],
        'old_parent_endpoint_bindings':old['baseline_ref'],
        'H1_parameters':'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json',
        'final_five_role_freeze':current['references']['method_freeze']['ref']}
    values={n:json.loads((root/path).read_text()) for n,path in names.items()}
    from .source_phase_absolute_h1_control_r1 import validate_parameters
    validate_parameters(values['H1_parameters'])
    if (old['states']!=values['natural_state_selection']['states']
            or values['natural_state_selection']['parent_method']!='P_OFF'
            or values['math_parameters']['gamma']!=values['H1_parameters']['gamma']
            or values['H1_parameters']['old_math_parameters_fingerprint']!=values['math_parameters']['fingerprint']
            or values['final_five_role_freeze']['repeat_timing_bindings']['CPA_HIGH_FIDELITY']!='TABLE_PHASE_H1'):
        raise ValueError('Reuse the original natural16 and the already frozen source-aware A semantics')
    scenes=[r['name'] for r in old['requests']];states=old['states']
    if len(scenes)!=4 or len(set(scenes))!=4 or len(states)!=16:
        raise ValueError('All four old CAL scenes and16 source/phase states required')
    parents=[];cells={(s,p) for s in ('D','P') for p in ('EARLY','LATE')}
    for request in old['requests']:
        if request['seed']!=0 or request['num_steps']!=35 or request['num_output_frames']!=93:
            raise ValueError('Do not use new test inputs or change the old full36 protocol')
        selected=[s for s in states if s['scene']==request['name']]
        if (len(selected)!=4 or {(s['source'],s['phase']) for s in selected}!=cells
                or len({s['chosen']['step'] for s in selected})!=4
                or any(not s['chosen']['partial_ready'] or s['chosen']['state_before'][5]>=2 for s in selected)):
            raise ValueError('All original legal P0 trials and four cells must survive')
        for mode in ('BASELINE','AUDIT','LEAN'):
            parents.append(dict(id=request['name']+'__'+mode,scene=request['name'],mode=mode,
                parent_method='P_OFF',complete_updates=36,new_output_positions=1,
                measured_steps=[] if mode=='BASELINE' else sorted(s['chosen']['step'] for s in selected),
                readout='BETA1_ONE_PHASE',gamma=values['math_parameters']['gamma']))
    raw=read_reference(root,current['references']['shared_CPU_raw'])
    accepted=read_reference(root,current['references']['shared_CPU_acceptance'])
    reused=verify_sampling_sources(root,raw,accepted)
    sources=['src/wcomr/action_price16_collection_r1.py','src/wcomr/post_probe_action_clock_r1.py',
        'src/wcomr/action_price16_audit_r1.py','src/wcomr/action_price16_plan_r1.py',
        'tests/check_action_price16_sampling_cpu_r1.py','tests/test_post_probe_action_clock_r1.py',
        'scripts/analyze_wc_paper_N09_action16_CPU_r1.py','scripts/prepare_wc_paper_N09_action16_scope_r1.py']
    result=dict(version='N09_ACTION_PRICE16_FULL12_AUDIT_LEAN_SCOPE_R1',scope_counts=COUNTS,
        requests=old['requests'],states=states,complete_parent_matrix=parents,actions=list(ACTIONS),
        action_rounds=[dict(section=r,order=list(order)) for r,order in ROUNDS],
        cost_boundary=BOUNDARY,selection_and_normal_source_commit_included=True,
        all_trial_probes_snapshots_saves_charged_to_whole_card=True,
        no_research_observer_hooks_in_lean=True,algorithm_projection_cache_hooks_retained=True,
        current_H1_execution_A_semantics=True,GCR_A_NO_P_controller_cost_not_inferred_from_this_owner=True,
        primitive_selector_is_calibration_controller_not_final_H1_score=True,
        references={n:dict(ref=path,sha256=sha(root/path)) for n,path in names.items()},
        source_bindings={n:dict(sha256=sha(root/n),bytes=(root/n).stat().st_size) for n in sources},
        unchanged_numerical_source_reuse=reused,
        all36_parent_guided_actions_history_and_all_compatible93_RGB_required=True,
        audit_lean_all_trials_raw_equality_required=True,warmups_not_in_formal_price_statistics=True,
        actual_GPU_card_selected=False,actual_production_CPU_accepted=False,
        forecast_complete_GPUh=None,billed_limit_GPUh=None,new_parameters_fitted_or_deployed=False,
        minimum_calibration_collection_measured=False,new_F_B_P_ACR_T1_or_training=False,
        mainline_order='N07_then_N08_then_N09_N10',GPU_submissions=0,ledger_written=False)
    result['fingerprint']=fingerprint(result)
    return result
