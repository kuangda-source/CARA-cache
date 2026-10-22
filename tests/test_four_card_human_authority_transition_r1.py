import copy,json,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1]/'src')]
from four_card_human_authority_transition_r1 import build,validate,QUOTE
from wcomr.gpu_budget_pool_v2 import BudgetPool

class TransitionTests(unittest.TestCase):
 def setUp(self):
  self.base=json.loads(Path('reports/wc_scout_BANK24_fresh_resource_20261020_1601.json').read_text())['remote']['pool']
  self.auth=dict(user_reply_quote=QUOTE,four_card_is_only_future_authorized_writer=True,two_card_future_dispatch_authority_revoked=True,two_card_remote_fence_observed=False,reset_history=False)
  self.route=dict(original_owned_client_exited=True,original_33620_has_no_listener=True,two_card_remote_commands=0,two_card_remote_fence_observed=False)
 def make(self):return build(self.base,self.auth,self.route,'four-card-human-retirement-test',1792654000.0,BudgetPool.accounting)
 def test_preserve_all_history_and_complete_uncertainty_reservations(self):
  before=copy.deepcopy(self.base);v=self.make();x=validate(self.base,v,BudgetPool.accounting)
  self.assertEqual(self.base,before);self.assertEqual(x['historical_jobs_preserved'],12);self.assertAlmostEqual(v['available_gpu_hours'],92.674976891229)
  self.assertEqual(v['used_gpu_hours'],before['used_gpu_hours']);self.assertEqual(v['reserved_gpu_hours'],16.5)
 def test_history_edit_rejected(self):
  v=self.make();next(iter(v['jobs'].values()))['actual_GPUh']=0
  with self.assertRaises(ValueError):validate(self.base,v,BudgetPool.accounting)
 def test_unknown_cost_cannot_be_zero_settlement(self):
  v=self.make();v['jobs']['retired-two-card-bank24-uncertainty-hold-20261022']['actual_GPUh']=0
  with self.assertRaises(ValueError):validate(self.base,v,BudgetPool.accounting)
 def test_old_active_snapshot_rejected(self):
  next(iter(self.base['jobs'].values()))['status']='RESERVED_OR_RUNNING'
  with self.assertRaises(ValueError):self.make()
 def test_missing_local_fence_rejected(self):
  self.route['original_owned_client_exited']=False
  with self.assertRaises(ValueError):self.make()
 def test_cannot_claim_remote_fence(self):
  self.auth['two_card_remote_fence_observed']=True
  with self.assertRaises(ValueError):self.make()
 def test_origin_cap_or_stored_total_drift_rejected(self):
  self.base['used_gpu_hours']-=1
  with self.assertRaises(ValueError):self.make()
 def test_missing_human_reassignment_rejected(self):
  self.auth['four_card_is_only_future_authorized_writer']=False
  with self.assertRaises(ValueError):self.make()

if __name__=='__main__':unittest.main()
