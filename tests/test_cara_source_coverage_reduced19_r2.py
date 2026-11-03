"""Prospective fixed A1 rule, without reselecting or executing any video."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_cara_source_coverage_reduced19_r2 import a1_variant
from wcomr.cara_fast_spec_r1 import profile_from


class ReducedA1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card=json.loads((ROOT/'plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json').read_bytes())
        cls.profile=profile_from(cls.card['profile'])

    def test_portable_rule_reproduces_original_f19_a1_exactly(self):
        self.assertEqual(a1_variant(self.profile,self.card['roles']['F19_C']['policy']),
                         self.card['roles']['F19_A1']['policy'])

    def test_all_frozen_candidates_keep_dense_layout_and_legal_age_one(self):
        for candidate in self.card['views']['main8-K19']['candidates']:
            original=candidate['policy'];out=a1_variant(self.profile,original)
            self.assertEqual(out['dense_mask'],original['dense_mask'])
            self.assertLessEqual(out['counts']['A'],6)
            for t,action in enumerate(out['actions'],1):
                if action=='A':
                    self.assertTrue(9<=t<=19)
                    self.assertEqual(out['actions'][t-2],'D')
                    self.assertEqual(out['shared_alpha'][t-1],1.)


if __name__=='__main__':
    unittest.main()
