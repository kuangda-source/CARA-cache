import copy,json,unittest
from pathlib import Path
from wcomr.policy_generator_r1.cost112_card import MANIFEST,check_card
from wcomr.policy_generator_r1.cost112_model import analyze
ROOT=Path(__file__).resolve().parents[1]
class Clock(unittest.TestCase):
 def setUp(self):
  self.c=json.loads((ROOT/MANIFEST).read_text());self.rows=[]
  d,a=self.c['cost_model']['coefficients']
  for s in self.c['matrix']:
   if s['section'] not in ('ANCHOR','CALIBRATION','VALIDATION'):continue
   count=self.c['policies'][s['role']]['counts'] if s['role']!='NATIVE' else {'D':36,'A':0}
   self.rows.append(dict(s,seconds=300+d*(count['D']-36)+a*count['A'],status='COMPLETE',complete_request_boundary=True,diagnostic=False))
 def test_thermal_parser(self):
  from wcomr.policy_generator_r1.cost112_telemetry import parse
  self.assertEqual(parse('GPU-x, 88, 855, 280, Active, Not Active','GPU-x')['SM_MHz'],855)
  for raw in ('GPU-y, 88, 855, 280, Active, Not Active','GPU-x, nan, 855, 280, Active, Not Active'):
   with self.assertRaises(ValueError):parse(raw,'GPU-x')
 def test_full_independent72(self):
  v=analyze(self.c,self.rows);self.assertTrue(v['timing_model_validated']);self.assertEqual(v['validation_rows'],72);self.assertFalse(v['validation_refit'])
 def test_incomplete(self):
  with self.assertRaises(ValueError):analyze(self.c,self.rows[:-1])
 def test_target_cannot_be_own_anchor(self):
  c=copy.deepcopy(self.c);s=next(s for s in c['matrix'] if s['role']=='PG_ALL_D' and s['section']=='VALIDATION');s['clock_anchor_id']=s['id']
  r=next(r for r in self.rows if r['id']==s['id']);r['clock_anchor_id']=s['id']
  with self.assertRaises(ValueError):analyze(c,self.rows)
 def test_second_round_failure_not_averaged_away(self):
  r=next(r for r in self.rows if r['role']=='PG_ALL_D' and r['section']=='VALIDATION');r['seconds']+=2.1
  self.assertFalse(analyze(self.c,self.rows)['timing_model_validated'])
 def test_no_new_fit(self):
  self.c['cost_model']['new_card_refit']=True
  with self.assertRaises(ValueError):analyze(self.c,self.rows)
 def test_nan_refused(self):
  self.rows[0]['seconds']=float('nan')
  with self.assertRaises(ValueError):analyze(self.c,self.rows)
 def test_old_alpha_and_strong_baselines_exact(self):
  old=json.loads((ROOT/'manifests/cara_historical_bridge104_scope_quote_r1_20261024.json').read_text())
  for role,p in old['policies'].items():self.assertEqual(p,self.c['policies'][role])
  self.assertEqual(self.c['budget'],old['budget']);self.assertEqual(self.c['timing']['fixed_margin_seconds'],6)
if __name__=='__main__':unittest.main()
