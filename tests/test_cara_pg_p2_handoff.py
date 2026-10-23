import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p2_handoff',ROOT/'scripts/prepare_cara_pg_p2_after_p1_r1.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Handoff(unittest.TestCase):
 def batch(self):
  return dict(status='PG_P1_CAL_SELECTION_COMPLETE',selected_policy={'fingerprint':'winner'},simple_controls=['C','A'],
   selection={'order':[{'fingerprint':'winner'},{'fingerprint':'A'},{'fingerprint':'C'}]},
   candidates=[dict(proposal={'policy':{'fingerprint':f}}) for f in ('winner','A','C')])
 def test_select_existing_best_feasible_control(self):
  self.assertEqual(module.roles_from_batch(self.batch()),{'CARA':{'fingerprint':'winner'},'SIMPLE':{'fingerprint':'A'}})
 def test_no_simple_no_diagnostic_selection(self):
  b=self.batch();b['selection']['order']=[{'fingerprint':'winner'}]
  with self.assertRaises(ValueError):module.roles_from_batch(b)
 def test_unfinished_p1_blocked(self):
  for status in ('PG_P1_FIT_FIRST4','BUDGET_NOT_VERIFIED'):
   b=self.batch();b['status']=status
   with self.assertRaises(ValueError):module.roles_from_batch(b)
 def test_selected_simple_can_alias(self):
  b=self.batch();b['selected_policy']={'fingerprint':'A'}
  self.assertEqual(module.roles_from_batch(b)['CARA'],module.roles_from_batch(b)['SIMPLE'])
class HistoryBatch(unittest.TestCase):
 def setUp(self):
  from wcomr.policy_generator_r1.interval_grammar import Profile,Edge,compile_policy
  self.profile=Profile(36,tuple(range(1,8))+(36,),28,2,1,'CPU_FIXTURE')
  dense=list(range(1,8))+[10,16,27,36,37]
  self.policy=compile_policy(self.profile,[Edge(a,b) for a,b in zip(dense,dense[1:])]);self.states=[]
 def run_card(self,callback):
  from wcomr.policy_generator_r1.p2_production_batch import run_history
  import copy
  return run_history(profile=self.profile,roles={'CARA':self.policy,'SIMPLE':self.policy},members=['a','b'],execute_request=callback,save=lambda s:self.states.append(copy.deepcopy(s)))
 def result(self,row,policy):
  return dict(status='COMPLETE',shadow_D_pairs=row['diagnostic']['shadow_D_pairs'],history_records=row['diagnostic']['points'],clean_deployment_timing=False,full_request_seconds=None)
 def test_alias_keeps_roles_and_exact_three_paths(self):
  s=self.run_card(self.result);self.assertEqual(len(s['rows']),3);self.assertEqual(s['matrix']['shadow_guided_pairs'],18)
  self.assertTrue(all(r['roles']==['CARA','SIMPLE'] for r in s['rows']))
 def test_no_silent_missing_history(self):
  with self.assertRaises(ValueError):self.run_card(lambda r,p:{**self.result(r,p),'history_records':[]})
  self.assertEqual(len(self.states[-1]['rows']),3);self.assertEqual(self.states[-1]['rows'][-1]['status'],'NOT_REACHED')
 def test_shadow_clock_cannot_enter_latency(self):
  with self.assertRaises(ValueError):self.run_card(lambda r,p:{**self.result(r,p),'full_request_seconds':1.})

if __name__=='__main__':unittest.main()
