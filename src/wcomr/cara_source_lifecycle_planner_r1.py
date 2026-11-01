"""Exact k-best DP for a declared two-source additive proxy, never LPIPS.

A change in D positions recomputes every affected (a,b,c) interval. The local
state is the last two true D sources; latent, solver and C working state are
deliberately compressed away and need complete free-running validation.
"""
from functools import lru_cache
import math

from .cara_fast_spec_r1 import policy_from_mask


def plan(profile, dense_count, risk, weights, *, top_k=3):
    """Return up to three distinct lowest-proxy legal exact-K D/C plans.

risk(t,a,b) is nonnegative same-state shadow-D error predicted for C at t,
with true sources a<b<t. Terminal node N+1 consumes no model computation.
The initial a=0 sentinel can traverse only consecutive D until two sources
exist; it is never passed to the fitted risk model.
"""
    n = profile.horizon
    if (type(dense_count) is not int or not len(profile.protected_dense) <= dense_count <= n
            or type(top_k) is not int or not 1 <= top_k <= 3
            or profile.min_C_anchors != 2 or not callable(risk)):
        raise ValueError('Exact-K, top1..3, two-anchor C-only planner required')
    weights = tuple(weights)
    if (len(weights) != n or any(type(w) not in (int,float) or not math.isfinite(w) or w < 0 for w in weights)
            or not any(w > 0 for w in weights)):
        raise ValueError('Complete frozen nonnegative numerical-scale weights required')
    protected = set(profile.protected_dense)

    def legal(b, c, count):
        return (not any(b < t < c for t in protected)
                and c-b-1 <= profile.max_source_age
                and (c == b+1 or count >= 2))

    @lru_cache(maxsize=None)
    def interval(a, b, c):
        terms = []
        for t in range(b+1, c):
            value = risk(t,a,b)
            if type(value) not in (int,float) or not math.isfinite(value) or value < 0:
                raise ValueError('Finite nonnegative source-conditioned risk required')
            terms.append(weights[t-1]*value)
        return math.fsum(terms)

    # For each exact D count, keep the k best prefixes at each last-two state.
    # All future costs depend only on that state, so retaining k prefixes is
    # sufficient for the global k best paths under this additive proxy.
    layer = {(0,1): [(0., (1,))]}
    for count in range(1, dense_count):
        next_layer = {}
        for (a,b), prefixes in layer.items():
            for c in range(b+1, n+1):
                if not legal(b,c,count) or n-c < dense_count-count-1:
                    continue
                cost = interval(a,b,c)
                candidates = next_layer.setdefault((b,c), [])
                candidates.extend((math.fsum((value,cost)), mask+(c,)) for value,mask in prefixes)
                candidates.sort()
                del candidates[top_k:]
        layer = next_layer
    candidates = []
    for (a,b), prefixes in layer.items():
        if legal(b,n+1,dense_count):
            tail = interval(a,b,n+1)
            candidates.extend((math.fsum((value,tail)), mask) for value,mask in prefixes)
    candidates.sort()
    if not candidates:
        raise ValueError('No legal schedule at the exact registered D budget')
    plans = []
    for value,mask in candidates[:top_k]:
        policy = policy_from_mask(profile, list(mask))
        if policy['counts'] != dict(D=dense_count, A=0, C=n-dense_count):
            raise ValueError('Proxy path does not compile to the original D/C grammar')
        plans.append(dict(dense_steps=list(mask), proxy_cost=value, policy=policy))
    return dict(schema='CARA_SOURCE_LIFECYCLE_PROXY_DP_R1', plans=plans,
        horizon=n, exact_D=dense_count, top_k=top_k, proxy_objective_optimized_exactly=True,
        final_LPIPS_optimized_exactly=False, compressed_state=['previous_D','latest_D'],
        frozen_weights=list(weights), unique_interval_costs=interval.cache_info().currsize,
        endpoint_evaluated=False, GPU_dispatch_ready=False)
