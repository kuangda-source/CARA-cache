"""Independent two-parent C/D diagnostic scope; does not alter full RV0.

The first action is controlled, the future policy remains adaptive. Reused
Native references require a verified current-to-historical WC encoded bridge.
"""
import math

SCENES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191', 'human_199']
LABELS = ['OFF1', 'OFF2', 'C_first', 'D_second', 'D_first', 'C_second']


def proposal():
    return {'card': 'WC-W3-SMALL-CD-R1-20261004-A', 'run_id': 'wc-w3-small-cd-r1',
            'sample_names': SCENES.copy(), 'sample_indices': [1, 2], 'seed': 0,
            'scene_role': 'EXPOSED_CAL_DIAGNOSTIC_NOT_CONF', 'requested_steps': 35,
            'parent_solver_updates': 36, 'parent_CFG_calls': 72, 'snapshot_step': 22,
            'suffix_solver_updates': 14, 'suffix_CFG_calls': 28,
            'target_calls': [45, 46], 'selected_CFG_slots': [0, 1],
            'action_unit': 'ONE_CFG_BRANCH_CALL', 'maximum_age_solver_steps': 32,
            'suffix_labels_per_scene': LABELS.copy(), 'parent_phases': 2,
            'complete_suffix_controls': 12, 'new_encoded_outputs': 8,
            'existing_matched_Native_references': 2,
            'suffix_policy': 'ORIGINAL_WC_ADAPTIVE', 'budget_matched': False,
            'formal_RV_training_labels': False, 'full_RV0_acceptance': False,
            'native_uninstrumented_GPU_parity': 'NOT_ESTABLISHED_BY_THIS_DIAGNOSTIC',
            'current_WC_historical_encoded_bridge_required': True,
            'primary_loss': 'LPIPS_V0P1_ALEX_ALL93_FULL432X768_CPU_NATIVE_RELATIVE',
            'negative_and_failed_pairs_preserve_denominator': True,
            'new_sparse_W1_Head_LoRA_training_human_review': False,
            'logical_copy_cap_bytes': 6*(1 << 30), 'workspace_reserve_bytes': 4*(1 << 30),
            'minimum_disk_free_bytes': 15000000000,
            'timeout_seconds': 3900, 'child_timeout_seconds': 3870,
            'release_allowance_seconds': 30, 'kill_grace_seconds': 5,
            'admission_allowance_seconds': 15, 'cumulative_cap_gpu_hours': 13,
            'budget_authorization_ref': 'manifests/budget_authorization_20261004_wc_13gpuh.json',
            'CPU_scoring_after_GPU_release': True, 'GPU_execution_selected': False,
            'GPU_submitted': False, 'GPU_reserved_seconds': 0, 'RV_labels': 0}


def validate_scope(scope):
    expected = proposal()
    if set(scope) != set(expected):
        raise ValueError('Independent small C/D scope keys differ')
    for name, value in expected.items():
        if type(scope[name]) is not type(value) or scope[name] != value:
            raise ValueError('Independent small C/D scope differs: '+name)
    return {'status': 'SMALL_CD_SCOPE_PASS_NOT_GPU_SELECTION',
            'parents': 2, 'complete_suffixes': 12, 'new_outputs': 8, 'science_pairs': 2}


def budget_gate(budget, scope):
    validate_scope(scope)
    used = budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours') != 13
            or budget.get('budget_authorization_ref') != scope['budget_authorization_ref']
            or type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= 13
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Authorized13 usage/reference/inflight state differs')
    remaining = (13-used)*3600
    required = scope['timeout_seconds']+scope['admission_allowance_seconds']
    if remaining < required:
        raise ValueError('Complete small C/D cap and admission exceed remaining budget')
    return {'fits': True, 'remaining_seconds': remaining, 'required_seconds': required,
            'remaining_if_full_cap_spent': remaining-required, 'GPU_selected': False}
