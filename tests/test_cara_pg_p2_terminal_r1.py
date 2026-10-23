"""P2 whole lifecycle acceptance with synthetic terminal snapshots only."""
import copy,unittest
from test_cara_pg_p1_combination_r1 import fixture as p1_fixture,put
from wcomr.policy_price_terminal_r1 import record
from wcomr.policy_generator_r1.p2_terminal import accept_lifecycle
from wcomr.policy_generator_r1.p2_combination import digest
from wcomr.gpu_budget_pool_v2 import BudgetPool

def fixture():
 v=p1_fixture();L=v['launch'];old=L['run_id'];L['run_id']='cara-pg-p2-CPU-FIXTURE';counts=dict(physical_paths=518);L['scope_counts']=counts
 c=record(v,'config');c.update(scope_counts=counts,manifest_sha256=digest('CPU518'),final_P1_and_dedup_bound=True);L['config_sha256']=put(v,'config',c)
 q=record(v,'quote');q.update(scope_counts=counts,manifest_sha256=c['manifest_sha256'],final_budget_determined=True);put(v,'quote',q)
 reg=record(v,'registration');reg['payload_sha256'].update({'pg-p2-config.json':v['files']['config']['sha256'],'pg-p2-whole-quote.json':v['files']['quote']['sha256']});L['registration_sha256']=put(v,'registration',reg);v['payload_actual_sha256']=reg['payload_sha256'];v['container']['manifest_sha256']=L['registration_sha256']
 cpu=record(v,'CPU_acceptance');cpu['registration_sha256']=L['registration_sha256'];put(v,'CPU_acceptance',cpu)
 auth=record(v,'authorization');auth.update({k:L[k] for k in ('run_id','scope_counts','config_sha256','registration_sha256')},specific_whole_card_approved=True,independent_CPU_acceptance_sha256=v['files']['CPU_acceptance']['sha256']);L['authorization_sha256']=put(v,'authorization',auth)
 for key in ('supervisor','billing'):
  d=record(v,key);d.update(run_id=L['run_id'],scope_counts=counts);put(v,key,d)
 d=record(v,'guardian');d['status']='PG_P2_HOST_GUARDIAN_TERMINAL';put(v,'guardian',d)
 d=record(v,'runner');d.update(registration_sha256=L['registration_sha256'],config_sha256=L['config_sha256']);put(v,'runner',d)
 d=record(v,'post');d['runner_sha256']=v['files']['runner']['sha256'];put(v,'post',d)
 d=record(v,'post_exit');d['final_result_sha256']=v['files']['post']['sha256'];put(v,'post_exit',d)
 job=v['pool']['jobs'].pop(old);job['billing_sha256']=v['files']['billing']['sha256'];v['pool']['jobs'][L['run_id']]=job
 v['pool'].update(BudgetPool.accounting(v['pool']));return v

class Terminal(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.template=fixture()
 def setUp(self):self.v=copy.deepcopy(self.template)
 def change(self,key,fun):d=record(self.v,key);fun(d);put(self.v,key,d)
 def test_complete(self):self.assertTrue(accept_lifecycle(self.v)['lifecycle_and_finance_accepted'])
 def test_unsettled(self):
  self.v['pool']['jobs'][self.v['launch']['run_id']]['status']='RESERVED_OR_RUNNING'
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_failed_child(self):
  self.change('supervisor',lambda d:d.update(child_exit_code=1))
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_live_container(self):
  self.v['container']['state']['Running']=True
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_lock_not_released(self):
  self.v['own_UUID_lock_free']=False
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_tail_gap(self):
  self.change('billing',lambda d:d.update(wall_seconds=d['wall_seconds']+60,actual_GPUh=(d['wall_seconds']+60)/3600))
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_foreign_context(self):
  import json
  rows=[json.loads(r) for r in self.v['monitor_raw_utf8'].splitlines()];rows[-1]['snapshot']['compute_apps'].append(dict(pid=999,uid=1005,start_ticks=1));raw=''.join(json.dumps(r)+'\n' for r in rows);self.v['monitor_raw_utf8']=raw
  import hashlib
  self.change('monitor_final',lambda d:d.update(monitor_sha256=hashlib.sha256(raw.encode()).hexdigest()))
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_scope_changed(self):
  self.v['launch']['scope_counts']['physical_paths']=90
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_post_sha(self):
  self.change('post_exit',lambda d:d.update(final_result_sha256='0'*64))
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
 def test_budget_not_fallback(self):
  self.change('quote',lambda d:d.update(final_budget_determined=False))
  with self.assertRaises(ValueError):accept_lifecycle(self.v)
if __name__=='__main__':unittest.main()
