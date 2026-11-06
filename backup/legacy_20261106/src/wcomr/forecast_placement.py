"""Pure source-topology replay and exact exposed-trace placement search.

No model, sparse kernel or video generation. Positions use future reference
schedule information and must never be advertised as an online policy.
"""
from collections import Counter
from itertools import combinations

from .selective_refresh_policy import SparsePlacementPolicy


def replay(events, policy, *, verify_actual=False):
    if len(events) != 72:
        raise ValueError('Complete 72-call event record required')
    windows, dense_history, ordinals = [[], []], [[], []], [0, 0]
    rows, sources, kind_pairs = [], [], Counter()
    for call, event in enumerate(events, 1):
        cfg = (call - 1) % 2
        assert event['call'] == call and event['cfg'] == cfg
        assert event['counter'] == (call - 1) % 70
        assert event['native_cycle_reset'] == (call == 70)
        eligible = (not event['official_skipped'] and not event['warm_start']
                    and len(dense_history[cfg]) >= 2 and event['paid_probe'])
        assert eligible == event['selection_eligible']
        chosen = False
        if eligible:
            ordinals[cfg] += 1
            chosen = policy.select(ordinals[cfg], cfg=cfg)
        references = windows[cfg][-2:]
        assert [v['call'] for v in references] == [v['call'] for v in event['references_read']]
        if verify_actual:
            assert chosen == event['selection_sparse_chosen']
            assert [(v['call'], v['kind']) for v in references] == [
                (v['call'], v['kind']) for v in event['references_read']]
        if event['official_skipped']:
            assert not chosen and event['action'] == 'cache' and len(references) == 2
            kinds = tuple(v['kind'] for v in references)
            kind_pairs[kinds] += 1
            rows.append({'call':call, 'cfg':cfg,
                'source_calls':[v['call'] for v in references],
                'source_kinds':list(kinds),
                'same_CFG_source_ages':[(call-v['call'])//2 for v in references]})
        else:
            source = {'call':call, 'cfg':cfg, 'kind':'sparse' if chosen else 'dense',
                      'eligible_ordinal':ordinals[cfg] if eligible else None}
            sources.append(source)
            if len(windows[cfg]) <= 2:
                windows[cfg].append(source)
            else:
                windows[cfg][-2], windows[cfg][-1] = windows[cfg][-1], source
            if not chosen:
                dense_history[cfg] = (dense_history[cfg]+[source])[-2:]
        if event['native_cycle_reset']:
            windows, dense_history, ordinals = [[], []], [[], []], [0, 0]
    sparse = [s for s in sources if s['kind'] == 'sparse']
    exposure = []
    for source in sparse:
        uses = [row for row in rows if source['call'] in row['source_calls']]
        exposure.append({'S_call':source['call'], 'cfg':source['cfg'],
            'future_cache_calls':[row['call'] for row in uses],
            'same_CFG_ages':[(row['call']-source['call'])//2 for row in uses]})
    return {'deep_calls':len(sources), 'cache_calls':len(rows),
        'S_calls':[s['call'] for s in sparse],
        'S_per_CFG':[sum(s['cfg']==cfg for s in sparse) for cfg in (0,1)],
        'S_operators':len(sparse)*len(policy.sparse_layers),
        'approximate_cache_calls':[row['call'] for row in rows if 'sparse' in row['source_kinds']],
        'approximate_source_reads':sum(row['source_kinds'].count('sparse') for row in rows),
        'reference_kind_pairs':{','.join(k):v for k,v in kind_pairs.items()},
        'cache_rows':rows, 'S_source_exposure':exposure}


def optimize(events, layers, quotas, *, keep_first_S=False):
    """Enumerate every branch-local schedule with fixed S quotas, no errors."""
    selected, branches = [], []
    for cfg in (0, 1):
        count = sum(e['cfg']==cfg and e['selection_eligible'] for e in events)
        quota = quotas[cfg]
        if not 0 < quota <= count:
            raise ValueError('Positive fixed branch-local S quota required')
        best, tried = None, 0
        for slots in combinations(range(1,count+1), quota):
            if keep_first_S and 1 not in slots:
                continue
            per_cfg = [(), ()];per_cfg[cfg] = slots
            policy = SparsePlacementPolicy(tuple(layers), per_cfg_eligible_ordinals=tuple(per_cfg))
            result = replay(events, policy)
            cost = sum(row['cfg']==cfg and 'sparse' in row['source_kinds'] for row in result['cache_rows'])
            reads = sum(row['source_kinds'].count('sparse') for row in result['cache_rows'] if row['cfg']==cfg)
            score = (cost, reads, slots)
            tried += 1
            if best is None or score < best[0]:
                best = (score, slots)
        selected.append(best[1])
        branches.append({'cfg':cfg, 'eligible_refreshes':count, 'S_quota':quota,
            'enumerated_schedules':tried, 'minimum_approximate_cache_calls':best[0][0],
            'minimum_source_reads_at_primary_minimum':best[0][1]})
    policy = SparsePlacementPolicy(tuple(layers), per_cfg_eligible_ordinals=tuple(selected))
    return {'policy':policy.to_dict(), 'keep_first_S':keep_first_S,
            'branches':branches, 'replay':replay(events,policy)}
