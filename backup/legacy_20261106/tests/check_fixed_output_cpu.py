"""Pinned four-output composition and denominator controls, no real video."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile

from wcomr.fixed_output import run_fixed_output
from wcomr.fixed_refresh_mask import FixedRefreshMask
from wcomr.light_sampling import Hooks
from wcomr.mid_coverage import tree_digest


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow):
    spec = importlib.util.spec_from_file_location('fixed_observer', Path(__file__).with_name('check_fixed_refresh_diagnostic_cpu.py'))
    observer = importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    context = ('CPU_FIXED_COMPOSE:human', 'toy', 'condition:human')
    source, rows, error = observer.observed_pair(inference, samples[1], wc, settings,
        inference_module, mode_setup, lambda kind, ctx: None, context)
    assert error is None
    calls = tuple(p['deep_executed'] for p in source['phases'][0]['trace'])
    mask = FixedRefreshMask('human', 'toy', 'condition:human', calls,
        hashlib.sha256(repr(calls).encode()).hexdigest())
    checks = []
    for scenario in ['complete_four', 'control_mask_mismatch', 'measurement_kernel_failure']:
        selected = mask
        if scenario == 'control_mask_mismatch':
            changed = list(calls); changed[14:16] = [True, True]; changed[22:24] = [False, False]
            selected = FixedRefreshMask('human', 'toy', 'condition:human', tuple(changed), mask.source_receipt_sha256)
        def operation(*args, **kwargs):
            value, metadata = kernel(*args, **kwargs)
            if scenario == 'measurement_kernel_failure':
                value = value.clone(); value.flatten()[0] = float('nan')
            return value, metadata
        state, error = {}, None
        sampler_returns = []
        hooks = Hooks()
        hooks.wrap(inference.pipe.model, 'generate_samples_from_batch',
                   after=lambda value: sampler_returns.append(tree_digest(value)))
        with tempfile.TemporaryDirectory(prefix='fixed-four-output-cpu-') as directory:
            try:
                run_fixed_output(inference, samples[1], wc, settings, selected,
                    state=state, save=lambda: None, output=Path(directory),
                    inference_module=inference_module, context=context, mode_setup=mode_setup,
                    fallback=(2,), kernel=operation, expected_video=(93, 16, 16))
            except ValueError as exc:
                error = str(exc)
            finally:
                hooks.close()
            assert state['planned_total_phases'] == state['planned_output_files'] == 4
            assert not hasattr(inference.pipe.model.net, '_wc_refresh_adapter')
            if scenario == 'complete_four':
                assert error is None, error
                assert state['status'] == 'FOUR_FIXED_DIAGNOSTIC_OUTPUTS_COMPLETE_REQUIRES_INDEPENDENT_AUDIT'
                assert len(list(Path(directory).rglob('*.mp4'))) == 4
                assert state['dense_control']['diagnostic_observers'] and not state['dense_control']['performance_sample']
                assert all(state['dense_control']['nine_checks'].values())
                assert all(state['dense_control']['pipeline_checks'].values())
                assert not state['measurement']['diagnostic_observers']
                phases = state['dense_control']['phases'] + state['measurement']['phases']
                assert all(p['prepare_calls'] == 1 and p['solver_steps'] == 36 and p['CFG_calls'] == 72 for p in phases)
                assert phases[0]['artifacts'] == phases[1]['artifacts'] == phases[2]['artifacts']
                # The toy decoder tanh can saturate and give identical mock
                # files despite different sampler latents. This is an interface
                # check; candidate encoded-video difference is not a requirement.
                assert len(sampler_returns) == 4
                assert sampler_returns[0] == sampler_returns[1] == sampler_returns[2]
                assert sampler_returns[2] != sampler_returns[3]
                assert not any(e['sparse_layers'] for e in phases[2]['refresh_provenance']['events'])
                assert any(e['sparse_layers'] for e in phases[3]['refresh_provenance']['events'])
                checks.append({'flow': flow, 'scenario': scenario, 'four_complete36_72_with_real_prepare_calls': 4,
                    'DD_nine_and_final_pipeline_pass': True, 'three_dense_artifacts_equal': True,
                    'measurement_observers_removed_source_cost_retained': True,
                    'CPU_sparse_stand_in_changes_sampler_return': True,
                    'mock_decoder_artifact_difference_is_not_required': True})
            else:
                assert error and state['status'] == 'TECH_BLOCKED_FIXED_FOUR_OUTPUT_DENOMINATOR_PRESERVED'
                if scenario == 'control_mask_mismatch':
                    assert not state['measurement']['phases']
                    assert state['dense_control']['status'] == 'TECH_BLOCKED_DD_MEASUREMENTS_NOT_STARTED'
                    assert len(list(Path(directory).rglob('*.mp4'))) == 2
                else:
                    assert state['dense_control']['status'] == 'FRESH_PREPARE_LIGHT_DD_NINE_AND_FINAL_PIPELINE_PASS'
                    assert len(state['measurement']['phases']) == 2
                    assert state['measurement']['phases'][0]['status'].startswith('COMPLETE36_CFG72')
                    assert state['measurement']['phases'][1]['status'] == 'TECH_BLOCKED'
                    assert len(list(Path(directory).rglob('*.mp4'))) == 3
                checks.append({'flow': flow, 'scenario': scenario, 'error': error,
                               'four_denominator_and_completed_artifacts_preserved': True})
    return checks


def run(runtime):
    spec = importlib.util.spec_from_file_location('pinned_fixed_four_fixture', Path(__file__).with_name('check_full_sampling.py'))
    fixture = importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    result = fixture.run(runtime, exercise=exercise)
    result['status'] = 'FIXED_FOUR_OUTPUT_COMPOSITION_CPU_PASS_NOT_GPU_VIDEO_OR_FIDELITY'
    return result
