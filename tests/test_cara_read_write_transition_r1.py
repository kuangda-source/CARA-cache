"""Pinned WC/RF arithmetic with declared tiny CPU modules and conditions.

These controls exercise the real cache recurrence/warp, not Cosmos weights or
the eventual video terminal loss. RF intentionally returns FP32, so directional
differences use a finite, stated tolerance rather than claiming double parity.
"""
import ast
import copy
from enum import Enum
import os
from pathlib import Path
import types
import unittest

from einops import rearrange
import torch

from wcomr.cara_read_write_transition_r1 import FunctionalWorldCache, WorldCacheMemory
from wcomr.cfg_paired_probe_forward import RF_PATH, WC_PATH, forced_reference
from wcomr.mid_coverage import tree_digest, WC_FIELDS


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('CARA_READ_WRITE_RUNTIME', ROOT/'.sync/read-write-pinned-runtime-r1'))
METRICS = {}


class DataType(str, Enum):
    VIDEO = 'video'
    IMAGE = 'image'


def pinned_functions(path, names, scope):
    nodes = [node for node in ast.walk(ast.parse(path.read_bytes()))
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert sorted(node.name for node in nodes) == sorted(names)
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future]+nodes, type_ignores=[]))
    exec(compile(module, str(path), 'exec'), scope)


def modules():
    wc = types.ModuleType('read_write_WC_CPU_namespace')
    wc.__file__ = str(RUNTIME/WC_PATH)
    vars(wc).update(torch=torch, rearrange=rearrange, F=torch.nn.functional,
        amp=torch.amp, DataType=DataType, log=types.SimpleNamespace(info=lambda *a: None))
    pinned_functions(RUNTIME/WC_PATH, ['estimate_optical_flow', 'warp_feature',
        'compute_saliency_map', 'compute_optimal_gamma',
        'worldcache_mini_train_dit_forward', 'apply_worldcache'], vars(wc))
    rf = types.ModuleType('read_write_RF_CPU_namespace')
    rf.__file__ = str(RUNTIME/RF_PATH)
    rf.torch = torch
    pinned_functions(RUNTIME/RF_PATH, ['denoise'], vars(rf))
    rf.Video2WorldModelRectifiedFlow = types.SimpleNamespace(denoise=rf.denoise)
    return wc, rf


