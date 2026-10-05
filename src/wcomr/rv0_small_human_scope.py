"""Explicit Human-only completion draft; cumulative authorization is not new-card authorization."""
import copy

_SCOPE = {'card': 'WC-W3-SMALL-HUMAN-COMPLEMENT-R1-20261005-A', 'run_id': 'wc-w3-small-human-complement-r1', 'sample_names': ['human_199'], 'sample_indices': [2], 'seed': 0, 'scene_role': 'EXPOSED_CAL_DIAGNOSTIC_NOT_CONF', 'requested_steps': 35, 'parent_solver_updates': 36, 'parent_CFG_calls': 72, 'snapshot_step': 22, 'suffix_solver_updates': 14, 'suffix_CFG_calls': 28, 'target_calls': [46], 'selected_CFG_slots': [1], 'action_unit': 'ONE_CFG_BRANCH_CALL', 'maximum_age_solver_steps': 32, 'suffix_labels_per_scene': ['OFF1', 'OFF2', 'C_first', 'D_second', 'D_first', 'C_second'], 'parent_phases': 1, 'complete_suffix_controls': 6, 'new_encoded_outputs': 4, 'existing_matched_Native_references': 1, 'suffix_policy': 'ORIGINAL_WC_ADAPTIVE', 'budget_matched': False, 'formal_RV_training_labels': False, 'full_RV0_acceptance': False, 'native_uninstrumented_GPU_parity': 'NOT_ESTABLISHED_BY_THIS_DIAGNOSTIC', 'current_WC_historical_encoded_bridge_required': True, 'primary_loss': 'LPIPS_V0P1_ALEX_ALL93_FULL432X768_CPU_NATIVE_RELATIVE', 'negative_and_failed_pairs_preserve_denominator': True, 'new_sparse_W1_Head_LoRA_training_human_review': False, 'logical_copy_cap_bytes': 6442450944, 'workspace_reserve_bytes': 4294967296, 'minimum_disk_free_bytes': 15000000000, 'timeout_seconds': 4500, 'child_timeout_seconds': 4470, 'release_allowance_seconds': 30, 'kill_grace_seconds': 5, 'admission_allowance_seconds': 15, 'cumulative_cap_gpu_hours': 24, 'budget_authorization_ref': 'manifests/budget_authorization_20261005_wc_24gpuh.json', 'CPU_scoring_after_GPU_release': True, 'GPU_execution_selected': False, 'GPU_submitted': False, 'GPU_reserved_seconds': 0, 'RV_labels': 0, 'completion_of_original_card': 'WC-W3-SMALL-CD-R1-20261004-A', 'original_failed_card_denominator': [2, 12, 8, 2], 'this_card_science_pairs': 1, 'remaining_original_point_only': True, 'distinct_GPU_card_authorization_required': True, 'prior_card_failure_reclassified_as_success': False}


def proposal():
    return copy.deepcopy(_SCOPE)


def validate_scope(scope):
    expected = proposal()
    if set(scope) != set(expected):
        raise ValueError('Human complement exact scope keys differ')
    for name, value in expected.items():
        if type(scope[name]) is not type(value) or scope[name] != value:
            raise ValueError('Human complement scope differs: '+name)
    return {'status': 'HUMAN_COMPLEMENT_DRAFT_SCOPE_NOT_GPU_AUTHORIZATION',
            'parents': 1, 'suffixes': 6, 'new_outputs': 4, 'science_pairs': 1,
            'original_denominator_retained': [2, 12, 8, 2], 'GPU_selected': False}
