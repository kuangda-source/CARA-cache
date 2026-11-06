"""Freeze all four events from audited source histories before intervention."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    ref = 'reports/wc_e4c_existing_trace_clocks_cpu_r1_20261011.json'
    raw = (root / ref).read_bytes()
    report = json.loads(raw)
    assert report['summary']['complete_captured_paths'] == 22
    names = ['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199']
    method = 'A_CPD_W1_ONE_PHASE'
    events = []
    for name in names:
        rows = [r for r in report['per_complete_path_all22']
                if r['sample_name'] == name and r['method'] == method
                and r['strategy'] == 'WORKING_P_AGE_KEEP_INTERVAL'
                and (r['inventory'] == 'ORIGINAL64' if name == names[0]
                     else r['inventory'] == 'E1_FULL8' and r['arm'] == 'CPU_PREFIX')]
        assert len(rows) == 1
        row = rows[0]
        for phase, lo, hi in [('early', 8, 24), ('late', 25, 30)]:
            eligible = [p for p in row['trace']['P_events'] if lo <= p['created_step'] <= hi]
            assert eligible, (name, phase)
            chosen = min(eligible, key=lambda p: p['created_step'])
            step = chosen['created_step']
            events.append({'id': name + '-' + phase, 'sample_name': name,
                'phase': phase, 'birth_step': step, 'fork_after_update': step - 1,
                'last_diagnostic_update': step + 4, 'source_inventory': row['inventory'],
                'source_arm': row.get('arm'), 'source_receipt_sha256': row['source_receipt_sha256'],
                'source_method': method, 'source_strategy': row['strategy'],
                'original_birth_action': row['trace']['steps'][step-1]['action']})
    assert [e['birth_step'] for e in events] == [13, 25, 12, 27]
    scope = {'identity': 'E4C_MATCHED_P_D_AGE124_COMPLETE_SCOPE_PREREGISTERED_NOT_GPU',
        'card': 'WC-E4C-MATCHED-P-D-AGE124-OFFON4-SUFFIX16-R1-20261011-A',
        'run_id': 'wc-e4c-matched-p-d-age124-offon4-suffix16-r1',
        'source_trace_report_ref': ref, 'source_trace_report_sha256': hashlib.sha256(raw).hexdigest(),
        'event_selection': 'EARLIEST_ACTUAL_P_IN_FIXED_EARLY8_24_AND_LATE25_30_EACH_TWO_AVAILABLE_SCENES',
        'selection_uses_quality_speed_or_candidate_error': False,
        'sample_names': names, 'seed': 0, 'method': method,
        'working_epoch_strategy': 'WORKING_P_AGE_KEEP_INTERVAL', 'events': events,
        'parent_collection_modes': ['OFF', 'ON'],
        'suffix_arms': ['POLICY_REPEAT1', 'POLICY_REPEAT2', 'P_BIRTH_C4', 'D_BIRTH_C4'],
        'suffix_updates_each': 5, 'forced_source_births': ['P', 'D'],
        'forced_following_actions': ['C'] * 4, 'teacher_ages': [1, 2, 4],
        'scope_counts': {'full_parent_paths': 4, 'full_parent_updates': 144,
            'events': 4, 'suffix_branches': 16, 'suffix_updates': 80,
            'same_state_C_dense_teacher_points': 24, 'teacher_pairs': 24,
            'total_pair_computations': 248, 'total_normal_and_teacher_CFG_calls': 496},
        'same_state_teacher_input': 'DENSE_ON_EACH_ACTUAL_CANDIDATE_LATENT_NOT_OTHER_ARM_LATENT',
        'teacher_updates_deployment_state': False,
        'P_promotes_true_D_or_zeroes_creation_floor': False,
        'missing_event_behavior': 'RETAIN_REGISTERED_EVENT_AS_MISSING_NO_REPLACEMENT',
        'physical_copy_gate_or_original_protection_bypassed': False,
        'actual_method_required_storage_and_transport_in_cost': True,
        'full_parent_OFF_ON_and_policy_suffix_repeat_controls': True,
        'C4_is_OFFLINE_DIAGNOSTIC_not_online_policy': True,
        'completed_GPU_cards_E2_E3_cancelled_or_narrowed': False,
        'separate_E4_hypothesis_not_substitute_for_pending_E2_E3': True,
        'GPU_queue_reason': 'PREPARE_E4_WITHOUT_REPLACING_PENDING_COMPLETE_E2_E3; SELECT_QUEUE_BEFORE_ANY_GPU',
        'GPU_forecast_status': 'PENDING_IMPLEMENTATION_CPU_AND_BOUND_REAL_COST_CALCULATION',
        'automatic_single_job_GPUh': 8, 'training': False, 'human_review': False,
        'new_end_to_end_quality_or_speed_claim': False, 'GPU_execution_selected': False,
        'GPU_submissions': 0, 'ledger_written': False}
    target = root/'manifests/wc_e4c_matched_source_age_complete_scope_r1_20261011.json'
    assert not target.exists()
    target.write_text(json.dumps(scope, indent=2) + '\n')
    print(json.dumps({'status': scope['identity'], 'events': [e['birth_step'] for e in events],
        'scope_counts': scope['scope_counts'], 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
