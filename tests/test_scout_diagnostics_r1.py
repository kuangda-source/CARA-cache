"""Small analytic numerical controls; no real model or video claims."""
import unittest
import torch
from wcomr.scout_diagnostics_r1 import amplitude_and_direction, one_exchange, legal_mask, native_variation


class ScoutMath(unittest.TestCase):
    def test_interior_amplitude_and_input_immutability(self):
        c = torch.ones(1, 1, 1, 2, 2)
        phi = -c
        teacher = torch.zeros_like(c)
        result = amplitude_and_direction(c, phi, teacher, torch=torch)
        self.assertEqual(result['diagnostic_oracle_alpha_clipped'], .5)
        self.assertEqual(result['diagnostic_oracle_MSE'], 0.)
        self.assertEqual(result['q_parallel'], 1.)
        self.assertEqual(result['q_perpendicular'], 0.)
        self.assertTrue(torch.equal(c, torch.ones_like(c)))

    def test_worse_direction_and_zero_fallbacks(self):
        c = torch.ones(1, 1, 1, 2, 2)
        result = amplitude_and_direction(c, 2*c, torch.zeros_like(c), torch=torch)
        self.assertEqual(result['diagnostic_oracle_alpha_clipped'], 0.)
        result = amplitude_and_direction(c, c, c, torch=torch)
        self.assertTrue(result['zero_correction'])
        self.assertIsNone(result['diagnostic_oracle_alpha_unconstrained'])
        result = amplitude_and_direction(c*0, c, c*0, torch=torch)
        self.assertTrue(result['zero_visible_direction'])
        self.assertEqual(result['q_perpendicular'], result['q_Phi'])

    def test_orthogonal_projection_edges_and_bad_geometry(self):
        c = torch.tensor([1., -1., 1., -1.]).reshape(1, 1, 1, 2, 2)
        phi = torch.ones_like(c)
        result = amplitude_and_direction(c, phi, c*0, torch=torch)
        self.assertEqual(result['q_parallel'], 0.)
        self.assertEqual(result['q_perpendicular'], 1.)
        self.assertGreaterEqual(result['edge_weight_min'], .5)
        self.assertLessEqual(result['edge_weight_max'], 2.)
        with self.assertRaises(ValueError):
            amplitude_and_direction(c, phi.flatten(), c, torch=torch)
        with self.assertRaises(ValueError):
            amplitude_and_direction(c, phi*float('nan'), c, torch=torch)

    def test_single_exchange_quotas_protection_and_no_candidate(self):
        mask = ['D' if n <= 21 or n in (24, 27, 30, 33, 36) else 'C' for n in range(1, 37)]
        s = [1.] * 36
        self.assertFalse(one_exchange(s, mask)['changed'])
        s[22], s[20] = 3., .1
        r = one_exchange(s, mask)
        self.assertEqual((r['remove_D'], r['add_D']), (21, 23))
        self.assertEqual(r['D_count'], 26)
        self.assertTrue(legal_mask(r['mask']))
        bad = mask.copy(); bad[0] = 'C'
        self.assertFalse(legal_mask(bad))

    def test_variation_gain_exactly_once_and_not_geometric_curvature(self):
        g = [torch.full((1,1,1,2,2), float(i)) for i in range(36)]
        r = native_variation(g, [2.]*36, torch=torch)
        self.assertEqual(r['unweighted'][1:], [1.]*35)
        self.assertEqual(r['gain_squared_weighted'][1:], [4.]*35)
        self.assertFalse(r['geometric_curvature_or_optimal_schedule_claim'])


if __name__ == '__main__':
    unittest.main()
