"""Independent exhaustive oracle, real source-owner CPU paths and cohort controls."""
import copy
from dataclasses import asdict
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cara_source_coverage_r1 import (
    DISTANCE_SCALE, TILTS, candidate_pool, coverage_distance, coverage_plans,
    select_endpoint, source_trace)
from wcomr.policy_generator_r1.interval_grammar import Profile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_MANIFEST_R1.json'
METRICS = {}


def small_profile(n=9):
    return Profile(n, (1, 2, n), 3, 2, 1, 'source-coverage-CPU-fixture')


def exhaustive(profile, count, sigmas, tilt, mode):
    """No DP or production coverage/scoring helper used by this oracle."""
    values = []
    for mask in combinations(range(1, profile.horizon+1), count):
        if not set(profile.protected_dense) <= set(mask):
            continue
        if any(b-a-1 > profile.max_source_age for a, b in zip(mask, mask[1:]+(profile.horizon+1,))):
            continue
        anchors, distances = [], []
        for t in range(1, profile.horizon+1):
            if t in mask:
                anchors.append(t)
            else:
                if len(anchors) < 2:
                    break
                s, b, a = (sigmas[i-1]/sigmas[0] for i in (t, anchors[-1], anchors[-2]))
                d_b = ((t-anchors[-1])/profile.horizon+b-s)/2
                d_a = ((t-anchors[-2])/profile.horizon+a-s)/2
                distance = d_b if mode == 'single' else (d_b+d_a)/2
                distances.append(round(math.exp(tilt*(s-.5))*distance*DISTANCE_SCALE))
        else:
            values.append((max(distances, default=0), sum(v*v for v in distances), mask))
    values.sort()
    if not values:
        return []
    optimum = values[0][0]
    return [v for v in values if v[0] == optimum][:3]


def endpoint_fixture(pool):
    return [dict(candidate_id=c['candidate_id'], member=m, status='COMPLETE', frames=93,
        LPIPS=.2+.01*i, T_DD=150., T_request=175., actual_GPUh=.1,
        input_sha256=('a' if m == 'fit-a' else 'b')*64,
        reference_sha256=('c' if m == 'fit-a' else 'd')*64, metric_protocol_sha256='e'*64)
        for i, c in enumerate(pool['candidates']) for m in ('fit-a', 'fit-b')]


