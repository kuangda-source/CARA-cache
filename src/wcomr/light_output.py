"""Fresh-prepare dense control before balanced light deployment measurements."""
from contextlib import ExitStack
import torch

from .full_sampling import CompleteStateRoundtrip, PARITY_KEYS, STATE_STEPS
from .light_sampling import Hooks, run_light_pair
from .mid_coverage import tree_digest
from .prepared_input import input_signatures
from .refresh_deployment import SimpleRefreshAdapter
from .stage_witness import StageWitness


def run_light_dense_control(inference, sample, wc, settings, *, state, save, output,
                            inference_module, context, mode_setup, fallback,
                            expected_video=(93, 432, 768), adapter_factory=None):
    """Diagnostic observers apply only to these two unscored control outputs."""
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    rows, active = [], [None]
    hooks, stages = Hooks(), StageWitness()
    with ExitStack() as stack:
        stack.callback(stages.close)
        stack.callback(hooks.close)
        def prepared(value):
            row = {'prepared': input_signatures((), value), 'input_hashes': [],
                   'output_hashes': [], 'named_inputs': [], 'conditions': [],
                   'field_signatures': [], 'state_fingerprints': [], 'steps': 0,
                   'stage_start': len(stages.events)}
            rows.append(row)
            active[0] = row
        hooks.wrap(inference.pipe, '_get_data_batch_input', after=prepared)
        def before(module, args, kwargs):
            active[0]['named_inputs'].append(input_signatures(args, kwargs))
            active[0]['input_hashes'].append(tree_digest([v for v in
                list(args) + list(kwargs.values()) if isinstance(v, torch.Tensor)]))
        def after(module, args, kwargs, value):
            active[0]['output_hashes'].append(tree_digest(value))
        stack.callback(net.register_forward_pre_hook(before, with_kwargs=True).remove)
        stack.callback(net.register_forward_hook(after, with_kwargs=True).remove)
        def condition(args, kwargs):
            value = kwargs.get('condition', args[3] if len(args) > 3 else None)
            if value is None:
                raise ValueError('Light D/D condition missing')
            active[0]['conditions'].append(input_signatures((), value.to_dict(skip_underscore=False)))
        hooks.wrap(model, 'denoise', before=condition)
        def step(args, kwargs):
            active[0]['step_generators'] = [kwargs['generator']] if kwargs.get('generator') is not None else []
        def stepped(value):
            row = active[0]
            row['steps'] += 1
            if row['steps'] in STATE_STEPS:
                fields = CompleteStateRoundtrip(net, scheduler, value[0], row['step_generators']).components()
                fields.pop('refresh.provenance', None)
                row['field_signatures'].append({'solver_step': row['steps'], 'components': fields})
                row['state_fingerprints'].append(tree_digest(fields))
        hooks.wrap(scheduler, 'step', before=step, after=stepped)
        def first(args, kwargs):
            return args[0] if args else next(iter(kwargs.values()))
        stages.wrap(model, 'generate_samples_from_batch', after=lambda v: stages.record('sample_return', v))
        stages.wrap(model, 'decode', before=lambda a, k: stages.record('decode_input', first(a, k)),
                    after=lambda v: stages.record('decode_output', v))
        stages.wrap(inference_module.guardrail_presets, 'run_video_guardrail',
                    before=lambda a, k: stages.record('guardrail_input', first(a, k)),
                    after=lambda v: stages.record('guardrail_output', v))
        stages.wrap(inference_module, 'save_img_or_video',
                    before=lambda a, k: stages.record('save_input', first(a, k)))
        state['diagnostic_observers'] = True
        state['performance_sample'] = False
        try:
            run_light_pair(inference, sample, wc, settings, state=state, save=save,
                output=output, inference_module=inference_module, context=context,
                mode_setup=mode_setup, expected_video=expected_video,
                adapter_factory=adapter_factory or (lambda kind, ctx: None if kind == 'official' else
                    SimpleRefreshAdapter(ctx, fallback_layers=tuple(fallback))))
            if len(rows) != 2:
                raise ValueError('Light D/D fresh prepare coverage differs')
            for i, (row, phase) in enumerate(zip(rows, state['phases'])):
                row.pop('step_generators', None)
                end = rows[i + 1]['stage_start'] if i + 1 < len(rows) else len(stages.events)
                row['pipeline_witnesses'] = stages.events[row.pop('stage_start'):end]
                for key in ('trace', 'block_counts', 'sampling', 'artifacts', 'flags_before', 'flags_after', 'rng_after'):
                    row[key] = phase[key]
            state['nine_checks'] = {k: rows[0][k] == rows[1][k] for k in PARITY_KEYS}
            state['pipeline_checks'] = {k: rows[0][k] == rows[1][k] for k in
                ('prepared', 'pipeline_witnesses', 'artifacts', 'flags_before', 'flags_after', 'rng_after')}
            if (not all(state['nine_checks'].values()) or not all(state['pipeline_checks'].values())
                    or any(len(r['output_hashes']) != 72 or len(r['field_signatures']) != 5 for r in rows)):
                raise ValueError('Real fresh-prepare light D/D control differs')
            state['status'] = 'FRESH_PREPARE_LIGHT_DD_NINE_AND_FINAL_PIPELINE_PASS'
        except BaseException as error:
            state.update(status='TECH_BLOCKED_DD_MEASUREMENTS_NOT_STARTED',
                         error_type=type(error).__name__, error=str(error))
            raise
        finally:
            state['observers'] = rows
            save()


