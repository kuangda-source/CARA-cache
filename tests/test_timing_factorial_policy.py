"""Early/late intervention geometry and immutable original human design."""
import json
from pathlib import Path
import unittest

from wcomr.selective_refresh_policy import SparsePlacementPolicy, SparseRefreshPolicy
from wcomr.timing_factorial_policy import validate_timing_factorial


class TimingFactorialPolicyTests(unittest.TestCase):
    layers = (2, 3, 5)

    def policies(self, common=((4, 5, 6, 7, 8), (4, 5, 6, 7)),
                 both=((1, 4, 5, 6, 7, 8, 9), (1, 4, 5, 6, 7, 8))):
        return (SparseRefreshPolicy(self.layers, 2),
                SparsePlacementPolicy(self.layers, per_cfg_eligible_ordinals=common),
                SparsePlacementPolicy(self.layers, per_cfg_eligible_ordinals=both))

    def test_asymmetric_CFG_quotas(self):
        expected, factors = validate_timing_factorial(self.policies(), self.layers, [12, 10])
        self.assertEqual(expected, [[6, 5], [5, 4], [7, 6]])
        self.assertEqual(factors['early_eligible_ordinal_per_CFG'], [1, 1])
        self.assertEqual(factors['late_eligible_ordinal_per_CFG'], [9, 8])
        self.assertTrue(factors['varying_S_counts_are_not_matched_cost'])

    def test_frozen_human_missing_arms_match(self):
        manifest = json.loads((Path(__file__).parents[1] / 'manifests' /
            'wc_timing_factorial_draft_20261004.json').read_text())
        arms = {a['name']: a for a in manifest['arms']}
        layers = tuple(arms['E0L0']['policy']['sparse_layers'])
        selected = (SparseRefreshPolicy(layers, 2),) + tuple(
            SparsePlacementPolicy(layers, per_cfg_eligible_ordinals=tuple(
                tuple(v) for v in arms[name]['policy']['per_cfg_eligible_ordinals']))
            for name in ('E0L0', 'E1L1'))
        expected, _ = validate_timing_factorial(selected, layers, [12, 10])
        self.assertEqual(expected[1:], [arms[n]['source_replay']['S_per_CFG']
            for n in ('E0L0', 'E1L1')])
        self.assertEqual([sum(v) * len(layers) for v in expected], [253, 207, 299])
        self.assertFalse(manifest['GPU_submitted'])

    def test_reject_malformed_factor_interventions(self):
        baseline = self.policies()
        cases = {
            'mutable_container': list(baseline),
            'wrong_legacy_cadence': (SparseRefreshPolicy(self.layers, 1),) + baseline[1:],
            'periodic_new_arm': (baseline[0], SparseRefreshPolicy(self.layers), baseline[2]),
            'wrong_layers': (baseline[0], baseline[1],
                SparsePlacementPolicy((2, 3), per_cfg_eligible_ordinals=baseline[2].per_cfg_eligible_ordinals)),
            'wrong_common_quota': self.policies(common=((4, 5, 6, 7), (4, 5, 6, 7))),
            'wrong_both_quota': self.policies(both=((1, 4, 5, 6, 7, 8), (1, 4, 5, 6, 7, 8))),
            'common_contains_early': self.policies(common=((1, 5, 6, 7, 8), (4, 5, 6, 7))),
            'missing_early': self.policies(both=((2, 4, 5, 6, 7, 8, 9), (1, 4, 5, 6, 7, 8))),
            'late_before_common': self.policies(both=((1, 2, 4, 5, 6, 7, 8), (1, 4, 5, 6, 7, 8))),
            'common_not_subset': self.policies(both=((1, 4, 5, 6, 7, 9, 10), (1, 4, 5, 6, 7, 8))),
            'past_mask_range': self.policies(both=((1, 4, 5, 6, 7, 8, 13), (1, 4, 5, 6, 7, 8))),
            'CFG_swapped': self.policies(common=baseline[1].per_cfg_eligible_ordinals[::-1]),
        }
        for case, selected in cases.items():
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate_timing_factorial(selected, self.layers, [12, 10])

    def test_insufficient_or_invalid_mask(self):
        for counts in ([1, 1], [2, 2], [3, 2], [True, 10], [12, 0], [12], [12, 10, 8]):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                validate_timing_factorial(self.policies(), self.layers, counts)


if __name__ == '__main__':
    unittest.main()
