import unittest

import torch

from wcomr.p_acr_history_diff_r1 import PastCFGDelta


class TestPastCFGComparator(unittest.TestCase):
    def test_shared_drift_is_exact_for_both_directions(self):
        with torch.no_grad():
            past=(torch.tensor([1.,3.]),torch.tensor([.5,1.]));true=(past[0]+2,past[1]+2)
            history=PastCFGDelta.from_actual_DD(context=('p',0),step=7,pair=past,semantic_action='DD',diagnostic_only=False)
            c=history.readout(true[0],context=('p',0),step=12,direction='Pc')
            u=history.readout(true[1],context=('p',0),step=12,direction='Pu')
            self.assertTrue(all(torch.equal(a,b) for a,b in zip(c,true)))
            self.assertTrue(all(torch.equal(a,b) for a,b in zip(u,true)))

    def test_shadow_or_approximate_pairs_do_not_promote_history(self):
        pair=(torch.ones(2),torch.zeros(2))
        for action,diagnostic in (('DD',True),('PP',False),('Pc',False),('CC',False)):
            with self.assertRaises(ValueError):PastCFGDelta.from_actual_DD(context=('p',0),step=7,pair=pair,semantic_action=action,diagnostic_only=diagnostic)

    def test_current_or_other_context_is_rejected(self):
        history=PastCFGDelta.from_actual_DD(context=('p',0),step=7,pair=(torch.ones(2),torch.zeros(2)),semantic_action='DD',diagnostic_only=False)
        with self.assertRaises(ValueError):history.readout(torch.ones(2),context=('other',0),step=8,direction='Pc')
        with self.assertRaises(ValueError):history.readout(torch.ones(2),context=('p',0),step=7,direction='Pc')


if __name__=='__main__':unittest.main()