class Block(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.gain = torch.nn.Parameter(torch.tensor(.04, dtype=torch.float64), requires_grad=False)

    def forward(self, value, **kwargs):
        return value+self.gain*value.tanh()+.003*kwargs['crossattn_emb'].mean()


class Head(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.register_buffer('visits', torch.zeros((), dtype=torch.float64))

    def forward(self, value, *args, **kwargs):
        self.visits.add_(1)
        return value+.017*value.sin()


class TinyNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks = torch.nn.ModuleList([Block() for _ in range(4)])
        self.final_layer = Head()
        self.use_crossattn_projection = False
        self.use_wan_fp32_strategy = False
        self.t_embedder = lambda t: (t.unsqueeze(-1), None)
        self.t_embedding_norm = lambda t: t

    def prepare_embedded_sequence(self, value, **kwargs):
        return value[:, :8].movedim(1, -1).contiguous(), None, None

    def unpatchify(self, value):
        return value.movedim(-1, 1).contiguous()


class Condition:
    is_video = True
    use_video_condition = True

    def __init__(self, branch):
        self.gt_frames = torch.zeros(1, 8, 2, 4, 4, dtype=torch.float64)
        self.condition_video_input_mask_B_C_T_H_W = torch.zeros(1, 1, 2, 4, 4, dtype=torch.float64)
        self.cross = torch.ones(1, 2, 3, dtype=torch.float64)*(1+branch)

    def to_dict(self):
        return dict(crossattn_emb=self.cross, data_type=DataType.VIDEO, fps=torch.tensor([24.]),
            condition_video_input_mask_B_C_T_H_W=self.condition_video_input_mask_B_C_T_H_W)


def fixture(flow=True):
    wc, rf = modules()
    net = TinyNet().eval()
    wc.apply_worldcache(net, num_steps=70, ret_ratio=.06, probe_depth=2,
        osi_enabled=True, flow_enabled=flow, flow_scale=1,
        saliency_enabled=True, dynamic_decay=True)
    model = types.SimpleNamespace(net=net, tensor_kwargs=dict(device='cpu', dtype=torch.float64),
        config=types.SimpleNamespace(conditional_frame_timestep=.15, denoise_replace_gt_frames=True))
    conditions = tuple(Condition(branch) for branch in (0, 1))
    noise = torch.linspace(-.4, .7, 256, dtype=torch.float64).reshape(1, 8, 2, 4, 4)
    return model, wc, rf, conditions, noise


def parent(adapter, net, conditions, noise):
    memory = WorldCacheMemory.capture(net)
    with torch.no_grad():
        for step in range(7):
            _, memory = adapter.pair(memory, noise, noise*(1+.02*step)+.01*step,
                torch.tensor([[.9-.02*step]], dtype=torch.float64), conditions, action='D')
    return memory


class FunctionalTransition(unittest.TestCase):
    def test_full36_hard_forward_cache_and_buffer_match_source_order(self):
        from wcomr.cara_fast_spec_r1 import uniform_mask, profile_from
        import json
        card = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
        mask, _ = uniform_mask(card['schedule'], profile_from(card['profile']), 19)
        for flow in (False, True):
            model, wc, rf, conditions, noise = fixture(flow)
            adapter = FunctionalWorldCache(model, runtime=RUNTIME, wc=wc, rf=rf)
            reference = copy.deepcopy(model)
            functions = {action: forced_reference(RUNTIME, vars(wc), action*2) for action in ('C', 'D')}
            memory = WorldCacheMemory.capture(model.net)
            caller_before = tree_digest(memory.fields)
            with torch.no_grad():
                for step in range(1, 37):
                    action = 'D' if step in mask else 'C'
                    value = noise*(1+.002*step)+.001*step
                    timestep = torch.tensor([[.9-.02*step]], dtype=torch.float64)
                    before = tree_digest(dict(cache=memory.fields, buffers=memory.buffers))
                    observed, after = adapter.pair(memory, noise, value, timestep, conditions, action=action)
                    self.assertEqual(tree_digest(dict(cache=memory.fields, buffers=memory.buffers)), before)
                    reference.net.forward = types.MethodType(functions[action], reference.net)
                    branches = tuple(rf.Video2WorldModelRectifiedFlow.denoise(
                        reference, noise, value, timestep, c) for c in conditions)
                    expected = branches[0]+7*(branches[0]-branches[1])
                    self.assertTrue(torch.equal(observed, expected), (flow, step))
                    original = {name:getattr(reference.net, name) for name in WC_FIELDS if hasattr(reference.net, name)}
                    self.assertEqual(tree_digest(after.fields), tree_digest(original), (flow, step))
                    self.assertEqual(tree_digest(after.buffers), tree_digest(dict(reference.net.named_buffers())))
                    memory = after
            self.assertEqual(int(memory.fields['cnt']), 2)
            self.assertEqual(float(memory.buffers['final_layer.visits']), 72.)
            self.assertEqual(float(model.net.final_layer.visits), 0.)
            self.assertEqual(tree_digest(WorldCacheMemory.capture(model.net).fields), caller_before)
            METRICS['flow_'+str(flow)+'_full36'] = dict(exact_outputs=True, exact_complete_WC_state=True,
                exact_buffers=True, caller_and_each_input_state_unchanged=True,
                original70_call_cycle_reset_covered=True, total_branches=72)

    def test_C_transition_retains_input_and_cache_VJP_with_source_flow(self):
        model, wc, rf, conditions, noise = fixture(True)
        adapter = FunctionalWorldCache(model, runtime=RUNTIME, wc=wc, rf=rf)
        memory = parent(adapter, model.net, conditions, noise)
        value = noise*1.14+.07
        cached = memory.fields['residual_window'][0][-1]
        leaves = [value.detach().requires_grad_(), cached.detach().requires_grad_()]
        directions = [.02+.01*torch.sin(torch.arange(v.numel(), dtype=v.dtype)).reshape_as(v) for v in leaves]

        def evaluate(parts):
            def substitute(v):
                if v is cached:
                    return parts[1]
                if isinstance(v, dict):
                    return {k:substitute(x) for k,x in v.items()}
                if isinstance(v, list):
                    return [substitute(x) for x in v]
                return v
            state = WorldCacheMemory(substitute(memory.fields), memory.buffers)
            output, state = adapter.pair(state, noise, parts[0], torch.tensor([[.76]]), conditions, action='C')
            # A future C reads both the cache and the working state written by C.
            output, state = adapter.pair(state, noise, .9*parts[0]+.03*output,
                torch.tensor([[.74]]), conditions, action='C')
            return output.square().mean()+.03*state.fields['previous_internal_states'][0].square().mean()

        gradients = torch.autograd.grad(evaluate(leaves), leaves)
        records = []
        for index, (gradient, direction) in enumerate(zip(gradients, directions)):
            epsilon = .01
            high, low = [v.detach() for v in leaves], [v.detach() for v in leaves]
            high[index] = high[index]+epsilon*direction
            low[index] = low[index]-epsilon*direction
            predicted = float((gradient*direction).sum())
            numerical = float((evaluate(high)-evaluate(low))/(2*epsilon))
            self.assertAlmostEqual(predicted, numerical, delta=4e-6)
            self.assertGreater(abs(predicted), 1e-4)
            records.append(dict(group=('current_input', 'cached_residual')[index], predicted=predicted,
                central_FD=numerical, absolute_error=abs(predicted-numerical), epsilon=epsilon, tolerance=4e-6))
        METRICS['actual_C_cache_and_flow_RF_tiny_VJP'] = records

    def test_C_updates_working_state_and_graph_is_not_detached(self):
        model, wc, rf, conditions, noise = fixture(True)
        adapter = FunctionalWorldCache(model, runtime=RUNTIME, wc=wc, rf=rf)
        memory = parent(adapter, model.net, conditions, noise)
        latent = (noise*1.14+.07).requires_grad_()
        _, after = adapter.pair(memory, noise, latent, torch.tensor([[.76]]), conditions, action='C')
        self.assertFalse(torch.equal(memory.fields['previous_input'][0], after.fields['previous_input'][0]))
        derivative = torch.autograd.grad(after.fields['previous_internal_states'][0].square().mean(), latent)[0]
        self.assertGreater(float(derivative.abs().sum()), 0)
        self.assertEqual(tree_digest(after.fields['residual_window']), tree_digest(memory.fields['residual_window']))
        METRICS['C_working_state_is_nonidentity_and_differentiable'] = True

    def test_full36_WC_RF_UniPC_graph_direction_matches_finite_difference(self):
        import importlib.util
        from wcomr.cara_read_write_state_r1 import FunctionalUniPC, UniPCMemory
        from wcomr.cara_fast_spec_r1 import profile_from, uniform_mask
        import json
        spec = importlib.util.spec_from_file_location('read_write_transition_original_UniPC',
            RUNTIME/'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')
        original = importlib.util.module_from_spec(spec)
        import sys
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

        def evaluate(initial):
            value = initial
            cache = WorldCacheMemory.capture(model.net)
            memory = UniPCMemory.capture(scheduler)
            for step, timestep in enumerate(scheduler.timesteps, 1):
                velocity, cache = adapter.pair(cache, noise, value, timestep.reshape(1, 1), conditions,
                    action='D' if step in mask else 'C')
                value, memory = solver.step(memory, velocity, timestep, value)
            return (value-.2*noise).square().mean()

        initial = noise.clone().requires_grad_()
        direction = .02+.01*noise.sin()
        gradient = torch.autograd.grad(evaluate(initial), initial)[0]
        predicted = float((gradient*direction).sum())
        epsilon = .01
        with torch.no_grad():
            numerical = float((evaluate(initial+epsilon*direction)-evaluate(initial-epsilon*direction))/(2*epsilon))
        self.assertAlmostEqual(predicted, numerical, delta=4e-6)
        self.assertGreater(abs(predicted), 1e-5)
        METRICS['full36_pinned_WC_RF_UniPC_tiny_graph'] = dict(predicted=predicted,
            central_FD=numerical, absolute_error=abs(predicted-numerical), epsilon=epsilon,
            tolerance=4e-6, actual_Cosmos_weights=False, terminal_loss='declared_synthetic_latent_MSE')

    def test_unready_C_trainable_weights_eval_change_and_inference_mode_refused(self):
        model, wc, rf, conditions, noise = fixture()
        adapter = FunctionalWorldCache(model, runtime=RUNTIME, wc=wc, rf=rf)
        memory = WorldCacheMemory.capture(model.net)
        with self.assertRaisesRegex(ValueError, 'warmup'):
            adapter.pair(memory, noise, noise, torch.tensor([[.9]]), conditions, action='C')
        next(model.net.parameters()).requires_grad_()
        with self.assertRaisesRegex(ValueError, 'Frozen eval'):
            FunctionalWorldCache(model, runtime=RUNTIME, wc=wc, rf=rf)
        next(model.net.parameters()).requires_grad_(False)
        model.net.train()
        with self.assertRaisesRegex(ValueError, 'changed from frozen eval'):
            adapter.pair(memory, noise, noise, torch.tensor([[.9]]), conditions, action='D')
        model.net.eval()
        with torch.inference_mode(), self.assertRaisesRegex(ValueError, 'Inference tensors'):
            adapter.pair(memory, noise, noise, torch.tensor([[.9]]), conditions, action='D')


if __name__ == '__main__':
    unittest.main()
