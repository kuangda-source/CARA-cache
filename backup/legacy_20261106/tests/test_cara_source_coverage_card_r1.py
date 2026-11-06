"""C1 complete callback pipeline, cost isolation and unchanged default routes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_source_coverage_card_r1 import build,quote,validate
from wcomr.cara_source_coverage_collection_r1 import CoverageCollection
from test_cara_source_lifecycle_p1_collection_r1 import SyntheticRequests


ROOT = Path(__file__).resolve().parents[1]
METRICS = {}


def card_fixture():
    read = lambda p:json.loads((ROOT/p).read_text())
    return build(read('plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'),
        read('plans/cara_next_stage_20261103/source_coverage/CPU_CANDIDATE_POOLS_R4.json'))


class CoverageCard(unittest.TestCase):
    def setUp(self):
        self.card = card_fixture()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'collection'
        self.context = dict(scope_sha256=self.card['scope_sha256'],host='two_card',CPU_fixture_only=True,
            source_revision='1'*40,launch_id='2'*32,admission_sha256='3'*64)
        self.runtime = SyntheticRequests(self.context,dict(rows=[]))

    def collection(self, create=True):
        return CoverageCollection(root=self.root,card=self.card,context=self.context,weights=[1.]*36,
            execute=self.runtime.execute,score=self.runtime.score,elapsed_seconds=lambda:self.runtime.clock,
            query_bounds=dict(path_seconds=10.,FIT_score_seconds=2.,overhead_seconds=.1),
            cpu_validation=True,create=create)

    def test_matched_quotas_subsets_exact_budget_and_full_denominators(self):
        validate(self.card)
        self.assertEqual(sum(self.card['scientific_positions'].values()),166)
        for budget in (19,22):
            main = self.card['views'][f'main8-K{budget}']
            main_ids = {c['candidate_id'] for c in main['candidates']}
            for mode in ('main8','single8','neutral3','phase3'):
                view = self.card['views'][f'{mode}-K{budget}']
                self.assertEqual(len(view['candidates']),8 if mode.endswith('8') else 3)
                for c in view['candidates']:
                    self.assertEqual(c['policy']['counts']['D'],budget)
                    if mode.endswith('3'):
                        self.assertIn(c['candidate_id'],main_ids)

    def test_complete166_pipeline_search_isolation_selection_and_recovery(self):
        result = self.collection().run(allow_new=True)
        self.assertNotIn('failure',result,result.get('failure'))
        self.assertEqual(len(result['semantic_positions']),166)
        self.assertEqual(len(result['FIT_selected']),8)
        self.assertEqual(result['source_labels_collected'],0)
        self.assertEqual(result['scientific_quality_positions'],60)
        self.assertFalse(result['search_cross_method_cache_credit'])
        for budget, search in result['fair_searches'].items():
            self.assertEqual(search['queries'][0]['new_physical_paths'],2)
            self.assertLessEqual(search['measured_charged_seconds'],result['main8_cost_caps_seconds'][budget])
            self.assertIn(search['termination'],('CONFIGURED_SA_HC_FINISHED','MEASURED_COST_ADMISSION_STOP'))
        calls, scores, clock = len(self.runtime.calls),len(self.runtime.scores),self.runtime.clock
        summary = (self.root/'algorithm-summary.json').read_bytes()
        recovery = self.collection(create=False).run(allow_new=False)
        self.assertNotIn('failure',recovery,recovery.get('failure'))
        self.assertEqual(recovery['FIT_selected'],result['FIT_selected'])
        self.assertEqual(recovery['new_callback_calls'],0)
        self.assertEqual(len(recovery['semantic_positions']),166)
        self.assertEqual((len(self.runtime.calls),len(self.runtime.scores),self.runtime.clock),(calls,scores,clock))
        self.assertEqual((self.root/'algorithm-summary.json').read_bytes(),summary)
        METRICS['whole_pipeline'] = dict(semantic_positions=166,selected_views=8,
            synthetic_physical_callbacks=calls,synthetic_score_callbacks=scores,
            recovery_callbacks=0,search_first_query_new_paths_per_budget=2,
            actual_video_metric_pairs=0)

    def test_partial_fit_failure_is_retained_and_not_retried(self):
        self.runtime.half_score = True
        result = self.collection().run(allow_new=True)
        self.assertIn('failure',result)
        self.assertNotIn('FIT_selected',result)
        counts = len(self.runtime.calls),len(self.runtime.scores)
        recovery = self.collection(create=False).run(allow_new=False)
        self.assertIn('failure',recovery)
        self.assertEqual((len(self.runtime.calls),len(self.runtime.scores)),counts)

    def test_control_mismatch_precedes_any_candidate_score(self):
        self.runtime.break_control = 'control-allD'
        result = self.collection().run(allow_new=True)
        self.assertIn('failure',result)
        self.assertEqual(self.runtime.scores,[])

    def test_independent_uniform_search_bridge_must_match_baseline(self):
        self.runtime.break_control = 'search-K19-q1'
        result = self.collection().run(allow_new=True)
        self.assertIn('failure',result)
        self.assertNotIn('FIT_selected',result)

    def test_unresolved_intent_cannot_generate_a_second_request(self):
        self.root.mkdir()
        # Start a normal collector, then simulate the original process dying
        # between its durable intent and return. Recovery must not call execute.
        self.root.rmdir()
        self.collection().run(allow_new=True)
        target = next((self.root/'operations').glob('warm-Native/return.json'))
        target.unlink()
        calls = len(self.runtime.calls)
        result = self.collection(create=False).run(allow_new=False)
        self.assertIn('failure',result)
        self.assertEqual(len(self.runtime.calls),calls)

    def test_card_mutation_and_cross_method_credit_are_rejected(self):
        for key,value in (('physical_paths_upper',160),('search_cache','SHARED_WITH_MAIN')):
            card = copy.deepcopy(self.card)
            card[key] = value
            card['scope_sha256'] = digest({k:v for k,v in card.items() if k != 'scope_sha256'})
            with self.assertRaises(ValueError):
                validate(card)

    def test_existing_request_boundary_accepts_c1_only_with_explicit_validator(self):
        from typing import Optional,List,Tuple,Union
        from test_cara_read_write_transition_r1 import fixture,RUNTIME
        from wcomr.cara_source_lifecycle_p1_requests_r1 import Requests
        _,wc,_,_,_ = fixture()
        vars(wc).update(Optional=Optional,List=List,Tuple=Tuple,Union=Union)
        kwargs = dict(inference=SimpleNamespace(pipe=SimpleNamespace(_get_data_batch_input=lambda:None)),
            samples={},card=self.card,common=dict(runtime=RUNTIME,wc=wc),context=self.context,
            before_request=lambda slot:None,snapshot_limits={},cpu_validation=True)
        with self.assertRaises(ValueError):
            Requests(**kwargs)
        requests = Requests(**kwargs,card_validator=validate)
        self.assertEqual(requests.profile.horizon,36)
        self.assertEqual(set(requests.replay),set(self.card['FIT']+self.card['CHECK']))

    def test_quote_covers_every_path_internal_cpu_and_release_without_live_ledger(self):
        read=lambda p:json.loads((ROOT/p).read_text())
        result = quote(self.card,read('reports/cara_v1_P1_successor_original_algorithm_summary_r1_20261103.json'),
            read('reports/cara_v1_P1_successor_original_complete_analysis_r1_20261103.json'))
        self.assertGreater(result['components_seconds']['internal_CPU_held_allocation'],0)
        self.assertEqual(result['components_seconds']['stop_release_reserve'],600)
        self.assertLess(result['forecast_GPUh'],result['proposed_hard_GPUh'])
        self.assertFalse(result['GPU_authorized'])
        self.assertFalse(result['live_funds_verified'])


if __name__ == '__main__':
    unittest.main()
