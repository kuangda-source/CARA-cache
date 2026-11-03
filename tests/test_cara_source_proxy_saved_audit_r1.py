"""Statistical and incomplete-data controls for a saved-data-only audit."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('saved_proxy_audit', ROOT/'scripts/audit_cara_source_proxy_saved_r1.py')
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class SavedProxyAudit(unittest.TestCase):
    def test_rank_direction_ties_and_undefined_constant(self):
        self.assertEqual(audit_module.spearman([1, 1, 3], [2, 2, 4]), 1.)
        self.assertEqual(audit_module.spearman([1, 2, 3], [3, 2, 1]), -1.)
        self.assertIsNone(audit_module.spearman([1, 1, 1], [1, 2, 3]))

    def test_rejects_partial_labels(self):
        summary = json.loads((ROOT/'reports/cara_v1_P1_successor_original_algorithm_summary_r1_20261103.json').read_text())
        partial = copy.deepcopy(summary)
        partial['source_labels']['rows'].pop()
        with self.assertRaisesRegex(ValueError, 'production64'):
            audit_module.audit(partial, {}, [])

    def test_reconstruction_uses_both_sources_and_frozen_weights(self):
        model = dict(coefficients=[0., 0., 0., 1., 0., 0., 1.])
        sigmas, weights = [1., .8, .6, .4, 0.], [0., 0., 2., 0.]
        first = audit_module.proxy([1, 2, 4], model, sigmas, weights, {(3,1,2)})
        self.assertAlmostEqual(first['cost'], .8)
        self.assertEqual(first['unseen_fraction'], 0.)
        self.assertEqual(first['zero_clamp_fraction'], 0.)


if __name__ == '__main__':
    unittest.main()
