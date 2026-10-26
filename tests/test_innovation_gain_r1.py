import copy
from dataclasses import replace
import unittest

import numpy as np
import torch

from test_scout_readout_v22 import fixture, ROOT
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.innovation_gain_r1 import InnovationGainKernel, project_spatial_blocks, gain_proposal
from wcomr.innovation_gain_fit_r1 import output_moments, calibration, fit, box_quadratic
from wcomr.scout_readout_v22 import UnsupportedReadout, proposal


def kernel_for(base, gains):
    # Reuse the exact source-bound WC/RF adapters from the existing fixture.
    k = copy.copy(base)
    k.__class__ = InnovationGainKernel
    k.gains = tuple(gains)
    return k


class InnovationTests(unittest.TestCase):
    def test_projection_partial_boundary_and_axes(self):
        g = torch.Generator().manual_seed(20261027)
        for h,w in ((7,9),(1,3),(2,2),(3,1)):
            x = torch.randn(2,3,h,w,4,generator=g,dtype=torch.float64)
            low = project_spatial_blocks(x)
            oracle = torch.empty_like(x)
            for i in range(0,h,2):
                for j in range(0,w,2):
                    oracle[:,:,i:i+2,j:j+2,:] = x[:,:,i:i+2,j:j+2,:].mean((2,3),keepdim=True)
            self.assertTrue(torch.allclose(low,oracle,atol=1e-14,rtol=0))
            self.assertTrue(torch.allclose(project_spatial_blocks(low),low,atol=1e-14,rtol=0))
            self.assertLess(abs(float((low*(x-low)).sum())),1e-12)
            constant = torch.arange(24,dtype=torch.float64).reshape(2,3,1,1,4).expand_as(x)
            self.assertTrue(torch.equal(project_spatial_blocks(constant),constant))

    def test_actual_adapter_endpoints_all_states_and_flows(self):
        for flow in (False,True):
            for step in (22,23,25,33,34,35):
                k,a = fixture(flow,step)
                for gains,label in (((0.,0.),'FULL'),((1.,1.),'R4_GLOBAL')):
                    actual = kernel_for(k,gains).evaluate_gain(**a)
                    reference = k.evaluate(label,**a)
                    for x,y in zip(actual['outputs'],reference['outputs']):
                        self.assertTrue(torch.equal(x,y))
                    self.assertEqual(actual['alpha'],1. if step < 25 else .5)

    def test_true_band_response_and_failure_isolation(self):
        for flow in (False,True):
            k,a = fixture(flow)
            k = kernel_for(k,(.2,.8))
            state = CompleteStateRoundtrip(k.net,k.model.sample_scheduler,a['pair_inputs'][1])
            before = state.fingerprint()
            first = k.evaluate_gain(**a)
            self.assertEqual(state.fingerprint(),before)
            second = k.evaluate_gain(**a)
            self.assertTrue(all(torch.equal(x,y) for x,y in zip(first['outputs'],second['outputs'])))
            def fail(*args,**kwargs):
                k.net.audit_buffer.add_(2)
                k.model.sample_scheduler.history.append(torch.rand(2))
                raise OSError('IG injected head failure')
            k.net.final_layer.forward = fail
            with self.assertRaisesRegex(OSError,'IG injected'):
                k.evaluate_gain(**a)
            self.assertEqual(state.fingerprint(),before)

    def test_raw_identity_and_equal_gain_scalar(self):
        k,a = fixture();old,last = a['anchors'][0]
        torch.manual_seed(19)
        old = replace(old,probe=torch.randn_like(old.probe),residual=torch.randn_like(old.residual))
        last = replace(last,probe=torch.randn_like(last.probe),residual=torch.randn_like(last.residual))
        p = torch.randn_like(old.probe)
        full = proposal('FULL',p,old,last,kappa=1.4,age=3)[0]
        nu = p-(last.probe+1.4*(last.probe-old.probe))
        result = gain_proposal(p,old,last,ratio=1.4,gains=(.37,.37),age=3)
        self.assertTrue(torch.equal(result,full+.37*nu))
        with self.assertRaises(UnsupportedReadout):
            gain_proposal(p,old,last,ratio=1.4,gains=(float('nan'),.5),age=3)

    def test_cross_gram_known_gain_and_actual_nonlinearity(self):
        rng = np.random.default_rng(3)
        u = rng.normal(size=1000); v = .7*u+rng.normal(size=1000)
        zero = np.zeros_like(u);target=.3*u+.8*v
        m = output_moments(target,zero,u,v,u+v,.5*(u+v))
        self.assertGreater(m['G'][0][1],.5)
        # Zero-ridge solution is independently identifiable; regularized fit
        # must move toward its train-only scalar prior.
        optimum = box_quadratic(np.asarray(m['G'])[:2,:2],np.asarray(m['b'])[:2])
        np.testing.assert_allclose(optimum,[.3,.8],atol=1e-12)
        nonlinear = output_moments(target,zero,u,v,u+v+u*v,.5*(u+v)+.25*u*v)
        self.assertGreater(nonlinear['interaction_MSE'],.1)
        self.assertLess(nonlinear['midpoint_bilinear_error_MSE'],1e-30)

    def test_prompt_holdout_no_teacher_leakage(self):
        def rows(gain_b):
            result=[]
            for prompt,gain in (('A',.2),('B',gain_b)):
                for step in (22,23):
                    u=np.array([1.,2.,3.]);v=np.array([2.,-.5,1.]);z=np.zeros(3)
                    result.append(dict(prompt=prompt,step=step,moments=output_moments(gain*(u+v),z,u,v,u+v,.5*(u+v))))
            return result
        first = calibration(rows(.8),('A','B'),(22,23))
        second = calibration(rows(.05),('A','B'),(22,23))
        # B's teachers cannot influence a coefficient trained only on A.
        self.assertEqual(first['folds'][1]['coefficients'],second['folds'][1]['coefficients'])
        self.assertFalse(first['deployable'])
        with self.assertRaises(ValueError):calibration(rows(.8)[:-1],('A','B'),(22,23))

    def test_scalar_failure_does_not_veto_band(self):
        z=np.zeros(2);u=np.array([1.,0.]);v=np.array([0.,1.]);target=np.array([1.,-1.])
        m=output_moments(target,z,u,v,u+v,.5*(u+v))
        f=fit([dict(prompt='A',step=22,moments=m)])
        self.assertEqual(f['IG_SCALAR'],[0.,0.])
        self.assertLess(f['surrogate_loss']['IG_BAND'],f['surrogate_loss']['IG_SCALAR'])


if __name__ == '__main__':unittest.main()
