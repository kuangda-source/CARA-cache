"""Scientific controls for the bounded noncausal scene-scale closeout."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_cara_l1_scene_scale_closeout_20261023 import (
    scene_summary,scalar_predict,fit_scene_only,decompose)


class SceneScaleControls(unittest.TestCase):
    def test_recovers_pure_scene_scale_and_preserves_ranks(self):
        curve=np.array([1.,-.3,.2,2.])
        g=np.array([-1.,0.,1.])
        y=curve[None,:]+.6*g[:,None]
        base,pred,fit=scalar_predict(y,g,2.,0.)
        np.testing.assert_allclose(pred,curve+1.2,atol=1e-12)
        np.testing.assert_array_equal(np.argsort(pred),np.argsort(base))

    def test_constant_scene_summary_cannot_manufacture_signal(self):
        y=np.array([[1.,2.],[3.,4.],[5.,6.]])
        b,p,fit=scalar_predict(y,np.ones(3),7.,0.)
        np.testing.assert_array_equal(b,p)
        self.assertEqual(fit['slope'],0.)

    def test_outer_labels_are_not_needed_for_nested_predictions(self):
        g=np.array([-1.,0.,1.,2.])
        y=np.arange(6)[None,:]+g[:,None]*.4
        b,p,f=fit_scene_only(y[:3],g[:3],g[3],[0.,1.])
        y[3]+=999
        bb,pp,ff=fit_scene_only(y[:3],g[:3],g[3],[0.,1.])
        np.testing.assert_array_equal(p,pp)
        self.assertEqual(f,ff)
        self.assertTrue(all(len(r['inner_losses'])==3 for r in f['inner_selection']))

    def test_exact_loss_decomposition_and_oracle_offset(self):
        truth=np.array([1.,4.,2.]);pred=np.array([2.,2.,4.])
        d=decompose(truth,pred)
        oracle=decompose(truth,pred-d['mean_log_error'])
        self.assertAlmostEqual(d['log_MSE'],d['squared_mean_log_error']+d['centered_log_error_MSE'])
        self.assertAlmostEqual(oracle['log_MSE'],d['best_constant_offset_oracle_log_MSE'])

    def test_literal_mean_is_rms_mean_not_mean_log(self):
        q=np.log(np.array([[1.,9.,25.],[4.,16.,36.]]))
        np.testing.assert_allclose(scene_summary(q,'log_mean_RMS'),np.log([3.,4.]))
        np.testing.assert_allclose(scene_summary(q,'mean_log_d2'),q.mean(axis=1))


if __name__=='__main__':unittest.main()
