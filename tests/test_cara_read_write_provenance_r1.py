"""Original full36 WC/UniPC state, source lifecycle and augmented VJP controls."""
from dataclasses import replace
import importlib.util
import json
import sys
import unittest

import torch

from wcomr.cara_fast_spec_r1 import profile_from, uniform_mask
from wcomr.cara_read_write_adjoint_r1 import coordinates, hard_action_value, pullback, terminal_cotangent
from wcomr.cara_read_write_provenance_r1 import CacheProvenance
from wcomr.cara_read_write_step_r1 import ReadWriteStep
from wcomr.cara_read_write_transition_r1 import FunctionalWorldCache, WorldCacheMemory
from wcomr.mid_coverage import tree_digest
from test_cara_read_write_transition_r1 import fixture, ROOT, RUNTIME

METRICS = {}
OWNER = 'd'*64


def bound(flow=True):
    spec = importlib.util.spec_from_file_location('read_write_source_original_UniPC',
        RUNTIME/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')
    original = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = original
    spec.loader.exec_module(original)
    scheduler = original.FlowUniPCMultistepScheduler(
        num_train_timesteps=1000, shift=1, use_dynamic_shifting=False)
    scheduler.set_timesteps(35, device='cpu', shift=5, use_kerras_sigma=True)
    model, wc, rf, conditions, noise = fixture(flow)
    adapter = FunctionalWorldCache(model, runtime=RUNTIME, wc=wc, rf=rf)
    step = ReadWriteStep(adapter, scheduler, noise, conditions, owner=OWNER)
    card = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    mask, _ = uniform_mask(card['schedule'], profile_from(card['profile']), 19)
    return step, mask


def snapshots(step, mask):
    result = [step.initial]
    with torch.no_grad():
        for index in range(36):
            result.append(step(result[-1], 'D' if index+1 in mask else 'C'))
    return result


class Provenance(unittest.TestCase):
    def test_all36_both_flows_match_unannotated_original_adapter(self):
        for flow in (False, True):
            step, mask = bound(flow)
            state = step.initial
            plain = replace(state, cache={k:v for k,v in state.cache.items() if k != 'provenance'})
            for index in range(36):
                action = 'D' if index+1 in mask else 'C'
                with torch.no_grad():
                    state = step(state, action)
                    # Independently delegate exactly the same WC/CFG and original
                    # solver update with no provenance object attached.
                    velocity, cache = step.worldcache.pair(WorldCacheMemory(**plain.cache), step.noise,
                        plain.latent, step.timesteps[index].reshape(1,1), step.conditions, action=action)
                    latent, memory = step.solver.step(plain.memory, velocity, step.timesteps[index], plain.latent)
                    plain = replace(plain, latent=latent, memory=memory, cache=cache.bundle())
                self.assertTrue(torch.equal(state.latent, plain.latent))
                self.assertEqual(tree_digest({k:v for k,v in state.cache.items() if k != 'provenance'}),
                                 tree_digest(plain.cache))
                slots = state.cache['provenance'].slots(state.cache['fields'])
                self.assertEqual(len(slots), 22)
                self.assertEqual(state.cache['provenance'].completed, index+1)
            METRICS['flow_'+str(flow)+'_complete36'] = dict(exact_latent_cache_and_buffers=True,
                fixed_feature_slots=22, invalid_slots_are_None=True, original_reset_at35=True,
                actual_Cosmos_weights=False)

    def test_three_physical_slots_C_working_write_and_D_shift(self):
        step, mask = bound()
        states = snapshots(step, mask)
        parent = states[7]
        cached, dense = step(parent, 'C'), step(parent, 'D')
        c, d = cached.cache['provenance'], dense.cache['provenance']
        self.assertEqual([s.step for s in parent.cache['provenance'].window[0]], [1,6,7])
        self.assertEqual([s.step for s in c.window[0]], [1,6,7])
        self.assertEqual([s.step for s in d.window[0]], [1,7,8])
        for branch in (0,1):
            self.assertEqual(c.working[branch].step, 8)
            self.assertEqual(c.working[branch].action, 'C')
            self.assertEqual(c.residual[branch].step, 7)
            self.assertEqual(d.residual[branch].step, 8)
            self.assertEqual(d.residual[branch].sigma, d.sigmas[7])
            self.assertEqual(d.residual[branch].branch, branch)
            self.assertIs(dense.cache['fields']['residual_window'][branch][0],
                          parent.cache['fields']['residual_window'][branch][0])
        # Source metadata contains no Tensor; all active floating fields and
        # buffers remain in the independent complete adjoint coordinates.
        self.assertEqual(set(coordinates(cached)), set(coordinates(replace(cached,
            cache={k:v for k,v in cached.cache.items() if k != 'provenance'}))))
        METRICS['point8_sources'] = dict(parent_slots=[1,6,7], cached_slots=[1,6,7],
            dense_slots=[1,7,8], C_working_source=8, C_true_D_source=7,
            both_branches_and_actual_source_sigma=True, continuous_coordinates_not_pruned=True)

    def test_reset35_final_output_epilogue_and_regrowth36(self):
        step, mask = bound()
        states = snapshots(step, mask)
        a, b = states[35].cache, states[36].cache
        p, q = a['provenance'], b['provenance']
        self.assertEqual(a['fields']['cnt'], 0)
        self.assertEqual(p.working, (None,None))
        self.assertEqual(p.residual, (None,None))
        self.assertEqual(p.window, ((None,None,None),(None,None,None)))
        self.assertIsNone(p.output[0])
        self.assertEqual(p.output[1].step, 35)
        self.assertEqual(p.output[1].action, 'C')
        self.assertIsNone(a['fields']['previous_output'][0])
        for branch in (0,1):
            self.assertEqual(q.window[branch][0].step, 36)
            self.assertEqual(q.window[branch][1:], (None,None))
        self.assertEqual(b['fields']['cnt'], 2)
        METRICS['reset_lifecycle'] = dict(clears_working_residual_windows=True,
            output_sources_after_epilogue=[None,35], output_action='C',
            regrown_source=36, regrown_window_validity=[True,False,False])

    def test_bound_full36_augmented_adjoint_matches_direct_graph(self):
        step, mask = bound()
        states = snapshots(step, mask)
        objective = lambda state: 100*(state.latent-.2*step.noise).square().mean()
        _, co = terminal_cotangent(states[-1], objective)
        for index in reversed(range(36)):
            action = 'D' if index+1 in mask else 'C'
            co = pullback(states[index], lambda state:step(state, action), co)
        x = step.initial.latent.clone().requires_grad_()
        direct = replace(step.initial, latent=x)
        for index in range(36):
            direct = step(direct, 'D' if index+1 in mask else 'C')
        gradient = torch.autograd.grad(objective(direct), x)[0]
        error = float((gradient-co[('latent',)]).abs().max())
        self.assertTrue(torch.allclose(gradient, co[('latent',)], atol=2e-8, rtol=2e-5))
        METRICS['bound_augmented_adjoint'] = dict(full_updates=36, max_absolute_error=error,
            source_metadata_not_differentiated=True, complete_tiny_adjoint=True, actual_Cosmos_weights=False)

    def test_foreign_owner_counter_grid_and_missing_slot_refused(self):
        step, mask = bound()
        states = snapshots(step, mask)
        cached, dense = step(states[7], 'C'), step(states[7], 'D')
        _, co = terminal_cotangent(cached, lambda s:s.latent.square().mean())
        self.assertTrue(cached.cache['provenance'].same_parent_chart(dense.cache['provenance']))
        hard_action_value(cached, dense, co, incumbent='C')
        for changed in (replace(dense.cache['provenance'], owner='f'*64),
                        replace(dense.cache['provenance'], sigmas=(1.,)*36)):
            with self.assertRaisesRegex(ValueError, 'Same request/grid'):
                hard_action_value(cached, replace(dense, cache=dict(dense.cache, provenance=changed)), co, incumbent='C')
        with self.assertRaisesRegex(ValueError, 'solver history'):
            step(replace(states[7], memory=replace(states[7].memory, step_index=6)), 'C')
        fields = dict(states[7].cache['fields'], residual_window=[[],[]])
        with self.assertRaisesRegex(ValueError, 'window length'):
            states[7].cache['provenance'].slots(fields)
        with self.assertRaisesRegex(ValueError, 'complete36'):
            CacheProvenance.start(step.initial.cache['fields'], owner=OWNER,
                timesteps=step.timesteps[:35], sigmas=step.grid[1])
        METRICS['refusals'] = ['foreign_owner','foreign_sigma_grid','solver_cache_misalignment',
                               'missing_physical_window','partial_grid']


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main()