def run_light_output(inference, samples, wc, settings, config, *, state, save,
                     output, inference_module, contexts, mode_setup, kernel=None,
                     expected_video=(93, 432, 768)):
    if (len(samples) != 2 or [s.name for s in samples] != config['sample_names']
            or len(contexts) != 2 or [c[0] for c in contexts] !=
                [config['run_id'] + ':' + s.name for s in samples]
            or contexts[0][1] != contexts[1][1]):
        raise ValueError('Light complete request/model bindings differ')
    state.update(planned_total_phases=10, planned_output_files=10,
        dense_control={'status': 'NOT_STARTED', 'phases': []},
        measurements={'status': 'NOT_STARTED_DD_PENDING', 'requests': []})
    save()
    run_light_dense_control(inference, samples[0], wc, settings,
        state=state['dense_control'], save=save, output=output / 'dense-control',
        inference_module=inference_module, context=contexts[0], mode_setup=mode_setup,
        fallback=config['dense_fallback_layers'], expected_video=expected_video)
    def factory(kind, context):
        return None if kind == 'official' else SimpleRefreshAdapter(context,
            sparse=True, fallback_layers=tuple(config['dense_fallback_layers']), kernel=kernel)
    try:
        for sample, ctx, sequence in zip(samples, contexts, config['measurement_sequences']):
            request = {'sample_name': sample.name, 'status': 'STARTED', 'phases': [],
                       'diagnostic_observers': False, 'performance_sample': True}
            state['measurements']['requests'].append(request)
            save()
            run_light_pair(inference, sample, wc, settings, state=request, save=save,
                output=output / 'measurement' / sample.name, inference_module=inference_module,
                context=ctx, mode_setup=mode_setup, adapter_factory=factory,
                sequence=sequence, expected_video=expected_video)
            request['status'] = 'BALANCED_FOUR_COMPLETE_OUTPUTS_REQUIRES_METRICS'
            save()
        state['measurements']['status'] = 'EIGHT_LIGHT_MEASUREMENTS_COMPLETE_NOT_SPEED_OR_QUALITY_ACCEPTANCE'
        state['status'] = 'TEN_OUTPUT_LIGHT_PIPELINE_COMPLETE_REQUIRES_INDEPENDENT_AUDIT'
    except BaseException as error:
        state.update(status='TECH_BLOCKED_TEN_OUTPUT_DENOMINATOR_PRESERVED',
                     error_type=type(error).__name__, error=str(error))
        raise
    finally:
        save()
