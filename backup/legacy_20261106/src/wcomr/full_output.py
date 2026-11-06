"""Six complete generations: official/dense-adapter gate before two WC/S pairs."""
from .full_sampling import run_full_sampling_batch, run_full_sampling_pair
from .refresh_deployment import SimpleRefreshAdapter


def run_full_output(inference, samples, wc, settings, config, *, state, save,
                    output, inference_module, contexts, mode_setup, kernel=None):
    if (len(samples) != 2 or [s.name for s in samples] != config['sample_names']
            or len(contexts) != 2 or [v[0] for v in contexts]
                != [config['run_id'] + ':' + s.name for s in samples]
            or contexts[0][1] != contexts[1][1]):
        raise ValueError('Complete six-output request/model binding differs')
    state.update(planned_total_phases=6, planned_output_files=6,
        planned_comparison_requests=2, dense_control={'status': 'STARTED', 'phases': []},
        comparison={'status': 'NOT_STARTED_DD_GATE_PENDING', 'requests': []})
    save()
    dense_config = dict(config, comparison_kind='dense_parity')
    def dense_factory(phase, context):
        return (None if phase == 'baseline_full' else
            SimpleRefreshAdapter(context, fallback_layers=tuple(config['dense_fallback_layers'])))
    run_full_sampling_pair(inference, samples[0], wc, settings, dense_config,
        state=state['dense_control'], save=save, output=output / 'dense-control' / samples[0].name,
        inference_module=inference_module, mode_setup=mode_setup,
        adapter_factory=dense_factory, context=contexts[0])
    state['dense_control']['status'] = 'OFFICIAL_DENSE_ADAPTER_FULL_PIPELINE_DD_GATE_PASS'
    save()
    def sparse_factory(phase, context):
        return (None if phase == 'baseline_full' else SimpleRefreshAdapter(context,
            sparse=True, fallback_layers=tuple(config['dense_fallback_layers']), kernel=kernel))
    run_full_sampling_batch(inference, samples, wc, settings,
        dict(config, comparison_kind='closed_loop_interface'), state=state['comparison'],
        save=save, output=output / 'comparison', inference_module=inference_module,
        contexts=contexts, mode_setup=mode_setup, adapter_factory=sparse_factory)
    state['status'] = 'COMPLETE_DD_GATE_AND_TWO_WC_S_OUTPUT_PAIRS_REQUIRES_ARTIFACT_AUDIT'
    save()
