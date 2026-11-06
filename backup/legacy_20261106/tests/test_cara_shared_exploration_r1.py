import copy,json,unittest
from pathlib import Path
from wcomr.policy_generator_r1.shared_exploration import base_dense,shared_dense,compile_dense,roles,PROTECTED
from wcomr.policy_generator_r1.interval_grammar import Profile
ROOT=Path(__file__).resolve().parents[1]
class Shared(unittest.TestCase):
 def setUp(self):
  self.card=json.loads((ROOT/'manifests/cara_shared_CAL106_scope_quote_r1_20261025.json').read_text());p=self.card['profile'];p['protected_dense']=tuple(p['protected_dense']);p['alpha_candidates']=tuple(p['alpha_candidates']);self.p=Profile(**p);self.s=self.card['energy_scores']
 def test_all_legal_quotas(self):
  for n in range(9,37):
   v=shared_dense(self.s,n);self.assertEqual(len(v['dense']),n);self.assertTrue(set(PROTECTED)<=set(v['dense']))
   for correction in (False,True):
    p=compile_dense(self.p,v['dense'],correction=correction,age_cap=3)
    for t,a in enumerate(p['actions'],1):
     if a=='A':self.assertLessEqual(t-p['source_before'][t-1],3);self.assertEqual(p['shared_alpha'][t-1],1. if t<25 else .5)
 def test_original26(self):
  v=shared_dense(self.s,26);self.assertEqual((v['remove_D'],v['add_D']),(33,22))
 def test_ties_and_flat(self):
  self.assertIsNone(shared_dense([1.]*36,24)['remove_D'])
  s=[0.]*36;s[19]=s[20]=10.;self.assertEqual(shared_dense(s,24)['add_D'],20)
 def test_invalid(self):
  for n in (8,37,True,24.5):
   with self.assertRaises(ValueError):base_dense(n)
  for s in ([0.]*35,[float('nan')]*36,[-1.]*36):
   with self.assertRaises(ValueError):shared_dense(s,24)
 def test_frozen_roles_scope(self):
  self.assertEqual(roles(self.p,self.s),self.card['roles']);m=self.card['matrix'];self.assertEqual(len(m),106);self.assertEqual(len({r['id'] for r in m}),106)
  self.assertEqual(sum(r['actual_updates'] for r in m),3669)
  self.assertFalse(self.card['GPU_dispatch_ready']);self.assertFalse(self.card['quote']['limit_approved'])
 def test_age_fallback_preserves_D(self):
  d=shared_dense(self.s,24)['dense'];c=compile_dense(self.p,d);a=compile_dense(self.p,d,correction=True,age_cap=3)
  self.assertEqual(c['dense_mask'],a['dense_mask']);self.assertEqual(a['actions'][33],'C')
if __name__=='__main__':unittest.main()
