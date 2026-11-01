"""Exact proxy k-best, inherited legality and fixed solver-scale controls."""
from dataclasses import replace
from itertools import combinations
import math
import unittest

import torch

from wcomr.cara_fast_spec_r1 import policy_from_mask
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.cara_source_lifecycle_planner_r1 import plan
from wcomr.cara_source_lifecycle_weights_r1 import current_velocity_weights
from wcomr.cara_read_write_state_r1 import FunctionalUniPC, UniPCMemory
from test_cara_read_write_provenance_r1 import bound

METRICS = {}


def small_profile():
    return Profile(horizon=9, protected_dense=(1,2,9), max_source_age=3,
        min_C_anchors=2, min_A_anchors=1, identity='DECLARED_CPU_PROXY_ONLY')


def enumerate_plans(profile, count, risk, weights):
    options = sorted(set(range(1,profile.horizon+1))-set(profile.protected_dense))
    results = []
    for extra in combinations(options, count-len(profile.protected_dense)):
        mask = sorted((*profile.protected_dense,*extra))
        try:
            policy_from_mask(profile,mask)
        except ValueError:
            continue
        terms = []
        for index,b in enumerate(mask):
            c = mask[index+1] if index+1 < len(mask) else profile.horizon+1
            a = mask[index-1] if index else 0
            terms.extend(weights[t-1]*risk(t,a,b) for t in range(b+1,c))
        results.append((math.fsum(terms),mask))
    return sorted(results)


class Planner(unittest.TestCase):
    def test_k_best_matches_exhaustive_all_small_budgets(self):
        profile = small_profile();weights = [1+.01*i for i in range(9)]
        risk = lambda t,a,b: float(((t-b)*(b-a))**2+.03*t)
        for count in range(3,10):
            expected = enumerate_plans(profile,count,risk,weights)[:3]
            if not expected:
                with self.assertRaisesRegex(ValueError,'No legal'):
                    plan(profile,count,risk,weights)
                continue
            actual = plan(profile,count,risk,weights)['plans']
            self.assertEqual([r['dense_steps'] for r in actual],[m for _,m in expected])
            for row,(value,_) in zip(actual,expected):
                self.assertAlmostEqual(row['proxy_cost'],value,delta=1e-10)
        METRICS['brute_force'] = dict(all_D_budgets=list(range(3,10)),
            top3_exact=True, horizon=9, synthetic_proxy=True)

    def test_true_sources_change_downstream_cost_and_ties_are_deterministic(self):
        calls = set()
        def risk(t,a,b):
            self.assertTrue(1 <= a < b < t <= 9)
            calls.add((t,a,b))
            return float((t-b)*(b-a))
        result = plan(small_profile(),5,risk,[1.]*9)
        self.assertTrue(any(a != x and t == u and b == y
            for t,a,b in calls for u,x,y in calls))
        tied = plan(small_profile(),5,lambda t,a,b:1.,[1.]*9)
        expected = enumerate_plans(small_profile(),5,lambda t,a,b:1.,[1.]*9)[:3]
        self.assertEqual([r['dense_steps'] for r in tied['plans']],[m for _,m in expected])
        self.assertFalse(result['final_LPIPS_optimized_exactly'])
        self.assertFalse(result['endpoint_evaluated'])
        METRICS['source_recomputation'] = dict(different_previous_D_at_same_t_b=True,
            full_affected_intervals_recomputed=True, deterministic_top3_ties=True)

    def test_original36_generates_exact19_and22_without_F19_initialization(self):
        step,_ = bound()
        from wcomr.cara_fast_spec_r1 import profile_from
        import json
        from test_cara_read_write_transition_r1 import ROOT
        card = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
        profile = profile_from(card['profile'])
        weights = current_velocity_weights(step.solver._template)['weights']
        rows = {}
        for budget in (19,22):
            result = plan(profile,budget,lambda t,a,b:float((t-b)**2*(1+.1*(b-a))),weights)
            masks = [r['dense_steps'] for r in result['plans']]
            self.assertEqual(len({tuple(m) for m in masks}),len(masks))
            self.assertTrue(all(len(m)==budget and set(profile.protected_dense)<=set(m) for m in masks))
            rows[str(budget)] = dict(distinct_candidates=len(masks), masks=masks, real_fit_selected=False)
        METRICS['synthetic_full36'] = rows

    def test_solver_scales_match_current_input_autograd_on_nonzero_history(self):
        step,_ = bound();scheduler = step.solver._template
        result = current_velocity_weights(scheduler)
        memory = UniPCMemory.capture(scheduler);sample = torch.full((1,1,1,1,1),.23)
        errors = []
        for index,timestep in enumerate(scheduler.timesteps):
            velocity = torch.full_like(sample,.05+.003*index,requires_grad=True)
            updated,memory_after = step.solver.step(memory,velocity,timestep,sample)
            derivative = float(torch.autograd.grad(updated,velocity)[0])
            errors.append(abs(derivative-result['coefficients'][index]))
            sample,memory = updated.detach(),replace(memory_after,
                model_outputs=tuple(None if v is None else v.detach() for v in memory_after.model_outputs),
                last_sample=memory_after.last_sample.detach())
        self.assertLessEqual(max(errors),1e-5)
        self.assertEqual(len(result['weights']),36)
        self.assertTrue(all(math.isfinite(w) and w>=0 for w in result['weights']))
        self.assertFalse(result['terminal_sensitivity'])
        METRICS['UniPC_current_input_scale'] = dict(updates=36,max_gradient_error=max(errors),
            includes_current_corrector_and_predictor=True, terminal_sensitivity=False)

    def test_partial_negative_risk_impossible_budget_and_extra_actions_refused(self):
        profile = small_profile()
        with self.assertRaisesRegex(ValueError,'Complete frozen'):
            plan(profile,4,lambda *args:1.,[1.]*8)
        with self.assertRaisesRegex(ValueError,'nonnegative source'):
            plan(profile,4,lambda *args:-1.,[1.]*9)
        with self.assertRaisesRegex(ValueError,'Exact-K'):
            plan(profile,2,lambda *args:1.,[1.]*9)
        with self.assertRaisesRegex(ValueError,'Exact-K'):
            plan(profile,4,lambda *args:1.,[1.]*9,top_k=4)
        with self.assertRaisesRegex(ValueError,'two-anchor'):
            plan(replace(profile,min_C_anchors=1),4,lambda *args:1.,[1.]*9)
        METRICS['refusals'] = ['partial_weights','negative_risk','underprotected_budget',
                               'over3_candidates','wrong_source_grammar']


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main()
