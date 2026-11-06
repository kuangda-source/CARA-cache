import unittest
from unittest.mock import patch
import torch
from wcomr.scout_cfg_common_proposal_r1 import common_long_proposal
from wcomr.scout_common_long_r1 import CommonLongKernel
from wcomr.scout_readout_v22 import ScoutReadoutKernel,Anchor,PARENT_FINGERPRINT

class ReadoutTests(unittest.TestCase):
 def test_short_never_evaluates_extrapolator(self):
  x=torch.ones(1,2,1,2,2);context=('r','weights',PARENT_FINGERPRINT)
  anchors=tuple(tuple(Anchor(context,b,s,xi,x,x) for s,xi in [(20,.2),(21,.3)]) for b in (0,1))
  value={'outputs':(x,x),'component_outputs':(x,x),'alpha':1}
  with patch.object(ScoutReadoutKernel,'evaluate',return_value=value) as parent:
   out=CommonLongKernel.__new__(CommonLongKernel).evaluate('R4_COMMON_LONG',context=context,step=22,xi=.4,anchors=anchors)
  self.assertEqual(parent.call_count,1);self.assertEqual(parent.call_args.args[0],'A_PHASE')
  self.assertTrue(torch.equal(out['outputs'][0],x))
 def test_common_increment_cancels_in_cfg_difference(self):
  torch.manual_seed(29);pairs=[tuple(torch.randn(1,2,1,2,2) for _ in range(2)) for _ in range(3)]
  c,a,r=pairs
  from wcomr.cfg_guided_w1_outputs import shared_output_fusion
  base=shared_output_fusion(c,a,.5)
  out=common_long_proposal(C=c,A_component=a,R4_component=r,step=34,anchor_step=30)
  torch.testing.assert_close(out[0]-out[1],base[0]-base[1],atol=1e-6,rtol=1e-6)
 def test_invalid_identity_and_nonfinite_rejected(self):
  x=torch.ones(1,2,1,2,2);pair=(x,x)
  for step,anchor in [(30,27),(34,27),(22,22)]:
   with self.assertRaises(ValueError):common_long_proposal(C=pair,A_component=pair,R4_component=pair,step=step,anchor_step=anchor)
  bad=(x*float('nan'),x)
  with self.assertRaises(ValueError):common_long_proposal(C=pair,A_component=pair,R4_component=bad,step=34,anchor_step=30)
if __name__=='__main__':unittest.main()
