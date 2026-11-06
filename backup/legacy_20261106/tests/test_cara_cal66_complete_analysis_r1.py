"""Frozen CAL selection boundaries; no model, server or GPU access."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_cara_cal66_complete_r1 import gates, choose, reference_role


def summary(loss, musiq=65., budget=.98, actions=0):
    return dict(LPIPS=loss, quality=dict(MUSIQ_LONGER512=musiq,
                subject_consistency=.95, motion_smoothness=.98),
                budget=dict(V=budget), actions=dict(A=actions))


class FrozenSelectionTests(unittest.TestCase):
    def test_quality_can_reject_better_fidelity(self):
        v=gates(summary(.08,63.9),summary(.1,65),summary(0,65),[-.02]*4)
        self.assertFalse(v['passed'])
        self.assertIn('Native35:MUSIQ_LONGER512',v['failed_checks'])

    def test_both_practical_gain_conditions_required(self):
        v=gates(summary(.009),summary(.01),summary(0),[-.001]*4)
        self.assertTrue(v['checks']['relative_gain'])
        self.assertFalse(v['checks']['absolute_gain'])

    def test_direction_and_budget_are_separate(self):
        v=gates(summary(.08,budget=1.001),summary(.1),summary(0),[-.05,-.04,.005,.005])
        self.assertFalse(v['checks']['budget_point'])
        self.assertFalse(v['checks']['at_least_three_improved'])
        self.assertTrue(v['checks']['worst_LPIPS_increase'])

    def test_reference_tie_prefers_C(self):
        self.assertEqual(reference_role({'S25_C':summary(.08+5e-13),
                                         'S25_A_PHASE':summary(.08)},25),'S25_C')

    def test_choose_only_eligible_and_near_best(self):
        s={'bad':summary(.01), 'best':summary(.06,budget=.99,actions=10),
           'near':summary(.061,budget=.98), 'far':summary(.07,budget=.9)}
        checks={k:dict(passed=k!='bad') for k in s}
        self.assertEqual(choose(s,checks),'near')
        for v in checks.values(): v['passed']=False
        self.assertIsNone(choose(s,checks))


if __name__=='__main__': unittest.main()
