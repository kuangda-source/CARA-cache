"""Original CPU terminal/source/resource acceptance and forged-proof refusals."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from accept_cara_read_write_transition_linux_cpu_r1 import accept


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.launch = ROOT/'reports/cara_read_write_transition_Linux_CPU_prepare_r1_20261101.json'
        self.capture = ROOT/'reports/cara_read_write_transition_Linux_CPU_capture_r1_20261101.json'

    def test_actual_complete_original_accepted(self):
        result = accept(self.launch, self.capture)
        self.assertEqual(result['tests_run'], 5)
        self.assertFalse(result['actual_Cosmos_model_VJP'])

    def rejected(self, mutate, *, rehash=False):
        value = json.loads(self.capture.read_text())
        cap = value['result']
        mutate(cap)
        if rehash:
            cap['CPU_proof_sha256'] = hashlib.sha256((json.dumps(cap['CPU_proof'], indent=2)+'\n').encode()).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/'capture.json'
            target.write_text(json.dumps(value))
            with self.assertRaises(AssertionError):
                accept(self.launch, target)

    def test_live_nonzero_exit_and_extra_swap_refused(self):
        for mutate in (
            lambda c:c['container_state'].update(Status='running', Pid=123),
            lambda c:c['container_state'].update(ExitCode=1),
            lambda c:c['host_config'].update(MemorySwap=8*2**30)):
            with self.subTest(mutate=mutate):
                self.rejected(mutate)

    def test_foreign_payload_and_namespace_claim_refused(self):
        self.rejected(lambda c:c.update(payload_intact=False))
        self.rejected(lambda c:c['CPU_proof'].update(actual_WC_RF_imports_and_globals_accepted=False), rehash=True)

    def test_partial_matrix_and_forged_direction_tolerance_refused(self):
        self.rejected(lambda c:c['CPU_proof']['metrics']['flow_True_full36'].update(total_branches=70), rehash=True)
        self.rejected(lambda c:c['CPU_proof']['metrics']['actual_C_cache_and_flow_RF_tiny_VJP'][0].update(
            central_FD=0, absolute_error=.00863885745208517, tolerance=1), rehash=True)


if __name__ == '__main__':
    unittest.main()
