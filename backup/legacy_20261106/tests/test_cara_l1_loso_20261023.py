"""Leakage, conditional-null and decision-accounting controls for offline L1."""
from pathlib import Path
import sys
import unittest
import itertools
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_cara_l1_loso_20261023 import fit_predict, predict_fold, evaluate, refresh
from audit_cara_l1_loso_20261023 import constrained_choice


class L1Controls(unittest.TestCase):
    def setUp(self):
        self.grid = [(s,t) for t in range(10,16) for s in range(7,t)]
        n = len(self.grid)
        self.q = np.array([np.linspace(-1,1,n)+a for a in (-.6,.1,.5,1.)])
        self.y = np.stack([np.exp(.7*self.q + b) for b in (0.,-.2,.2)], axis=-1)

    def test_exact_conditional_signal_generalizes(self):
        baseline, pred, _ = fit_predict(self.y[:3,:,0], self.q[:3], self.q[3], self.grid, 'log', 0.)
        np.testing.assert_allclose(pred,self.y[3,:,0],rtol=1e-10)
        self.assertGreater(np.mean((baseline-self.y[3,:,0])**2),.01)

    def test_time_age_only_signal_is_conditional_null(self):
        q = np.tile(np.arange(len(self.grid)),(3,1)).astype(float)
        for mode in ('log','relative'):
            b,p,_ = fit_predict(self.y[:3,:,0],q,q[0]+5,self.grid,mode,0.)
            np.testing.assert_array_equal(b,p)

    def test_no_held_out_label_leakage(self):
        y = self.y.copy()
        b,p,f = predict_fold(y[:3],self.q[:3],self.q[3],self.grid,'log',[0.,1.])
        y[3] *= 1e8
        bb,pp,ff = predict_fold(y[:3],self.q[:3],self.q[3],self.grid,'log',[0.,1.])
        np.testing.assert_array_equal(p,pp)
        self.assertEqual(f,ff)
        self.assertEqual(len(f[0]['inner_selection'][0]['inner_scores']),3)

    def test_shift_of_q_by_cell_cancels_exactly(self):
        shift = np.linspace(1,2,len(self.grid))
        for mode in ('log','relative'):
            _,p,_ = fit_predict(self.y[:3,:,0],self.q[:3],self.q[3],self.grid,mode,.1)
            _,pp,_ = fit_predict(self.y[:3,:,0],self.q[:3]+shift,self.q[3]+shift,self.grid,mode,.1)
            np.testing.assert_allclose(p,pp,rtol=1e-10)

    def test_oracle_regret_and_equal_refresh_quota(self):
        y = self.y[3]
        e = evaluate(y,y,self.grid,[.25])
        self.assertAlmostEqual(e['action_choice']['regret'],0.)
        oracle = refresh(y[:,0],y[:,0],self.grid,.25)
        bad = refresh(y[:,0],-y[:,0],self.grid,.25)
        self.assertEqual(oracle['hypothetical_D_cells'],bad['hypothetical_D_cells'])
        self.assertAlmostEqual(oracle['regret'],0.)
        self.assertGreater(bad['regret'],0.)

    def test_none_lambda_is_exact_baseline(self):
        for mode in ('log','relative'):
            b,p,_=fit_predict(self.y[:3,:,0],self.q[:3],self.q[3],self.grid,mode,None)
            np.testing.assert_array_equal(b,p)

    def test_equal_counts_assignment_matches_exhaustive_oracle(self):
        costs = np.array([[2.,1.,6.],[1.,7.,3.],[5.,4.,2.],[3.,2.,1.]])
        counts = [1,2,1]
        action = constrained_choice(costs,counts)
        candidates = set(itertools.permutations([0,1,1,2]))
        best = min(sum(costs[i,a] for i,a in enumerate(v)) for v in candidates)
        self.assertAlmostEqual(sum(costs[i,a] for i,a in enumerate(action)),best)
        self.assertEqual(np.bincount(action,minlength=3).tolist(),counts)

    def test_invalid_action_denominator_is_rejected(self):
        with self.assertRaises(ValueError):
            constrained_choice(np.ones((4,3)),[1,1,1])


if __name__ == '__main__': unittest.main()
