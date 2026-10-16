"""Small real files and original dispatch boundaries; no SSH/model execution."""
import ast
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('fixed_resource_relay_only', ROOT/'scripts/relay_wc_N10_viclip_resource_r1.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
RAW = b'SYNTHETIC_RESOURCE_FIXTURE_NOT_A_MODEL_CHECKPOINT'
EXPECTED = dict(name='SYNTHETIC.pth', bytes=len(RAW), sha256=hashlib.sha256(RAW).hexdigest(),
                url='https://example.invalid/NO_NETWORK_IN_TESTS')


def metadata():
    registration = json.dumps(dict(purpose='SYNTHETIC_RESOURCE_FIXTURE', expected_weight=EXPECTED))+'\n'
    return dict(remote_stage='.sync/wc-N10-viclip-relay-SYNTHETIC', expected_weight=EXPECTED,
        remote_registration_text=registration,
        remote_registration_sha256=hashlib.sha256(registration.encode()).hexdigest(),
        source_revision='SYNTHETIC_NOT_REAL_DISPATCH', local_resource_capture_sha256='a'*64,
        local_download_source_revision='SYNTHETIC_NOT_REAL_DOWNLOAD')


def execute(code, root, **values):
    tree = ast.parse(code)
    class FixtureRoot(ast.NodeTransformer):
        def visit_Constant(self, node):
            if node.value == M.SERVER_ROOT:
                return ast.copy_location(ast.Constant(str(root)), node)
            return node
    tree = ast.fix_missing_locations(FixtureRoot().visit(tree))
    output = io.StringIO()
    with redirect_stdout(output):
        exec(compile(tree, 'SYNTHETIC_LOCAL_RESOURCE_ONLY', 'exec'), values)
    return json.loads(output.getvalue())


def local_capture(root):
    stage = root/'original-local'; stage.mkdir()
    target = stage/EXPECTED['name']; target.write_bytes(RAW)
    value = dict(status='N10_LOCAL_PROXY_RESOURCE_ORIGINAL_ONCE_CAPTURE', original_process_alive=False,
        local_resource_bytes_independently_accepted=True, observed_unix=2.,
        launch=dict(stage=str(stage), expected_weight=EXPECTED, source_revision='SYNTHETIC_DOWNLOAD',
                    first_collection_not_before_unix=1.),
        result=dict(status='N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME',
                    exit_code=0, target=str(target), source_revision='SYNTHETIC_DOWNLOAD'),
        independent_target_bytes=len(RAW), independent_target_sha256=EXPECTED['sha256'])
    path = root/'original-capture.json'; path.write_text(json.dumps(value))
    return path, target


class ResourceRelayControls(unittest.TestCase):
    def test_fresh_registered_prepare_does_not_touch_existing_project_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'.sync').mkdir()
            sentinel = root/'untouched-budget.json'; sentinel.write_bytes(b'PRESERVE')
            meta = metadata(); prepared = execute(M.PREPARE, root, META=meta)
            self.assertEqual(prepared['registration_sha256'], meta['remote_registration_sha256'])
            self.assertEqual(sentinel.read_bytes(), b'PRESERVE')
            self.assertFalse((Path(prepared['stage'])/EXPECTED['name']).exists())
            self.assertEqual(prepared['GPU_submissions'], 0)

    def test_original_remote_stage_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'.sync').mkdir(); meta = metadata()
            first = execute(M.PREPARE, root, META=meta)
            original = (Path(first['stage'])/'registration.json').read_bytes()
            with self.assertRaises(AssertionError): execute(M.PREPARE, root, META=meta)
            self.assertEqual((Path(first['stage'])/'registration.json').read_bytes(), original)

    def test_whole_remote_bytes_required_before_rename_and_result(self):
        for data in (RAW, RAW[:-1], RAW+b'EXTRA', bytes([RAW[0]^1])+RAW[1:]):
            with self.subTest(data=data), tempfile.TemporaryDirectory() as folder:
                root = Path(folder); (root/'.sync').mkdir(); meta = metadata()
                prepared = execute(M.PREPARE, root, META=meta)
                part = Path(prepared['partial']); part.write_bytes(data)
                if data == RAW:
                    result = execute(M.FINALIZE, root, META=meta, PREPARED=prepared)
                    self.assertEqual(result['actual_sha256'], EXPECTED['sha256'])
                    self.assertEqual(Path(result['target']).read_bytes(), RAW)
                    self.assertFalse(part.exists())
                    self.assertEqual(result['transport_origin'], 'LOCAL_PINNED_RESOURCE_THEN_ORIGINAL_SCP')
                else:
                    with self.assertRaises(AssertionError):
                        execute(M.FINALIZE, root, META=meta, PREPARED=prepared)
                    self.assertEqual(part.read_bytes(), data)
                    self.assertFalse((part.parent/EXPECTED['name']).exists())
                    self.assertFalse((part.parent/'resource-result.json').exists())

    def test_independent_capture_hashes_terminal_target_but_not_active_transfer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'.sync').mkdir(); meta = metadata()
            prepared = execute(M.PREPARE, root, META=meta)
            Path(prepared['partial']).write_bytes(RAW)
            execute(M.FINALIZE, root, META=meta, PREPARED=prepared)
            live = execute(M.CAPTURE, root, META=meta, ORIGINAL_ALIVE=True)
            self.assertNotIn('independent_target_sha256', live)
            final = execute(M.CAPTURE, root, META=meta, ORIGINAL_ALIVE=False)
            self.assertEqual(final['independent_target_sha256'], EXPECTED['sha256'])
            self.assertFalse(final['server_files_written'])

    def test_unaccepted_local_resource_is_refused_before_any_git_ssh_or_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            path, _ = local_capture(Path(folder)); value = json.loads(path.read_text())
            value['original_process_alive'] = True; path.write_text(json.dumps(value))
            with patch.object(M, 'EXPECTED', EXPECTED), patch.object(M.subprocess, 'check_output') as git, \
                 patch.object(M, 'remote') as ssh, patch.object(M.subprocess, 'Popen') as child:
                with self.assertRaises(ValueError):
                    M.launch(SimpleNamespace(local_resource_capture=path, stage='UNUSED', output=Path(folder)/'UNUSED'))
                git.assert_not_called(); ssh.assert_not_called(); child.assert_not_called()

    def test_local_target_change_after_capture_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            path, target = local_capture(Path(folder))
            with patch.object(M, 'EXPECTED', EXPECTED):
                self.assertEqual(M.accepted_local_resource(path)[1], target)
                target.write_bytes(b'X'*len(RAW))
                with self.assertRaises(ValueError): M.accepted_local_resource(path)

    def test_failed_scp_is_preserved_and_original_worker_cannot_redispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); capture, _ = local_capture(root); stage = root/'relay'; stage.mkdir()
            meta = metadata()
            meta.update(purpose='N10_PINNED_RESOURCE_ORIGINAL_SCP_ONLY',
                worker_sha256=M.sha(M.__file__), local_resource_capture_ref=str(capture),
                local_resource_capture_sha256=M.sha(capture))
            (stage/'registration.json').write_text(json.dumps(meta))
            remote_stage = root/'FAKE_SERVER_PROJECT'/meta['remote_stage']
            prepared = dict(status='N10_RESOURCE_RELAY_FRESH_SERVER_STAGE_PREPARED',
                stage=str(remote_stage), source_revision=meta['source_revision'],
                registration_sha256=meta['remote_registration_sha256'], partial=str(remote_stage/'SYNTHETIC.pth.part'))
            with patch.object(M, 'EXPECTED', EXPECTED), patch.object(M, 'remote', return_value=prepared) as ssh, \
                 patch.object(M.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout=b'', stderr=b'SYNTHETIC_TRANSFER_FAILED')) as scp:
                self.assertEqual(M.run_worker(stage), 1)
                self.assertEqual(ssh.call_count, 1); self.assertEqual(scp.call_count, 1)
                result = json.loads((stage/'relay-result.json').read_text())
                self.assertFalse(result['retry_authorized'])
                self.assertEqual(json.loads((stage/'scp-exit.json').read_text())['exit_code'], 1)
                with self.assertRaises(FileExistsError): M.run_worker(stage)
                self.assertEqual(ssh.call_count, 1); self.assertEqual(scp.call_count, 1)

    def test_collection_before_eta_does_not_query_pid_files_or_ssh(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'future-launch.json'
            path.write_text(json.dumps(dict(first_collection_not_before_unix=time.time()+3600)))
            with patch.object(M, 'original_local_process') as process, patch.object(M, 'remote') as ssh:
                with self.assertRaises(SystemExit):
                    M.capture(SimpleNamespace(launch_ref=path, output=Path(folder)/'UNUSED'))
                process.assert_not_called(); ssh.assert_not_called()

    def test_mac_identity_survives_nice_exec_but_not_pid_reuse(self):
        stage = '/SYNTHETIC ONLY/relay'
        worker = stage+'/relay_wc_N10_viclip_resource_r1.py'
        launch = dict(pid=123, stage=stage, process_at_admission=
            '123 Fri Oct 16 13:00:00 2026 /usr/bin/nice -n 10 /python '+worker+' run --stage '+stage)
        cases = [('13:00:00', worker, True), ('13:01:00', worker, False),
                 ('13:00:00', '/SYNTHETIC_FOREIGN_WORKER.py', False)]
        for start, actual_worker, expected in cases:
            with self.subTest(start=start, worker=actual_worker):
                output = '123 Fri Oct 16 '+start+' 2026 S /python '+actual_worker+' run --stage '+stage
                with patch.object(M.subprocess, 'run', return_value=SimpleNamespace(stdout=output)):
                    self.assertEqual(M.original_local_process(launch)[0], expected)


if __name__ == '__main__':
    unittest.main()
