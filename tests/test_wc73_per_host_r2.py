import copy,tempfile,unittest
from pathlib import Path
from wcomr.wc73_execution_r1 import Pool,admit_host,RUN
from wcomr.gpu_budget_pool_v2 import atomic_json
class Tests(unittest.TestCase):
 def value(self,host='two_card'):
  v=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=173.2,origin_gpu_jobs_launched=0,events=[],jobs={'other':dict(status='RESERVED_OR_RUNNING',host=host,gpu_uuid='GPU-other',billed_limit_GPUh=3,launch_id='immutable-other')})
  v.update(Pool.accounting(v));return v
 def test_real_reserve_and_phase_settle_preserve_other_host(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'reports').mkdir();v=self.value();atomic_json(root/'reports/gpu-budget-v2.json',v);p=Pool(root)
   j=dict(job_id=RUN,host='four_card',gpu_uuid='GPU-own',billed_limit_GPUh=12,forecast_GPUh=9.51)
   p.reserve(j,dict(uuid='GPU-own',name='RTX 6000 Ada',compute_cap='8.9',memory_used_mib=23,pids=[]))
   self.assertEqual(p.read()['reserved_gpu_hours'],15)
   p.finish_A(2,'a'*64,True);admit_host(p.read(),'four_card',exclude=RUN);p.settle(RUN,3,'b'*64)
   self.assertEqual(p.read()['jobs']['other'],v['jobs']['other']);self.assertEqual(p.read()['reserved_gpu_hours'],3)
 def test_same_host_and_unknown_host_block(self):
  for h in ['four_card',None,'unknown']:
   with self.assertRaises(ValueError):admit_host(self.value(h),'four_card')
 def test_two_jobs_on_other_host_block(self):
  v=self.value();v['jobs']['second']=copy.deepcopy(v['jobs']['other'])
  with self.assertRaises(ValueError):admit_host(v,'four_card')
 def test_b_excludes_only_own_original(self):
  v=self.value();v['jobs'][RUN]=dict(status='RESERVED_OR_RUNNING',host='four_card')
  self.assertTrue(admit_host(v,'four_card',exclude=RUN))
  with self.assertRaises(ValueError):admit_host(v,'four_card')
 def test_both_host_directions(self):
  self.assertTrue(admit_host(self.value('four_card'),'two_card'))
 def test_budget_still_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'reports').mkdir();v=self.value();v['cap_gpu_hours']=180;v.update(Pool.accounting(v));atomic_json(root/'reports/gpu-budget-v2.json',v)
   with self.assertRaises(ValueError):Pool(root).reserve(dict(job_id=RUN,host='four_card',gpu_uuid='GPU-own',billed_limit_GPUh=12,forecast_GPUh=9.51),dict(uuid='GPU-own',name='RTX 6000 Ada',compute_cap='8.9',memory_used_mib=23,pids=[]))
if __name__=='__main__':unittest.main()
