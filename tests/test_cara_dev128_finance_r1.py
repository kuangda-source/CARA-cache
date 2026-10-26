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

class RetiredLiability(unittest.TestCase):
 def test_same_uuid_hold_keeps_money_allows_actual_idle(self):
  from wcomr.policy_generator_r1.dev128_card import COUNTS
  raw={'schema': 'WC_GPU_BUDGET_POOL_V2', 'cap_gpu_hours': 226, 'origin_used_gpu_hours': 161.39662063362806, 'origin_gpu_jobs_launched': 0, 'jobs': {'retired-two-card-bank24-uncertainty-hold-20261022': {'job_id': 'retired-two-card-bank24-uncertainty-hold-20261022', 'kind': 'UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD', 'status': 'RESERVED_OR_RUNNING', 'billed_limit_GPUh': 4.5, 'gpu_uuid': 'GPU-de9a5370-cd87-0f1c-a48e-288888777dd3', 'supervisor_pid': None, 'supervisor_start_ticks': None, 'source_revision': 'NO_NEW_OLD_HOST_RUN_ASSERTED', 'launch_id': 'NOT_A_CONFIRMED_GPU_SUBMISSION', 'stage': 'RETIRED_HOST_UNKNOWN_DO_NOT_CONTACT', 'actual_cost_unknown': True, 'confirmed_GPU_submission': False, 'reserved_unix': 1792654151.8925738, 'release_policy': 'ONLY_WITH_INDEPENDENT_TERMINAL_OR_EXPLICIT_BUDGET_RECONCILIATION'}, 'retired-two-card-full1624-uncertainty-hold-20261022': {'job_id': 'retired-two-card-full1624-uncertainty-hold-20261022', 'kind': 'UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD', 'status': 'RESERVED_OR_RUNNING', 'billed_limit_GPUh': 12.0, 'gpu_uuid': 'GPU-cebf7119-cf03-23b9-e192-cd196332b704', 'supervisor_pid': None, 'supervisor_start_ticks': None, 'source_revision': 'NO_NEW_OLD_HOST_RUN_ASSERTED', 'launch_id': 'NOT_A_CONFIRMED_GPU_SUBMISSION', 'stage': 'RETIRED_HOST_UNKNOWN_DO_NOT_CONTACT', 'actual_cost_unknown': True, 'confirmed_GPU_submission': False, 'reserved_unix': 1792654151.8925738, 'release_policy': 'ONLY_WITH_INDEPENDENT_TERMINAL_OR_EXPLICIT_BUDGET_RECONCILIATION'}}, 'events': []};raw.update(HostBudgetPool.accounting(raw))
  before=copy.deepcopy(raw);uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);atomic_json(root/'reports/gpu-budget-v2.json',raw);pool=HostBudgetPool(root)
   job=dict(job_id=RUN,run_id=RUN,host='two_card',scope_counts=COUNTS,forecast_GPUh=11.618228467131088,billed_limit_GPUh=12,source_revision='fixture',config_sha256='a'*64,launch_id='fixture',gpu_uuid=uuid)
   gpu=dict(uuid=uuid,name='NVIDIA RTX A6000',compute_cap='8.6',memory_used_mib=24,pids=[])
   after=pool.reserve(job,gpu)
   self.assertEqual(after['reserved_gpu_hours'],28.5)
   self.assertTrue(all(after['jobs'][k]==v for k,v in before['jobs'].items()))
   with self.assertRaises(ValueError):pool.reserve(job,gpu)
   settled=pool.settle(RUN,.01,'a'*64);self.assertEqual(settled['reserved_gpu_hours'],16.5)
   self.assertTrue(all(settled['jobs'][k]==v for k,v in before['jobs'].items()))
 def test_false_flag_alone_does_not_hide_live_collision(self):
  from wcomr.policy_generator_r1.dev128_finance import financial_hold
  self.assertFalse(financial_hold(dict(confirmed_GPU_submission=False)))
  v=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=0,origin_gpu_jobs_launched=0,jobs={str(i):dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-same',billed_limit_GPUh=1,confirmed_GPU_submission=False) for i in range(2)})
  with self.assertRaises(ValueError):HostBudgetPool.accounting(v)
