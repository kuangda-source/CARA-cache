"""Deterministic single-exchange Shared rule; no endpoint-dependent search.

Generalizes the historical 26D exchange to legal integer quotas 9..36.
D24 is protected so the original alpha phase boundary is never crossed inside
an A interval. Counts are fixed; an age-limited A falls back to C, never D.
"""
import math
from .interval_grammar import Edge, compile_policy

PROTECTED = tuple(range(1, 8)) + (24, 36)
# Reproduces all original S24/25/26 masks, extends deterministically in both directions.
PRIORITY = (27, 30, 33) + tuple(range(8, 24)) + (25, 26, 28, 29, 31, 32, 34, 35)


def base_dense(n_dense):
    if type(n_dense) is not int or not 9 <= n_dense <= 36:
        raise ValueError('Legal quota is an integer in 9..36 (nine protected D)')
    return tuple(sorted(PROTECTED + PRIORITY[:n_dense - len(PROTECTED)]))


def max_age(dense):
    return max(b-a-1 for a,b in zip(dense,dense[1:]+(37,)))


def shared_dense(scores, n_dense):
    if len(scores)!=36 or any(type(v) not in (float,int) or not math.isfinite(v) or v<0 for v in scores):
        raise ValueError('36 finite nonnegative frozen energy scores required')
    base=base_dense(n_dense); age_limit=max(6,max_age(base)); candidates=[]
    for remove in base:
        if remove in PROTECTED: continue
        for add in range(8,36):
            if add in base: continue
            dense=tuple(sorted((set(base)-{remove})|{add}))
            gain=scores[add-1]-scores[remove-1]
            if gain>0 and max_age(dense)<=age_limit:
                candidates.append((gain,remove,add,dense))
    best=sorted(candidates,key=lambda x:(-x[0],x[1],x[2]))
    gain,remove,add,dense=best[0] if best else (0.,None,None,base)
    return dict(dense=list(dense),base_dense=list(base),remove_D=remove,add_D=add,
        score_delta=gain,max_source_age=max_age(dense),allowed_source_age=age_limit,
        rule='ONE_POSITIVE_EXCHANGE_GAIN_DESC_REMOVE_ASC_ADD_ASC',n_dense=n_dense)


def compile_dense(profile,dense,*,correction=False,age_cap=None):
    dense=tuple(dense)
    if tuple(sorted(set(dense)))!=dense or not set(PROTECTED)<=set(dense):
        raise ValueError('Ordered distinct D including phase boundary24 required')
    if age_cap is not None and (type(age_cap) is not int or age_cap<1):
        raise ValueError('Positive integer correction age cap')
    edges=[]
    for s,t in zip(dense,dense[1:]+(37,)):
        end=min(t-1,s+age_cap) if age_cap is not None else t-1
        window=(s+1,end) if correction and end>s else ()
        alpha=(1. if s+1<25 else .5) if window else 0.
        if window and window[0]<25<=window[1]: raise ValueError('A window crosses original phase')
        edges.append(Edge(s,t,window,alpha))
    return compile_policy(profile,edges)


def roles(profile,scores):
    from .historical_bridge import historical_policies
    old=historical_policies(profile)
    result={f'NATIVE{n}':dict(kind='native',requested_steps=n,policy=None) for n in (35,26,28,30)}
    for key in ('S26_C','S26_A_PHASE','SHARED26_C'):
        result[key]=dict(kind='policy',requested_steps=35,policy=old[key])
    for n in (24,25,20):
        dense=base_dense(n); generated=shared_dense(scores,n)['dense']
        # Original S24/25 alpha and placements unchanged. At20 the age cap is explicit.
        for family,mask in (('S',dense),('SHARED',generated)):
            for action in ('C','A_PHASE'):
                age_cap=3 if (family=='SHARED' or n==20) else None
                key=f'{family}{n}_{action}'
                result[key]=dict(kind='policy',requested_steps=35,
                    policy=compile_dense(profile,mask,correction=action=='A_PHASE',age_cap=age_cap),
                    correction_age_cap=age_cap if action=='A_PHASE' else None)
    assert len(result)==19
    for key in ('S24_C','S24_A_PHASE','S25_C','S25_A_PHASE'):
        assert result[key]['policy']==old[key]
    return result
