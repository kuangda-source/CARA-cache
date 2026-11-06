"""Launch contract, immutable source handoff and duplicate intent gates; CPU only."""
import sys,unittest,tempfile,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
import wc_four_card_cara_shared66_gpu_r1 as c

class Dispatch(unittest.TestCase):
 def test_remote_templates(self):
  for name in ('PREPARE','PREFLIGHT','LAUNCH_PREFIX','LAUNCH_SUFFIX','CAPTURE'):
   compile(getattr(c,name),name,'exec')
  self.assertIn('wc_cara_shared66_host_guardian_r1.py',c.LAUNCH_SUFFIX)
  self.assertIn("'quality-binding.json'",c.PREFLIGHT)
  self.assertIn('history104-storage.json',c.CAPTURE)
 def test_duplicate_intent_exits_without_dispatch(self):
  import io,contextlib
  with tempfile.TemporaryDirectory() as d:
   Path(d,'pg-GPU-intent.json').write_text('{"launch_id":"existing"}')
   with patch('sys.stdin',io.StringIO(json.dumps({'stage_ref':{'stage':d}}))),contextlib.redirect_stdout(io.StringIO()) as output:
    env={}
    try:
     with self.assertRaises(SystemExit):exec(c.LAUNCH_PREFIX,env)
    finally:
     if 'lock' in env:env['lock'].close()
   self.assertEqual(json.loads(output.getvalue())['original']['launch_id'],'existing')
 def test_prepare_exact_accepted_closure_and_binding(self):
  import hashlib
  root=c.REPO
  a=SimpleNamespace(cpu_capture=root/'reports/cara_CAL66_combination_CPU_exited_r3_20261025.json',cpu_acceptance=root/'reports/cara_CAL66_combination_CPU_accepted_r3_20261025.json',storage_ref=Path('storage'),stage_name='cara-shared66-full-ada-r1-20261025',output=Path('unused'))
  original=c.read
  def read(p):return {'storage_contract':{'run_id':c.RUN}} if p==Path('storage') else original(p)
  sent=[]
  with patch.object(c,'read',read),patch.object(c,'write'),patch.object(c,'ssh',side_effect=lambda code,data:sent.append(data) or {'status':'fixture'}):c.prepare(a)
  import base64
  data=sent[0];config=json.loads(base64.b64decode(data['files']['pg-config.json']))
  self.assertEqual(config['scope_counts']['total_paths'],66);self.assertEqual(config['billed_limit_GPUh'],8)
  self.assertEqual(base64.b64decode(data['files']['quality-binding.json']),(root/'reports/cara_CAL66_quality_binding_20261025.json').read_bytes())
  self.assertTrue(all(hashlib.sha256(base64.b64decode(raw)).hexdigest()==data['hashes'][name] for name,raw in data['files'].items()))
 def test_bad_authorization_never_contacts_server(self):
  with tempfile.TemporaryDirectory() as d:
   s=Path(d,'stage');s.write_text('{}');a=Path(d,'auth');a.write_text('{}')
   with patch.object(c,'ssh') as ssh:
    with self.assertRaises(ValueError):c.launch(SimpleNamespace(stage_ref=s,recovery_authorization=a))
    ssh.assert_not_called()
if __name__=='__main__':unittest.main()
