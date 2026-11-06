"""Explicit two-call early/late interventions, never an online routing policy."""
from .selective_refresh_policy import SparsePlacementPolicy, SparseRefreshPolicy


def validate_timing_factorial(policies, group, eligible_counts):
    if (type(policies) is not tuple or len(policies) != 3
            or type(policies[0]) is not SparseRefreshPolicy
            or policies[0].every != 2
            or any(type(p) is not SparsePlacementPolicy for p in policies[1:])
            or any(p.sparse_layers != group for p in policies)
            or len(eligible_counts) != 2
            or any(type(n) is not int or n < 1 for n in eligible_counts)):
        raise ValueError('Timing factorial needs legacy alternating and two full-group explicit policies')
    quotas = [(n + 1) // 2 for n in eligible_counts]
    if any(q < 2 or q + 1 > n for q, n in zip(quotas, eligible_counts)):
        raise ValueError('Mask cannot support common and both timing factorial arms')
    expected = [quotas, [q - 1 for q in quotas], [q + 1 for q in quotas]]
    common, early, late = [], [], []
    for cfg in (0, 1):
        base = policies[1].per_cfg_eligible_ordinals[cfg]
        both = policies[2].per_cfg_eligible_ordinals[cfg]
        extras = tuple(sorted(set(both) - set(base)))
        if (len(base) != expected[1][cfg] or len(both) != expected[2][cfg]
                or not set(base) < set(both) or 1 in base
                or len(extras) != 2 or extras[0] != 1
                or extras[-1] <= base[-1] or both[-1] > eligible_counts[cfg]):
            raise ValueError('Timing arms must differ only by first and post-common eligible refresh per CFG')
        common.append(list(base)); early.append(1); late.append(extras[-1])
    return expected, {'common_eligible_ordinals_per_CFG': common,
                      'early_eligible_ordinal_per_CFG': early,
                      'late_eligible_ordinal_per_CFG': late,
                      'varying_S_counts_are_not_matched_cost': True}
