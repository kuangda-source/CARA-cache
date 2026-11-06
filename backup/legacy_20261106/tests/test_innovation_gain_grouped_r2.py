import copy,unittest
import torch
from test_scout_readout_v22 import fixture
from test_innovation_gain_r1 import kernel_for
from wcomr.scout_readout_v22 import LABELS
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.innovation_gain_grouped_r2 import GroupedScoutKernel,GroupedGainKernel,group,ACTIVE
class Grouped(unittest.TestCase):
 def test_all_labels_and_gains_exact_original(self):
  for flow in (False,True):
   for step in (22,23,25,33,34,35):
    original,args=fixture(flow,step)
    labels={label:original.evaluate(label,**args)['outputs'] for label in LABELS}
    gains={pair:kernel_for(original,pair).evaluate_gain(**args)['outputs'] for pair in ((0.,0.),(1.,1.),(1.,0.),(0.,1.),(.5,.5),(.2,.8))}
    k=copy.copy(original);k.__class__=GroupedScoutKernel
    with group(k.model,args) as audit:
     for label in LABELS:
      actual=k.evaluate(label,**args)
      self.assertTrue(all(torch.equal(a,b) for a,b in zip(actual['outputs'],labels[label])))
     k.__class__=GroupedGainKernel
     for pair,expected in gains.items():
      k.gains=pair;actual=k.evaluate_gain(**args)
      self.assertTrue(all(torch.equal(a,b) for a,b in zip(actual['outputs'],expected)))
     self.assertEqual(audit['points'],12)
 def test_failure_restores_buffers_solver_rng(self):
  k,args=fixture();k.__class__=GroupedGainKernel;k.gains=(.2,.8)
  snapshot=CompleteStateRoundtrip(k.net,k.model.sample_scheduler,args['pair_inputs'][1]);before=snapshot.fingerprint()
  def fail(*a,**kw):
   k.net.audit_buffer.add_(2);k.model.sample_scheduler.history.append(torch.rand(2));raise OSError('injected head')
  k.net.final_layer.forward=fail
  with self.assertRaisesRegex(OSError,'injected head'):
   with group(k.model,args):k.evaluate_gain(**args)
  self.assertEqual(snapshot.fingerprint(),before);self.assertIsNone(ACTIVE.get())
 def test_no_unaudited_call(self):
  k,args=fixture();k.__class__=GroupedScoutKernel
  with self.assertRaisesRegex(ValueError,'enclosing full audit'):k.evaluate('FULL',**args)
if __name__=='__main__':unittest.main()
