"""Full pinned sampler/pipeline CPU integration with explicit stand-in boundaries."""
import ast
from enum import Enum
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import types
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from einops import rearrange

import wcomr.full_sampling as full
from wcomr.h0_mode import establish_shared_eval
from wcomr.refresh_deployment import SimpleRefreshAdapter
from wcomr.stage_witness import witness

HASHES = {
    'cosmos_predict2/inference.py': '0db96c49f0b3f18a971bc989e0727132dafc27ef621145a2d25a3da62a7a1975',
    'cosmos_predict2/_src/predict2/inference/video2world.py': '59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95',
    'cosmos_predict2/_src/predict2/inference/worldcache_utils.py': 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903',
    'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py': 'c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87',
    'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py': 'f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3',
}


def load_functions(path, names, namespace):
    """Extract unchanged function bodies; defer original type annotations only."""
    tree = ast.parse(path.read_text())
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    assert sorted(node.name for node in functions) == sorted(names)
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    module = ast.Module(body=[future] + functions, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), 'exec'), namespace)


def run(runtime, refresh=False):
    runtime = Path(runtime)
    for path, digest in HASHES.items():
        assert hashlib.sha256((runtime / path).read_bytes()).hexdigest() == digest, path
    assert not torch.cuda.is_initialized()

    class DataType(str, Enum):
        VIDEO = 'video'
        IMAGE = 'image'

    quiet = types.SimpleNamespace(**{k: lambda *a, **kw: None for k in
        ['info', 'debug', 'warning', 'success', 'critical']})
    common = dict(torch=torch, np=np, rearrange=rearrange, amp=torch.amp,
                  F=torch.nn.functional, DataType=DataType, log=quiet,
                  Dict=Dict, List=List, Tuple=Tuple, Union=Union,
                  Optional=Optional, Callable=Callable)
    wc = types.ModuleType('cpu_full_pinned_wc')
    vars(wc).update(common)
    load_functions(runtime / 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py',
        ['compute_optimal_gamma', 'estimate_optical_flow', 'warp_feature',
         'worldcache_mini_train_dit_forward', 'apply_worldcache'], vars(wc))
    sampler_ns = dict(common, INTERNAL=True,
        parallel_state=types.SimpleNamespace(is_initialized=lambda: False),
        misc=types.SimpleNamespace(arch_invariant_rand=lambda shape, dtype, device, seed:
            torch.randn(shape, dtype=dtype, device=device,
                        generator=torch.Generator(device=device).manual_seed(seed))))
    load_functions(runtime / 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py',
        ['generate_samples_from_batch', 'get_velocity_fn_from_batch', 'denoise', 'decode'], sampler_ns)
    pipe_ns = dict(common, _DEFAULT_NEGATIVE_PROMPT='negative')
    load_functions(runtime / 'cosmos_predict2/_src/predict2/inference/video2world.py',
                   ['generate_vid2world'], pipe_ns)
    inference_module = types.ModuleType('cpu_full_pinned_inference')
    vars(inference_module).update(common, SMOKE=False,
        path_to_str=lambda v: str(v) if v is not None else None,
        guardrail_presets=types.SimpleNamespace(run_text_guardrail=lambda *a: True,
            run_video_guardrail=lambda frames, runner: frames.copy()))
    load_functions(runtime / 'cosmos_predict2/inference.py',
                   ['generate', '_generate_sample'], vars(inference_module))
    spec = importlib.util.spec_from_file_location('cpu_full_unipc',
        runtime / 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py')
    unipc = importlib.util.module_from_spec(spec); spec.loader.exec_module(unipc)

    class Attention(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.gain = torch.nn.Parameter(torch.tensor(1.002), requires_grad=False)

        def forward(self, q, k, v):
            return (q * self.gain).reshape(1, 128, 2048)

    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.attention = Attention()
            self.self_attn = types.SimpleNamespace(attn_op=self.attention)
            self.register_buffer('visits', torch.zeros(()))

        def forward(self, x, **kwargs):
            self.visits.add_(1)
            q = x.reshape(1, 128, 16, 128)
            return self.self_attn.attn_op(q, q, q).reshape_as(x) + kwargs['crossattn_emb'].mean() * .002

    class ToyNet(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = torch.nn.ModuleList([Block() for _ in range(4)])
            self.use_crossattn_projection = False
            self.use_wan_fp32_strategy = False
            self.is_context_parallel_enabled = False
            self.t_embedder = lambda t: (t.unsqueeze(-1), None)
            self.t_embedding_norm = lambda t: t
            self.final_layer = lambda x, *a, **kw: x
            self.unpatchify = lambda x: x.movedim(-1, 1).contiguous()

        def prepare_embedded_sequence(self, x, **kwargs):
            if failure == 'solver_tail' and model.generation == 4 and scheduler._step_index == 35:
                raise ValueError('CPU injected failure at final sampler tail')
            step = self.cnt // 2 + 1
            full_steps = set(range(1, 8)) | {12, 21, 26, 33, 34, 35}
            self.worldcache_rel_l1_thresh = -1 if step in full_steps else 1e6
            if model.generation == 4 and step == 12:
                if failure == 'refresh_context': self._wc_refresh_adapter.ledger.context = ('other', 'toy', 'condition:human')
                if failure == 'refresh_model': self._wc_refresh_adapter.net = object()
                if failure == 'refresh_group': self._wc_refresh_adapter.ledger.group = (2, 4)
                if failure == 'refresh_window': self.residual_window[0][-1] = self.residual_window[0][-1].clone()
                if failure == 'refresh_insufficient': self._wc_refresh_adapter.ledger.true_dense_history[self.cnt % 2] = []
                if failure == 'refresh_nonfinite':
                    x = x.clone(); x.flatten()[0] = float('nan')
            return x.movedim(1, -1).contiguous(), None, None

    class Condition:
        def __init__(self, branch, batch):
            self.branch, self.batch = branch, batch
            self.cross = torch.ones(1, 3, 4) * (1 + branch + .1 * (batch['prompt'] == 'human'))
            self.data_type = DataType.VIDEO

        def edit_data_type(self, kind):
            self.data_type = kind
            return self

        def to_dict(self, **kwargs):
            if failure == 'refresh_condition' and model.generation == 4 and scheduler._step_index == 11:
                return {'crossattn_emb': self.cross + .01, 'fps': self.batch['fps'], 'data_type': self.data_type}
            return {'crossattn_emb': self.cross, 'fps': self.batch['fps'], 'data_type': self.data_type}

    class Sample:
        num_steps, seed, guidance, num_output_frames, num_input_frames = 35, 0, 7, 93, 0
        input_path, negative_prompt, resolution, enable_autoregressive = None, 'negative', '16,16', False

        def __init__(self, name):
            self.name = self.prompt = name

        def model_dump_json(self):
            return json.dumps({'name': self.name, 'frames': self.num_output_frames})

    original_snapshot = full.CompleteStateRoundtrip

    class CorruptThenRestore(original_snapshot):
        def __init__(self, *args, **kwargs):
            self.live_output = args[2]
            super().__init__(*args, **kwargs)

        def restore(self):
            self.live_output.add_(.25)
            self.net.cnt = -100
            self.scheduler._step_index = 100
            for value in self.net.buffers(): value.add_(100)
            for module in self.net.modules(): module.training = True
            random.random(); np.random.rand(); torch.rand(3)
            for generator, _ in self.generators: torch.rand(3, generator=generator)
            adapter = getattr(self.net, '_wc_refresh_adapter', None)
            if adapter:
                adapter.ledger.call = -10
                adapter.ledger.windows = [[], []]
                adapter.ledger.true_dense_history = [[], []]
            return super().restore()

    checks = []
    scenarios = [(False, None), (True, None), (True, 'corrupt_restore')]
    scenarios += [(True, f) for f in ['solver_tail', 'decode', 'writer', 'output_corruption', 'rng_after_decode']]
    if refresh:
        scenarios = [(flow, f) for flow in (False, True) for f in ('refresh_dense', 'refresh_sparse')]
        scenarios += [(True, f) for f in ['refresh_corrupt_restore', 'refresh_insufficient',
            'refresh_context', 'refresh_model', 'refresh_group', 'refresh_condition',
            'refresh_window', 'refresh_nonfinite', 'refresh_kernel_nan']]
    telemetry = {name: getattr(torch.cuda, name) for name in
                 ['is_available', 'memory_allocated', 'reset_peak_memory_stats']}
    # Exact pipe body is kept. Its CUDA-only telemetry is a declared CPU adapter;
    # actual allocation, movement and lazy initialization remain forbidden.
    torch.cuda.is_available = lambda: False
    torch.cuda.memory_allocated = lambda **kwargs: 0
    torch.cuda.reset_peak_memory_stats = lambda *a, **kw: None
    try:
        for flow, failure in scenarios:
            net = ToyNet()
            settings = dict(worldcache_num_steps=35, worldcache_ret_ratio=.2,
                worldcache_rel_l1_thresh=.08, probe_depth=1,
                worldcache_osi_enabled=True, worldcache_flow_enabled=flow, worldcache_flow_scale=1)
            wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
            mode = establish_shared_eval(net)
            scheduler = unipc.FlowUniPCMultistepScheduler(num_train_timesteps=1000,
                shift=1, use_dynamic_shifting=False)
            model = types.SimpleNamespace(net=net, sample_scheduler=scheduler, generation=0,
                tensor_kwargs={'device': 'cpu', 'dtype': torch.float32},
                input_data_key='video', input_image_key='images', text_encoder=None,
                config=types.SimpleNamespace(use_lora=False, use_kerras_sigma_at_inference=True,
                    state_ch=2048, state_t=2))

            def normalize(batch):
                model.generation += 1

            def decode(latent):
                if model.generation == 4 and failure == 'decode':
                    raise ValueError('CPU injected decoder failure')
                base = latent.mean().tanh().reshape(1, 1, 1, 1, 1)
                video = (base + torch.linspace(-.1, .1, 93).reshape(1, 1, 93, 1, 1)).expand(1, 3, 93, 16, 16).clone()
                if model.generation == 4 and failure == 'output_corruption': video += .05
                if model.generation == 4 and failure == 'rng_after_decode': torch.rand(1)
                return video

            model.tokenizer = types.SimpleNamespace(spatial_compression_factor=2,
                get_latent_num_frames=lambda t: 2, get_pixel_num_frames=lambda t: 93, decode=decode)
            model._normalize_video_databatch_inplace = normalize
            model._augment_image_dim_inplace = lambda batch: None
            model.is_image_batch = lambda batch: False
            model.get_data_and_condition = lambda batch: (None, batch['video'], None)
            model.conditioner = types.SimpleNamespace(get_condition_with_negative_prompt=lambda batch:
                (Condition(0, batch), Condition(1, batch)))
            model.broadcast_split_for_model_parallelsim = lambda x, c, e, s: (x, c, e, s)
            for name in ['generate_samples_from_batch', 'get_velocity_fn_from_batch', 'denoise', 'decode']:
                setattr(model, name, types.MethodType(sampler_ns[name], model))

            def prepare(video, prompt, **kwargs):
                return {'video': video, 'prompt': prompt, 'fps': torch.randint(16, 32, (1,)).float(),
                        'metadata': (random.random(), float(np.random.rand()))}

            pipe = types.SimpleNamespace(model=model, _get_data_batch_input=prepare,
                offload_diffusion_model=False, offload_text_encoder=False,
                offload_tokenizer=False, worldcache_enabled=True)
            pipe.generate_vid2world = types.MethodType(pipe_ns['generate_vid2world'], pipe)
            inference = types.SimpleNamespace(pipe=pipe, rank0=True, setup_args=types.SimpleNamespace(keep_going=False),
                text_guardrail_runner=object(), video_guardrail_runner=object())
            for name in ['generate', '_generate_sample']:
                setattr(inference, name, types.MethodType(getattr(inference_module, name), inference))

            def write(video, path, fps):
                if failure == 'writer' and model.generation == 4: return
                Path(path + '.mp4').write_text(json.dumps({'CPU_MOCK_WRITER_NOT_VIDEO': True,
                    'value': witness(video), 'fps': fps}, sort_keys=True))
            inference_module.save_img_or_video = write
            config = {'run_id': 'CPU', 'sample_names': ['common', 'human'],
                      'phases': ['baseline_full', 'restored_full'], 'state_steps': full.STATE_STEPS}
            candidate = refresh and failure != 'refresh_dense'
            if candidate: config['comparison_kind'] = 'closed_loop_interface'
            def kernel(q, k, v, mask, sim, cdf, force_full):
                assert sim == .1 and cdf == .98 and not force_full
                assert mask.shape == (1, 16, 1, 2) and mask.dtype == torch.bool
                # Controlled stand-in deliberately changes the returned latent.
                # This is interface evidence, not a CPU sparse-attention kernel.
                result = (q * 1.001).reshape(1, 128, 2048)
                if failure == 'refresh_kernel_nan' and model.generation == 4:
                    result = result.clone(); result.flatten()[0] = float('nan')
                return result, {'selected_fraction': .5, 'executed_fraction': .5,
                                'CPU_STAND_IN_NOT_SPARSE_KERNEL': True}
            def adapter_factory(phase, context):
                return SimpleRefreshAdapter(context, sparse=candidate and phase == 'restored_full',
                                            fallback_layers=(2,), kernel=kernel)
            state = {}
            originals = (net.forward, model.denoise, scheduler.step, model.generate_samples_from_batch,
                         model.decode, inference_module.save_img_or_video, pipe._get_data_batch_input)
            full.CompleteStateRoundtrip = CorruptThenRestore if failure in ('corrupt_restore', 'refresh_corrupt_restore') else original_snapshot
            caught = None
            with tempfile.TemporaryDirectory(prefix='full-sampling-cpu-') as directory:
                try:
                    full.run_full_sampling_batch(inference, [Sample('common'), Sample('human')], wc,
                        settings, config, state=state, save=lambda: None, output=Path(directory),
                        inference_module=inference_module,
                        contexts=[('CPU:' + n, 'toy', 'condition:' + n) for n in ['common', 'human']], mode_setup=mode,
                        adapter_factory=adapter_factory if refresh else None)
                except ValueError as error:
                    caught = str(error)
                assert originals == (net.forward, model.denoise, scheduler.step, model.generate_samples_from_batch,
                         model.decode, inference_module.save_img_or_video, pipe._get_data_batch_input)
                assert all(float(b) == 0 for b in net.buffers())
                assert not any(m.training for m in net.modules())
                assert not hasattr(net, '_wc_refresh_adapter')
                assert state['planned_requests'] == 2 and state['planned_phases'] == 4
                assert state['planned_cfg_calls_per_phase'] == 72
                first, second = state['requests']
                expected_status = ('FULL36_CFG72_CLOSED_LOOP_INTERFACE_PASS_NOT_QUALITY' if candidate
                                   else 'FULL36_CFG72_DD_FINAL_PIPELINE_CONTROL_PASS')
                assert first['status'] == expected_status
                fail_control = failure and failure not in ('corrupt_restore', 'refresh_dense',
                    'refresh_sparse', 'refresh_corrupt_restore', 'refresh_insufficient')
                if fail_control:
                    assert caught and second['status'] == 'TECH_BLOCKED'
                    checks.append({'flow': flow, 'failure': failure, 'error': caught,
                        'planned_phases': 4, 'denominators_preserved': True,
                        'first_request_complete_preserved': True, 'second_phase_updates':
                        [p['solver_steps'] for p in second['phases']], 'all_hooks_and_decode_flags_restored': True})
                    continue
                assert caught is None, caught
                for request in state['requests']:
                    assert len(request['all_gate_checks']) == 9
                    assert all(request['shared_contract_checks'].values())
                    if not candidate:
                        assert all(request['all_gate_checks'].values())
                        assert all(request['pipeline_checks'].values())
                    for phase in request['phases']:
                        assert phase['solver_steps'] == 36 and phase['actual_cfg_calls_entered'] == 72
                        assert [p['cache_counter_before'] for p in phase['trace']][-4:] == [68, 69, 0, 1]
                        assert [p['stage'] for p in phase['pipeline_events']] == [
                            'sample_return', 'decode_input', 'decode_output', 'guardrail_input', 'guardrail_output', 'save_input']
                        assert phase['pipeline_events'][2]['value']['shape'] == [1, 3, 93, 16, 16]
                    restored = request['phases'][1]
                    provenance_control = {}
                    if refresh:
                        report = restored['refresh_provenance']
                        events = report['events']
                        sparse_rows = [row for row in events if row.get('source', {}).get('kind') == 'sparse']
                        assert len(events) == 72 and report['epoch'] == 1
                        assert events[69]['native_cycle_reset'] and not events[70]['references_read'] and not events[71]['references_read']
                        assert all(e['action'] == 'dense' for e in events[:14] + events[70:])
                        assert all(v['kind'] == 'dense' for w in report['true_dense_history'] for v in w)
                        if candidate:
                            assert sparse_rows
                            assert all(not e['inserted_into_true_dense_history'] and e['paid_probe']
                                and e['two_past_true_dense'] and not e['official_skipped']
                                and e['sparse_layers'] == [1, 3] for e in sparse_rows)
                            assert not request['all_gate_checks']['output_hashes']
                            assert not request['pipeline_checks']['pipeline_events']
                            assert request['phases'][0]['pipeline_events'][0]['value'] != restored['pipeline_events'][0]['value']
                            reads_s = [e for e in events if e['official_skipped'] and
                                any(v['kind'] == 'sparse' for v in e['references_read'])]
                            assert reads_s
                        else: assert not sparse_rows
                        if failure == 'refresh_insufficient' and request['sample_name'] == 'human':
                            assert all(e['action'] == 'dense' and not e['two_past_true_dense'] for e in events[22:24])
                        provenance_control = {'sparse_refresh_calls': len(sparse_rows),
                            'cache_hit_reads_approximate_forecast': bool(candidate),
                            'fallback_layer_2_never_sparse': True, 'warm_and_final_dense': True,
                            'native70_reset_invalidates_both_cfg_histories': True,
                            'sparse_never_true_dense': True, 'ledger_restored_and_rebound': True,
                            'approximate_closure_changes_actual_final_latent': bool(candidate)}
                    assert [p['solver_step'] for p in restored['roundtrips']] == full.STATE_STEPS
                    checks.append({'flow': flow, 'request': request['sample_name'], 'control': failure or 'ordinary',
                        'full_updates': [p['solver_steps'] for p in request['phases']],
                        'cfg_calls': [p['actual_cfg_calls_entered'] for p in request['phases']],
                        'nine_gates': request['all_gate_checks'], 'pipeline_gates': request['pipeline_checks'],
                        'checkpoints': full.STATE_STEPS,
                        'component_counts': [len(p['components']) for p in restored['field_signatures']],
                        'actual_restored_latent_continues_to_final': True,
                        'official70_reset_final_counters': [68, 69, 0, 1],
                        'mock_decode_and_writer_full93_interface': True,
                        'all_hooks_buffers_modes_decode_flags_restored': True})
                    checks[-1]['refresh_controls'] = provenance_control
    finally:
        full.CompleteStateRoundtrip = original_snapshot
        for name, method in telemetry.items(): setattr(torch.cuda, name, method)
    assert not torch.cuda.is_initialized()
    return {'status': ('FULL36_CFG72_PINNED_SPARSE_REFRESH_INTERFACE_CPU_PASS' if refresh
                      else 'FULL36_CFG72_PINNED_OFFICIAL_SAMPLER_PIPELINE_CPU_CONTROL_PASS'),
        'checks': checks, 'upstream_sha256': HASHES, 'cuda_initialized': False,
        'limits': 'Unchanged pinned sampler/get_velocity/denoise/decode wrapper, WC, UniPC, '
                  'generate_vid2world and Inference method bodies. Explicit Toy net, CPU '
                  'noise/conditioner/normalize/broadcast/prepare/tokenizer/mock writer, '
                  'offload disabled and CUDA telemetry adapters; equal finite threshold '
                  'schedule is CPU control only. No weights, true VAE/encoded video, '
                  'GPU completion, independent restart or quality result. '
                  + ('Deployed S uses a controlled CPU output stand-in, not a sparse kernel.'
                     if refresh else 'No sparse candidate in this control.')}
