#!/usr/bin/env python3
"""Describe the complete accepted P0 card, without new generation or scoring.

Use the source-bound FP64 moments and all3 group timings for all8 origins.
This does not pick a production policy, tune a threshold or claim video quality.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics


PROOF='reports/wc_p0_real_group_r2_terminal_20261010_capture_and_independent_audit.json'
OUTPUT='reports/wc_p0_real_group_r1_complete_mechanism_and_cost_analysis_20261010.json'
NAMES=['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199',
       'misc_13398218_3840_2160_60fps','av_51b45829-502e-4143-9c32-c026bd6ab191']
MODES=['DENSE_REFERENCE','DENSE_WITH_P0','ROTATION_050','RANDOM_050','ROTATION_075','RANDOM_075']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def raw_object(proof,key):
    item=proof['files'][key];raw=gzip.decompress(Path(item['local_path']).read_bytes())
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def full_strength_mse(moment):
    values=[moment['base_guided_MSE'],moment['guided_error_update_mean_dot'],moment['guided_update_mean_square']]
    assert all(type(v) in (int,float) and math.isfinite(v) for v in values)
    assert values[0]>=0 and values[2]>=0
    raw=math.fsum([values[0],2*values[1],values[2]])
    tolerance=1e-12*max(1,abs(values[0]),abs(values[1]),abs(values[2]))
    assert raw>=-tolerance
    return max(raw,0),raw


def main():
    protocol_ref='manifests/wc_p0_complete_descriptive_analysis_20261010.json'
    protocol=json.loads(Path(protocol_ref).read_text())
    assert protocol['analysis_source_sha256']==sha(__file__)
    assert protocol['source_card']=='WC-MF-P0-REAL-GROUP-R1-20261010-A'
    assert protocol['complete_scope']=={'scenes':4,'same_state_origins':8,'modes':6,'rows':48,'repeat_group_timing_values':144}
    proof=json.loads(Path(PROOF).read_text())
    assert proof['run_id']=='wc-mf-p0-real-group-r1' and proof['source_revision']=='25dc7157394b3451be785cb4f549b9225d72aabb'
    assert proof['GPU_exit_code']==proof['CPU_exit_code']==0 and proof['independent_checks']['success']
    assert proof['independent_checks']['complete_8_parent_8_origin_6_mode_reconstruction']
    audit,table,runner,gpu=(raw_object(proof,k) for k in ('CPU_result','calibration_table','runner','supervisor'))
    assert table['all_modes_direct_guided_moments']==audit['all_modes_direct_guided_moments']
    assert table['all_group_cost_seconds']==audit['all_group_cost_seconds']
    assert table['actual_same_state_teacher_and_post_RF_bundles_verified'] and not table['teacher_updates_deployment_anchor']
    assert not table['new_policy_or_quality_or_clean_latency_claim']
    origins=[(n,'step'+str(t)) for n in NAMES for t in (12,30)]
    moments=table['all_modes_direct_guided_moments'];costs=table['all_group_cost_seconds']
    assert list(moments)==MODES and [(c['scene'],'step'+str(c['step'])) for c in costs]==origins
    for mode in MODES:
        assert [(m['scene'],m['state']) for m in moments[mode]]==origins
    rows=[]
    for i,((scene,state),cost) in enumerate(zip(origins,costs)):
        times=cost['costs'];assert set(times)==set(MODES)
        assert all(len(v)==3 and all(type(t) in (int,float) and math.isfinite(t) and t>0 for t in v) for v in times.values())
        dense_mean=math.fsum(times['DENSE_REFERENCE'])/3
        base=moments['DENSE_REFERENCE'][i]['base_guided_MSE']
        for mode in MODES:
            moment=moments[mode][i];assert moment['base_guided_MSE']==base
            mse,unclipped=full_strength_mse(moment);mean_seconds=math.fsum(times[mode])/3
            expected_rows=31104 if mode.startswith('DENSE') else 15488 if mode.endswith('050') else 23296
            actual=cost['warmup_real_Linear_inputs_and_sources'][mode]['Linear_inputs']
            assert len(actual)==16 and all(x['rows']==expected_rows for x in actual)
            assert moment['diagnostics']['actual_CFG_coefficients']==[8,-7]
            assert moment['diagnostics']['velocity_shape']==[1,16,24,54,96]
            assert len(moment['diagnostics']['original_branch_MSE'])==len(moment['diagnostics']['proposed_branch_MSE'])==2
            rows.append({'scene':scene,'step':cost['step'],'mode':mode,
                'base_C_guided_MSE':base,'full_strength_guided_MSE_from_FP64_moments':mse,
                'unclipped_quadratic_guided_MSE':unclipped,'C_minus_mode_guided_MSE':base-mse,
                'relative_C_error_reduction_percent':100*(base-mse)/base if base>0 else None,
                'retained_fraction_of_C_error':mse/base if base>0 else None,
                'original_branch_MSE':moment['diagnostics']['original_branch_MSE'],
                'proposed_branch_MSE':moment['diagnostics']['proposed_branch_MSE'],
                'active_rows_in_each_of_16_Linear_inputs':expected_rows,
                'selected_four_MLP_layers':[4,10,16,22],
                'fraction_of_token_rows_active':expected_rows/31104,
                'all_three_group_seconds':times[mode],
                'mean_group_seconds':mean_seconds,'median_group_seconds':statistics.median(times[mode]),
                'range_group_seconds':[min(times[mode]),max(times[mode])],
                'mean_dense_reference_group_seconds':dense_mean,
                'dense_minus_mode_mean_group_seconds':dense_mean-mean_seconds,
                'group_seconds_saved_percent':100*(dense_mean-mean_seconds)/dense_mean,
                'dense_over_mode_group_time_ratio':dense_mean/mean_seconds,
                'improves_C_error_and_dense_group_time_descriptively':mse<base and mean_seconds<dense_mean,
                'clean_end_to_end_latency_or_policy_or_video_claim':False})
    aggregates=[]
    for mode in MODES:
        own=[r for r in rows if r['mode']==mode]
        assert len(own)==8
        mse=math.fsum(r['full_strength_guided_MSE_from_FP64_moments'] for r in own)/8
        base=math.fsum(r['base_C_guided_MSE'] for r in own)/8
        aggregates.append({'mode':mode,'scenes':4,'same_state_origins':8,
            'scene_equal_mean_guided_MSE':mse,'scene_equal_mean_C_guided_MSE':base,
            'relative_reduction_of_scene_equal_C_MSE_percent':100*(base-mse)/base if base>0 else None,
            'median_state_relative_C_error_reduction_percent':statistics.median(r['relative_C_error_reduction_percent'] for r in own) if all(r['base_C_guided_MSE']>0 for r in own) else None,
            'states_improving_C_MSE':sum(r['C_minus_mode_guided_MSE']>0 for r in own),
            'states_worsening_C_MSE':sum(r['C_minus_mode_guided_MSE']<0 for r in own),
            'median_state_group_seconds_saved_percent':statistics.median(r['group_seconds_saved_percent'] for r in own),
            'states_faster_than_dense_group':sum(r['dense_minus_mode_mean_group_seconds']>0 for r in own),
            'states_slower_than_dense_group':sum(r['dense_minus_mode_mean_group_seconds']<0 for r in own),
            'states_with_both_descriptive_benefits':sum(r['improves_C_error_and_dense_group_time_descriptively'] for r in own),
            'mean_group_seconds':math.fsum(r['mean_group_seconds'] for r in own)/8,
            'all_24_group_timing_values_retained':True,'no_inference_as_24_independent_states':True})
    contrasts=[]
    for fraction in ('050','075'):
        values=[]
        for scene,state in origins:
            matches=[r for r in rows if (r['scene'],'step'+str(r['step']))==(scene,state)]
            rotate=next(r for r in matches if r['mode']=='ROTATION_'+fraction)
            random=next(r for r in matches if r['mode']=='RANDOM_'+fraction)
            values.append({'scene':scene,'step':rotate['step'],
                'random_minus_rotation_guided_MSE':random['full_strength_guided_MSE_from_FP64_moments']-rotate['full_strength_guided_MSE_from_FP64_moments'],
                'random_minus_rotation_mean_group_seconds':random['mean_group_seconds']-rotate['mean_group_seconds'],
                'same_actual_active_rows':rotate['active_rows_in_each_of_16_Linear_inputs']==random['active_rows_in_each_of_16_Linear_inputs']})
        contrasts.append({'nominal_active_fraction':fraction,'per_origin':values,
            'scene_equal_mean_random_minus_rotation_guided_MSE':math.fsum(v['random_minus_rotation_guided_MSE'] for v in values)/8,
            'origins_with_lower_rotation_error':sum(v['random_minus_rotation_guided_MSE']>0 for v in values),
            'origins_with_higher_rotation_error':sum(v['random_minus_rotation_guided_MSE']<0 for v in values)})
    phases=[]
    for step in (12,30):
        for mode in MODES:
            own=[r for r in rows if r['mode']==mode and r['step']==step];assert len(own)==4
            base=math.fsum(r['base_C_guided_MSE'] for r in own)/4
            mse=math.fsum(r['full_strength_guided_MSE_from_FP64_moments'] for r in own)/4
            phases.append({'step':step,'mode':mode,'same_state_origins':4,
                'scene_equal_mean_C_guided_MSE':base,'scene_equal_mean_guided_MSE':mse,
                'relative_reduction_of_scene_equal_C_MSE_percent':100*(base-mse)/base if base>0 else None,
                'states_improving_C_MSE':sum(r['C_minus_mode_guided_MSE']>0 for r in own),
                'median_state_group_seconds_saved_percent':statistics.median(r['group_seconds_saved_percent'] for r in own),
                'states_faster_than_dense_group':sum(r['dense_minus_mode_mean_group_seconds']>0 for r in own),
                'does_not_choose_new_alpha_or_phase_boundary':True})
    assert all(r['full_strength_guided_MSE_from_FP64_moments']==0 for r in rows if r['mode'].startswith('DENSE'))
    result={'status':'COMPLETE_P0_REAL_GROUP_DESCRIPTIVE_MECHANISM_AND_COST_NOT_POLICY_OR_VIDEO_RESULT',
        'source_proof_ref':PROOF,'source_proof_sha256':sha(PROOF),
        'source_revision':proof['source_revision'],'source_table_native_ref':proof['files']['calibration_table']['local_path'],
        'source_table_sha256':proof['files']['calibration_table']['sha256'],
        'analysis_source_sha256':sha(__file__),'complete_rows':48,'actual_same_state_origins':8,
        'descriptive_protocol_ref':protocol_ref,'descriptive_protocol_sha256':sha(protocol_ref),
        'actual_group_timing_values':144,'per_origin_mode':rows,'scene_equal_aggregates':aggregates,
        'same_actual_row_count_rotation_vs_random':contrasts,
        'both_registered_phases_all_modes':phases,
        'instrumented_parent_pipeline_costs':audit['instrumented_parent_pipeline_costs'],
        'actual_GPU_paid_wall_seconds':gpu['wall_seconds'],'actual_GPU_paid_hours':gpu['wall_seconds']/3600,
        'budget_settled':proof['budget_settled'],'new_GPU_submissions':0,'new_metric_execution':False,
        'moments_formula':'E(alpha=1)=E_C+2*<e_C,delta>+||delta||^2; source-bound post-RF FP32 vectors, FP64 reductions',
        'aggregation':'four scenes equal weight, two registered origins equal weight within each; three repeat timings describe each state',
        'same_state_full_D_truth_not_independent_native_trajectory':True,
        'partial_outputs_are_not_zero_error_D_anchors':True,
        'local_error_not_endpoint_video_fidelity':True,'instrumented_group_time_not_clean_end_to_end_speed':True,
        'no_module_or_direction_rejected_by_single_threshold':True,
        'does_not_train_or_select_policy_or_new_alpha':True,'development_exposure_not_confirmation':True}
    target=Path(OUTPUT);assert not target.exists()
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'scope':[48,8,144],
        'scene_equal_aggregates':aggregates,'GPU_paid_hours':result['actual_GPU_paid_hours']},indent=2))


if __name__=='__main__':main()
