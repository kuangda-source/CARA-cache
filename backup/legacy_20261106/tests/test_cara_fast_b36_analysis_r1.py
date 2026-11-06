"""Schematic complete metadata only: no B GPU dispatch or metric networks."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wcomr.cara_fast_b36_analysis_r1 import analyze_complete, summarize, CLOCKS
from wcomr.cara_fast_b36_capture_r1 import captured_file
from wcomr.cara_fast_b36_terminal_r1 import bound_A, settle_original
from test_cara_fast_b36_post_r1 import fixture, score_fixture, accepted, replace_record, write

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT/'plans/cara_next_stage_20261028/mainline/r2/A32_FROZEN_BASELINES.json'


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.project = Path(cls.directory.name)
        cls.frozen_bytes = FROZEN.read_bytes()
        cls.card, cls.capture, pool, _, output, _ = fixture(cls.project)
        cls.settlement = settle_original(pool, cls.capture, cls.card)
        inputs = score_fixture(cls.capture, cls.card, cls.settlement, output)
        cls.manifest, cls.manifest_sha, _, execution, new_manifest, new_scores = inputs
        cls.accepted = accepted(cls.capture, cls.card, cls.settlement, inputs)
        cls.score_capture = dict(status='FAST_B36_SCORE_TERMINAL_CAPTURE', execution=execution,
            files=dict(scores=captured_file(output/'B-score-CPU/scores.json'),
                       new_manifest=new_manifest, new_scores=new_scores))

    @classmethod
    def tearDownClass(cls):
        if FROZEN.read_bytes() != cls.frozen_bytes:
            raise AssertionError('Analysis changed the actual immutable A32 freeze')
        cls.directory.cleanup()

    def build(self, **changes):
        inputs = dict(capture=self.capture, card=self.card, settlement=self.settlement,
            manifest=self.manifest, manifest_file_sha256=self.manifest_sha,
            score_capture=self.score_capture, accepted=self.accepted, cpu_validation=True)
        inputs.update(changes)
        return analyze_complete(**inputs)

    def test_complete_matrix_preserves_curves_psnr_reuse_and_unmatched(self):
        result = self.build()
        self.assertEqual(result['status'], 'CPU_METADATA_FIXTURE_ONLY')
        self.assertTrue(result['CPU_fixture_only'])
        rows = result['per_member']
        self.assertEqual(len(rows), 32)
        self.assertEqual(sum(row['reused_A_source'] for row in rows), 8)
        self.assertEqual(sum(row['reused_A_score_id'] is not None for row in rows), 6)
        scores = {row['id']: row for row in self.accepted['rows']}
        for row in rows:
            original = scores[row['score_id']]
            self.assertEqual(row['metrics']['Alex_frames'], original['Alex_frames'])
            self.assertEqual(row['metrics']['SSIM_frames'], original['SSIM_frames'])
            self.assertEqual(len(row['metrics']['Alex_frames']), 93)
            self.assertEqual(row['metrics']['PSNR_video_dB'], original['PSNR_video_dB'])
            if row['role'] in ('WC_FAST', 'RA_FAST'):
                self.assertEqual(row['FIT_baseline_time_match'], 'UNMATCHED')
            elif row['role'] == 'NATIVE_K':
                self.assertEqual(row['FIT_baseline_time_match'], 'MATCHED')
            if row['role'] == 'NATIVE35':
                self.assertEqual(row['metrics']['PSNR_video_dB'], '+inf')
        self.assertEqual(len(result['prompt_equal_summaries']['ALL']), 8)
        self.assertEqual(len(result['FIT_phase_A_only_sensitivity']), 3)
        self.assertFalse(result['new_selection'])
        self.assertFalse(result['independent_new_inputs'])

    def test_repeat_counts_prompt_equal_weights_and_separate_clocks(self):
        binding = bound_A(self.capture, self.card)
        collection = json.loads(self.capture['files']['collection']['raw_utf8'])
        # Repeats exist only for CHECK F19. Pooling physical samples would bias
        # the registered equal-input estimate toward those two members.
        values = {member: 10. * (index + 1) for index, member in enumerate(row['name'] for row in self.card['inputs'])}
        for row in collection['rows']:
            slot = row['slot']
            if slot['role'] == 'F19_C':
                row['result'].update(T_DD=values[slot['member']], T_request=100.+values[slot['member']])
            if slot['section'] == 'B_REPEAT' and slot['role'] == 'NATIVE35':
                row['result'].update(T_DD=300., T_request=600.)
        summary = summarize(self.card, binding, collection, self.manifest, self.accepted)
        rows = summary['per_member']
        f19 = [row for row in summary['prompt_equal_summaries']['ALL'] if row['role'] == 'F19_C'][0]
        self.assertEqual(f19['time_mean'], dict(T_DD=25., T_request=125.))
        self.assertNotEqual(f19['time_mean']['T_DD'], (10+20+30+30+40+40)/6)
        used = [sample['slot_id'] for row in rows for sample in row['timing_samples']]
        self.assertEqual(len(used), 38)
        self.assertEqual(len(set(used)), 38)
        self.assertEqual(sum(len(row['timing_samples'])-1 for row in rows), 6)
        for row in rows:
            expected = 2 if ((row['partition'] == 'FIT' and row['role'] == 'NATIVE35') or
                (row['partition'] == 'CHECK' and row['role'] in ('F19_C', 'F19_A1'))) else 1
            self.assertEqual(len(row['timing_samples']), expected)
            self.assertTrue(all(sample['section'] in ('A_ANCHOR', 'A_CALIBRATION', 'B_QUALITY', 'B_REPEAT')
                                for sample in row['timing_samples']))
        native = next(row for row in summary['prompt_equal_summaries']['ALL'] if row['role'] == 'NATIVE35')
        for clock in CLOCKS:
            self.assertEqual(f19['speedup'][clock], native['time_mean'][clock]/f19['time_mean'][clock])

    def test_fit_sensitivity_excludes_all_B_repeats_and_preserves_labels(self):
        result = self.build()
        rows = result['per_member']
        for baseline in result['FIT_phase_A_only_sensitivity']:
            for member in baseline['per_member']:
                native = next(row for row in rows if row['member'] == member['member'] and row['role'] == 'NATIVE35')
                self.assertEqual(member['native_time'], native['formal_time'])
                self.assertNotEqual(member['native_time'], native['time_mean'])
                self.assertEqual(native['timing_samples'][0]['phase'], 'A')
                self.assertEqual(native['timing_samples'][1]['phase'], 'B')
            self.assertEqual(baseline['FIT_baseline_time_match'],
                             'MATCHED' if baseline['role'] == 'NATIVE_K' else 'UNMATCHED')

    def test_undefined_gradient_has_explicit_members_and_no_finite_subset_mean(self):
        scores = copy.deepcopy(self.accepted)
        first = next(row for row in scores['rows'] if row['role'] == 'F19_C')
        first['gradient_energy_ratio'] = None
        first['gradient_ratio_status'] = 'ZERO_REFERENCE_ENERGY'
        result = summarize(self.card, bound_A(self.capture, self.card),
            json.loads(self.capture['files']['collection']['raw_utf8']), self.manifest, scores)
        role = next(row for row in result['prompt_equal_summaries']['ALL'] if row['role'] == 'F19_C')
        self.assertIsNone(role['gradient_energy_ratio'])
        self.assertEqual(role['undefined_gradient_members'], [first['member']])
        self.assertEqual(role['gradient_ratio_status'], 'UNDEFINED_FOR_AT_LEAST_ONE_MEMBER')

    def test_partial_mixed_unaccepted_and_live_evidence_never_aggregate(self):
        for kind in ('partial_B', 'live_GPU', 'unknown_GPU', 'partial_32', 'accepted_mismatch',
                     'manifest_scope', 'score_running', 'frozen_hash', 'source_changed'):
            with self.subTest(kind=kind):
                capture = copy.deepcopy(self.capture)
                score_capture = copy.deepcopy(self.score_capture)
                accepted_rows = copy.deepcopy(self.accepted)
                manifest = copy.deepcopy(self.manifest)
                if kind == 'partial_B':
                    replace_record(capture, 'collection', lambda data: data['rows'].pop())
                elif kind in ('live_GPU', 'unknown_GPU'):
                    capture['original_live_handles']['runner'] = True if kind == 'live_GPU' else None
                elif kind == 'partial_32':
                    replace_record(score_capture, 'scores', lambda data: data['rows'].pop())
                elif kind == 'accepted_mismatch':
                    accepted_rows['rows'][0]['Alex'] = 7.
                elif kind == 'manifest_scope':
                    manifest['scope_sha256'] = '0'*64
                elif kind == 'score_running':
                    score_capture['status'] = 'FAST_B36_CPU_SCORE_RUNNING'
                elif kind == 'frozen_hash':
                    capture['A32_handoff']['files']['frozen']['sha256'] = '0'*64
                else:
                    replace_record(capture, 'CPU_acceptance', lambda data: data['critical_source_sha256'].update(
                        {'src/wcomr/cara_fast_b36_post_r1.py': '0'*64}))
                with self.assertRaises(ValueError):
                    self.build(capture=capture, manifest=manifest, score_capture=score_capture, accepted=accepted_rows)

    def test_production_entry_refuses_synthetic_data_and_existing_output(self):
        with self.assertRaisesRegex(ValueError, 'CPU metadata fixtures'):
            self.build(cpu_validation=False)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {'capture': self.capture, 'settlement': self.settlement, 'manifest': self.manifest,
                     'score-capture': self.score_capture, 'accepted-scores': self.accepted}
            command = [sys.executable, str(ROOT/'scripts/analyze_cara_fast_b36_complete_r1.py')]
            for name, data in files.items():
                path = root/(name+'.json')
                write(path, data)
                command.extend(['--'+name, str(path)])
            output = root/'analysis.json'
            command.extend(['--output', str(output)])
            run = subprocess.run(command, text=True, capture_output=True, timeout=30)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('CPU metadata fixtures', run.stderr)
            self.assertFalse(output.exists())
            output.write_bytes(b'ORIGINAL_DO_NOT_REPLACE')
            run = subprocess.run(command, text=True, capture_output=True, timeout=30)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(output.read_bytes(), b'ORIGINAL_DO_NOT_REPLACE')


if __name__ == '__main__':
    unittest.main()
