"""Global k-best single-source coverage schedules; no labels or model runtime."""
from functools import lru_cache
import math

from .cara_fast_spec_r1 import digest, policy_from_mask
from .cara_source_coverage_r1 import DISTANCE_SCALE, coverage_distance, normalized_sigmas


def global_topk(profile, dense_count, sigmas, *, tilt, top_k=3):
    """Rank complete masks by (peak, energy, mask), including higher-peak runners-up.

    Saturated path counts locate the peak of each requested order statistic.
    At each such peak, an additive DP keeps k lowest-energy paths that attain
    that peak exactly. This avoids unsafe lexicographic prefix pruning when a
    common suffix can equalize different prefix peaks.
    """
    scales = normalized_sigmas(profile, sigmas)
    n = profile.horizon
    if (type(dense_count) is not int or not len(profile.protected_dense)<=dense_count<=n
            or profile.min_C_anchors!=2 or type(top_k) is not int or not 1<=top_k<=3
            or type(tilt) not in (int,float) or not math.isfinite(tilt) or abs(tilt)>8):
        raise ValueError('Exact legal D count, two C anchors, finite tilt and top1..3 required')
    protected = set(profile.protected_dense)

    def legal(b,c,count):
        return (not any(b<t<c for t in protected) and c-b-1<=profile.max_source_age
                and (c==b+1 or count>=2))

    @lru_cache(maxsize=None)
    def edge(b,c):
        values=[round(DISTANCE_SCALE*coverage_distance(scales,t,b,b,tilt,'single'))
                for t in range(b+1,c)]
        return max(values,default=0),sum(v*v for v in values)

    levels=sorted({edge(b,c)[0] for b in range(1,n+1) for c in range(b+1,n+2)
                   if legal(b,c,2)})

    @lru_cache(maxsize=None)
    def count_paths(peak):
        layer={1:1}
        for count in range(1,dense_count):
            following={}
            for b,ways in layer.items():
                for c in range(b+1,n+1):
                    if n-c>=dense_count-count-1 and legal(b,c,count) and edge(b,c)[0]<=peak:
                        following[c]=min(top_k,following.get(c,0)+ways)
            layer=following
        return min(top_k,sum(ways for b,ways in layer.items()
            if legal(b,n+1,dense_count) and edge(b,n+1)[0]<=peak))

    available=count_paths(levels[-1])
    if not available:
        raise ValueError('No legal schedule at the exact D quota')
    thresholds=set()
    for order in range(1,available+1):
        lo,hi=0,len(levels)-1
        while lo<hi:
            mid=(lo+hi)//2
            if count_paths(levels[mid])>=order:
                hi=mid
            else:
                lo=mid+1
        thresholds.add(levels[lo])

    complete=[]
    for threshold in sorted(thresholds):
        layer={(1,False):[(0,(1,))]}
        for count in range(1,dense_count):
            following={}
            for (b,hit),prefixes in layer.items():
                for c in range(b+1,n+1):
                    if n-c<dense_count-count-1 or not legal(b,c,count):
                        continue
                    peak,energy=edge(b,c)
                    if peak>threshold:
                        continue
                    options=following.setdefault((c,hit or peak==threshold),[])
                    options.extend((cost+energy,mask+(c,)) for cost,mask in prefixes)
                    options.sort()
                    del options[top_k:]
            layer=following
        for (b,hit),prefixes in layer.items():
            if legal(b,n+1,dense_count):
                peak,energy=edge(b,n+1)
                if peak<=threshold and (hit or peak==threshold):
                    complete.extend((threshold,cost+energy,mask) for cost,mask in prefixes)
    plans=[dict(dense_steps=list(mask),peak_units=peak,squared_units=energy,
        peak=peak/DISTANCE_SCALE,squared_sum=energy/DISTANCE_SCALE**2,
        policy=policy_from_mask(profile,list(mask))) for peak,energy,mask in sorted(complete)[:top_k]]
    return dict(schema='CARA_PHASE_SINGLE_SOURCE_GLOBAL_TOPK_R1',plans=plans,
        exact_D=dense_count,tilt=tilt,mode='single',ranking='GLOBAL_PEAK_THEN_ENERGY_THEN_MASK',
        distance_scale=DISTANCE_SCALE,local_error_labels_used=0,endpoint_evaluated=False)


def seven_candidate_pool(profile,dense_count,sigmas):
    candidates,seen=[],{}
    for tilt,count in ((2.,3),(4.,3),(0.,1)):
        group=global_topk(profile,dense_count,sigmas,tilt=tilt,top_k=count)
        for rank,plan in enumerate(group['plans'],1):
            key=plan['policy']['fingerprint']
            origin=dict(tilt=tilt,rank=rank,peak=plan['peak'],squared_sum=plan['squared_sum'])
            if key in seen:
                seen[key]['origins'].append(origin)
            else:
                row=dict(candidate_id=key,**plan,origins=[origin])
                seen[key]=row;candidates.append(row)
    payload=dict(schema='CARA_SINGLE_SOURCE_DEVELOPMENT_REDESIGN_POOL_R3',exact_D=dense_count,
        profile_sha256=profile.fingerprint,sigmas=list(sigmas),candidates=candidates,
        requested_semantic_slots=7,unique_candidates=len(candidates),mode='single',
        designed_after_original42_development_audit=True,endpoint_evaluated=False,
        global_lexicographic_topk=True,local_error_labels_used=0)
    return dict(payload,pool_sha256=digest(payload))
