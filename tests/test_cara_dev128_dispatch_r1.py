"""Bounded CPU checks of new controller refusal/recovery wiring."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import wc_two_card_cara_dev128_gpu_r1 as c
import review_cara_dev128_prelaunch_exposure_r1 as e
class Entry(unittest.TestCase):
 def test_remote_programs_compile(self):
  for name in ('PREPARE','PREFLIGHT','CENTRAL','LAUNCH','CAPTURE'):compile(getattr(c,name),name,'exec')
 def test_existing_handle_no_dispatch(self):
  with patch.object(c,'read',return_value={}),patch.object(c,'published',return_value='frozen'),patch.object(c,'recover',return_value={'original_files':{'intent':1}}),patch.object(c,'ssh') as s:
   self.assertIn('original_files',c.launch(SimpleNamespace(stage_ref=None,published_ref=None)));s.assert_not_called()
 def test_busy_no_reservation(self):
  with patch.object(c,'read',return_value={}),patch.object(c,'published',return_value='frozen'),patch.object(c,'recover',return_value={'original_files':{}}),patch.object(c,'ssh',return_value={'admissible':False,'reasons':['GPU_BUSY']}),patch.object(c.transport,'four_ssh') as s:
   self.assertFalse(c.launch(SimpleNamespace(stage_ref=None,published_ref=None,gpu_uuid='GPU-x'))['admissible']);s.assert_not_called()
 def test_stale_exposure_no_reservation(self):
  with patch.object(c,'read',return_value={}),patch.object(c,'published',return_value='frozen'),patch.object(c,'recover',return_value={'original_files':{}}),patch.object(c,'ssh',side_effect=[{'admissible':True},{'exposure':{'observed_unix':0,'scoped_no_execution_evidence':True}}]),patch.object(c.transport,'four_ssh') as s:
   with self.assertRaises(AssertionError):c.launch(SimpleNamespace(stage_ref=None,published_ref=None,gpu_uuid='GPU-x'))
   s.assert_not_called()
 def test_metadata_review_accepts_exact(self):
  v=json.loads((ROOT/'reports/cara_DEV128_prelaunch_dual_exposure_20261026.json').read_text());self.assertTrue(e.review(v)['scoped_no_execution_evidence'])
 def test_exposure_real_hits_not_exempt(self):
  v=json.loads((ROOT/'reports/cara_DEV128_prelaunch_dual_exposure_20261026.json').read_text());v['protected_remote_hits']={'new_dev':['generated']}
  with self.assertRaises(AssertionError):e.review(v)
 def test_exposure_new_local_output_not_exempt(self):
  v=json.loads((ROOT/'reports/cara_DEV128_prelaunch_dual_exposure_20261026.json').read_text());v['local_blockers'].append({'ref':'reports/new-generated-output.json'})
  with self.assertRaises(AssertionError):e.review(v)
 def test_storage_recipe_scoped(self):
  from provision_cara_dev128_storage_r1 import code
  text=code();compile(text,'private-storage','exec');self.assertIn("run='cara-shared25-dev128-r1'",text);self.assertNotIn('nvidia-smi',text);self.assertIn("assert not base.exists() and not out.exists()",text)
if __name__=='__main__':unittest.main()
