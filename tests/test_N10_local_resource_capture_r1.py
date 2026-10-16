"""ETA-gated Mac handle checks and independent tiny target byte audit."""
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('local_resource_capture_only', ROOT/'scripts/capture_wc_N10_viclip_local_proxy_r2.py')
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


def fixture(root, range_worker=True):
    stage = root/'.sync/SYNTHETIC'; stage.mkdir(parents=True)
    name = 'fetch_wc_N10_viclip_ranges_r1.py' if range_worker else 'fetch_wc_N10_viclip_resource_r1.py'
    worker = stage/name; worker.write_bytes(b'# SYNTHETIC ONLY NOT EXECUTED')
    data = b'SYNTHETIC_NOT_WEIGHTS'
    expected = dict(name='SYNTHETIC.pth',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    (stage/expected['name']).write_bytes(data)
    reg = dict(source_revision='SYNTHETIC',worker_sha256=M.sha(worker),expected_weight=expected)
    (stage/'registration.json').write_text(json.dumps(reg))
    (stage/'resource-result.json').write_text(json.dumps(dict(source_revision='SYNTHETIC',exit_code=0,
        status='N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME',target=str(stage/expected['name']),
        actual_bytes=len(data),actual_sha256=expected['sha256'])))
    (stage/'range-progress.json').write_text(json.dumps(dict(committed_bytes=len(data),completed_ranges=1)))
    launch = dict(source_revision='SYNTHETIC',stage=str(stage),pid=123,first_collection_not_before_unix=10.,
        worker_sha256=M.sha(worker),registration_sha256=M.sha(stage/'registration.json'),expected_weight=expected,
        process_at_admission=f'123 Fri Oct 16 13:00:00 2026 /usr/bin/nice -n 10 /python {worker} --stage {stage}')
    if range_worker: launch['worker_file']=name
    path = root/'launch.json'; path.write_text(json.dumps(launch))
    return path, launch


def capture(root, path, process='', now=20.):
    out = root/'capture.json'
    with patch.object(M,'ROOT',root.resolve()),patch.object(M.time,'time',return_value=now), \
         patch.object(M.subprocess,'run',return_value=SimpleNamespace(stdout=process)) as ps, \
         patch.object(sys,'argv',['capture','--launch-ref',str(path),'--output',str(out)]),redirect_stdout(io.StringIO()):
        M.main()
    return json.loads(out.read_text()), ps


class LocalResourceCaptureControls(unittest.TestCase):
    def test_new_range_and_original_legacy_worker_both_keep_independent_full_sha(self):
        for ranged in (False, True):
            with self.subTest(ranged=ranged),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);path,launch=fixture(root,ranged);value,_=capture(root,path)
                self.assertTrue(value['local_resource_bytes_independently_accepted'])
                self.assertFalse(value['original_process_alive'])
                self.assertEqual(value['independent_target_sha256'],launch['expected_weight']['sha256'])
                self.assertEqual(value['range_progress']['completed_ranges'],1)

    def test_original_nice_exec_identity_is_live_and_blocks_resource_acceptance(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC only ') as folder:
            root=Path(folder);path,launch=fixture(root)
            worker=Path(launch['stage'])/launch['worker_file']
            process=f'123 Fri Oct 16 13:00:00 2026 R /python {worker} --stage {launch["stage"]}'
            value,_=capture(root,path,process)
            self.assertTrue(value['original_process_alive']);self.assertTrue(value['PID_identity_matches'])
            self.assertFalse(value['local_resource_bytes_independently_accepted'])
            self.assertIsNone(value['independent_target_sha256'])

    def test_before_original_eta_refuses_without_any_process_query(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path,_=fixture(root)
            with patch.object(M.subprocess,'run') as ps,self.assertRaises(SystemExit):
                capture(root,path,now=0.)
            ps.assert_not_called();self.assertFalse((root/'capture.json').exists())

    def test_foreign_worker_name_refuses_before_process_query(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path,launch=fixture(root);launch['worker_file']='../FOREIGN.py'
            path.write_text(json.dumps(launch))
            with patch.object(M.subprocess,'run') as ps,self.assertRaises(AssertionError):capture(root,path)
            ps.assert_not_called();self.assertFalse((root/'capture.json').exists())


if __name__=='__main__':unittest.main()
