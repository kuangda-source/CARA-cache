"""CPU controls execute the same phase function used by the production H1 CLI."""
import ast
from enum import Enum
import hashlib
import importlib.util
from pathlib import Path
import random
import tempfile
import types
from typing import List, Optional, Tuple, Union

import numpy as np
import torch
from einops import rearrange

from wcomr.h0_mode import establish_shared_eval
from wcomr.h1_prefix import run_h1_prefixes


def run(source_path, unipc_path):
    source_path, unipc_path = Path(source_path), Path(unipc_path)
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903'
    assert hashlib.sha256(unipc_path.read_bytes()).hexdigest() == 'f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3'
    tree = ast.parse(source_path.read_text())
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in (
        'compute_optimal_gamma', 'estimate_optical_flow', 'warp_feature',
        'worldcache_mini_train_dit_forward', 'apply_worldcache')]
    spec = importlib.util.spec_from_file_location('h1_actual_unipc', unipc_path)
    unipc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(unipc)

    class DataType(Enum):
        VIDEO = 1

    class Op(torch.nn.Module):
        def forward(self, q, k, v):
            return (q * 1.002).reshape(1, 128, 2048)

    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.self_attn = types.SimpleNamespace(attn_op=Op())
            self.register_buffer('visits', torch.zeros(()))

        def forward(self, x, **kwargs):
            self.visits.add_(1)
            q = x.reshape(1, 128, 16, 128)
            return self.self_attn.attn_op(q, q, q).reshape_as(x) + .002

    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = torch.nn.ModuleList([Block() for _ in range(4)])
            self.use_crossattn_projection = False
            self.use_wan_fp32_strategy = False
            self.t_embedder = lambda t: (t.unsqueeze(-1), None)
            self.t_embedding_norm = lambda t: t
            self.final_layer = lambda x, *args, **kwargs: x
            self.unpatchify = lambda x: x

        def prepare_embedded_sequence(self, x, **kwargs):
            return x, None, None

    class Condition:
        def __init__(self, branch, batch, changed=False):
            self.branch, self.batch = branch, batch
            self.cross = torch.ones(1, 3, 4) * (branch + 1 + .1 * changed)

        def to_dict(self, **kwargs):
            return {'fps': self.batch['fps'], 'cross': self.cross,
                    'branch': self.branch, 'metadata': self.batch['metadata']}

    sample = types.SimpleNamespace(num_steps=35, seed=0)
    config = {'phases': ['baseline_prefix', 'observed_prefix'], 'source_solver_step': 17,
        'reuse_ages': [1, 2, 4], 'stop_after_solver_steps': 21, 'state_steps': [13, 21],
        'warmups': 1, 'repeats': 3, 'dense_fallback_layers': [2], 'policy': {'sim': .1, 'cdf': .98}}
    checks = []
    for flow, failure in ((False, None), (True, None), (True, 'sparse'), (True, 'condition')):
        wc = types.ModuleType('cpu_pinned_wc')
        vars(wc).update(torch=torch, amp=torch.amp, F=torch.nn.functional,
            rearrange=rearrange, DataType=DataType, List=List, Optional=Optional,
            Tuple=Tuple, Union=Union, log=types.SimpleNamespace(info=lambda *args: None))
        exec(compile(tree, str(source_path), 'exec'), vars(wc))
        settings = dict(worldcache_num_steps=35, worldcache_ret_ratio=.2,
            worldcache_rel_l1_thresh=-1, probe_depth=1,
            worldcache_osi_enabled=True, worldcache_flow_enabled=flow, worldcache_flow_scale=1)
        net = wc.apply_worldcache(Toy(), **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
        mode = establish_shared_eval(net)
        scheduler = unipc.FlowUniPCMultistepScheduler(num_train_timesteps=1000,
            shift=1, use_dynamic_shifting=False)
        model = types.SimpleNamespace(net=net, sample_scheduler=scheduler,
            config=types.SimpleNamespace(use_kerras_sigma_at_inference=True))
        def denoise(x, timestep, *, condition):
            return net(x, timestep, condition.cross, fps=condition.batch['fps'])
        model.denoise = denoise
        def prepare(**kwargs):
            return {'video': torch.linspace(.7, 1.3, 128 * 2048).reshape(1, 2, 8, 8, 2048),
                'fps': torch.randint(16, 32, (1,)).float(),
                'metadata': (random.random(), float(np.random.rand()))}
        pipe = types.SimpleNamespace(model=model, _get_data_batch_input=prepare)
        inference = types.SimpleNamespace(pipe=pipe)
        generation_count = 0
        buffer_deltas = []
        def generate(samples, output_dir):
            nonlocal generation_count
            generation_count += 1
            before = [x.clone() for x in net.buffers()]
            # Stand-in for the already separately tested official request reset;
            # the production integration still requires the real reset source.
            net.worldcache_num_steps = 2 * samples[0].num_steps
            scheduler.set_timesteps(35, device='cpu', shift=5, use_kerras_sigma=True)
            batch = pipe._get_data_batch_input(prompt='same', negative_prompt='same-negative')
            generator = torch.Generator().manual_seed(samples[0].seed)
            x = batch['video'].clone()
            try:
                for index, timestep in enumerate(scheduler.timesteps):
                    velocities = []
                    x = x + torch.rand(x.shape, generator=generator) * .00001
                    for branch in (0, 1):
                        changed = generation_count == 2 and failure == 'condition' and index == 17 and branch == 0
                        condition = Condition(branch, batch, changed)
                        velocities.append(model.denoise(x, timestep.reshape(1), condition=condition))
                    x = scheduler.step((velocities[0] + velocities[1]) / 2,
                        timestep, x, return_dict=False, generator=generator)[0]
            finally:
                buffer_deltas.append([float((a - b).item()) for a, b in zip(net.buffers(), before)])
        inference.generate = generate
        def kernel(q, k, v, mask, sim, cdf, full):
            value = (q * 1.002 * (.999 if full else .99)).reshape(1, 128, 2048)
            if failure == 'sparse' and not full:
                value = value * float('nan')
            return value, {'selected_fraction': .7}
        state = {'phases': [], 'planned_source_denominator': 6,
                 'planned_lifetime_denominator': 18, 'planned_raw_files': 30}
        original_forward, original_denoise = net.forward, model.denoise
        original_step, original_wc = scheduler.step, wc.worldcache_mini_train_dit_forward
        with tempfile.TemporaryDirectory(prefix='h1-prefix-cpu-') as directory:
            caught = None
            try:
                run_h1_prefixes(inference, sample, wc, settings, config, state=state,
                    save=lambda: None, output=Path(directory), context=('CPU', 'toy', 'condition'),
                    mode_setup=mode, kernel=kernel)
            except ValueError as error:
                caught = str(error)
            assert net.forward == original_forward and model.denoise == original_denoise
            assert scheduler.step == original_step and wc.worldcache_mini_train_dit_forward == original_wc
            assert pipe._get_data_batch_input is prepare
            assert not getattr(net, '_w1_shadow_active', False)
            assert state['planned_source_denominator'] == 6 and state['planned_lifetime_denominator'] == 18
            if failure:
                assert caught and ('nonfinite/undefined' in caught if failure == 'sparse' else 'conditioning changed' in caught)
                assert not state['h1_records']
                assert len(state['h1_source_attempts']) == (1 if failure == 'sparse' else 2)
                checks.append({'failure': failure, 'full_denominators_preserved': True,
                    'all_hooks_restored': True, 'no_future_truth_or_reselection': True})
                continue
            assert caught is None, caught
            assert all(state['all_gate_checks'].values()) and len(state['all_gate_checks']) == 9
            assert state['h1_coverage']['future_source_age_cells'] == 18
            assert buffer_deltas[0] == buffer_deltas[1] == [42.0] * 4
            assert [x['source'] for x in state['prepared_input_calls']] == [
                'OFFICIAL_PREPARE_ONCE', 'SHARED_OFFICIAL_PREPARED_BATCH']
            assert [r['solver_step'] for r in state['phases'][1]['roundtrips']] == [13, 21]
            assert [r['call'] for r in state['phases'][1]['roundtrips']] == [26, 42]
            assert all(r['shadow_D_matches_deployed_full'] for r in state['h1_records'])
            assert len(list(Path(directory).glob('raw-h1/*/*.pt'))) == 30
            fields = [len(r['components']) for r in state['phases'][1]['field_signatures']]
            checks.append({'flow': flow, 'actual_unipc_grid': len(scheduler.timesteps),
                'prefix_updates': [p['solver_steps'] for p in state['phases']],
                'cfg_calls': [p['actual_cfg_calls_entered'] for p in state['phases']],
                'nine_gate_checks': state['all_gate_checks'], 'state_steps': [13, 21],
                'state_component_counts': fields, 'paired_lifetime_cells': 18,
                'shared_prepare_RNG_and_buffer_delta_exact': True,
                'all_hooks_restored': True, 'raw_files': 30})
    assert not torch.cuda.is_initialized()
    return {'status': 'H1_PRODUCTION_PREFIX_CORE_CPU_CONTROLS_PASS_NOT_REAL_MODEL_RESULT',
        'checks': checks, 'cuda_initialized': False,
        'limits': 'Actual pinned WC functions and UniPC with Toy modules, synthetic kernel and stand-in Inference/prepare/reset; no GPU, real model, full video or independent fork.'}
