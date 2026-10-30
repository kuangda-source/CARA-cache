"""Private-path and disk refusal controls; no format, mount or allocation."""
from contextlib import ExitStack
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import provision_cara_budget_two_storage_r1 as operator
import cara_budget_storage_two_transport_r1 as transport


class StorageProvisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root/'images/private'
        self.output = self.root/'outputs/private'
        self.journal = self.root/'controls/private'
        for p in (self.base.parent, self.output.parent, self.journal.parent):
            p.mkdir()

    def check(self, data_free=100*2**30, journal_free=4*2**30, same_device=False):
        original_stat = Path.stat
        original_read = Path.read_text

        def stat(path, *args, **kwargs):
            value = original_stat(path, *args, **kwargs)
            if path == self.journal.parent and not same_device:
                values = list(value)
                values[2] += 1
                return os.stat_result(values)
            return value

        def read(path, *args, **kwargs):
            if str(path) == '/proc/meminfo':
                return 'MemAvailable: 8388608 kB\n'
            return original_read(path, *args, **kwargs)

        with ExitStack() as stack:
            for name, value in [('ROOT', self.root), ('BASE', self.base),
                                ('OUTPUT', self.output), ('JOURNAL_DIR', self.journal)]:
                stack.enter_context(patch.object(operator, name, value))
            stack.enter_context(patch.object(Path, 'stat', stat))
            stack.enter_context(patch.object(Path, 'read_text', read))
            stack.enter_context(patch.object(shutil, 'disk_usage', side_effect=lambda p:
                shutil._ntuple_diskusage(200*2**30, 0, journal_free if p == self.journal.parent else data_free)))
            return operator.preflight()

    def test_complete_fresh_private_geometry_can_pass(self):
        result = self.check()
        self.assertNotEqual(result['data_device'], result['journal_device'])
        self.assertEqual(result['MemAvailable_bytes'], 8*2**30)
        self.assertFalse(self.base.exists())

    def test_deployed_worker_name_does_not_shadow_standard_library(self):
        filename = 'budget_storage_worker.py'
        self.assertIn("operator=control/'"+filename+"'", transport.REMOTE)
        source = Path(operator.__file__).read_text()
        marker = "if __name__ == '__main__':\n    main()"
        self.assertEqual(source.count(marker), 1)
        # Run all real top-level imports from the actual deployment basename,
        # without entering the host-only formatting or mounting routine.
        deployed = self.root/filename
        deployed.write_text(source.replace(marker, "print('IMPORTS_OK')"))
        result = subprocess.run([sys.executable, str(deployed)], text=True,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'IMPORTS_OK')

    def test_existing_target_is_preserved_and_refused(self):
        self.base.mkdir()
        evidence = self.base/'original.txt'
        evidence.write_text('Keep original')
        with self.assertRaises(AssertionError):
            self.check()
        self.assertEqual(evidence.read_text(), 'Keep original')

    def test_symlinked_parent_is_refused(self):
        self.journal.parent.rmdir()
        self.journal.parent.symlink_to(self.output.parent, target_is_directory=True)
        with self.assertRaises(AssertionError):
            self.check()

    def test_same_filesystem_journal_is_refused(self):
        with self.assertRaises(AssertionError):
            self.check(same_device=True)

    def test_insufficient_disk_margin_is_refused(self):
        for args in (dict(data_free=79*2**30), dict(journal_free=2**30)):
            with self.subTest(args=args), self.assertRaises(AssertionError):
                self.check(**args)
        self.assertFalse(self.base.exists())
        self.assertFalse(self.output.exists())
        self.assertFalse(self.journal.exists())


if __name__ == '__main__':
    unittest.main()
