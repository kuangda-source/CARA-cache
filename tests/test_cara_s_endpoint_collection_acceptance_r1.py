"""Independent acceptance controls against the original completed Linux CPU run."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from accept_cara_s_endpoint_collection_cpu_r1 import accept, encoded_sha


class AcceptanceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt = json.loads((ROOT / 'reports/cara_s_endpoint_collection_CPU_accepted_r2_20261031.json').read_text())
        cls.capture = json.loads((ROOT / receipt['capture_ref']).read_text())
        cls.launch = json.loads((ROOT / receipt['launch_ref']).read_text())

    def reject(self, change, message, resign=False):
        captured = copy.deepcopy(self.capture)
        change(captured['result'])
        if resign: captured['result']['CPU_proof_sha256'] = encoded_sha(captured['result']['CPU_proof'])
        with self.assertRaisesRegex(ValueError, message): accept(captured, self.launch)

    def test_original_complete_acceptance(self):
        result = accept(self.capture, self.launch)
        self.assertEqual(result['production_paths'], 114)
        self.assertEqual(result['independent_reference_paths'], 16)
        self.assertFalse(result['whole_GPU_card_accepted'])

    def test_running_is_not_accepted(self):
        self.reject(lambda c: c['container_state'].update(Running=True), 'Exited zero')

    def test_missing_proof(self):
        self.reject(lambda c: c.update(CPU_proof=None), 'Exited zero')

    def test_source_intact_required(self):
        self.reject(lambda c: c.update(payload_intact=False), 'source/runtime')

    def test_resource_limits_required(self):
        self.reject(lambda c: c['host_config'].update(DeviceRequests=[{}]), 'resource boundary')

    def test_proof_bytes_required(self):
        self.reject(lambda c: c['CPU_proof'].update(production_paths=113), 'Original bytes')

    def test_partial_matrix_even_rehashed(self):
        self.reject(lambda c: c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(paths=31), 'matrix', True)

    def test_both_flows_required(self):
        self.reject(lambda c: c['CPU_proof']['numeric']['checks'].pop(), 'Both flow', True)

    def test_changed_bound_scope(self):
        self.reject(lambda c: c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(scope_sha256='0'*64), 'matrix', True)

    def test_wrong_actual_settings(self):
        self.reject(lambda c: c['CPU_proof']['numeric']['checks'][0]['effective_settings'].update(worldcache_flow_enabled='wrong'),
                    'matched production', True)

    def test_failure_denominator_cannot_be_dropped(self):
        self.reject(lambda c: c['CPU_proof']['numeric']['checks'][0]['cases'][0]['failures'].pop(), 'matrix', True)

    def test_no_real_historical_claim(self):
        self.reject(lambda c: c['CPU_proof']['numeric']['checks'][0]['cases'][0].update(actual_historical_RGB_acceptance=True),
                    'synthetic-scope', True)

    def test_cuda_initialization_refused(self):
        self.reject(lambda c: c['CPU_proof'].update(CUDA_initialized=True), 'CPU boundary', True)


if __name__ == '__main__': unittest.main()
