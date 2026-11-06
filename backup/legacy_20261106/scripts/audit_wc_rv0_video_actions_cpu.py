#!/usr/bin/env python3
"""Independent read-only joint frozen-Video/action CPU receipt audit, no Torch."""
import argparse
import hashlib
import json
import math
from pathlib import Path

VIDEO = 'cosmos_predict2/_src/predict2/configs/video2world/defaults/conditioner.py'
VIDEO_SHA = 'd58f515074237843b707d67001751c0e022546061348728e6322faaaa22e837c'
FIELDS = sorted(['_is_broadcasted', 'crossattn_emb', 'data_type', 'padding_mask', 'fps',
                 'use_video_condition', 'gt_frames', 'condition_video_input_mask_B_C_T_H_W'])
CHECKS = ['original_vs_OFF_all72_inputs_outputs_cache_banks_latent_state_RNG_artifact_equal',
          'CFG0_and_CFG1_same_input_current_CD_deep0_vs_full',
          'CC_DD_swapped_CD_full_suffix_and_state_equal', 'native_matching_action_equals_OFF',
          'current_CD_uses_paid_probe_past_own_CFG_true_full_only',
          'cache_full_side_effects_left_to_pinned_body',
          'six_invalid_plans_and_missing_history_refused',
          'changed_eval_mode_refused_and_restored',
          'TECH_BLOCKED_attempts_and_parent_restore_verified',
          'actual_Video2World_class_AST', 'all_real_mutable_condition_fields_restored',
          'Video2World_set_and_edit_for_inference_exercised']


