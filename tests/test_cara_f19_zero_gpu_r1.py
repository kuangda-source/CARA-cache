"""Causal lag/CFG algebra controls and real pinned tiny full36 policy paths."""
import copy
import hashlib
import json
import os
from pathlib import Path
from types import MethodType
import unittest
import tempfile

import torch

from wcomr.cara_f19_profile_r1 import profile_policy_owner
from wcomr.cara_f19_zero_gpu_r1 import (
    analyze_saved_B1, candidate_layouts, delta_hold_error, lag_pairs, timing_audit)
from wcomr.policy_generator_r1 import production_sampling as sampling
from wcomr.mid_coverage import tree_digest, WC_FIELDS

ROOT = Path(__file__).resolve().parents[1]
METRICS = {}


def evidence():
    read = lambda p: json.loads((ROOT/p).read_text())
    manifest = read('plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json')
    timing = timing_audit(read('reports/cara_fast_B36_complete_analysis_r1_20261029.json'),
        manifest, read('reports/wc_paper_N09_full40_complete_results_analysis_20261018.json'))
    return manifest, timing, candidate_layouts(manifest, timing)


class OfflineControls(unittest.TestCase):
    def test_timing_denominator_and_unidentified_C(self):
        _, timing, _ = evidence()
        self.assertEqual(timing['F19_A1_counts'], dict(D=19, A=6, C=11))
        self.assertAlmostEqual(timing['seconds_to_save'], 16.4233043301053)
        self.assertAlmostEqual(timing['marginal_D_to_C_seconds'], 6.226303969375)
        self.assertIsNone(timing['C_seconds'])
        self.assertFalse(timing['historical_component_intervals_additive'])

    def test_layouts_keep_front_and_cycle_reset_and_blind_scores(self):
        manifest, _, layouts = evidence()
        original = layouts['original_D_steps']
        for row in layouts['candidates']:
            self.assertIn(row['count_D'], (16, 17))
            self.assertEqual([x for x in row['dense_steps'] if x <= 16],
                             [x for x in original if x <= 16])
            for value in row['variants'].values():
                plan = value['policy']
                self.assertEqual(len(plan['actions']), 36)
                self.assertEqual(plan['actions'][-1], 'D')
                self.assertEqual(plan['counts']['D'], row['count_D'])
                self.assertIsNone(value['measured_LPIPS'])
                self.assertFalse(plan['GPU_dispatch_ready'])
                for r in value['trace']:
                    if r['action'] == 'A':
                        self.assertIn(r['source_age'], (1, 2))
                        self.assertEqual(r['alpha'], 1. if r['step'] < 25 else .5)

    def test_lag_coverage_never_crosses_request_or_fills_missing_updates(self):
        rows = [dict(prompt=p, step=s) for p in ('a', 'b') for s in (22,23,25,33,34,35)]
        pairs = lag_pairs(rows)
        self.assertEqual(len(pairs), 10)
        self.assertEqual(sum(lag == 1 for _, _, lag in pairs), 6)
        self.assertEqual(sum(lag == 2 for _, _, lag in pairs), 4)
        for source, target, lag in pairs:
            self.assertEqual(source['prompt'], target['prompt'])
            self.assertEqual(target['step']-source['step'], lag)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            lag_pairs(rows+[rows[0]])

    def test_cfg_conditional_hold_uses7_and_common_motion_cancels(self):
        source = (torch.tensor([2.]), torch.tensor([1.]))
        target = (torch.tensor([5.]), torch.tensor([3.]))
        result = delta_hold_error(source, target, target)
        self.assertEqual(result['held_guided_MSE'], 49.)
        self.assertEqual(result['delta_drift_MSE'], 1.)
        self.assertIsNone(result['held_to_WC_C_MSE_ratio'])
        common = (torch.tensor([5.]), torch.tensor([4.]))
        self.assertEqual(delta_hold_error(source, common, common)['held_guided_MSE'], 0.)

    def test_cfg_branch_reversal_nonfinite_and_shape_failures(self):
        source = (torch.tensor([2.]), torch.tensor([1.]))
        target = (torch.tensor([5.]), torch.tensor([3.]))
        # If only one pair's branch order is wrong, the error is much larger.
        self.assertEqual(delta_hold_error(source[::-1], target, target)['held_guided_MSE'], 441.)
        for invalid in ((torch.tensor([float('nan')]), source[1]),
                        (torch.ones(2), source[1])):
            with self.assertRaisesRegex(ValueError, 'Finite aligned'):
                delta_hold_error(invalid, target, target)

    def test_saved_B1_IO_hash_context_and_complete_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def save(name, value):
                path = root/name
                torch.save(value, path)
                return dict(name=name, bytes=path.stat().st_size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            anchor = save('anchor.pt', dict(fixture_only=True))
            states = []
            for prompt in ('a', 'b'):
                for step in (22,23,25,33,34,35):
                    c = torch.full((1,1,1,2,2), float(step))
                    u = c-1
                    value = dict(context=(prompt,'tiny_fixture','Shared25_C'), step=step,
                        anchors=((anchor, anchor), (anchor, anchor)), teacher=(c,u),
                        readouts=dict(WC_C=dict(outputs=(c+.1,u+.1))),
                        P0_actual_dense=True, P1_dense_head_RF_equal=True, P2_C_actual_parent_equal=True)
                    states.append(dict(prompt=prompt, step=step, artifact=save(f'{prompt}_{step}.pt',value)))
            raw = json.dumps(dict(states=states)).encode()
            (root/'manifest.json').write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            result = analyze_saved_B1(root, digest)
            self.assertEqual(result['comparisons'], 10)
            self.assertEqual(result['lag_counts'], {'1':6, '2':4})
            self.assertTrue(all(r['held_guided_MSE'] == 0 for r in result['rows']))
            self.assertFalse(result['GPU_screen_ready'])
            with self.assertRaisesRegex(ValueError, 'manifest SHA'):
                analyze_saved_B1(root, '0'*64)
            changed = states[0]['artifact']['name']
            (root/changed).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'bytes/SHA mismatch'):
                analyze_saved_B1(root, digest)


