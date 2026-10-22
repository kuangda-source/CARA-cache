"""Offline P1 summaries over registered endpoint rows; never an acceptor.

The existing measured selector owns the decision. Missing/failed positions stay
in the denominator. GPU bills are physical events; information queries are a
separate ledger, including accepted prior endpoints and rejected attempts.
"""
import math

from .budgeted_planner import number
from .search_protocol import choose_observed


def prompt_means(rows, key):
    groups = {}
    for row in rows:
        number(row[key], key, key == 'measured_seconds')
        groups.setdefault(row['prompt'], []).append(row[key])
    return {p: math.fsum(values) / len(values) for p, values in groups.items()}


def spearman(x, y):
    """Average ranks for ties; a constant ranking is explicitly undefined."""
    if len(x) != len(y):
        raise ValueError('Paired candidate ranks required')
    if len(x) < 2:
        return None
    def ranks(values):
        return [1 + sum(a < v for a in values) + (sum(a == v for a in values)-1)/2 for v in values]
    a, b = ranks(x), ranks(y)
    ma, mb = math.fsum(a)/len(a), math.fsum(b)/len(b)
    den = math.sqrt(math.fsum((v-ma)**2 for v in a)*math.fsum((v-mb)**2 for v in b))
    return math.fsum((u-ma)*(v-mb) for u, v in zip(a,b))/den if den else None


def calibration_costs(events, queries, *, query_limit, limit_GPUh):
    number(limit_GPUh, 'complete calibration limit', True)
    if type(query_limit) is not int or query_limit < 1:
        raise ValueError('Frozen logical query limit required')
    ids, totals = set(), {}
    for e in events:
        if not e['event_id'] or e['event_id'] in ids:
            raise ValueError('Each physical cost event is charged once')
        ids.add(e['event_id'])
        if e['kind'] not in ('LOAD_GUARD', 'NATIVE', 'PROPOSAL', 'WARM_BRIDGE', 'FIT', 'SELECT', 'SCORE_POST', 'FAILURE_EXIT'):
            raise ValueError('Explicit complete-card cost category required')
        number(e['actual_GPUh'], 'actual physical GPUh')
        totals.setdefault(e['kind'], []).append(e['actual_GPUh'])
    seen, executions = set(), set()
    for q in queries:
        if not q['fingerprint'] or q['fingerprint'] in seen:
            raise ValueError('Aliases cannot create duplicate logical queries')
        seen.add(q['fingerprint'])
        if q['origin'] not in ('NEW_EVALUATION', 'ACCEPTED_PRIOR_ENDPOINT') or q['status'] not in ('COMPLETE', 'REJECTED', 'TECHNICAL_FAILURE', 'NOT_REACHED'):
            raise ValueError('Keep original query origin and outcome')
        if q['origin'] == 'ACCEPTED_PRIOR_ENDPOINT' and q['physical_execution_ids']:
            raise ValueError('Reused information is not newly executed')
        executions.update(q['physical_execution_ids'])
    attempted = sum(q['status'] != 'NOT_REACHED' for q in queries)
    totals = {k:math.fsum(v) for k,v in totals.items()}
    total = math.fsum(totals.values())
    return dict(actual_GPUh=total, by_component_GPUh=totals,
        registered_queries=len(queries), attempted_information_queries=attempted,
        accepted_prior_queries=sum(q['origin']=='ACCEPTED_PRIOR_ENDPOINT' for q in queries),
        unique_new_endpoint_executions=len(executions),
        query_cap_met=len(queries)<=query_limit, cost_cap_met=total<=limit_GPUh,
        complete_cost_coverage_asserted=False)


