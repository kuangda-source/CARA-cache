"""Synthetic metadata only: timing weighting, score identities and partial refusal."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_cara_s_endpoint_scores_r1 import fixture
from wcomr import cara_s_endpoint_artifacts_r1 as artifacts
from wcomr.cara_s_endpoint_scores_r1 import accept_scores
from wcomr.cara_endpoint7_analysis_r1 import analyze
from wcomr.cara_fast_spec_r1 import digest
from wcomr.policy_price_terminal_r1 import record

class Analysis(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  original=artifacts.postrelease_manifest;observed={}
  def read(**kw):observed.update(kw);return original(**kw)
  with patch.object(artifacts,'postrelease_manifest',side_effect=read):self.score=fixture(Path(self.tmp.name)/'score',endpoint7=True)
  self.card=observed['card'];self.collection=record(observed['capture'],'collection')
  self.accepted=accept_scores(**self.score)
 def run_analysis(self):return analyze(self.card,self.collection,self.accepted,**self.score)
 def test_complete_and_no_historical_time_pooling(self):
  report=self.run_analysis();self.assertEqual(len(report['per_member']),28)
  for group in report['prompt_equal_summaries'].values():
   self.assertIsNone(next(r for r in group if r['role']=='UNIFORM19_C')['time_mean'])
  self.assertTrue(all(len(r['metrics']['Alex_frames'])==93 for r in report['per_member']))
  self.assertFalse(report['new_selection']);self.assertFalse(report['new_freeze'])
 def test_prompt_means_before_group_mean(self):
  target='F19_RISKSWAP_C'
  for row in self.collection['rows']:
   if row['slot']['role']==target:
    row['result']['T_DD']=10. if row['slot']['purpose']=='REPEAT' else 2.
    row['result']['T_request']=20.
  packet=self.score['packet'];packet['release']['collection_sha256']=digest(self.collection)
  packet['manifest']['collection_sha256']=digest(self.collection)
  packet['manifest']['release_sha256']=digest(packet['release'])
  from wcomr.cara_s_endpoint_scores_r1 import bind_scorer
  import json,hashlib
  cfg=self.score['config'];cfg=bind_scorer(packet,{k:cfg[k] for k in ('torch_home','piq_site','weights_sha256')},cpu_validation=True)
  h=hashlib.sha256((json.dumps(cfg,indent=2)+'\n').encode()).hexdigest()
  self.score.update(config=cfg,manifest_sha256=h);self.score['result']['manifest_sha256']=h
  self.score['execution'].update(manifest_sha256=h,result_sha256=digest(self.score['result']))
  self.accepted=accept_scores(**self.score)
  group=self.run_analysis()['prompt_equal_summaries']['ALL'];row=next(r for r in group if r['role']==target)
  self.assertEqual(row['time_mean']['T_DD'],4.)
 def test_partial_collection_refused(self):
  self.collection['rows'].pop()
  with self.assertRaises(ValueError):self.run_analysis()
 def test_changed_accepted_score_refused(self):
  self.accepted['source_rows'][next(iter(self.accepted['source_rows']))]['Alex']=9.
  with self.assertRaisesRegex(ValueError,'complete28'):self.run_analysis()
 def test_fixture_cannot_be_production(self):
  self.score['cpu_validation']=False
  with self.assertRaises(ValueError):self.run_analysis()
if __name__=='__main__':unittest.main()
