"""Deterministic producer/consumer publication and isolated RPC regressions."""
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

import cara_source_lifecycle_p1_control_r1 as control
from wcomr import cara_source_lifecycle_fit_broker_r1 as broker
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_budget_search_journal_r1 import OriginalQueryUnknown, create_record, read_record
import test_cara_source_lifecycle_fit_broker_r1 as fixtures


class QueryPublicationTests(unittest.TestCase):
    def setUp(self):
        fixtures.FitBrokerTests.setUp(self)
        if sys.platform != 'linux':
            for name, value in (('bind_original_process', dict(unit_role='LOCAL_MAC_CPU_FIXTURE')),
                                ('observe_original_process', dict(original_live=True))):
                mocked = patch.object(broker, name, return_value=value)
                mocked.start()
                self.addCleanup(mocked.stop)

    def test_live_consumer_cannot_see_query_until_complete_publication(self):
        paused, resume, scanned = threading.Event(), threading.Event(), threading.Event()
        results, failures = [], []
        client = broker.Client(self.spec)
        test_deadline = time.monotonic()+8
        original_create, original_sleep = broker.create_record, time.sleep
        main_thread = threading.get_ident()
        worker = None

        def write(path, value):
            if path.name == 'request.json':
                paused.set()
                if not resume.wait(5):
                    raise TimeoutError('CPU producer was not resumed')
            return original_create(path, value)

        def produce():
            try:
                results.append(client(self.packet, None))
            except BaseException as error:
                failures.append(error)

        def clock():
            nonlocal worker
            if time.monotonic() >= test_deadline:
                raise TimeoutError('CPU interleaving exceeded its bound')
            if (Path(self.spec['queue'])/'service-start.json').exists() and worker is None:
                worker = threading.Thread(target=produce, daemon=True)
                worker.start()
                self.assertTrue(paused.wait(3))
                self.assertEqual(list(Path(self.spec['queue']).glob('score-*')), [])
            return 0.

        def sleep(seconds):
            if threading.get_ident() == main_thread:
                self.assertEqual(seconds, 1.)
                if not resume.is_set():
                    scanned.set()
                    resume.set()
            original_sleep(.005)

        def dispatch(candidate):
            self.assertTrue(scanned.is_set())
            self.assertEqual(candidate, self.candidate)
            self.assertEqual(read_record(self.query/'request.json'), self.config)
            payload = dict(CPU_fixture_only=True, complete_pair_count=2)
            original_create(self.query/'response.json', dict(status='ACCEPTED_INTERNAL',
                config_sha256=digest(self.config), payload=payload, payload_sha256=digest(payload)))
            original_create(Path(self.spec['queue'])/'stop-request.json',
                            dict(context_sha256=digest(self.spec['context'])))
            return dict(status='ORIGINAL_COMPLETE_FIT_ACCEPTED')

        try:
            with patch.object(broker, 'create_record', side_effect=write), \
                    patch.object(broker.time, 'sleep', side_effect=sleep), \
                    patch.object(broker.Host, 'dispatch_query', side_effect=dispatch) as called, \
                    patch.object(broker.subprocess, 'Popen') as spawn:
                broker.Host(self.spec, clock).serve()
                worker.join(3)
                self.assertFalse(worker.is_alive())
                self.assertEqual(failures, [])
                self.assertEqual(results, [dict(CPU_fixture_only=True, complete_pair_count=2)])
                called.assert_called_once_with(self.candidate)
                spawn.assert_not_called()
        finally:
            resume.set()
            client.spec['work_stop_monotonic'] = time.monotonic()-1
            if worker is not None:
                worker.join(9)
        self.assertIsNone(read_record(Path(self.spec['queue'])/'service-terminal.json')['error'])

    def test_interrupted_hidden_publication_is_retained_and_not_retried(self):
        client = broker.Client(self.spec)
        with patch.object(broker, 'create_record', side_effect=OSError('CPU forced publication interruption')):
            with self.assertRaisesRegex(OSError, 'forced publication'):
                client(self.packet, None)
        self.assertFalse(self.query.exists())
        pending = self.query.with_name('.pending-'+self.query.name)
        self.assertTrue(pending.is_dir())
        inode = pending.stat().st_ino
        with patch.object(broker.subprocess, 'Popen') as spawn:
            with self.assertRaises(OriginalQueryUnknown):
                client(self.packet, None)
            spawn.assert_not_called()
        self.assertEqual(pending.stat().st_ino, inode)
        self.assertFalse(self.query.exists())

    def test_visible_torn_original_still_refuses_without_dispatch(self):
        self.query.mkdir()
        inode = self.query.stat().st_ino
        with patch.object(broker.Host, 'dispatch_query') as dispatch:
            with self.assertRaisesRegex(OriginalQueryUnknown, 'Torn original'):
                broker.Host(self.spec, lambda: 0.).serve()
            dispatch.assert_not_called()
        with self.assertRaises((ValueError, OriginalQueryUnknown)):
            broker.Client(self.spec)(self.packet, None)
        self.assertEqual(self.query.stat().st_ino, inode)
        self.assertEqual(list(self.query.iterdir()), [])

    def test_changed_existing_request_cannot_be_replaced(self):
        self.query.mkdir()
        changed = copy.deepcopy(self.config)
        changed['foreign_request'] = True
        create_record(self.query/'request.json', changed)
        original = (self.query/'request.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'cannot be replaced'):
            broker.Client(self.spec)(self.packet, None)
        self.assertEqual((self.query/'request.json').read_bytes(), original)

    def test_whole42_query_limit_refuses_before_new_publication(self):
        queue = Path(self.spec['queue'])
        for i in range(42):
            (queue/('score-'+str(i).zfill(64))).mkdir()
        with self.assertRaisesRegex(ValueError, 'maximum42'):
            broker.Client(self.spec)(self.packet, None)
        self.assertFalse(self.query.exists())
        self.assertFalse(self.query.with_name('.pending-'+self.query.name).exists())


class RPCEnvelopeTests(unittest.TestCase):
    def run_remote(self, remote):
        code = 'packet={"arguments":{"marker":"ORIGINAL"}}\n'+control.wrapped_rpc_code(remote)
        return subprocess.run([sys.executable, '-I', '-c', code],
                              capture_output=True, text=True, timeout=5)

    def decoded(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json.loads(result.stdout)
        raw = gzip.decompress(base64.b64decode(envelope['gzip_base64']))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), envelope['sha256'])
        return json.loads(raw)

    def test_original_receipt_variable_names_do_not_replace_stdout(self):
        result = self.run_remote("import json;saved={'job':'same-original'};raw='remote';print(json.dumps(dict(marker=packet['arguments']['marker'],receipt=saved)))")
        self.assertEqual(self.decoded(result), dict(marker='ORIGINAL', receipt=dict(job='same-original')))

    def test_rpc_wraps_normal_json_with_its_exact_digest(self):
        self.assertEqual(self.decoded(self.run_remote("import json;print(json.dumps(dict(ledger_written=False)))")),
                         dict(ledger_written=False))

    def test_remote_error_remains_a_failure_without_a_success_envelope(self):
        result = self.run_remote("saved={};raise ValueError('CPU original failure')")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('CPU original failure', result.stderr)


if __name__ == '__main__':
    unittest.main()
