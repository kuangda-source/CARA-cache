import ast,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wc_four_card_bank24_native_transport_r3 import bridge
class NativeBridgeTests(unittest.TestCase):
 def test_reject_missing_actual_native_CPU(self):
  with self.assertRaises(ValueError):bridge('print(1)',{})
 def test_exact_command_literal_not_rewritten(self):
  code="print('CODE and RUNTIME remain original literals')"
  r=bridge(code,dict(status='NATIVE_CONTROL_PYTHON_CPU_PASS',exit_code=0,job='/own/private/runtime'))
  ast.parse(r,feature_version=(3,8));self.assertIn(repr(code),r);self.assertIn('CUDA_VISIBLE_DEVICES',r)
if __name__=='__main__':unittest.main()
