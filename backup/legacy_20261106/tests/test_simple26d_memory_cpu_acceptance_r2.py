"""Reject corrupted saved CPU proofs before a GPU launch; no server access."""
import copy,gzip,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('memory_acceptance',ROOT/'scripts/accept_wc_simple26d_memory_cpu_r2.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class AcceptanceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.value=json.loads(gzip.decompress((ROOT/'reports/wc_simple26d_memory_full144_CPU_collection_20261015_2352.json.gz').read_bytes()))
 def test_saved_immutable_complete_receipt_accepted(self):
  self.assertEqual(m.accept(self.value)['CPU_paths'],144)
 def test_negative_source_scope_process_budget_and_GPU_flags(self):
  mutations=[lambda v:v['payload_verified'].__setitem__(next(iter(v['payload_verified'])),False),
   lambda v:v['numeric'].__setitem__('actual_CPU_paths',96),
   lambda v:v['numeric'].__setitem__('repair_complete_paths',48),
   lambda v:v['numeric'].__setitem__('CUDA_initialized',True),
   lambda v:v['production'].__setitem__('source_revision','foreign'),
   lambda v:v['production'].__setitem__('sampling_CPU_sha256','foreign'),
   lambda v:v['bundle']['commands'][-1].__setitem__('exit_code',1),
   lambda v:v['production']['matrix'].pop(),
   lambda v:v['process'].__setitem__('state','R'),
   lambda v:v['pool'].__setitem__('used_gpu_hours',0.)]
  for mutate in mutations:
   bad=copy.deepcopy(self.value);mutate(bad)
   with self.assertRaises(AssertionError):m.accept(bad)
if __name__=='__main__':unittest.main()
