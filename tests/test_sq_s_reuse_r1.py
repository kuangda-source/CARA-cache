import ast
import copy
import hashlib
from pathlib import Path
import unittest

import torch

from wcomr.sq_s_batch_r1 import tensor_signature
from wcomr.sq_s_reuse_r1 import tensor_bridge, trajectory_bridge

# Exercise the retained producer's actual digest function without importing
# its unrelated generation/scoring modules into this data-only CPU audit.
source = Path(__file__).resolve().parents[1]/'src/wcomr/policy_generator_r1/dev128_collection.py'
function = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == 'tensor_digest')
namespace = dict(hashlib=hashlib)
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
tensor_digest = namespace['tensor_digest']


class LegacyBridge(unittest.TestCase):
    def test_both_original_conventions(self):
        for dtype in (torch.float32, torch.bfloat16):
            value = torch.arange(24).reshape(1, 2, 3, 4).to(dtype).transpose(2, 3)
            old = tensor_digest(value)
            result = tensor_bridge(value, old)
            self.assertEqual(result['legacy_raw_bytes'], old)
            self.assertEqual(result['S_typed_tensor'], tensor_signature(value))
            self.assertNotEqual(old['sha256'], result['S_typed_tensor']['sha256'])

    def test_same_bytes_different_geometry_refused(self):
        value = torch.arange(24.).reshape(1, 2, 3, 4)
        with self.assertRaises(ValueError):
            tensor_bridge(value.reshape(1, 2, 4, 3), tensor_digest(value))

    def test_changed_value_refused(self):
        value = torch.zeros(1, 2, 3, 4)
        reference = tensor_digest(value)
        value[0, 0, 0, 0] = 1
        with self.assertRaises(ValueError):
            tensor_bridge(value, reference)

    def test_nonfinite_original_refused(self):
        value = torch.full((1, 1, 1, 1), float('nan'))
        with self.assertRaises(ValueError):
            tensor_bridge(value, tensor_digest(value))

    def test_full_trajectory_and_short_payload(self):
        guided = [torch.full((1, 1, 1, 1), float(t)) for t in range(36)]
        checks = dict(guided_steps=36, guided_tensors=[tensor_digest(t) for t in guided],
                      latent_tensor=tensor_digest(guided[-1]))
        result = trajectory_bridge(guided, guided[-1], checks)
        self.assertEqual(len(result['guided']), 36)
        with self.assertRaises(ValueError):
            trajectory_bridge(guided[:-1], guided[-1], checks)
        changed = copy.deepcopy(checks)
        changed['guided_tensors'][17] = changed['guided_tensors'][16]
        with self.assertRaises(ValueError):
            trajectory_bridge(guided, guided[-1], changed)


if __name__ == '__main__':
    unittest.main()
