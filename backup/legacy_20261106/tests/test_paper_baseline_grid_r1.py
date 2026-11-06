"""Finite scope, reversible Native timing and immutable threshold selection."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from wcomr.paper_baseline_grid_r1 import METHODS, NATIVE_UPDATES, RA_THRESHOLD, compile_native_execute, matrix, point

ROOT = Path(__file__).resolve().parents[1]


class GridContract(unittest.TestCase):
    def test_all66_positions_and_predeclared_order(self):
        scenes = ['av', 'human', 'misc', 'av51']
        rows = matrix(scenes)
        self.assertEqual(len(rows), 66)
        self.assertEqual(len({r['id'] for r in rows}), 66)
        self.assertEqual(sum(r['section'] == 'TIMED' for r in rows), 44)
        for method in METHODS:
            self.assertEqual([r['scene'] for r in rows if r['method'] == method and r['section'] == 'TIMED'], scenes)
        self.assertEqual([r['method'] for r in rows[11:22]], list(METHODS[::-1]))
        with self.assertRaises(ValueError): matrix(scenes[:-1])

    def test_grid_is_exact_registered_finite_grid(self):
        registered = json.loads((ROOT/'manifests/wc_paper_N05_bounded_baseline_grid_preregistration_draft_20261016.json').read_text())
        self.assertEqual([r['id'] for r in registered['core_methods']], list(METHODS))
        for r in registered['core_methods']:
            actual = point(r['id'])
            self.assertEqual(actual['requested_steps'], r['requested_steps'])
            if r['family'] == 'WC': self.assertEqual(actual['threshold'], r['worldcache_rel_l1_thresh'])
            elif r['family'] == 'RA': self.assertEqual(actual['threshold'], r['RA_threshold'])
        for invalid in ('NATIVE17', 'WC_OTHER', 'RA_other', 'P_OFF', 'T1_CAD'):
            with self.assertRaises(ValueError): point(invalid)

    def test_native_count_adaptation_is_reversible_and_strict(self):
        execute, proof = compile_native_execute()
        self.assertEqual(proof['reversible_replacements'], 4)
        self.assertTrue(proof['inverse_bytes_and_AST_equal'])
        dummy = SimpleNamespace(rank0=True, text_guardrail_runner=None, video_guardrail_runner=None)
        for steps in (18,26,35):
            sample = SimpleNamespace(num_steps=steps)
            for wrong in (0,36 if steps!=35 else 35):
                with self.assertRaisesRegex(ValueError, '35-step guarded request'):
                    execute(dummy, sample, 'NATIVE', expected_updates=wrong,
                            runtime=None,wc=None,rf=None,settings={},calibration=None,specs={},
                            inference_module=None,output=None,expected_shape=[])
            with self.assertRaisesRegex(ValueError, 'Ordinary guardrails'):
                execute(dummy, sample, 'NATIVE', expected_updates=NATIVE_UPDATES[steps],
                        runtime=None,wc=None,rf=None,settings={},calibration=None,specs={},
                        inference_module=None,output=None,expected_shape=[])
        with self.assertRaisesRegex(ValueError, '35-step guarded request'):
            execute(dummy, SimpleNamespace(num_steps=35), 'WC', runtime=None,wc=None,rf=None,
                    settings={},calibration=None,specs={},inference_module=None,output=None,expected_shape=[])

if __name__ == '__main__': unittest.main()
