"""CPU controls: original UniPC, explicit memory, and bounded hard proposals.

The small nonlinear velocity/cache examples are declared synthetic systems.
They check derivatives and attribution conventions, not Cosmos video quality.
"""
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

import torch

from wcomr.cara_fast_spec_r1 import profile_from, policy_from_mask, uniform_mask
from wcomr.cara_read_write_proposals_r1 import propose_exchanges
from wcomr.cara_read_write_state_r1 import (
    FunctionalUniPC, PostUpdateState, UniPCMemory, factorial_effects,
    read_write_corners,
)
from wcomr.mid_coverage import tree_digest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('CARA_READ_WRITE_RUNTIME', ROOT / '.sync/wc-time-p0-runtime'))
METRICS = {}


def original_scheduler():
    path = RUNTIME / 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py'
    name = 'cara_read_write_original_unipc'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    scheduler = sys.modules[name].FlowUniPCMultistepScheduler(
        num_train_timesteps=1000, shift=1, use_dynamic_shifting=False)
    scheduler.set_timesteps(35, device='cpu', shift=5, use_kerras_sigma=True)
    return scheduler


def profile_and_mask():
    card = json.loads((ROOT / 'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    profile = profile_from(card['profile'])
    scheduler = original_scheduler()
    mask, _ = uniform_mask(dict(actual_updates=len(scheduler.timesteps),
        timesteps=scheduler.timesteps.tolist(), sigmas=scheduler.sigmas.tolist()), profile, 19)
    return profile, mask


class OriginalUniPCState(unittest.TestCase):
    def test_all36_forward_and_mutable_history_match_original(self):
        scheduler = original_scheduler()
        functional = FunctionalUniPC(scheduler)
        memory = UniPCMemory.capture(scheduler)
        x = torch.tensor([[.5, -.3, .2]], dtype=torch.float64)
        reference = x.clone()
        for index, t in enumerate(scheduler.timesteps):
            velocity = .11 * x + .03 * x.square() + .002 * index
            old = tree_digest(vars(scheduler))
            updated, memory = functional.step(memory, velocity, t, x)
            self.assertEqual(tree_digest(vars(scheduler)), old)
            reference = scheduler.step(.11 * reference + .03 * reference.square() + .002 * index,
                                       t, reference, return_dict=False)[0]
            self.assertTrue(torch.equal(updated, reference))
            self.assertEqual(tree_digest(vars(memory)), tree_digest(vars(UniPCMemory.capture(scheduler))))
            x = updated
        self.assertEqual(memory.step_index, 36)
        METRICS['all36_forward_and_complete_memory_exact'] = True

    def test_rollout_keeps_gradient_to_initial_sample(self):
        scheduler = original_scheduler()
        functional = FunctionalUniPC(scheduler)
        initial = torch.tensor([[.2, -.4]], dtype=torch.float64, requires_grad=True)
        def evaluate(value):
            x, memory = value, UniPCMemory.capture(scheduler)
            for t in scheduler.timesteps:
                x, memory = functional.step(memory, .1 * x + .015 * x.square(), t, x)
            return x.square().mean()
        derivative = torch.autograd.grad(evaluate(initial), initial)[0]
        direction = torch.tensor([[.3, -.2]], dtype=torch.float64)
        epsilon = 1e-5
        numerical = (evaluate(initial.detach() + epsilon * direction) -
                     evaluate(initial.detach() - epsilon * direction)) / (2 * epsilon)
        predicted = (derivative * direction).sum()
        self.assertTrue(torch.allclose(predicted, numerical, atol=1e-8, rtol=2e-5))
        METRICS['full36_synthetic_velocity_VJP_absolute_error'] = abs(float(predicted - numerical))

    def test_directional_derivative_includes_prediction_history_and_last_sample(self):
        scheduler = original_scheduler()
        x = torch.tensor([[.2, -.4, .7]], dtype=torch.float64)
        for index, t in enumerate(scheduler.timesteps[:12]):
            x = scheduler.step(.09 * x + .01 * x.square() + .001 * index,
                               t, x, return_dict=False)[0]
        functional = FunctionalUniPC(scheduler)
        memory = UniPCMemory.capture(scheduler)
        parts = [x, *memory.model_outputs, memory.last_sample]
        leaves = [p.detach().clone().requires_grad_() for p in parts]
        directions = [torch.tensor([[.03, -.05, .08]], dtype=torch.float64) * (i + 1)
                      for i in range(len(leaves))]
        def evaluate(values):
            value = values[0]
            history = replace(memory, model_outputs=tuple(values[1:3]), last_sample=values[3])
            for t in scheduler.timesteps[12:17]:
                value, history = functional.step(history, .09 * value + .01 * value.square(), t, value)
            return value.square().mean()
        gradients = torch.autograd.grad(evaluate(leaves), leaves)
        components = [float((g * d).sum()) for g, d in zip(gradients, directions)]
        predicted = sum(components)
        epsilon = 1e-5
        high = evaluate([p.detach() + epsilon * d for p, d in zip(leaves, directions)])
        low = evaluate([p.detach() - epsilon * d for p, d in zip(leaves, directions)])
        numerical = float((high - low) / (2 * epsilon))
        self.assertAlmostEqual(predicted, numerical, delta=2e-7)
        self.assertGreater(abs(sum(components[1:])), 1e-5)
        METRICS['history_VJP'] = dict(predicted=predicted, finite_difference=numerical,
            absolute_error=abs(predicted - numerical), memory_contribution=sum(components[1:]),
            per_coordinate_group=components)

    def test_same_input_memory_not_mutated_and_calls_independent(self):
        scheduler = original_scheduler()
        x = torch.ones(1, 3, dtype=torch.float64)
        for t in scheduler.timesteps[:3]:
            x = scheduler.step(.2 * x, t, x, return_dict=False)[0]
        memory = UniPCMemory.capture(scheduler)
        functional = FunctionalUniPC(scheduler)
        before = tree_digest(vars(memory))
        first, _ = functional.step(memory, .2 * x, scheduler.timesteps[3], x)
        functional.step(memory, .7 * x, scheduler.timesteps[3], x)
        repeated, _ = functional.step(memory, .2 * x, scheduler.timesteps[3], x)
        self.assertEqual(tree_digest(vars(memory)), before)
        self.assertTrue(torch.equal(first, repeated))

    def test_read_and_write_directional_derivatives_through_original_unipc_suffix(self):
        scheduler = original_scheduler()
        x = torch.tensor([[.2, -.4, .7]], dtype=torch.float64)
        cache = torch.tensor([[.3, -.1, .2]], dtype=torch.float64)
        for t in scheduler.timesteps[:7]:
            x = scheduler.step(.1 * x, t, x, return_dict=False)[0]
        functional = FunctionalUniPC(scheduler)
        memory = UniPCMemory.capture(scheduler)
        xc, mc = functional.step(memory, .12 * cache + .03 * x,
                                 scheduler.timesteps[7], x)
        xd, md = functional.step(memory, .14 * x + .02 * x.square(),
                                 scheduler.timesteps[7], x)
        cc, cd = .9 * cache + .1 * x.square(), .2 * x + .5

        def evaluate(read, write):
            value = torch.lerp(xc, xd, read)
            state = replace(mc,
                model_outputs=tuple(torch.lerp(a, b, read) for a, b in zip(mc.model_outputs, md.model_outputs)),
                last_sample=torch.lerp(mc.last_sample, md.last_sample, read))
            working = torch.lerp(cc, cd, write)
            for index, t in enumerate(scheduler.timesteps[8:], 8):
                # Declared synthetic differentiable cache recurrence. C also
                # writes working state; it is not an identity cache map.
                velocity = .1 * value + .04 * working.square()
                working = .96 * working + .04 * value
                value, state = functional.step(state, velocity, t, value)
            return (value - .1).square().mean()

        read = torch.tensor(0., dtype=torch.float64, requires_grad=True)
        write = torch.tensor(0., dtype=torch.float64, requires_grad=True)
        gr, gw = torch.autograd.grad(evaluate(read, write), (read, write))
        epsilon = 1e-5
        fd_read = (evaluate(epsilon, 0.) - evaluate(-epsilon, 0.)) / (2 * epsilon)
        fd_write = (evaluate(0., epsilon) - evaluate(0., -epsilon)) / (2 * epsilon)
        self.assertAlmostEqual(float(gr), float(fd_read), delta=2e-7)
        self.assertAlmostEqual(float(gw), float(fd_write), delta=2e-7)
        self.assertGreater(abs(float(gw)), 1e-6)
        effects = factorial_effects({k: float(evaluate(float(k[0]), float(k[1])))
                                     for k in ('00', '10', '01', '11')})
        self.assertAlmostEqual(effects['read'] + effects['write'] + effects['interaction'], effects['total'])
        METRICS['synthetic_cache_actual_UniPC_suffix'] = dict(
            read_gradient=float(gr), write_gradient=float(gw),
            read_FD_error=abs(float(gr - fd_read)), write_FD_error=abs(float(gw - fd_write)),
            hard_four_corner_effects=effects,
            actual_Cosmos_cache_or_model=False)

    def test_template_keeps_original_grid_if_caller_changes(self):
        scheduler = original_scheduler()
        functional = FunctionalUniPC(scheduler)
        memory = UniPCMemory.capture(scheduler)
        x = torch.ones(1, dtype=torch.float64)
        original_t = scheduler.timesteps[0].clone()
        first, _ = functional.step(memory, .1 * x, original_t, x)
        scheduler.sigmas[1] = .05
        second, _ = functional.step(memory, .1 * x, original_t, x)
        self.assertTrue(torch.equal(first, second))

    def test_unknown_scheduler_and_auxiliary_solver_refused(self):
        class Other:
            pass
        with self.assertRaises(ValueError):
            FunctionalUniPC(Other())
        scheduler = original_scheduler()
        scheduler.solver_p = object()
        with self.assertRaises(ValueError):
            FunctionalUniPC(scheduler)


class FourCornerState(unittest.TestCase):
    def states(self):
        scheduler = original_scheduler()
        memory = UniPCMemory.capture(scheduler)
        # Bundle values and source identity together. These are synthetic
        # stand-ins, never registered Cosmos feature tensors.
        cached = PostUpdateState(torch.tensor([.2], dtype=torch.float64), memory,
            dict(value=torch.tensor([.3], dtype=torch.float64), source_steps=(6, 7), source_sigmas=(.9, .8)))
        dense = PostUpdateState(torch.tensor([.6], dtype=torch.float64),
            replace(memory, last_sample=torch.tensor([.4], dtype=torch.float64)),
            dict(value=torch.tensor([.7], dtype=torch.float64), source_steps=(7, 8), source_sigmas=(.8, .7)))
        return cached, dense

    def test_mixed_corners_keep_solver_with_read_and_provenance_with_write(self):
        c, d = self.states()
        corners = read_write_corners(c, d)
        self.assertIs(corners['00'], c)
        self.assertIs(corners['11'], d)
        self.assertIs(corners['10'].latent, d.latent)
        self.assertIs(corners['10'].memory, d.memory)
        self.assertIs(corners['10'].cache, c.cache)
        self.assertIs(corners['01'].latent, c.latent)
        self.assertIs(corners['01'].memory, c.memory)
        self.assertIs(corners['01'].cache, d.cache)

    def test_unequal_post_update_boundary_refused(self):
        c, d = self.states()
        with self.assertRaises(ValueError):
            read_write_corners(c, replace(d, memory=replace(d.memory, step_index=3)))

    def test_exact_signed_read_write_interaction_identity(self):
        corners = read_write_corners(*self.states())
        losses = {k: float((s.latent + s.cache['value']).square().mean())
                  for k, s in corners.items()}
        effects = factorial_effects(losses)
        self.assertAlmostEqual(effects['total'], effects['read'] + effects['write'] + effects['interaction'])
        self.assertGreater(effects['interaction'], .1)
        METRICS['synthetic_four_corner_effects'] = effects

    def test_equal_current_output_can_have_future_write_effect(self):
        c, d = self.states()
        d = replace(d, latent=c.latent, memory=c.memory)
        corners = read_write_corners(c, d)
        losses = {k: float((s.latent + s.cache['value'] - 1).square().mean())
                  for k, s in corners.items()}
        effects = factorial_effects(losses)
        self.assertEqual(effects['read'], 0)
        self.assertLess(effects['write'], -.1)

    def test_no_future_cache_consumer_has_zero_write_effect(self):
        corners = read_write_corners(*self.states())
        effects = factorial_effects({k: float(s.latent.square().mean()) for k, s in corners.items()})
        self.assertEqual(effects['write'], 0)
        self.assertAlmostEqual(effects['interaction'], 0)

    def test_missing_or_nonfinite_loss_refused(self):
        for losses in [dict.fromkeys(('00', '10', '11'), 1.),
                       dict(zip(('00', '10', '01', '11'), (1., 2., 3., float('nan'))))]:
            with self.assertRaises(ValueError):
                factorial_effects(losses)


class BoundedProposals(unittest.TestCase):
    def test_signed_value_orientation_and_exact_legal_budget(self):
        profile, mask = profile_and_mask()
        values = [0.] * 36
        values[7] = -3.  # C8 -> D8 helps in the linear model.
        values[15] = 2.  # D16 -> C16 helps in the linear model.
        proposals = propose_exchanges(profile, mask, values)
        self.assertEqual(len(proposals), 1)
        p = proposals[0]
        self.assertEqual(p['added_D'], [8])
        self.assertEqual(p['removed_D'], [16])
        self.assertEqual(p['predicted_loss_change'], -5.)
        self.assertEqual(p['policy']['counts']['D'], 19)
        selected = [i for i, action in enumerate(p['policy']['actions'], 1) if action == 'D']
        self.assertTrue(set(profile.protected_dense) <= set(selected))
        self.assertFalse(p['endpoint_evaluated'])
        self.assertFalse(p['measured_time_accepted'])

    def test_radius_two_can_propose_two_exchanges_without_duplicating_queries(self):
        profile, mask = profile_and_mask()
        values = [0.] * 36
        for t, value in [(8, -5.), (9, -4.), (16, 3.), (19, 2.)]:
            values[t - 1] = value
        proposals = propose_exchanges(profile, mask, values)
        self.assertEqual(len(proposals), 2)
        self.assertEqual(proposals[1]['added_D'], [8, 9])
        self.assertEqual(proposals[1]['removed_D'], [16, 19])
        self.assertLess(proposals[1]['predicted_loss_change'], proposals[0]['predicted_loss_change'])
        METRICS['synthetic_proposals'] = [{k: v for k, v in p.items() if k != 'policy'} for p in proposals]

    def test_protected_refresh_cannot_be_removed_even_if_linear_value_high(self):
        profile, mask = profile_and_mask()
        values = [0.] * 36
        values[0] = 1000.
        values[7] = -1.
        for p in propose_exchanges(profile, mask, values):
            self.assertNotIn(1, p['removed_D'])

    def test_source_age_is_enforced_by_real_grammar(self):
        profile, mask = profile_and_mask()
        profile = replace(profile, max_source_age=8)
        values = [0.] * 36
        values[15] = 9.
        values[34] = -9.
        for p in propose_exchanges(profile, mask, values):
            selected = [i for i, action in enumerate(p['policy']['actions'], 1) if action == 'D']
            # Removing D16 needs a replacement within the resulting long gap;
            # the unconstrained best exchange D16 -> D35 must be refused.
            self.assertNotEqual((p['removed_D'], p['added_D']), ([16], [35]))
            self.assertEqual(policy_from_mask(profile, selected), p['policy'])
            self.assertLessEqual(max(b - a - 1 for a, b in zip(selected, selected[1:] + [37])), 8)

    def test_zero_signal_does_not_create_fake_improving_candidate(self):
        profile, mask = profile_and_mask()
        self.assertEqual(propose_exchanges(profile, mask, [0.] * 36), [])

    def test_deterministic_ties_and_at_most_two_candidates(self):
        profile, mask = profile_and_mask()
        values = [-1. if t not in mask else 1. for t in range(1, 37)]
        one = propose_exchanges(profile, mask, values)
        two = propose_exchanges(profile, mask, values)
        self.assertEqual(one, two)
        self.assertLessEqual(len(one), 2)
        self.assertEqual(len({p['policy']['fingerprint'] for p in one}), len(one))

    def test_incomplete_nonfinite_or_illegal_parent_refused(self):
        profile, mask = profile_and_mask()
        for values in [[0.] * 35, [float('inf')] + [0.] * 35]:
            with self.assertRaises(ValueError):
                propose_exchanges(profile, mask, values)
        with self.assertRaises(ValueError):
            propose_exchanges(profile, mask[1:], [0.] * 36)


if __name__ == '__main__':
    unittest.main()
