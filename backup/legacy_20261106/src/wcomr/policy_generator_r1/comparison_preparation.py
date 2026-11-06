"""Pre-endpoint controls for P2; no GPU dispatch and no endpoint feedback.

The existing P1 four-plus-four recipe is unchanged. These are preparation
interfaces for a separately registered, completely priced comparison card.
"""
import hashlib

from .budgeted_planner import solve
from .interval_grammar import Edge
from .search_protocol import front_dense_control, _path_proposal


def refresh_only(profile, graph, costs, *, budget_seconds, quantum_seconds, mode='A'):
    """Optimize refresh boundaries while fixing all internal readouts to C/A1."""
    costs.validate(profile)
    if mode not in ('C','A'):
        raise ValueError('Freeze C or full-interval A1')
    frozen=[]
    for item in graph:
        e=item.edge
        allowed=(not e.window) if mode=='C' else (e.end==e.start+1 or (e.window==(e.start+1,e.end-1) and e.alpha==1))
        if allowed:frozen.append(item)
    return solve(profile,frozen,budget_seconds=budget_seconds,shared_seconds=costs.shared_seconds,
        quantum_seconds=quantum_seconds,paths_per_state=4,maximum_final_paths=32)


def pure_proxy(proposals):
    """One policy frozen from the graph reservoir before endpoint information."""
    rows=proposals['proposals']
    return min(rows,key=lambda r:(r['proxy_loss'],r['predicted_seconds'],r['policy']['fingerprint'])) if rows else None


def simple_search(profile, costs, *, budget_seconds, quantum_seconds, query_limit=8,
                  salt='CARA-P2-SIMPLE-COST-ONLY-Q8-R1'):
    """Two front-dense controls plus hash-ranked prefix/periodic C/A plans.

    Hashing breaks ties deterministically; it is not uniform sampling over all
    legal schedules. No proposal labels or endpoint scores enter this control.
    """
    if type(query_limit) is not int or query_limit<2:
        raise ValueError('Reserve both strong simple controls in the same Q')
    costs.validate(profile);pool={};slots=[]
    for mode in ('C','A'):
        best=front_dense_control(profile,costs,budget_seconds=budget_seconds,mode=mode,quantum_seconds=quantum_seconds)
        slots.append(dict(role='SIMPLE_'+mode,proposal=best))
        for prefix in range(1,profile.horizon+1):
            for period in range(1,profile.max_source_age+2):
                dense=sorted(set(range(1,prefix+1))|set(profile.protected_dense)|set(range(prefix+period,profile.horizon+1,period)))
                boundaries=dense+[profile.horizon+1]
                edges=tuple(Edge(s,r,(s+1,r-1) if mode=='A' and r>s+1 else (),1. if mode=='A' and r>s+1 else 0.) for s,r in zip(boundaries,boundaries[1:]))
                try:row=_path_proposal(profile,edges,costs,budget_seconds,quantum_seconds)
                except ValueError:continue
                if row:pool[row['policy']['fingerprint']]=row
    used={s['proposal']['policy']['fingerprint'] for s in slots if s['proposal']}
    rest=sorted((f for f in pool if f not in used),key=lambda f:(hashlib.sha256((salt+'|'+f).encode()).hexdigest(),f))
    # A duplicate control still occupies its original slot; no free replacement.
    slots += [dict(role='HASH_SIMPLE_'+str(i+1),proposal=pool[f]) for i,f in enumerate(rest[:query_limit-2])]
    return dict(status='P2_PREPARATION_ONLY_NOT_DISPATCH',slots=slots,
        logical_slots_registered=query_limit,unavailable_slots=query_limit-sum(s['proposal'] is not None for s in slots),
        distinct_plans=len({s['proposal']['policy']['fingerprint'] for s in slots if s['proposal']}),
        proxy_or_endpoint_scores_used=False,query_limit=query_limit,
        endpoint_selection_rule='SAME_PROMPT_EQUAL_MEASURED_BUDGET_AND_TAIL_RULE_AS_CARA',
        physical_dedup_does_not_erase_each_method_information_exposure=True)
