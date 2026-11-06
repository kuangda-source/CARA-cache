import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_cara_budget_calibration_cost_basis_r1 import build


class CostTests(unittest.TestCase):
    def setUp(self):
        self.analysis=json.loads((ROOT/'reports/cara_fast_B36_complete_analysis_r1_20261029.json').read_text())
        self.capture=json.loads((ROOT/'reports/cara_budget_full_RGB_cost_four_card_CPU_capture_r1_20261030.json').read_text())

    def test_actual_sources_and_complete_301_count(self):
        value=build(self.analysis,self.capture)
        self.assertEqual(value['default_teacher_plus_candidate_paths'],604)
        self.assertGreater(value['default_pipeline_request_proxy_GPUh'],36)
        self.assertFalse(value['whole_GPU_quote_accepted']);self.assertIsNone(value['proposed_hard_GPUh'])
        self.assertEqual(len(value['FIT_timing_samples']),6)

    def test_CHECK_timing_is_not_used(self):
        before=build(self.analysis,self.capture)
        for row in self.analysis['per_member']:
            if row['partition']!='FIT':
                for sample in row['timing_samples']:sample['T_request']=99999
        after=build(self.analysis,self.capture)
        self.assertEqual(before['default_pipeline_request_proxy_GPUh'],after['default_pipeline_request_proxy_GPUh'])

    def test_incomplete_original_or_wrong_CPU_resources_refused(self):
        self.analysis['formal_logical_positions']=31
        with self.assertRaises(ValueError):build(self.analysis,self.capture)
        self.analysis['formal_logical_positions']=32
        self.capture['host_config']['MemorySwap']=8*2**30
        with self.assertRaises(ValueError):build(self.analysis,self.capture)

    def test_changed_measurement_digest_refused(self):
        self.capture['CPU_proof']['candidate_save_fsync_and_hash_seconds']=.001
        with self.assertRaises(ValueError):build(self.analysis,self.capture)


if __name__=='__main__':unittest.main()
