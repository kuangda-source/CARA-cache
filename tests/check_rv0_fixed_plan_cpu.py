"""Standard-library contracts for recorded parent masks and invalid swaps."""
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256


def run():
    # A controlled mixed mask, not a claim about any live model's trajectory.
    mask = tuple('D' if n <= 14 or n > 68 or (n-1)//2 % 3 == 0 else 'C'
                 for n in range(1, 73))
    plan = FixedMaskPlan(mask, (45, 49))
    plan.validate()
    actual = plan.action_mask()
    assert [n for n in range(1, 73) if mask[n-1] != actual[n-1]] == [45, 49]
    assert cfg_full_counts(mask) == cfg_full_counts(actual)
    assert actual[:44] == mask[:44] and actual[68:] == mask[68:]
    FixedMaskPlan(mask).validate()
    try:
        plan.swap_calls = ()
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError('Plan lost immutability')
    bad = [replace(plan, parent_mask=list(mask)), replace(plan, parent_mask=mask[:-1]),
           replace(plan, parent_mask=('C',)+mask[1:]), replace(plan, parent_mask=mask[:-1]+('C',)),
           replace(plan, parent_mask=mask[:20]+('S',)+mask[21:]),
           replace(plan, swap_calls=[45, 49]), replace(plan, swap_calls=(45,)),
           replace(plan, swap_calls=(True, 49)), replace(plan, swap_calls=(45, 50)),
           replace(plan, swap_calls=(49, 45)), replace(plan, swap_calls=(43, 49)),
           replace(plan, swap_calls=(45, 69)), replace(plan, swap_calls=(47, 51)),
           replace(plan, prefix_calls=42), replace(plan, prefix_calls=True),
           replace(plan, maximum_age_solver_steps=0), replace(plan, maximum_age_solver_steps=34),
           replace(plan, maximum_age_solver_steps=True)]
    for candidate in bad:
        try:
            candidate.validate()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid mask/swap accepted: '+repr(candidate))
    source = Path(__file__).resolve().parents[1]/'reports/wc_w3_small_window_cpu_preparation_20261004.json'
    rows = json.loads(source.read_text())['selected_parent_mask_swaps']
    for row in rows:
        real = FixedMaskPlan(tuple(row['parent_mask']),
                             (row['from_cache_call_n'], row['donor_full_call_m']))
        real.validate()
        assert list(cfg_full_counts(real.action_mask())) == row['parent_full_CFG_counts']
    return {'status': 'FIXED_PLAN_STDLIB_CPU_PASS', 'invalid_plans_refused': len(bad),
            'real_parent_static_masks_checked': len(rows),
            'parent_mask_sha256': mask_sha256(mask), 'per_CFG_full_counts': list(cfg_full_counts(mask)),
            'GPU_submissions': 0, 'real_state_feasibility_or_method_results': False}


if __name__ == '__main__':
    print(json.dumps(run()))
