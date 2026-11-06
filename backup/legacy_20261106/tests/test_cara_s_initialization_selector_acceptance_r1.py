"""Reject incomplete or altered original selector CPU receipts."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from accept_cara_s_initialization_selector_cpu_r1 import accept, encoded_sha


class SelectorAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture = json.loads((ROOT/'reports/cara_s_initialization_selector_CPU_capture_r1_20261031.json').read_text())
        cls.launch = json.loads((ROOT/'reports/cara_s_initialization_selector_CPU_launch_r1_20261031.json').read_text())

    def test_original_complete(self):
        accepted = accept(self.capture, self.launch)
        self.assertEqual(accepted['additional_histories_verified'], 138)
        self.assertEqual(accepted['checked_selector_pairs'], 12312)

    def test_running_refused(self):
        captured = copy.deepcopy(self.capture)
        captured['result']['container_state']['Running'] = True
        with self.assertRaisesRegex(ValueError, 'exit zero'):
            accept(captured, self.launch)

    def test_wrong_resource_refused(self):
        captured = copy.deepcopy(self.capture)
        captured['result']['host_config']['MemorySwap'] *= 2
        with self.assertRaisesRegex(ValueError, 'boundary differs'):
            accept(captured, self.launch)

    def test_changed_source_refused(self):
        captured = copy.deepcopy(self.capture)
        captured['result']['payload_intact'] = False
        with self.assertRaisesRegex(ValueError, 'source and runtime differ'):
            accept(captured, self.launch)

    def check_proof_mutation(self, key, value, message):
        captured = copy.deepcopy(self.capture)
        result = captured['result']
        result['CPU_proof'][key] = value
        # Preserve byte integrity to exercise semantic acceptance separately.
        result['CPU_proof_sha256'] = encoded_sha(result['CPU_proof'])
        with self.assertRaisesRegex(ValueError, message):
            accept(captured, self.launch)

    def test_incomplete_history_refused(self):
        self.check_proof_mutation('additional_histories_verified', [], 'All 138')

    def test_wrong_policy_denominator_refused(self):
        self.check_proof_mutation('checked_distinct_policies', 341, 'denominator')

    def test_missing_anchor_control_refused(self):
        self.check_proof_mutation('anchor_mutations_refused', [], 'anchor refusals')

    def test_cuda_initialization_refused(self):
        self.check_proof_mutation('CUDA_initialized', True, 'no-GPU boundary')


if __name__ == '__main__':
    unittest.main()
