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
if __name__=='__main__':unittest.main()
