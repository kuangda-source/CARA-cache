"""Frozen historical masks and budget-boundary controls; no endpoint selection."""
from .interval_grammar import Edge, compile_policy

DEPLOYMENT_LIMIT_SECONDS = 257.7712338712067
HISTORICAL_ROLES = ('S26_C', 'S26_A_PHASE', 'SHARED26_C', 'S25_C',
                    'S25_A_PHASE', 'S24_C', 'S24_A_PHASE')


def historical_policies(profile):
    result = {}
    for role in HISTORICAL_ROLES:
        if role == 'SHARED26_C':
            dense = list(range(1, 23)) + [24, 27, 30, 36]
        else:
            count = int(role[1:3])
            dense = list(range(1, count-4)) + [24, 27, 30, 33, 36]
        edges = []
        for s, r in zip(dense, dense[1:]+[37]):
            correction = role.endswith('A_PHASE') and r > s+1
            alpha = (.5 if s+1 >= 25 else 1.) if correction else 0.
            # These fixed intervals never straddle the original phase boundary.
            assert not correction or (r-1 < 25 or s+1 >= 25)
            edges.append(Edge(s, r, (s+1, r-1) if correction else (), alpha))
        result[role] = compile_policy(profile, edges)
    return result


def runtime_budget(native_seconds):
    if native_seconds <= 0:
        raise ValueError('Positive independently measured Native clock required')
    return min(DEPLOYMENT_LIMIT_SECONDS, .8*native_seconds)