class CoverageAlgorithm(unittest.TestCase):
    def test_two_pass_dp_matches_independent_exhaustive_oracle(self):
        checked = 0
        for n in (5, 7, 9):
            profile = small_profile(n)
            for power in (1., 2.):
                sigmas = [(1-i/n)**power for i in range(n+1)]
                for count in range(3, n+1):
                    for mode in ('single', 'two'):
                        for tilt in (-2., 0., 4.):
                            expected = exhaustive(profile, count, sigmas, tilt, mode)
                            if not expected:
                                with self.assertRaisesRegex(ValueError, 'No legal schedule'):
                                    coverage_plans(profile, count, sigmas, tilt=tilt, mode=mode)
                                checked += 1
                                continue
                            result = coverage_plans(profile, count, sigmas, tilt=tilt, mode=mode)
                            actual = [(r['peak_units'], r['squared_units'], tuple(r['dense_steps']))
                                      for r in result['plans']]
                            self.assertEqual(actual, expected, (n, power, count, mode, tilt))
                            checked += 1
        METRICS['exhaustive_cases'] = checked

    def test_later_peak_can_reverse_prefix_lexicographic_order(self):
        # One-pass lexicographic prefix pruning would discard B. Both paths
        # reach the same two-source state; their common future has peak10.
        a, b, future = (2, 8), (3, 6), (10, 100)
        self.assertLess(a, b)
        self.assertLess((max(b[0], future[0]), b[1]+future[1]),
                        (max(a[0], future[0]), a[1]+future[1]))

    def test_nearly_flat_sigma_still_pays_for_actual_update_lifetime(self):
        scales = tuple(1-i*1e-9 for i in range(9))
        distance = coverage_distance(scales, 7, 1, 2, 0., 'two')
        self.assertGreater(distance, .3)
        self.assertGreater(distance, coverage_distance(scales, 4, 1, 2, 0., 'two'))

    def test_actual36_budgets_compile_and_are_deterministic_and_bounded(self):
        manifest = json.loads(MANIFEST.read_text())
        profile, sigmas = profile_from(manifest['profile']), manifest['schedule']['sigmas']
        counts = {}
        for count in (19, 22):
            for mode in ('single', 'two'):
                pool = candidate_pool(profile, count, sigmas, mode=mode)
                self.assertEqual(pool, candidate_pool(profile, count, sigmas, mode=mode))
                candidates = pool['candidates']
                self.assertTrue(1 <= len(candidates) <= 12)
                self.assertEqual(len({c['candidate_id'] for c in candidates}), len(candidates))
                for c in candidates:
                    self.assertEqual(c['policy']['counts'], dict(D=count, C=36-count, A=0))
                    self.assertTrue(set(profile.protected_dense) <= set(c['dense_steps']))
                    self.assertEqual(c['trace']['source_reads_per_CFG_branch'], 2*(36-count))
                counts[f'{mode}_{count}'] = len(candidates)
        METRICS['actual36_pool_sizes'] = counts

    def test_different_grid_and_budget_need_no_hand_step_table(self):
        # Declared synthetic51 grid; this is not a production50 scheduler claim.
        profile = Profile(51, (1, 2, 3, 4, 5, 6, 7, 51), 28, 2, 1, 'synthetic51-CPU')
        pool = candidate_pool(profile, 27, [(1-i/51)**2 for i in range(52)])
        self.assertTrue(pool['candidates'])
        for c in pool['candidates']:
            self.assertEqual(c['policy']['counts'], dict(D=27, C=24, A=0))
        METRICS['synthetic51_27D_candidates'] = len(pool['candidates'])

    def test_source_swap_recomputes_future_intervals_and_total_usage_is_constant(self):
        profile = small_profile()
        sigmas = [1-i/9 for i in range(10)]
        a = source_trace(profile, [1, 2, 5, 9], sigmas)
        b = source_trace(profile, [1, 2, 6, 9], sigmas)
        old = {r['t']: r for r in a['C_states']}
        new = {r['t']: r for r in b['C_states']}
        self.assertEqual(old[3], new[3])
        self.assertNotEqual(old[7], new[7])
        self.assertEqual((old[7]['a'], old[7]['b']), (2, 5))
        self.assertEqual((new[7]['a'], new[7]['b']), (2, 6))
        self.assertEqual(a['source_reads_per_CFG_branch'], b['source_reads_per_CFG_branch'])
        self.assertNotEqual(a['lifetimes'], b['lifetimes'])

    def test_single_source_and_two_source_ablation_change_candidate_structure(self):
        profile = small_profile()
        sigmas = [(1-i/9)**2 for i in range(10)]
        one = candidate_pool(profile, 5, sigmas, mode='single')
        two = candidate_pool(profile, 5, sigmas)
        self.assertNotEqual({tuple(c['dense_steps']) for c in one['candidates']},
                            {tuple(c['dense_steps']) for c in two['candidates']})

    def test_grid_and_unsupported_budget_fail_at_boundary(self):
        profile = small_profile()
        good = [1-i/9 for i in range(10)]
        for bad in (good[:-1], good[:3]+[good[2]]+good[4:], [float('nan')]+good[1:]):
            with self.assertRaises(ValueError):
                coverage_plans(profile, 5, bad)
        for count in (2, 10, True):
            with self.assertRaises(ValueError):
                coverage_plans(profile, count, good)


