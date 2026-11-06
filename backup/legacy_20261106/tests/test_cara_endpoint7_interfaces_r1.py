"""46/28/16/13 interface composition with temporary ledgers and declared synthetic media."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from wcomr import cara_s_endpoint_scores_r1 as scores
from wcomr import cara_s_endpoint_artifacts_r1 as artifacts
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_plan_r1 import validate
from test_cara_s_endpoint_scores_r1 import fixture
from test_cara_s_endpoint_runner_binding_r1 import Fixture
from check_cara_s_endpoint_artifact_fixture_r2 import packet
from test_cara_s_endpoint_artifacts_r1 import write_media,decode
class SevenInterfaces(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
 def test_entry_binding46(self):
  f=Fixture(Path(self.tmp.name)/'entry',endpoint7=True);*_,context=f.validate()
  self.assertEqual(context['physical_paths'],46);self.assertEqual(f.profile['new_scoring_pairs'],16)
  f.auth['execution_authorized']=False;f.write_all()
  with self.assertRaises(ValueError):f.validate()
 def test_complete28_scores_and_original12(self):
  args=fixture(Path(self.tmp.name)/'scores',endpoint7=True)
  accepted=scores.accept_scores(**args)
  self.assertEqual((accepted['formal_logical_positions'],accepted['new_scored_pairs'],accepted['reused_original_rows']),(28,16,12))
  self.assertEqual(args['config']['physical_paths'],46);self.assertEqual(args['config']['identity_controls_passed'],13)
  self.assertEqual(args['config']['CPU_bound']['max_pairs'],16)
  for r in args['config']['reused_rows']:self.assertEqual(accepted['source_rows'][r['id']],r)
  args['result']['rows'].pop();args['execution']['result_sha256']=digest(args['result'])
  with self.assertRaisesRegex(ValueError,'denominator'):scores.accept_scores(**args)
 def test_all13_controls_required(self):
  args=packet(Path(self.tmp.name)/'controls',write_media,decode,endpoint7=True)
  args['proposal']['identity_controls'].pop()
  with patch.object(artifacts,'decode_video',side_effect=decode),self.assertRaises(ValueError):artifacts.postrelease_manifest(**args)
 def test_f19_replay_identity_cannot_change(self):
  args=packet(Path(self.tmp.name)/'f19',write_media,decode,endpoint7=True)
  def corrupt(artifact,**kw):
   d=decode(artifact,**kw)
   if '/B/' in artifact['path'] and 'F19_C' in Path(artifact['path']).read_text():d['RGB_sha256']='0'*64
   return d
  with patch.object(artifacts,'decode_video',side_effect=corrupt),self.assertRaisesRegex(ValueError,'RGB identity control'):artifacts.postrelease_manifest(**args)
 def test_score16_bound_refused(self):
  args=fixture(Path(self.tmp.name)/'bound',endpoint7=True)
  args['config']['CPU_bound']['max_pairs']=12
  with self.assertRaises(ValueError):scores.accept_scores(**args)
 def test_duplicate_physical_position_refused(self):
  root=Path(__file__).resolve().parents[1];p=json.loads((root/'configs/cara_endpoint_proposal.json').read_text())
  p['physical_matrix'][-1]=copy.deepcopy(p['physical_matrix'][-2])
  with self.assertRaises(ValueError):validate(p)
 def test_unreleased_refused(self):
  args=fixture(Path(self.tmp.name)/'unreleased',endpoint7=True)
  args['packet']['manifest']['GPU_released']=False
  with self.assertRaisesRegex(ValueError,'Released'):scores.accept_scores(**args)
 def test_original_capture28_and_active_no_scores(self):
  from test_cara_s_endpoint_score_capture_r1 import fixture as recovery_fixture,ended
  from wcomr import cara_s_endpoint_score_capture_r1 as reader
  args,container,out=recovery_fixture(Path(self.tmp.name)/'capture',endpoint7=True)
  with patch.object(reader,'inspect_original',return_value=dict(status='OBSERVED',container=container)),patch.object(reader,'observe_original_process',side_effect=ended):
   self.assertEqual(reader.recover(**args)['status'],'ORIGINAL_COMPLETE28_SCORE_ACCEPTED')
   container['State'].update(Status='running',Running=True,Pid=200)
   (out/'scores.json').unlink()
   self.assertEqual(reader.recover(**args)['status'],'ORIGINAL_SCORE_ACTIVE')
 def test_original_score_intent_two_hour_limit(self):
  from test_cara_s_endpoint_score_dispatch_r1 import fixture as dispatch_fixture
  from wcomr import cara_s_endpoint_score_dispatch_r1 as dispatcher
  from wcomr.cara_fast_fidelity_r1 import file_sha
  args,_,out,_=dispatch_fixture(Path(self.tmp.name)/'intent',endpoint7=True)
  with patch.object(dispatcher,'require_absent'),patch.object(dispatcher,'resource_admission',return_value={}),patch.object(dispatcher,'score_command',return_value=['CPU-ONLY']),patch.object(dispatcher.subprocess,'Popen') as spawn:
   spawn.return_value.pid=999
   dispatcher.dispatch(**args)
  control=args['stage']/'endpoint-score-control'
  intent=json.loads((control/'intent.json').read_text());config=json.loads((out/'manifest.json').read_text())
  intent.update(CPU_fixture_only=False,work_seconds=7200)
  config['CPU_bound']=scores.scorer_bound(config,False)
  (out/'manifest.json').write_text(json.dumps(config))
  intent['manifest_sha256']=file_sha(out/'manifest.json')
  (control/'intent.json').write_text(json.dumps(intent))
  with patch.object(dispatcher,'verify'):
   self.assertEqual(dispatcher.read_intent(args['stage'])[0]['work_seconds'],7200)
   intent['work_seconds']=14400;(control/'intent.json').write_text(json.dumps(intent))
   with self.assertRaisesRegex(ValueError,'frozen score intent'):dispatcher.read_intent(args['stage'])
if __name__=='__main__':unittest.main()
