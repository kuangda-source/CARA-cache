"""Analytic tiny CPU controls, not actual saved warm trajectories."""
import copy
import unittest
import torch

from wcomr.drop1_warm21_analysis_r1 import compare_round, METHODS


def fixture():
    tensors = {m: [torch.full((1, 2), 2.) for _ in range(36)] for m in METHODS}
    tensors['S25-C'][20] = torch.full((1, 2), 4.)
    tensors['S25-A'][20] = torch.full((1, 2), 3.)
    rows = {m: dict(scene='SYNTHETIC_NOT_REAL_CAL', round=1, method=m,
        scheduler_timesteps=list(range(36)), actions=['DD'] * 36) for m in METHODS}
    for m in ('S25-C', 'S25-A'):
        rows[m]['actions'][20] = 'CC'
    return tensors, rows


class SavedWarm21Controls(unittest.TestCase):
    def evaluate(self, x, rows, **kw):
        return compare_round(x, rows, expected_shape=(1, 2), torch=torch,
                             validated_same_input=kw.get('validated_same_input', True))

    def test_analytic_errors_index21_FP64_no_double_CFG_or_propagation_gain(self):
        x, rows = fixture()
        x['S25-A'][21] = torch.full((1, 2), 1000.)
        out = self.evaluate(x, rows)
        self.assertTrue(out['same_state_verified'])
        self.assertEqual((out['absolute_guided_MSE_C'], out['absolute_guided_MSE_A']), (4., 1.))
        self.assertEqual(out['reference_energy'], 4.)
        self.assertEqual(out['relative_guided_MSE_A'], .25)
        self.assertEqual(out['A_over_C_when_C_positive'], .25)
        self.assertEqual(out['local_MSE_reduction_fraction'], .75)
        self.assertFalse(out['CFG_or_propagation_gain_applied_again'])

    def test_prefix_input_time_and_action_mismatch_cannot_create_same_state_labels(self):
        for kind in ('prefix', 'input', 'time', 'round', 'scene_missing', 'method', 'reference_action', 'student_action'):
            with self.subTest(kind=kind):
                x, rows = fixture(); kw = {}
                if kind == 'prefix': x['S25-A'][19].add_(1)
                elif kind == 'input': kw['validated_same_input'] = False
                elif kind == 'time': rows['S25-C']['scheduler_timesteps'][20] += 1
                elif kind == 'round': rows['S25-A']['round'] = 2
                elif kind == 'scene_missing':
                    for m in METHODS: rows[m].pop('scene')
                elif kind == 'method': rows['S25-A']['method'] = 'S25-C'
                elif kind == 'reference_action': rows['S26-C']['actions'][20] = 'CC'
                else: rows['S25-A']['actions'][20] = 'DD'
                out = self.evaluate(x, rows, **kw)
                self.assertFalse(out['same_state_verified'])
                self.assertIsNone(out['absolute_guided_MSE_A'])

    def test_zero_denominators_are_unknown_ratios_not_zero_gain_claims(self):
        x, rows = fixture()
        for m in METHODS: x[m][20].zero_()
        out = self.evaluate(x, rows)
        self.assertEqual(out['absolute_guided_MSE_C'], 0.)
        for key in ('relative_guided_MSE_C', 'A_over_C_when_C_positive', 'local_MSE_reduction_fraction'):
            self.assertIsNone(out[key])

    def test_worse_correction_retains_negative_improvement(self):
        x, rows = fixture(); x['S25-A'][20].fill_(5.)
        out = self.evaluate(x, rows)
        self.assertEqual(out['A_over_C_when_C_positive'], 2.25)
        self.assertEqual(out['local_MSE_reduction_fraction'], -1.25)

    def test_short_shape_or_nonfinite_payload_refused_and_inputs_unmodified(self):
        x, rows = fixture(); before = copy.deepcopy(x)
        self.evaluate(x, rows)
        self.assertTrue(all(torch.equal(a, b) for m in METHODS for a, b in zip(x[m], before[m])))
        for kind in ('short', 'shape', 'nan', 'integer'):
            with self.subTest(kind=kind):
                x, rows = fixture()
                if kind == 'short': x['S25-A'].pop()
                elif kind == 'shape': x['S25-A'][20] = torch.zeros(3)
                elif kind == 'integer': x['S25-A'][20] = torch.zeros((1, 2), dtype=torch.int64)
                else: x['S25-A'][20].fill_(float('nan'))
                with self.assertRaises(ValueError): self.evaluate(x, rows)


if __name__ == '__main__':
    unittest.main()
