"""Internal score-boundary controls using explicit synthetic completion records."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_budget_search_r1 import FIT_MEMBERS, SCHEDULE_SHA256
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_source_lifecycle_fit_scores_r1 import (
    bind_scorer, validate_config, accept_rows, accept_internal_scores,
)


class SourceLifecycleFitScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.packet = dict(schema='CARA_V1_INTERNAL_COMPLETE_FIT_ARTIFACTS_R1',
            purpose='P1_INTERNAL_FIT_CALIBRATION', CPU_fixture_only=True,
            FIT_members=list(FIT_MEMBERS), schedule_sha256=SCHEDULE_SHA256,
            source_revision='1'*40, launch_id='2'*32, context_sha256='3'*64,
            candidate_id='4'*64, query_id='K19-SA-1', score_shape=[93, 64, 64, 3], pairs=[])
        for i, member in enumerate(FIT_MEMBERS):
            pair = dict(member=member)
            for side in ('candidate', 'reference'):
                video = root/f'{side}-{i}.mp4'
                video.write_bytes(b'EXPLICIT_CPU_UNIT_FIXTURE_NOT_AN_ACTUAL_VIDEO')
                proof_file = root/f'{side}-{i}.json'
                proof = dict(status='COMPLETE', CPU_fixture_only=True, context_sha256='3'*64,
                    source_revision='1'*40, launch_id='2'*32, member=member, seed=0,
                    candidate_id='4'*64 if side == 'candidate' else 'NATIVE35',
                    solver_steps=36, guided_pairs=36, actual_updates=36, fallback_count=0,
                    video=dict(path=str(video), sha256=file_sha(video)))
                proof_file.write_text(json.dumps(proof))
                pair[side] = dict(member=member, seed=0, candidate_id=proof['candidate_id'],
                    proof_path=str(proof_file), proof_sha256=file_sha(proof_file), **proof['video'])
            self.packet['pairs'].append(pair)
        self.config = bind_scorer(self.packet, dict(torch_home='OFFLINE_FIXTURE',
            piq_site='CPU_FIXTURE', weights_sha256={}), cpu_validation=True)
        self.result = dict(status='COMPLETE_INTERNAL_FIT_NOT_SCIENTIFIC_ACCEPTANCE',
            config_sha256=digest(self.config),
            packet_sha256=digest(self.packet), source_sha256=self.config['source_sha256'],
            CPU_fixture_only=True, CUDA_initialized=False, GPU_submissions=0,
            original_identity={'explicit_CPU_unit_fixture': True}, rows=[])
        for pair in self.packet['pairs']:
            self.result['rows'].append(dict(member=pair['member'], candidate=pair['candidate'],
                reference=pair['reference'], status='COMPLETE', PTS_equal=True, frames=93,
                temporal_frame_pairs=92, Alex_frames=[0.]*93, SSIM_frames=[1.]*93, Alex=0., SSIM=1.,
                Alex_worst=0., Alex_q95_higher=0., Alex_first_worst_frame_zero_based=0,
                MSE_video=0., PSNR_is_infinite=True, PSNR_video_dB='+inf',
                reference_temporal_L1=0., reference_gradient_L1=0., candidate_gradient_energy=0.,
                reference_gradient_energy=0., gradient_energy_ratio=None, gradient_ratio_status='ZERO_REFERENCE_ENERGY',
                decoded_RGB_sha256=['5'*64, '5'*64]))

    def execution(self):
        return dict(config_sha256=digest(self.config), result_sha256=digest(self.result),
            original_process_ended=True, exit_code=0, GPU_hidden=True,
            source_sha256=self.config['source_sha256'], original_identity=self.result['original_identity'],
            wall_seconds=1.)

    def test_internal_complete_metrics_allowed_while_allocation_is_held_but_not_science(self):
        accepted = accept_internal_scores(self.config, self.result, self.execution(), cpu_validation=True)
        self.assertEqual(len(accepted['rows']), 2)
        self.assertEqual(accepted['status'], 'ACCEPTED_INTERNAL_CALIBRATION_ONLY')
        self.assertFalse(accepted['whole_card_scientific_accepted'])
        self.assertTrue(accepted['requires_original_terminal_release_and_settlement'])
        self.assertNotIn('release', self.config)
        with self.assertRaises(ValueError):
            validate_config(self.config, cpu_validation=False)

    def test_same_input_complete_proof_hash_and_no_fallback_required(self):
        for field, value in (('solver_steps', 35), ('fallback_count', 1), ('member', 'EXPOSED_CHECK'),
                             ('candidate_id', '0'*64), ('source_revision', '0'*40)):
            packet = copy.deepcopy(self.packet)
            descriptor = packet['pairs'][0]['candidate']
            proof_file = Path(descriptor['proof_path'])
            original = proof_file.read_bytes()
            proof = json.loads(original)
            proof[field] = value
            proof_file.write_text(json.dumps(proof))
            descriptor['proof_sha256'] = file_sha(proof_file)
            with self.subTest(field=field), self.assertRaises(ValueError):
                bind_scorer(packet, self.config, cpu_validation=True)
            proof_file.write_bytes(original)

    def test_tampered_video_and_incomplete_or_check_cohorts_refused(self):
        for fault in ('bytes', 'missing', 'duplicate', 'CHECK'):
            packet = copy.deepcopy(self.packet)
            if fault == 'bytes': packet['pairs'][0]['candidate']['sha256'] = '0'*64
            elif fault == 'missing': packet['pairs'].pop()
            elif fault == 'duplicate': packet['pairs'][1] = packet['pairs'][0]
            elif fault == 'CHECK': packet['FIT_members'][1] = 'EXPOSED_CHECK'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bind_scorer(packet, self.config, cpu_validation=True)

    def test_partial_nonfinite_wrong_identity_and_invalid_original_reductions_refused(self):
        for fault in ('partial', 'last_frame', 'PTS', 'mean', 'PSNR', 'zero_gradient', 'wrong_member', 'GPU'):
            result = copy.deepcopy(self.result)
            row = result['rows'][0]
            if fault == 'partial': result['rows'].pop()
            elif fault == 'last_frame': row['Alex_frames'].pop()
            elif fault == 'PTS': row['PTS_equal'] = False
            elif fault == 'mean': row['Alex'] = .1
            elif fault == 'PSNR': row['PSNR_video_dB'] = 100.
            elif fault == 'zero_gradient': row['gradient_energy_ratio'] = 0.
            elif fault == 'wrong_member': row['member'] = 'EXPOSED_CHECK'
            elif fault == 'GPU': result['CUDA_initialized'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                accept_rows(self.config, result)

    def test_no_acceptance_before_original_cpu_terminal_or_for_another_result(self):
        for key, value in (('original_process_ended', False), ('exit_code', 1),
                           ('GPU_hidden', False), ('wall_seconds', 601.), ('result_sha256', '0'*64)):
            execution = self.execution()
            execution[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                accept_internal_scores(self.config, self.result, execution, cpu_validation=True)


if __name__ == '__main__':
    unittest.main()
