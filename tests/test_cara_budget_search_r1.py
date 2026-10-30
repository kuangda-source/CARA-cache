"""Actual frozen grid/grammar with synthetic endpoint objectives, never a model."""
from dataclasses import replace
from pathlib import Path
import random
import unittest

from wcomr.cara_budget_search_r1 import SearchConfig, initial_mask, legal_swaps, search
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest, policy_from_mask, profile_from

ROOT = Path(__file__).resolve().parents[1]


class BudgetSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
        cls.profile = profile_from(cls.card['profile'])

    def run_search(self, config=None, evaluate=None):
        def flat(request):
            return dict(request_sha256=request['request_sha256'], rows=[
                dict(member=m, status='COMPLETE', RGB_MSE=1.0) for m in request['FIT_members']])
        return search(self.card['schedule'], self.profile, config or SearchConfig(42, 8),
            fit_members=self.card['FIT'], context_sha256=digest({'CPU_FIXTURE': self.card['scope_sha256']}),
            evaluate=evaluate or flat)

    def test_full_default_controller_preserves_quota_and_counts_repeated_calls(self):
        result = self.run_search(SearchConfig(42, 301))
        self.assertEqual(result['termination'], 'CONFIGURED_SEARCH_FINISHED')
        self.assertEqual(result['attempted_cohort_evaluations'], 301)
        self.assertEqual(result['completed_cohort_evaluations'], 301)
        self.assertEqual(result['requested_endpoint_paths'], 602)
        self.assertEqual(result['SA_iterations_completed'], 200)
        self.assertEqual(result['HC_iterations_completed'], 5)
        self.assertGreater(result['duplicate_candidate_calls'], 0)
        self.assertEqual(result['best_complete_candidate']['query_id'], 1)
        for row in result['queries']:
            self.assertEqual(len(row['dense']), 19)
            self.assertTrue(set(range(1, 8)) | {24, 36} <= set(row['dense']))
        for flag in ('teacher_cost_included', 'evaluation_memoization', 'convergence_claimed',
                     'GPU_dispatch_ready', 'durable_production_recovery_implemented'):
            self.assertFalse(result[flag])

    def test_current_neighborhood_reaches_beyond_original_single_swap(self):
        dense = initial_mask(self.card['schedule'], self.profile)
        self.assertEqual(dense, [1,2,3,4,5,6,7,16,19,22,23,24,25,26,27,28,29,31,36])
        self.assertEqual(policy_from_mask(self.profile, dense), self.card['roles']['UNIFORM19_C']['policy'])
        neighbors = legal_swaps(self.profile, dense)
        self.assertEqual(len(neighbors), 170)
        second = legal_swaps(self.profile, neighbors[0][2])
        self.assertTrue(any(len(set(candidate)-set(dense)) == 2 for _, _, candidate in second))

    def test_private_randomness_reproducible_and_does_not_touch_global_rng(self):
        random.seed(109)
        before = random.getstate()
        one = self.run_search()
        self.assertEqual(random.getstate(), before)
        random.seed(234)
        self.assertEqual(one, self.run_search())
        self.assertNotEqual(one['queries'], self.run_search(SearchConfig(43, 8))['queries'])

    def test_exact_query_cap_and_best_complete_on_partial_hc(self):
        calls = []
        def improving(request):
            calls.append(request)
            return dict(request_sha256=request['request_sha256'], rows=[
                dict(member=m, status='COMPLETE', RGB_MSE=10-request['query_id'])
                for m in request['FIT_members']])
        result = self.run_search(SearchConfig(42, 7, sa_iterations=2), improving)
        self.assertEqual(len(calls), 7)
        self.assertEqual(result['termination'], 'QUERY_CAP_REACHED')
        self.assertEqual(result['best_complete_candidate']['query_id'], 7)
        self.assertEqual(result['HC_iterations_completed'], 0)
        self.assertFalse(result['configured_search_finished'])
        self.assertFalse(result['convergence_claimed'])

    def test_two_fit_objective_is_equal_weight_and_row_order_independent(self):
        def different(request):
            return dict(request_sha256=request['request_sha256'], rows=[
                dict(member=m, status='COMPLETE', RGB_MSE=value)
                for m, value in reversed(list(zip(request['FIT_members'], [2.0, 6.0])))])
        result = self.run_search(SearchConfig(42, 1, sa_iterations=0, hc_iterations=0), different)
        self.assertEqual(result['best_complete_candidate']['mean_RGB_MSE'], 4)
        self.assertTrue(result['configured_search_finished'])

    def test_failed_query_consumes_cap_and_preserves_previous_best_without_retry(self):
        for fault in ('exception', 'identity', 'missing', 'duplicate', 'incomplete', 'nan', 'inf', 'negative'):
            with self.subTest(fault=fault):
                calls = []
                def evaluate(request):
                    calls.append(request['query_id'])
                    response = dict(request_sha256=request['request_sha256'], rows=[
                        dict(member=m, status='COMPLETE', RGB_MSE=1.0) for m in request['FIT_members']])
                    if len(calls) == 1:
                        return response
                    if fault == 'exception':
                        raise OSError('declared CPU evaluator failure')
                    if fault == 'identity': response['request_sha256'] = '0'*64
                    elif fault == 'missing': response['rows'].pop()
                    elif fault == 'duplicate': response['rows'][1] = dict(response['rows'][0])
                    elif fault == 'incomplete': response['rows'][1]['status'] = 'RUNNING'
                    else: response['rows'][1]['RGB_MSE'] = {'nan':float('nan'), 'inf':float('inf'), 'negative':-1}[fault]
                    return response
                result = self.run_search(evaluate=evaluate)
                self.assertEqual(calls, [1, 2])
                self.assertEqual(result['termination'], 'EVALUATION_FAILED_NO_RETRY')
                self.assertEqual(result['attempted_cohort_evaluations'], 2)
                self.assertEqual(result['completed_cohort_evaluations'], 1)
                self.assertEqual(result['best_complete_candidate']['query_id'], 1)
                self.assertEqual(result['queries'][-1]['status'], 'FAILED')

    def test_first_query_failure_returns_no_selected_candidate(self):
        result = self.run_search(evaluate=lambda request: None)
        self.assertEqual(result['attempted_cohort_evaluations'], 1)
        self.assertIsNone(result['best_complete_candidate'])
        self.assertIsNotNone(result['failure'])

    def test_callback_cannot_mutate_controller_request(self):
        def mutate(request):
            request['dense'].clear()
            request['policy']['actions'].clear()
            return dict(request_sha256=request['request_sha256'], rows=[
                dict(member=m, status='COMPLETE', RGB_MSE=1.0) for m in request['FIT_members']])
        result = self.run_search(evaluate=mutate)
        self.assertTrue(all(len(row['dense']) == 19 for row in result['queries']))
        self.assertEqual(len(result['best_complete_candidate']['dense']), 19)

    def test_invalid_configuration_refused(self):
        for change in (dict(max_evaluations=0), dict(max_evaluations=True), dict(sa_iterations=-1),
                       dict(hc_neighbors=0), dict(temperature_end=0), dict(temperature_start=float('nan'))):
            with self.subTest(change=change), self.assertRaises(ValueError):
                SearchConfig(**dict(dict(seed=42, max_evaluations=5), **change))

    def test_invalid_grid_and_mask_refused_before_evaluation(self):
        with self.assertRaises(ValueError):
            initial_mask(dict(self.card['schedule'], actual_updates=51), self.profile)
        dense = initial_mask(self.card['schedule'], self.profile)
        with self.assertRaises(ValueError): legal_swaps(self.profile, dense[:-1])
        with self.assertRaises(ValueError): legal_swaps(self.profile, sorted(set(dense)-{24} | {30}))
        restricted = replace(self.profile, max_source_age=2)
        with self.assertRaises(ValueError): legal_swaps(restricted, dense)

    def test_changed_frozen_context_and_check_members_never_reach_evaluator(self):
        calls = []
        arguments = dict(schedule=self.card['schedule'], profile=self.profile,
            config=SearchConfig(42, 1), fit_members=self.card['FIT'], context_sha256='1'*64,
            evaluate=lambda request: calls.append(request))
        for change in (dict(fit_members=self.card['CHECK']), dict(context_sha256='unknown'),
                       dict(profile=replace(self.profile, max_source_age=27)),
                       dict(schedule=dict(self.card['schedule'], actual_updates=35))):
            with self.subTest(change=change), self.assertRaises(ValueError):
                search(**dict(arguments, **change))
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
