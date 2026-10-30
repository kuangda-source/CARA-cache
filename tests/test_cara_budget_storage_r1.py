import os
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_budget_storage_r1 import StorageLimits,tree_usage,check_scope,generation_snapshot
import test_cara_budget_calibration_r1 as calibration_tests


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.limits=StorageLimits(4*2**20,2**16,2**16,2**16,2**16,2**16)

    def test_incomplete_files_count_and_scope_refuses_reservation(self):
        (self.root/'unfinished').write_bytes(b'x'*int(3.8*2**20))
        self.assertGreater(tree_usage(self.root)[0],3*2**20)
        with self.assertRaises(ValueError):check_scope(self.root,self.limits,reserve_next=True)
        self.assertTrue((self.root/'unfinished').exists())

    def test_generation_payload_cap_and_changed_content(self):
        p=self.root/'video';p.write_bytes(b'a'*100)
        before=generation_snapshot(self.root,self.limits)
        p.write_bytes(b'b'*100)
        self.assertNotEqual(before,generation_snapshot(self.root,self.limits))
        p.write_bytes(b'x'*(2**16+1))
        with self.assertRaises(ValueError):generation_snapshot(self.root,self.limits)

    def test_links_and_special_files_refused(self):
        original=self.root/'original';original.write_bytes(b'x')
        link=self.root/'link';link.symlink_to(original)
        with self.assertRaises(ValueError):tree_usage(self.root)
        link.unlink();os.link(original,link)
        with self.assertRaises(ValueError):tree_usage(self.root)
        link.unlink();os.mkfifo(link)
        with self.assertRaises(ValueError):tree_usage(self.root)

    def test_invalid_or_unusable_limits_refused(self):
        for args in [(True,1,1,1,1,1),(5,1,1,1,1,1),(100,1,1,1,0,1)]:
            with self.assertRaises(ValueError):StorageLimits(*args)


class CalibrationStorageTests(calibration_tests.CalibrationTests):
    """Re-run existing controller controls with the storage boundary enabled."""
    def execute(self,slot,policy,output):
        output.mkdir();(output/'video.fixture').write_bytes(b'CPU fixture, not a video')
        if self.fault=='storage':(output/'oversized').write_bytes(b'x'*2**17)
        return super().execute(slot,policy,output)

    def entry(self,create=False,config=None):
        from wcomr.cara_budget_calibration_r1 import Calibration
        return Calibration(root=self.root,card=self.card,config=config or self.config,context_sha256='b'*64,
            RGB_shape=[3,93,2,2],execute=self.execute,cpu_validation=True,create=create,
            storage_limits=StorageLimits(32*2**20,2**16,2**16,2**16,2**16,2**16))

    def test_oversized_original_payload_stops_without_retry_or_completion(self):
        from wcomr.cara_budget_search_journal_r1 import OriginalQueryUnknown
        self.fault='storage'
        with self.assertRaises(ValueError):self.entry(True).run(allow_new=True)
        self.assertFalse((self.root/'warm-native/complete.json').exists())
        self.assertTrue((self.root/'warm-native/generation/oversized').exists())
        count=len(self.calls)
        with self.assertRaises(OriginalQueryUnknown):self.entry().run(allow_new=True)
        self.assertEqual(len(self.calls),count)

    def test_deleted_completed_payload_refuses_recovery(self):
        self.entry(True).run(allow_new=True);count=len(self.calls)
        (self.root/'warm-native/generation/video.fixture').unlink()
        with self.assertRaises(ValueError):self.entry().run(allow_new=True)
        self.assertEqual(len(self.calls),count)
