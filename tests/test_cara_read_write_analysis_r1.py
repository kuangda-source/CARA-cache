"""Signed contrasts and full-denominator refusals; synthetic scores only."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_read_write_analysis_r1 import analyze
from wcomr.cara_read_write_scores_r1 import accept_scores
from wcomr.cara_fast_spec_r1 import digest
from test_cara_read_write_postrelease_r1 import score_fixture

ROOT = Path(__file__).resolve().parents[1]


class Analysis(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.card = json.loads((ROOT/'plans/cara_next_stage_20261101/read_write/M1_FULL14_MANIFEST_R2.json').read_text())
        args = score_fixture(self.temp.name)
        levels = dict(RW00=.4, RW10=.3, RW01=.2, RW11=.15)
        for row in args['result']['rows']:
            curve = [levels[row['role']]]*93
            row.update(Alex_frames=curve, Alex=sum(curve)/93, Alex_worst=max(curve),
                Alex_q95_higher=max(curve), Alex_first_worst_frame_zero_based=0)
        args['execution']['result_sha256'] = digest(args['result'])
        self.accepted = accept_scores(**args)

    def test_signed_read_write_interaction_and_equal_input_mean(self):
        report = analyze(self.card, self.accepted, cpu_validation=True)
        effects = report['equal_input_mean_Alex_effects']
        for key, value in dict(read=-.1, write=-.2, interaction=.05, joint=-.25).items():
            self.assertAlmostEqual(effects[key], value)
        self.assertEqual(len(report['equal_input_mean_Alex_frame_effects']), 93)
        self.assertFalse(report['method_established'])

    def test_partial_or_changed_reference_is_refused(self):
        for fault in ('partial', 'reference', 'curve'):
            value = copy.deepcopy(self.accepted)
            if fault == 'partial':
                value['rows'].pop()
            elif fault == 'reference':
                value['rows'][1]['reference']['sha256'] = '0'*64
            else:
                value['rows'][0]['Alex_frames'].pop()
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                analyze(self.card, value, cpu_validation=True)

    def test_CPU_fixture_cannot_produce_production_report(self):
        with self.assertRaises(ValueError):
            analyze(self.card, self.accepted)


if __name__ == '__main__':
    unittest.main()
