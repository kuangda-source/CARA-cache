"""Structural interval-policy compiler; no model execution or GPU permission.

Updates are one based. Moving a dense update and deleting one for interval
correction are deliberately different operations. Compile the final D set
before deriving any A interval, so a newly retained D always terminates it.
The protected boundary and source-age limit below belong to this registered
36-update development protocol, not to every diffusion model.
"""
from dataclasses import dataclass
import hashlib
import json
import math


VERSION = 'CARA_INTERVAL_V6_STRUCTURAL_R1'
FRONT_D = tuple(range(1, 22)) + (24, 27, 30, 33, 36)


@dataclass(frozen=True)
class IntervalPlan:
    actions: tuple
    dense_steps: tuple
    correction_steps: tuple
    source_steps: tuple
    alpha: float
    corrected_intervals: tuple
    fingerprint: str

    def manifest(self):
        return dict(version=VERSION, actions=list(self.actions),
            D_steps=list(self.dense_steps), A_steps=list(self.correction_steps),
            source_before=list(self.source_steps), shared_alpha=self.alpha,
            corrected_intervals=[list(x) for x in self.corrected_intervals],
            counts={a:self.actions.count(a) for a in ('D','A','C')},
            mask_identity_sha256=self.fingerprint,
            structural_only=True, production_CPU_accepted=False,
            GPU_dispatch_ready=False)


def _steps(values, horizon, name):
    values = tuple(values)
    if (any(type(x) is not int or not 1 <= x <= horizon for x in values)
            or len(values) != len(set(values))):
        raise ValueError(f'{name}: distinct one-based integer updates required')
    return set(values)


def compile_interval_plan(*, base_dense=FRONT_D, move_dense=(), drop_dense=(),
        coverage='dropped_intervals', interval_offset=0, explicit_A=None,
        alpha=1., horizon=36, protected=tuple(range(1,8))+(36,), max_source_age=6):
    if (type(horizon) is not int or horizon < 2 or type(max_source_age) is not int
            or max_source_age < 1 or type(interval_offset) is not int
            or interval_offset < 0 or type(alpha) not in (int,float)
            or not math.isfinite(alpha) or not 0 < alpha <= 1):
        raise ValueError('Finite shared alpha and explicit structural limits required')
    dense = _steps(base_dense,horizon,'base_dense')
    protected = _steps(protected,horizon,'protected')
    if not protected <= dense or not {1,horizon} <= protected:
        raise ValueError('Registered first/last and protected D updates required')
    moves = tuple(tuple(x) for x in move_dense)
    if any(len(x)!=2 for x in moves):
        raise ValueError('Each dense move has one old and one new update')
    sources = _steps((x[0] for x in moves),horizon,'move_sources')
    targets = _steps((x[1] for x in moves),horizon,'move_targets')
    drops = _steps(drop_dense,horizon,'drop_dense')
    if (not sources <= dense or sources & protected or targets & dense
            or targets & sources or drops & sources or drops & targets):
        raise ValueError('Dense moves must be unambiguous and preserve protected D')
    dense = (dense-sources)|targets
    if not drops <= dense or drops & protected:
        raise ValueError('Only an unprotected retained dense update can be deleted')
    dense -= drops
    intervals = tuple((k,min(d for d in dense if d>k)) for k in sorted(drops))
    if coverage == 'dropped_intervals':
        if explicit_A is not None:
            raise ValueError('Choose an interval rule or an explicit ablation mask')
        correction = {t for k,end in intervals for t in range(k+interval_offset,end)}-dense
    elif coverage == 'all_reuse':
        if explicit_A is not None or interval_offset:
            raise ValueError('Full interval coverage has no explicit mask or offset')
        correction = set(range(1,horizon+1))-dense
    elif coverage == 'explicit_ablation':
        if explicit_A is None or interval_offset:
            raise ValueError('Explicit ablations require the complete A mask')
        correction = _steps(explicit_A,horizon,'explicit_A')
        if correction & dense:
            raise ValueError('Stale A overlay conflicts with the final D set')
    else:
        raise ValueError('Unknown predeclared coverage rule')
    actions = tuple('D' if t in dense else 'A' if t in correction else 'C'
                    for t in range(1,horizon+1))
    last = None; source_before = []
    for t,action in enumerate(actions,1):
        source_before.append(last)
        if action == 'D':
            last = t
        elif last is None or t-last > max_source_age:
            raise ValueError('Reuse lacks a supported strictly past true-D source')
    identity = dict(version=VERSION,actions=actions,alpha=alpha,
        protected=sorted(protected),max_source_age=max_source_age,
        source_before=source_before)
    fingerprint=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    return IntervalPlan(actions,tuple(sorted(dense)),tuple(sorted(correction)),
                        tuple(source_before),float(alpha),intervals,fingerprint)


