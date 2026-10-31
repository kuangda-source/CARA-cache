"""Fresh original asset I/O and dispatch admission ordering; no GPU access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_s_endpoint_reuse_admission_r1 as reuse
from wcomr import cara_s_endpoint_gpu_dispatch_r1 as dispatch
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import sha
from wcomr.policy_price_terminal_r1 import record
from check_cara_s_endpoint_artifact_fixture_r1 import packet
from test_cara_s_endpoint_artifacts_r1 import write_media,decode

ROOT=Path(__file__).resolve().parents[1]


class ReuseAdmission(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name)/'case';self.packet=packet(self.project,write_media,decode)
        self.proposal=self.packet['proposal'];self.scores=record(self.packet['capture'],'original_scores')

    def verify(self):return reuse.verify_reuse(self.project,self.proposal,self.scores,cpu_validation=True)

    def test_complete32_files_and12_unchanged_scores(self):
        before=copy.deepcopy(self.scores);result=self.verify()
        self.assertEqual(len(result['files']),32);self.assertEqual(result['original_videos'],16)
        self.assertEqual(result['reused_score_rows'],12);self.assertEqual(self.scores,before)
        self.assertEqual(result['metrics_computed'],0);self.assertFalse(result['active_GPU_outputs_read'])
        self.assertTrue(all(r['stable_during_read'] and sha(r['path'])==r['sha256'] for r in result['files']))

    def test_changed_video(self):
        Path(self.proposal['reference_sources'][0]['source']['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'artifact bytes'):self.verify()

    def test_changed_arguments(self):
        Path(self.proposal['reference_sources'][0]['source']['path']).with_suffix('.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'saved request'):self.verify()

    def test_missing_video(self):
        Path(self.proposal['reference_sources'][0]['source']['path']).unlink()
        with self.assertRaises(FileNotFoundError):self.verify()

    def test_partial_scores(self):
        self.scores['rows'].pop()
        with self.assertRaisesRegex(ValueError,'complete32'):self.verify()

    def test_duplicate_score_id(self):
        self.scores['rows'][1]['id']=self.scores['rows'][0]['id']
        with self.assertRaisesRegex(ValueError,'unique'):self.verify()

    def test_changed_reused_score(self):
        score_id=next(r['score_id'] for r in self.proposal['formal_matrix'] if r['mode']=='REUSE_COMPLETE_SCORE')
        row=next(r for r in self.scores['rows'] if r['id']==score_id);row['Alex']=999
        with self.assertRaisesRegex(ValueError,'reused complete score'):self.verify()

    def test_missing_native(self):
        self.proposal['reference_sources'].pop();self.proposal['scope_sha256']=digest({k:v for k,v in self.proposal.items() if k!='scope_sha256'})
        with self.assertRaisesRegex(ValueError,'four original Native'):self.verify()

    def test_fixture_not_production(self):
        with self.assertRaisesRegex(ValueError,'fixture mode'):reuse.verify_reuse(self.project,self.proposal,self.scores)

    def test_active_path_refused_before_read(self):
        descriptor=copy.deepcopy(self.proposal['reference_sources'][0]['source'])
        descriptor['path']=str(self.project/'outputs/cara-budget-calibration-14gpuh-r2-20261031/partial.mp4')
        with patch.object(reuse,'expected_sources',return_value=[descriptor]),patch.object(reuse,'verify_file') as read:
            with self.assertRaisesRegex(ValueError,'Only completed original'):self.verify()
        read.assert_not_called()

    def test_original_stage_binding_and_changed_scores(self):
        stage=self.project/'.sync/reuse-admission-CPU';stage.mkdir(parents=True)
        for path,value in ((reuse.PROPOSAL,self.proposal),(reuse.ORIGINAL_SCORES,self.scores)):
            target=stage/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(value)+'\n')
        target=stage/reuse.SOURCE;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/reuse.SOURCE).read_bytes())
        registration=dict(payload_sha256={p:sha(stage/p) for p in (reuse.SOURCE,reuse.PROPOSAL,reuse.ORIGINAL_SCORES)})
        (stage/'registration.json').write_text(json.dumps(registration)+'\n')
        self.assertEqual(len(reuse.verify_stage(stage,cpu_validation=True)['files']),32)
        (stage/reuse.ORIGINAL_SCORES).write_text('{}')
        with self.assertRaisesRegex(ValueError,'Registered original reuse'):reuse.verify_stage(stage,cpu_validation=True)

    def test_reuse_refused_before_common_resource_admission(self):
        with patch.object(dispatch,'verify_reuse_stage',side_effect=ValueError('Missing old asset')),\
             patch.object(dispatch,'common_fresh_resources') as common:
            with self.assertRaisesRegex(ValueError,'Missing old asset'):dispatch.fresh_resources(self.project,'stage',{}, {})
        common.assert_not_called()

    def test_dispatch_retains_fresh_reuse_evidence(self):
        proof=self.verify();storage=object()
        with patch.object(dispatch,'verify_reuse_stage',return_value=proof),\
             patch.object(dispatch,'common_fresh_resources',return_value=(storage,{'GPU_fixture':True})):
            actual,resources=dispatch.fresh_resources(self.project,'stage',{}, {})
        self.assertIs(actual,storage);self.assertEqual(resources['original_endpoint_reuse'],proof)


if __name__=='__main__':unittest.main()
