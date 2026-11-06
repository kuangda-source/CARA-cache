"""Pinned WC/RF, both flows: compare shared-prefix ACR with real C/A/D bodies.

Weights/attention are explicitly Toy CPU fixtures. No real Cosmos parameter,
teacher label, video quality or latency result is produced by this program.
"""
import copy
import importlib.util
from pathlib import Path
import types

import torch

from wcomr.calibration import ResidualCalibrator
from wcomr.cfg_paired_probe_forward import forced_reference, RF_PATH
from wcomr.cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from wcomr.cfg_guided_w1_forward import compile_collection
from wcomr.math_n2_source_readout_r1 import SourceFusionReadout
from wcomr.mid_coverage import tree_digest
from wcomr.p_acr_readout_r1 import ACRReadoutExecutor, CACHE_FIELDS, WINDOW_FIELDS, compensate


def load(name):
    s = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def exercise(*, inference, wc, flow, runtime, **kwargs):
    base = copy.deepcopy(inference.pipe.model.net)
    class Head(torch.nn.Module):
        def forward(self, x, *args, **kw): return x
    base.final_layer = Head().eval()
    base.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    wc.__file__ = str(runtime / 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py')
    namespace = vars(wc)
    load('check_full_sampling').load_functions(Path(wc.__file__), ['compute_saliency_map'], namespace)
    rf = types.ModuleType('acr_pinned_RF_cpu_' + str(flow)); rf.__file__ = str(runtime / RF_PATH)
    vars(rf).update(namespace); rf.__file__ = str(runtime / RF_PATH)
    load('check_full_sampling').load_functions(runtime / RF_PATH, ['denoise'], vars(rf))
    rf.Video2WorldModelRectifiedFlow = types.SimpleNamespace(denoise=rf.denoise)
    original = rf.denoise
    dense_forward = forced_reference(runtime, namespace, 'DD')
    cached_forward = forced_reference(runtime, namespace, 'CC')
    wc.apply_worldcache(base, num_steps=70, ret_ratio=.06, rel_l1_thresh=.08,
        probe_depth=2, osi_enabled=True, flow_enabled=flow, flow_scale=1)
    base.eval()
    shape = (1, 2048, 2, 8, 8)
    noise = torch.linspace(-.8, .9, 2048 * 2 * 8 * 8).reshape(shape)
    latent = noise * .72 + .08
    cls, _ = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, wc.DataType)
    conditions = tuple(cls(crossattn_emb=torch.ones(1, 3, 4) * (1 + s), fps=torch.tensor([16.]),
        use_video_condition=torch.tensor([True]), padding_mask=torch.zeros(1, 1, 8, 8))
        .set_video_condition(noise * .1 + s * .02, 0, 0, num_conditional_frames=1) for s in (0, 1))
    context = ('CPU_SHARED_PREFIX', 'TOY', 'TWO_FROZEN_CONDITIONS')
    def model(net):
        m = types.SimpleNamespace(net=net, tensor_kwargs={'device': 'cpu', 'dtype': torch.float32},
            config=types.SimpleNamespace(conditional_frame_timestep=.15, denoise_replace_gt_frames=True))
        m.denoise = types.MethodType(original, m); return m
    def cache(net):
        return {'cnt': net.cnt, **{n: getattr(net, n) for n in CACHE_FIELDS + WINDOW_FIELDS}}
    def bank():
        cs = [ResidualCalibrator(), ResidualCalibrator()]
        for c in cs: c.reset(context)
        return cs
    def bank_digest(cs):
        return tree_digest([{'receipt': c.receipt(), 'anchors': [vars(a) for a in c.anchors]} for c in cs])
    def reference_A(m, cs, working, step, time):
        proxy = types.SimpleNamespace(model=m, net=m.net, context=context, dense=cs, working=working,
            current={'action': 'C', 'source_choice': types.SimpleNamespace(reason='MATH_REFERENCE:A')})
        readout = SourceFusionReadout(proxy, method='BETA1_ONE_PHASE', gamma=.7235237005554214)
        readout.completed = step - 1
        proxy.prewarp, proxy.hidden, proxy.output = readout.prewarp, readout.semantic_hidden, readout.output
        _, denoise, proof = compile_collection(runtime, wc, rf, proxy)
        readout.warp, readout.to_velocity = proxy.warp, proxy.to_velocity
        executor = NativePolicyPairedExecutor(m, denoise, torch,
            wc_forward=wc.worldcache_mini_train_dit_forward, rf_denoise=original)
        readout.begin(noise, latent, time, conditions)
        ordinary = executor.pair(noise, latent, time, conditions, lambda _: 'CC')
        return readout.end(ordinary, 'CC')
    checks = []
    with torch.no_grad():
        parent = model(base); cs = bank(); last_D = 0
        for step in range(1, 36):
            time = torch.tensor([.94 - .021 * step])
            if step in (12, 23, 29, 30, 35):
                expected_cache = model(copy.deepcopy(parent.net))
                expected_cache.net.forward = types.MethodType(wc.worldcache_mini_train_dit_forward, expected_cache.net)
                working = [{'kind': 'D', 'created_step': last_D, 'context': context} for _ in (0, 1)]
                expected_A = reference_A(expected_cache, copy.deepcopy(cs), copy.deepcopy(working), step, time)
                teacher = model(copy.deepcopy(parent.net)); teacher.net.forward = types.MethodType(dense_forward, teacher.net)
                expected_D = tuple(original(teacher, noise, latent, time, c) for c in conditions)
                for direction in ('Pc', 'Pu'):
                    for coefficient in (0., 1., .83, 8 / 7 if direction == 'Pc' else 7 / 8):
                        test = model(copy.deepcopy(parent.net)); test.net.forward = types.MethodType(wc.worldcache_mini_train_dit_forward, test.net)
                        count_before = [float(b.visits) for b in test.net.blocks]
                        read_cs, read_work = copy.deepcopy(cs), copy.deepcopy(working)
                        bank_sha = bank_digest(read_cs); work_sha = tree_digest(read_work)
                        rng = torch.get_rng_state().clone(); input_sha = tree_digest((noise, latent, time, [vars(c) for c in conditions]))
                        executor = ACRReadoutExecutor(test, runtime=runtime, wc=wc, rf=rf, context=context,
                            dense=read_cs, working=read_work, gamma=.7235237005554214,
                            direction=direction, coefficient=coefficient, step=step)
                        observed, base_A, observed_D = executor.execute(noise, latent, time, conditions)
                        side = 0 if direction == 'Pc' else 1
                        assert all(torch.equal(a, b) for a, b in zip(base_A, expected_A)), 'Shared-prefix A differs'
                        assert torch.equal(observed_D, expected_D[side]), 'Selected post-RF D differs'
                        target = compensate(expected_A, expected_D[side], direction=direction, coefficient=coefficient)
                        assert all(torch.equal(a, b) for a, b in zip(observed, target)), 'Compensation differs'
                        assert tree_digest(cache(test.net)) == tree_digest(cache(expected_cache.net)), 'Working cache not C-compatible'
                        visits = [float(b.visits) - old for b, old in zip(test.net.blocks, count_before)]
                        assert visits == [2., 2., 1., 1.], 'Probe repeated or omitted branch executed deep'
                        assert bank_digest(read_cs) == bank_sha and tree_digest(read_work) == work_sha
                        assert torch.equal(rng, torch.get_rng_state()) and tree_digest((noise, latent, time, [vars(c) for c in conditions])) == input_sha
                        assert executor.last['paid_prefixes'] == 2 and executor.last['actual_dense_branches'] == 1
                        checks.append({'step': step, 'flow': flow, 'direction': direction, 'coefficient': coefficient,
                            'actual_prefix_visit_delta': visits[:2], 'deep_visit_delta': visits[2:],
                            'base_A_and_dense_and_compensation_equal': True, 'C_compatible_cache_equal': True,
                            'past_D_working_RNG_inputs_unchanged': True, 'cycle70_reset': step == 35})
            parent.net.forward = types.MethodType(dense_forward if step <= 24 or step == 31 else cached_forward, parent.net)
            for slot, condition in enumerate(conditions):
                original(parent, noise, latent, time, condition)
                if step <= 24 or step == 31:
                    assert cs[slot].observe_full(context=context, step=step,
                        probe=parent.net.probe_residual_cache[slot], residual=parent.net.residual_cache[slot])
                    last_D = step
    return [{'flow': flow, 'status': 'PASS', 'cases': checks, 'CPU_cases': len(checks),
             'Toy_weights_attention_only': True, 'GPU_submissions': 0}]


def run(runtime):
    runtime = Path(runtime)
    result = load('check_full_sampling').run(runtime, exercise=lambda **kw: exercise(runtime=runtime, **kw))
    assert {r['flow'] for r in result['checks']} == {False, True}
    assert sum(r['CPU_cases'] for r in result['checks']) == 80
    result.update(status='ACR_SHARED_TWO_PREFIX_ONE_DENSE_80_CPU_CASES_PASS_NOT_REAL_MODEL',
                  actual_Cosmos_weights_or_speed_or_quality=False, GPU_submissions=0)
    return result