class CompleteEndpointSelection(unittest.TestCase):
    def setUp(self):
        self.pool = candidate_pool(small_profile(), 5, [1-i/9 for i in range(10)])
        self.rows = endpoint_fixture(self.pool)

    def select(self, rows=None, **kwargs):
        return select_endpoint(self.pool, ['fit-a', 'fit-b'], self.rows if rows is None else rows,
                               cost_limit_GPUh=10., **kwargs)

    def test_complete_input_equal_selection_and_ordered_tie(self):
        rows = copy.deepcopy(self.rows)
        for row in rows:
            row['LPIPS'] = .1 if row['member'] == 'fit-a' else .5
        result = self.select(rows, overhead_GPUh=.3)
        self.assertEqual(result['selected']['candidate_id'], self.pool['candidates'][0]['candidate_id'])
        self.assertAlmostEqual(result['selected']['LPIPS_mean'], .3)
        self.assertAlmostEqual(result['actual_calibration_GPUh'], .3+.1*len(rows))
        self.assertFalse(result['frozen'])
        self.assertEqual(result['position_denominator'], len(rows))

    def test_failed_candidate_retains_denominator_and_paid_cost(self):
        self.rows[0].update(status='FAILED', LPIPS=None, frames=0)
        result = self.select()
        self.assertFalse(result['candidates'][0]['eligible'])
        self.assertNotEqual(result['selected']['candidate_id'], self.rows[0]['candidate_id'])
        self.assertEqual(result['position_denominator'], len(self.rows))
        self.assertAlmostEqual(result['actual_calibration_GPUh'], .1*len(self.rows))
        for row in self.rows:
            row.update(status='MISSING', LPIPS=None)
        self.assertEqual(self.select()['status'], 'NO_COMPLETE_CANDIDATE')

    def test_missing_or_duplicate_cohorts_and_partial_video_are_rejected(self):
        for rows in (self.rows[:-1], self.rows+[self.rows[0]]):
            with self.assertRaises(ValueError):
                self.select(rows)
        self.rows[0]['frames'] = 92
        with self.assertRaises(ValueError):
            self.select()

    def test_cost_limit_includes_failures_and_overhead(self):
        self.rows[0]['status'] = 'FAILED'
        with self.assertRaisesRegex(ValueError, 'cost exceeds'):
            select_endpoint(self.pool, ['fit-a', 'fit-b'], self.rows,
                overhead_GPUh=.5, cost_limit_GPUh=.1*len(self.rows)+.4)

    def test_changed_pool_and_unregistered_input_are_rejected(self):
        altered = copy.deepcopy(self.pool)
        altered['candidates'][0]['dense_steps'].append(8)
        with self.assertRaisesRegex(ValueError, 'digest differs'):
            select_endpoint(altered, ['fit-a', 'fit-b'], self.rows, cost_limit_GPUh=10.)
        self.rows[0]['member'] = 'protected-final-fixture'
        with self.assertRaises(ValueError):
            self.select()

    def test_mixed_reference_or_metric_protocol_is_rejected(self):
        for key in ('input_sha256', 'reference_sha256', 'metric_protocol_sha256'):
            rows = copy.deepcopy(self.rows)
            rows[0][key] = 'f'*64
            with self.assertRaisesRegex(ValueError, 'fixed input/reference'):
                self.select(rows)

    def test_generate_and_select_actual_offline_CLI(self):
        from dataclasses import asdict
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            manifest, pool_path, rows_path, output = [folder/name for name in (
                'manifest.json', 'pool.json', 'rows.json', 'selected.json')]
            manifest.write_text(json.dumps(dict(profile=asdict(small_profile()),
                schedule=dict(sigmas=[1-i/9 for i in range(10)]))))
            command = [sys.executable, str(ROOT/'scripts/cara_source_coverage_r1.py')]
            subprocess.run(command+['generate', '--manifest', str(manifest), '--dense', '5',
                '--output', str(pool_path)], check=True, capture_output=True, text=True)
            pool = json.loads(pool_path.read_text())
            rows_path.write_text(json.dumps(endpoint_fixture(pool)))
            subprocess.run(command+['select', '--pool', str(pool_path), '--rows', str(rows_path),
                '--fit', 'fit-a', 'fit-b', '--cost-limit-gpuh', '10', '--output', str(output)],
                check=True, capture_output=True, text=True)
            selected = json.loads(output.read_text())
            self.assertEqual(selected['status'], 'SELECTED')
            self.assertEqual(selected['pool_sha256'], pool['pool_sha256'])


