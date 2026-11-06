"""Offline objective parity and original-score provenance; no model runtime."""
import base64
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_cara_source_coverage_saved_r1 import geometry, original_queries
from audit_cara_source_proxy_saved_r1 import spearman
from wcomr.cara_fast_spec_r1 import profile_from


class SavedCoverageAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card=json.loads((ROOT/'plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json').read_bytes())
        cls.profile=profile_from(cls.card['profile'])

    def test_offline_cost_matches_the_original_generator_objective(self):
        for budget in (19,22):
            for mode,view in (('single','single8'),('two','main8')):
                for candidate in self.card['views'][f'{view}-K{budget}']['candidates']:
                    for origin in candidate['origins']:
                        cost=geometry(self.profile,self.card['schedule']['sigmas'],
                                      candidate['dense_steps'],mode,origin['tilt'])
                        self.assertAlmostEqual(cost['peak'],origin['peak'],places=15)
                        self.assertAlmostEqual(cost['squared_sum'],origin['squared_sum'],places=15)

    def test_rank_direction_and_ties_are_handled(self):
        self.assertEqual(spearman([(1,20),(1,10),(2,1)],[2.,1.,3.]),1.)
        self.assertEqual(spearman([1.,1.,2.],[2.,2.,1.]),-1.)
        self.assertIsNone(spearman([1.,1.],[2.,3.]))

    def test_changed_original_score_bytes_are_rejected_before_analysis(self):
        load=lambda path:json.loads((ROOT/path).read_bytes())
        summary=load('reports/cara_v1_P1_successor_original_algorithm_summary_r1_20261103.json')
        analysis=load('reports/cara_v1_P1_successor_original_complete_analysis_r1_20261103.json')
        returns=load('reports/cara_source_coverage_P1_original42_score_returns_r1_20261103.json')
        changed=copy.deepcopy(returns)
        changed[next(iter(changed))]=base64.b64encode(b'{}').decode()
        with self.assertRaisesRegex(ValueError,'SHA differs'):
            original_queries(summary,analysis,changed,self.card['FIT'])
        self.assertEqual(len(original_queries(summary,analysis,returns,self.card['FIT'])),42)


if __name__=='__main__':
    unittest.main()
