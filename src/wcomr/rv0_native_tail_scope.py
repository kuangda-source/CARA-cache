"""One frozen Human parent and two fixed/native-tail comparisons, no Torch."""
from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256

CARD = 'WC-W3-NATIVE-TAIL-RESPONSE-R1-20261007-A'
RUN = 'wc-w3-native-tail-response-r1'
LABELS = ['OFF1', 'OFF2', 'FIXED46_first', 'TAIL46_first', 'FIXED61_first',
          'TAIL61_first', 'TAIL61_second', 'FIXED61_second', 'TAIL46_second', 'FIXED46_second']
ENCODED = ['OFF1', 'FIXED46_first', 'TAIL46_first', 'FIXED61_first', 'TAIL61_first']
CASES = [{'name': '46', 'CFG_slot': 1, 'swap_calls': [46, 48]},
         {'name': '61', 'CFG_slot': 0, 'swap_calls': [61, 63]}]


def label_case(label, cases=CASES):
    if label.startswith('OFF'):
        return None
    name = label.split('_')[0].removeprefix('FIXED').removeprefix('TAIL')
    return next(c for c in cases if c['name'] == name)


def validate_scope(scope, prereg=None, *, fixture=False):
    if (scope['maximum_age_solver_steps'] != 33 or len(scope['scenes']) != 1
            or scope['order'] != LABELS or scope['encoded'] != ['PARENT']+ENCODED
            or scope['scope_counts'] != [1, 10, 6, 2] or scope['responsive_calls_only'] != [69, 70]):
        raise ValueError('Complete native-tail1/10/6/2 scope differs')
    row = scope['scenes'][0]
    mask = tuple(row['parent_action_mask'])
    if (row['parent_mask_sha256'] != mask_sha256(mask)
            or row['parent_full_counts_per_CFG'] != list(cfg_full_counts(mask))):
        raise ValueError('Native-tail parent mask/count identity differs')
    FixedMaskPlan(mask).validate()
    cases = row['cases']
    if len(cases) != 2 or [c['name'] for c in cases] != ['46', '61']:
        raise ValueError('Both registered tail comparison cases required')
    for case in cases:
        FixedMaskPlan(mask, tuple(case['swap_calls'])).validate()
        if case['CFG_slot'] != (case['swap_calls'][0]-1) % 2:
            raise ValueError('Native-tail CFG slot differs')
    if fixture:
        if scope.get('CPU_TOY_fixture') is not True or not scope['run_id'].startswith('CPU_NATIVE_TAIL:'):
            raise ValueError('Explicit CPU native-tail Toy identity required')
    else:
        if (scope['card'] != CARD or scope['run_id'] != RUN or row['scene'] != 'human_199'
                or cases != CASES or row['parent_full_counts_per_CFG'] != [20, 18]
                or mask[68:70] != ('C', 'C') or row['sample_index'] != 2):
            raise ValueError('Registered real Human/seed0 cases differ')
        if prereg is None or (prereg['card'] != CARD or prereg['run_id'] != RUN
                or prereg['parent_action_mask'] != list(mask) or prereg['cases'] != CASES
                or prereg['scope_counts'] != scope['scope_counts']
                or prereg['order'] != LABELS or prereg['encoded'] != ['PARENT']+ENCODED):
            raise ValueError('Prospective frozen native-tail preregistration required')
    return {'scope_counts': [1, 10, 6, 2], 'current_truth_used': False,
            'responsive_counts_may_change': True, 'CPU_fixture': fixture}
