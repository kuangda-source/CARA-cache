"""Actual observe path with disappearing /proc records; preserve fail-closed gates."""
import errno,unittest,time
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from wcomr.policy_generator_r1 import production_exclusive as ex
class ProcRace(unittest.TestCase):
 def probe(self,error=None,mps=False,gpu_unknown=False):
  def query(cmd,**kw):
   return 'GPU-test, Exclusive_Process\n' if '--query-gpu=' in ' '.join(cmd) else ('GPU-test, 123, 64\n' if gpu_unknown else '')
  def read(p,*a,**kw):
   if error:raise error
   return 'nvidia-cuda-mps-server' if mps else 'python'
  with patch.object(ex.subprocess,'check_output',query),patch.object(ex.Path,'iterdir',lambda p:iter([Path('/proc/99999')])),patch.object(ex.Path,'read_text',read),patch.object(ex,'process_identity',side_effect=ProcessLookupError(errno.ESRCH,'gone')):
   return ex.observe('GPU-test')
 def test_esrch_and_enoent_continue_exact_gate(self):
  for e in [ProcessLookupError(errno.ESRCH,'gone'),FileNotFoundError(errno.ENOENT,'gone')]:
   for _ in range(3):ex.verify(self.probe(e),'GPU-test')
 def test_permission_fails_closed(self):
  with self.assertRaises(ValueError):ex.verify(self.probe(PermissionError(errno.EACCES,'denied')),'GPU-test')
 def test_other_io_still_raises(self):
  with self.assertRaises(OSError):self.probe(OSError(errno.EIO,'io error'))
 def test_mps_still_rejected(self):
  with self.assertRaises(ValueError):ex.verify(self.probe(mps=True),'GPU-test')
 def test_unknown_GPU_identity_still_rejected(self):
  with self.assertRaises(ValueError):ex.verify(self.probe(gpu_unknown=True),'GPU-test',dict(pid=123,start_ticks=1,uid=1004))
