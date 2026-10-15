"""Held-label isolation and phase-only information boundary on real receipts."""
import copy, gzip, json, unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
from wcomr.w3_grouped_action_eval_r1 import accept_dataset
from wcomr.w3_phase_vs_state_cpu_r1 import fit_phase_fold, time_feature, evaluate_phase_controls, TIME_NAMES
ROOT = Path(__file__).resolve().parents[1]

class PhaseControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = json.loads((ROOT/'reports/wc_w3_grouped_T0_T1_T2_primary_and_raw_sensitivity_accepted_r2_20261016.json').read_text())
        load = lambda k: json.loads(gzip.decompress((ROOT/cls.previous[k+'_capture_ref']).read_bytes()))
        cls.data, _ = accept_dataset(ROOT, load('original'), load('repair'))

    def test_held_teacher_cannot_change_time_or_step_predictions(self):
        rows = [r for r in self.data if r['primary']]; held = rows[0]['group']
        before = fit_phase_fold(rows, held)
        changed = [{**r, 'label': replace(r['label'], q_C=r['label'].q_C*1000, q_A=r['label'].q_A*1000)}
                   if r['group'] == held else r for r in rows]
        self.assertEqual(before, fit_phase_fold(changed, held))
        train = [r for r in rows if r['group'] != held]
        self.assertTrue(np.array_equal(before['mean'], np.array([time_feature(r).values for r in train]).mean(0)))

    def test_time_model_ignores_probe_source_and_history_values(self):
        rows = [r for r in self.data if r['primary']]; held = rows[0]['group']
        changed = []
        for r in rows:
            f = r['feature']['T1']
            values = tuple(v if n in TIME_NAMES else v+999 for n, v in zip(f.names, f.values))
            changed.append({**r, 'feature': {**r['feature'], 'T1': replace(f, values=values)}})
        a = fit_phase_fold(rows, held); b = fit_phase_fold(changed, held)
        self.assertEqual(a, b)
        self.assertEqual(a['feature_names'], list(TIME_NAMES))

    def test_original_results_and_explicit_posthoc_scope_are_preserved(self):
        for old in self.previous['cohorts']:
            value = evaluate_phase_controls(self.data, old)
            self.assertFalse(value['independent_final_test'])
            self.assertEqual(value['step23_rule_status'], 'POSTHOC_FIXED_CANDIDATE_EVALUATED_ON_EXPOSED_DATA')
            base = {r['id']: r for r in value['point_predictions'] if r['model'] == 'T0_CAD'}
            for row in value['point_predictions']:
                if row['model'] == 'STEP23_A_ONLY_POSTHOC':
                    self.assertEqual(row['action'], 'A' if row['step'] == 23 else base[row['id']]['action'])
                    self.assertIsNone(row['raw_prediction'])
                if row['model'].endswith('_NEG_FALLBACK'):
                    p = row['raw_prediction']; trigger = p[0] < 0 or p[0]+p[1] < 0
                    self.assertEqual(row['fallback'], trigger)
                    if trigger:self.assertEqual(row['action'], base[row['id']]['action'])
            self.assertEqual(len(value['point_predictions']), value['points']*8)
            for fold in value['folds']:
                self.assertTrue(set(fold['training_ids']).isdisjoint(fold['held_ids']))

if __name__ == '__main__': unittest.main()
