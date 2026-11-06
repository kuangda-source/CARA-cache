#!/usr/bin/env python3
"""Independent hash/trajectory audit of full causal CPU controls; no Torch."""
import argparse
import hashlib
import json
import math
from pathlib import Path

MODES = ['NATIVE_ORIGINAL', 'CACHE_OFF_NATIVE_PATH',
         'WC_ORIGINAL_ROUTER_ABSENT', 'WC_ROUTER_OFF_WITH_SHADOWS']
LABELS = ['OFF1', 'OFF2', 'C_first', 'D_second', 'D_first', 'C_second']
TRACE = ['inputs', 'outputs', 'deep', 'banks', 'solver_outputs']
PIPELINE = ['decode_input', 'decode_output', 'guardrail_input', 'guardrail_output', 'save_input']


def verify_row(row):
    assert len(row['children']) == 12 and len(row['decoded_children']) == 5
    by = {(c['slot'], c['label']): c for c in row['children']}
    assert len(by) == 12
    for slot in (0, 1):
        off = by[slot, 'OFF1']
        for key in TRACE:
            assert off[key] == row[key][22 if key == 'solver_outputs' else 44:]
        assert off['final_latent_sha256'] == row['final_latent_sha256']
        assert off['record']['final_state_components'] == row['final_components']
        for first, second in [('OFF1', 'OFF2'), ('C_first', 'C_second'), ('D_first', 'D_second')]:
            a, b = by[slot, first], by[slot, second]
            for key in TRACE+['final_latent_sha256']:
                assert a[key] == b[key]
            assert a['record']['final_state_components'] == b['record']['final_state_components']
        c, d = by[slot, 'C_first'], by[slot, 'D_first']
        assert c['inputs'][:slot+1] == d['inputs'][:slot+1]
        assert c['deep'][slot] == 0 and d['deep'][slot] == 2
        for label in LABELS:
            child = by[slot, label]
            assert child['status'] == 'COMPLETE_SUFFIX_NOT_RV_LABEL'
            for key in TRACE:
                assert len(child[key]) == (14 if key == 'solver_outputs' else 28)
            record = child['record']; report = record['action_report']
            assert record['parent_restored'] is True and record['counterfactual_label'] is False
            assert (record['completed_updates'], record['planned_remaining_updates']) == (22, 14)
            assert record['final_latent_sha256'] == child['final_latent_sha256']
            assert report['budget_matched'] is report['RV_label'] is False
            assert report['remaining_policy'] == 'ORIGINAL_WC_ADAPTIVE'
            action = 'OFF' if label.startswith('OFF') else label[0]
            assert child['action'] == report['plan']['action'] == action
            assert (report['plan']['target_call'], report['plan']['cfg_slot']) == (45+slot, slot)
            assert report['decision_interventions'] == int(action != 'OFF')
            events = report['suffix_events']
            assert len(events) == 28 and [e['call'] for e in events] == list(range(45, 73))
            assert [e['cfg_slot'] for e in events] == [i % 2 for i in range(28)]
            assert events[slot]['paid_probe'] is True
            assert all(not e['current_deep_truth_used'] for e in events)
            # The official 70-call horizon ends before the final two native
            # calls; those legitimately bypass the shallow probe.
            assert all(e['paid_probe'] for e in events[:26])
            if action != 'OFF':
                target = events[slot]
                assert target['requested'] == target['actual_action'] == action
                assert 1 <= target['age_solver_steps'] <= 32
                assert (target['true_full_history'][slot][-1] == 23) == (action == 'D')
                if action == 'C':
                    assert all(t < 23 for t in target['true_full_history'][slot])
    decoded = {c['label']: c for c in row['decoded_children']}
    assert set(decoded) == {'0_OFF1', '0_C_first', '0_D_first', '1_C_first', '1_D_first'}
    for child in decoded.values():
        assert child['status'] == 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
        assert child['flags_before'] == child['flags_after']
        assert [e['stage'] for e in child['pipeline']] == PIPELINE
        assert child['artifact']['bytes'] > 0 and len(child['artifact']['sha256']) == 64
    assert decoded['0_OFF1']['pipeline'] == row['pipeline']
    assert decoded['0_OFF1']['artifact']['sha256'] == row['artifact']['sha256']


