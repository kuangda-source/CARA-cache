"""Real Linux Popen/pipe/publication; temporary metadata, no GPU admission."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import test_cara_budget_dispatch_r1 as fixtures
from wcomr import cara_budget_dispatch_r1 as dispatch
from wcomr.cara_budget_original_handles_r1 import observe_original_process
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.gpu_budget_pool_v2 import sha
from wcomr.history104_storage_r2 import FixedJournal

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = []


@unittest.skipUnless(Path('/proc/self').exists(), 'Actual Linux PID/start ticks required')
class DispatchChildTests(unittest.TestCase):
    write = fixtures.DispatchTests.write
    write_all = fixtures.DispatchTests.write_all
    refresh = fixtures.DispatchTests.refresh

    def setUp(self):
        fixtures.DispatchTests.setUp(self)
        self.auth['host'] = self.launch['host'] = self.reg['host'] = self.proof['host'] = 'two_card'
        self.refresh()
        # The real child imports the unchanged production entry and modules.
        for folder in ('src', 'scripts'):
            shutil.copytree(ROOT/folder, self.stage/folder, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__'))
        self.shim = self.project/'CPU-child-imports'
        self.shim.mkdir()
        (self.stage/'CPU-dispatch-fixture').write_text('TEMPORARY_CPU_ONLY\n')
        (self.shim/'sitecustomize.py').write_text(
            'import os\ntry:\n'
            ' from check_cara_budget_dispatch_child_fixture_r1 import install\n'
            ' install()\nexcept BaseException:\n'
            ' import traceback\n traceback.print_exc()\n os._exit(72)\n')
        self.write('CPU-storage.json', self.storage.config)
        self.storage.journal.path.parent.mkdir(parents=True, exist_ok=True)
        FixedJournal(self.storage.journal.path).create()
        self.env = dict(CARA_DISPATCH_CPU_STAGE=str(self.stage),
            PYTHONPATH=os.pathsep.join(map(str, [self.shim, self.stage/'src', self.stage/'scripts', ROOT/'tests'])),
            CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void')

    def test_actual_child_pipe_publication_terminal_and_no_replay(self):
        original_sources = {n: sha(self.stage/n) for n in dispatch.REQUIRED}
        with patch.dict(os.environ, self.env), patch.object(dispatch, 'fresh_resources',
                return_value=(self.storage, {'CPU_metadata_fixture': True})):
            # No Popen or identity mock: production dispatch starts the exact entry.
            result = dispatch.dispatch(self.project, self.stage, self.snapshot, 'CPU-ONLY-NO-CREDENTIAL')
        handle = result['guardian_identity']
        try:
            until = time.monotonic()+30
            while True:
                pid, status = os.waitpid(handle['pid'], os.WNOHANG)
                if pid:
                    code = os.waitstatus_to_exitcode(status)
                    break
                if time.monotonic() >= until:
                    self.fail('Original CPU child did not exit: '+(self.stage/'host-guardian.log').read_text()[-2000:])
                time.sleep(.02)
        finally:
            if observe_original_process(handle)['original_live'] is True:
                # Signal only this test's still-bound original child.
                os.kill(handle['pid'], 15)
                os.waitpid(handle['pid'], 0)
        log = (self.stage/'host-guardian.log').read_text()
        self.assertEqual(code, 1, log)
        launch = read_record(self.stage/'GPU-launch.json')
        self.assertEqual(launch['guardian_identity'], handle)
        self.assertNotEqual(handle['pid'], os.getpid())
        self.assertFalse(observe_original_process(handle)['original_live'])
        self.assertTrue(read_record(self.stage/'CPU-credential-received.json')['synthetic_credential_received'])
        guardian = read_record(self.stage/'guardian.json')
        bill = read_record(self.stage/'billing.json')
        self.assertEqual(guardian['status'], 'BUDGET_CALIBRATION_GUARDIAN_TERMINAL')
        self.assertIn('credential delivery failed', guardian['error'])
        self.assertFalse(any(guardian['allocation_attempts'].values()))
        self.assertTrue(bill['wall_interval_complete'])
        self.assertGreater(bill['wall_seconds'], 0)
        self.assertEqual(bill['actual_GPUh'], bill['wall_seconds']/3600)
        self.assertEqual(guardian['billing_sha256'], sha(self.stage/'billing.json'))
        self.assertEqual(FixedJournal(self.storage.journal.path).read('billing'), bill)
        self.assertFalse((self.stage/'container.cid').exists())
        self.assertFalse((self.stage/'container-cli.log').exists())
        originals = {name: sha(self.stage/name) for name in
            ('GPU-intent.json', 'GPU-dispatch.json', 'GPU-launch.json', 'guardian.json', 'billing.json')}
        for name in originals:
            self.assertNotIn('CPU-ONLY-NO-CREDENTIAL', (self.stage/name).read_text())
        with patch.object(dispatch, 'ready_inputs', side_effect=AssertionError('Must recover first')), \
             patch.object(dispatch.subprocess, 'Popen', side_effect=AssertionError('No second child')):
            recovered = dispatch.dispatch(self.project, self.stage, {}, None)
        self.assertFalse(recovered['authorizes_retry'])
        self.assertFalse(recovered['guardian_observation']['original_live'])
        self.assertEqual(originals, {n: sha(self.stage/n) for n in originals})
        self.assertEqual(original_sources, {n: sha(self.stage/n) for n in original_sources})
        OBSERVATIONS.append(dict(original_identity=handle, child_exit_code=code,
            exact_guardian_entry=True, real_Popen_and_private_pipe=True,
            guardian_launch_identity_equal=True, original_child_ended=True,
            original_failure_journal_and_bill_complete=True, no_allocation_attempted=True,
            no_replay=True, sources_unchanged=True, synthetic_metadata_only=True,
            actual_GPU_resources_exercised=False, actual_GPUh=0, ledger_written=False))


if __name__ == '__main__':
    unittest.main()
