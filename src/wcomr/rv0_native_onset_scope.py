"""Prospective Human61 joint swap with fixed and three response windows."""
from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256

CARD = 'WC-W3-NATIVE-RESPONSE-ONSET-R1-20261007-A'
RUN = 'wc-w3-native-response-onset-r1'
LABELS = ['OFF1', 'OFF2', 'FIXED61_first', 'LATE69_first', 'RESP65_first', 'RESP67_first',
          'RESP67_second', 'RESP65_second', 'LATE69_second', 'FIXED61_second']
ENCODED = ['OFF1', 'FIXED61_first', 'LATE69_first', 'RESP65_first', 'RESP67_first']
CALLS = {'FIXED61': [], 'LATE69': [69, 70], 'RESP65': list(range(65, 71)), 'RESP67': list(range(67, 71))}
CASE = {'name': '61', 'CFG_slot': 0, 'swap_calls': [61, 63]}


def label_mode(label):
    if label.startswith('OFF'):
        return None
    mode = label.split('_')[0]
    if mode not in CALLS or label not in LABELS:
        raise ValueError('Registered response-onset label differs')
    return mode


def validate_scope(scope, prereg=None, *, fixture=False):
    if (scope['maximum_age_solver_steps'] != 33 or len(scope['scenes']) != 1
            or scope['order'] != LABELS or scope['encoded'] != ['PARENT']+ENCODED
            or scope['scope_counts'] != [1, 10, 6, 2] or scope['responsive_calls'] != CALLS):
        raise ValueError('Complete response-onset1/10/6/2 scope differs')
    row = scope['scenes'][0]; mask = tuple(row['parent_action_mask']); case = row['case']
    if (row['parent_mask_sha256'] != mask_sha256(mask)
            or row['parent_full_counts_per_CFG'] != list(cfg_full_counts(mask))
            or case['name'] != '61' or case['CFG_slot'] != 0
            or len(case['swap_calls']) != 2 or case['swap_calls'][1] >= 65
            or any((n-1) % 2 != 0 for n in case['swap_calls'])):
        raise ValueError('Response-onset parent mask and common own-CFG pair differ')
    FixedMaskPlan(mask).validate()
    fixed = FixedMaskPlan(mask, tuple(case['swap_calls'])); fixed.validate()
    if fixture:
        if scope.get('CPU_TOY_fixture') is not True or not scope['run_id'].startswith('CPU_NATIVE_ONSET:'):
            raise ValueError('Explicit new CPU response-onset Toy identity required')
    else:
        if (scope['card'] != CARD or scope['run_id'] != RUN or row['scene'] != 'human_199'
                or row['sample_index'] != 2 or case != CASE
                or row['parent_full_counts_per_CFG'] != [20, 18]
                or mask[60] != 'C' or mask[62] != 'D' or mask[64:70] != ('C',)*6):
            raise ValueError('Frozen real Human/seed0 response-onset scope differs')
        if (prereg is None or prereg['card'] != CARD or prereg['run_id'] != RUN
                or prereg['parent_action_mask'] != list(mask)
                or prereg['joint_swap_calls'] != case['swap_calls']
                or prereg['fixed61_action_mask'] != list(fixed.action_mask())
                or prereg['scope_counts'] != scope['scope_counts'] or prereg['labels'] != LABELS
                or prereg['encoded_children'] != ENCODED or prereg['responsive_calls'] != CALLS):
            raise ValueError('Prospective complete response-onset preregistration required')
    return {'scope_counts': [1, 10, 6, 2], 'current_truth_used': False,
            'responsive_counts_may_change': True, 'CPU_fixture': fixture}
