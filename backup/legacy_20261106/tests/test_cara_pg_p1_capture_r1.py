"""Original-file collector joins the tested terminal replay; GPU/decode mocked here."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_cara_pg_p1_combination_r1 import fixture
from wcomr.policy_generator_r1.production_capture import collect
from wcomr.policy_generator_r1.production_stage import RUN
from wcomr.policy_generator_r1.production_terminal import scientific
from wcomr.policy_price_terminal_r1 import record

class OriginalFileCollection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.packet=fixture()
 def test_real_original_file_enumeration_replays_complete_decision(self):
  v=self.packet
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);stage=root/'.sync/PG';out=root/'outputs'/RUN;stage.mkdir(parents=True);out.mkdir(parents=True)
   names={'runner':'runner.json','consumer':'consumer.json','native_clock':'native-clock.json','post':'post-results.json','post_exit':'post-exit.json','supervisor':'supervisor.json','billing':'billing.json','monitor_final':'exclusive-monitor-final.json'}
   for key,name in names.items():(out/name).write_text(v['files'][key]['raw_utf8'])
   names={'registration':'registration.json','config':'pg-config.json','quote':'pg-whole-quote.json','CPU_acceptance':'pg-independent-CPU-acceptance.json','authorization':'pg-GPU-authorization.json','guardian':'pg-host-guardian.json','ready':'pg-runner-context-ready.json','grant':'pg-runner-context-granted.json','old_bundle':'pg-old-labels.json','new_bundle':'pg-clean-prices.json','old_acceptance':'pg-old-acceptance.json','price_acceptance':'pg-price-acceptance.json'}
   for key,name in names.items():(stage/name).write_text(v['files'][key]['raw_utf8'])
   (out/'native-monitor-prefix.jsonl').write_text(v['native_monitor_prefix_raw_utf8']);(out/'exclusive-monitor.jsonl').write_text(v['monitor_raw_utf8'])
   manifest=stage/'plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json';manifest.parent.mkdir(parents=True);manifest.write_text(json.dumps({'selected_sources':[{'name':s} for s in v['select_members']]}))
   paths={}
   for key,raw in v['requests'].items():
    d=out/key;d.mkdir();(d/'request.json').write_text(raw['raw_utf8'])
    if key in v['scores']:(d/'score.json').write_text(v['scores'][key]['raw_utf8'])
   rows=record(v,'runner')['batch']['rows']
   for row in rows:
    for key in ('video_artifact','final_latent_artifact'):
     if key in row:paths[row[key]['path']]=row[key]
   def verify(ref,base):
    if ref['path'].endswith('score.json'):
     return out/Path(ref['path']).parent.name/'score.json'
    return Path(ref['path'])
   with patch('wcomr.policy_generator_r1.production_capture.verify_artifact',side_effect=verify),patch('wcomr.policy_generator_r1.production_capture.artifact',side_effect=lambda p,r:paths[str(p)]),patch('wcomr.rv0_video_reader.probe_video',return_value={'frames':93}):
    captured=collect(root,stage,v['launch'])
   self.assertEqual(scientific(captured),scientific(v))
 def test_early_stop_retains_original_runner_without_native_clock(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);stage=root/'.sync/PG';out=root/'outputs'/RUN;stage.mkdir(parents=True);out.mkdir(parents=True)
   (out/'runner.json').write_text(json.dumps({'status':'TECH_FAILED'}))
   manifest=stage/'plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json';manifest.parent.mkdir(parents=True);manifest.write_text(json.dumps({'selected_sources':[{'name':'e'},{'name':'f'}]}))
   v=collect(root,stage,{})
   self.assertTrue(v['files']['runner']['exists']);self.assertFalse(v['files']['native_clock']['exists']);self.assertEqual(v['native_monitor_prefix_raw_utf8'],'')
if __name__=='__main__':unittest.main()
