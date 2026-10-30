"""No single-host, unfinished or altered CPU receipt can complete the F18 bridge."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from accept_cara_fast_f18_cpu_r1 import accept


class F18AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = [ROOT/f'reports/cara_fast_F18_{h}_CPU_terminal_r1_20261030.json'
                     for h in ('four_card', 'two_card')]
        cls.values = [json.loads(p.read_text()) for p in cls.paths]

    def changed_paths(self, folder, change, rebind=False):
        values = copy.deepcopy(self.values)
        change(values)
        paths = []
        for i, value in enumerate(values):
            if rebind:
                value['CPU_proof_sha256'] = hashlib.sha256((json.dumps(
                    value['CPU_proof'], indent=2, allow_nan=False)+'\n').encode()).hexdigest()
            path = Path(folder)/(str(i)+'.json'); path.write_text(json.dumps(value)); paths.append(path)
        return paths

    def test_complete_two_original_hosts(self):
        result = accept(self.paths)
        self.assertEqual(len(result['receipts']), 2)
        self.assertEqual(result['successful_tiny_paths_per_host'], 36)
        self.assertEqual(result['declared_failure_attempts_per_host'], 18)
        self.assertEqual(result['CHECK_positions'], 6)
        self.assertFalse(result['GPU_dispatch_ready'])
        self.assertFalse(result['whole_quote_frozen'])
        self.assertEqual(result['GPU_submissions'], 0)

    def test_single_or_duplicate_host_refused(self):
        for paths in (self.paths[:1], [self.paths[0], self.paths[0]]):
            with self.subTest(paths=paths), self.assertRaises(ValueError): accept(paths)

    def test_running_or_failed_container_refused(self):
        for kind in ('running', 'failed'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
                def change(values):
                    state=values[1]['container_state']
                    if kind=='running': state.update(Status='running', Running=True, Pid=12)
                    else: state['ExitCode']=1
                with self.assertRaisesRegex(ValueError, 'must exit normally'):
                    accept(self.changed_paths(folder, change))

    def test_changed_proof_bytes_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
            def change(values): values[1]['CPU_proof']['numeric']['checks'].pop()
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                accept(self.changed_paths(folder, change))

    def test_incomplete_matrix_or_anchor_control_refused_after_rebinding(self):
        for kind in ('flow', 'count', 'anchor', 'scope'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
                def change(values):
                    rows=values[1]['CPU_proof']['numeric']['checks']
                    if kind=='flow': rows.pop()
                    elif kind=='count': rows[0]['successful_tiny_paths']=17
                    elif kind=='anchor': rows[0]['F18_A1_step9_C_from_D7_preserved']=False
                    else: rows[0]['CPU_fragment_scope_sha256']='other-fragment'
                with self.assertRaises(ValueError): accept(self.changed_paths(folder, change, rebind=True))

    def test_GPU_initialization_or_missing_isolation_refused(self):
        for kind in ('CUDA', 'device'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
                def change(values):
                    if kind=='CUDA': values[1]['CPU_proof']['CUDA_initialized']=True
                    else: values[1]['host_config']['DeviceRequests']=[dict(Count=1)]
                with self.assertRaisesRegex(ValueError, 'GPU-hidden'):
                    accept(self.changed_paths(folder, change, rebind=True))


if __name__ == '__main__': unittest.main()
