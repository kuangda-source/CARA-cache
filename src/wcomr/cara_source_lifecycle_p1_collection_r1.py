"""Whole P1 algorithm on caller-owned request/CPU-score callbacks.

The original guardian remains the sole allocation bill. Measured operation
intervals here allocate calibration costs to the fair comparator; they never
create another bill. Persistent intents refuse physical/scorer retries.
"""
import copy
import fcntl
import json
import math
from pathlib import Path
import re

from .cara_budget_search_journal_r1 import (
    OriginalQueryUnknown, create_record, read_record, sync_directory,
)
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_estimation_r1 import complete_samples, fit_validate_plan, select_complete_FIT
from .cara_source_lifecycle_p1_plan_r1 import validate, SEARCH_CONFIG
from .cara_source_lifecycle_search_r1 import run_search


class Collection:
    def __init__(self, *, root, card, context, weights, execute, score, elapsed_seconds,
                 query_bounds, cpu_validation=False, create=False):
        self.profile = validate(card)
        if (context['scope_sha256'] != card['scope_sha256'] or context['host'] != 'two_card'
                or context['CPU_fixture_only'] is not cpu_validation
                or len(weights) != 36 or any(not math.isfinite(w) or w < 0 for w in weights)
                or not any(w > 0 for w in weights)):
            raise ValueError('Exact whole P1 caller context and frozen36 numerical weights required')
        if (set(query_bounds) != {'path_seconds', 'FIT_score_seconds', 'overhead_seconds'}
                or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in query_bounds.values())):
            raise ValueError('Complete preregistered query admission cost bounds required')
        self.root, self.card, self.context = Path(root), copy.deepcopy(card), copy.deepcopy(context)
        self.weights, self.query_bounds = list(weights), dict(query_bounds)
        self.execute, self.score, self.elapsed = execute, score, elapsed_seconds
        self.cpu_validation = cpu_validation
        self.binding = dict(schema='CARA_V1_P1_COLLECTION_BINDING_R1', context=context,
            scope_sha256=card['scope_sha256'], weights=weights, query_bounds=query_bounds,
            source_sha256={name: file_sha(Path(__file__).parent/name) for name in (
                Path(__file__).name, 'cara_source_lifecycle_p1_plan_r1.py',
                'cara_source_lifecycle_search_r1.py', 'cara_source_lifecycle_fit_scores_r1.py',
                'cara_source_lifecycle_estimation_r1.py', 'cara_source_lifecycle_planner_r1.py')})
        if create:
            self.root.mkdir(mode=0o700)
            sync_directory(self.root.parent)
            create_record(self.root/'binding.json', self.binding)
            create_record(self.root/'collection.lock', {})
            (self.root/'operations').mkdir()
        if read_record(self.root/'binding.json') != self.binding:
            raise ValueError('Original P1 source, design, cost bounds or context changed')
        self.allow_new, self.cursor = False, 0.
        self.operations, self.positions, self.physical_cache, self.score_cache = {}, [], {}, {}
        self.new_callbacks = 0

    def once(self, name, request, callback):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', name):
            raise ValueError('Fixed bounded operation identity required')
        directory = self.root/'operations'/name
        identity = dict(name=name, context_sha256=digest(self.context), request=request)
        if directory.exists():
            if read_record(directory/'intent.json') != identity:
                raise ValueError('Original operation identity differs: '+name)
            if not (directory/'return.json').exists():
                raise OriginalQueryUnknown('Recover original P1 operation without retry: '+name)
            returned = read_record(directory/'return.json')
            if returned['request_sha256'] != digest(identity) or digest(returned['payload']) != returned['payload_sha256']:
                raise ValueError('Original operation return changed: '+name)
            if returned['kind'] == 'FAILED_NO_RETRY':
                raise RuntimeError('Original P1 failure: '+json.dumps(returned['payload'], sort_keys=True))
        else:
            if not self.allow_new:
                raise OriginalQueryUnknown('Original P1 operation not reached; recovery cannot dispatch: '+name)
            before = self.elapsed()
            if not math.isfinite(before) or before < self.cursor:
                raise ValueError('Original guardian-relative monotonic allocation clock required')
            directory.mkdir(mode=0o700)
            sync_directory(directory.parent)
            create_record(directory/'intent.json', identity)
            self.new_callbacks += 1
            try:
                value = callback(directory)
                digest(value)
                kind = 'COMPLETE'
            except Exception as error:
                value = dict(type=type(error).__name__, message=str(error))
                kind = 'FAILED_NO_RETRY'
                after = self.elapsed()
                returned = dict(kind=kind, request_sha256=digest(identity), payload=value,
                    payload_sha256=digest(value), before_seconds=before, after_seconds=after,
                    charged_seconds=after-self.cursor)
                create_record(directory/'return.json', returned)
                raise
            after = self.elapsed()
            if not math.isfinite(after) or after < before:
                raise ValueError('Original elapsed clock moved backwards; preserve unresolved operation')
            returned = dict(kind=kind, request_sha256=digest(identity), payload=value,
                payload_sha256=digest(value), before_seconds=before, after_seconds=after,
                charged_seconds=after-self.cursor)
            create_record(directory/'return.json', returned)
        self.cursor = max(self.cursor, returned['after_seconds'])
        self.operations[name] = returned
        return copy.deepcopy(returned['payload'])

    def physical(self, name, member, kind, *, policy=None, timing='CLEAN', parent_id=None):
        candidate = 'NATIVE35' if kind == 'native' else ('ALLD' if kind == 'allD' else policy['fingerprint'])
        slot = dict(id=name, member=member, kind=kind, policy=policy, candidate_id=candidate,
            seed=0, timing=timing, parent_id=parent_id, context_sha256=digest(self.context))
        cache_key = digest({k: slot[k] for k in ('member', 'kind', 'candidate_id', 'seed', 'timing', 'parent_id')})
        if timing == 'CLEAN' and cache_key in self.physical_cache:
            original = self.physical_cache[cache_key]
            self.positions.append(dict(id=name, status='QUALITY_AND_CLEAN_SAMPLE_ALIAS',
                original_operation=original['operation'], independent_clean_sample=False))
            return original

        def invoke(directory):
            proof = self.execute(copy.deepcopy(slot), directory/'generation')
            if (proof['status'] != 'COMPLETE' or proof['CPU_fixture_only'] is not self.cpu_validation
                    or proof['context_sha256'] != digest(self.context)
                    or proof['source_revision'] != self.context['source_revision']
                    or proof['launch_id'] != self.context['launch_id']
                    or proof['member'] != member or proof['candidate_id'] != candidate or proof['seed'] != 0
                    or proof['solver_steps'] != 36 or proof['guided_pairs'] != 36
                    or proof['actual_updates'] != 36 or proof['fallback_count'] != 0
                    or proof['physical_model_pairs'] != (44 if kind == 'scalar' else 36)):
                raise ValueError('Complete original P1 free-running physical request required')
            if file_sha(proof['video']['path']) != proof['video']['sha256']:
                raise ValueError('Original complete guarded video bytes differ')
            create_record(directory/'request-complete.json', proof)
            return dict(operation=name, proof=proof,
                proof_path=str((directory/'request-complete.json').resolve()),
                proof_sha256=file_sha(directory/'request-complete.json'))

        position = dict(id=name, status='ATTEMPTED', original_operation=name,
                        independent_clean_sample=timing == 'CLEAN')
        self.positions.append(position)
        try:
            result = self.once(name, slot, invoke)
        except Exception as error:
            position['status'] = 'UNKNOWN' if isinstance(error, OriginalQueryUnknown) else 'FAILED_NO_RETRY'
            raise
        proof = result['proof']
        if (file_sha(result['proof_path']) != result['proof_sha256']
                or read_record(Path(result['proof_path'])) != proof
                or file_sha(proof['video']['path']) != proof['video']['sha256']
                or file_sha(proof['final_latent']['path']) != proof['final_latent']['file_sha256']):
            raise ValueError('Retained original complete request changed')
        self.physical_cache[cache_key] = result
        position['status'] = 'COMPLETE'
        return result

    @staticmethod
    def equivalent(left, right):
        a, b = left['proof'], right['proof']
        if (a['final_latent']['tensor_sha256'] != b['final_latent']['tensor_sha256']
                or a['pre_encode_RGB'] != b['pre_encode_RGB']
                or a['post_request_RNG_sha256'] != b['post_request_RNG_sha256']):
            raise ValueError('Full latent, RGB or post-request RNG identity control failed')

    def fit_score(self, candidate, outputs, references):
        if candidate in self.score_cache:
            return self.score_cache[candidate]
        pairs = []
        for member, output, reference in zip(self.card['FIT'], outputs, references):
            pair = dict(member=member)
            for side, value in (('candidate', output), ('reference', reference)):
                pair[side] = dict(member=member, seed=0, candidate_id=value['proof']['candidate_id'],
                    proof_path=value['proof_path'], proof_sha256=value['proof_sha256'], **value['proof']['video'])
            pairs.append(pair)
        packet = dict(schema='CARA_V1_INTERNAL_COMPLETE_FIT_ARTIFACTS_R1',
            purpose='P1_INTERNAL_FIT_CALIBRATION', CPU_fixture_only=self.cpu_validation,
            FIT_members=self.card['FIT'], schedule_sha256=digest(self.card['schedule']),
            source_revision=self.context['source_revision'], launch_id=self.context['launch_id'],
            context_sha256=digest(self.context), candidate_id=candidate, query_id='score-'+candidate,
            score_shape=[93, 64, 64, 3] if self.cpu_validation else [93, 432, 768, 3], pairs=pairs)

        def invoke(directory):
            accepted = self.score(copy.deepcopy(packet), directory)
            if (accepted['schema'] != 'CARA_V1_INTERNAL_COMPLETE_FIT_SCORES_R1'
                    or accepted['status'] != 'ACCEPTED_INTERNAL_CALIBRATION_ONLY'
                    or accepted['CPU_fixture_only'] is not self.cpu_validation
                    or accepted['packet_sha256'] != digest(packet)
                    or accepted['whole_card_scientific_accepted'] is not False):
                raise ValueError('Original complete bounded internal calibration acceptance required')
            # Reuse the fixed selector's complete-cohort validation; no selection
            # from a one-input or partial93-frame internal return is possible.
            plan = dict(policy=dict(fingerprint=candidate), proxy_cost=0., dense_steps=[])
            select_complete_FIT([plan], accepted['rows'], self.card['FIT'])
            return accepted

        name = 'score-'+candidate
        result = self.once(name, packet, invoke)
        self.score_cache[candidate] = result, name
        return result, name

    def run(self, *, allow_new=False):
        with (self.root/'collection.lock').open('r+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.allow_new = allow_new
            self.positions, self.physical_cache, self.score_cache = [], {}, {}
            self.operations, self.cursor, self.new_callbacks = {}, 0., 0
            result = dict(status='P1_INCOMPLETE_NO_SCIENTIFIC_ACCEPTANCE',
                scope_sha256=self.card['scope_sha256'], CPU_fixture_only=self.cpu_validation,
                semantic_upper=self.card['semantic_positions'], physical_paths_upper=146,
                whole_card_scientific_accepted=False, GPU_submissions=0, ledger_written=False)
            try:
                result.update(self._run())
                result['status'] = 'P1_ALGORITHM_COMPLETE_PENDING_ORIGINAL_RELEASE_SETTLEMENT_AND_SCIENCE'
            except Exception as error:
                result['failure'] = dict(type=type(error).__name__, message=str(error))
            result.update(semantic_positions=copy.deepcopy(self.positions),
                complete_semantic_positions=sum(p['status'] in ('COMPLETE', 'QUALITY_AND_CLEAN_SAMPLE_ALIAS')
                                               for p in self.positions),
                new_callback_calls=self.new_callbacks,
                operations={name: dict(charged_seconds=row['charged_seconds'],
                    return_sha256=file_sha(self.root/'operations'/name/'return.json')) for name, row in self.operations.items()})
            target = self.root/'algorithm-summary.json'
            if target.exists():
                # Recovery is an observation; never replace the original summary.
                result['original_summary_sha256'] = file_sha(target)
            elif allow_new:
                create_record(target, result)
            return result

    def _run(self):
        card, design = self.card, self.card['calibration_design']
        baseline, parents = {}, {}
        common = set()
        for control in card['controls'][:2]:
            role = card['roles'].get(control.get('role'), {})
            out = self.physical(control['id'], control['member'], control['kind'],
                                policy=role.get('policy'), timing=control['timing'])
            common.add(out['operation'])
        for member in card['FIT']:
            for role in card['baseline_roles']:
                definition = card['roles'][role]
                out = self.physical('baseline-'+role+'-'+str((card['FIT']+card['CHECK']).index(member)),
                    member, definition['kind'], policy=definition.get('policy'))
                baseline[member, role] = out
                if member in card['FIT'] and role in ('NATIVE35', 'UNIFORM19_C'):
                    common.add(out['operation'])
        for i, member in enumerate(card['FIT']):
            for parent in design['parents']:
                out = self.physical('parent-'+parent['id']+'-'+str(i), member, 'scalar',
                    policy=parent['policy'], parent_id=parent['id'], timing='DIAGNOSTIC')
                parents[member, parent['id']] = out
                common.add(out['operation'])
        for control in card['controls'][2:]:
            if control['member'] not in card['FIT']:
                continue
            role = card['roles'].get(control.get('role'), {})
            out = self.physical(control['id'], control['member'], control['kind'],
                policy=control.get('policy', role.get('policy')), timing=control['timing'])
            expected = (parents[control['member'], control['compare_parent']] if 'compare_parent' in control
                        else baseline[control['member'], control['compare_to']])
            self.equivalent(out, expected)
            if control['member'] in card['FIT']:
                common.add(out['operation'])
        packet = dict(schema='CARA_V1_SAME_STATE_SCALAR_LABELS_R1', status='COMPLETE',
            input_kind='SYNTHETIC_CPU' if self.cpu_validation else 'PRODUCTION_CAPTURE',
            design_scope_sha256=design['scope_sha256'], schedule_sha256=digest(card['schedule']),
            rows=[r for out in parents.values() for r in out['proof']['scalar_labels']],
            provenance=dict(teacher='candidate_own_current_state_shadow_D', teacher_writes_parent=False,
                target='FP64_MSE_OF_ACTUAL_SAME_STATE_FP32_CFG', target_normalized=False))
        samples = complete_samples(packet, design, card['schedule'])
        references = [baseline[m, 'NATIVE35'] for m in card['FIT']]
        models, selected, main_dependencies = {}, {}, {}
        for family in card['families']:
            model_name = 'fit-'+family
            models[family] = self.once(model_name, dict(labels_sha256=digest(packet), weights=self.weights),
                lambda directory: fit_validate_plan(samples, design, card, self.weights, families=(family,)))
            for budget in card['D_budgets']:
                candidates = models[family]['families'][0]['candidates'][str(budget)]['plans']
                scores, dependencies = [], set()
                for rank, plan in enumerate(candidates):
                    outputs = [self.physical(f'fit-{family}-K{budget}-r{rank}-f{i}', member, 'policy',
                        policy=plan['policy']) for i, member in enumerate(card['FIT'])]
                    accepted, score_name = self.fit_score(plan['policy']['fingerprint'], outputs, references)
                    scores.extend(accepted['rows'])
                    dependencies.update([score_name, *(out['operation'] for out in outputs)])
                selection_name = 'select-'+family+'-K'+str(budget)
                selection = self.once(selection_name, dict(candidates=candidates, scores_sha256=digest(scores)),
                    lambda directory: select_complete_FIT(candidates, scores, card['FIT']))
                winner = next(p for p in candidates if p['policy']['fingerprint'] == selection['candidate_id'])
                selected[family, budget] = winner
                dependencies.add(selection_name)
                if family == card['families'][-1]:
                    main_dependencies[budget] = dependencies
        # FIT selection is sealed above before any selected-policy CHECK output.
        for member in card['CHECK']:
            for role in card['baseline_roles']:
                definition = card['roles'][role]
                baseline[member, role] = self.physical(
                    'baseline-'+role+'-'+str((card['FIT']+card['CHECK']).index(member)),
                    member, definition['kind'], policy=definition.get('policy'))
        for control in card['controls'][2:]:
            if control['member'] in card['CHECK']:
                out = self.physical(control['id'], control['member'], control['kind'], timing=control['timing'])
                self.equivalent(out, baseline[control['member'], control['compare_to']])
        for (family, budget), winner in selected.items():
            for i, member in enumerate(card['CHECK']):
                self.physical(f'CHECK-{family}-K{budget}-{i}', member, 'policy', policy=winner['policy'])

        costs = lambda names: math.fsum(self.operations[name]['charged_seconds'] for name in names)
        main_model_cost = costs({'fit-'+card['families'][-1]})
        common_cost = costs(common)
        references_and_controls = {name for name in common
            if not name.startswith(('parent-', 'control-parent-'))}
        reference_share = costs(references_and_controls)/2
        searches = {}
        for budget in card['D_budgets']:
            cap = common_cost/2+main_model_cost/2+costs(main_dependencies[budget])
            origin = self.once('search-clock-K'+str(budget), dict(cap_seconds=cap),
                               lambda directory: dict(elapsed_seconds=self.elapsed()))['elapsed_seconds']

            def evaluate(query):
                before = reference_share+self.elapsed()-origin
                policy = query['policy']
                candidate = policy['fingerprint']
                needed = sum(digest(dict(member=m, kind='policy', candidate_id=candidate, seed=0,
                    timing='CLEAN', parent_id=None)) not in self.physical_cache for m in card['FIT'])
                bound = (needed*self.query_bounds['path_seconds']
                         +(0 if candidate in self.score_cache else self.query_bounds['FIT_score_seconds'])
                         +self.query_bounds['overhead_seconds'])
                base = dict(request_sha256=query['request_sha256'], charged_before_seconds=before,
                            cost_cap_seconds=cap)
                if before+bound > cap:
                    return dict(base, status='NOT_ADMITTED', rows=[], new_physical_paths=0,
                                charged_after_seconds=reference_share+self.elapsed()-origin)
                outputs = [self.physical(f'search-K{budget}-q{query["query_id"]}-f{i}', member, 'policy',
                    policy=policy) for i, member in enumerate(card['FIT'])]
                accepted, _ = self.fit_score(candidate, outputs, references)
                return dict(base, status='COMPLETE', rows=accepted['rows'], new_physical_paths=needed,
                    charged_after_seconds=reference_share+self.elapsed()-origin,
                    score_packet_sha256=digest(accepted))

            directory = self.root/('search-K'+str(budget))
            result = run_search(directory, card['schedule'], self.profile, budget, SEARCH_CONFIG,
                fit_members=card['FIT'], context_sha256=digest(self.context), cap_seconds=cap,
                evaluate=evaluate, create=not directory.exists() and self.allow_new,
                allow_new_queries=self.allow_new)
            if (result['failure'] or result['termination'] not in (
                    'CONFIGURED_SA_HC_FINISHED', 'MEASURED_COST_ADMISSION_STOP')):
                raise ValueError('Original fair-search failure/unknown requires recovery, not a new search')
            searches[str(budget)] = dict(result, cap_components_seconds=dict(
                half_shared_calibration=common_cost/2, half_main_estimation=main_model_cost/2,
                main_complete_FIT_selection=costs(main_dependencies[budget]), reference_share=reference_share))
            # A deterministic controller replay reuses durable query returns.
            # Re-read their original artifacts too, without authorizing callbacks.
            allowed = self.allow_new
            self.allow_new = False
            try:
                for query in result['queries']:
                    for i, member in enumerate(card['FIT']):
                        name = f'search-K{budget}-q{query["query_id"]}-f{i}'
                        if any(p['id'] == name for p in self.positions):
                            continue
                        if query['status'] == 'COMPLETE':
                            from .cara_fast_spec_r1 import policy_from_mask
                            policy = policy_from_mask(self.profile, query['dense'])
                            self.physical(name, member, 'policy', policy=policy)
                        else:
                            self.positions.append(dict(id=name, status='BUDGET_NOT_ADMITTED',
                                                       independent_clean_sample=False))
                for q in range(result['requested_queries']+1, SEARCH_CONFIG.max_evaluations+1):
                    self.positions.extend(dict(id=f'search-K{budget}-q{q}-f{i}',
                        status='BUDGET_STOP_NOT_REACHED', independent_clean_sample=False) for i in range(2))
                for query in result['queries']:
                    if query['status'] == 'COMPLETE':
                        candidate = query['policy_fingerprint']
                        if candidate not in self.score_cache:
                            outputs = [self.physical_cache[digest(dict(member=m, kind='policy',
                                candidate_id=candidate, seed=0, timing='CLEAN', parent_id=None))]
                                for m in card['FIT']]
                            self.fit_score(candidate, outputs, references)
            finally:
                self.allow_new = allowed
            best = result['best_complete_candidate']
            if best is None:
                raise ValueError('Fair comparator did not complete even its original Uniform query')
            from .cara_fast_spec_r1 import policy_from_mask
            policy = policy_from_mask(self.profile, best['dense'])
            for i, member in enumerate(card['CHECK']):
                self.physical(f'CHECK-search-K{budget}-{i}', member, 'policy', policy=policy)
        return dict(source_labels=packet, models=models,
            FIT_selected={family+'-K'+str(budget): winner for (family, budget), winner in selected.items()},
            fair_searches=searches, original_RGB_MSE_search_reselected=False,
            internal_metric_results_recomputed=False, final_scoring_and_original_terminal_acceptance_pending=True)
