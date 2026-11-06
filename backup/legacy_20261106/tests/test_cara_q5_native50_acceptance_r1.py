"""The original Native50 CPU component cannot stand in for a full Q5 card."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from accept_cara_q5_native50_cpu_r1 import accept


class Native50AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = [ROOT/f'reports/cara_Q5_Native50_{host}_CPU_terminal_r1_20261030.json'
                     for host in ('four_card', 'two_card')]
        cls.values = [json.loads(path.read_bytes()) for path in cls.paths]

    def altered(self, folder, mutate, rebind=True):
        values = copy.deepcopy(self.values)
        mutate(values[1])
        paths = []
        for i, value in enumerate(values):
            if rebind:
                value['CPU_proof_sha256'] = hashlib.sha256((json.dumps(
                    value['CPU_proof'], indent=2, allow_nan=False)+'\n').encode()).hexdigest()
            path = Path(folder)/(str(i)+'.json')
            path.write_text(json.dumps(value))
            paths.append(path)
        return paths

    def test_two_original_hosts_accept_only_the_native_component(self):
        result = accept(self.paths)
        self.assertEqual(result['schedule']['actual_updates'], 51)
        self.assertEqual(result['expected_CFG_model_calls'], 102)
        self.assertEqual(result['successful_tiny_paths_per_host'], 48)
        self.assertEqual(result['declared_failures_per_host'], 12)
        self.assertFalse(result['sparse_profile_mapping_frozen'])
        self.assertFalse(result['GPU_dispatch_ready'])

    def test_missing_or_duplicate_host_refused(self):
        for paths in (self.paths[:1], [self.paths[0], self.paths[0]]):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                accept(paths)

    def test_running_failed_or_other_launch_refused(self):
        for key in ('running', 'failed', 'launch'):
            with self.subTest(key=key), tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
                def mutate(value):
                    if key == 'running':value['container_state'].update(Status='running', Running=True, Pid=12)
                    elif key == 'failed':value['container_state']['ExitCode'] = 1
                    else:value['launch']['client_identity']['start_ticks'] += 1
                with self.assertRaises(ValueError):
                    accept(self.altered(folder, mutate))

    def test_changed_proof_bytes_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
            def mutate(value):value['CPU_proof']['numeric']['checks'].pop()
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                accept(self.altered(folder, mutate, rebind=False))

    def test_grid_incomplete_matrix_or_sparse_expansion_refused(self):
        for key in ('grid', 'grid_values', 'flow', 'paths', 'scope', 'sparse', 'parity'):
            with self.subTest(key=key), tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
                def mutate(value):
                    rows = value['CPU_proof']['numeric']['checks']
                    if key == 'grid':rows[0]['schedule']['actual_updates'] = 50
                    elif key == 'grid_values':rows[0]['schedule']['sigmas'][0] += .0001
                    elif key == 'flow':rows.pop()
                    elif key == 'paths':rows[0]['successful_tiny_paths'] = 23
                    elif key == 'scope':rows[0]['CPU_fragment_scope_sha256'] = 'other'
                    elif key == 'sparse':rows[0]['derivation']['sparse_policy_support_extended'] = True
                    else:rows[0]['Native_allD_ON_OFF_audit_latent_RGB_RNG_exact'] = False
                with self.assertRaises(ValueError):
                    accept(self.altered(folder, mutate))

    def test_CUDA_or_device_request_refused(self):
        for key in ('CUDA', 'device'):
            with self.subTest(key=key), tempfile.TemporaryDirectory(dir=ROOT/'.sync') as folder:
                def mutate(value):
                    if key == 'CUDA':value['CPU_proof']['CUDA_initialized'] = True
                    else:value['host_config']['DeviceRequests'] = [dict(Count=1)]
                with self.assertRaisesRegex(ValueError, 'GPU-hidden'):
                    accept(self.altered(folder, mutate))


if __name__ == '__main__':
    unittest.main()
