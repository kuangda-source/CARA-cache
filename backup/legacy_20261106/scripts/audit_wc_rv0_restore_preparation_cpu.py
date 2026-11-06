#!/usr/bin/env python3
"""Read-only original-receipt audit of frozen-condition CPU preparation."""
import argparse
import hashlib
import json
import math
from pathlib import Path

UPSTREAM={
 'cosmos_predict2/inference.py':'0db96c49f0b3f18a971bc989e0727132dafc27ef621145a2d25a3da62a7a1975',
 'cosmos_predict2/_src/predict2/inference/video2world.py':'59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95',
 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py':'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903',
 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py':'c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87',
 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py':'f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3',
 'cosmos_predict2/_src/predict2/conditioner.py':'47554e88f2a5d5157e30b18b1d7ad4a4ee55a99dfbaf7071f680c7acf438843a'}


def audit(root, stage, runtime, expected, profile_stage):
    raw=(stage/'receipt.json').read_bytes();r=json.loads(raw)
    assert r['status']=='RV0_FROZEN_RESTORE_CPU_CONTROLS_PASS_NOT_REAL_GPU' and r['exit_code']==0
    assert r['payload_sha256']==expected and len(expected)==35
    for name,digest in expected.items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest,name
    for name,digest in UPSTREAM.items():assert hashlib.sha256((runtime/name).read_bytes()).hexdigest()==digest,name
    budget=json.loads((root/'reports/budget.json').read_text())
    assert r['original_GPU_budget_unchanged_during_CPU'] is True and budget==r['budget_before']
    assert budget['cap_gpu_hours']==12 and budget['gpu_jobs_launched']==44
    assert not any(k.endswith('_inflight') for k in budget)
    assert r['GPU_submissions']==r['RV_labels']==0
    assert math.isfinite(r['CPU_wall_seconds']) and 0<r['CPU_wall_seconds']<=600
    body=r['controls'];assert body['torch_version']=='2.7.1+cu128' and body['cuda_initialized'] is False
    result=body['controls'];actions=result['actions'];restoration=result['restore']
    assert actions['CUDA_initialized'] is False and actions['GPU_submissions']==actions['RV_labels']==0
    regression=actions['unchanged_suffix_regression']
    for key in ['parent36_CFG72_matches_unobserved_full_pipeline',
                'four_suffixes22_to36_CFG28_match_every_input_output_deep_and_final_latent',
                'all_suffix_final_state_components_equal','AB_BA_order_invariant_parent_restored',
                'missing_identity_changed_code_half_CFG_condition_drift_nonfinite_child_duplicate_refused',
                'live_parent_latent_and_shortened_grid_drift_refused']:
        assert len(regression['checks'])==4 and all(row[key] is True for row in regression['checks'])
    five={k:v for k,v in UPSTREAM.items() if not k.endswith('/conditioner.py')}
    assert regression['upstream_sha256']==five
    current=actions['current'];assert current['cuda_initialized'] is False and current['upstream_sha256']==five
    assert [(row['flow'],row['native_control']) for row in current['checks']]==[(False,'full'),(False,'cache'),(True,'full'),(True,'cache')]
    for row in current['checks']:
        for key in ['original_vs_OFF_all72_inputs_outputs_cache_banks_latent_state_RNG_artifact_equal',
                    'CFG0_and_CFG1_same_input_current_CD_deep0_vs_full','CC_DD_swapped_CD_full_suffix_and_state_equal',
                    'native_matching_action_equals_OFF','current_CD_uses_paid_probe_past_own_CFG_true_full_only',
                    'cache_full_side_effects_left_to_pinned_body','six_invalid_plans_and_missing_history_refused',
                    'changed_eval_mode_refused_and_restored','TECH_BLOCKED_attempts_and_parent_restore_verified']:
            assert row[key] is True,key
        assert (row['suffix_controls'],row['suffix_updates'],row['suffix_CFG_calls'])==(12,14,28)
        assert row['budget_matched_or_real_GPU_labels'] is False
    assert restoration['status']=='PINNED_FROZEN_CONDITION_AND_RESTORE_CORE_CPU_PASS_NOT_REAL_GPU'
    assert restoration['CUDA_initialized'] is False and restoration['GPU_submissions']==restoration['RV_labels']==0
    controls=restoration['controls'];assert controls['cuda_initialized'] is False and controls['upstream_sha256']==five
    assert [row['flow'] for row in controls['checks']]==[False,True]
    for group in controls['checks']:
        for key in ['pinned_frozen_condition_assignment_refused','condition_identity_values_and_frozen_behavior_restored',
                    'two_parents_four_unchanged_suffixes_and_ordinary_continuations_equal',
                    'ordinary_mock_output_bridges_equal','copy_cap_and_live_headroom_refused_before_allocation']:
            assert group[key] is True,key
        assert group['conditioner_source_sha256']==UPSTREAM['cosmos_predict2/_src/predict2/conditioner.py']
        assert group['real_model_or_GPU_restore_acceptance'] is False
        assert [row['sample_name'] for row in group['requests']]==['common','human']
        for row in group['requests']:
            assert row['status']=='RESTORE_CONTROLS_AND_ORDINARY_PARENT_CONTINUATION_PASS'
            assert row['prepare_calls']==1 and len(row['inputs'])==len(row['outputs'])==len(row['deep'])==72
            assert len(row['solver_outputs'])==36 and [c['label'] for c in row['controls']]==['A','B']
            assert row['sample_return_sha256']==row['final_latent_sha256']
            assert row['all_suffix_inputs_outputs_solver_deep_latent_state_equal'] is True
            assert row['historical_official_video_bridge_equal'] is True
            assert row['artifact']['bytes']>0 and len(row['artifact']['sha256'])==64
            assert row['capture_inventory']['clone_or_transfer_performed'] is False
            assert row['flags_before']==row['flags_after']
            assert row['decode_policy']=='SCOPED_CUDNN_BENCHMARK_FALSE_DETERMINISTIC_TRUE'
            assert all(v['frozen_dataclass'] for v in row['condition_classes'].values())
            for key in ['memory_before_parent','memory_before_snapshot','memory_after_snapshot','memory_after_parent']:
                assert row[key]=={'status':'CUDA_NOT_INITIALIZED','GPU_measurement':False}
            for child in row['controls']:
                for key in ['inputs','outputs','deep']:assert child[key]==row[key][44:]
                assert child['solver_outputs']==row['solver_outputs'][22:]
                assert child['final_latent_sha256']==row['final_latent_sha256']
                record=child['record'];assert record['parent_restored'] is True
                assert record['final_state_components']==row['final_components']
                assert record['current_action_intervention'] is False and record['counterfactual_label'] is False
                assert child['memory_after_suffix_and_restore']=={'status':'CUDA_NOT_INITIALIZED','GPU_measurement':False}
    profile_raw=(profile_stage/'receipt.json').read_bytes();pr=json.loads(profile_raw)
    assert pr['exit_code']==0 and pr['original_GPU_budget_unchanged'] is True and pr['budget_before']==budget
    for name,digest in pr['payload_sha256'].items():
        assert hashlib.sha256((profile_stage/name).read_bytes()).hexdigest()==digest,name
    p=pr['profile'];assert p['CUDA_initialized'] is False and p['GPU_submissions']==p['RV_labels']==0
    assert p['status']=='CPU_RECORDED_SHAPE_HASH_COST_MEASURED_NOT_GPU_BOUND'
    assert p['complete_GPU_cost_or_peak_bound_validated'] is False
    assert p['D2H_H2D_or_GPU_snapshot_timing_measured'] is False
    assert [row['bytes_per_tensor'] for row in p['rows']]==[127401984,254803968]
    for row in p['rows']:
        for name,values in row['timing_seconds'].items():
            assert len(values)==3 and all(math.isfinite(v) and v>0 for v in values)
            assert row['max_seconds'][name]==max(values)
    return {'status':'FROZEN_CONDITION_RESTORE_AND_HOST_COST_ORIGINAL_CPU_AUDIT_PASS_NOT_REAL_GPU',
            'server_receipt_sha256':hashlib.sha256(raw).hexdigest(),
            'host_profile_server_receipt_sha256':hashlib.sha256(profile_raw).hexdigest(),
            'current_payload_sha256':expected,'upstream_sha256':UPSTREAM,'budget':budget,
            'CPU_wall_seconds':r['CPU_wall_seconds'],'restore_flow_groups':2,
            'restore_parent_phases_per_flow':2,'restore_complete_suffixes_per_flow':4,
            'action_regression_groups':4,'action_complete_suffixes':48,
            'unchanged_suffix_regression_groups':4,'GPU_submissions':0,'RV_labels':0,
            'real_model_restore_or_quality_acceptance':False,
            'complete_GPU_cost_or_peak_bound_validated':False,'no_Torch_import_in_auditor':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','runtime','expected','profile-stage']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.project,a.stage,a.runtime,json.loads(a.expected.read_text()),a.profile_stage)))