def initial_development_candidates():
    """Finite first round: 3 candidates per count family, not a time budget."""
    return {
        'K25_FRONT_FULL':compile_interval_plan(drop_dense=(21,)),
        'K25_FRONT_LATE':compile_interval_plan(drop_dense=(21,),interval_offset=1),
        'K25_MOVE22_DROP21_FULL':compile_interval_plan(move_dense=((33,22),),drop_dense=(21,)),
        'K26_FRONT_FULL':compile_interval_plan(coverage='all_reuse'),
        'K26_MOVE22_FULL':compile_interval_plan(move_dense=((33,22),),coverage='all_reuse'),
        'K26_MOVE22_C':compile_interval_plan(move_dense=((33,22),),coverage='explicit_ablation',explicit_A=()),
        'SINGLE22':compile_interval_plan(drop_dense=(21,),coverage='explicit_ablation',explicit_A=(22,)),
        'SINGLE23':compile_interval_plan(drop_dense=(21,),coverage='explicit_ablation',explicit_A=(23,)),
    }


def select_calibrated_candidate(records, *, scenes, candidates, budget_seconds,
        per_prompt_loss_ceiling, tail_limit, measurement_protocol_sha256):
    """Select one shared candidate from complete CAL endpoints, never TEST.

    The caller must freeze the real time boundary, quality ceilings and tail
    limit first. Counts and engineering forecasts cannot replace observations.
    This utility is unconnected to production inference.
    """
    if (not isinstance(measurement_protocol_sha256,str)
            or len(measurement_protocol_sha256)!=64
            or any(x not in '0123456789abcdef' for x in measurement_protocol_sha256)
            or not scenes or len(set(scenes))!=len(scenes) or not candidates
            or len(set(candidates))!=len(candidates)
            or set(per_prompt_loss_ceiling)!=set(scenes)
            or not math.isfinite(budget_seconds) or budget_seconds<=0
            or not math.isfinite(tail_limit) or tail_limit<0
            or any(not math.isfinite(x) or x<0 for x in per_prompt_loss_ceiling.values())):
        raise ValueError('Freeze complete CAL membership, measured budget and quality guards')
    lookup={}
    for r in records:
        key=(r['candidate'],r['scene'])
        if key in lookup or key[0] not in candidates or key[1] not in scenes:
            raise ValueError('Duplicate/foreign endpoint in the calibration matrix')
        if r.get('measurement_protocol_sha256')!=measurement_protocol_sha256:
            raise ValueError('Legacy/concurrent/diagnostic timing cannot replace this measured protocol')
        lookup[key]=r
    if set(lookup)!={(c,s) for c in candidates for s in scenes}:
        raise ValueError('Keep the complete matrix including rejected or failed endpoints')
    feasible=[]; exclusions={}
    for c in candidates:
        rows=[lookup[(c,s)] for s in scenes]
        if any(r.get('status')!='COMPLETE' for r in rows):
            exclusions[c]='REJECTED_OR_FAILED_ENDPOINT_NOT_IMPUTED';continue
        if any(not math.isfinite(r[k]) or r[k]<0 for r in rows for k in ('LPIPS','measured_seconds')):
            raise ValueError('Finite observed endpoint losses and times required')
        if any(r['measured_seconds']==0 for r in rows):
            raise ValueError('Measured inference time must be positive, never zero-filled')
        avg_time=sum(r['measured_seconds'] for r in rows)/len(rows)
        tail=max(r['LPIPS']-per_prompt_loss_ceiling[s] for r,s in zip(rows,scenes))
        if avg_time>budget_seconds or tail>tail_limit:
            exclusions[c]='OUTSIDE_PREDECLARED_TIME_OR_TAIL_GUARD';continue
        avg_loss=sum(r['LPIPS'] for r in rows)/len(rows)
        feasible.append((avg_loss,avg_time,c))
    feasible.sort()
    return dict(selected=feasible[0][2] if feasible else None,
        order=[dict(candidate=c,mean_LPIPS=l,mean_seconds=t) for l,t,c in feasible],
        excluded=exclusions,scope='CAL_ONLY_SHARED_POLICY_NO_TEST_NO_GLOBAL_OPTIMUM',
        production_CPU_accepted=False,GPU_dispatch_ready=False)
