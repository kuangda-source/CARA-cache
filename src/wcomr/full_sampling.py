"""Complete official sampling D/D control; no candidate policy or prefix stop.

This core runs the caller's real Inference.generate through its ordinary return.
CPU tests supply stand-ins at explicitly reported model/prepare/decode/write
boundaries. Equal hashes establish D/D control, never D/S quality acceptance.
"""
import hashlib
import time

import torch

from .decoder_policy import backend_flags, decode_policy
from .h0_mode import verify_shared_eval
from .measurement import BlockCounts
from .mid_coverage import StateRoundtrip, tree_digest
from .mid_prefix_audit import state_components
from .mid_scope import request_wc_gate
from .prepared_input import PreparedInputReplay, RNGState, input_signatures
from .stage_witness import StageWitness

PARITY_KEYS = ('input_hashes', 'output_hashes', 'trace', 'block_counts',
               'state_fingerprints', 'sampling', 'named_inputs', 'conditions',
               'field_signatures')
STATE_STEPS = [13, 21, 33, 35, 36]


class CompleteStateRoundtrip(StateRoundtrip):
    """Existing in-process state plus mutable net buffers and module modes.

    Conditioning and the sampler's closure remain live and unchanged. This is
    not a serialized pipeline, decoder-state checkpoint or independent fork.
    """
    def __init__(self, net, scheduler, output, generators=()):
        super().__init__(net, scheduler, output, generators)
        self.buffers = {name: (value, value.detach().clone())
                        for name, value in net.named_buffers()}
        self.modes = {name: (module, module.training)
                      for name, module in net.named_modules()}
        self.refresh_adapter = getattr(net, '_wc_refresh_adapter', None)
        self.refresh_state = self.refresh_adapter.snapshot() if self.refresh_adapter else None

    def components(self):
        values = state_components(self)
        values.update({'buffer.' + k: tree_digest(v) for k, v in self.net.named_buffers()})
        values.update({'mode.' + k: tree_digest(m.training)
                       for k, m in self.net.named_modules()})
        if self.refresh_adapter:
            values['refresh.provenance'] = tree_digest(self.refresh_adapter.report())
        return values

    def fingerprint(self):
        return tree_digest(self.components())

    def restore(self):
        value = super().restore()
        current = dict(self.net.named_buffers())
        modules = dict(self.net.named_modules())
        if set(current) != set(self.buffers) or set(modules) != set(self.modes):
            raise ValueError('Complete state buffer/module topology changed')
        with torch.no_grad():
            for name, (original, saved) in self.buffers.items():
                target = current[name]
                if (target is not original or target.shape != saved.shape
                        or target.dtype != saved.dtype or target.device != saved.device):
                    raise ValueError('Complete state buffer identity changed: ' + name)
                target.copy_(saved)
        for name, (original, training) in self.modes.items():
            if modules[name] is not original:
                raise ValueError('Complete state module identity changed: ' + name)
            modules[name].training = training
        if self.refresh_adapter:
            if getattr(self.net, '_wc_refresh_adapter', None) is not self.refresh_adapter:
                raise ValueError('Complete state refresh adapter identity changed')
            self.refresh_adapter.restore(self.refresh_state)
        return value


def run_full_sampling_batch(inference, samples, wc, settings, config, *, state,
                            save, output, inference_module, contexts, mode_setup,
                            adapter_factory=None):
    names = [sample.name for sample in samples]
    if (len(samples) != 2 or names != config['sample_names'] or len(contexts) != 2
            or any(len(c) != 3 for c in contexts)
            or [c[0] for c in contexts] != [config['run_id'] + ':' + n for n in names]
            or contexts[0][1] != contexts[1][1]
            or any(not isinstance(v, str) or not v for c in contexts for v in c)):
        raise ValueError('Complete sampling request/model identities differ')
    state.update(planned_requests=2, planned_phases=4,
                 planned_solver_updates_per_phase=36, planned_cfg_calls_per_phase=72,
                 requests=[])
    for sample, context in zip(samples, contexts):
        request = {'sample_name': sample.name, 'context': list(context),
                   'status': 'STARTED', 'phases': []}
        state['requests'].append(request)
        save()
        try:
            run_full_sampling_pair(inference, sample, wc, settings, config,
                state=request, save=save, output=output / sample.name,
                inference_module=inference_module, mode_setup=mode_setup,
                adapter_factory=adapter_factory, context=context)
            request['status'] = ('FULL36_CFG72_DD_FINAL_PIPELINE_CONTROL_PASS'
                if config.get('comparison_kind', 'dense_parity') == 'dense_parity'
                else 'FULL36_CFG72_CLOSED_LOOP_INTERFACE_PASS_NOT_QUALITY')
        except BaseException as error:
            request.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error))
            raise
        finally:
            save()
    state['status'] = ('REQUESTS2_FULL36_CFG72_DD_PIPELINE_CONTROL_PASS'
        if config.get('comparison_kind', 'dense_parity') == 'dense_parity'
        else 'REQUESTS2_FULL36_CFG72_CLOSED_LOOP_INTERFACE_PASS_NOT_QUALITY')
    save()


