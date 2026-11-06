import copy
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('scheduler_feasibility_analysis', Path(__file__).with_name('analyze.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AnalysisControls(unittest.TestCase):
    def test_orthogonal_known_effects(self):
        grid = [(7, 8), (7, 9), (8, 9), (7, 10)]
        cell = [-3., -1., 1., 3.]
        prompt = [-1., 1.]
        interaction = [[1., -1., -1., 1.], [-1., 1., 1., -1.]]
        y = [[cell[j]+prompt[i]+interaction[i][j] for j in range(4)] for i in range(2)]
        d = m.decompose(y, grid)
        self.assertAlmostEqual(d['cell_SS'], 40.)
        self.assertAlmostEqual(d['prompt_SS'], 8.)
        self.assertAlmostEqual(d['interaction_SS'], 8.)

    def test_known_additive_time_age_signal(self):
        grid = [(s, t) for t in range(8, 12) for s in range(7, t)]
        y = [[.2*t + .4*(t-s) for s, t in grid]]*4
        d = m.decompose(y, grid)
        self.assertAlmostEqual(d['additive_time_age_R2'], 1.)
        self.assertAlmostEqual(d['joint_cell_fraction'], 1.)
        self.assertAlmostEqual(d['interaction_SS'], 0.)

    def test_constant_data_is_undefined_not_perfect_R2(self):
        d = m.decompose([[2., 2.]]*4, [(7, 8), (7, 9)])
        self.assertIsNone(d['joint_cell_fraction'])
        self.assertIsNone(d['additive_time_age_R2'])

    def test_heldout_label_does_not_choose_its_shared_action(self):
        x = [[[1., 2., 3.]], [[2., 1., 3.]], [[2., 1., 3.]], [[2., 1., 3.]]]
        r = m.loo_actions(x, ['a', 'b', 'c', 'd'])['rows'][0]
        self.assertEqual(r['shared_local_MSE'], 2.)
        self.assertEqual(r['privileged_cellwise_oracle_local_MSE'], 1.)

    def test_exact_ties_keep_regret_range(self):
        x = [[[3., 1., 2.]], [[1., 1., 2.]], [[1., 1., 2.]], [[1., 1., 2.]]]
        r = m.loo_actions(x, ['a', 'b', 'c', 'd'])['rows'][0]
        self.assertEqual(r['mean_tied_choice_regret_range'], [0., 2.])
        self.assertEqual(r['best_set_overlap_fraction'], 1.)

    def test_missing_duplicate_and_false_history_rejected(self):
        cap = m.read(m.ROOT/m.CAPTURE)
        original = [r for r in cap['runner']['runs'] if r['section'] == 'FORMAL' and r['mode'] == 'COLLECT']
        scenes = [r['scene'] for r in original]
        grid = [(s, t) for t in range(8, 36) for s in range(7, t)]
        for mutation in ('missing', 'duplicate', 'history', 'nonpositive'):
            rows = copy.deepcopy(original)
            points = rows[0]['interval_cells']
            if mutation == 'missing': points.pop()
            elif mutation == 'duplicate': points[-1] = copy.deepcopy(points[0])
            elif mutation == 'history': points[0]['free_policy_history_truth'] = True
            else: points[0]['statistics']['e2'] = 0.
            with self.assertRaises(ValueError): m.validate_rows(rows, scenes, grid)


if __name__ == '__main__':
    unittest.main()
