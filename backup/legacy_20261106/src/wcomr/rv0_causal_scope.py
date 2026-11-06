"""Full RV0 C/D causal-control proposal and cumulative budget gate, no Torch.

This proposal does not select/submit a GPU job or generate scientific labels.
The first action diagnostic retains the original adaptive suffix; subsequent
budget-matched targets, calibration and independent confirmation remain gates.
"""
import math

SCENES = ['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191', 'human_199']
LABELS = ['OFF1', 'OFF2', 'C_first', 'D_second', 'D_first', 'C_second']


def proposal():
    return {
        'status': 'FULL_RV0_CAUSAL_CONTROL_PROPOSAL_NOT_SELECTED',
        'sample_names': SCENES.copy(), 'sample_indices': [1, 2], 'scene_role': 'EXPOSED_CAL_TECHNICAL_ONLY',
        'seed': 0, 'requested_steps': 35, 'parent_solver_updates': 36, 'parent_CFG_calls': 72,
        'WC_horizon': 70, 'probe_depth': 2, 'WC_threshold': .06,
        'snapshot_step': 22, 'CFG_slots': [0, 1], 'target_calls': [45, 46],
        'action_unit': 'ONE_CFG_BRANCH_FULL_CALL', 'maximum_age_solver_steps': 32,
        'suffix_labels_per_CFG': LABELS.copy(), 'suffix_solver_updates': 14, 'suffix_CFG_calls': 28,
        'parent_modes_per_scene': ['NATIVE_ORIGINAL', 'CACHE_OFF_NATIVE_PATH',
                                  'WC_ORIGINAL_ROUTER_ABSENT', 'WC_ROUTER_OFF_WITH_SHADOWS'],
        'parent_phases': 8, 'suffix_controls': 24, 'parent_output_files': 8,
        'decoded_unique_C_D_outputs': 8, 'decoded_OFF_bridge_outputs': 2, 'total_encoded_outputs': 18,
        'unchanged_OFF_suffix_outputs_compared_to_parent': 8,
        'repeated_C_D_suffixes_compared_before_duplicate_decode': 8,
        'suffix_policy': 'ORIGINAL_WC_ADAPTIVE',
        'same_policy_function_not_same_future_mask': True, 'budget_matched': False,
        'reference': 'MATCHED_NATIVE_ORIGINAL_SAME_INPUT_NOISE_FULL_GRID_AND_DECODE',
        'causal_control_loss': 'EVERY_INPUT_OUTPUT_DEEP_SOLVER_STATE_LATENT_AND_NATIVE_VIDEO_COMPATIBILITY',
        'signed_fidelity_diagnostic': 'RGB_MSE_C_MINUS_RGB_MSE_D_RELATIVE_TO_MATCHED_NATIVE',
        'signed_fidelity_diagnostic_is_primary_RV_training_label': False,
        'formal_RV_primary_loss': 'LPIPS_V0P1_ALEX_ALL93_FULL432X768_CPU_NATIVE_RELATIVE',
        'formal_RV_training_labels_ready': False,
        'negative_diagnostic_benefit_retained': True, 'failed_pairs_preserve_denominator': True,
        'new_sparse_kernel_or_W1_approximator': False, 'Head_or_LoRA': False,
        'training_or_paid_scoring_or_human_review': False,
        'logical_copy_cap_bytes': 6*(1<<30), 'transient_copy_factor': 2,
        'workspace_reserve_bytes': 4*(1<<30),
        'proposed_timeout_seconds': 6900, 'proposed_child_timeout_seconds': 6870,
        'cumulative_cap_gpu_hours': 13,
        'budget_authorization_ref': 'manifests/budget_authorization_20261004_wc_13gpuh.json',
        'kill_grace_seconds': 5, 'release_allowance_seconds': 30, 'admission_allowance_seconds': 15,
        'complete_cost_bound_validated': False, 'GPU_execution_selected': False,
        'GPU_submitted': False, 'reserved_seconds': 0, 'RV_labels': 0,
        'full_RV0_already_accepted': False,
    }


def validate_scope(scope):
    for name, value in proposal().items():
        if scope.get(name) != value or type(scope.get(name)) is not type(value):
            raise ValueError('Full causal proposal differs: '+name)
    return {'scene_count': 2, 'CFG_slots': [0, 1], 'parent_phases': 8,
            'complete_suffixes': 24, 'encoded_outputs': 18, 'GPU_selected': False}


def price(scope, *, loading, native_pipeline, wc_pipeline, diagnostic_parent_without_children,
          unchanged_suffix_inclusive, unique_decode_allowance=30., bookkeeping_allowance=75.):
    validate_scope(scope)
    values = [loading, native_pipeline, wc_pipeline, diagnostic_parent_without_children,
              unchanged_suffix_inclusive, unique_decode_allowance, bookkeeping_allowance]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('Finite positive complete scope cost components required')
    parts = {
        'loading': loading,
        'four_Native_original_and_cache_off_parents': 4*native_pipeline,
        'two_uninstrumented_WC_parents': 2*wc_pipeline,
        'two_router_OFF_parents_including_snapshot_without_children': 2*diagnostic_parent_without_children,
        'twenty_four_suffixes_using_unchanged_inclusive_cost_proxy': 24*unchanged_suffix_inclusive,
        'eight_unique_C_D_decode_guardrail_encode_allowances_not_measured': 8*unique_decode_allowance,
        'two_OFF_decode_bridge_allowances_not_measured': 2*unique_decode_allowance,
        'additional_bookkeeping_allowance_not_measured': bookkeeping_allowance,
    }
    subtotal = sum(parts.values())
    estimate = subtotal*1.2+scope['release_allowance_seconds']
    if estimate > scope['proposed_timeout_seconds']:
        raise ValueError('Complete planned scope estimate exceeds proposed spend cap')
    return {'components_seconds': parts, 'proxy_subtotal_seconds': subtotal,
            'planning_buffer_factor': 1.2, 'conditional_estimated_seconds': estimate,
            'proposed_timeout_seconds': scope['proposed_timeout_seconds'],
            'incremental_CD_future_mask_cost_measured': False,
            'unique_CD_decode_encode_cost_measured': False,
            'estimate_is_GPU_upper_bound': False, 'complete_scope_time_guaranteed': False,
            'observed_peak_is_next_CD_memory_upper_bound': False}


def budget_gate(budget, scope):
    validate_scope(scope)
    used = budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours') != scope['cumulative_cap_gpu_hours']
            or budget.get('budget_authorization_ref') != scope['budget_authorization_ref']
            or type(used) not in (int, float)
            or not math.isfinite(used) or not 0 <= used <= scope['cumulative_cap_gpu_hours']
            or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Authorized cumulative13 budget/reference/usage/inflight state differs')
    remaining = (scope['cumulative_cap_gpu_hours']-used)*3600
    required = scope['proposed_timeout_seconds']+scope['admission_allowance_seconds']
    if remaining < required:
        raise ValueError('Complete causal spend cap plus admission allowance exceeds remaining budget')
    return {'remaining_seconds': remaining, 'required_seconds': required,
            'reserved_seconds': 0, 'fits': True, 'GPU_selected': False}
