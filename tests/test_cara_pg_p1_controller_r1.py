"""No-dispatch faults and source binding for the new PG controller."""
import argparse,copy,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wc_four_card_cara_pg_gpu_r1 as controller
from wcomr.immutable_stage_payload_r1 import local_python_closure

class Controller(unittest.TestCase):
 def test_all_remote_programs_parse(self):
  for source in [controller.PREPARE,controller.PREFLIGHT,controller.LAUNCH_PREFIX+controller.PREFLIGHT.replace('p=json.load(sys.stdin);','')+controller.LAUNCH_SUFFIX,controller.CAPTURE]:compile(source,'PG_REMOTE','exec')
 def test_existing_intent_short_circuits_before_credential_or_launch(self):
  with tempfile.TemporaryDirectory() as folder:
   stage=Path(folder);(stage/'pg-GPU-intent.json').write_text(json.dumps({'launch_id':'ORIGINAL'}))
   out=io.StringIO()
   namespace={'__name__':'CPU_FIXTURE'}
   try:
    with patch.object(sys,'stdin',io.StringIO(json.dumps({'stage_ref':{'stage':folder}}))),patch.object(sys,'stdout',out):
     with self.assertRaises(SystemExit):exec(controller.LAUNCH_PREFIX,namespace)
   finally:
    if 'lock' in namespace:namespace['lock'].close()
   self.assertEqual(json.loads(out.getvalue())['original']['launch_id'],'ORIGINAL')
 def test_resource_wait_never_reads_secret_or_dispatches(self):
  with tempfile.TemporaryDirectory() as f:
   path=Path(f)/'stage.json';path.write_text('{}');a=argparse.Namespace(stage_ref=path,gpu_uuid='GPU-fixture',output=Path(f)/'receipt.json')
   with patch.object(controller,'published',return_value=('source',{})),patch.object(controller,'ssh',return_value={'admissible':False,'status':'GPU_BUSY'}) as remote,patch.object(controller,'saved_secret',side_effect=AssertionError('NO_SECRET')):
    controller.launch(a)
   self.assertEqual(remote.call_count,1)
 def test_unknown_preflight_never_dispatches(self):
  with tempfile.TemporaryDirectory() as f:
   path=Path(f)/'stage.json';path.write_text('{}');a=argparse.Namespace(stage_ref=path,gpu_uuid='GPU-fixture',output=Path(f)/'receipt.json')
   with patch.object(controller,'published',return_value=('source',{})),patch.object(controller,'ssh',return_value={'status':'UNKNOWN'}) as remote,patch.object(controller,'saved_secret',side_effect=AssertionError('NO_SECRET')):controller.launch(a)
   self.assertEqual(remote.call_count,1)
 def test_launch_uses_verified_host_wrapper_and_fsync_intent(self):
  source=controller.LAUNCH_SUFFIX
  self.assertIn("command=[host_python",source);self.assertNotIn('command=[sys.executable',source)
  self.assertIn('os.fsync',source);self.assertIn("auth['independent_CPU_acceptance_sha256']",source)
  self.assertNotIn('accepted_base64',source);self.assertNotIn('price-GPU',source)
 def test_controller_source_closure_includes_terminal_and_package_export(self):
  result=local_python_closure(ROOT,['scripts/wc_four_card_cara_pg_gpu_r1.py'])
  self.assertIn('src/wcomr/policy_generator_r1/production_terminal.py',result)
  self.assertIn('src/wcomr/policy_generator_r1/__init__.py',result)
 def test_original_quote_stays_complete64(self):
  q=json.loads((ROOT/controller.QUOTE).read_text());self.assertEqual(len(q['matrix']),64);self.assertEqual(q['billed_limit_GPUh'],10.5)
if __name__=='__main__':unittest.main()
