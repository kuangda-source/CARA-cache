"""Complete two-position figure denominators and signed write-value exports."""
from copy import deepcopy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from render_cara_source_lifecycle_p0_complete_r1 import render, validate


def fixture():
    members = ['av_CPU_FIXTURE', 'human_CPU_FIXTURE']
    points = []
    effects = dict(read=-.1, write=-.2, interaction=.05, joint=-.25)
    for t in (8, 20):
        rows = [dict(member=member, losses_Alex=dict(RW00=.4, RW10=.3, RW01=.2, RW11=.15),
                     Alex_write_values=dict(W_C=.2, W_D=.15), Alex_effects=deepcopy(effects),
                     Alex_frame_effects=[deepcopy(effects) for _ in range(93)]) for member in members]
        points.append(dict(target_update=t, CPU_fixture_only=True, scientific_pairs=8, members=rows,
                           equal_input_mean_Alex_write_values=dict(W_C=.2, W_D=.15),
                           equal_input_mean_Alex_frame_effects=[deepcopy(effects) for _ in range(93)]))
    return dict(status='COMPLETE16_SCIENTIFIC_POSITIONS_WITH_ORIGINAL_POINT8_REUSED',
                CPU_fixture_only=True, target_updates=[8, 20], complete_scientific_positions=16,
                new_scoring_pairs=8, reused_original_scoring_rows=8, original_point8_new_scoring=0,
                old_FIT_members=members, point_summaries=points)


class Figures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)/'figures'
        cls.report = fixture()
        cls.metadata = render(cls.report, cls.output, cpu_validation=True)

    def test_full16_and_all93_exports_keep_two_independent_inputs(self):
        self.assertEqual(self.metadata['independent_input_count'], 2)
        self.assertEqual(self.metadata['complete_scientific_positions'], 16)
        self.assertEqual(self.metadata['per_input_frame_rows'], 372)
        self.assertEqual(self.metadata['mean_frame_rows'], 186)
        self.assertEqual(self.metadata['metrics_computed'], 0)
        for path, prefix in [('P0_two_position_write_values.png', b'\x89PNG'),
                             ('P0_two_position_write_values.pdf', b'%PDF')]:
            self.assertTrue((self.output/path).read_bytes().startswith(prefix))
        self.assertEqual(len(self.metadata['files']), 5)
        with self.assertRaises(FileExistsError):
            render(self.report, self.output, cpu_validation=True)

    def test_complete_frame_write_values_match_both_factorial_contexts(self):
        with (self.output/'all93_equal_input_effects.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 186)
        self.assertEqual({int(r['target_update']) for r in rows}, {8, 20})
        for row in rows:
            self.assertAlmostEqual(float(row['W_C']), .2)
            self.assertAlmostEqual(float(row['W_D']), .15)
        with (self.output/'all93_per_input_effects.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len({(r['target_update'], r['member']) for r in rows}), 4)

    def test_fixtures_partial_reuse_duplicates_and_missing_frames_refused(self):
        with self.assertRaises(ValueError):
            validate(self.report, False)
        mutations = [lambda r: r.update(new_scoring_pairs=7),
                     lambda r: r.update(reused_original_scoring_rows=7),
                     lambda r: r.update(old_FIT_members=['same', 'same']),
                     lambda r: r['point_summaries'][1]['members'].pop(),
                     lambda r: r['point_summaries'][0]['members'][0]['Alex_frame_effects'].pop(),
                     lambda r: r['point_summaries'][1]['equal_input_mean_Alex_frame_effects'].pop()]
        for mutation in mutations:
            report = deepcopy(self.report)
            mutation(report)
            with self.assertRaises(ValueError):
                validate(report, True)


if __name__ == '__main__':
    unittest.main()
