"""Real grammar, synthetic objectives/costs, original on-disk query recovery."""
import copy
from pathlib import Path
import random
import tempfile
import unittest

from wcomr.cara_budget_search_r1 import SearchConfig, legal_swaps as original_swaps
from wcomr.cara_fast_spec_r1 import digest, policy_from_mask, profile_from, uniform_mask
from wcomr.cara_source_lifecycle_search_r1 import legal_swaps, search, run_search
from wcomr.cara_budget_search_journal_r1 import read_record
import json

ROOT = Path(__file__).resolve().parents[1]


class SourceLifecycleSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
        cls.profile = profile_from(cls.card['profile'])

    def setUp(self):
        self.config = SearchConfig(42, 6, sa_iterations=2, hc_iterations=1, hc_neighbors=3)
        self.kw = dict(fit_members=self.card['FIT'], context_sha256=digest({'explicit_CPU_fixture': True}),
                       cap_seconds=100.)

    def evaluate(self, query):
        return dict(status='COMPLETE', request_sha256=query['request_sha256'],
            cost_cap_seconds=self.kw['cap_seconds'], charged_before_seconds=5.*(query['query_id']-1),
            charged_after_seconds=5.*query['query_id'], new_physical_paths=2,
            score_packet_sha256=digest(query), rows=[dict(member=m, status='COMPLETE',
                candidate_id=query['policy']['fingerprint'], Alex_curve=[i+1.]*93)
                for i, m in enumerate(query['FIT_members'])])

    def run_component(self, budget=19, evaluate=None):
        return search(self.card['schedule'], self.profile, budget, self.config,
                      evaluate=evaluate or self.evaluate, **self.kw)

    def test_both_budgets_share_the_dp_grammar_without_extra_step24(self):
        for budget in (19, 22):
            result = self.run_component(budget)
            self.assertEqual(result['completed_queries'], 6)
            self.assertEqual(result['SA_iterations_completed'], 2)
            self.assertEqual(result['HC_iterations_completed'], 1)
            self.assertTrue(result['configured_search_finished'])
            self.assertEqual(result['best_complete_candidate']['input_equal_Alex'], 1.5)
            self.assertEqual(result['queries'][0]['dense'], uniform_mask(self.card['schedule'], self.profile, budget)[0])
            dense = result['queries'][0]['dense']
            choices = legal_swaps(self.profile, dense, budget)
            self.assertTrue(any(remove == 24 for remove, _, _ in choices))
            for _, _, mask in choices:
                self.assertEqual(policy_from_mask(self.profile, mask)['counts']['D'], budget)
                self.assertTrue(set(self.profile.protected_dense) <= set(mask))
        old = original_swaps(self.profile, uniform_mask(self.card['schedule'], self.profile, 19)[0])
        self.assertFalse(any(remove == 24 for remove, _, _ in old))

    def test_private_rng_determinism_and_complete_last_frame_objective(self):
        random.seed(872)
        state = random.getstate()
        def evaluate(query):
            result = self.evaluate(query)
            for row in result['rows']:
                row['Alex_curve'] = [0.]*92+[1./query['query_id']]
            return result
        result = self.run_component(evaluate=evaluate)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(result, self.run_component(evaluate=evaluate))
        self.assertEqual(result['best_complete_candidate']['query_id'], 6)
        self.assertAlmostEqual(result['best_complete_candidate']['input_equal_Alex'], 1./6/93)

    def test_measured_cost_stops_before_hc_without_claiming_it_completed(self):
        def evaluate(query):
            result = self.evaluate(query)
            if query['query_id'] == 3:
                result.update(status='NOT_ADMITTED', rows=[], new_physical_paths=0)
            return result
        result = self.run_component(evaluate=evaluate)
        self.assertEqual(result['termination'], 'MEASURED_COST_ADMISSION_STOP')
        self.assertEqual(result['completed_queries'], 2)
        self.assertEqual(result['HC_iterations_completed'], 0)
        self.assertFalse(result['configured_search_finished'])
        self.assertEqual(result['queries'][-1]['status'], 'NOT_ADMITTED')

    def test_failed_partial_wrong_identity_overcap_and_nonfinite_queries_never_retry(self):
        for fault in ('missing', 'duplicate', 'last_frame', 'candidate', 'request', 'over_cap', 'clock_backwards', 'exception'):
            calls = []
            def evaluate(query):
                calls.append(query['query_id'])
                result = self.evaluate(query)
                if query['query_id'] == 2:
                    if fault == 'missing': result['rows'].pop()
                    elif fault == 'duplicate': result['rows'][1] = copy.deepcopy(result['rows'][0])
                    elif fault == 'last_frame': result['rows'][0]['Alex_curve'][-1] = float('nan')
                    elif fault == 'candidate': result['rows'][0]['candidate_id'] = '0'*64
                    elif fault == 'request': result['request_sha256'] = '0'*64
                    elif fault == 'over_cap': result['charged_after_seconds'] = 101.
                    elif fault == 'clock_backwards': result['charged_before_seconds'] = 4.
                    elif fault == 'exception': raise OSError('original CPU fixture failure')
                return result
            with self.subTest(fault=fault):
                result = self.run_component(evaluate=evaluate)
                self.assertEqual(calls, [1, 2])
                self.assertEqual(result['termination'], 'ORIGINAL_QUERY_FAILED_NO_RETRY')
                self.assertEqual(result['completed_queries'], 1)
                self.assertFalse(result['scientific_freeze_written'])

    def test_complete_journal_recovery_invokes_no_evaluator_or_new_physical_request(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'search'
            first = run_search(path, self.card['schedule'], self.profile, 22, self.config,
                evaluate=self.evaluate, create=True, allow_new_queries=True, **self.kw)
            recovered = run_search(path, self.card['schedule'], self.profile, 22, self.config,
                evaluate=lambda q: self.fail('Original evaluator must not run again'), **self.kw)
            self.assertEqual(first['queries'], recovered['queries'])
            self.assertEqual(recovered['journal']['new_callback_calls'], 0)
            self.assertEqual(recovered['journal']['reused_callback_returns'], 6)
            with self.assertRaises(ValueError):
                run_search(path, self.card['schedule'], self.profile, 19, self.config,
                    evaluate=self.evaluate, **self.kw)

    def test_unknown_original_query_and_recorded_failure_are_preserved(self):
        for unknown in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'search'
                calls = []
                def evaluate(query):
                    calls.append(query['query_id'])
                    if query['query_id'] == 2:
                        if unknown: raise SystemExit('Original callback lost before durable return')
                        raise OSError('Original callback returned a failure')
                    return self.evaluate(query)
                if unknown:
                    with self.assertRaises(SystemExit):
                        run_search(path, self.card['schedule'], self.profile, 19, self.config,
                            evaluate=evaluate, create=True, allow_new_queries=True, **self.kw)
                else:
                    run_search(path, self.card['schedule'], self.profile, 19, self.config,
                        evaluate=evaluate, create=True, allow_new_queries=True, **self.kw)
                recovered = run_search(path, self.card['schedule'], self.profile, 19, self.config,
                    evaluate=lambda q: self.fail('Never repeat unresolved or failed callback'), **self.kw)
                self.assertEqual(calls, [1, 2])
                self.assertEqual(recovered['completed_queries'], 1)
                self.assertEqual(recovered['queries'][-1]['status'], 'UNKNOWN' if unknown else 'FAILED')
                self.assertTrue((path/'query-000002.intent.json').exists())
                self.assertEqual((path/'query-000002.return.json').exists(), not unknown)

    def test_bound_search_requires_complete_sa_hc_scope_and_exact_fit(self):
        bad = dict(self.kw, fit_members=['human_199', 'EXPOSED_CHECK'])
        with self.assertRaises(ValueError):
            search(self.card['schedule'], self.profile, 19, self.config, evaluate=self.evaluate, **bad)
        with self.assertRaises(ValueError):
            search(self.card['schedule'], self.profile, 19, SearchConfig(42, 1),
                   evaluate=self.evaluate, **self.kw)


if __name__ == '__main__':
    unittest.main()
