"""Actual pinned sampler/WC/UniPC CPU suffix replay, explicit Toy model boundary."""
import copy
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.light_sampling import Hooks
from wcomr.mid_coverage import WC_FIELDS, tree_digest
from wcomr.prepared_input import PreparedInputReplay, RNGState, input_signatures
from wcomr.rv0_fork import WC_CONFIGURATION, SamplerSuffixControl, official_suffix


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow, runtime):
    model, net, scheduler = inference.pipe.model, inference.pipe.model.net, inference.pipe.model.sample_scheduler
    # Reuse pinned official WC, preserving a fixed threshold throughout a run.
    prepare = net.prepare_embedded_sequence
    net.prepare_embedded_sequence = lambda x, **kwargs: (x.movedim(1, -1).contiguous(), None, None)
    original_forward = net.forward
    buffers = {n: v.detach().clone() for n, v in net.named_buffers()}
    caller_state = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    caller_fingerprint = caller_state.fingerprint()
    caller_configuration = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    caller_keys = {k for k in WC_FIELDS if hasattr(net, k)}
    suffix = official_suffix(runtime / 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    checks = []
    try:
        # Forced full and forced reuse are separate CPU restoration controls;
        # these thresholds do not define a new method or production schedule.
        for threshold, kind in [(-1.0, 'full'), (1e6, 'cache')]:
            entry = RNGState()
            prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            observations, controls = [], []
            for observed in (False, True):
                entry.restore()
                with torch.no_grad():
                    for name, value in net.named_buffers(): value.copy_(buffers[name])
                phase_settings = {**settings, 'worldcache_rel_l1_thresh': threshold}
                wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in phase_settings.items()})
                hooks = Hooks()
                current = {'inputs': [], 'outputs': [], 'deep_per_call': [], 'solver': []}
                observations.append(current)
                state = {'inside': False, 'velocity': None, 'noise': None}
                original_prepare = inference.pipe._get_data_batch_input
                inference.pipe._get_data_batch_input = prepared
                hooks.wrap(model, 'get_velocity_fn_from_batch', after=lambda v: state.update(velocity=v))
                hooks.wrap(model, 'denoise', before=lambda a, k: state.update(noise=a[0]))
                counts = [0]
                handles = [b.register_forward_hook(lambda *a: counts.__setitem__(0, counts[0] + 1))
                           for b in list(net.blocks)[1:]]
                def before_forward(a, k):
                    current['inputs'].append(input_signatures(a, k)); counts[0] = 0
                def after_forward(v):
                    if state.get('fail_child') and state['inside']:
                        v.flatten()[0] = float('nan')
                    current['outputs'].append(tree_digest(v)); current['deep_per_call'].append(counts[0])
                hooks.wrap(net, 'forward', before=before_forward, after=after_forward)
                fork_holder = []
                def after_step(value):
                    if state['inside']: return
                    current['solver'].append(tree_digest(value))
                    if scheduler._step_index == 36:
                        final = CompleteStateRoundtrip(net, scheduler, value[0].squeeze(0), [state['generator']])
                        current['actual_final_components'] = final.components()
                    if scheduler._step_index == 22 and observed:
                        # The generator is captured in the step call, not rebuilt by seed.
                        fork = SamplerSuffixControl(model, value[0].squeeze(0), state['noise'],
                            state['generator'], state['velocity'], suffix,
                            context=('CPU_RV0:'+kind, 'toy_frozen_model', 'condition:'+samples[0].name))
                        fork_holder.append(fork)
                        before = copy.deepcopy(current)
                        try:
                            SamplerSuffixControl(model, value[0].squeeze(0), state['noise'],
                                state['generator'], state['velocity'], suffix, context=('', 'toy', 'cond'))
                        except ValueError: pass
                        else: raise AssertionError('Missing request identity accepted')
                        original_code = suffix.__code__
                        suffix.__code__ = (lambda *a: None).__code__
                        try:
                            SamplerSuffixControl(model, value[0].squeeze(0), state['noise'],
                                state['generator'], state['velocity'], suffix, context=fork.context)
                        except ValueError: pass
                        else: raise AssertionError('Changed suffix code accepted')
                        finally: suffix.__code__ = original_code
                        net.cnt -= 1
                        try:
                            SamplerSuffixControl(model, value[0].squeeze(0), state['noise'],
                                state['generator'], state['velocity'], suffix, context=fork.context)
                        except ValueError: pass
                        else: raise AssertionError('Half CFG boundary accepted')
                        finally: fork.restore_parent()
                        fork.parent_latents.add_(.25)
                        try: fork.repeat('invalid_parent_latent')
                        except ValueError: pass
                        else: raise AssertionError('Changed live parent latent accepted')
                        finally: fork.restore_parent()
                        scheduler.timesteps = scheduler.timesteps[:-1]
                        try:
                            SamplerSuffixControl(model, value[0].squeeze(0), state['noise'],
                                state['generator'], state['velocity'], suffix, context=fork.context)
                        except ValueError: pass
                        else: raise AssertionError('Shortened official grid accepted')
                        finally: fork.restore_parent()
                        fork.conditions[0].cross.add_(.01)
                        try: fork.repeat('invalid_condition')
                        except ValueError: pass
                        else: raise AssertionError('Changed conditioning accepted')
                        finally: fork.restore_parent()
                        state['inside'] = True
                        try:
                            state['fail_child'] = True
                            try: fork.repeat('failed_nonfinite_child')
                            except ValueError: pass
                            else: raise AssertionError('Nonfinite child accepted')
                            finally:
                                state['fail_child'] = False
                                for key in before: current[key] = copy.deepcopy(before[key])
                            assert fork.records[-1]['status'] == 'TECH_BLOCKED'
                            assert fork.records[-1]['parent_restored']
                            for label in ('A_first', 'B_second', 'B_first', 'A_second'):
                                start = len(current['inputs'])
                                latent = fork.repeat(label)
                                controls.append({'label': label, 'kind': kind,
                                    'inputs': copy.deepcopy(current['inputs'][start:]),
                                    'outputs': current['outputs'][start:].copy(),
                                    'deep_per_call': current['deep_per_call'][start:].copy(),
                                    'latent': tree_digest(latent), 'record': copy.deepcopy(fork.records[-1])})
                            try: fork.repeat('A_first')
                            except ValueError: pass
                            else: raise AssertionError('Duplicate branch label accepted')
                        finally:
                            state['inside'] = False
                            for key in before: current[key] = before[key]
                hooks.wrap(scheduler, 'step', before=lambda a, k: state.update(generator=k['generator']), after=after_step)
                hooks.wrap(model, 'generate_samples_from_batch', after=lambda v: current.update(final_latent=tree_digest(v)))
                hooks.wrap(model, 'decode', before=lambda a, k: current.update(decode_input=tree_digest(a[0])))
                try:
                    with tempfile.TemporaryDirectory(prefix='rv0-suffix-cpu-') as directory:
                        paths = inference.generate([samples[0]], output_dir=Path(directory))
                        current['mock_artifact'] = Path(paths[0]).read_bytes().hex()
                    current['rng'] = RNGState().signatures()
                    final = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
                    current['final_state'] = final.fingerprint()
                    if observed:
                        assert len(fork_holder) == 1 and len(controls) == 4
                        base = observations[0]
                        for control in controls:
                            assert control['inputs'] == base['inputs'][44:]
                            assert control['outputs'] == base['outputs'][44:]
                            assert control['deep_per_call'] == base['deep_per_call'][44:]
                            assert len(control['inputs']) == 28 and control['latent'] == base['final_latent']
                            assert control['record']['parent_restored']
                            assert control['record']['final_state_components'] == base['actual_final_components']
                        assert len({c['record']['final_state_sha256'] for c in controls}) == 1
                finally:
                    hooks.close(); inference.pipe._get_data_batch_input = original_prepare
                    for h in handles: h.remove()
            assert observations[0] == observations[1]
            if kind == 'full': assert all(c > 0 for c in observations[0]['deep_per_call'])
            else: assert sum(c == 0 for c in observations[0]['deep_per_call']) > 0
            checks.append({'flow': flow, 'control': kind,
                'parent36_CFG72_matches_unobserved_full_pipeline': True,
                'four_suffixes22_to36_CFG28_match_every_input_output_deep_and_final_latent': True,
                'all_suffix_final_state_components_equal': True,
                'AB_BA_order_invariant_parent_restored': True,
                'missing_identity_changed_code_half_CFG_condition_drift_nonfinite_child_duplicate_refused': True,
                'live_parent_latent_and_shortened_grid_drift_refused': True,
                'official_loop_AST_sha256': suffix.official_loop_ast_sha256,
                'real_model_GPU_actions_or_RV_labels': False})
        return checks
    finally:
        net.prepare_embedded_sequence = prepare; net.forward = original_forward
        for key in set(WC_FIELDS) - caller_keys:
            if hasattr(net, key): delattr(net, key)
        for key, value in caller_configuration.items(): setattr(net, key, value)
        caller_state.restore()
        assert caller_state.fingerprint() == caller_fingerprint


def run(runtime):
    spec = importlib.util.spec_from_file_location('rv0_pinned_full_fixture', Path(__file__).with_name('check_full_sampling.py'))
    fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
    result = fixture.run(runtime, exercise=lambda **kwargs: exercise(runtime=Path(runtime), **kwargs))
    return {'status': 'PINNED_CPU_SUFFIX_CONTROLS_ONLY_NOT_REAL_RV0_ACCEPTANCE',
            'checks': result['checks'], 'upstream_sha256': result['upstream_sha256'],
            'stand_in_limits': result['limits'],
            'CUDA_initialized': torch.cuda.is_initialized(), 'RV_labels': 0, 'GPU_submissions': 0}
