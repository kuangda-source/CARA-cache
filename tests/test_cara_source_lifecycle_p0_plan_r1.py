"""Full P0 increment denominator, new control identity and no-replay boundary."""
import copy
import json
from pathlib import Path
import unittest

from wcomr.cara_read_write_plan_r1 import build as original
from wcomr.cara_source_lifecycle_p0_plan_r1 import build,validate

ROOT=Path(__file__).resolve().parents[1]


class Scope(unittest.TestCase):
    def setUp(self):
        self.parent=json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())

    def test_full14_512_new_calls_and_eight_new_scientific_corners(self):
        card=build(self.parent);validate(card,self.parent)
        self.assertEqual(card['target_update'],20)
        self.assertEqual(len(card['physical_matrix']),14)
        self.assertEqual(card['counts']['physical_model_pairs'],512)
        self.assertEqual(card['counts']['scientific_four_corner_outputs'],8)
        self.assertEqual(card['original_point8_new_GPU_paths'],0)
        self.assertEqual(card['original_point8_new_scoring'],0)

    def test_twenty_dense_control_and_same_frozen_Uniform_parent(self):
        card=build(self.parent)
        self.assertEqual(card['roles']['D20_CONTROL']['policy']['counts']['D'],20)
        self.assertEqual(card['roles']['UNIFORM19_C']['policy']['counts']['D'],19)
        self.assertNotIn('D8_CONTROL',card['roles'])
        self.assertFalse(card['GPU_authorized'])
        self.assertFalse(card['GPU_dispatch_ready'])
        self.assertFalse(card['consumer_predictions_are_actual_results'])

    def test_old_original_scope_missing_native_or_wrong_point_refused(self):
        with self.assertRaisesRegex(ValueError,'not reusable'):validate(original(self.parent),self.parent)
        for change in (lambda c:c.update(target_update=8),lambda c:c['physical_matrix'].pop(),
                       lambda c:c.update(GPU_authorized=True)):
            card=build(self.parent);change(card)
            with self.assertRaisesRegex(ValueError,'Exact new point20'):validate(card,self.parent)


if __name__=='__main__':unittest.main()