def run_full_sampling_pair(inference, sample, wc, settings, config, *, state, save,
                            output, inference_module, mode_setup,
                            adapter_factory=None, context=None):
    if (config['phases'] != ['baseline_full', 'restored_full']
            or config['state_steps'] != STATE_STEPS or sample.num_steps != 35):
        raise ValueError('Complete sampling scope changed')
    comparison = config.get('comparison_kind', 'dense_parity')
    if comparison not in ('dense_parity', 'closed_loop_interface'):
        raise ValueError('Unsupported full sampling comparison')
    if comparison == 'closed_loop_interface' and adapter_factory is None:
        raise ValueError('Closed loop requires explicit deployment adapter')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    common_rng = RNGState()
    prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
    owned, prior = '_get_data_batch_input' in vars(inference.pipe), vars(inference.pipe).get('_get_data_batch_input')
    forward_owned, forward_prior = 'forward' in vars(net), vars(net).get('forward')
    inference.pipe._get_data_batch_input = prepared
    parameters = [(p, p._version) for p in net.parameters()]
    initial_buffers = {name: value.detach().clone() for name, value in net.named_buffers()}

    def reset_buffers():
        current = dict(net.named_buffers())
        if set(current) != set(initial_buffers):
            raise ValueError('Shared initial net buffer topology changed')
        with torch.no_grad():
            for name, saved in initial_buffers.items():
                target = current[name]
                if target.shape != saved.shape or target.dtype != saved.dtype:
                    raise ValueError('Shared initial net buffer contract changed')
                target.copy_(saved.to(target.device))

    try:
        for phase in config['phases']:
            verify_shared_eval(net, mode_setup)
            common_rng.restore()
            reset_buffers()
            wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
            adapter = adapter_factory(phase, context) if adapter_factory else None
            if adapter is not None:
                adapter.install(net, wc)
            result = {'phase': phase, 'status': 'GENERATING_COMPLETE_SAMPLE',
                'input_hashes': [], 'output_hashes': [], 'named_inputs': [],
                'conditions': [], 'field_signatures': [], 'state_fingerprints': [],
                'refresh_field_signatures': [], 'roundtrips': [],
                'solver_steps': 0, 'flags_before': backend_flags()}
            state['phases'].append(result)
            counts = BlockCounts(net.blocks, cache_model=net)
            stages = StageWitness()
            call = step = 0
            original_forward, original_denoise = net.forward, model.denoise
            original_step = scheduler.step

            def forward(*args, **kwargs):
                nonlocal call
                call += 1
                if call == 1:
                    request_wc_gate(net, sample.num_steps, settings['probe_depth'])
                result['named_inputs'].append(input_signatures(args, kwargs))
                result['input_hashes'].append(tree_digest([x for x in
                    list(args) + list(kwargs.values()) if isinstance(x, torch.Tensor)]))
                value = original_forward(*args, **kwargs)
                result['output_hashes'].append(tree_digest(value))
                return value

            def denoise(*args, **kwargs):
                condition = kwargs.get('condition', args[3] if len(args) > 3 else None)
                if condition is None:
                    raise ValueError('Complete sampling condition missing')
                result['conditions'].append(input_signatures((), condition.to_dict(skip_underscore=False)))
                return original_denoise(*args, **kwargs)

            def solver_step(*args, **kwargs):
                nonlocal step
                value = original_step(*args, **kwargs)
                step += 1
                result['solver_steps'] = step
                if step in STATE_STEPS:
                    if not isinstance(value, tuple) or not value:
                        raise ValueError('Expected official return_dict=False tuple')
                    generator = kwargs.get('generator')
                    snapshot = CompleteStateRoundtrip(net, scheduler, value[0],
                        generators=[generator] if generator is not None else [])
                    before = snapshot.fingerprint()
                    components = snapshot.components()
                    refresh_signature = components.pop('refresh.provenance', None)
                    # Provenance is an extra sidecar, not an original native
                    # state field. Save it separately while the restoration
                    # fingerprint above still verifies native+sidecar together.
                    if refresh_signature is not None:
                        result['refresh_field_signatures'].append({'solver_step': step,
                            'call': call, 'sha256': refresh_signature})
                    result['field_signatures'].append({'solver_step': step, 'call': call,
                        'components': components})
                    if phase == 'restored_full':
                        restored = snapshot.restore()
                        if snapshot.fingerprint() != before or tree_digest(restored) != tree_digest(snapshot.output):
                            raise ValueError('Complete sampling roundtrip drift')
                        # The official caller actually continues from the restored
                        # latent, not the original still-live tuple's first item.
                        value = (restored,) + value[1:]
                        result['roundtrips'].append({'solver_step': step, 'call': call,
                            'status': 'RESTORED_LATENT_RETURNED_TO_OFFICIAL_SAMPLER'})
                    result['state_fingerprints'].append({'solver_step': step, 'call': call,
                        'sha256': tree_digest(components)})
                return value

            def input_event(name):
                return lambda args, kwargs: stages.record(name, args[0] if args else next(iter(kwargs.values())))

            stages.wrap(net, 'forward')
            net.forward = forward
            stages.wrap(model, 'denoise')
            model.denoise = denoise
            stages.wrap(scheduler, 'step')
            scheduler.step = solver_step
            stages.wrap(model, 'generate_samples_from_batch',
                after=lambda v: stages.record('sample_return', v))
            stages.wrap(model, 'decode', before=input_event('decode_input'),
                after=lambda v: stages.record('decode_output', v),
                call_context=lambda: decode_policy(True))
            stages.wrap(inference_module.guardrail_presets, 'run_video_guardrail',
                before=input_event('guardrail_input'),
                after=lambda v: stages.record('guardrail_output', v))
            stages.wrap(inference_module, 'save_img_or_video', before=input_event('save_input'))
            begin = time.perf_counter()
            try:
                paths = inference.generate([sample], output_dir=output / phase)
                if torch.cuda.is_initialized():
                    torch.cuda.synchronize()
                expected = output / phase / (sample.name + '.mp4')
                if paths != [str(expected)] or not expected.is_file() or not expected.stat().st_size:
                    raise ValueError('Complete generation missing expected output artifact')
                result.update(status='COMPLETE_SAMPLE_RETURNED', wall_seconds=time.perf_counter() - begin,
                    artifacts=[{'name': expected.name, 'bytes': expected.stat().st_size,
                                'sha256': hashlib.sha256(expected.read_bytes()).hexdigest()}],
                    pipeline_events=stages.events, flags_after=backend_flags(),
                    rng_after=RNGState().signatures())
                result['sampling'] = {'scheduler_class': type(scheduler).__name__,
                    'requested_steps': sample.num_steps, 'actual_schedule_steps': len(scheduler.timesteps),
                    'timesteps': scheduler.timesteps.cpu().tolist(),
                    'worldcache_horizon': net.worldcache_num_steps,
                    'use_kerras_sigma': model.config.use_kerras_sigma_at_inference}
                if step != 36 or call != 72 or len(counts.trace) != 72 or len(scheduler.timesteps) != 36:
                    raise ValueError('Complete36/72 sampling coverage differs')
                if not model.config.use_kerras_sigma_at_inference or net.worldcache_num_steps != 70:
                    raise ValueError('Official grid/horizon changed')
                if [p['cache_counter_before'] for p in counts.trace] != list(range(70)) + [0, 1]:
                    raise ValueError('Official70 counter reset and final two calls differ')
                if not all(p['deep_executed'] for p in counts.trace[-2:]):
                    raise ValueError('Official final two warm-start calls were not full')
                save()
            finally:
                result.update(actual_cfg_calls_entered=call, trace=counts.trace,
                              block_counts=counts.result(), pipeline_events=stages.events)
                stages.close()
                counts.close()
                if adapter:
                    result['refresh_provenance'] = adapter.report()
                    adapter.close()
                save()
            verify_shared_eval(net, mode_setup)
        state['prepared_input_calls'] = prepared.calls
        left, right = state['phases']
        state['all_gate_checks'] = {key: left[key] == right[key] for key in PARITY_KEYS}
        state['pipeline_checks'] = {key: left[key] == right[key]
            for key in ['pipeline_events', 'artifacts', 'flags_before', 'flags_after', 'rng_after']}
        state['shared_contract_checks'] = {
            'sampling': left['sampling'] == right['sampling'],
            'conditions': left['conditions'] == right['conditions'],
            'first_named_inputs': left['named_inputs'][0] == right['named_inputs'][0],
            'backend_flags': left['flags_before'] == right['flags_before']
                and left['flags_after'] == right['flags_after'],
            'rng_after': left['rng_after'] == right['rng_after'],
            'pipeline_stage_order': [p['stage'] for p in left['pipeline_events']]
                == [p['stage'] for p in right['pipeline_events']],
        }
        if (len(prepared.calls) != 2 or prepared.calls[0]['prepared'] != prepared.calls[1]['prepared']
                or not all(state['shared_contract_checks'].values())
                or (comparison == 'dense_parity' and (not all(state['all_gate_checks'].values())
                    or not all(state['pipeline_checks'].values())))):
            raise ValueError('Complete D/D state or final pipeline control differs')
        current_parameters = list(net.parameters())
        if (len(current_parameters) != len(parameters) or any(p is not original or p._version != version
                for p, (original, version) in zip(current_parameters, parameters))):
            raise ValueError('Complete sampling modified parameters')
    finally:
        state['prepared_input_calls'] = prepared.calls
        if forward_owned:
            net.forward = forward_prior
        else:
            delattr(net, 'forward')
        if owned:
            inference.pipe._get_data_batch_input = prior
        else:
            delattr(inference.pipe, '_get_data_batch_input')
        reset_buffers()
        save()
