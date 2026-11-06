import importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('dedup',Path(__file__).resolve().parents[1]/'scripts/cara_completed_tensor_dedup_r2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class DedupTests(unittest.TestCase):
 def setUp(self):
  self.proc=patch.object(m,'open_hits',return_value=[]);self.hits=self.proc.start();self.addCleanup(self.proc.stop)
 def fixture(self,root):
  a=root/'a.pt';b=root/'b.pt';alias=root/'alias.pt';a.write_bytes(b'original evidence'*20);b.write_bytes(a.read_bytes());os.link(a,alias)
  entries=[]
  for p in (a,b,alias):
   s=p.stat();entries.append(dict(path=str(p),inode=s.st_ino,dev=s.st_dev,bytes=s.st_size,mtime_ns=s.st_mtime_ns))
  return [dict(bytes=a.stat().st_size,sha256=m.sha(a),files=entries)],a,b,alias
 def test_merge_preserves_bytes_aliases_and_repeat_receipt(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);groups,a,b,alias=self.fixture(root);guard=lambda:dict(protected=True)
   r=m.consolidate(groups,root/'control',guard,lambda p:p.relative_to(root))
   self.assertEqual(r['retired_distinct_inodes'],1);self.assertEqual(r['newly_replaced_paths'],1)
   self.assertTrue(os.path.samefile(a,b));self.assertTrue(os.path.samefile(alias,b));self.assertEqual(m.sha(b),groups[0]['sha256']);self.assertFalse(b.stat().st_mode&0o222)
   self.assertEqual(m.consolidate(groups,root/'control',guard,lambda p:None),r)
   restored=root/'restore.pt';restored.write_bytes(b.read_bytes());self.assertNotEqual(restored.stat().st_ino,b.stat().st_ino);self.assertEqual(m.sha(restored),m.sha(b))
 def test_changed_source_rejected_before_replacement(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);groups,a,b,alias=self.fixture(root);b.write_bytes(b'changed')
   with self.assertRaises(AssertionError):m.consolidate(groups,root/'control',lambda:{},lambda p:None)
   self.assertFalse(os.path.samefile(a,b));self.assertEqual(b.read_bytes(),b'changed')
 def test_open_inode_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);groups,a,b,alias=self.fixture(root)
   self.hits.return_value=[dict(pid=123,fd='3')]
   with b.open('rb'):
    with self.assertRaises(AssertionError):m.consolidate(groups,root/'control',lambda:{},lambda p:None)
   self.assertFalse(os.path.samefile(a,b))
 def test_protection_failure_prevents_all_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);groups,a,b,alias=self.fixture(root)
   def fail():raise RuntimeError('P1 changed')
   with self.assertRaises(RuntimeError):m.consolidate(groups,root/'control',fail,lambda p:None)
   self.assertFalse(os.path.samefile(a,b));self.assertTrue(a.stat().st_mode&0o200)
if __name__=='__main__':unittest.main()
