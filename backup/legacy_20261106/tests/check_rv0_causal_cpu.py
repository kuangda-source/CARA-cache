"""Full eight-parent/24-suffix/18-output core with pinned Native/Video bodies."""
import copy
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.h0_mode import establish_shared_eval
from wcomr.rv0_causal import run_causal_batch, verify_children


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def exercise(*, inference, samples, wc, settings, inference_module, flow, runtime, **unused):
    model, net = inference.pipe.model, inference.pipe.model.net
    prior_class, prior_prepare = type(net), net.prepare_embedded_sequence
    prior_conditioner = model.conditioner.get_condition_with_negative_prompt
    prior_blocks = [b.forward for b in net.blocks]
    prior_forward, prior_enabled = net.forward, inference.pipe.worldcache_enabled
    native = load('check_fair_sampling_cpu')
    video = load('check_rv0_video_actions_cpu')
    net.__class__ = native.native_toy_class(runtime, prior_class, dict(vars(wc)))
    net.timestep_scale = .001
    net.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    for block, original in zip(net.blocks, prior_blocks):
        def forward(x, *a, _original=original, **kw):
            if a: kw.update(emb_B_T_D=a[0], crossattn_emb=a[1])
            return _original(x, **kw)
        block.forward = forward
    frozen, class_sha = video.pinned_video_condition(runtime,
        wc.worldcache_mini_train_dit_forward.__globals__['DataType'])
    def conditions(batch):
        return tuple(frozen(crossattn_emb=torch.ones(1, 3, 4)*(1+slot+.1*(batch['prompt']=='human')),
            fps=batch['fps'], use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1, 2048, 2, 8, 8), 0, 0, num_conditional_frames=1) for slot in (0, 1))
    model.conditioner.get_condition_with_negative_prompt = conditions
    mode = establish_shared_eval(net)
    settings = {**settings, 'probe_depth': 2, 'worldcache_rel_l1_thresh': .06}
    config = {'sample_names': ['common', 'human'], 'run_id': 'CPU_CAUSAL',
              'logical_copy_cap_bytes': 6*(1<<30), 'workspace_reserve_bytes': 4*(1<<30)}
    contexts = [('CPU_CAUSAL:'+s.name, 'toy_native', 'condition:'+s.name) for s in samples]
    states = []
    original_writer = inference_module.save_img_or_video
    try:
        for failure in ([None] if not flow else [None, 'child_writer', 'child_guardrail']):
            state = {}; calls = [0]
            original_guard = inference_module.guardrail_presets.run_video_guardrail
            def writer(value, path, fps):
                if failure == 'child_writer' and 'child_0_OFF1' in str(path): return
                original_writer(value, path, fps)
            def guard(frames, runner):
                calls[0] += 1
                if failure == 'child_guardrail' and calls[0] == 4: return None
                return original_guard(frames, runner)
            inference_module.save_img_or_video = writer
            inference_module.guardrail_presets.run_video_guardrail = guard
            try:
                with tempfile.TemporaryDirectory(prefix='rv0-causal-complete-cpu-') as d:
                    error = None
                    try:
                        run_causal_batch(inference, samples, wc, settings, state=state, save=lambda: None,
                            output=Path(d), inference_module=inference_module, contexts=contexts,
                            mode_setup=mode, runtime=runtime, config=config)
                    except (ValueError, Exception) as e:
                        error = str(e)
                    assert (state['planned_parent_phases'], state['planned_suffix_controls'], state['planned_encoded_outputs']) == (8, 24, 18)
                    if failure:
                        assert error and state['requests'][0]['status'] == 'TECH_BLOCKED'
                        row = state['requests'][0]['parents'][-1]
                        assert row['mode'] == 'WC_ROUTER_OFF_WITH_SHADOWS' and row['status'] == 'TECH_BLOCKED'
                        assert row['children'][0]['status'] == row['decoded_children'][0]['status'] == 'TECH_BLOCKED'
                        assert row['children'][0]['record']['parent_restored'] is True
                    else:
                        assert error is None, error
                        assert len(state['requests']) == 2
                        for request in state['requests']:
                            assert request['Native_compatibility'] and request['router_OFF_equal']
                            assert len(request['parents']) == 4
                            row = request['parents'][-1]; assert len(row['children']) == 12 and len(row['decoded_children']) == 5
                            assert all('cpu_rv0_pinned_video_condition.Video2WorldCondition' == n for n in row['condition_classes'])
                            verify_children(row, 2)
                            for key in ['inputs', 'deep', 'record']:
                                damaged = copy.deepcopy(row)
                                if key == 'record': damaged['children'][0]['record']['parent_restored'] = False
                                else: damaged['children'][0][key].pop()
                                try: verify_children(damaged, 2)
                                except ValueError: pass
                                else: raise AssertionError('Corrupted suffix evidence accepted')
                        assert sum(len(r['parents']) for r in state['requests']) == 8
                        assert sum(len(r['parents'][-1]['children']) for r in state['requests']) == 24
                        assert sum(len(r['parents'])+len(r['parents'][-1]['decoded_children']) for r in state['requests']) == 18
                states.append({'flow': flow, 'failure': failure, 'receipt': state,
                               'CPU_MOCK_outputs_not_video': True, 'frozen_condition_class_AST_sha256': class_sha})
            finally:
                inference_module.save_img_or_video = original_writer
                inference_module.guardrail_presets.run_video_guardrail = original_guard
            assert net.forward == prior_forward and inference.pipe.worldcache_enabled == prior_enabled
            assert not hasattr(net, '_wc_rv0_router') and all(float(v) == 0 for v in net.buffers())
        return states
    finally:
        net.__class__ = prior_class; net.prepare_embedded_sequence = prior_prepare
        if hasattr(net, 'timestep_scale'): delattr(net, 'timestep_scale')
        for b, old in zip(net.blocks, prior_blocks): b.forward = old
        model.conditioner.get_condition_with_negative_prompt = prior_conditioner
        net.forward = prior_forward; inference.pipe.worldcache_enabled = prior_enabled


def run(runtime):
    runtime = Path(runtime)
    result = load('check_full_sampling').run(runtime, exercise=lambda **k: exercise(runtime=runtime, **k))
    result['status'] = 'FULL_CAUSAL_CORE_NATIVE_VIDEO_CD_DECODE_BRIDGE_CPU_PASS_NOT_GPU'
    result['upstream_sha256'].update(load('check_fair_sampling_cpu').NATIVE_SOURCES)
    result['GPU_submissions'] = result['RV_labels'] = 0
    return result
