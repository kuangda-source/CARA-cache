"""Actual pinned CPU sampler exercises for the fresh-prepare lightweight core."""
from contextlib import ExitStack
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.full_sampling import CompleteStateRoundtrip, PARITY_KEYS, STATE_STEPS
from wcomr.light_sampling import run_light_pair
from wcomr.mid_coverage import tree_digest
from wcomr.prepared_input import input_signatures
from wcomr.refresh_deployment import SimpleRefreshAdapter
from wcomr.stage_witness import StageWitness


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow):
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    checks = []
    scenarios = ['dense', 'sparse', 'insufficient_history', 'reverse_dense', 'abba_dense',
                 'decode_failure', 'writer_failure', 'kernel_nonfinite', 'condition_change',
                 'text_guardrail_reject', 'text_guardrail_keep_going']
    if not flow:
        scenarios = ['dense', 'sparse']
    for scenario in scenarios:
        state, spy, syncs = {}, [], []
        sequence = ('candidate', 'official') if scenario == 'reverse_dense' else (
                   ('official', 'candidate', 'candidate', 'official') if scenario == 'abba_dense'
                   else ('official', 'candidate'))
        originals = (model.decode, inference_module.save_img_or_video,
                     inference.pipe._get_data_batch_input, model.denoise, scheduler.step)
        context = ('CPU_LIGHT:common', 'toy', 'condition:common')
        stack = ExitStack()
        if scenario in ('text_guardrail_reject', 'text_guardrail_keep_going'):
            original_text = inference_module.guardrail_presets.run_text_guardrail
            calls = [0]
            def text_guardrail(*args, **kwargs):
                calls[0] += 1
                return calls[0] != 2
            inference_module.guardrail_presets.run_text_guardrail = text_guardrail
            stack.callback(setattr, inference_module.guardrail_presets, 'run_text_guardrail', original_text)
            original_keep = inference.setup_args.keep_going
            inference.setup_args.keep_going = scenario == 'text_guardrail_keep_going'
            stack.callback(setattr, inference.setup_args, 'keep_going', original_keep)
        active = [None]
        def prepare(*args, **kwargs):
            value = originals[2](*args, **kwargs)
            row = {'prepared': input_signatures((), value), 'input_hashes': [], 'output_hashes': [],
                   'named_inputs': [], 'conditions': [], 'field_signatures': [], 'state_fingerprints': []}
            spy.append(row)
            active[0] = row
            return value
        inference.pipe._get_data_batch_input = prepare
        stack.callback(setattr, inference.pipe, '_get_data_batch_input', originals[2])
        def pre(module, args, kwargs):
            active[0]['named_inputs'].append(input_signatures(args, kwargs))
            active[0]['input_hashes'].append(tree_digest([v for v in list(args) + list(kwargs.values()) if isinstance(v, torch.Tensor)]))
        def post(module, args, kwargs, value):
            active[0]['output_hashes'].append(tree_digest(value))
        stack.callback(net.register_forward_pre_hook(pre, with_kwargs=True).remove)
        stack.callback(net.register_forward_hook(post, with_kwargs=True).remove)
        def denoise(*args, **kwargs):
            condition = kwargs.get('condition', args[3] if len(args) > 3 else None)
            if scenario == 'condition_change' and len(spy) == 2 and scheduler._step_index == 11:
                condition.cross = condition.cross + .01
            active[0]['conditions'].append(input_signatures((), condition.to_dict(skip_underscore=False)))
            return originals[3](*args, **kwargs)
        model.denoise = denoise
        stack.callback(setattr, model, 'denoise', originals[3])
        def step(*args, **kwargs):
            value = originals[4](*args, **kwargs)
            n = scheduler._step_index
            if n in STATE_STEPS:
                generators = [kwargs['generator']] if kwargs.get('generator') is not None else []
                components = CompleteStateRoundtrip(net, scheduler, value[0], generators).components()
                components.pop('refresh.provenance', None)
                active[0]['field_signatures'].append({'solver_step': n, 'components': components})
                active[0]['state_fingerprints'].append(tree_digest(components))
            return value
        scheduler.step = step
        stack.callback(setattr, scheduler, 'step', originals[4])
        def decode(*args, **kwargs):
            if scenario == 'decode_failure' and len(spy) == 2:
                raise ValueError('CPU light decoder failure')
            return originals[0](*args, **kwargs)
        model.decode = decode
        stack.callback(setattr, model, 'decode', originals[0])
        def write(*args, **kwargs):
            if scenario == 'writer_failure' and len(spy) == 2:
                return None
            return originals[1](*args, **kwargs)
        inference_module.save_img_or_video = write
        stack.callback(setattr, inference_module, 'save_img_or_video', originals[1])
        class Insufficient(SimpleRefreshAdapter):
            def before(self, net, skipped, branch, original, probe):
                self.ledger.true_dense_history[branch] = []
                return super().before(net, skipped, branch, original, probe)
        def bad_kernel(*args, **kwargs):
            value, metadata = kernel(*args, **kwargs)
            if scenario == 'kernel_nonfinite':
                value = value.clone(); value.flatten()[0] = float('nan')
            return value, metadata
        def factory(kind, context):
            if kind == 'official':
                return None
            cls = Insufficient if scenario == 'insufficient_history' else SimpleRefreshAdapter
            return cls(context, sparse=scenario not in ('dense', 'reverse_dense', 'abba_dense'),
                       fallback_layers=(2,), kernel=bad_kernel)
        # Full CPU control observers are external to the production timing core.
        # Their time is deliberately not a performance result.
        witness = StageWitness()
        witness.wrap(model, 'generate_samples_from_batch', after=lambda v: witness.record('sample_return', v))
        witness.wrap(model, 'decode', after=lambda v: witness.record('decode_output', v))
        stack.callback(witness.close)
        error = None
        try:
            with tempfile.TemporaryDirectory(prefix='light-sampling-cpu-') as directory:
                try:
                    run_light_pair(inference, samples[0], wc, settings, state=state,
                        save=lambda: None, output=Path(directory), inference_module=inference_module,
                        context=context, mode_setup=mode_setup, adapter_factory=factory,
                        sequence=sequence, expected_video=(93, 16, 16), sync=lambda: syncs.append(len(spy)))
                except Exception as exc:
                    error = str(exc)
                assert state['planned_phases'] == state['planned_outputs'] == len(sequence)
                assert len(spy) == (1 if scenario in ('text_guardrail_reject', 'text_guardrail_keep_going') else len(sequence))
                assert all(p['prepared'] == spy[0]['prepared'] for p in spy)
                assert len(syncs) == 2 * len(sequence)
                assert syncs[:2] == [0, 1]
                assert not state['checkpoint_restore'] and not state['per_forward_tensor_diagnostic_hashes']
                assert state['refresh_condition_content_hashes_retained']
                assert state['refresh_ledger_and_kernel_checks_counted_in_wall']
                assert not hasattr(net, '_wc_refresh_adapter')
                assert all(float(v) == 0 for v in net.buffers())
                if scenario in ('dense', 'sparse', 'insufficient_history', 'reverse_dense', 'abba_dense'):
                    assert error is None, error
                    assert state['status'] == 'COMPLETE_LIGHT_PIPELINE_INTERFACE_REQUIRES_GPU_PARITY_AND_METRICS'
                    a = next(p for p in state['phases'] if p['kind'] == 'official')
                    b = next(p for p in state['phases'] if p['kind'] == 'candidate')
                    assert all(p['solver_steps'] == 36 and p['CFG_calls'] == 72 and p['prepare_calls'] == 1 for p in (a, b))
                    assert a['sampling'] == b['sampling'] and a['flags_before'] == b['flags_before']
                    assert a['flags_after'] == b['flags_after'] and a['rng_after'] == b['rng_after']
                    assert [v['cache_counter_before'] for v in b['trace']] == list(range(70)) + [0, 1]
                    for row, phase in zip(spy, state['phases']):
                        row.update(trace=phase['trace'], block_counts=phase['block_counts'], sampling=phase['sampling'])
                    nine = {key: all(p[key] == spy[0][key] for p in spy) for key in PARITY_KEYS}
                    events = b['refresh_provenance']['events']
                    assert len(events) == 72 and events[69]['native_cycle_reset']
                    assert not events[70]['references_read'] and not events[71]['references_read']
                    assert all(e['action'] == 'dense' for e in events[:14] + events[70:])
                    assert all(v['kind'] == 'dense' for w in b['refresh_provenance']['true_dense_history'] for v in w)
                    sparse = [e for e in events if e['sparse_layers']]
                    if scenario == 'sparse':
                        assert sparse and all(e['sparse_layers'] == [1, 3] and not e['inserted_into_true_dense_history'] for e in sparse)
                        assert any(e['action'] == 'cache' and any(v['kind'] == 'sparse' for v in e['references_read']) for e in events)
                        assert not nine['output_hashes']
                    else:
                        assert not sparse and all(nine.values())
                        assert a['artifacts'] == b['artifacts']
                        assert all(witness.events[:2] == witness.events[i:i+2]
                                   for i in range(2, len(witness.events), 2))
                    checks.append({'flow': flow, 'scenario': scenario, 'nine_CPU_control_checks': nine,
                        'ordinary36_72_93_interface': True, 'actual_prepare_calls': len(sequence),
                        'sequence': list(sequence),
                        'CPU_stand_in_is_not_sparse_kernel': scenario not in ('dense', 'reverse_dense', 'abba_dense'),
                        'source_reset_true_dense_separation_fallback_and_tail_pass': True,
                        'hash_and_snapshot_observers_external_to_timing_core': True})
                else:
                    assert error and state['status'] == 'TECH_BLOCKED_DENOMINATOR_PRESERVED'
                    assert state['phases'][0]['status'].startswith('COMPLETE36_CFG72')
                    assert state['phases'][1]['status'] == 'TECH_BLOCKED'
                    checks.append({'flow': flow, 'scenario': scenario, 'error': error,
                                   'first_phase_preserved': True, 'planned_phases': 2,
                                   'all_cleanup_and_boundaries_restored': True})
        finally:
            stack.close()
        assert originals == (model.decode, inference_module.save_img_or_video,
                             inference.pipe._get_data_batch_input, model.denoise, scheduler.step)
    # Invalid work allocations must fail before initial reset or generation.
    for sequence in [('official', 'official', 'candidate'), {'official', 'candidate'}]:
        try:
            run_light_pair(inference, samples[0], wc, settings, state={}, save=lambda: None,
                output=Path('/invalid-unused'), inference_module=inference_module,
                context=('CPU_LIGHT:common', 'toy', 'condition:common'), mode_setup=mode_setup,
                sequence=sequence, expected_video=(93, 16, 16))
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid light work allocation accepted')
    checks.append({'flow': flow, 'scenario': 'unequal_or_unordered_sequence_refused_before_generation'})
    return checks


def run(runtime):
    spec = importlib.util.spec_from_file_location('pinned_light_fixture', Path(__file__).with_name('check_full_sampling.py'))
    fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
    result = fixture.run(runtime, exercise=exercise)
    result['status'] = 'LIGHT_FRESH_PREPARE_COMPLETE_SAMPLER_CPU_GATE_PASS_NOT_GPU_VIDEO_OR_SPEED'
    return result
