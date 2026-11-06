import importlib.util,os,tempfile,unittest,zipfile,tarfile,io
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('archive',Path(__file__).resolve().parents[1]/'scripts/cara_archive_equivalence_cleanup_r1.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ArchiveTests(unittest.TestCase):
 def setUp(self):
  self.patch=patch.object(m,'visible_open_hits',return_value=dict(hits=[],unreadable_process_fd_directories=0));self.patch.start();self.addCleanup(self.patch.stop)
 def setup_zip(self,root,data=b'original',member='dataset/f.bin'):
  tree=root/'tree';tree.mkdir();(tree/'f.bin').write_bytes(data);a=root/'archive.zip'
  with zipfile.ZipFile(a,'w',zipfile.ZIP_DEFLATED) as z:z.writestr(member,b'original')
  s=a.stat();p=dict(id='one',archive=str(a),root=str(tree),strip_root='dataset',format='zip',expected_inode=s.st_ino,expected_bytes=s.st_size,expected_mtime_ns=s.st_mtime_ns);return p,a,tree
 def test_full_match_removes_only_archive(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t).resolve();p,a,tree=self.setup_zip(root);c=root/'control';c.mkdir();r=m.verify_one(p,c,True)
   self.assertTrue(r['removed']);self.assertFalse(a.exists());self.assertEqual((tree/'f.bin').read_bytes(),b'original');self.assertTrue((c/'one/verified.json').exists());self.assertTrue((c/'one/delete-intent.json').exists())
 def test_same_size_different_bytes_keeps_archive(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t).resolve();p,a,tree=self.setup_zip(root,b'differen');c=root/'control';c.mkdir();r=m.verify_one(p,c,True)
   self.assertFalse(r['removed']);self.assertTrue(a.exists());self.assertIn('Content mismatch',r['error'])
 def test_missing_file_keeps_archive(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t).resolve();p,a,tree=self.setup_zip(root);(tree/'f.bin').unlink();c=root/'control';c.mkdir();r=m.verify_one(p,c,True)
   self.assertFalse(r['removed']);self.assertTrue(a.exists())
 def test_traversal_is_refused(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t).resolve();p,a,tree=self.setup_zip(root,member='dataset/../f.bin');c=root/'control';c.mkdir();r=m.verify_one(p,c,True)
   self.assertFalse(r['removed']);self.assertTrue(a.exists())
 def test_no_delete_flag_preserves_equal_archive(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t).resolve();p,a,tree=self.setup_zip(root);c=root/'control';c.mkdir();r=m.verify_one(p,c,False)
   self.assertFalse(r['removed']);self.assertEqual(r['status'],'VERIFIED_NOT_REMOVED');self.assertTrue(a.exists())
 def test_tar_full_stream_verifies(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t).resolve();tree=root/'tree';tree.mkdir();(tree/'f.bin').write_bytes(b'data');a=root/'archive.tgz'
   with tarfile.open(a,'w:gz') as z:
    info=tarfile.TarInfo('f.bin');info.size=4;z.addfile(info,io.BytesIO(b'data'))
   s=a.stat();p=dict(id='one',archive=str(a),root=str(tree),format='tar',expected_inode=s.st_ino,expected_bytes=s.st_size,expected_mtime_ns=s.st_mtime_ns);c=root/'control';c.mkdir();r=m.verify_one(p,c,True);self.assertTrue(r['removed']);self.assertEqual((tree/'f.bin').read_bytes(),b'data')
if __name__=='__main__':unittest.main()