def audit_receipt(root, receipt, *, stage=None, runtime=None):
    result = json.loads(receipt.read_text())
    claimed_sha = result.pop('server_receipt_sha256', None)
    canonical = (json.dumps(result, indent=2)+'\n').encode()
    digest = hashlib.sha256(canonical).hexdigest()
    if claimed_sha is not None:
        assert digest == claimed_sha
    assert result['status'] == 'RV0_CAUSAL_CORE_CPU_PASS_NOT_REAL_GPU' and result['exit_code'] == 0
    assert result['GPU_submissions'] == result['RV_labels'] == 0
    assert math.isfinite(result['CPU_wall_seconds']) and 0 < result['CPU_wall_seconds'] < 1010
    payload = result['payload_sha256']; upstream = result['upstream_sha256']
    assert len(payload) == 40 and len(upstream) == 9
    for name, value in payload.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == value, name
    prior = json.loads((root/'reports/wc_rv0_frozen_restore_cpu_r4_20261004.json').read_text())
    assert result['reused_prior_CPU_original_sha256'] == prior['server_receipt_sha256']
    assert prior['exit_code'] == 0 and len(prior['payload_sha256']) == 35
    assert all(payload[n] == value for n, value in prior['payload_sha256'].items())
    expected = json.loads((root/'configs/wc_rv0_restore_r1.json').read_text())['upstream_source_sha256']
    expected.update({
        'cosmos_predict2/_src/predict2/configs/video2world/defaults/conditioner.py': 'd58f515074237843b707d67001751c0e022546061348728e6322faaaa22e837c',
        'cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py': '2d3ddcf94158c61223bc610f31ede475f7e4e27cc3b604ff3557b73d891e665f',
        'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py': 'a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'})
    assert upstream == expected
    rechecked = stage is not None and runtime is not None
    if rechecked:
        assert hashlib.sha256((stage/'receipt.json').read_bytes()).hexdigest() == digest
        for name, value in payload.items():
            assert hashlib.sha256((stage/name).read_bytes()).hexdigest() == value
        for name, value in upstream.items():
            assert hashlib.sha256((runtime/name).read_bytes()).hexdigest() == value
    actual = result['actual_import']
    assert actual['status'] == 'ACTUAL_VIDEO_CONDITION_IMPORT_ORIGIN_FROZEN_RESTORE_PASS_NO_CUDA'
    assert actual['source_sha256'] == expected['cosmos_predict2/_src/predict2/configs/video2world/defaults/conditioner.py']
    assert actual['CUDA_initialized'] is actual['weights_loaded'] is False
    assert actual['frozen_dataclass'] is True and actual['class'] == 'Video2WorldCondition'
    budget = json.loads((root/'reports/budget.json').read_text())
    historical_budget = result['budget_before']
    assert result['original_GPU_budget_unchanged_during_CPU'] is True
    assert historical_budget['cap_gpu_hours'] == 12
    assert all(budget[k] == historical_budget[k] for k in ['used_gpu_hours', 'gpu_jobs_launched'])
    if budget != historical_budget:
        authorization = json.loads((root/budget['budget_authorization_ref']).read_text())
        assert authorization['source_user_text'] == '允许增加 GPUh'
        assert authorization['user_message_id'] == 'Sentinel_861e63a87d8c819180ec9a8bcfa6dc92'
        assert authorization['cumulative_cap_gpu_hours'] == budget['cap_gpu_hours'] == 13
        assert authorization['previous_cap_gpu_hours'] == 12 and authorization['usage_reset'] is False
    assert not any(k.endswith('_inflight') for k in budget)
    body = result['controls']; assert body['cuda_initialized'] is False
    assert body['torch_version'] == '2.7.1+cu128'
    controls = body['controls']
    assert controls['status'] == 'FULL_CAUSAL_CORE_NATIVE_VIDEO_CD_DECODE_BRIDGE_CPU_PASS_NOT_GPU'
    assert controls['cuda_initialized'] is False and controls['GPU_submissions'] == controls['RV_labels'] == 0
    groups = controls['checks']
    assert [(g['flow'], g['failure']) for g in groups] == [
        (False, None), (True, None), (True, 'child_writer'), (True, 'child_guardrail')]
    parent_count = suffix_count = output_count = 0
    for group in groups:
        assert group['CPU_MOCK_outputs_not_video'] is True
        assert group['frozen_condition_class_AST_sha256'] == actual['class_AST_sha256']
        state = group['receipt']
        assert (state['planned_parent_phases'], state['planned_suffix_controls'], state['planned_encoded_outputs']) == (8, 24, 18)
        assert state['source_derived_tails']['writer_namespace_binding'] == 'CALL_TIME_INFERENCE_MODULE_SAVE_IMG_OR_VIDEO'
        assert state['GPU_RV_labels'] == 0
        assert state['budget_matched'] is state['full_RV0_accepted'] is state['formal_RV_training_labels'] is False
        if group['failure']:
            assert len(state['requests']) == 1
            request = state['requests'][0]; assert request['status'] == 'TECH_BLOCKED'
            assert [r['mode'] for r in request['parents']] == MODES
            row = request['parents'][-1]
            assert row['status'] == row['children'][0]['status'] == row['decoded_children'][0]['status'] == 'TECH_BLOCKED'
            assert row['children'][0]['record']['parent_restored'] is True
            assert row['decoded_children'][0]['flags_before'] == row['decoded_children'][0]['flags_after']
            continue
        assert state['status'] == 'FULL_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'
        assert [r['sample_name'] for r in state['requests']] == ['common', 'human']
        for request in state['requests']:
            assert request['Native_compatibility'] is request['router_OFF_equal'] is True
            assert [r['mode'] for r in request['parents']] == MODES
            for row in request['parents']:
                assert row['status'] == 'FULL_PARENT_AND_PLANNED_CONTROLS_COMPLETE'
                for key in TRACE:
                    assert len(row[key]) == (36 if key == 'solver_outputs' else 72)
                assert row['prepare_calls'] == 1 and row['flags_before'] == row['flags_after']
                assert row['sample_return_sha256'] == row['final_latent_sha256']
                assert [e['stage'] for e in row['pipeline']] == PIPELINE
            native, native_off, wc, wc_off = request['parents']
            assert native['deep'] == native_off['deep'] == [2]*72
            for left, right in [(native, native_off), (wc, wc_off)]:
                for key in TRACE+['final_latent_sha256', 'final_components', 'pipeline', 'RNG_after']:
                    assert left[key] == right[key]
                assert left['artifact']['sha256'] == right['artifact']['sha256']
            verify_row(wc_off)
            parent_count += 4; suffix_count += 12; output_count += 9
    assert (parent_count, suffix_count, output_count) == (16, 48, 36)
    return {'status': 'FULL_CAUSAL_CPU_RETURNED_RECEIPT_AUDIT_PASS_NOT_GPU',
            'server_receipt_sha256': digest, 'payload_sha256': payload, 'upstream_sha256': upstream,
            'CPU_wall_seconds': result['CPU_wall_seconds'], 'successful_flow_groups': 2,
            'completed_mock_parents': parent_count, 'complete_mock_suffixes': suffix_count,
            'mock_encoded_outputs': output_count, 'TECH_BLOCKED_controls': 2,
            'full_denominator_per_group': {'parents': 8, 'suffixes': 24, 'outputs': 18},
            'remote_original_and_stage_files_rechecked': rechecked,
            'local_payload_and_returned_receipt_SHA_verified': True,
            'no_Torch_import_in_auditor': True, 'budget': budget,
            'recorded_CPU_budget_before_later_authorized_change': historical_budget,
            'GPU_submissions': 0, 'RV_labels': 0, 'full_RV0_or_quality_accepted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--stage', type=Path)
    parser.add_argument('--runtime', type=Path)
    args = parser.parse_args()
    if (args.stage is None) != (args.runtime is None):
        parser.error('stage and runtime must be provided together for server original rechecks')
    print(json.dumps(audit_receipt(args.project, args.receipt, stage=args.stage, runtime=args.runtime)))