class PinnedPaths(unittest.TestCase):
    def test_complete36_paths_and_noninterfering_diagnostic(self):
        from test_cara_read_write_provenance_r1 import bound, RUNTIME
        from test_cara_read_write_transition_r1 import modules
        from wcomr.cara_fast_spec_r1 import profile_from
        from wcomr.policy_interval_readout_r1 import guided

        manifest, _, layouts = evidence()
        profile = profile_from(manifest['profile'])
        plans = [('F19_A1', manifest['roles']['F19_A1']['policy'])]+[
            (row['candidate']+'_'+variant, row['variants'][variant]['policy'])
            for row in layouts['candidates']
            for variant in ('A1_RETAIN_LEGAL_ORIGINAL', 'A2_EACH_INTERVAL')]
        total = 0
        for flow in (False, True):
            outputs = {}
            for name, plan in plans+[('NO_SALIENCY', plans[0][1]), ('PROFILE', plans[0][1])]:
                step, _ = bound(flow)
                adapter, scheduler = step.worldcache, copy.deepcopy(step.solver._template)
                wc, rf = modules()
                adapter.net.forward = MethodType(wc.worldcache_mini_train_dit_forward, adapter.net)
                adapter.model.denoise = MethodType(rf.denoise, adapter.model)
                adapter.model.tensor_kwargs['dtype'] = torch.float32
                noise = step.noise.float()
                for condition in step.conditions:
                    condition.gt_frames = condition.gt_frames.float()
                    condition.cross = condition.cross.float()
                    condition.condition_video_input_mask_B_C_T_H_W = condition.condition_video_input_mask_B_C_T_H_W.float()
                if name == 'NO_SALIENCY':
                    adapter.net.worldcache_saliency_enabled = False
                owner = sampling.PolicyOwner(adapter.model, policy=plan, profile=profile,
                    context=('F19_tiny_CPU', 'declared_weights', 'flow_'+str(flow)),
                    runtime=RUNTIME, wc=wc, rf=rf)
                latent = noise.clone()
                velocities = []
                measurement = profile_policy_owner(owner, scheduler, device='cpu') if name == 'PROFILE' else None
                spans = measurement.__enter__() if measurement else None
                try:
                    with torch.no_grad():
                        for timestep in step.timesteps:
                            pair = owner.pair(noise, latent, timestep.reshape(1,1),
                                step.conditions, owner.choose)
                            velocity = guided(pair)
                            velocities.append(velocity.clone())
                            latent = scheduler.step(velocity, timestep, latent, return_dict=False)[0]
                    assert [h['actual'] for h in owner.history] == plan['actions']
                    assert not any(h['fallback_reason'] for h in owner.history)
                    state = tree_digest(dict(cache={k:getattr(owner.net,k) for k in WC_FIELDS if hasattr(owner.net,k)},
                        buffers=dict(owner.net.named_buffers()),
                        solver=dict(model_outputs=scheduler.model_outputs, last_sample=scheduler.last_sample,
                            step_index=scheduler._step_index)))
                    outputs[name] = (velocities, latent, state)
                    total += 1
                finally:
                    if measurement:
                        measurement.__exit__(None, None, None)
                    owner.close()
                if name in ('NO_SALIENCY', 'PROFILE'):
                    plain = outputs['F19_A1']
                    assert all(torch.equal(a,b) for a,b in zip(plain[0], velocities))
                    assert torch.equal(plain[1], latent)
                if name == 'PROFILE':
                    assert plain[2] == state
                    components = spans.summary['components']
                    assert components['pair_D']['calls'] == 19
                    assert components['pair_A']['calls'] == 6
                    assert components['pair_C']['calls'] == 11
                    assert components['compute_optimal_gamma']['calls'] == 34
                    assert components['compute_saliency_map']['calls'] > 0
                    assert components['_mf_a_hidden_inclusive']['calls'] == 72
                    if flow:
                        assert components['estimate_optical_flow']['calls'] == 46
                        assert components['warp_feature']['calls'] == 92
                    METRICS[str(flow)] = dict(complete36_paths=len(plans)+2,
                        profiled_unprofiled_guided_latent_cache_solver_equal=True,
                        fixed_policy_saliency_OFF_all36_guided_latent_equal=True,
                        profile_components=components, profile_intervals=spans.summary['intervals'],
                        CPU_seconds_are_not_GPU_prices=True, actual_Cosmos_weights=False,
                        actual_VAE_or_video=False)
        self.assertEqual(total, 18)
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    torch.set_num_threads(2)
    unittest.main()