def audit(root, stage, runtime, expected):
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    raw = (stage/'receipt.json').read_bytes(); r = json.loads(raw)
    assert r['status'] == 'RV0_VIDEO_ACTIONS_JOINT_CPU_PASS_NOT_REAL_GPU' and r['exit_code'] == 0
    assert len(expected) == 37 and r['payload_sha256'] == expected
    for name, digest in expected.items(): assert sha(stage/name) == digest, name
    assert len(r['upstream_sha256']) == 7 and r['upstream_sha256'][VIDEO] == VIDEO_SHA
    for name, digest in r['upstream_sha256'].items(): assert sha(runtime/name) == digest, name
    assert sha(root/'.sync/wc-rv0-frozen-restore-cpu-r4/receipt.json') == r['reused_prior_CPU_original_sha256']
    prior = json.loads((root/'.sync/wc-rv0-frozen-restore-cpu-r4/receipt.json').read_text())
    assert prior['exit_code'] == 0 and len(prior['payload_sha256']) == 35
    assert all(expected[name] == digest for name, digest in prior['payload_sha256'].items())
    budget = json.loads((root/'reports/budget.json').read_text())
    assert budget == r['budget_before'] and r['original_GPU_budget_unchanged_during_CPU'] is True
    assert budget['cap_gpu_hours'] == 12 and not any(k.endswith('_inflight') for k in budget)
    assert r['GPU_submissions'] == r['RV_labels'] == 0
    assert math.isfinite(r['CPU_wall_seconds']) and 0 < r['CPU_wall_seconds'] <= 1010
    actual = r['actual_import']
    assert actual['status'] == 'ACTUAL_VIDEO_CONDITION_IMPORT_ORIGIN_FROZEN_RESTORE_PASS_NO_CUDA'
    assert Path(actual['path']).resolve() == (runtime/VIDEO).resolve()
    assert actual['class'] == 'Video2WorldCondition' and actual['frozen_dataclass'] is True
    assert actual['source_sha256'] == VIDEO_SHA and sorted(actual['fields']) == FIELDS
    assert actual['CUDA_initialized'] is False and actual['weights_loaded'] is False
    assert actual['GPU_submissions'] == actual['RV_labels'] == 0
    adapter = actual['CPU_import_only_flash_availability_adapter']
    assert adapter['installed_version'] == '2.6.3+cu128.torch27'
    assert all(adapter[k] is True for k in ['installed_package_present', 'version_at_least_2p1',
               'CUDA_hardware_availability_not_overridden', 'original_helpers_restored'])
    assert all(adapter[k] is False for k in ['original_helper_available', 'GPU_runtime_adapter', 'kernel_executed'])
    device = actual['CPU_import_only_current_device_default_adapter']
    assert device['constructor_default_ordinal'] == 0 and device['original_current_device_restored'] is True
    assert all(device[k] is False for k in ['CUDA_context_created', 'GPU_runtime_adapter', 'model_instantiated'])
    body = r['controls']; assert body['torch_version'] == '2.7.1+cu128' and body['cuda_initialized'] is False
    result = body['controls']
    assert result['status'] == 'PINNED_VIDEO_CONDITION_CD_JOINT_CPU_PASS_NOT_REAL_GPU'
    assert result['complete_suffixes'] == 96 and result['CPU_flow_groups'] == 2
    assert result['scene_names'] == ['common', 'human'] and result['CFG_slots'] == [0, 1]
    assert result['CUDA_initialized'] is False and result['GPU_submissions'] == result['RV_labels'] == 0
    current = result['controls']; groups = current['checks']
    assert current['cuda_initialized'] is False and len(current['upstream_sha256']) == 5
    assert [g['flow'] for g in groups] == [False, True]
    suffixes = failures = 0
    for group in groups:
        assert group['real_frozen_class_AST_sha256'] == actual['class_AST_sha256']
        assert group['whole_class_body_not_V2_or_GR00T'] is True
        assert group['condition_construction_weights_network_decoder_writer_are_Toy'] is True
        assert [(c['sample'], c['native_control']) for c in group['checks']] == [
            ('common', 'full'), ('common', 'cache'), ('human', 'full'), ('human', 'cache')]
        for row in group['checks']:
            assert all(row[k] is True for k in CHECKS)
            assert (row['suffix_controls'], row['suffix_updates'], row['suffix_CFG_calls']) == (12, 14, 28)
            assert row['budget_matched_or_real_GPU_labels'] is False
            assert row['pinned_video_source_sha256'] == VIDEO_SHA
        captures = group['raw_captures']
        assert [(c['sample'], c['threshold']) for c in captures] == [
            ('common', -1.), ('common', 1e6), ('human', -1.), ('human', 1e6)]
        for capture in captures:
            assert capture['flow'] == group['flow']
            assert capture['condition_class_AST_sha256'] == actual['class_AST_sha256']
            assert capture['condition_fields'] == FIELDS
            assert len(capture['condition_before']) == 2
            branches = capture['branches']; assert len(branches) == 12
            by = {b['label']: b for b in branches}; assert len(by) == 12
            for slot in (0, 1):
                for left, right in [('OFF1', 'OFF2'), ('C_first', 'C_second'), ('D_first', 'D_second')]:
                    a, b = by[f'{slot}_{left}'], by[f'{slot}_{right}']
                    assert a['final_latent_sha256'] == b['final_latent_sha256']
                    assert a['final_state_components'] == b['final_state_components']
                    assert a['final_state_sha256'] == b['final_state_sha256']
                native = by[f'{slot}_'+('D_first' if capture['threshold'] < 0 else 'C_first')]
                assert native['final_latent_sha256'] == by[f'{slot}_OFF1']['final_latent_sha256']
                for label in ['OFF1', 'OFF2', 'C_first', 'D_second', 'D_first', 'C_second']:
                    branch = by[f'{slot}_{label}']; report = branch['action_report']
                    assert branch['status'] == 'C_D_SUFFIX_COMPLETE_INTERFACE_ONLY_NOT_RV_LABEL'
                    assert branch['parent_restored'] is True and branch['counterfactual_label'] is False
                    assert branch['condition_after_restore'] == capture['condition_before']
                    assert branch['condition_identity_and_frozen_behavior_preserved'] is True
                    assert (branch['completed_updates'], branch['planned_remaining_updates']) == (22, 14)
                    assert report['plan']['target_call'] == 45+slot and report['plan']['cfg_slot'] == slot
                    events = report['suffix_events']
                    assert len(events) == 28 and [e['call'] for e in events] == list(range(45, 73))
                    assert [e['cfg_slot'] for e in events] == [n % 2 for n in range(28)]
                    action = report['plan']['action']
                    assert action == ('OFF' if label.startswith('OFF') else label[0])
                    assert report['decision_interventions'] == int(action != 'OFF')
                    assert report['remaining_policy'] == 'ORIGINAL_WC_ADAPTIVE'
                    assert report['budget_matched'] is False and report['RV_label'] is False
                    assert events[slot]['paid_probe'] is True and events[slot]['current_deep_truth_used'] is False
                    if action != 'OFF':
                        target = events[slot]
                        assert target['requested'] == target['actual_action'] == action
                        assert 1 <= target['age_solver_steps'] <= 32
                        assert (target['true_full_history'][slot][-1] == 23) == (action == 'D')
            expected_failures = ['missing_history', 'changed_eval'] if capture['threshold'] < 0 else [
                'invalid_age', 'missing_history', 'changed_eval']
            assert [f['label'] for f in capture['failures']] == expected_failures
            for failure in capture['failures']:
                assert failure['status'] == 'TECH_BLOCKED' and failure['parent_restored'] is True
            suffixes += len(branches); failures += len(capture['failures'])
    assert suffixes == 96 and failures == 20
    return {'status': 'VIDEO_CONDITION_CD_JOINT_ORIGINAL_CPU_AUDIT_PASS_NOT_REAL_GPU',
            'server_receipt_sha256': hashlib.sha256(raw).hexdigest(),
            'payload_sha256': expected, 'upstream_sha256': r['upstream_sha256'],
            'actual_import': actual, 'CPU_wall_seconds': r['CPU_wall_seconds'],
            'flow_scene_native_groups': 8, 'complete_suffixes': suffixes,
            'TECH_BLOCKED_controls_preserved': failures, 'CFG_slots': [0, 1],
            'budget': budget, 'GPU_submissions': 0, 'RV_labels': 0,
            'no_Torch_import_in_auditor': True, 'full_RV0_or_budget_matched_labels_accepted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'stage', 'runtime', 'expected']: p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.project, a.stage, a.runtime, json.loads(a.expected.read_text()))))
