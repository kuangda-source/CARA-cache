"""CPU-only fixture panels; every exported table and figure carries that label."""
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_cara_fast_b36_analysis_r1 as base
from analyze_cara_fast_r1 import ratio_interval
from wcomr.cara_fast_b36_figures_r1 import verify_analysis, export_report, label, INPUTS
from wcomr.cara_fast_b36_post_r1 import assemble_scores, accept_scores
from wcomr.policy_price_terminal_r1 import record

ROOT = Path(__file__).resolve().parents[1]


class FigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base.AnalysisTests.setUpClass()
        cls.context = base.AnalysisTests()
        cls.context.score_capture = copy.deepcopy(cls.context.score_capture)
        def zero_reference(data):
            row = next(item for item in data['rows'] if item['role'] == 'F19_C')
            row.update(reference_gradient_energy=0., candidate_gradient_energy=0.,
                       gradient_energy_ratio=None, gradient_ratio_status='ZERO_REFERENCE_ENERGY')
        base.replace_record(cls.context.score_capture, 'new_scores', zero_reference)
        captured = cls.context.score_capture
        result = assemble_scores(cls.context.manifest, cls.context.manifest_sha,
            record(captured, 'new_manifest'), captured['files']['new_manifest']['sha256'],
            record(captured, 'new_scores'), captured['files']['new_scores']['sha256'])
        def assembled(data):
            data.clear()
            data.update(result)
        base.replace_record(captured, 'scores', assembled)
        cls.context.accepted = accept_scores(cls.context.capture, cls.context.card, cls.context.settlement,
            cls.context.manifest, cls.context.manifest_sha, result, captured['execution'],
            new_manifest=captured['files']['new_manifest'], new_scores=captured['files']['new_scores'])
        cls.analysis = cls.context.build()
        root = cls.context.project/'figure-inputs'
        root.mkdir()
        values = dict(zip(INPUTS, (cls.context.capture, cls.context.settlement,
            cls.context.manifest, cls.context.score_capture, cls.context.accepted)))
        files = {}
        for name, value in values.items():
            path = root/(name+'.json')
            base.write(path, value)
            files[name] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        cls.analysis.update(input_file_sha256=files,
            analysis_source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                'scripts/analyze_cara_fast_b36_complete_r1.py', 'src/wcomr/cara_fast_b36_analysis_r1.py')})
        cls.path = root/'analysis.json'
        base.write(cls.path, cls.analysis)

    @classmethod
    def tearDownClass(cls):
        base.AnalysisTests.tearDownClass()

    def test_rebuild_all_original_inputs_and_reject_fixture_production_path(self):
        analysis, sha = verify_analysis(self.path, cpu_validation=True)
        self.assertEqual(analysis, self.analysis)
        self.assertEqual(sha, hashlib.sha256(self.path.read_bytes()).hexdigest())
        with self.assertRaisesRegex(ValueError, 'CPU fixtures'):
            verify_analysis(self.path)

    def test_edited_aggregate_missing_input_and_changed_source_are_refused(self):
        for kind in ('mean', 'partial', 'source', 'input', 'digest'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                analysis = copy.deepcopy(self.analysis)
                if kind == 'mean':
                    analysis['per_member'][0]['time_mean']['T_DD'] += 1
                elif kind == 'partial':
                    analysis['per_member'].pop()
                elif kind == 'source':
                    analysis['analysis_source_sha256']['src/wcomr/cara_fast_b36_analysis_r1.py'] = '0'*64
                elif kind == 'input':
                    analysis['input_file_sha256'].pop('accepted-scores')
                else:
                    analysis['input_file_sha256']['manifest']['sha256'] = '0'*64
                path = Path(directory)/'analysis.json'
                base.write(path, analysis)
                with self.assertRaises(ValueError):
                    verify_analysis(path, cpu_validation=True)

    def test_complete_tables_curves_and_four_actual_rendered_panels(self):
        from PIL import Image
        from matplotlib.axes import Axes
        analysis, _ = verify_analysis(self.path, cpu_validation=True)
        preview = os.environ.get('CARA_B36_FIGURE_PREVIEW')
        output = Path(preview) if preview else self.context.project/'figure-preview'
        units = []
        def interval(native, candidate):
            units.append((len(native), len(candidate)))
            return ratio_interval(native, candidate)
        numbers, undefined = [], []
        original_annotate, original_text = Axes.annotate, Axes.text
        def annotated(ax, text, *args, **kwargs):
            numbers.append(text)
            return original_annotate(ax, text, *args, **kwargs)
        def text(ax, x, y, value, *args, **kwargs):
            if value == 'undefined':
                undefined.append(value)
            return original_text(ax, x, y, value, *args, **kwargs)
        with patch.object(Axes, 'annotate', annotated), patch.object(Axes, 'text', text):
            result = export_report(analysis, output, interval, cpu_validation=True)
        roles = self.context.card['formal_roles']
        members = [item['name'] for item in self.context.card['inputs']]
        expected = [str(roles.index(row['role'])+1) for _ in range(2) for member in members
                    for row in analysis['per_member'] if row['member'] == member]
        self.assertEqual(numbers, expected)
        self.assertGreaterEqual(len(undefined), 2)
        self.assertEqual(result['status'], 'CPU_FIGURE_LAYOUT_ONLY')
        self.assertEqual(len(result['files']), 12)
        self.assertEqual(units, [(4, 4)]*8+[(2, 2)]*16)
        for filename, count in [('per_member.csv', 32), ('frame_curves.csv', 2976),
                                ('prompt_equal.csv', 24), ('FIT_A_only.csv', 6)]:
            with (output/filename).open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), count)
            self.assertTrue(all(row['CPU_fixture_only'] == 'True' for row in rows))
            if filename == 'per_member.csv':
                native = [row for row in rows if row['role'] == 'NATIVE35']
                self.assertTrue(all(row['PSNR_video_dB'] == '+inf' for row in native))
                self.assertEqual(sum(row['FIT_baseline_time_match'] == 'UNMATCHED' for row in rows), 8)
            if filename == 'prompt_equal.csv':
                for row in rows:
                    if row['role'] == 'NATIVE35':
                        self.assertEqual(float(row['speedup_DD_CI95_low']), 1.)
                        self.assertEqual(float(row['speedup_DD_CI95_high']), 1.)
                    if row['gradient_ratio_status'] != 'FINITE':
                        self.assertEqual(row['gradient_energy_ratio'], '')
                        self.assertTrue(json.loads(row['undefined_gradient_members']))
        for path in output.glob('*.png'):
            with Image.open(path) as image:
                self.assertGreaterEqual(image.width, 1900)
                self.assertGreaterEqual(image.height, 1200)
                self.assertNotEqual(image.convert('RGB').getextrema(), ((255, 255),)*3)
        for path in output.glob('*.pdf'):
            self.assertTrue(path.read_bytes().startswith(b'%PDF-'))
        base.write(output/'CPU-layout-proof.json', result)

    def test_every_frozen_label_keeps_its_FIT_scope(self):
        for role in ('WC_FAST', 'RA_FAST'):
            self.assertIn('[FIT UNMATCHED]', label(self.analysis, role))
        self.assertEqual(label(self.analysis, 'NATIVE_K'), 'NATIVE22 [FIT MATCHED]')

    def test_existing_and_partial_output_directories_are_never_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'original'
            output.mkdir()
            witness = output/'partial-original'
            witness.write_bytes(b'RETAIN')
            with self.assertRaisesRegex(ValueError, 'Fresh report directory'):
                export_report(self.analysis, output, ratio_interval, cpu_validation=True)
            self.assertEqual(witness.read_bytes(), b'RETAIN')

    def test_actual_CLI_refuses_fixture_before_creating_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'report'
            result = subprocess.run([sys.executable, str(ROOT/'scripts/render_cara_fast_b36_figures_r1.py'),
                '--analysis', str(self.path), '--output-dir', str(output)], text=True, capture_output=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('CPU fixtures', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
