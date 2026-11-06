"""Full14 file/latent gates and complete8 score acceptance with explicit CPU media."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_read_write_artifacts_r1 as reader
from wcomr import cara_read_write_scores_r1 as scores
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import sha
from wcomr.policy_price_terminal_r1 import record
from check_cara_read_write_packet_fixture_r1 import packet
from test_cara_s_endpoint_artifacts_r1 import write_media, decode
from wcomr.cara_read_write_identity_r1 import M1


class Postrelease(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.args = packet(self.temp.name, write_media)

    def read(self):
        with patch.object(reader, 'decode_video', side_effect=decode):
            return reader.released_artifacts(**self.args)

    def test_full14_latent_RGB_controls_and_only8_pairs(self):
        saved = self.read()
        self.assertEqual(len(saved['artifacts']), 14)
        self.assertEqual(len(saved['manifest']['pairs']), 8)
        self.assertEqual(saved['manifest']['identity_controls_passed'], 4)
        self.assertFalse(saved['manifest']['scientific_accepted'])

    def test_no_artifact_read_before_physical_financial_closure(self):
        self.args['capture']['process_observations']['runner']['original_live'] = None
        with patch.object(reader, 'decode_video', side_effect=AssertionError('Read before release')):
            with self.assertRaisesRegex(ValueError, 'Original process live, unknown'):
                reader.released_artifacts(**self.args)

    def test_changed_latent_or_video_bytes_refused(self):
        stage = Path(record(self.args['capture'], 'launch')['stage'])
        collection = json.loads((stage.parents[1]/'outputs/cara-read-write-M1-cpu-full14/read-write-collection.json').read_text())
        for artifact in (collection['rows'][0]['tensor_artifact'], collection['rows'][0]['result']['video_artifact']):
            path = Path(artifact['path'])
            original = path.read_bytes()
            path.write_bytes(original+b' ')
            with self.subTest(path=str(path)), self.assertRaisesRegex(ValueError, 'artifact bytes differ'):
                self.read()
            path.write_bytes(original)

    def test_missing_corner_wrong_parent_or_pair_count_refused(self):
        stage = Path(record(self.args['capture'], 'launch')['stage'])
        path = stage.parents[1]/'outputs/cara-read-write-M1-cpu-full14/read-write-collection.json'
        value = json.loads(path.read_text())
        from wcomr.cara_read_write_runner_binding_r1 import CARD
        card = json.loads((stage/CARD).read_text())
        for fault in ('partial', 'parent', 'pairs', 'fallback'):
            changed = copy.deepcopy(value)
            if fault == 'partial':
                changed['rows'].pop()
            elif fault == 'parent':
                changed['rows'][3]['result']['intervention']['parent_state_sha256'] = 'b'*64
            elif fault == 'pairs':
                changed['rows'][3]['result']['physical_model_pairs'] = 36
            else:
                changed['rows'][3]['result']['semantic_history'][8]['fallback_reason'] = 'CPU intentional fallback'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                reader.check_collection(card, changed, cpu_validation=True)


def score_fixture(root, *, identity=M1):
    args = packet(root, write_media, identity=identity)
    with patch.object(reader, 'decode_video', side_effect=decode):
        saved = reader.released_artifacts(**args)
    config = scores.bind_scorer(saved, dict(torch_home='/CPU-ONLY/torch', piq_site='/CPU-ONLY/site', weights_sha256={}), cpu_validation=True)
    manifest_sha = hashlib.sha256((json.dumps(config, indent=2)+'\n').encode()).hexdigest()
    rows = []
    for pair in config['pairs']:
        candidate = pair['candidate']
        alex, ssim = [.3]*93, [.8]*93
        rows.append(dict(id=pair['id'], member=candidate['member'], role=candidate['role'],
            candidate=copy.deepcopy(candidate), reference=copy.deepcopy(pair['reference']), status='COMPLETE',
            frames=93, temporal_frame_pairs=92, PTS_equal=True,
            decoded_RGB_sha256=[saved['decoded'][pair[s]['slot_id']]['RGB_sha256'] for s in ('candidate', 'reference')],
            Alex_frames=alex, SSIM_frames=ssim, Alex=sum(alex)/93, SSIM=sum(ssim)/93,
            Alex_worst=.3, Alex_q95_higher=.3, Alex_first_worst_frame_zero_based=0,
            MSE_video=.01, PSNR_is_infinite=False, PSNR_video_dB=20., reference_temporal_L1=.1,
            reference_gradient_L1=.2, candidate_gradient_energy=1., reference_gradient_energy=1.,
            gradient_energy_ratio=1., gradient_ratio_status='FINITE'))
    identity = dict(pid=100, start_ticks=1000, host_view=dict(boot_id='CPU_FIXTURE', pid_namespace_inode=123))
    result = dict(status='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED', registered_pairs=[p['id'] for p in config['pairs']], rows=rows,
        manifest_sha256=manifest_sha, analysis_scope_sha256=config['scope_sha256'], protocol_sha256=config['protocol_sha256'],
        worker_sha256=config['scorer_source_sha256'][scores.WORKER], CPU_fixture_only=True, CUDA_initialized=False,
        GPU_submissions=0, source_actual_sha256=config['scorer_source_sha256'], original_identity=identity)
    execution = dict(kind='ACTUAL_CPU_FIXTURE_CHILD', exit_code=0, original_process_ended=True, GPU_hidden=True,
        original_identity=identity, original_observation=dict(original_live=False, status='ORIGINAL_NOT_LIVE',
            original_pid=100, original_start_ticks=1000, observed_host_view=identity['host_view']),
        manifest_sha256=manifest_sha, source_actual_sha256=config['scorer_source_sha256'], wall_seconds=1., result_sha256=digest(result))
    return dict(packet=saved, config=config, manifest_sha256=manifest_sha, result=result, execution=execution, cpu_validation=True)


class Scores(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.args = score_fixture(self.temp.name)

    def test_complete8_has_no_old_scores_or_scientific_promotion(self):
        accepted = scores.accept_scores(**self.args)
        self.assertEqual((accepted['new_scored_pairs'], accepted['reused_original_rows']), (8, 0))
        self.assertFalse(accepted['main_method_established'])

    def test_missing_pair_reordered_pair_curve_and_reduction_refused(self):
        for fault in ('missing', 'reordered', 'curve', 'reduction', 'RGB'):
            args = copy.deepcopy(self.args)
            rows = args['result']['rows']
            if fault == 'missing':
                rows.pop()
            elif fault == 'reordered':
                rows.reverse()
            elif fault == 'curve':
                rows[0]['Alex_frames'].pop()
            elif fault == 'reduction':
                rows[0]['Alex'] = .9
            else:
                rows[0]['decoded_RGB_sha256'] = ['0'*64]*2
            args['execution']['result_sha256'] = digest(args['result'])
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                scores.accept_scores(**args)

    def test_original_child_must_exit(self):
        self.args['execution']['original_process_ended'] = False
        with self.assertRaisesRegex(ValueError, 'child must exit'):
            scores.accept_scores(**self.args)

    def test_zero_reference_gradient_and_infinite_PSNR_preserved(self):
        row = self.args['result']['rows'][0]
        row.update(MSE_video=0, PSNR_video_dB='+inf', PSNR_is_infinite=True,
            reference_gradient_energy=0, gradient_energy_ratio=None, gradient_ratio_status='ZERO_REFERENCE_ENERGY')
        self.args['execution']['result_sha256'] = digest(self.args['result'])
        scores.accept_scores(**self.args)


if __name__ == '__main__':
    unittest.main()
