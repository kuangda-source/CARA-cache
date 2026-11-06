"""Whole P1 control flow with explicit synthetic media, labels and cost clock."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_source_lifecycle_p1_plan_r1 import build
from wcomr.cara_source_lifecycle_p1_collection_r1 import Collection
from test_cara_source_lifecycle_estimation_r1 import fixture_packet


class SyntheticRequests:
    def __init__(self, context, labels, scalar_seconds=100.):
        self.context, self.labels, self.scalar_seconds = context, labels, scalar_seconds
        self.clock, self.calls, self.scores, self.trace = 0., [], [], []
        self.fail_slot = self.break_control = self.half_score = None

    def execute(self, slot, output):
        self.calls.append(slot['id'])
        self.trace.append(('request', slot['member'], slot['id']))
        if self.fail_slot and self.fail_slot in slot['id']:
            raise OSError('Declared synthetic physical failure')
        output.mkdir()
        candidate = 'NATIVE35' if slot['kind'] in ('native', 'allD') else slot['candidate_id']
        token = digest(dict(candidate=candidate, member=slot['member'], seed=0))
        latent, video = output/'latent.bin', output/'fixture.mp4'
        latent.write_bytes(token.encode())
        video.write_bytes(('SYNTHETIC_UNIT_MEDIA_NOT_REAL_VIDEO_'+token).encode())
        if slot['kind'] == 'scalar':
            labels = [r for r in self.labels['rows'] if r['member'] == slot['member'] and r['parent_id'] == slot['parent_id']]
            self.clock += self.scalar_seconds
        else:
            labels = []
            self.clock += 10.
        tensor_sha = '0'*64 if self.break_control and self.break_control in slot['id'] else token
        return dict(status='COMPLETE', CPU_fixture_only=True, source_revision=self.context['source_revision'],
            launch_id=self.context['launch_id'], context_sha256=digest(self.context), member=slot['member'], seed=0,
            candidate_id='NATIVE35' if slot['kind'] == 'native' else slot['candidate_id'],
            actual_updates=36, solver_steps=36, guided_pairs=36, fallback_count=0,
            physical_model_pairs=44 if slot['kind'] == 'scalar' else 36,
            video=dict(path=str(video), sha256=file_sha(video)),
            final_latent=dict(path=str(latent), file_sha256=file_sha(latent), tensor_sha256=tensor_sha),
            pre_encode_RGB=dict(shape=[3, 93, 64, 64], dtype='float32', sha256=token),
            post_request_RNG_sha256=digest(slot['member']), scalar_labels=labels,
            timing=slot['timing'], T_DD=.01, T_request=.02)

    def score(self, packet, output):
        self.scores.append(packet['candidate_id'])
        self.trace.append(('score', 'COMPLETE_TWO_FIT', packet['candidate_id']))
        self.clock += 2.
        loss = .2+(int(packet['candidate_id'][:4], 16) % 100)/1000
        rows = [dict(candidate_id=packet['candidate_id'], member=m, status='COMPLETE', Alex_curve=[loss]*93)
                for m in packet['FIT_members']]
        if self.half_score:
            rows.pop()
        return dict(schema='CARA_V1_INTERNAL_COMPLETE_FIT_SCORES_R1',
            status='ACCEPTED_INTERNAL_CALIBRATION_ONLY', CPU_fixture_only=True,
            packet_sha256=digest(packet), rows=rows, whole_card_scientific_accepted=False)


class P1CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.labels, self.design, parent = fixture_packet()
        self.card = build(parent, self.design)
        self.context = dict(scope_sha256=self.card['scope_sha256'], host='two_card', CPU_fixture_only=True,
            source_revision='1'*40, launch_id='2'*32, admission_sha256='3'*64)

    def collection(self, name='complete', *, runtime=None, create=True):
        runtime = runtime or SyntheticRequests(self.context, self.labels)
        collection = Collection(root=self.root/name, card=self.card, context=self.context,
            weights=[1.]*36, execute=runtime.execute, score=runtime.score, elapsed_seconds=lambda: runtime.clock,
            query_bounds=dict(path_seconds=10., FIT_score_seconds=2., overhead_seconds=.1),
            cpu_validation=True, create=create)
        return collection, runtime

    def test_complete_whole_algorithm_both_budgets_and_explicit146_scope(self):
        collection, runtime = self.collection()
        result = collection.run(allow_new=True)
        self.assertNotIn('failure', result)
        self.assertEqual(result['status'], 'P1_ALGORITHM_COMPLETE_PENDING_ORIGINAL_RELEASE_SETTLEMENT_AND_SCIENCE')
        self.assertEqual(len(result['source_labels']['rows']), 64)
        self.assertEqual(len(result['FIT_selected']), 6)
        self.assertEqual(result['complete_semantic_positions'], 146)
        self.assertEqual(len({p['id'] for p in result['semantic_positions']}), 146)
        self.assertEqual(self.card['original132_path_draft_omitted_controls'], 14)
        self.assertLess(len(runtime.calls), 146)
        self.assertTrue(any(p['status'] == 'QUALITY_AND_CLEAN_SAMPLE_ALIAS' for p in result['semantic_positions']))
        for budget in ('19', '22'):
            search = result['fair_searches'][budget]
            self.assertTrue(search['configured_search_finished'])
            self.assertEqual(search['completed_queries'], 12)
            self.assertLessEqual(search['measured_charged_seconds'], search['measured_cost_cap_seconds'])
        # CHECK appears only after all18 complete FIT candidate positions and
        # six fixed selections. There are no CHECK labels or internal scores.
        first_check = next(i for i, row in enumerate(runtime.trace) if row[1] in self.card['CHECK'])
        self.assertGreater(sum(row[0] == 'score' for row in runtime.trace[:first_check]), 0)
        self.assertTrue(all(r['member'] in self.card['FIT'] for r in result['source_labels']['rows']))
        self.assertFalse(result['whole_card_scientific_accepted'])
        self.assertTrue(result['final_scoring_and_original_terminal_acceptance_pending'])

    def test_original_complete_recovery_reuses_all_physical_and_scoring_returns(self):
        collection, runtime = self.collection()
        first = collection.run(allow_new=True)
        self.assertNotIn('failure', first)
        before = len(runtime.calls), len(runtime.scores), runtime.clock
        original = (self.root/'complete/algorithm-summary.json').read_bytes()
        recovered, _ = self.collection(runtime=runtime, create=False)
        result = recovered.run()
        self.assertNotIn('failure', result)
        self.assertEqual(before, (len(runtime.calls), len(runtime.scores), runtime.clock))
        self.assertEqual(result['new_callback_calls'], 0)
        self.assertEqual(result['complete_semantic_positions'], 146)
        self.assertEqual(result['FIT_selected'], first['FIT_selected'])
        self.assertEqual((self.root/'complete/algorithm-summary.json').read_bytes(), original)

    def test_actual_cost_stop_retains_unreached_denominator_and_hc_count(self):
        runtime = SyntheticRequests(self.context, self.labels, scalar_seconds=14.)
        collection, _ = self.collection(runtime=runtime)
        result = collection.run(allow_new=True)
        self.assertNotIn('failure', result)
        self.assertEqual(len(result['semantic_positions']), 146)
        self.assertLess(result['complete_semantic_positions'], 146)
        self.assertTrue(any(p['status'] in ('BUDGET_NOT_ADMITTED', 'BUDGET_STOP_NOT_REACHED')
                            for p in result['semantic_positions']))
        self.assertTrue(any(s['termination'] == 'MEASURED_COST_ADMISSION_STOP' for s in result['fair_searches'].values()))
        for search in result['fair_searches'].values():
            if not search['configured_search_finished']:
                self.assertLess(search['HC_iterations_completed'], 1)

    def test_original_failed_request_consumes_attempt_and_cannot_be_replayed(self):
        runtime = SyntheticRequests(self.context, self.labels)
        runtime.fail_slot = 'parent-K19_SIGMA_FARTHEST-0'
        collection, _ = self.collection(runtime=runtime)
        first = collection.run(allow_new=True)
        calls = len(runtime.calls)
        self.assertIn('failure', first)
        self.assertEqual(first['semantic_positions'][-1]['status'], 'FAILED_NO_RETRY')
        runtime.fail_slot = None
        recovered, _ = self.collection(runtime=runtime, create=False)
        result = recovered.run(allow_new=True)
        self.assertIn('Original P1 failure', result['failure']['message'])
        self.assertEqual(len(runtime.calls), calls)
        self.assertNotIn('models', result)

    def test_same_state_parent_control_failure_and_half_fit_never_select(self):
        for mode in ('parent_control', 'half_FIT'):
            runtime = SyntheticRequests(self.context, self.labels)
            if mode == 'parent_control': runtime.break_control = 'control-parent-K19-0'
            else: runtime.half_score = True
            collection, _ = self.collection(mode, runtime=runtime)
            result = collection.run(allow_new=True)
            self.assertIn('failure', result)
            self.assertNotIn('FIT_selected', result)
            self.assertFalse(any(row[1] in self.card['CHECK'] for row in runtime.trace))

    def test_tampered_original_video_and_changed_quote_refuse_without_callbacks(self):
        collection, runtime = self.collection()
        result = collection.run(allow_new=True)
        self.assertNotIn('failure', result)
        calls = len(runtime.calls), len(runtime.scores)
        file = next((self.root/'complete/operations').glob('baseline-*/generation/fixture.mp4'))
        file.write_bytes(b'DECLARED_CORRUPTION_FIXTURE')
        recovered, _ = self.collection(runtime=runtime, create=False)
        result = recovered.run()
        self.assertIn('Retained original complete request changed', result['failure']['message'])
        self.assertEqual(calls, (len(runtime.calls), len(runtime.scores)))
        with self.assertRaises(ValueError):
            Collection(root=self.root/'complete', card=self.card, context=self.context, weights=[1.]*36,
                execute=runtime.execute, score=runtime.score, elapsed_seconds=lambda: runtime.clock,
                query_bounds=dict(path_seconds=11., FIT_score_seconds=2., overhead_seconds=.1),
                cpu_validation=True)


if __name__ == '__main__':
    unittest.main()
