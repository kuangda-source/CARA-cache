"""Full release and file I/O; local decoder is an explicit metadata fixture."""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_s_endpoint_artifacts_r1 as reader
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_endpoint_scoring_manifest_r1 import validate_pair_identities
from wcomr.policy_price_terminal_r1 import record
from test_cara_budget_lifecycle_r1 import put
from check_cara_s_endpoint_artifact_fixture_r1 import packet


def write_media(path,tag):path.write_text(json.dumps(dict(CPU_metadata_only=True,tag=tag)))


def decode(artifact,*,shape):
    value=json.loads(Path(artifact['path']).read_text());assert value['CPU_metadata_only']
    return dict(RGB_sha256=hashlib.sha256(value['tag'].encode()).hexdigest(),frames=93,shape=list(shape),fps=16,
                PTS=[[p.numerator,p.denominator] for p in (Fraction(i,16) for i in range(93))])


class ArtifactControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.args=packet(Path(self.temp.name)/'case',write_media,decode)

    def run_reader(self):
        with patch.object(reader,'decode_video',side_effect=decode):return reader.postrelease_manifest(**self.args)

    def test_complete32_preserves12_old_rows_and_scope(self):
        result=self.run_reader();manifest=result['manifest']
        self.assertEqual(len(result['artifacts']),32);self.assertEqual(len(manifest['pairs']),12)
        old={r['id']:r for r in record(self.args['capture'],'original_scores')['rows']}
        self.assertTrue(all(row==old[row['id']] for row in manifest['reused_rows']))
        self.assertTrue(all(p['candidate']['scope_sha256']!=p['reference']['scope_sha256'] for p in manifest['pairs']))
        self.assertEqual(manifest['metrics_computed'],0);self.assertFalse(manifest['scoring_dispatch_allowed'])

    def test_alias25_keeps24_logical_and8_new_pairs(self):
        self.args=packet(Path(self.temp.name)/'alias',write_media,decode,alias=True)
        manifest=self.run_reader()['manifest']
        self.assertEqual(manifest['physical_paths'],25);self.assertEqual(len(manifest['pairs']),8)
        self.assertEqual(len(manifest['formal_positions']),24)
        self.assertEqual(len(set(p['score_id'] for p in manifest['formal_positions'])),20)

    def test_no_artifact_read_before_release(self):
        self.args['capture']['own_UUID_lock_free']=False
        with patch.object(reader,'decode_video',side_effect=AssertionError('early frame read')):
            with self.assertRaises(ValueError):reader.postrelease_manifest(**self.args)

    def test_partial_collection_refused(self):
        collection=record(self.args['capture'],'collection');collection['rows'][-1]['status']='NOT_REACHED'
        put(self.args['capture'],'collection',collection)
        with self.assertRaisesRegex(ValueError,'Incomplete'):self.run_reader()

    def test_changed_video_rejected(self):
        path=record(self.args['capture'],'collection')['rows'][0]['result']['video_path']
        Path(path).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'artifact bytes'):self.run_reader()

    def test_changed_tensor_rejected(self):
        path=record(self.args['capture'],'collection')['rows'][0]['tensor_artifact']['path']
        Path(path).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'artifact bytes'):self.run_reader()

    def test_changed_registered_argument_rejected(self):
        path=Path(record(self.args['capture'],'collection')['rows'][0]['result']['video_path']).with_suffix('.json')
        args=json.loads(path.read_text());args['seed']=1;path.write_text(json.dumps(args))
        with self.assertRaisesRegex(ValueError,'registered request'):self.run_reader()

    def test_unregistered_default_change_rejected(self):
        path=Path(record(self.args['capture'],'collection')['rows'][0]['result']['video_path']).with_suffix('.json')
        args=json.loads(path.read_text());args['extra_conditioning']='changed';path.write_text(json.dumps(args))
        with self.assertRaisesRegex(ValueError,'conditioning/default'):self.run_reader()

    def test_pts_mismatch_rejected(self):
        def shifted(artifact,*,shape):
            value=decode(artifact,shape=shape)
            if '/outputs/' in artifact['path']:value['PTS'][0]=[1,16]
            return value
        with patch.object(reader,'decode_video',side_effect=shifted):
            with self.assertRaisesRegex(ValueError,'PTS differ'):reader.postrelease_manifest(**self.args)

    def test_rgb_replay_failure_rejected(self):
        rows=record(self.args['capture'],'collection')['rows']
        target=next(r['result']['video_path'] for r in rows if r['slot']['purpose']=='REPLAY_CONTROL')
        def changed(artifact,*,shape):
            value=decode(artifact,shape=shape)
            if artifact['path']==target:value['RGB_sha256']='0'*64
            return value
        with patch.object(reader,'decode_video',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'RGB identity control'):reader.postrelease_manifest(**self.args)

    def test_changed_original_score_row_rejected(self):
        capture=self.args['capture'];scores=record(capture,'original_scores')
        scores['rows'][0]['Alex']=100.;put(capture,'original_scores',scores)
        with self.assertRaisesRegex(ValueError,'registered proposal/scores'):self.run_reader()

    def test_old_scope_cannot_be_rewritten(self):
        manifest=self.run_reader()['manifest'];pair=manifest['pairs'][0]
        pair['reference']['scope_sha256']=manifest['analysis_scope_sha256']
        with self.assertRaisesRegex(ValueError,'reference scope'):validate_pair_identities(manifest)

    def test_reused_scores_not_new_pairs(self):
        manifest=self.run_reader()['manifest'];manifest['pairs'][0]['candidate']=copy.deepcopy(manifest['reused_rows'][0]['candidate'])
        with self.assertRaisesRegex(ValueError,'reference scope'):validate_pair_identities(manifest)

    def test_partial_new_pairs_rejected(self):
        manifest=self.run_reader()['manifest'];manifest['pairs'].pop()
        with self.assertRaisesRegex(ValueError,'denominator'):validate_pair_identities(manifest)

    def test_cpu_fixture_cannot_enter_production(self):
        self.args['cpu_validation']=False
        with self.assertRaisesRegex(ValueError,'CPU fixtures'):self.run_reader()


if __name__=='__main__':unittest.main()
