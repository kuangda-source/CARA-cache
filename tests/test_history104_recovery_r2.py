import copy,json,tempfile,unittest,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from wcomr.history104_failure_recovery_r1 import classify,reconstruction,settle_reconstructed
from wcomr.gpu_budget_pool_v2 import BudgetPool,atomic_json

class Recovery(unittest.TestCase):
 def setUp(self):
  self.c=json.loads((Path(__file__).resolve().parents[1]/'reports/cara_history104_failed_terminal_repaired_capture_20261024.json').read_text());self.c.pop('reconstruction',None)
 def test_original_estimate(self):
  r=reconstruction(self.c);self.assertEqual(r['charge_GPUh'],5.48);self.assertIsNone(r['exact_actual_GPUh']);self.assertFalse(r['full_protocol_accepted'])
 def test_failure_is_not_unknown(self):
  self.assertEqual(classify(self.c['container_state'],self.c['live_handles']),'FAILED_ORIGINAL_TERMINAL')
 def test_live_refused(self):
  self.c['live_handles']['runner']=True
  with self.assertRaises(ValueError):reconstruction(self.c)
 def test_existing_bill_refused(self):
  self.c['original_billing_exists']=True
  with self.assertRaises(ValueError):reconstruction(self.c)
 def test_changed_identity_refused(self):
  self.c['registration_sha256']='bad'
  with self.assertRaises(ValueError):reconstruction(self.c)
 def test_clock_drift_refused(self):
  self.c['monitor_summary']['clock_offset_span_seconds']=5
  with self.assertRaises(ValueError):reconstruction(self.c)
 def test_zero_exit_is_not_acceptance(self):
  self.assertEqual(classify(dict(Running=False,ExitCode=0),{}),'EXITED_ZERO_REQUIRES_FULL_ACCEPTANCE')
 def test_accounting_idempotent_and_legacy_readable(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);pool=BudgetPool(root);before=copy.deepcopy(self.c['pool']);atomic_json(pool.path,before);r=reconstruction(self.c)
   after=settle_reconstructed(pool,r,'a'*64);again=settle_reconstructed(pool,r,'a'*64)
   self.assertEqual(after,again);self.assertEqual(pool.read(),after)
   self.assertAlmostEqual(after['used_gpu_hours']-before['used_gpu_hours'],5.48)
   self.assertAlmostEqual(before['reserved_gpu_hours']-after['reserved_gpu_hours'],11.9)
   self.assertEqual(before['cap_gpu_hours'],after['cap_gpu_hours'])
   others={k:v for k,v in before['jobs'].items() if k!=r['run_id']};self.assertEqual(others,{k:v for k,v in after['jobs'].items() if k!=r['run_id']})
   with self.assertRaises(ValueError):settle_reconstructed(pool,r,'b'*64)
 def test_oversized_charge_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   pool=BudgetPool(tmp);atomic_json(pool.path,self.c['pool']);r=reconstruction(self.c);r['charge_GPUh']=12
   with self.assertRaises(ValueError):settle_reconstructed(pool,r,'a'*64)
if __name__=='__main__':unittest.main()
