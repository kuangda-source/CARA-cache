import copy
import json
import unittest
from pathlib import Path

from wcomr.cara_fast_binding_r2 import execution_view, load_card

ROOT = Path(__file__).resolve().parents[1]
SPEC = 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json'


class ProductionBindingTests(unittest.TestCase):
    def test_complete_three_arm_gate_precedes_clean_calibration(self):
        card = load_card(ROOT, SPEC)
        slots = card['physical_matrix']
        diagnostics = [s for s in slots if s['section'] == 'A_DIAGNOSTIC']
        self.assertEqual(len(slots), 68)
        self.assertEqual(len(diagnostics), 12)
        expected = {(m, r, enabled) for m in card['FIT']
                    for r in ('NATIVE35','ALLD','WC_T006') for enabled in (False, True)}
        self.assertEqual({(s['member'],s['role'],s['timing_enabled']) for s in diagnostics}, expected)
        self.assertTrue(all(s['audit_enabled'] and not s['eligible_clean_time'] for s in diagnostics))
        self.assertLess(max(slots.index(s) for s in diagnostics),
                        min(i for i,s in enumerate(slots) if s['purpose']=='calibration'))
        anchors = [s for s in slots if s['section'] == 'A_ANCHOR']
        self.assertEqual(len(anchors), 2)
        self.assertTrue(all(s['role']=='NATIVE35' and s['eligible_clean_time']
                            and not s['audit_enabled'] for s in anchors))
        self.assertEqual(len(card['formal_matrix']),32)
        self.assertEqual(sum(s['phase']=='A' for s in slots),32)
        self.assertEqual(sum(s['phase']=='B' for s in slots),36)

    def test_clean_audit_and_duplicate_slot_corruption_refused(self):
        spec = json.loads((ROOT/SPEC).read_text())
        science = json.loads((ROOT/spec['base_manifest']['path']).read_text())
        bad = copy.deepcopy(spec)
        next(s for s in bad['overrides']['physical_matrix']
             if s['eligible_clean_time'])['audit_enabled'] = True
        with self.assertRaises(ValueError):
            execution_view(science, bad)
        bad = copy.deepcopy(spec)
        bad['overrides']['physical_matrix'].append(copy.deepcopy(bad['overrides']['physical_matrix'][0]))
        with self.assertRaises(ValueError):
            execution_view(science, bad)

    def test_science_and_total_budget_are_preserved(self):
        card = load_card(ROOT, SPEC)
        original = json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())
        for key in ('roles','inputs','FIT','CHECK','profile','schedule','schedules','finite_grids',
                    'fidelity_protocol_ref','fidelity_protocol_sha256'):
            self.assertEqual(card[key],original[key])
        quote = json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json').read_text())
        self.assertEqual(quote['scope_sha256'],card['scope_sha256'])
        for host in quote['host_quotes'].values():
            self.assertEqual(len(host['positions']),68)
            self.assertLessEqual(host['proposed_whole_hard_GPUh'],11)
            self.assertGreater(host['proposed_whole_hard_GPUh'],host['complete_forecast_GPUh'])
        self.assertFalse(quote['GPU_authorized'])
        self.assertEqual(quote['new_reserved_GPUh'],0)


if __name__ == '__main__':
    unittest.main()
