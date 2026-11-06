import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('accept_shared',ROOT/'scripts/audit_cara_shared_exploration_cpu_r1.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Acceptance(unittest.TestCase):
 def setUp(self):self.cap=json.loads((ROOT/'reports/cara_shared_CAL106_CPU_terminal_r1_20261025.json').read_text())
 def test_original(self):self.assertTrue(mod.accept(self.cap)['production_entry_CPU_accepted'])
 def test_running(self):
  self.cap['container']['state']['Running']=True
  with self.assertRaises(ValueError):mod.accept(self.cap)
 def test_GPU_visible(self):
  self.cap['container']['device_requests']=[{'Count':1}]
  with self.assertRaises(ValueError):mod.accept(self.cap)
 def test_changed_runtime(self):
  k=next(iter(self.cap['runtime_actual_sha256']));self.cap['runtime_actual_sha256'][k]='0'*64
  with self.assertRaises(ValueError):mod.accept(self.cap)
 def test_missing_role(self):
  self.cap['proof']['data']['numeric']['checks'][0]['roles'].pop()
  with self.assertRaises(ValueError):mod.accept(self.cap)
 def test_wrong_updates(self):
  self.cap['proof']['data']['numeric']['checks'][0]['roles'][0]['updates']=35
  with self.assertRaises(ValueError):mod.accept(self.cap)
 def test_changed_alpha_check(self):
  self.cap['proof']['data']['numeric']['checks'][0]['original_alpha_and_D_preserved']=False
  with self.assertRaises(ValueError):mod.accept(self.cap)
 def test_no_implicit_GPU(self):
  a=mod.accept(self.cap);self.assertFalse(a['GPU_dispatch_ready']);self.assertFalse(a['full_GPU_lifecycle_accepted']);self.assertFalse(a['quality_or_speed_result'])
if __name__=='__main__':unittest.main()
