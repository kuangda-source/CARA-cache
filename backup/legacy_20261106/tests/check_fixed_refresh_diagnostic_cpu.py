"""Pinned full sampler exercises for offline fixed-refresh diagnostic routing."""
from contextlib import ExitStack
import hashlib
import importlib.util
from pathlib import Path
import tempfile

import torch

from wcomr.fixed_refresh_diagnostic import FixedRefreshDiagnosticAdapter
from wcomr.fixed_refresh_mask import FixedRefreshMask
from wcomr.full_sampling import CompleteStateRoundtrip, PARITY_KEYS, STATE_STEPS
from wcomr.light_sampling import Hooks, run_light_pair
from wcomr.mid_coverage import tree_digest
from wcomr.prepared_input import input_signatures, RNGState
from wcomr.refresh_deployment import SimpleRefreshAdapter
from wcomr.stage_witness import StageWitness


def observed_pair(inference, sample, wc, settings, module, mode, factory, context):
    model, net = inference.pipe.model, inference.pipe.model.net
    rows, active, state = [], [None], {}
    hooks, stages = Hooks(), StageWitness()
    originals = (net.forward, model.denoise, model.sample_scheduler.step, model.decode,
                 inference.pipe._get_data_batch_input, module.save_img_or_video)
    with ExitStack() as stack:
        stack.callback(hooks.close); stack.callback(stages.close)
        def prepared(value):
            row = {'prepared': input_signatures((), value), 'input_hashes': [], 'output_hashes': [],
                   'named_inputs': [], 'conditions': [], 'state_fingerprints': [],
                   'field_signatures': [], 'stage_start': len(stages.events)}
            rows.append(row); active[0] = row
        hooks.wrap(inference.pipe, '_get_data_batch_input', after=prepared)
        def before(mod, args, kwargs):
            active[0]['named_inputs'].append(input_signatures(args, kwargs))
            active[0]['input_hashes'].append(tree_digest([v for v in list(args) + list(kwargs.values())
                if isinstance(v, torch.Tensor)]))
        def after(mod, args, kwargs, value):
            active[0]['output_hashes'].append(tree_digest(value))
        stack.callback(net.register_forward_pre_hook(before, with_kwargs=True).remove)
        stack.callback(net.register_forward_hook(after, with_kwargs=True).remove)
        def denoise(args, kwargs):
            c = kwargs.get('condition', args[3] if len(args) > 3 else None)
            active[0]['conditions'].append(input_signatures((), c.to_dict(skip_underscore=False)))
        hooks.wrap(model, 'denoise', before=denoise)
        def stepped(value):
            n = model.sample_scheduler._step_index
            if n in STATE_STEPS:
                fields = CompleteStateRoundtrip(net, model.sample_scheduler, value[0]).components()
                fields.pop('refresh.provenance', None)
                active[0]['field_signatures'].append({'solver_step': n, 'components': fields})
                active[0]['state_fingerprints'].append(tree_digest(fields))
        hooks.wrap(model.sample_scheduler, 'step', after=stepped)
        stages.wrap(model, 'generate_samples_from_batch', after=lambda v: stages.record('sample_return', v))
        stages.wrap(model, 'decode', after=lambda v: stages.record('decode_output', v))
        stages.wrap(module.guardrail_presets, 'run_video_guardrail', after=lambda v: stages.record('guardrail_output', v))
        stages.wrap(module, 'save_img_or_video', before=lambda a, k: stages.record('save_input', a[0]))
        error = None
        with tempfile.TemporaryDirectory(prefix='fixed-refresh-cpu-') as directory:
            try:
                run_light_pair(inference, sample, wc, settings, state=state, save=lambda: None,
                    output=Path(directory), inference_module=module, context=context,
                    mode_setup=mode, adapter_factory=factory, expected_video=(93, 16, 16),
                    sync=lambda: None)
            except Exception as exc:
                error = str(exc)
        for i, (row, phase) in enumerate(zip(rows, state['phases'])):
            end = rows[i + 1]['stage_start'] if i + 1 < len(rows) else len(stages.events)
            row['pipeline'] = stages.events[row.pop('stage_start'):end]
            for key in ('trace', 'block_counts', 'sampling', 'artifacts', 'flags_after', 'rng_after'):
                if key in phase: row[key] = phase[key]
    assert originals == (net.forward, model.denoise, model.sample_scheduler.step, model.decode,
                        inference.pipe._get_data_batch_input, module.save_img_or_video)
    assert not hasattr(net, '_wc_refresh_adapter')
    assert all(float(v) == 0 for v in net.buffers())
    return state, rows, error


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow):
    context = ('CPU_FIXED:common', 'toy', 'condition:common')
    args = (inference, samples[0], wc, settings, inference_module, mode_setup)
    # The CPU prepare fixture samples fps and Python/NumPy metadata. Reusing
    # the seed of the latent alone does not match entry RNG across separate pairs.
    entry_rng = RNGState()
    entry_rng.restore()
    state, rows, error = observed_pair(*args,
        lambda kind, ctx: None if kind == 'official' else SimpleRefreshAdapter(ctx, fallback_layers=(2,)), context)
    assert error is None and len(rows) == 2
    assert all(rows[0][key] == rows[1][key] for key in PARITY_KEYS)
    dense_calls = tuple(r['deep_executed'] for r in state['phases'][0]['trace'])
    mask = FixedRefreshMask('common', 'toy', 'condition:common', dense_calls,
        hashlib.sha256(repr(dense_calls).encode()).hexdigest())
    reference = rows[0]
    checks = [{'flow': flow, 'scenario': 'default_adaptive_dense_control', 'nine_checks': True}]
    for scenario in ['same_mask_dense', 'changed_mask_dense', 'fixed_sparse',
                     'missing_native_history', 'sparse_failure']:
        selected = mask
        if scenario == 'changed_mask_dense':
            calls = list(dense_calls)
            assert not calls[14] and not calls[15] and calls[22] and calls[23]
            calls[14:16] = [True, True]; calls[22:24] = [False, False]
            selected = FixedRefreshMask('common', 'toy', 'condition:common', tuple(calls), mask.source_receipt_sha256)
        class Missing(FixedRefreshDiagnosticAdapter):
            def start(self, net, branch, condition):
                super().start(net, branch, condition)
                if self.ledger.call == 15:
                    net.previous_input[branch] = None
        def factory(kind, ctx):
            if scenario == 'missing_native_history' and kind == 'candidate': cls = Missing
            else: cls = FixedRefreshDiagnosticAdapter
            def operation(*a, **kw):
                output, metadata = kernel(*a, **kw)
                if scenario == 'sparse_failure':
                    output = output.clone();output.flatten()[0] = float('nan')
                return output, metadata
            return cls(ctx, selected, sparse=kind == 'candidate' and scenario in ['fixed_sparse', 'sparse_failure'],
                       fallback_layers=(2,), kernel=operation)
        entry_rng.restore()
        result, observations, error = observed_pair(*args, factory, context)
        assert result['planned_phases'] == result['planned_outputs'] == 2
        if scenario in ['missing_native_history', 'sparse_failure']:
            assert error and result['status'] == 'TECH_BLOCKED_DENOMINATOR_PRESERVED'
            assert result['phases'][0]['status'].startswith('COMPLETE36_CFG72')
            assert result['phases'][1]['status'] == 'TECH_BLOCKED'
            checks.append({'flow': flow, 'scenario': scenario, 'error': error,
                           'first_phase_and_full_denominator_preserved': True})
            continue
        assert error is None, error
        assert len(observations) == 2
        assert all(p['solver_steps'] == 36 and p['CFG_calls'] == 72 and p['prepare_calls'] == 1
                   for p in result['phases'])
        assert all(tuple(r['deep_executed'] for r in p['trace']) == selected.dense_calls for p in result['phases'])
        assert [r['cache_counter_before'] for r in result['phases'][1]['trace']] == list(range(70)) + [0, 1]
        nine = {key: observations[0][key] == observations[1][key] for key in PARITY_KEYS}
        if scenario in ['same_mask_dense', 'changed_mask_dense']:
            assert all(nine.values())
            assert observations[0]['pipeline'] == observations[1]['pipeline']
            assert observations[0]['artifacts'] == observations[1]['artifacts']
            if scenario == 'same_mask_dense':
                assert all(reference[key] == observations[0][key] for key in PARITY_KEYS), ('cross_pair_difference', [key for key in PARITY_KEYS if reference[key] != observations[0][key]])
                assert reference['pipeline'] == observations[0]['pipeline']
        else:
            assert not nine['output_hashes'] and nine['trace'] and nine['block_counts']
        report = result['phases'][1]['refresh_provenance']
        assert report['online_policy'] is False and report['causal_refresh_value_labels'] is False
        events = report['events'];assert len(events) == 72 and events[69]['native_cycle_reset']
        assert not events[70]['references_read'] and not events[71]['references_read']
        assert all(e['fixed_diagnostic_mask'] and e['selected_fixed_skip'] == (not selected.dense_calls[i])
                   for i, e in enumerate(events))
        if scenario == 'changed_mask_dense':
            assert any(e['original_predicate_on_this_arm_state'] != e['selected_fixed_skip']
                       for e in events if e['original_predicate_on_this_arm_state'] is not None)
        sparse = [e for e in events if e['sparse_layers']]
        assert bool(sparse) == (scenario == 'fixed_sparse')
        if sparse:
            assert all(e['sparse_layers'] == [1, 3] and not e['inserted_into_true_dense_history'] for e in sparse)
            assert any(e['action'] == 'cache' and any(r['kind'] == 'sparse' for r in e['references_read']) for e in events)
        checks.append({'flow': flow, 'scenario': scenario, 'nine_CPU_checks': nine,
            'same_fixed_actions_actual36_72': True, 'reset_warm_tail_and_source_isolation': True,
            'dense_pipeline_equivalence': scenario != 'fixed_sparse',
            'CPU_output_stand_in_not_sparse_kernel': scenario == 'fixed_sparse'})
    return checks


def run(runtime):
    spec = importlib.util.spec_from_file_location('pinned_fixed_fixture', Path(__file__).with_name('check_full_sampling.py'))
    fixture = importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    result = fixture.run(runtime, exercise=exercise)
    result['status'] = 'FIXED_DIAGNOSTIC_PINNED_SAMPLER_CPU_CONTROL_PASS_NOT_GPU_FIDELITY'
    return result
