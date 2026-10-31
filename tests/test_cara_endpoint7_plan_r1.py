import copy,json,unittest
from pathlib import Path
from wcomr.cara_endpoint7_plan_r1 import validate,quote,NEW_ROLES
from wcomr.cara_fast_spec_r1 import digest
ROOT=Path(__file__).resolve().parents[1]
class EndpointSeven(unittest.TestCase):
 def test_scope_denominators_and_reuse(self):
  for count in (39,46):
   p=json.loads((ROOT/f'plans/cara_next_stage_20261101/e1/ENDPOINT7_{count}_MANIFEST_R1.json').read_text());validate(p)
   self.assertEqual(sum(r['mode']=='GENERATE_AND_SCORE' for r in p['formal_matrix']),16)
   self.assertEqual(sum(r['mode']=='REUSE_COMPLETE_SCORE' for r in p['formal_matrix']),12)
   for role in NEW_ROLES:self.assertEqual(sum(r['role']==role for r in p['physical_matrix']),7)
   self.assertEqual(quote(p,321.40277120284736)['proposed_hard_GPUh'],6.25 if count==39 else 7)
 def test_tamper_and_protected_inputs(self):
  p=json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
  for mutation in ('drop','test','budget'):
   q=copy.deepcopy(p)
   if mutation=='drop':q['physical_matrix'].pop()
   if mutation=='test':q['physical_matrix'][0]['member']='PROTECTED_TEST'
   if mutation=='budget':q['roles']['F19_RISKSWAP_C']['policy']['actions'][0]='C'
   q['scope_sha256']=digest({k:v for k,v in q.items() if k!='scope_sha256'})
   with self.assertRaises(ValueError):validate(q)
if __name__=='__main__':unittest.main()
