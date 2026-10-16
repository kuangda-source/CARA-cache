"""Same complete byte protocol with synthetic curl; no public download or models."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import test_N10_resource_ranges_r1 as old_tests

ROOT=Path(__file__).resolve().parents[1]


def script(name):
    spec=importlib.util.spec_from_file_location('direct_resource_test_'+name,ROOT/'scripts'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


W=script('fetch_wc_N10_viclip_direct_r2')


class DirectResourceControls(old_tests.RangeResourceControls):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.stage=Path(self.temp.name)
        shutil.copyfile(ROOT/'scripts'/W.ORIGINAL,self.stage/W.ORIGINAL)
        self.worker,self.proof=W.derive(self.stage)
        setting=patch.object(old_tests,'M',self.worker);setting.start();self.addCleanup(setting.stop)

    def test_exact_direct_route_preserves_TLS_range_and_whole_object_logic(self):
        self.assertTrue(self.proof['inverse_bytes_and_AST_equal'])
        self.assertTrue(self.proof['full_scope_and_range_ETag_and_whole_SHA_unchanged'])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old_tests.fixture(root);callback,calls=old_tests.fake_curl()
            def inspect(command,**kwargs):
                self.assertEqual(command[1],'--disable')
                self.assertEqual(command[command.index('--proxy')+1],'')
                self.assertEqual(command[command.index('--noproxy')+1],'*')
                self.assertEqual(command[command.index('--max-time')+1],'90')
                self.assertNotIn('--insecure',command);self.assertNotIn('-k',command)
                return callback(command,**kwargs)
            with self.constants(),patch.object(self.worker.subprocess,'run',side_effect=inspect):
                code=self.worker.download(root)
            self.assertEqual(code,0);self.assertEqual(calls,[(0,7),(8,15),(16,19)])
            self.assertEqual((root/'SYNTHETIC.pth').read_bytes(),old_tests.RAW)

    def test_changed_original_helper_or_unregistered_route_refuses(self):
        (self.stage/W.ORIGINAL).write_text('CHANGED_ORIGINAL_SOURCE')
        with self.assertRaises(ValueError):W.derive(self.stage)
        (self.stage/'registration.json').write_text(json.dumps(dict(transport_policy='OTHER_ROUTE',
            original_range_worker_sha256=W.ORIGINAL_SHA)))
        with self.assertRaisesRegex(ValueError,'explicitly registered direct route'):W.download(self.stage)

    def test_collector_explicitly_binds_both_direct_and_original_source_bytes(self):
        collector=script('capture_wc_N10_viclip_local_proxy_r2')
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);name='fetch_wc_N10_viclip_direct_r2.py'
            for file in (name,W.ORIGINAL):shutil.copyfile(ROOT/'scripts'/file,stage/file)
            reg=dict(worker_sha256=collector.sha(stage/name),original_range_worker_sha256=W.ORIGINAL_SHA,
                transport_policy=W.POLICY)
            launch=dict(worker_file=name,worker_sha256=reg['worker_sha256'],transport_policy=W.POLICY)
            self.assertEqual(collector.worker_identity(stage,launch,reg),name)
            reg['transport_policy']='OTHER'
            with self.assertRaises(AssertionError):collector.worker_identity(stage,launch,reg)
            reg['transport_policy']=W.POLICY;(stage/W.ORIGINAL).write_text('changed')
            with self.assertRaises(AssertionError):collector.worker_identity(stage,launch,reg)

    def test_launcher_uses_actual_successful_direct_nonzero_bytes_not_HEAD_only(self):
        launcher=script('launch_wc_N10_viclip_direct_r2')
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);body=stage/'failed_offset_direct.bin';body.write_bytes(b'x'*1048576)
            expected=dict(url='https://example.invalid/PINNED',bytes=1710545812,sha256='a'*64,name='test')
            row=dict(name='failed_offset_direct',route='DIRECT',accepted=True,curl_exit=0,response_status=206,
                requested_range=[117440512,118489087],body_bytes=1048576,
                body_sha256=hashlib.sha256(body.read_bytes()).hexdigest(),response_headers=dict(
                etag='"object"',**{'content-range':'bytes 117440512-118489087/1710545812'}))
            probe=dict(canonical_public_url=expected['url'],expected_ETag='"object"',
                requests=[row],local_stage=str(stage))
            self.assertEqual(launcher.validated_direct_probe(probe,expected,'"object"'),row)
            for field,value in [('accepted',False),('route','PROXY'),('body_bytes',1),('response_status',200)]:
                bad=copy.deepcopy(probe);bad['requests'][0][field]=value
                with self.subTest(field=field),self.assertRaises(ValueError):
                    launcher.validated_direct_probe(bad,expected,'"object"')
            body.write_bytes(b'changed')
            with self.assertRaises(ValueError):launcher.validated_direct_probe(probe,expected,'"object"')


if __name__=='__main__':unittest.main()
