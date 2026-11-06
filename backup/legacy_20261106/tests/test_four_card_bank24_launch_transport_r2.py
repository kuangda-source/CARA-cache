import copy,json,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
from wc_four_card_bank24_launch_transport_r2 import bind,OLD,NEW
from wc_four_card_bank24_execution_r1 import REMOTE_LAUNCH

class TransportTests(unittest.TestCase):
 def setUp(self):
  p='reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_'
  self.L=json.loads(Path(p+'launch_20261022.json').read_text());self.A=json.loads(Path(p+'independent_acceptance_20261022.json').read_text())
 def test_exact_two_control_paths_and_every_other_byte_preserved(self):
  c=bind(REMOTE_LAUNCH,self.L,self.A);self.assertEqual(c.count(NEW),2);self.assertEqual(c.replace(NEW,OLD),REMOTE_LAUNCH)
 def test_reject_unaccepted_CPU(self):
  self.A['full_new_host_scope_production_CPU_accepted']=False
  with self.assertRaises(ValueError):bind(REMOTE_LAUNCH,self.L,self.A)
 def test_reject_wrong_target(self):
  self.L['target_stage']+='/../escape'
  with self.assertRaises(ValueError):bind(REMOTE_LAUNCH,self.L,self.A)
 def test_reject_wrong_source(self):
  self.A['source_revision']='different'
  with self.assertRaises(ValueError):bind(REMOTE_LAUNCH,self.L,self.A)
 def test_reject_missing_or_extra_literal(self):
  for c in [REMOTE_LAUNCH.replace(OLD,NEW,1),REMOTE_LAUNCH+'\n#'+OLD]:
   with self.assertRaises(ValueError):bind(c,self.L,self.A)
if __name__=='__main__':unittest.main()
