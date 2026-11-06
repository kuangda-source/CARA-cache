import contextlib,io,json,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wc_cara_ig_b1_capture_r1 as control
from wcomr.gpu_budget_pool_v2 import SCHEMA,atomic_json
from wcomr.innovation_gain_b1_card_r1 import RUN,ENVELOPE,COUNTS
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool
class Settlement(unittest.TestCase):
 def run_case(self,invalid=False):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);pool=HostBudgetPool(root)
   auth=dict(run_id=RUN,launch_id='new',source_revision='source',gpu_uuid='GPU-new',stage='stage',scope_counts=COUNTS,billed_limit_GPUh=1.5,host='two_card')
   job=dict(auth,status='RESERVED_OR_RUNNING');other=dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-old',billed_limit_GPUh=12.)
   original=dict(schema=SCHEMA,cap_gpu_hours=226,origin_used_gpu_hours=170.,origin_gpu_jobs_launched=10,jobs={ENVELOPE:job,'DEV128':other},events=[])
   original.update(pool.accounting(original));atomic_json(pool.path,original)
   bill=dict(auth,wall_seconds=360,actual_GPUh=.1);bill['launch_id']='wrong' if invalid else 'new'
   phase=dict(auth,status='SETTLED',actual_GPUh=.1,billing_sha256='a'*64)
   cap=dict(observed_unix=time.time(),files={'auth':dict(value=auth),'billing':dict(value=bill,sha256='a'*64)},terminal=True,UUID_lock_free=True,live_handles={'runner':False},GPU={'compute_apps':[]},private_pool={'jobs':{RUN:phase}})
   data=dict(source_stage=str(root),capture=cap,command='settle')
   source=control.CENTRAL.replace("'/data20t/gaokuangda/worldcache_workspace'",repr(str(root)))
   for repeat in range(2):
    with patch('sys.stdin',io.StringIO(json.dumps(data))),contextlib.redirect_stdout(io.StringIO()):
     if invalid:
      with self.assertRaises(AssertionError):exec(compile(source,'settlement-CPU-fixture','exec'),{})
     else:exec(compile(source,'settlement-CPU-fixture','exec'),{})
    result=pool.read()
    if invalid:self.assertEqual(result,original)
    else:
     self.assertEqual(result['used_gpu_hours'],170.1);self.assertEqual(result['reserved_gpu_hours'],12.)
     self.assertEqual(result['jobs']['DEV128'],other)
 def test_failed_science_still_settles_same_bill_once(self):self.run_case()
 def test_mismatched_original_rejected(self):self.run_case(True)
if __name__=='__main__':unittest.main()
