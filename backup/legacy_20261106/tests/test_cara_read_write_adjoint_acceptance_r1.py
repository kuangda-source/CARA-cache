"""Actual original tiny-adjoint CPU receipt and numerical/scope refusals."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from accept_cara_read_write_adjoint_linux_cpu_r1 import accept


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.launch = ROOT/'reports/cara_read_write_adjoint_Linux_CPU_prepare_r2_20261101.json'
        self.capture = ROOT/'reports/cara_read_write_adjoint_Linux_CPU_capture_r2_20261101.json'

    def test_actual_complete_original_accepted(self):
        result = accept(self.launch, self.capture)
        self.assertEqual(result['tests_run'], 5)
        self.assertTrue(result['complete_tiny_adjoint'])
        self.assertFalse(result['real_Cosmos_adjoint'])

    def reject_proof(self, mutate):
        value = json.loads(self.capture.read_text());cap = value['result']
        mutate(cap['CPU_proof'])
        cap['CPU_proof_sha256'] = hashlib.sha256((json.dumps(cap['CPU_proof'], indent=2)+'\n').encode()).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'capture.json';path.write_text(json.dumps(value))
            with self.assertRaises(AssertionError):
                accept(self.launch, path)

    def test_partial_derivatives_and_false_zero_control_refused(self):
        self.reject_proof(lambda p:p['metrics']['actual_WC_tiny_point8_auxiliary_derivatives'].pop())
        self.reject_proof(lambda p:p['metrics']['actual_WC_post35_no_future_cache_consumer'].update(write=1e-8))

    def test_bad_adjoint_error_and_overstated_real_model_scope_refused(self):
        self.reject_proof(lambda p:p['metrics']['full36_recomputed_adjoint'].update(max_absolute_error=.1))
        self.reject_proof(lambda p:p.update(actual_Cosmos_weights=True))


if __name__ == '__main__':
    unittest.main()
