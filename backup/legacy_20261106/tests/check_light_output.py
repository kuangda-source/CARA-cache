"""Pinned native-body CPU composition, not a kernel/video/speed benchmark."""
import importlib.util
from pathlib import Path
import tempfile

from wcomr.light_output import run_light_output


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow):
    model = inference.pipe.model
    original_decode = model.decode
    original_prepare = inference.pipe._get_data_batch_input
    initial_hooks = (len(model.net._forward_hooks), len(model.net._forward_pre_hooks))
    checks = []
    cases = ['ordinary'] if not flow else ['ordinary', 'DD_mismatch', 'second_request_decode_failure']
    for case in cases:
        config = {'run_id': 'CPU_LIGHT_OUTPUT', 'sample_names': [s.name for s in samples],
            'dense_fallback_layers': [2], 'measurement_sequences':
                [['official', 'candidate', 'candidate', 'official'],
                 ['candidate', 'official', 'official', 'candidate']]}
        count = [0]
        def prepare(*args, **kwargs):
            count[0] += 1
            return original_prepare(*args, **kwargs)
        def decode(*args, **kwargs):
            if case == 'second_request_decode_failure' and count[0] == 8:
                raise ValueError('CPU second request light decoder failure')
            value = original_decode(*args, **kwargs)
            if case == 'DD_mismatch' and count[0] == 2:
                return value + .01
            return value
        inference.pipe._get_data_batch_input = prepare
        model.decode = decode
        contexts = [('CPU_LIGHT_OUTPUT:' + s.name, 'toy_model', 'cond:' + s.name) for s in samples]
        state = {}
        error = None
        try:
            with tempfile.TemporaryDirectory(prefix='light-output-cpu-') as directory:
                try:
                    run_light_output(inference, samples, wc, settings, config,
                        state=state, save=lambda: None, output=Path(directory),
                        inference_module=inference_module, contexts=contexts,
                        mode_setup=mode_setup, kernel=kernel, expected_video=(93, 16, 16))
                except ValueError as exc:
                    error = str(exc)
                assert state['planned_total_phases'] == state['planned_output_files'] == 10
                dd = state['dense_control']
                if case == 'DD_mismatch':
                    assert error == 'Real fresh-prepare light D/D control differs'
                    assert dd['status'] == 'TECH_BLOCKED_DD_MEASUREMENTS_NOT_STARTED'
                    assert count[0] == 2 and not state['measurements']['requests']
                else:
                    assert dd['status'] == 'FRESH_PREPARE_LIGHT_DD_NINE_AND_FINAL_PIPELINE_PASS'
                    assert all(dd['nine_checks'].values()) and all(dd['pipeline_checks'].values())
                    requests = state['measurements']['requests']
                    assert len(requests) == 2
                    assert all(not r['diagnostic_observers'] and r['performance_sample'] for r in requests)
                    assert requests[0]['sequence'] == config['measurement_sequences'][0]
                    assert requests[1]['sequence'] == config['measurement_sequences'][1]
                    if case == 'ordinary':
                        assert error is None and count[0] == 10
                        assert state['status'] == 'TEN_OUTPUT_LIGHT_PIPELINE_COMPLETE_REQUIRES_INDEPENDENT_AUDIT'
                        for request in requests:
                            assert len(request['phases']) == 4
                            assert all(p['CFG_calls'] == 72 and p['solver_steps'] == 36
                                       and p['prepare_calls'] == 1 for p in request['phases'])
                            assert all(not p.get('observers') for p in request['phases'])
                            candidates = [p for p in request['phases'] if p['kind'] == 'candidate']
                            assert all(any(e['sparse_layers'] for e in p['refresh_provenance']['events']) for p in candidates)
                    else:
                        assert error == 'CPU second request light decoder failure' and count[0] == 8
                        assert state['status'] == 'TECH_BLOCKED_TEN_OUTPUT_DENOMINATOR_PRESERVED'
                        assert len(requests[0]['phases']) == 4 and requests[0]['status'].startswith('BALANCED_FOUR')
                        assert requests[1]['planned_phases'] == 4 and len(requests[1]['phases']) == 2
                        assert requests[1]['phases'][0]['status'].startswith('COMPLETE36')
                        assert requests[1]['phases'][1]['status'] == 'TECH_BLOCKED'
                assert (len(model.net._forward_hooks), len(model.net._forward_pre_hooks)) == initial_hooks
                assert not hasattr(model.net, '_wc_refresh_adapter')
                assert all(float(b) == 0 for b in model.net.buffers())
                checks.append({'flow': flow, 'case': case, 'prepare_calls': count[0],
                    'planned_outputs': 10, 'dense_control_status': dd['status'],
                    'measurement_requests': len(state['measurements']['requests']),
                    'all_observer_hooks_removed_before_measurements_and_after_return': True,
                    'ten_output_denominator_preserved': True, 'error': error})
        finally:
            model.decode = original_decode
            inference.pipe._get_data_batch_input = original_prepare
    return checks


def run(runtime):
    spec = importlib.util.spec_from_file_location('light_output_fixture', Path(__file__).with_name('check_full_sampling.py'))
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    result = fixture.run(runtime, exercise=exercise)
    result['status'] = 'TEN_OUTPUT_FRESH_PREPARE_LIGHT_COMPOSITION_CPU_PASS_NOT_VIDEO'
    return result
