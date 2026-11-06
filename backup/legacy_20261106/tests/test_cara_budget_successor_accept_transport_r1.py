"""Recovery must not resubmit an existing complete-reader CPU job."""
import ast
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
TREE = ast.parse((ROOT/'scripts/cara_budget_successor_accept_transport_r1.py').read_text())
REMOTE = next(ast.literal_eval(node.value) for node in TREE.body if isinstance(node, ast.Assign)
              and node.targets[0].id == 'REMOTE')


class OriginalReaderRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root/'.sync/cara-budget-calibration-GPU-a6000-r3-20261031'
        self.stage.mkdir(parents=True)
        self.cpu = self.root/'.sync/test-reader'
        self.source = 'a'*40
        self.image = 'sha256:'+'b'*64
        (self.stage/'GPU-launch.json').write_text(json.dumps({'launch_id': 'original-launch'}))
        self.launch_sha = hashlib.sha256((self.stage/'GPU-launch.json').read_bytes()).hexdigest()
        (self.stage/'registration.json').write_text(json.dumps(dict(source_revision=self.source,
            payload_sha256={}, container_image=self.image)))
        self.payload = dict(action='capture', cpu_name='test-reader', launch_sha256=self.launch_sha,
                            source_revision=self.source, worker_sha256=hashlib.sha256(b'worker').hexdigest())
        self.container = None

    def run_remote(self):
        calls = []
        def inspect_only(command, **kwargs):
            calls.append(command)
            self.assertEqual(command, ['docker', 'inspect', 'test-reader-cpu'])
            return subprocess.CompletedProcess(command, 0 if self.container else 1,
                json.dumps([self.container]) if self.container else '',
                '' if self.container else 'No such container')
        code = REMOTE.replace("pathlib.Path('/data20t/gaokuangda/worldcache_workspace')", repr(self.root))
        # repr(Path) is PosixPath(...); use the explicitly imported pathlib name.
        code = code.replace(repr(self.root), 'pathlib.Path('+repr(str(self.root))+')')
        output = io.StringIO()
        with patch('subprocess.run', side_effect=inspect_only), redirect_stdout(output):
            exec(compile(code, 'original-reader-remote', 'exec'), {'packet': {'arguments': self.payload}})
        self.assertEqual(len(calls), 1)
        return json.loads(output.getvalue())

    def existing(self):
        self.cpu.mkdir()
        (self.cpu/'worker.py').write_bytes(b'worker')
        (self.cpu/'plan.json').write_text(json.dumps(dict(stage=str(self.stage), source_revision=self.source,
            launch_sha256=self.launch_sha, worker_sha256=self.payload['worker_sha256'])))
        self.container = dict(Image=self.image, Config={'Labels': {'wcomr.original-launch': 'original-launch'}},
            HostConfig=dict(DeviceRequests=None, Memory=8*2**30, MemorySwap=8*2**30, NanoCpus=2*10**9,
                NetworkMode='none', ReadonlyRootfs=True, CpusetCpus='26,27'), State={'Running': True, 'Pid': 123})

    def test_absent_capture_never_creates(self):
        result = self.run_remote()
        self.assertFalse(result['stage_exists'])
        self.assertFalse(result['new_CPU_submission'])

    def test_existing_prepare_is_recovery_only(self):
        self.existing(); self.payload['action'] = 'prepare'
        self.assertFalse(self.run_remote()['new_CPU_submission'])

    def test_existing_directory_without_container_never_replays(self):
        self.cpu.mkdir(); self.payload['action'] = 'prepare'
        result = self.run_remote()
        self.assertIsNone(result['container'])
        self.assertFalse(result['new_CPU_submission'])

    def test_gpu_device_refused(self):
        self.existing(); self.container['HostConfig']['DeviceRequests'] = [{'Count': 1}]
        with self.assertRaises(AssertionError): self.run_remote()

    def test_changed_worker_refused(self):
        self.existing(); (self.cpu/'worker.py').write_bytes(b'changed')
        with self.assertRaises(AssertionError): self.run_remote()

    def test_other_launch_refused(self):
        self.existing(); self.container['Config']['Labels']['wcomr.original-launch'] = 'another'
        with self.assertRaises(AssertionError): self.run_remote()


if __name__ == '__main__':
    unittest.main()
