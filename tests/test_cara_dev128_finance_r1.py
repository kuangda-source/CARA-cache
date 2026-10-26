"""Isolated real BudgetPool settlement, duplicate/refusal boundaries; no SSH."""
import copy,json,tempfile,unittest
from pathlib import Path
from wcomr.policy_generator_r1.dev128_finance import RUN,ENVELOPE,settle_original,audit_settlement,HostBudgetPool
from wcomr.gpu_budget_pool_v2 import BudgetPool,atomic_json
from wcomr.policy_price_terminal_r1 import record

def central_fixture(v):
 L=v['launch'];eid=RUN if L['host']=='four_card' else ENVELOPE;b=record(v,'billing')
 job=dict(run_id=RUN,stage=L['stage'],source_revision=L['source_revision'],gpu_uuid=L['gpu_uuid'],launch_id=L['launch_id'],billed_limit_GPUh=12.,status='RESERVED_OR_RUNNING')
 before=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226.,origin_used_gpu_hours=161.39662063362806,origin_gpu_jobs_launched=0,jobs={eid:job,'old-unknown':dict(status='RESERVED_OR_RUNNING',billed_limit_GPUh=16.5,gpu_uuid='GPU-OLD-UNKNOWN')},events=[])
 before.update(BudgetPool.accounting(before));after=copy.deepcopy(before)
 after['jobs'][eid].update(status='SETTLED',actual_GPUh=b['actual_GPUh'],billing_sha256=v['files']['billing']['sha256']);after.update(BudgetPool.accounting(after))
 v['central_settlement']=dict(central_before=before,central_after=after,envelope_id=eid,billing_sha256=v['files']['billing']['sha256'],host=L['host'],launch_id=L['launch_id'],scientific_acceptance_implied=False,same_money_not_two_charges=True)
 return before

class Finance(unittest.TestCase):
 def fixture(self):
  from test_cara_dev128_terminal_r1 import fixture
  return fixture()
 def test_actual_idempotent_external_settlement(self):
  v=self.fixture();before=central_fixture(v)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);atomic_json(root/'reports/gpu-budget-v2.json',before);pool=BudgetPool(root)
   v['central_settlement']=settle_original(pool,v);self.assertTrue(audit_settlement(v)['financial_terminal_accepted'])
   original=pool.read();settle_original(pool,v);self.assertEqual(pool.read(),original)
   self.assertEqual(original['jobs']['old-unknown'],before['jobs']['old-unknown']);self.assertNotIn(RUN,original['jobs'])
 def test_failed_science_still_billed(self):
  from test_policy_price_terminal_r1 import put
  v=self.fixture();d=record(v,'runner');d['batch']['status']='FAILED';put(v,'runner',d)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);atomic_json(root/'reports/gpu-budget-v2.json',central_fixture(v));v['central_settlement']=settle_original(BudgetPool(root),v)
   self.assertFalse(audit_settlement(v)['science_accepted'])
 def test_central_mutations(self):
  v=self.fixture()
  for kind in ('missing','double','unknown','wrong_bill','wrong_host','wrong_launch'):
   w=copy.deepcopy(v);s=w['central_settlement']
   if kind=='missing':s['central_after']['jobs'][ENVELOPE]['status']='RESERVED_OR_RUNNING'
   elif kind=='double':s['central_after']['jobs'][RUN]=copy.deepcopy(s['central_after']['jobs'][ENVELOPE])
   elif kind=='unknown':s['central_after']['jobs']['old-unknown']['billed_limit_GPUh']=0
   elif kind=='wrong_bill':s['billing_sha256']='0'*64
   elif kind=='wrong_host':s['host']='four_card'
   else:s['central_after']['jobs'][ENVELOPE]['launch_id']='different'
   with self.subTest(kind=kind),self.assertRaises(ValueError):audit_settlement(w)
 def test_conflicting_settlement(self):
  v=self.fixture()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);atomic_json(root/'reports/gpu-budget-v2.json',central_fixture(v));pool=BudgetPool(root);settle_original(pool,v)
   with self.assertRaises(ValueError):pool.settle(ENVELOPE,.1,'a'*64)
 def test_busy_host_and_overquote_refused(self):
  from wcomr.policy_generator_r1.dev128_card import COUNTS
  v=self.fixture();base=central_fixture(v);base['jobs'].pop(ENVELOPE);base.update(BudgetPool.accounting(base))
  for host,name,cap in [('four_card','NVIDIA RTX 6000 Ada Generation','8.9'),('two_card','NVIDIA RTX A6000','8.6')]:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);atomic_json(root/'reports/gpu-budget-v2.json',base);pool=HostBudgetPool(root)
    j=dict(job_id=RUN,run_id=RUN,host=host,scope_counts=COUNTS,forecast_GPUh=11.,billed_limit_GPUh=12.,source_revision='fixture',config_sha256='a'*64,launch_id='fixture',gpu_uuid='GPU-fixture')
    g=dict(uuid='GPU-fixture',name=name,compute_cap=cap,memory_used_mib=0,pids=[])
    with self.assertRaises(ValueError):pool.reserve(dict(j,forecast_GPUh=12.349232),g)
    with self.assertRaises(ValueError):pool.reserve(j,dict(g,pids=[123]))
    with self.assertRaises(ValueError):pool.reserve(j,dict(g,compute_cap='0.0'))
    pool.reserve(j,g)
    with self.assertRaises(ValueError):pool.reserve(j,g)
