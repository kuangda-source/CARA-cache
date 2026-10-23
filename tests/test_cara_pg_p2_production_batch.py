import copy,unittest
from wcomr.policy_generator_r1.p2_production_batch import timing_matrix,run_timing
from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY

class Timing(unittest.TestCase):
 def setUp(self):
  self.members=['a','b','c','d'];self.states=[];self.calls=[]
  self.grid=[dict(requested_steps=n,actual_updates=n+1) for n in range(18,36)]
 def endpoint(self,row):
  self.calls.append(row)
  seconds=260. if row['method']=='CARA' else (int(row['method'][6:])+1)*10.
  return dict(status='COMPLETE',full_request_seconds=seconds,timing_boundary=TIME_BOUNDARY)
 def run_card(self,endpoint=None,accept=None):
  return run_timing(members=self.members,schedule_rows=self.grid,profile_identity='test',execute_request=endpoint or self.endpoint,
   accept_exclusive_prefix=accept or (lambda rows:dict(accepted=True,sha256='a'*64)),save=lambda s:self.states.append(copy.deepcopy(s)))
 def test_complete84_and_cal_only(self):
  s=self.run_card();self.assertEqual(len(self.calls),84);self.assertEqual(s['choice']['selected_steps'],[25]);self.assertFalse(s['quality_values_used'])
  self.assertEqual(len({r['id'] for r in s['rows']}),84)
 def test_balanced_rotation(self):
  rows=timing_matrix(['B','A'],self.members,'t');self.assertEqual(len(rows),28)
  self.assertEqual([(r['member'],r['method']) for r in rows[4:8]],[('a','A'),('a','B'),('b','B'),('b','A')])
  self.assertEqual(rows[12]['member'],'b');self.assertEqual(rows[12]['method'],'B')
 def test_quality_rejected_before_selection(self):
  with self.assertRaises(ValueError):self.run_card(lambda r:{**self.endpoint(r),'LPIPS':0.})
  self.assertEqual(len(self.calls),1);self.assertEqual(self.states[-1]['status'],'P2_TIME_STOP_FULL_DENOMINATOR_RETAINED')
 def test_refusal_keeps_remaining_positions(self):
  with self.assertRaises(ValueError):self.run_card(lambda r:dict(status='TEXT_REJECTED'))
  self.assertEqual(len(self.states[-1]['rows']),28);self.assertEqual(self.states[-1]['rows'][-1]['status'],'NOT_REACHED')
 def test_bad_exclusive_prefix_no_candidates(self):
  with self.assertRaises(ValueError):self.run_card(accept=lambda rows:dict(accepted=False,sha256='a'*64))
  self.assertEqual(len(self.calls),28)
 def test_identity_overwrite_stops(self):
  with self.assertRaises(ValueError):self.run_card(lambda r:{**self.endpoint(r),'member':'changed'})
class HistoryAnalysis(unittest.TestCase):
 def test_constant_rank_and_zero_denominator(self):
  from wcomr.policy_generator_r1.p2_history_analysis import compare
  r=compare(dict(C=0.,A_HALF=0.,A_ONE=0.),dict(C=0.,A_HALF=0.,A_ONE=0.))
  self.assertIsNone(r['Spearman_with_average_ties']);self.assertEqual(set(r['ratio'].values()),{None})
  self.assertEqual(r['tied_other_choice_regret_range'],[0.,0.])
 def test_ties_preserve_possible_regret(self):
  from wcomr.policy_generator_r1.p2_history_analysis import compare
  r=compare(dict(C=3.,A_HALF=1.,A_ONE=2.),dict(C=0.,A_HALF=0.,A_ONE=1.))
  self.assertEqual(r['tied_other_choice_regret_range'],[0.,2.]);self.assertEqual(r['best_set_intersection'],['A_HALF'])
 def test_nonfinite_or_negative_rejected(self):
  from wcomr.policy_generator_r1.p2_history_analysis import compare
  for bad in (-1.,float('nan'),float('inf')):
   with self.assertRaises(ValueError):compare(dict(C=bad,A_HALF=1.,A_ONE=2.),dict(C=1.,A_HALF=2.,A_ONE=3.))

if __name__=='__main__':unittest.main()
