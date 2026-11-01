"""Bounded, deterministic hard proposals from already computed signed values.

For the 36-update pilot, enumerate radius-one/two exchanges directly. This is
the exact small linear proposal problem, not a global endpoint optimizer.
Real hard FIT evaluation must accept or reject every proposed schedule.
"""
from itertools import combinations
import math

from .cara_fast_spec_r1 import policy_from_mask


def propose_exchanges(profile, dense_mask, signed_values):
    """Return at most two distinct improving linear proposals, preserving K.

signed_values[k] estimates loss(D)-loss(C) on the incumbent's own trajectory.
The existing grammar enforces true-anchor, protection and age constraints.
Equal D counts are a mechanism control, not measured time equality.
"""
    policy_from_mask(profile, dense_mask)
    if (profile.horizon != 36 or len(signed_values) != profile.horizon
            or any(type(v) not in (int, float) or not math.isfinite(v)
                   for v in signed_values)):
        raise ValueError('Complete finite signed values for the full36 pilot required')
    removable = sorted(set(dense_mask) - set(profile.protected_dense))
    available = sorted(set(range(1, profile.horizon + 1)) - set(dense_mask))
    proposals = []
    seen = set()
    for radius in (1, 2):
        best = None
        # The radius-two problem includes radius one. A duplicated best plan
        # is emitted once, rather than inventing an additional query.
        for size in range(1, radius + 1):
            for removed in combinations(removable, size):
                for added in combinations(available, size):
                    delta = math.fsum(signed_values[t - 1] for t in added) - math.fsum(
                        signed_values[t - 1] for t in removed)
                    if delta >= 0:
                        continue
                    candidate = tuple(sorted(set(dense_mask) - set(removed) | set(added)))
                    key = (delta, size, candidate)
                    if best is not None and key >= best[0]:
                        continue
                    try:
                        compiled = policy_from_mask(profile, list(candidate))
                    except ValueError:
                        # This boundary enumerates schedules outside the legal
                        # grammar; refusal excludes that candidate only.
                        continue
                    best = (key, removed, added, compiled)
        if best is None or best[0][2] in seen:
            continue
        (delta, _, candidate), removed, added, compiled = best
        seen.add(candidate)
        proposals.append(dict(radius=radius, added_D=list(added), removed_D=list(removed),
                              predicted_loss_change=delta, policy=compiled,
                              endpoint_evaluated=False, measured_time_accepted=False))
    return proposals
