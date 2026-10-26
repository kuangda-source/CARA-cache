import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

from wcomr.gpu_budget_pool_v2 import SCHEMA,atomic_json
from wcomr.innovation_gain_b1_card_r1 import PhaseBudgetPool,RUN,COUNTS

class Finance(unittest.TestCase):
 def test_phase_does_not_overwrite_running_main_ledger(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);stage=root/'stage';stage.mkdir();pool=PhaseBudgetPool(root,stage)
   prior=dict(schema=SCHEMA,cap_gpu_hours=226,origin_used_gpu_hours=160.,origin_gpu_jobs_launched=10,
    jobs={'DEV128':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-old',billed_limit_GPUh=12)},events=[])
   prior.update(pool.accounting(prior));atomic_json(pool.path,prior)
   main=root/'reports/gpu-budget-v2.json';atomic_json(main,dict(protected='running CPU scorer original'))
   before=main.read_bytes()
   job=dict(job_id=RUN,run_id=RUN,scope_counts=COUNTS,billed_limit_GPUh=1.5,launch_id='same',gpu_uuid='GPU-new')
   atomic_json(stage/'pg-GPU-authorization.json',dict(launch_id='same'))
   atomic_json(stage/'central-envelope.json',dict(job=job))
   gpu=dict(uuid='GPU-new',name='NVIDIA RTX A6000',compute_cap='8.6',pids=[],memory_used_mib=24)
   with patch('wcomr.innovation_gain_b1_card_r1.validate',return_value=({'host':'two_card'},{})):
    v=pool.reserve(job,gpu)
    self.assertEqual(v['jobs']['DEV128'],prior['jobs']['DEV128'])
    with self.assertRaises(ValueError):pool.reserve(job,gpu)
   v=pool.settle(RUN,.2,'a'*64)
   self.assertEqual(v['used_gpu_hours'],160.2);self.assertEqual(v['reserved_gpu_hours'],12.)
   self.assertEqual(main.read_bytes(),before)

if __name__=='__main__':unittest.main()
