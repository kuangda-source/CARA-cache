"""Two-position analysis preserves reused rows and both write-value contexts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_read_write_identity_r1 import M1,P0
from wcomr.cara_read_write_scores_r1 import accept_scores
from wcomr.cara_source_lifecycle_p0_analysis_r1 import combine
from test_cara_read_write_postrelease_r1 import score_fixture

ROOT=Path(__file__).resolve().parents[1]


class Analysis(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cards=[json.loads((ROOT/s.manifest).read_text()) for s in (M1,P0)]
        self.original=[]
        self.scores=[]
        for i,spec in enumerate((M1,P0)):
            args=score_fixture(Path(self.temp.name)/str(i),identity=spec)
            for row in args['result']['rows']:
                level=dict(RW00=.4,RW10=.3,RW01=.2,RW11=.15)[row['role']]
                curve=[level]*93
                row.update(Alex_frames=curve,Alex=sum(curve)/93,Alex_worst=level,
                           Alex_q95_higher=level,Alex_first_worst_frame_zero_based=0)
            args['execution']['result_sha256']=digest(args['result'])
            self.scores.append(accept_scores(**args))
            self.original.append(args)
        self.packet=self.original[1]['packet']

    def report(self):
        return combine(self.cards[0],self.scores[0],self.cards[1],self.scores[1],self.packet,cpu_validation=True)

    def test_complete16_reuses8_and_reports_W_C_and_W_D_separately(self):
        saved=copy.deepcopy(self.scores)
        report=self.report()
        self.assertEqual(self.scores,saved)
        self.assertEqual((report['complete_scientific_positions'],report['new_scoring_pairs'],
                          report['reused_original_scoring_rows']),(16,8,8))
        for point in report['point_summaries']:
            self.assertAlmostEqual(point['equal_input_mean_Alex_write_values']['W_C'],.2)
            self.assertAlmostEqual(point['equal_input_mean_Alex_write_values']['W_D'],.15)
            self.assertAlmostEqual(point['equal_input_mean_Alex_effects']['interaction'],.05)
        self.assertEqual(report['write_value_sign_counts']['W_D']['denominator'],4)
        self.assertFalse(report['source_lifecycle_planner_established'])
        self.assertFalse(report['automatic_P1_launch_authorized'])

    def test_partial_original_or_new_denominator_refused(self):
        for position in (0,1):
            row=self.scores[position]['rows'].pop()
            with self.subTest(position=position),self.assertRaises(ValueError):
                self.report()
            self.scores[position]['rows'].append(row)

    def test_missing_native_bridge_or_changed_packet_binding_refused(self):
        self.packet['manifest']['cross_point_Native_controls_passed']=1
        with self.assertRaises(ValueError):
            self.report()
        self.packet['manifest']['cross_point_Native_controls_passed']=2
        self.packet['release']['collection_sha256']='0'*64
        with self.assertRaises(ValueError):
            self.report()

    def test_CPU_fixture_never_produces_scientific_production_report(self):
        with self.assertRaises(ValueError):
            combine(self.cards[0],self.scores[0],self.cards[1],self.scores[1],self.packet)


if __name__=='__main__':
    unittest.main()
