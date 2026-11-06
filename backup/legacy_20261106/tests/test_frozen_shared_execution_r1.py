"""Seed identity, immutable legacy source and complete shared-template controls."""
import copy
import inspect
from types import SimpleNamespace
import unittest
import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.frozen_shared_execution_r1 import (
    AVAILABLE_METHODS, cache_context, compile_seed_gate, execute, matrix, point,
)
from wcomr.paper_baseline_grid_r1 import RA_THRESHOLD


class FrozenExecution(unittest.TestCase):
    def test_sampler_observer_unwraps_the_original_namespace(self):
        sentinel = object()
        namespace = {'torch': torch, 'misc': sentinel}
        exec(compile('@torch.inference_mode()\ndef sampler():\n    return misc\n',
                     'declared-sampler-source.py', 'exec'), namespace)
        decorated = namespace['sampler']
        self.assertNotIn('misc', decorated.__globals__)
        original = inspect.unwrap(decorated)
        self.assertIs(original.__globals__['misc'], sentinel)
        self.assertEqual(original.__code__.co_filename, 'declared-sampler-source.py')

    def test_whole180_template_has_all_original_seed_method_positions(self):
        cases = [dict(id=f'p{i}_seed{s}', prompt_id=f'p{i}', seed=s)
                 for i in range(8) for s in (17, 43)]
        methods = ['NATIVE35', 'NATIVE26', 'NATIVE18', 'WC_DEFAULT', 'RA_DEFAULT',
                   'A_NO_P', 'TABLE_PHASE_H1', 'FRONT_DENSE_C', 'FRONT_DENSE_A', 'UNIFORM_C']
        rows = matrix(cases, methods)
        self.assertEqual(len(rows), 180)
        self.assertEqual(len({r['id'] for r in rows}), 180)
        formal = [r for r in rows if r['section'] == 'TIMED']
        self.assertEqual({(r['case_id'], r['method']) for r in formal},
                         {(c['id'], m) for c in cases for m in methods})
        for changed_cases, changed_methods in (
                (cases[:-1], methods), (cases, methods[:-1]),
                (cases, methods[:-1] + ['P_ACR']),
                (cases, methods[:-1] + [methods[0]])):
            with self.assertRaises(ValueError):
                matrix(changed_cases, changed_methods)
        bad = copy.deepcopy(cases)
        bad[0]['seed'] = 17.0
        with self.assertRaises(ValueError):
            matrix(bad, methods)

    def test_two_seed_gate_changes_are_exactly_reversible(self):
        for family in ('GRID', 'SIMPLE'):
            _, proof = compile_seed_gate(family)
            self.assertEqual(proof['replacements'], 1)
            self.assertTrue(proof['inverse_bytes_and_AST_equal'])
            self.assertFalse(proof['thresholds_readouts_or_sampler_changed'])

    def test_context_keeps_seed0_parity_and_binds_both_new_seeds(self):
        original = ('prior-run:case', 'Cosmos', 'fixed-seed0-request')
        self.assertIs(cache_context(original, 'case', 0), original)
        self.assertNotEqual(cache_context(original, 'case', 17), cache_context(original, 'case', 43))
        for name, seed in [('other', 17), ('case', 18), ('case', False), ('case', 43.0)]:
            with self.assertRaises(ValueError):
                cache_context(original, name, seed)

    def test_all_existing_points_and_simple_dense_quotas_are_preserved(self):
        self.assertEqual(len(AVAILABLE_METHODS), 17)
        self.assertEqual([point('NATIVE' + str(n))['actual_updates'] for n in (35, 26, 18)], [36, 27, 19])
        for method, a, c in [('FIXED_A', 5, 5), ('UNIFORM_A', 10, 0),
                             ('FRONT_DENSE_C', 0, 10), ('FRONT_DENSE_A', 10, 0)]:
            p = point(method)
            self.assertEqual((p['dense_quota'], p['corrected_reuses'], p['plain_reuses']), (26, a, c))

    def test_invalid_seed_and_guardrail_failure_do_not_leak_installation(self):
        install = clean.install
        common = dict(table_parameters={}, previous_parameters={'original_RA_threshold': RA_THRESHOLD},
                      settings={'worldcache_rel_l1_thresh': .06}, specs={'SOURCE_RA': {'threshold': RA_THRESHOLD}})
        for seed in (False, 18, 43.0):
            with self.assertRaises(ValueError):
                execute(None, SimpleNamespace(seed=seed, num_steps=35), 'NATIVE35', **common)
        dummy = SimpleNamespace(text_guardrail_runner=None, video_guardrail_runner=None)
        for seed in (17, 43):
            with self.assertRaisesRegex(ValueError, 'Ordinary guardrails'):
                execute(dummy, SimpleNamespace(seed=seed, num_steps=35, name='case'), 'NATIVE35', **common)
            self.assertIs(clean.install, install)


if __name__ == '__main__':
    unittest.main()
