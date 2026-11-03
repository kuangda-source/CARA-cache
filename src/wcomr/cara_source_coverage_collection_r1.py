"""C1 endpoint collection on the existing persistent request/scorer callbacks."""
import copy
import fcntl
import math
from pathlib import Path

from .cara_budget_search_journal_r1 import create_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest, policy_from_mask
from .cara_source_coverage_card_r1 import validate
from .cara_source_coverage_r1 import select_endpoint
from .cara_source_lifecycle_p1_collection_r1 import Collection
from .cara_source_lifecycle_p1_plan_r1 import SEARCH_CONFIG
from .cara_source_lifecycle_search_r1 import run_search


class CoverageCollection(Collection):
    def __init__(self, **kwargs):
        kwargs['card_validator'] = validate
        super().__init__(**kwargs)

    def cost(self, names):
        return math.fsum(self.operations[name]['charged_seconds'] for name in set(names))

    def run(self, *, allow_new=False):
        with (self.root/'collection.lock').open('r+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.allow_new = allow_new
            self.positions, self.physical_cache, self.score_cache = [], {}, {}
            self.operations, self.cursor, self.new_callbacks = {}, 0., 0
            result = dict(status='C1_INCOMPLETE_NO_SCIENTIFIC_ACCEPTANCE',
                scope_sha256=self.card['scope_sha256'], CPU_fixture_only=self.cpu_validation,
                semantic_denominator=166, physical_paths_upper=166,
                whole_card_scientific_accepted=False, GPU_submissions=0, ledger_written=False)
            try:
                result.update(self._collect())
                if len(self.positions) != 166:
                    raise ValueError('Complete C1 semantic denominator differs')
                result['status'] = 'C1_COMPLETE_PENDING_RELEASE_SETTLEMENT_AND_FINAL_SCORES'
            except Exception as error:
                result['failure'] = dict(type=type(error).__name__, message=str(error))
            result.update(semantic_positions=copy.deepcopy(self.positions),
                new_callback_calls=self.new_callbacks,
                operations={name:dict(charged_seconds=row['charged_seconds'],
                    return_sha256=file_sha(self.root/'operations'/name/'return.json'))
                    for name,row in self.operations.items()})
            target = self.root/'algorithm-summary.json'
            if target.exists():
                result['original_summary_sha256'] = file_sha(target)
            elif allow_new:
                create_record(target, result)
            return result

    def _collect(self):
        card, baseline, common = self.card, {}, set()
        all_members = card['FIT']+card['CHECK']
        for row in card['controls'][:2]:
            definition = card['roles'].get(row.get('role'), {})
            out = self.physical(row['id'], row['member'], row['kind'],
                policy=definition.get('policy'), timing=row['timing'])
            common.add(out['operation'])
        for member in card['FIT']:
            for role in card['baseline_roles']:
                definition = card['roles'][role]
                out = self.physical(f'baseline-{role}-{all_members.index(member)}', member,
                    definition['kind'], policy=definition.get('policy'))
                baseline[member,role] = out
                if role in ('NATIVE35','UNIFORM19_C'):
                    common.add(out['operation'])
        for row in card['controls'][2:]:
            if row['member'] not in card['FIT']:
                continue
            definition = card['roles'].get(row.get('role'), {})
            out = self.physical(row['id'], row['member'], row['kind'],
                policy=definition.get('policy'), timing=row['timing'])
            self.equivalent(out, baseline[row['member'],row['compare_to']])
            common.add(out['operation'])
        reference_share = self.cost(common)/2
        references = [baseline[m,'NATIVE35'] for m in card['FIT']]
        inputs = {r['name']:digest(r) for r in card['inputs']}
        metric_protocol = digest(dict(metric='ALEX_LPIPS_FULL93_FIDELITY_V2',
            schedule=card['schedule'], source_revision=self.context['source_revision']))
        selected, caps, candidate_outputs = {}, {}, {}
        # main/single are evaluated once; neutral/phase views reuse their
        # predeclared main8 subsets without another generation or score.
        for name, view in card['views'].items():
            rows, dependencies = [], set()
            for rank, candidate in enumerate(view['candidates']):
                key = candidate['candidate_id']
                if name.startswith(('neutral3','phase3')):
                    outputs = candidate_outputs[key]
                else:
                    outputs = [self.physical(f'candidate-{name}-r{rank}-f{i}', member, 'policy',
                        policy=candidate['policy']) for i,member in enumerate(card['FIT'])]
                candidate_outputs[key] = outputs
                accepted, operation = self.fit_score(key, outputs, references)
                dependencies.update([operation, *(out['operation'] for out in outputs)])
                score_cost = self.cost([operation])/2
                for i,member in enumerate(card['FIT']):
                    score = next(r for r in accepted['rows'] if r['member'] == member)
                    proof = outputs[i]['proof']
                    rows.append(dict(candidate_id=key, member=member, status='COMPLETE', frames=93,
                        LPIPS=math.fsum(score['Alex_curve'])/93, T_DD=proof['T_DD'],
                        T_request=proof['T_request'], input_sha256=inputs[member],
                        reference_sha256=references[i]['proof']['video']['sha256'],
                        metric_protocol_sha256=metric_protocol,
                        actual_GPUh=(self.cost([outputs[i]['operation']])+score_cost)/3600))
            choice = self.once('select-'+name, dict(pool_sha256=view['pool_sha256'], rows_sha256=digest(rows)),
                lambda directory: select_endpoint(view, card['FIT'], rows,
                    cost_limit_GPUh=math.fsum([reference_share/3600]+[r['actual_GPUh'] for r in rows]),
                    overhead_GPUh=reference_share/3600))
            if choice['status'] != 'SELECTED':
                raise ValueError('No complete candidate in the frozen endpoint view')
            winner = next(c for c in view['candidates'] if c['candidate_id'] == choice['selected']['candidate_id'])
            selected[name] = dict(candidate=winner, selection=choice)
            if name.startswith('main8'):
                caps[name[-2:]] = reference_share+self.cost(dependencies|{'select-'+name})

        searches, search_outputs = {}, {}
        for budget in card['D_budgets']:
            cap = caps[str(budget)]
            origin = self.once(f'search-clock-K{budget}', dict(cap_seconds=cap),
                lambda directory: dict(elapsed_seconds=self.elapsed()))['elapsed_seconds']
            saved_caches = self.physical_cache, self.score_cache
            self.physical_cache, self.score_cache = {}, {}
            try:
                def evaluate(query):
                    candidate = query['policy']['fingerprint']
                    needed = sum(digest(dict(member=m,kind='policy',candidate_id=candidate,seed=0,
                        timing='CLEAN',parent_id=None)) not in self.physical_cache for m in card['FIT'])
                    before = reference_share+self.elapsed()-origin
                    bound = needed*self.query_bounds['path_seconds'] + self.query_bounds['overhead_seconds']
                    if candidate not in self.score_cache:
                        bound += self.query_bounds['FIT_score_seconds']
                    base = dict(request_sha256=query['request_sha256'], charged_before_seconds=before,
                        cost_cap_seconds=cap)
                    if before+bound > cap:
                        return dict(base,status='NOT_ADMITTED',rows=[],new_physical_paths=0,
                            charged_after_seconds=reference_share+self.elapsed()-origin)
                    outputs = [self.physical(f'search-K{budget}-q{query["query_id"]}-f{i}',m,'policy',
                        policy=query['policy']) for i,m in enumerate(card['FIT'])]
                    if query['phase'] == 'INITIAL':
                        for i,m in enumerate(card['FIT']):
                            self.equivalent(outputs[i],baseline[m,f'UNIFORM{budget}_C'])
                    # Method isolation needs an independent score operation ID,
                    # even if a candidate was scored by a different method.
                    accepted, _ = self.search_score(budget, candidate, outputs, references)
                    return dict(base,status='COMPLETE',rows=accepted['rows'],new_physical_paths=needed,
                        charged_after_seconds=reference_share+self.elapsed()-origin,
                        score_packet_sha256=digest(accepted))
                directory = self.root/f'search-K{budget}'
                search = run_search(directory,card['schedule'],self.profile,budget,SEARCH_CONFIG,
                    fit_members=card['FIT'],context_sha256=digest(self.context),cap_seconds=cap,
                    evaluate=evaluate,create=not directory.exists() and self.allow_new,
                    allow_new_queries=self.allow_new)
                if search['failure'] or search['best_complete_candidate'] is None:
                    raise ValueError('Original bounded search failure/unknown; no retry or replacement')
                allowed = self.allow_new
                self.allow_new = False
                try:
                    for q in range(1,SEARCH_CONFIG.max_evaluations+1):
                        query = next((r for r in search['queries'] if r['query_id'] == q),None)
                        for i,m in enumerate(card['FIT']):
                            name = f'search-K{budget}-q{q}-f{i}'
                            if any(p['id'] == name for p in self.positions):
                                continue
                            if query and query['status'] == 'COMPLETE':
                                out = self.physical(name,m,'policy',policy=policy_from_mask(self.profile,query['dense']))
                                search_outputs[budget,query['policy_fingerprint'],m] = out
                            else:
                                status = 'BUDGET_NOT_ADMITTED' if query else 'BUDGET_STOP_NOT_REACHED'
                                self.positions.append(dict(id=name,status=status,
                                    independent_clean_sample=False))
                        if query and query['status'] == 'COMPLETE':
                            key = query['policy_fingerprint']
                            outputs = [self.physical_cache[digest(dict(member=m,kind='policy',
                                candidate_id=key,seed=0,timing='CLEAN',parent_id=None))] for m in card['FIT']]
                            self.search_score(budget,key,outputs,references)
                    best = search['best_complete_candidate']
                    for m in card['FIT']:
                        key = digest(dict(member=m,kind='policy',candidate_id=best['policy_fingerprint'],
                            seed=0,timing='CLEAN',parent_id=None))
                        search_outputs[budget,best['policy_fingerprint'],m] = self.physical_cache[key]
                finally:
                    self.allow_new = allowed
                searches[str(budget)] = search
            finally:
                self.physical_cache, self.score_cache = saved_caches

        for member in card['CHECK']:
            for role in card['baseline_roles']:
                definition = card['roles'][role]
                baseline[member,role] = self.physical(f'baseline-{role}-{all_members.index(member)}',member,
                    definition['kind'],policy=definition.get('policy'))
        for row in card['controls'][2:]:
            if row['member'] not in card['CHECK']:
                continue
            out = self.physical(row['id'],row['member'],row['kind'],timing=row['timing'])
            self.equivalent(out,baseline[row['member'],row['compare_to']])
        for name, choice in selected.items():
            for i,member in enumerate(card['CHECK']):
                self.physical(f'CHECK-{name}-{i}',member,'policy',policy=choice['candidate']['policy'])
        for budget,search in searches.items():
            policy = policy_from_mask(self.profile,search['best_complete_candidate']['dense'])
            for i,member in enumerate(card['CHECK']):
                self.physical(f'CHECK-search-K{budget}-{i}',member,'policy',policy=policy)
        return dict(FIT_selected=selected,fair_searches=searches,common_cost_seconds=self.cost(common),
            main8_cost_caps_seconds=caps,source_labels_collected=0,scientific_quality_positions=60,
            Uniform_search_baseline_identity_bridges=4,
            endpoint_selection_uses_CHECK=False,search_cross_method_cache_credit=False,
            formal_scores_pending_original_release_and_unique_settlement=True)

    def search_score(self, budget, candidate, outputs, references):
        return self.fit_score(candidate,outputs,references,operation_prefix=f'searchK{budget}-')