class PinnedCacheExecution(unittest.TestCase):
    def test_generated_plans_on_original_WC_RF_UniPC_tiny_CPU(self):
        import torch
        from test_cara_read_write_provenance_r1 import bound
        from wcomr.cara_read_write_state_r1 import UniPCMemory
        from wcomr.cara_read_write_transition_r1 import WorldCacheMemory
        from wcomr.mid_coverage import tree_digest

        manifest = json.loads(MANIFEST.read_text())
        profile, sigmas = profile_from(manifest['profile']), manifest['schedule']['sigmas']
        paths, C_pairs = 0, 0

        def state_digest(state):
            return tree_digest(dict(latent=state.latent, memory=vars(state.memory),
                fields=state.cache['fields'], buffers=state.cache['buffers'],
                provenance=asdict(state.cache['provenance'])))

        for count in (19, 22):
            pool = candidate_pool(profile, count, sigmas)
            # Both neutral geometry and its largest positive fixed tilt.
            for candidate in (pool['candidates'][0], pool['candidates'][-1]):
                for flow in (False, True):
                    step, _ = bound(flow)
                    state = step.initial
                    scheduler = copy.deepcopy(step.solver._template)
                    plain_cache = WorldCacheMemory.capture(step.worldcache.net)
                    plain_latent = state.latent.clone()
                    before = state_digest(state)
                    trace = {r['t']: r for r in candidate['trace']['C_states']}
                    for t, action in enumerate(candidate['policy']['actions'], 1):
                        if action == 'C':
                            record = trace[t]
                            for branch in (0, 1):
                                actual = [s.step for s in state.cache['provenance'].window[branch] if s]
                                self.assertEqual(actual[-2:], [record['a'], record['b']])
                            C_pairs += 1
                        with torch.no_grad():
                            original_state = state_digest(state)
                            after = step(state, action)
                            self.assertEqual(state_digest(state), original_state)
                            # Independent unannotated WC owner and mutable original
                            # scheduler, not a second call to the planner/solver wrapper.
                            velocity, plain_cache = step.worldcache.pair(plain_cache, step.noise,
                                plain_latent, step.timesteps[t-1].reshape(1, 1), step.conditions, action=action)
                            plain_latent = scheduler.step(velocity, step.timesteps[t-1],
                                plain_latent, return_dict=False)[0]
                        self.assertTrue(torch.equal(after.latent, plain_latent), (count, flow, t))
                        self.assertEqual(tree_digest(after.cache['fields']), tree_digest(plain_cache.fields))
                        self.assertEqual(tree_digest(after.cache['buffers']), tree_digest(plain_cache.buffers))
                        self.assertEqual(tree_digest(vars(after.memory)), tree_digest(vars(UniPCMemory.capture(scheduler))))
                        state = after
                    self.assertEqual(state_digest(step.initial), before)
                    self.assertEqual(state.memory.step_index, 36)
                    self.assertTrue(torch.isfinite(state.latent).all())
                    paths += 1
        METRICS['pinned_execution'] = dict(full36_paths=paths, CFG_branch_updates=paths*72,
            C_paired_updates=C_pairs, exact_latent_solver_cache_and_buffers=True,
            both_flow_settings=True, real_Cosmos_weights=False, video_quality_evaluated=False)


if __name__ == '__main__':
    unittest.main()
