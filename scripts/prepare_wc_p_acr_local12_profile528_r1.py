"""Freeze actual PA12 inputs and a conservative whole-card forecast locally.

No SSH, weight loading, runtime initialization, GPU selection or budget write.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.p_acr_profile528_contract_r1 import CARD,RUN,H1_FP,COEFF_FP,COUNTS,validate_local_bindings


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cost_ref='manifests/wc_p_acr_local12_profile528_full_cost_r1_20261015.json'
    config_ref='configs/wc_p_acr_local12_profile528_production_r1_20261015.json'
    proof_ref='reports/wc_p_acr_local12_profile528_local_binding_cpu_20261015.json'
    if any((ROOT/n).exists() for n in (cost_ref,config_ref,proof_ref)):
        raise ValueError('Registered proposal exists; use a fresh revision, not an overwrite')
    old_cost_ref='manifests/wc_math_n1_full180_cost_r1_20261012.json'
    capture_ref='reports/wc_source_phase16_live_or_terminal_capture_20261012.json'
    old_cost=json.loads((ROOT/old_cost_ref).read_text());capture=json.loads((ROOT/capture_ref).read_text())
    assert capture['supervisor']['child_exit_code']==0 and capture['post_exit']['exit_code']==0
    full=Path(capture['full_readonly_capture_path'])
    assert sha(full)==capture['full_readonly_capture_sha256']
    original=json.loads(full.read_text());rows=[]
    for b,d in zip(original['runner']['runs'][::2],original['runner']['runs'][1::2]):
        assert b['kind']=='BASELINE' and d['kind']=='DIAGNOSTIC' and b['scene']==d['scene']
        trials=sum(t['full_pair_research_seconds'] for point in d['diagnostic_points'] for t in point['trial_receipts'])
        delta=d['guarded_pipeline_without_write_seconds']-b['guarded_pipeline_without_write_seconds']
        rows.append({'scene':b['scene'],'baseline_pipeline_seconds':b['guarded_pipeline_without_write_seconds'],
            'diagnostic_added_seconds':delta,'actual_all20_trial_seconds':trials,
            'unisolated_4capture20restore_and_IO_seconds':delta-trials,
            'unisolated_per_origin_capture5restore_IO_seconds':(delta-trials)/4})
    assert len(rows)==4
    common={'imports_one_load_seconds':old_cost['components']['imports_and_one_load_seconds'],
        'four_baseline_parent_allowance_seconds':old_cost['components']['natural_parents_measured_seconds'],
        'four_diagnostic_parent_allowance_seconds':old_cost['components']['natural_parents_measured_seconds'],
        '96_C_A_pair_allowance_seconds':96*6.,'48_D_pair_allowance_seconds':48*12.,
        '96_asymmetric_pair_allowance_seconds':96*12.,'96_uncached_constructor_allowance_seconds':96.,
        'all8_parent_raw_IO_and_cleanup_allowance_seconds':320.}
    simple=dict(common,capture12_and240restore_event_allowance_seconds=12*21*30.)
    mixed=max(r['unisolated_per_origin_capture5restore_IO_seconds'] for r in rows)
    transfer=dict(common,measured_unisolated_capture_restore_IO_bundle_transfer_seconds=mixed*(20/5)*12)
    multiplier=1.5
    scenarios=[{'name':'LEGACY_EVENT30_ALLOWANCE','components':simple,'forecast_complete_GPUh':sum(simple.values())*multiplier/3600},
        {'name':'MEASURED_UNISOLATED_COPY_RESTORE_IO_TRANSFER','components':transfer,
         'forecast_complete_GPUh':sum(transfer.values())*multiplier/3600}]
    forecast=max(s['forecast_complete_GPUh'] for s in scenarios)
    cost={'identity':CARD+'_WHOLE_COST_PROPOSAL','full_paths':8,'complete_pairs':528,'CFG_calls':1056,'loads':1,
        'ordinary_pairs':288,'diagnostic_pairs':240,'teacher_D_pairs_including_repeats':48,
        'not_all_allowances_measured':True,'source_refs_sha256':{n:sha(ROOT/n) for n in (old_cost_ref,capture_ref)},
        'full_capture_sha256':sha(full),'historical_source_phase16_actual_GPUh':capture['supervisor']['wall_seconds']/3600,
        'historical_parent_comparisons':rows,'contingency_multiplier':multiplier,'scenarios':scenarios,
        'forecast_rule':'LARGER_COMPLETE_SCENARIO_NO_SCOPE_REDUCTION','forecast_complete_GPUh':forecast,
        'mixed_transfer_boundary':'Old bundle is capture+restores+hash/CPU copies/IO/parent audit differences; not isolated per-restore cost or clean action latency. Scaling20/5 conservatively repeats capture/IO too.',
        'method_latency_or_speedup_measurement':False,'budget_written':False,'GPU_submissions':0}
    (ROOT/cost_ref).write_text(json.dumps(cost,indent=2,allow_nan=False)+'\n')
    references={'requests':'configs/wc_h1_cost_curve_full60_production_r1_20261013.json',
        'selection':'manifests/wc_p_acr_h1_state_selection_e0_20261014.json',
        'H1':'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json',
        'previous':'manifests/wc_math_n2_frozen_parameters_r1_20261012.json',
        'coefficients':'manifests/wc_p_acr_development_source_phase_coefficients_r1_20261015.json',
        'baseline':'manifests/wc_h1_cost_curve_middle403_bindings_r1_20261013.json',
        'setup':'configs/f1_setup.json','profile_CPU':'reports/wc_p_acr_profile20_cpu_r1_independent_acceptance_20261015.json',
        'cost':cost_ref}
    old=json.loads((ROOT/references['requests']).read_text());sel=json.loads((ROOT/references['selection']).read_text())
    table=json.loads((ROOT/references['H1']).read_text())
    c={'status':'ACTUAL_PA12_INPUTS_BOUND_PRODUCTION_ENTRY_CPU_AND_NEW_GPU_PERMISSION_PENDING',
        'card':CARD,'run_id':RUN,'scope_counts':COUNTS,'requests':old['requests'],'states':sel['states'],
        'actions':['C','A','D','Pc','Pu'],'source_update':'ACR_READOUT_NOT_REFRESH',
        'H1_fingerprint':H1_FP,'coefficients_fingerprint':COEFF_FP,'gamma':table['gamma'],
        'strategy':'WORKING_P_AGE_NONZERO_REBASE','expected_real_shape':[1,16,24,54,96],
        'guarded_model':'Cosmos-Predict2.5-2B/post-trained','sample_domain':'EXPOSED_CAL_DEVELOPMENT_NOT_TEST',
        'original_input_stage':'.sync/wc-e3-complete64-selected-r1-20261011',
        'references':{k:{'ref':n,'sha256':sha(ROOT/n)} for k,n in references.items()},
        'checkpoint_reserves':{'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)},
        'whole_scope_not_split':True,'past_history_difference':'PAST_ORDINARY_DD_ONLY','per_action_constructor_cost_charged':True,
        'forecast_complete_GPUh':forecast,'automatic_single_job_GPUh':8,'cumulative_cap_GPUh':104.97136333301378,
        'remaining_GPUh_snapshot':24.974985961,'GPU_authorized':False,'GPU_execution_selected':False,
        'new_card_authorization_ref':None,'budget_reset':False,'training':False,'human_review':False,'F_B_enabled':False,
        'fit_on_current_teacher':False,'ACR_REFRESH':False,'source_rebase':False,'head_elision':False,
        'actual_production_CPU_accepted':False,'server_resources_currently_verified':False,
        'parent_video_rejections':'RETAIN_ALL8_POSITIONS_AND_ALL12_POINT_DENOMINATORS_NEVER_SUBSTITUTE',
        'parent_full36_reference':'SAME_RESIDENT_ORDINARY_H1_PARENT_THEN_DIAGNOSTIC_PARENT',
        'quality_boundary':'LOCAL_SAME_STATE_ABSOLUTE_GUIDED_MSE_ONLY; UNCHANGED_PARENT_LPIPS_NOT_NEW_METHOD_ENDPOINT'}
    values=validate_local_bindings(ROOT,c)
    (ROOT/config_ref).write_text(json.dumps(c,indent=2,allow_nan=False)+'\n')
    result={'status':'ACTUAL_PA12_LOCAL_INPUT_COEFF_SCOPE_AND_WHOLE_COST_BOUND_NOT_PRODUCTION_CPU',
        'config_ref':config_ref,'config_sha256':sha(ROOT/config_ref),'scope_counts':COUNTS,
        'H1_fingerprint':table['fingerprint'],'gamma':table['gamma'],'coefficients_fingerprint':COEFF_FP,
        'forecast_complete_GPUh':forecast,'scenario_GPUh':{s['name']:s['forecast_complete_GPUh'] for s in scenarios},
        'only_local_references_verified':True,'model_forwards':0,'GPU_submissions':0,'budget_written':False,
        'new_GPU_permission_required':True,'production_CPU_still_pending':True}
    (ROOT/proof_ref).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
