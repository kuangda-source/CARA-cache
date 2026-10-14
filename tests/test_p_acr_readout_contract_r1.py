from types import SimpleNamespace
import unittest

import torch

from wcomr.p_acr_readout_r1 import ACRReadoutExecutor, compensate


class TestACRContract(unittest.TestCase):
    def test_guided_innovation_formula_independent_of_branch_formula(self):
        a=(torch.tensor([1.,2.]),torch.tensor([.3,.7]));d=torch.tensor([1.4,1.8])
        for direction,coef in (('Pc',1.4),('Pu',.7)):
            pair=compensate(a,d,direction=direction,coefficient=coef)
            old=8*a[0]-7*a[1]
            delta=d-a[0 if direction=='Pc' else 1]
            expected=old+((8-7*coef) if direction=='Pc' else (8*coef-7))*delta
            self.assertTrue(torch.allclose(8*pair[0]-7*pair[1],expected,rtol=1e-6,atol=1e-6))

    def test_layout_precision_and_nonfinite_coefficient_rejected(self):
        a=(torch.ones(2),torch.zeros(2))
        for value in (torch.ones(3),torch.ones(2,dtype=torch.float64)):
            with self.assertRaises(ValueError):compensate(a,value,direction='Pc',coefficient=1.)
        with self.assertRaises(ValueError):compensate(a,torch.ones(2),direction='Pu',coefficient=float('nan'))

    def test_cold_sources_are_rejected_before_compilation_or_forward(self):
        net=SimpleNamespace(cnt=22,worldcache_num_steps=70,worldcache_ret_ratio=.2,
            previous_input=[None,None],previous_internal_states=[None,None],residual_cache=[None,None],probe_residual_cache=[None,None])
        model=SimpleNamespace(net=net)
        with self.assertRaisesRegex(ValueError,'before any model execution'):
            ACRReadoutExecutor(model,runtime='unavailable-must-not-be-opened',wc=None,rf=None,context=('p',0),dense=[None,None],
                working=[{'kind':'D','created_step':11}]*2,gamma=.7,direction='Pu',coefficient=.8,step=12)


if __name__=='__main__':unittest.main()
