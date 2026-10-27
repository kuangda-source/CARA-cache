"""Real WC73 observer under disappearing /proc and unknown CUDA PID fixtures."""
import unittest,errno,time
from unittest.mock import patch
from wcomr import wc73_exclusive_r1 as ex
class Proc:
 def __init__(self,name='root',error=None):self.name=name;self.error=error
 def __truediv__(self,x):return self
 def iterdir(self):return [Proc('1234',self.error)]
 def read_text(self):
  if self.error:raise self.error
  return 'other-process'
class Tests(unittest.TestCase):
 def run_case(self,error,apps=''):
  def query(args,**kw):return apps if 'compute-apps' in ' '.join(args) else 'GPU-fixture, Exclusive_Process\n'
  with patch.object(ex,'Path',lambda *a:Proc(error=error)),patch.object(ex.subprocess,'check_output',query):return ex.observe('GPU-fixture')
 def test_vanished_non_gpu_process_is_not_unknown_mps(self):
  for e in (ProcessLookupError(errno.ESRCH,'gone'),FileNotFoundError(errno.ENOENT,'gone')):
   s=self.run_case(e);self.assertEqual(s['mps_processes'],[]);ex.verify(s,'GPU-fixture')
 def test_permissions_still_block(self):
  s=self.run_case(PermissionError(errno.EACCES,'denied'))
  with self.assertRaises(ValueError):ex.verify(s,'GPU-fixture')
 def test_other_io_error_not_silenced(self):
  with self.assertRaises(OSError):self.run_case(OSError(errno.EIO,'I/O'))
 def test_unknown_gpu_identity_still_blocks(self):
  with patch.object(ex,'process_identity',side_effect=ProcessLookupError(errno.ESRCH,'gone')):s=self.run_case(None,'GPU-fixture, 1234, 10\n')
  self.assertTrue(s['compute_apps'][0]['identity_unknown'])
  with self.assertRaises(ValueError):ex.verify(s,'GPU-fixture')
