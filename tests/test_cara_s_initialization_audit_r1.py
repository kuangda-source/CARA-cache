"""Initialization changes must not silently use F19 as the no-gain fallback."""
import copy
import json
from pathlib import Path
import unittest

from wcomr.cara_s_initialization_audit_r1 import audit, candidates, rank, TARGETS
from wcomr.cara_fast_spec_r1 import profile_from

ROOT = Path(__file__).resolve().parents[1]


class InitializationTests(unittest.TestCase):
    def setUp(self):
        manifest = json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())
        result = json.loads((ROOT/'reports/cara_sq_s_A6000_complete_frozen_risk_result_r1_20261030.json').read_text())
        accepted = json.loads((ROOT/'reports/cara_sq_s_A6000_post_analysis_accepted_r1_20261030.json').read_text())
        self.profile = manifest['profile']
        self.bases = {name: [i for i, action in enumerate(policy['actions'], 1) if action == 'D']
                      for name, policy in result['risk_and_mask_proposals']['policies'].items()
                      if name in ('F19_C', 'Uniform19_C')}
        self.risk = {j: {int(k): v for k, v in rows.items()}
                     for j, rows in result['risk_and_mask_proposals']['risk'].items()}
        self.original = accepted['choices']

    def run_audit(self):
        return audit(self.profile, self.bases, self.risk, self.original, 170)

    def test_original_reproduction_and_fixed_uniform_difference(self):
        result = self.run_audit()
        self.assertEqual(result['origins']['F19_C']['choices'], self.original)
        uniform = result['origins']['Uniform19_C']
        self.assertEqual((uniform['choices']['BR']['remove'], uniform['choices']['CFG']['remove']), (22, 25))
        self.assertEqual({c['add'] for c in uniform['choices'].values()}, {35})
        self.assertFalse(uniform['all_objectives_same_mask'])
        self.assertEqual(len(result['additional_selector_histories']), 138)
        self.assertFalse(result['new_selector_history_CPU_accepted'])
        self.assertFalse(result['new_method_recipe_frozen'])
        self.assertEqual(result['GPU_submissions'], 0)

    def test_zero_or_negative_gain_keeps_each_original_initialization(self):
        for base in self.bases.values():
            _, rows = candidates(profile_from(self.profile), base)
            for risk in [dict.fromkeys(TARGETS, 0.0), {step: (2.0 if step in base else 1.0) for step in TARGETS}]:
                choice, _ = rank(risk, rows, base)
                self.assertEqual(choice['dense'], base)
                self.assertIsNone(choice['remove'])
                self.assertIsNone(choice['add'])

    def test_equal_positive_gains_follow_remove_add_order(self):
        base = self.bases['Uniform19_C']
        _, rows = candidates(profile_from(self.profile), base)
        risk = {step: (0.0 if step in base else 1.0) for step in TARGETS}
        choice, _ = rank(risk, list(reversed(rows)), base)
        self.assertEqual((choice['remove'], choice['add']), min((r['remove'], r['add']) for r in rows))

    def test_no_missing_or_nonfinite_risk_fill(self):
        original = copy.deepcopy(self.risk)
        for invalid in [None, float('nan'), float('inf'), -1.0]:
            self.risk = copy.deepcopy(original)
            if invalid is None:
                del self.risk['CFG'][35]
            else:
                self.risk['CFG'][35] = invalid
            with self.assertRaises(ValueError):
                self.run_audit()

    def test_altered_accepted_decision_is_refused(self):
        self.original['CFG']['remove'] = 20
        with self.assertRaises(ValueError):
            self.run_audit()

    def test_no_second_budget_or_unprotected_candidate(self):
        for remove in [24, 22]:
            base = [step for step in self.bases['Uniform19_C'] if step != remove]
            with self.assertRaises(ValueError):
                candidates(profile_from(self.profile), base)
        base = self.bases['Uniform19_C'].copy()
        base.remove(24)
        base.append(35)
        with self.assertRaises(ValueError):
            candidates(profile_from(self.profile), sorted(base))

    def test_same_common_candidate_domain_for_every_objective(self):
        result = self.run_audit()
        for origin in result['origins'].values():
            expected = {(r['remove'], r['add']) for r in origin['candidates']}
            for ranking in origin['rankings'].values():
                self.assertEqual({(r['remove'], r['add']) for r in ranking}, expected)
            for row in origin['candidates']:
                self.assertEqual(len(row['dense']), 19)
                for step, older, newer in row['history']:
                    self.assertLess(older, newer)
                    self.assertLess(newer, step)
                    self.assertLessEqual(step-newer, 28)


if __name__ == '__main__':
    unittest.main()
