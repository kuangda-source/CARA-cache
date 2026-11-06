"""Recovery must change identity/quote while keeping the scientific card frozen."""
import copy,json,tempfile,unittest
from pathlib import Path
from wcomr.policy_generator_r1.shared66_card import RUN,VERSION,CPU_PROOF,MANIFEST,COUNTS,read,check_card,execution_quote
ROOT=Path(__file__).resolve().parents[1]
class RecoveryIdentity(unittest.TestCase):
 def setUp(self):self.card=read(ROOT/MANIFEST)
 def test_distinct_identity(self):
  self.assertEqual(RUN,'cara-shared-cal66-ada-r2');self.assertEqual(VERSION,'CARA_SHARED66_RECOVERY_R2');self.assertEqual(CPU_PROOF,'shared66-recovery-CPU.json')
 def test_quote_changes_only_registered_startup(self):
  original=copy.deepcopy(self.card);q=execution_quote(self.card)
  self.assertEqual(self.card,original);self.assertEqual(q['arm_seconds'],original['quote']['arm_seconds'])
  self.assertEqual(q['components']['model_load_GPUh'],.5);self.assertEqual(q['proposed_limit_GPUh'],8);self.assertEqual(q['cumulative_cap_GPUh'],226)
  self.assertAlmostEqual(q['forecast_GPUh'],6.880951261871347)
 def test_scope_or_alpha_mutation_refused(self):
  self.card['roles']['S25_A_PHASE']['policy']['shared_alpha'][22]=.25
  with self.assertRaises(ValueError):check_card(self.card)
 def test_quote_edit_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'quote.json';p.write_text('{}')
   with self.assertRaises(ValueError):execution_quote(self.card,p)
 def test_old_launch_not_accepted_as_R2(self):
  from test_cara_shared66_combination_r1 import fixture
  from wcomr.policy_generator_r1.shared66_terminal import accept
  v=fixture();v['launch']['run_id']='cara-shared-cal66-ada-r1'
  with self.assertRaisesRegex(ValueError,'Wrong PG launch'):accept(v)
class RecoveryCPUAcceptance(unittest.TestCase):
 def test_original_and_resealed_invalid_evidence(self):
  import sys,hashlib
  sys.path.insert(0,str(ROOT/'scripts'))
  from audit_cara_cal66_recovery_launch_cpu_r2 import accept
  v=read(ROOT/'reports/cara_CAL66_R2_identity_CPU_complete_check_20261025.json')
  self.assertTrue(accept(v)['production_CPU_accepted'])
  for field,value in [('terminal_tests',0),('run_id','cara-shared-cal66-ada-r1'),('GPU_submissions',1),('actual_registered_stage_validate',False)]:
   bad=copy.deepcopy(v);bad['proof']['data'][field]=value
   bad['proof']['sha256']=hashlib.sha256((json.dumps(bad['proof']['data'],indent=2)+'\n').encode()).hexdigest()
   with self.subTest(field=field),self.assertRaises(ValueError):accept(bad)
  for section in ('lifecycle','storage_lifecycle'):
   bad=copy.deepcopy(v);bad['proof']['data'][section]['checks'].pop()
   bad['proof']['sha256']=hashlib.sha256((json.dumps(bad['proof']['data'],indent=2)+'\n').encode()).hexdigest()
   with self.subTest(section=section),self.assertRaises(ValueError):accept(bad)

if __name__=='__main__':unittest.main()
