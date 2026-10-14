import copy
import gzip
import json
import math
from pathlib import Path
import unittest
import importlib.util

from wcomr.p_acr_e0_analysis import fixed_direction_error, scalar_oracles, verify_h1_step


class TestE0Projection(unittest.TestCase):
    def test_correlated_direction_projection_and_coefficient_penalty(self):
        mc, mu, cross = 2., 3., 1.8
        out = scalar_oracles(mc, mu, cross)
        eta = out['eta_oracle']
        self.assertAlmostEqual(fixed_direction_error(mc, mu, cross, 'Pc', eta), out['q_Pc_oracle'])
        self.assertAlmostEqual(fixed_direction_error(mc, mu, cross, 'Pc', eta + .4),
                               out['q_Pc_oracle'] + 49 * mc * .4 ** 2)
        # Projection of guided error onto the observed branch innovation.
        dot = 8 * mc - 7 * cross
        self.assertAlmostEqual(out['Pc_gain_fraction'], dot ** 2 / (out['q_base'] * mc))
        self.assertTrue(out['oracle_only'])

    def test_zero_branch_and_zero_guided_are_explicit(self):
        out = scalar_oracles(0., 1., 0.)
        self.assertIsNone(out['eta_oracle'])
        self.assertEqual(out['q_Pc_oracle'], out['q_base'])
        self.assertEqual(out['q_Pu_oracle'], 0.)
        zero = scalar_oracles(49., 64., 56.)
        self.assertEqual(zero['q_base'], 0.)
        self.assertIsNone(zero['Pc_gain_fraction'])

    def test_eta_above_cfg_cancellation_point_is_not_rejected(self):
        out = scalar_oracles(1., 4., 1.7)
        self.assertGreater(out['eta_oracle'], 8 / 7)
        self.assertGreater(out['Pc_gain_fraction'], 0)

    def test_impossible_or_nonfinite_gram_is_rejected(self):
        for args in ((1., 1., 2.), (-1., 1., 0.), (1., 1., math.nan)):
            with self.assertRaises(ValueError):
                scalar_oracles(*args)


class TestActualReceiptRejection(unittest.TestCase):
    """Reject consequential corruptions of an accepted real decision receipt."""
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.parameters = json.loads((root / 'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text())
        capture = json.loads(gzip.decompress((root / 'reports/wc_h1_cost_curve_full60_collection_20261014_0245.json.gz').read_bytes()))
        cls.receipt_run = next(r for r in capture['runner']['runs'] if r['method'] == 'H1_MID' and r['section'] == 'TIMED')

    def test_changed_score_is_rejected(self):
        e = copy.deepcopy(self.receipt_run['source_history'][24])
        e['source_policy']['event_math']['candidate_risk_and_price']['A']['score'] += .01
        with self.assertRaises(ValueError):
            verify_h1_step(e, self.parameters, self.receipt_run['curve_lambda'])


    def test_physical_CC_does_not_prove_plain_C_readout(self):
        e = copy.deepcopy(self.receipt_run['source_history'][24])
        self.assertEqual(e['action'], 'CC')
        e['A_readout']['readout_action'] = 'C'
        with self.assertRaises(ValueError):
            verify_h1_step(e, self.parameters, self.receipt_run['curve_lambda'])

    def test_source_clock_or_binding_change_is_rejected(self):
        for field in ('age', 'source'):
            e = copy.deepcopy(self.receipt_run['source_history'][24])
            if field == 'age':
                e['source_policy']['event_math']['query_age'] += 1
            else:
                e['source_policy']['decision']['state_before'][1] = 'P'
            with self.assertRaises(ValueError):
                verify_h1_step(e, self.parameters, self.receipt_run['curve_lambda'])

    def test_D31_has_no_fabricated_optimizer_scores(self):
        e = copy.deepcopy(self.receipt_run['source_history'][30])
        actual = verify_h1_step(e, self.parameters, self.receipt_run['curve_lambda'])
        self.assertEqual(actual['category'], 'SUPPORT_OR_POLICY_FALLBACK')
        self.assertEqual(actual['source_age'], 7)
        self.assertIsNone(actual['scores'])
        e['source_policy']['decision']['reason'] = 'MATH_EVENT_TABLE_ABSOLUTE_H1:D'
        with self.assertRaises(ValueError):
            verify_h1_step(e, self.parameters, self.receipt_run['curve_lambda'])


class TestHeldPromptCoefficientIsolation(unittest.TestCase):
    def test_held_teacher_does_not_change_any_trained_coefficient(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('acr_lopo_e0', root / 'scripts/analyze_wc_p_acr_cal16_lopo_cpu.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        data = json.loads((root / 'reports/wc_p_acr_e0_16state_raw_oracles_20261014.json').read_text())
        rows = [r for r in data['families'] if r['readout'] == 'FUSION_A']
        held = sorted({r['scene'] for r in rows})[0]
        changed = copy.deepcopy(rows)
        for row in changed:
            if row['scene'] == held:
                for key in ('mc', 'mu', 'cross'):
                    row['moments'][key] *= 100
        for grouping in ('GLOBAL_SCALAR', 'SOURCE_PHASE_SCALAR'):
            for direction in ('Pc', 'Pu'):
                before = module.fit_and_predict(rows, held, grouping, direction)
                after = module.fit_and_predict(changed, held, grouping, direction)
                self.assertEqual([r['coefficient_from_train_only'] for r in before],
                                 [r['coefficient_from_train_only'] for r in after])
                self.assertTrue(all(held not in r['training_scenes'] for r in before))


if __name__ == '__main__':
    unittest.main()
