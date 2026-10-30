"""Actual S CLI -> model entry -> full tiny matrix, with declared CPU edges.

Admission, checkpoint lookup, environment, weight loader and CUDA telemetry are
CPU stand-ins. The production CLI has no CPU switch; the test adapter invokes
the existing explicit CPU boundaries in the model and data checkers.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import torch

from wcomr.cfg_paired_probe_forward import WC_PATH, WC_SHA, RF_PATH, RF_SHA
from wcomr.h0_mode import mode_snapshot
from wcomr.sq_s_batch_r1 import digest, make_scope
from wcomr.sq_s_physical_r1 import make_physical_scope

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'plans/cara_next_stage_20261028/sq'


def run(runtime, artifacts, host, actual_config, tiny_loader, *, native_modules=None):
    import check_full_sampling as full
    import check_partial_mlp_guided_sampling_cpu_r1 as blocks
    import check_rv0_video_actions_cpu as conditions_source
    import check_sq_s_collection_cpu_r1 as topology
    from wcomr import sq_s_model_entry_r1 as entry
    from wcomr import sq_s_data_terminal_r2 as data
    from wcomr import sq_s_execution_r2 as execution
    from wcomr import sq_s_stage_r2 as stage_source
    from wcomr import sq_control_storage_r1 as storage_source
    from wcomr import wc73_exclusive_r1 as exclusive
    from wcomr import runtime_config
    from wcomr.sq_s_spec_r2 import RUN
    import run_cara_sq_s_r2 as cli

    def body(*, inference, wc, settings, inference_module, flow, **unused):
        if native_modules is not None: wc, rf = native_modules
        model = inference.pipe.model
        net = model.net
        original = dict(blocks=net.blocks, t_embedder=net.t_embedder,
            unpatchify=net.unpatchify, final_layer=net.final_layer,
            prepare_embedded_sequence=net.prepare_embedded_sequence, forward=net.forward,
            use_wan_fp32_strategy=net.use_wan_fp32_strategy)
        model_original = {k: getattr(model, k) for k in
            ('denoise', 'get_velocity_fn_from_batch', 'get_data_and_condition', 'generate_samples_from_batch')}
        config_original = copy.deepcopy(vars(model.config))
        conditioner_original = model.conditioner.get_condition_with_negative_prompt
        prepare_original = inference.pipe._get_data_batch_input
        net.blocks = blocks.pinned_blocks(runtime)
        class Head(torch.nn.Module):
            def forward(self, x, *args, **kwargs): return x + .01*x.square()
        net.final_layer = Head().eval()
        net.t_embedder = lambda t: ((t.float()/1000).unsqueeze(-1).expand(*t.shape, 8), None)
        net.prepare_embedded_sequence = lambda x, **kw: (
            x[:, :8].movedim(1, -1).contiguous().repeat_interleave(2, 2).repeat_interleave(2, 3), None, None)
        net.unpatchify = lambda x: x[:, :, ::2, ::2, :].movedim(-1, 1).contiguous()
        net.use_wan_fp32_strategy = True
        model.precision = torch.float32
        model.config.state_ch = 8
        model.config.conditional_frame_timestep = .1
        model.config.denoise_replace_gt_frames = True
        model.config.min_num_conditional_frames = model.config.max_num_conditional_frames = 0
        model.config.conditional_frames_probs = None
        cls, _ = conditions_source.pinned_video_condition(runtime, wc.DataType)
        inputs = json.loads((BASE/'S_EXECUTION_IDENTITY_R1.json').read_text())['inputs']
        def conditions(batch):
            return tuple(cls(crossattn_emb=torch.ones(1, 3, 4)*
                (1+b+.1*(batch['prompt'] == inputs[1]['prompt'])), fps=batch['fps'],
                use_video_condition=torch.tensor([True])).set_video_condition(
                    torch.zeros(1, 8, 2, 8, 8), 0, 0, num_conditional_frames=0) for b in (0, 1))
        model.conditioner.get_condition_with_negative_prompt = conditions
        model.get_data_and_condition = lambda batch: (None, torch.zeros(1, 8, 2, 8, 8), None)
        geometry_calls = []
        def sample_tiny(batch, *args, **kw):
            assert 'state_shape' not in kw
            frames, height, width = batch[model.input_data_key].shape[-3:]
            original_shape = [model.config.state_ch, model.tokenizer.get_latent_num_frames(frames),
                height//model.tokenizer.spatial_compression_factor, width//model.tokenizer.spatial_compression_factor]
            geometry_calls.append(original_shape)
            assert original_shape == [8, 2, 216, 384]
            return model_original['generate_samples_from_batch'](batch, *args, **dict(kw, state_shape=[8, 2, 8, 8]))
        model.generate_samples_from_batch = sample_tiny
        def prepare(*args, **kw):
            batch = prepare_original(*args, **kw)
            assert 'num_conditional_frames' not in batch
            return dict(batch, num_conditional_frames=0)
        inference.pipe._get_data_batch_input = prepare
        names = ('denoise', 'get_velocity_fn_from_batch')
        if native_modules is None:
            rf = ModuleType('cpu_S_pinned_RF')
            namespace = dict(torch=torch, DataType=wc.DataType, NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames',
                parallel_state=SimpleNamespace(is_initialized=lambda: False))
            # Only the local branch uses extracted functions and CPU globals.
            wc.__file__ = str(runtime/WC_PATH)
            full.load_functions(runtime/WC_PATH, ['compute_saliency_map'], vars(wc))
            rf.__file__ = str(runtime/RF_PATH)
            vars(rf).update(namespace)
            assert hashlib.sha256((runtime/RF_PATH).read_bytes()).hexdigest() == RF_SHA
            full.load_functions(runtime/RF_PATH, names, vars(rf))
        else:
            for module, path, expected in ((wc, WC_PATH, WC_SHA), (rf, RF_PATH, RF_SHA)):
                assert Path(module.__file__).resolve() == (runtime/path).resolve()
                assert hashlib.sha256((runtime/path).read_bytes()).hexdigest() == expected
            assert rf.Video2WorldModelRectifiedFlow.get_velocity_fn_from_batch.__globals__ is vars(rf)
        methods = {name: getattr(rf if native_modules is None else rf.Video2WorldModelRectifiedFlow, name)
            for name in names}
        if native_modules is None:
            rf.Video2WorldModelRectifiedFlow = type('PinnedCPUVideo2World', (), methods)
        for name, method in methods.items(): setattr(model, name, method.__get__(model))
        root = Path(artifacts)/('flow-'+str(flow))
        root.mkdir(parents=True, exist_ok=False)
        (root/'runtime').symlink_to(Path(runtime).resolve(), target_is_directory=True)
        output = root/'outputs'/RUN
        output.mkdir(parents=True)
        stage = root/'stage'; stage.mkdir()
        identity = json.loads((BASE/'S_EXECUTION_IDENTITY_R1.json').read_text())
        identity['expected_real_shape'] = [1, 8, 2, 8, 8]
        identity['historical_WC_settings']['worldcache_flow_enabled'] = flow
        identity['model_setup']['worldcache_flow_enabled'] = flow
        identity['identity_sha256'] = digest({k: v for k, v in identity.items() if k != 'identity_sha256'})
        from wcomr.policy_generator_r1.interval_grammar import Profile
        values = json.loads((BASE/'S_SUPPORT_RECONCILIATION_R2.json').read_text())['profile']
        for key in ('protected_dense', 'alpha_candidates'): values[key] = tuple(values[key])
        upper = make_scope(Profile(**values), cpu_fixture=True)
        physical = make_physical_scope(upper, host, identity['identity_sha256'])
        contract = json.loads((BASE/'S_MODEL_ENTRY_CPU_RESOURCE_CONTRACT_R5.json').read_text())
        bundle = dict(identity=identity, upper=upper, physical=physical, resource_contract=contract,
            mode_types=mode_snapshot(net)['module_types'], CPU_decode_fixture=lambda r: dict(frames=93, sha256=r['RGB']['sha256']),
            execution_profile=dict(CUDA_allocator_fraction_max=.9, streaming_tensor_artifact_cap_GiB=1,
                output_file_GiB_max=1, minimum_output_free_MiB=1))
        authority = dict(run_id=RUN, host=host, gpu_uuid='', launch_id='CPU_FIXTURE_ONLY',
            source_revision='CPU_FIXTURE_NO_GPU_AUTHORITY', scope_sha256=upper['scope_sha256'])
        events = []
        def record(name): events.append(name)
        storage = SimpleNamespace(output=output, check=lambda: record('storage'))
        def load(setup):
            record('load'); inference.setup_args = setup
            assert type(setup) is actual_config.SetupArguments
            assert setup.model == runtime_config.MODEL and setup.experiment == runtime_config.EXPERIMENT
            return inference
        environment = ModuleType('cosmos_oss.init')
        environment.init_environment = lambda: record('init')
        environment.init_output_dir = lambda *a, **kw: record('output')
        environment.cleanup_environment = lambda: record('cleanup')
        oss = ModuleType('cosmos_oss'); oss.init = environment
        inference_package = ModuleType('cosmos_predict2._src.predict2.inference')
        inference_package.worldcache_utils = wc
        models_package = ModuleType('cosmos_predict2._src.predict2.models')
        models_package.video2world_model_rectified_flow = rf
        modules = {'cosmos_predict2.inference': inference_module, 'cosmos_oss': oss, 'cosmos_oss.init': environment}
        if native_modules is None:
            modules.update({'cosmos_predict2._src.predict2.inference': inference_package,
                'cosmos_predict2._src.predict2.inference.worldcache_utils': wc,
                'cosmos_predict2._src.predict2.models': models_package,
                'cosmos_predict2._src.predict2.models.video2world_model_rectified_flow': rf})
        import cosmos_predict2
        original_execute, original_check = entry.execute, data.check_result
        def cpu_entry(**kw):
            assert 'CPU_fixture' not in kw
            return original_execute(**kw, CPU_fixture=True)
        classifications = []
        def cpu_check(*a, **kw):
            assert 'CPU_fixture' not in kw
            value = original_check(*a, **kw, CPU_fixture=True)
            classifications.append(value)
            return value
        counts = dict(head=0, deep=0)
        def head(*args): counts['head'] += 1
        def deep(*args): counts['deep'] += 1
        hooks = [net.final_layer.register_forward_pre_hook(head),
            net.blocks[identity['historical_WC_settings']['probe_depth']].register_forward_pre_hook(deep)]
        args = SimpleNamespace(project=root, stage=stage,
            source_revision=authority['source_revision'], gpu_uuid='')
        try:
            with patch.dict(sys.modules, modules), patch.object(cosmos_predict2, 'inference', inference_module, create=True), \
                    patch.object(inference_module, 'Inference', load, create=True), \
                    patch.object(execution, 'validate', return_value=(bundle, dict(source_revision=args.source_revision), authority)), \
                    patch.object(storage_source, 'storage_for', return_value=storage), \
                    patch.object(stage_source, 'verify_lease_fd', return_value=None), \
                    patch.object(exclusive, 'runner_context_gate', return_value=SimpleNamespace(is_cuda=False)), \
                    patch.object(runtime_config, 'install_core_inference_registration', side_effect=lambda *a: record('register')), \
                    patch.object(entry, 'execute', side_effect=cpu_entry), patch.object(data, 'check_result', side_effect=cpu_check), \
                    patch.dict(os.environ, WC_SUPERVISOR_PID=str(os.getppid()), WC_LOCK_FD='CPU_NO_FD'), \
                    patch.object(torch.cuda, 'set_per_process_memory_fraction', return_value=None), \
                    patch.object(torch.cuda, 'max_memory_allocated', return_value=0), \
                    patch.object(torch.cuda, 'max_memory_reserved', return_value=0):
                result = cli.run(args)
                try: cli.run(args)
                except ValueError as error: assert 'recover without retry' in str(error)
                else: raise AssertionError('Original successful CLI attempt was replayed')
            assert counts == dict(head=936, deep=552), counts
            assert events.count('load') == events.count('cleanup') == events.count('register') == 1
            assert events.index('register') < events.index('load') < events.index('cleanup')
            assert result['model_entry']['environment_cleanup_accepted']
            assert len(result['attempted_new_role_ids']) == 10 and len(result['resource_checks']) == 108
            assert physical['counts']['reused_OFF_paths'] == 0
            assert len(geometry_calls) == 10
            assert len(classifications) == 1 and classifications[0]['CPU_fixture'] is True
            saved = json.loads((output/'S-collection.json').read_text())
            assert saved == result and saved['actual_CUDA'] is False
            rows = [r for path in result['matrix']['rows'] for r in path['result']['S_rows']]
            with patch.object(topology, '_tiny_tensor_loader', tiny_loader):
                reload_audit = topology.audit_storage(output/'streaming', rows)
            assert reload_audit['files_SHA_and_bytes_reloaded'] == 140
            scopes = output/'CPU-fixture-scopes.json'
            with scopes.open('x') as stream:
                json.dump(dict(identity=identity, upper=upper, physical=physical, resource_contract=contract),
                    stream, indent=2, allow_nan=False); stream.write('\n')
            return [dict(host=host, flow=flow, status='CPU_CLI_MODEL_MATRIX_PASS',
                model_load_standins=1, environment_cleanup_standins=1, new_tiny_paths=10,
                reused_OFF_roles=0, observed_head_calls=counts['head'], observed_deep_calls=counts['deep'],
                resource_checks=108, same_state_rows=108, raw_states=8, unique_anchors=24,
                original_cli_replay_refused=True, actual_pinned_config_parser=True,
                original_two_FIT_argument_objects=True, CPU_latent_shape_adapter_calls=len(geometry_calls),
                original_request_resolution_preserved=True, classification=classifications[0],
                full_native_WC_RF_module_namespaces=native_modules is not None,
                CPU_fixture_scopes_path=str(scopes),
                CPU_fixture_scopes_sha256=hashlib.sha256(scopes.read_bytes()).hexdigest(),
                reload_audit=reload_audit, output=str(output), events=events,
                actual_weights=False, actual_CUDA=False, real_S_labels=0)]
        finally:
            for hook in hooks: hook.remove()
            for key, value in original.items():
                if key == 'final_layer': del net.final_layer
                setattr(net, key, value)
            for key, value in model_original.items(): setattr(model, key, value)
            vars(model.config).clear(); vars(model.config).update(config_original)
            model.conditioner.get_condition_with_negative_prompt = conditioner_original
            inference.pipe._get_data_batch_input = prepare_original

    result = full.run(Path(runtime), exercise=body)
    result['upstream_sha256'][RF_PATH] = RF_SHA
    return result
