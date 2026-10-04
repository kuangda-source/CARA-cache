"""Actual pinned small C/D full-pipeline core, frozen Video2World CPU fixture."""
import copy
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.h0_mode import establish_shared_eval
from wcomr.rv0_small_causal import run_small_causal_batch, verify_small_children


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def exercise(*, inference, samples, wc, settings, inference_module, flow, runtime, **unused):
    model, net = inference.pipe.model, inference.pipe.model.net
    prior_prepare = net.prepare_embedded_sequence
    prior_conditioner = model.conditioner.get_condition_with_negative_prompt
    prior_forward = net.forward
    net.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    frozen, class_sha = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,
        wc.worldcache_mini_train_dit_forward.__globals__['DataType'])
    def conditions(batch):
        return tuple(frozen(crossattn_emb=torch.ones(1, 3, 4)*(1+slot+.1*(batch['prompt']=='human')),
            fps=batch['fps'], use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1, 2048, 2, 8, 8), 0, 0, num_conditional_frames=1) for slot in (0, 1))
    model.conditioner.get_condition_with_negative_prompt = conditions
    mode = establish_shared_eval(net)
    settings = {**settings, 'probe_depth': 2, 'worldcache_rel_l1_thresh': .06}
    config = {'sample_names': ['common', 'human'], 'run_id': 'CPU_SMALL:test',
              'target_calls': [45, 46], 'maximum_age_solver_steps': 32,
              'logical_copy_cap_bytes': 6*(1 << 30), 'workspace_reserve_bytes': 4*(1 << 30)}
    contexts = [(config['run_id']+':'+s.name, 'toy_model', 'condition:'+s.name) for s in samples]
    states = []
    original_writer = inference_module.save_img_or_video
    original_guard = inference_module.guardrail_presets.run_video_guardrail
    try:
        failures = [None] if not flow else [None, 'child_writer', 'child_guardrail', 'historical_bridge']
        for failure in failures:
            state = {}; calls = [0]
            def writer(value, path, fps):
                if failure == 'child_writer' and 'child_OFF1' in str(path):
                    return
                original_writer(value, path, fps)
            def guard(frames, runner):
                calls[0] += 1
                if failure == 'child_guardrail' and calls[0] == 1:
                    return None
                return original_guard(frames, runner)
            inference_module.save_img_or_video = writer
            inference_module.guardrail_presets.run_video_guardrail = guard
            if failure == 'historical_bridge':
                config['historical_wc_settings'] = settings.copy()
                config['references'] = {s.name: {'model_and_condition_context': list(c[1:]),
                    'timesteps': [], 'official_WC': {'sha256': '0'*64}}
                    for s, c in zip(samples, contexts)}
            try:
                with tempfile.TemporaryDirectory(prefix='rv0-small-causal-cpu-') as directory:
                    error = None
                    try:
                        run_small_causal_batch(inference, samples, wc, settings, state=state, save=lambda: None,
                            output=Path(directory), inference_module=inference_module, contexts=contexts,
                            mode_setup=mode, runtime=runtime, config=config,
                            require_historical_bridge=failure == 'historical_bridge')
                    except Exception as exception:
                        error = str(exception)
                    assert (state['planned_parent_phases'], state['planned_suffix_controls'],
                            state['planned_encoded_outputs']) == (2, 12, 8)
                    if failure:
                        assert error and state['requests'][0]['status'] == 'TECH_BLOCKED'
                        if failure != 'historical_bridge':
                            row = state['requests'][0]
                            assert row['children'][0]['status'] == row['decoded_children'][0]['status'] == 'TECH_BLOCKED'
                            assert row['children'][0]['record']['parent_restored']
                        else:
                            assert 'historical Native reference provenance' in error
                    else:
                        assert error is None, error
                        assert state['status'] == 'SMALL_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'
                        assert len(state['requests']) == 2
                        for slot, row in enumerate(state['requests']):
                            verify_small_children(row, slot, 2)
                            assert len(row['children']) == 6 and len(row['decoded_children']) == 3
                            assert row['historical_WC_encoded_bridge_pass'] == 'CPU_TOY_NOT_REAL_REFERENCE'
                            assert all('cpu_rv0_pinned_video_condition.Video2WorldCondition' == c
                                       for c in row['condition_classes'])
                            for key in ('inputs', 'deep', 'record', 'pipeline'):
                                damaged = copy.deepcopy(row)
                                if key == 'record':
                                    damaged['children'][0]['record']['parent_restored'] = False
                                elif key == 'pipeline':
                                    damaged['decoded_children'][0]['pipeline'].pop()
                                else:
                                    damaged['children'][0][key].pop()
                                try:
                                    verify_small_children(damaged, slot, 2)
                                except ValueError:
                                    pass
                                else:
                                    raise AssertionError('Corrupted small full-pipeline evidence accepted')
                        assert sum(len(row['children']) for row in state['requests']) == 12
                        assert sum(1+len(row['decoded_children']) for row in state['requests']) == 8
                    states.append({'flow': flow, 'failure': failure, 'error': error,
                        'receipt': state, 'CPU_MOCK_outputs_not_video': True,
                        'frozen_condition_class_AST_sha256': class_sha})
                assert net.forward == prior_forward and not hasattr(net, '_wc_rv0_router')
                assert all(float(b) == 0 for b in net.buffers())
                assert all(not m.training for m in net.modules())
            finally:
                inference_module.save_img_or_video = original_writer
                inference_module.guardrail_presets.run_video_guardrail = original_guard
        return states
    finally:
        net.prepare_embedded_sequence = prior_prepare
        model.conditioner.get_condition_with_negative_prompt = prior_conditioner
        net.forward = prior_forward


def run(runtime):
    result = load('check_full_sampling').run(Path(runtime),
        exercise=lambda **k: exercise(runtime=Path(runtime), **k))
    assert len(result['checks']) == 5
    assert not torch.cuda.is_initialized()
    result.update(status='SMALL_CD_FULL_PIPELINE_CPU_PASS_NOT_GPU', GPU_submissions=0, RV_labels=0,
        complete_successful_parents=4, complete_successful_suffixes=24, successful_mock_outputs=16,
        failed_attempts_retained=3, current_historical_GPU_encoded_bridge='UNTESTED_BY_CPU_TOY')
    return result
