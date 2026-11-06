import copy,json,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src')]
from wcomr.policy_generator_r1.dev128_card import check_card,MANIFEST,COUNTS
from wcomr.policy_generator_r1.dev128_collection import collect,control_pairs,score_after_release
class Contract(unittest.TestCase):
 def setUp(self):self.c=json.loads((ROOT/MANIFEST).read_text())
 def test_original_policies_and_denominators(self):
  old=json.loads((ROOT/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json').read_text())
  self.assertEqual(self.c['roles'],{r:old['roles'][r] for r in self.c['roles']});check_card(self.c)
  self.assertEqual(sum(s['actual_updates'] for s in self.c['matrix']),4419);self.assertEqual(len(control_pairs(self.c)),26)
 def test_unplanned_alpha_rejected(self):
  self.c['roles']['S25_A_PHASE']['policy']['shared_alpha'][20]=.123
  with self.assertRaises(ValueError):check_card(self.c)
 def test_missing_path_rejected(self):
  self.c['matrix'].pop()
  with self.assertRaises(ValueError):check_card(self.c)
 def test_failure_retains128(self):
  saved=[]
  def bad(*args):raise OSError('ENTRY_FAILURE')
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaises(OSError):collect(self.c,root,bad,lambda s:saved.append(copy.deepcopy(s)))
  self.assertEqual(saved[-1]['status'],'FAILED128_DENOMINATOR_RETAINED');self.assertEqual(len(saved[-1]['rows']),128)
  self.assertEqual(sum(r['status']=='NOT_REACHED' for r in saved[-1]['rows']),127)
 def test_pre_release_rejected(self):
  with self.assertRaises(ValueError):score_after_release(self.c,{},'.',None,{},dict(GPU_released=False,ledger_settled=True,lock_free=True,CUDA_hidden=True),lambda s:None)
 def test_no_final_confirmation_in_dev(self):
  pool=json.loads((ROOT/'plans/cara_policy_generator_20261020/NEW_INPUT_POOL48_R1_20261025.json').read_text())
  expected=[r['name'] for r in pool['members'] if r['role']=='NEW_DEV_RESERVED']
  self.assertEqual(self.c['DEV_members'],expected)
  self.assertTrue(all(s['member'] in expected for s in self.c['matrix'] if s['section'] in ('QUALITY','TIMING_REPEAT')))
if __name__=='__main__':unittest.main()