def analyze(d):
    """Use one split at a time; CAL_SELECT begins only after finalist freeze."""
    number(d['quantum_seconds'],'cost quantum',True)
    number(d['shared_seconds'],'shared seconds')
    members=tuple(tuple(x) for x in d['members'])
    candidates=d['candidates'];ids=[c['fingerprint'] for c in candidates]
    if not members or len(set(members))!=len(members) or len(set(ids))!=len(ids) or not ids:
        raise ValueError('Freeze distinct members and candidates')
    if d['evidence_kind'] not in ('SYNTHETIC_UNIT_FIXTURE','ACCEPTED_ENDPOINT_EXPORT'):
        raise ValueError('Identify the endpoint export provenance')
    if d['split']=='CAL_SELECT' and d.get('finalists_frozen_before_scores') is not True:
        raise ValueError('No selection results before finalist identity freeze')
    records=d['records']
    # Reuse the original selector to validate every row, split, timing, profile,
    # endpoint coordinate and registered member before reporting statistics.
    ceiling=max([number(r['LPIPS'],'LPIPS') for r in records if r['status']=='COMPLETE']+[0.])+1
    common=dict(members=members,candidate_fingerprints=ids,budget_seconds=d['budget_seconds'],
        timing_protocol=d['timing_protocol'],profile_identity=d['profile_identity'],split=d['split'])
    choose_observed(records,**common,loss_ceiling=ceiling)
    all_rows={f:[r for r in records if r['fingerprint']==f] for f in ids}
    complete={f:rows for f,rows in all_rows.items() if len(rows)==len(members) and all(r['status']=='COMPLETE' for r in rows)}
    controls={role:[c['fingerprint'] for c in candidates if role in c['roles']] for role in ('SIMPLE_C','SIMPLE_A')}
    if any(len(v)!=1 for v in controls.values()):
        raise ValueError('Exactly one identity for each fixed control; aliases may share it')
    available=all(v[0] in complete for v in controls.values())
    tails=None
    if available:
        losses={k:prompt_means(complete[v[0]],'LPIPS') for k,v in controls.items()}
        tails={p:min(losses['SIMPLE_C'][p],losses['SIMPLE_A'][p])+0.01 for p,_ in members}
    decision=choose_observed(records,**common,loss_ceiling=tails) if available else dict(
        status='CONTROL_ENDPOINT_MISSING_SELECTION_UNAVAILABLE',selected=None,order=[])
    feasible={r['fingerprint'] for r in decision['order']};summaries=[]
    for c in candidates:
        if c['phase'] not in ('INITIAL','REFINEMENT'):
            raise ValueError('Original search phase must remain explicit')
        f=c['fingerprint'];rows=all_rows[f]
        value=dict(fingerprint=f,roles=c['roles'],phase=c['phase'],registered_positions=len(members),
            returned_positions=len(rows),complete_positions=sum(r['status']=='COMPLETE' for r in rows),
            missing_members=[list(m) for m in members if not any((r['prompt'],r['seed'])==m for r in rows)],
            feasible=f in feasible,mean_LPIPS=None,measured_mean_seconds=None,
            worst_prompt_LPIPS=None,maximum_tail_excess=None)
        number(c['predicted_seconds'],'predicted seconds',True)
        number(c['proxy_loss'],'proxy loss')
        rounded=d['shared_seconds']+c['discrete_cost_units']*d['quantum_seconds']
        if type(c['discrete_cost_units']) is not int or c['discrete_cost_units']<0 or rounded+1e-9<c['predicted_seconds']:
            raise ValueError('Conservative discrete cost cannot understate its continuous prediction')
        value.update(predicted_seconds=c['predicted_seconds'],proxy_loss=c['proxy_loss'],
            rounded_predicted_seconds=rounded,rounding_overhead_seconds=rounded-c['predicted_seconds'])
        if f in complete:
            loss=prompt_means(rows,'LPIPS');seconds=prompt_means(rows,'measured_seconds')
            value.update(mean_LPIPS=math.fsum(loss.values())/len(loss),
                measured_mean_seconds=math.fsum(seconds.values())/len(seconds),
                worst_prompt_LPIPS=max(loss.values()),
                maximum_tail_excess=max(loss[p]-tails[p] for p in loss) if tails else None)
            value['prediction_residual_seconds']=value['measured_mean_seconds']-c['predicted_seconds']
        summaries.append(value)
    paired=[r for r in summaries if r['mean_LPIPS'] is not None]
    initial=[r for r in decision['order'] if next(c for c in candidates if c['fingerprint']==r['fingerprint'])['phase']=='INITIAL']
    gain=(initial[0]['mean_LPIPS']-decision['selected']['mean_LPIPS']) if initial and decision['selected'] else None
    return dict(status='OFFLINE_CALIBRATION_ANALYSIS',evidence_kind=d['evidence_kind'],
        split=d['split'],rows=summaries,selection=decision,
        proxy_endpoint_spearman=spearman([r['proxy_loss'] for r in paired],[r['mean_LPIPS'] for r in paired]),
        correlation_complete_candidates=len(paired),best_initial_to_final_LPIPS_gain=gain,
        cost=calibration_costs(d['cost_events'],d['query_ledger'],query_limit=d['query_limit'],limit_GPUh=d['calibration_limit_GPUh']),
        independent_TEST=False,production_acceptance_performed=False)
