"""Actual WC/RF/UniPC tiny-state adjoint and finite hard-action controls."""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import torch

from wcomr.cara_fast_spec_r1 import profile_from, uniform_mask
from wcomr.cara_read_write_adjoint_r1 import (
    coordinates, hard_action_value, map_coordinates, pullback, terminal_cotangent,
)
from wcomr.cara_read_write_state_r1 import FunctionalUniPC, PostUpdateState, UniPCMemory
from wcomr.cara_read_write_transition_r1 import FunctionalWorldCache, WorldCacheMemory
from wcomr.mid_coverage import tree_digest

from test_cara_read_write_transition_r1 import fixture, ROOT, RUNTIME

METRICS = {}


def trajectory():
    spec = importlib.util.spec_from_file_location('read_write_adjoint_original_UniPC',
        RUNTIME/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')
    original = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = original
    spec.loader.exec_module(original)
    scheduler = original.FlowUniPCMultistepScheduler(
        num_train_timesteps=1000, shift=1, use_dynamic_shifting=False)
    scheduler.set_timesteps(35, device='cpu', shift=5, use_kerras_sigma=True)
    solver = FunctionalUniPC(scheduler)
    card = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    mask, _ = uniform_mask(card['schedule'], profile_from(card['profile']), 19)
    model, wc, rf, conditions, noise = fixture(True)
    adapter = FunctionalWorldCache(model, runtime=RUNTIME, wc=wc, rf=rf)
    cache = WorldCacheMemory.capture(model.net)
    initial = PostUpdateState(noise.clone(), UniPCMemory.capture(scheduler),
        dict(fields=cache.fields, buffers=cache.buffers))

    def step(state, index, action=None):
        timestep = scheduler.timesteps[index]
        velocity, cache = adapter.pair(WorldCacheMemory(**state.cache), noise, state.latent,
            timestep.reshape(1, 1), conditions, action=action or ('D' if index+1 in mask else 'C'))
        value, memory = solver.step(state.memory, velocity, timestep, state.latent)
        return PostUpdateState(value, memory, dict(fields=cache.fields, buffers=cache.buffers))

    objective = lambda state: 100*(state.latent-.2*noise).square().mean()
    return initial, step, objective


class Adjoint(unittest.TestCase):
    def test_full36_recomputed_adjoint_equals_direct_autograd(self):
        initial, step, objective = trajectory()
        snapshots = [initial]
        with torch.no_grad():
            for index in range(36):
                snapshots.append(step(snapshots[-1], index))
        before = tree_digest(dict(cache=snapshots[8].cache, latent=snapshots[8].latent))
        _, co = terminal_cotangent(snapshots[-1], objective)
        for index in reversed(range(36)):
            co = pullback(snapshots[index], lambda state:step(state, index), co)
        x = initial.latent.clone().requires_grad_()
        direct = replace(initial, latent=x)
        for index in range(36):
            direct = step(direct, index)
        gradient = torch.autograd.grad(objective(direct), x)[0]
        error = float((gradient-co[('latent',)]).abs().max())
        self.assertTrue(torch.allclose(gradient, co[('latent',)], atol=2e-8, rtol=2e-5))
        self.assertEqual(before, tree_digest(dict(cache=snapshots[8].cache, latent=snapshots[8].latent)))
        METRICS['full36_recomputed_adjoint'] = dict(max_absolute_error=error,
            agrees_with_direct_graph=True, snapshots_unchanged=True, actual_Cosmos_weights=False)

    def test_read_write_contractions_match_auxiliary_state_directional_differences(self):
        initial, step, objective = trajectory()
        snapshots = [initial]
        with torch.no_grad():
            for index in range(36):
                snapshots.append(step(snapshots[-1], index))
        _, co = terminal_cotangent(snapshots[-1], objective)
        for index in reversed(range(8, 36)):
            co = pullback(snapshots[index], lambda state:step(state, index), co)
        with torch.no_grad():
            cached, dense = step(snapshots[7], 7, 'C'), step(snapshots[7], 7, 'D')
        values = hard_action_value(cached, dense, co, incumbent='C')
        c, d = coordinates(cached), coordinates(dense)

        def evaluate(u, group):
            def interpolate(path, value):
                chosen = group == 'total' or (path[0] == 'cache') == (group == 'write')
                if not chosen:
                    return value
                other = d.get(path, torch.zeros_like(value))
                return value+u*(other-value)
            state = map_coordinates(cached, interpolate)
            with torch.no_grad():
                for index in range(8, 36):
                    state = step(state, index)
                return float(objective(state))

        checks = []
        for group in ('read', 'write', 'total'):
            # RF casts to FP32. The read D-C direction is much smaller than
            # the cache direction; use two larger auxiliary-state amplitudes
            # to resolve it above quantization. R1 records the smaller-step
            # precision failure; do not alter RF or detach its gradient.
            for epsilon in ((.5, 1.) if group == 'read' else (.1, .2)):
                numerical = (evaluate(epsilon, group)-evaluate(-epsilon, group))/(2*epsilon)
                tolerance = max(3e-8, abs(values[group])*.05)
                self.assertAlmostEqual(values[group], numerical, delta=tolerance)
                checks.append(dict(group=group, predicted=values[group], central_FD=numerical,
                    absolute_error=abs(values[group]-numerical), epsilon=epsilon, tolerance=tolerance))
        self.assertAlmostEqual(values['total'], values['read']+values['write'])
        self.assertGreater(abs(values['write']), 1e-5)
        METRICS['actual_WC_tiny_point8_auxiliary_derivatives'] = checks

    def test_dense_incumbent_uses_the_same_D_minus_C_sign(self):
        state, step, objective = trajectory()
        with torch.no_grad():
            for index in range(15):
                state = step(state, index)
            cached, dense = step(state, 15, 'C'), step(state, 15, 'D')
        # A nearby synthetic terminal suffices to check the sign convention at
        # u=1; the separate full36 check covers the actual reverse recurrence.
        _, co = terminal_cotangent(dense, objective)
        values = hard_action_value(cached, dense, co, incumbent='D')
        c = coordinates(cached)
        def evaluate(u):
            mixed = map_coordinates(dense, lambda path,value:value+(u-1)*(value-c[path]))
            return float(objective(mixed))
        epsilon = .01
        numerical = (evaluate(1+epsilon)-evaluate(1-epsilon))/(2*epsilon)
        self.assertAlmostEqual(values['total'], numerical, delta=1e-8)
        METRICS['dense_incumbent_same_D_minus_C_sign'] = dict(values=values, central_FD=numerical)

    def test_last_C_write_before_reset_has_zero_terminal_cache_value(self):
        state, step, objective = trajectory()
        with torch.no_grad():
            for index in range(34):
                state = step(state, index)
            cached, dense = step(state, 34, 'C'), step(state, 34, 'D')
            final = step(cached, 35)
        _, co = terminal_cotangent(final, objective)
        co = pullback(cached, lambda value:step(value, 35), co)
        values = hard_action_value(cached, dense, co, incumbent='C')
        self.assertEqual(values['write'], 0.)
        METRICS['actual_WC_post35_no_future_cache_consumer'] = values

    def test_partial_cotangent_wrong_precision_and_changed_slots_refused(self):
        state, step, objective = trajectory()
        with torch.no_grad():
            for index in range(7):
                state = step(state, index)
            cached, dense = step(state, 7, 'C'), step(state, 7, 'D')
        _, co = terminal_cotangent(cached, objective)
        partial = dict(co);partial.pop(('latent',))
        with self.assertRaisesRegex(ValueError, 'Complete matching'):
            pullback(state, lambda value:step(value, 7), partial)
        wrong = dict(co);wrong[('latent',)] = wrong[('latent',)].float()
        with self.assertRaisesRegex(ValueError, 'precision'):
            hard_action_value(cached, dense, wrong, incumbent='C')
        malformed = {**dense.cache, 'fields':{**dense.cache['fields'], 'residual_window':[[], []]}}
        with self.assertRaisesRegex(ValueError, 'slot layout'):
            hard_action_value(cached, replace(dense, cache=malformed), co, incumbent='C')
        with self.assertRaisesRegex(ValueError, 'Aligned same-update'):
            hard_action_value(cached, replace(dense, memory=replace(dense.memory, this_order=1)), co, incumbent='C')


if __name__ == '__main__':
    unittest.main()
