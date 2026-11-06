"""Numeric-UID and writable process-cache regressions without Torch or GPU."""
import getpass
import importlib.util
import os
from pathlib import Path
import pwd
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r43worker',ROOT/'scripts/finish_wc_four_card_resources_cpu_r4.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)


class ProcessIdentityCacheControls(unittest.TestCase):
    def test_numeric_uid_without_passwd_entry_reproduced(self):
        with patch.dict(os.environ,{},clear=True),patch.object(pwd,'getpwuid',side_effect=KeyError('numeric UID missing')):
            with self.assertRaises(KeyError):getpass.getuser()

    def test_process_name_resolves_without_modifying_password_database(self):
        with tempfile.TemporaryDirectory() as d:
            values=w.process_cache_environment(d,'gaokuangda')
            with patch.dict(os.environ,values,clear=True),patch.object(pwd,'getpwuid',side_effect=KeyError('numeric UID missing')):
                self.assertEqual(getpass.getuser(),'gaokuangda')
                value=w.verify_process_cache_environment(d,'gaokuangda')
            self.assertFalse(value['system_passwd_modified']);self.assertEqual(value['numeric_uid'],os.getuid())

    def test_all_explicit_cache_directories_are_owned_and_writable(self):
        with tempfile.TemporaryDirectory() as d:
            values=w.process_cache_environment(d,'gaokuangda')
            with patch.dict(os.environ,values):value=w.verify_process_cache_environment(d,'gaokuangda')
            self.assertTrue(value['write_probe_pass'])
            for k,v in values.items():
                if k not in ['USER','LOGNAME']:
                    self.assertTrue(Path(v).is_dir());self.assertIn(Path(d),Path(v).parents)
                    self.assertFalse((Path(v)/'.owned-write-probe').exists())

    def test_missing_explicit_inductor_cache_refused(self):
        with tempfile.TemporaryDirectory() as d:
            values=w.process_cache_environment(d,'gaokuangda');values.pop('TORCHINDUCTOR_CACHE_DIR')
            with patch.dict(os.environ,values,clear=True):
                with self.assertRaises(AssertionError):w.verify_process_cache_environment(d,'gaokuangda')
            self.assertFalse((Path(d)/'process-caches').exists())

    def test_cache_parent_symlink_cannot_escape_new_job(self):
        with tempfile.TemporaryDirectory() as d,tempfile.TemporaryDirectory() as outside:
            (Path(d)/'process-caches').symlink_to(outside,target_is_directory=True)
            values=w.process_cache_environment(d,'gaokuangda')
            with patch.dict(os.environ,values):
                with self.assertRaises(AssertionError):w.verify_process_cache_environment(d,'gaokuangda')
            self.assertEqual(list(Path(outside).iterdir()),[])


if __name__=='__main__':unittest.main()
