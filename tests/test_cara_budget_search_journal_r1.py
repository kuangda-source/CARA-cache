"""Real local filesystem/process interruption, synthetic evaluation only."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from wcomr import cara_budget_search_journal_r1 as journal
from wcomr.cara_budget_search_r1 import SearchConfig
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import profile_from

ROOT = Path(__file__).resolve().parents[1]


def flat(request):
    return dict(request_sha256=request['request_sha256'], rows=[
        dict(member=m, status='COMPLETE', RGB_MSE=1.0) for m in request['FIT_members']])


class SearchJournalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)/'queries'
        self.card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
        self.arguments = dict(schedule=self.card['schedule'], profile=profile_from(self.card['profile']),
            config=SearchConfig(42, 4), fit_members=self.card['FIT'], context_sha256='1'*64)

    def run_component(self, **options):
        return journal.run_search(self.directory, **{**self.arguments, 'evaluate':flat, **options})

    def test_completed_returns_replay_without_model_or_cap_reset(self):
        first = self.run_component(create=True, allow_new_queries=True)
        calls = []
        second = self.run_component(evaluate=lambda request: calls.append(request))
        self.assertEqual(calls, [])
        self.assertEqual(first['queries'], second['queries'])
        self.assertEqual(second['termination'], 'QUERY_CAP_REACHED')
        self.assertEqual(second['journal']['persisted_intents'], 4)
        self.assertEqual(second['journal']['new_callback_calls'], 0)
        self.assertEqual(second['journal']['reused_callback_returns'], 4)

    def test_readonly_recovery_never_creates_new_intent(self):
        result = self.run_component(create=True)
        self.assertEqual(result['termination'], 'NEW_QUERY_NOT_ADMITTED')
        self.assertEqual(result['queries'][0]['status'], 'NOT_ADMITTED')
        self.assertEqual(result['journal']['persisted_intents'], 0)
        self.assertEqual(list(self.directory.glob('query-*')), [])

    def test_crash_after_one_return_reuses_it_and_only_admits_new_tail(self):
        original_create = journal.create_record
        def stop_before_second_intent(path, value):
            if path.name == 'query-000002.intent.json':
                raise KeyboardInterrupt('Declared CPU interruption before intent')
            original_create(path, value)
        with patch.object(journal, 'create_record', stop_before_second_intent), self.assertRaises(KeyboardInterrupt):
            self.run_component(create=True, allow_new_queries=True)
        readonly = self.run_component()
        self.assertEqual(readonly['termination'], 'NEW_QUERY_NOT_ADMITTED')
        self.assertEqual(readonly['journal']['persisted_intents'], 1)
        calls = []
        def evaluate(request):
            calls.append(request['query_id'])
            return flat(request)
        resumed = self.run_component(allow_new_queries=True, evaluate=evaluate)
        self.assertEqual(calls, [2,3,4])
        self.assertEqual(resumed['journal']['reused_callback_returns'], 1)

    def test_actual_process_exit_after_intent_remains_unknown_without_retry(self):
        program = '''
import os, sys
from pathlib import Path
from wcomr.cara_budget_search_journal_r1 import run_search
from wcomr.cara_budget_search_r1 import SearchConfig
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import profile_from
c=load_card(Path.cwd(),'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
run_search(sys.argv[1],c['schedule'],profile_from(c['profile']),SearchConfig(42,4),
    fit_members=c['FIT'],context_sha256='1'*64,create=True,allow_new_queries=True,
    evaluate=lambda request:os._exit(17))
'''
        child = subprocess.run([sys.executable, '-c', program, str(self.directory)], cwd=ROOT,
            env=dict(os.environ, PYTHONPATH=str(ROOT/'src')), capture_output=True, text=True, timeout=15)
        self.assertEqual(child.returncode, 17, child.stderr)
        calls = []
        recovered = self.run_component(allow_new_queries=True, evaluate=lambda request: calls.append(request))
        self.assertEqual(calls, [])
        self.assertEqual(recovered['termination'], 'ORIGINAL_QUERY_UNKNOWN_NO_DISPATCH')
        self.assertEqual(recovered['queries'][0]['status'], 'UNKNOWN')
        self.assertEqual(recovered['journal']['persisted_intents'], 1)
        self.assertIsNone(recovered['best_complete_candidate'])

    def test_callback_exception_is_preserved_and_never_retried(self):
        def fail(request):
            raise OSError('Declared evaluation exception; no physical terminal claim')
        first = self.run_component(create=True, allow_new_queries=True, evaluate=fail)
        calls = []
        second = self.run_component(allow_new_queries=True, evaluate=lambda request: calls.append(request))
        self.assertEqual(calls, [])
        self.assertEqual(first['journal']['original_callback_error'], second['journal']['original_callback_error'])
        self.assertEqual(second['termination'], 'EVALUATION_FAILED_NO_RETRY')
        self.assertFalse(second['journal']['physical_terminal_verified'])

    def test_return_serialization_failure_is_recorded_once(self):
        def nonfinite(request):
            response = flat(request)
            response['rows'][0]['RGB_MSE'] = float('nan')
            return response
        first = self.run_component(create=True, allow_new_queries=True, evaluate=nonfinite)
        self.assertEqual(first['termination'], 'EVALUATION_FAILED_NO_RETRY')
        result = self.run_component(allow_new_queries=True)
        self.assertEqual(result['journal']['new_callback_calls'], 0)
        self.assertEqual(result['journal']['persisted_intents'], 1)

    def test_invalid_return_is_replayed_as_original_invalid_value_not_repaired(self):
        def wrong_identity(request):
            response = flat(request)
            response['request_sha256'] = '0'*64
            return response
        first = self.run_component(create=True, allow_new_queries=True, evaluate=wrong_identity)
        second = self.run_component(allow_new_queries=True)
        self.assertEqual(first['queries'], second['queries'])
        self.assertEqual(second['termination'], 'EVALUATION_FAILED_NO_RETRY')
        self.assertEqual(second['journal']['new_callback_calls'], 0)

    def test_changed_binding_refused_before_callback(self):
        self.run_component(create=True, allow_new_queries=True)
        for key, value in [('context_sha256','2'*64), ('config',SearchConfig(43,4)),
                           ('config',SearchConfig(42,5))]:
            arguments = dict(self.arguments, **{key:value})
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, 'binding'):
                journal.run_search(self.directory, **arguments, evaluate=flat, allow_new_queries=True)

    def test_torn_return_and_changed_payload_refuse_without_callback(self):
        self.run_component(create=True, allow_new_queries=True)
        path = self.directory/'query-000001.return.json'
        original = path.read_bytes()
        for raw in (b'{', original.replace(b'1.0', b'2.0')):
            path.write_bytes(raw)
            with self.subTest(raw=raw[:20]), self.assertRaises(ValueError):
                self.run_component(allow_new_queries=True)
        path.write_bytes(original)

    def test_missing_middle_intent_and_orphan_return_refuse(self):
        self.run_component(create=True, allow_new_queries=True)
        path = self.directory/'query-000002.intent.json'
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'sequence gap'):
            self.run_component(allow_new_queries=True)
        path.write_bytes(original)
        (self.directory/'query-000004.intent.json').unlink()
        with self.assertRaisesRegex(ValueError, 'without its original intent'):
            self.run_component(allow_new_queries=True)

    def test_failed_intent_write_never_calls_evaluator(self):
        original_create = journal.create_record
        calls = []
        def disk_full(path, value):
            if path.name.endswith('.intent.json'):
                path.write_bytes(b'{')  # Interrupted write is retained, never silently removed.
                raise OSError(28, 'Declared partial intent write')
            original_create(path, value)
        with patch.object(journal, 'create_record', disk_full):
            result = self.run_component(create=True, allow_new_queries=True,
                evaluate=lambda request: calls.append(request))
        self.assertEqual(calls, [])
        self.assertEqual(result['journal']['new_callback_calls'], 0)
        with self.assertRaises(ValueError):
            self.run_component(allow_new_queries=True)

    def test_return_write_failure_leaves_unknown_intent(self):
        original_create = journal.create_record
        def disk_full(path, value):
            if path.name.endswith('.return.json'):
                raise OSError(28, 'Declared disk-full CPU control')
            original_create(path, value)
        with patch.object(journal, 'create_record', disk_full):
            result = self.run_component(create=True, allow_new_queries=True)
        self.assertEqual(result['journal']['new_callback_calls'], 1)
        recovered = self.run_component(allow_new_queries=True)
        self.assertEqual(recovered['termination'], 'ORIGINAL_QUERY_UNKNOWN_NO_DISPATCH')
        self.assertEqual(recovered['journal']['new_callback_calls'], 0)

    def test_second_controller_cannot_enter_original_lock(self):
        self.run_component(create=True)
        binding = json.loads((self.directory/'binding.json').read_text())
        with journal.QueryJournal(self.directory, binding):
            with self.assertRaises(BlockingIOError):
                self.run_component(allow_new_queries=True)

    def test_create_never_replaces_existing_journal(self):
        self.run_component(create=True)
        original = (self.directory/'binding.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_component(create=True, allow_new_queries=True)
        self.assertEqual((self.directory/'binding.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
