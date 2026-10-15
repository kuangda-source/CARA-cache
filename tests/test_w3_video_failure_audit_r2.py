"""Video container failure remains a failed control while all raw files audit."""
import importlib.util,inspect,subprocess,tempfile,unittest
from pathlib import Path
from wcomr.w3_video_failure_audit_r2 import VideoFailureGuard,derive_reader
from wcomr.w3_label64_fullpost_r1 import audit_all
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fullpost_fixture',Path(__file__).with_name('test_w3_label64_fullpost_r1.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)

class GuardTests(unittest.TestCase):
 def test_corrupt_video_and_original_rejections_keep18_72_and_raw_teacher_scope(self):
  with tempfile.TemporaryDirectory() as td:
   rows,requests,kw=f.cohort(Path(td))
   for row in rows[-2:]:row.update(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0,parent_vectors=None,diagnostic_points=[],actual_pair_computations=0)
   read=kw['read_video']
   def video(row):
    if row['id']==rows[9]['id']:raise subprocess.CalledProcessError(1,['ffprobe','ORIGINAL_BAD_VIDEO'])
    return read(row)
   guard=VideoFailureGuard();kw['read_video']=guard.wrap(video)
   result=audit_all(rows,requests,**kw);note=guard.annotate(result)
   self.assertEqual((len(result['parents']),len(result['labels'])),(18,72))
   self.assertEqual(result['audit_failed_parent_ids'],[rows[9]['id']])
   self.assertEqual((result['raw_files'],result['raw_tensors'],result['actual_pairs']),(80,1104,768))
   self.assertEqual((result['actual_available_labels'],result['accepted_videos']),(64,15))
   self.assertEqual((note['primary_grouped_fit_label_count'],len(note['primary_grouped_fit_prompt_groups'])),(48,6))
   self.assertEqual((note['model_only_formal_labels_not_in_primary_fit'],note['warmup_labels_excluded_from_fit']),(8,8))
   self.assertEqual((note['sensitivity_raw_model_fit_label_count'],len(note['sensitivity_raw_model_fit_prompt_groups'])),(56,7))
   self.assertNotEqual(result['status'],'W3_FULL18_LABEL72_RAW_PARENT_CPU_AUDITED')
   self.assertEqual(rows[9]['status'],'COMPLETE');self.assertEqual(rows[-1]['status'],'TEXT_REJECTED')
 def test_guard_does_not_swallow_ordinary_raw_or_programming_errors(self):
  for kind in (ValueError,KeyError,RuntimeError):
   guard=VideoFailureGuard()
   def fail(row):raise kind('ORIGINAL')
   with self.assertRaises(kind):guard.wrap(fail)({'id':'x','scene':'s'})
   self.assertEqual(guard.failures,[])
 def test_original_reader_inverse_AST_matches_only3_sites(self):
  p=ROOT/'scripts/postprocess_wc_w3_label64_full864_cpu_r1.py'
  s=importlib.util.spec_from_file_location('original_post_source',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  before=inspect.getsource(m.main);_,proof=derive_reader(m.main)
  self.assertEqual(proof['explicit_sites'],3);self.assertTrue(proof['inverse_AST_equal']);self.assertEqual(inspect.getsource(m.main),before)
if __name__=='__main__':unittest.main()
