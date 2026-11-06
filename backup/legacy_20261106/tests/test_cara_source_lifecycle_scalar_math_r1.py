"""Preserve the original RF arithmetic order and the branch-pair interface."""
import unittest

import torch

from wcomr.cara_source_lifecycle_scalar_collection_r1 import guided_output


class ScalarMath(unittest.TestCase):
    def test_original_fp32_cfg_order_then_fp64_difference(self):
        conditional = torch.tensor([1.e8, 1.0000001, -3.14, 2.71828], dtype=torch.float32)
        unconditional = torch.tensor([1.e8+8., -.3333333, 2.71, 1.e-7], dtype=torch.float32)
        pair = conditional, unconditional
        actual = guided_output(pair)
        expected = conditional+7*(conditional-unconditional)
        self.assertTrue(torch.equal(actual, expected))
        self.assertEqual(actual.dtype, torch.float32)
        self.assertIs(pair[0], conditional)
        self.assertIs(pair[1], unconditional)
        self.assertFalse(torch.equal(actual, 8*conditional-7*unconditional))

    def test_branch_pair_dtype_shape_and_both_conditions_required(self):
        one = torch.ones(4, dtype=torch.float32)
        for pair in (one, (one,), (one.double(), one), (one, one[:2])):
            with self.assertRaises(ValueError):
                guided_output(pair)


if __name__ == '__main__':
    unittest.main()
