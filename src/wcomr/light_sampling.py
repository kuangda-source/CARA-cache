"""Complete ordinary generation with fresh prepare and lightweight timing.

This removes full_sampling's shadow hashes, PreparedInputReplay and checkpoint
copies. Necessary refresh provenance and kernel checks stay in the adapter.
CPU fixture parity is wiring evidence, never GPU speed or quality acceptance.
"""
from contextlib import ExitStack, nullcontext
import functools
import hashlib
import time

import torch

from .decoder_policy import backend_flags, decode_policy
from .h0_mode import verify_shared_eval
from .measurement import BlockCounts
from .mid_scope import request_wc_gate
from .prepared_input import RNGState


class Hooks:
    def __init__(self):
        self.stack = ExitStack()

    def wrap(self, owner, name, before=None, after=None, context=None):
        original = getattr(owner, name)
        own, prior = name in vars(owner), vars(owner).get(name)
        def restore():
            if own:
                setattr(owner, name, prior)
            else:
                delattr(owner, name)
        self.stack.callback(restore)
        @functools.wraps(original)
        def wrapped(*args, **kwargs):
            if before:
                before(args, kwargs)
            with context() if context else nullcontext():
                result = original(*args, **kwargs)
            if after:
                after(result)
            return result
        setattr(owner, name, wrapped)

    def close(self):
        self.stack.close()


def geometry(value):
    if value is None:
        return None
    return {'shape': list(value.shape), 'dtype': str(value.dtype)}


def synchronize():
    if torch.cuda.is_initialized():
        torch.cuda.synchronize()


def run_light_pair(inference, sample, wc, settings, *, state, save, output,
                   inference_module, context, mode_setup, adapter_factory=None,
                   sequence=('official', 'candidate'), expected_video=(93, 432, 768),
                   sync=synchronize, clock=time.perf_counter, sequence_policy='balanced'):
    """Each phase calls real prepare; setup/reset and artifact SHA are outside wall.

    Substage numbers are unsynchronized host wall; only the complete pipeline
    has CUDA boundary synchronization. For GPU admission a separate frozen card
    and a real full-output parity gate remain necessary.
    """
    if (sample.num_steps != 35 or type(sequence) not in (tuple, list)
            or not sequence or set(sequence) != {'official', 'candidate'}
            or sequence_policy not in ('balanced', 'reference_then_candidates')
            or (sequence_policy == 'balanced' and sequence.count('official') != sequence.count('candidate'))
            or (sequence_policy == 'reference_then_candidates' and
                (sequence[0] != 'official' or sequence.count('official') != 1))
            or any(v not in ('official', 'candidate') for v in sequence)
            or type(context) is not tuple or len(context) != 3
            or any(not isinstance(v, str) or not v for v in context)
            or len(expected_video) != 3 or expected_video[0] != 93
            or any(type(v) is not int or v <= 0 for v in expected_video)):
        raise ValueError('Explicit complete35/93 light-pair contract differs')
    if state.get('phases'):
        raise ValueError('Existing light phase identity; inspect instead of rerun')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    verify_shared_eval(net, mode_setup)
    rng = RNGState()
    parameters = [(p, p._version) for p in net.parameters()]
    buffers = {n: (b, b.detach().clone()) for n, b in net.named_buffers()}
    own_forward, prior_forward = 'forward' in vars(net), vars(net).get('forward')
    state.update(planned_phases=len(sequence), planned_outputs=len(sequence),
                 sequence=list(sequence), phases=[], fresh_prepare_per_phase=True,
                 checkpoint_restore=False, per_forward_tensor_diagnostic_hashes=False,
                 refresh_condition_content_hashes_retained=True,
                 refresh_ledger_and_kernel_checks_counted_in_wall=True,
                 timing_wrappers_CUDA_boundary_sync_only=True, expected_video=list(expected_video),
                 context=list(context), clean_E2E_speed_claim=False)
    if sequence_policy != 'balanced':
        state['sequence_policy'] = sequence_policy
    save()

    def reset_buffers():
        current = dict(net.named_buffers())
        if set(current) != set(buffers):
            raise ValueError('Light initial buffer topology changed')
        with torch.no_grad():
            for name, (original, saved) in buffers.items():
                target = current[name]
                if target is not original or (target.shape, target.dtype, target.device) != (saved.shape, saved.dtype, saved.device):
                    raise ValueError('Light initial buffer contract changed')
                target.copy_(saved)

    try:
        for index, kind in enumerate(sequence):
            result = {'index': index, 'kind': kind, 'status': 'STARTED', 'solver_steps': 0,
                      'CFG_calls': 0, 'prepare_calls': 0, 'pipeline_events': [],
                      'substage_host_wall': {}, 'substage_cuda_isolated': False}
            state['phases'].append(result)
            save()
            adapter, hooks, counts = None, Hooks(), None
            try:
                verify_shared_eval(net, mode_setup)
                rng.restore()
                reset_buffers()
                wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
                adapter = adapter_factory(kind, context) if adapter_factory else None
                if adapter:
                    adapter.install(net, wc)
                counts = BlockCounts(net.blocks, cache_model=net)
                def counted_forward(args, kwargs):
                    result['CFG_calls'] += 1
                    if result['CFG_calls'] == 1:
                        request_wc_gate(net, sample.num_steps, settings['probe_depth'])
                hooks.wrap(net, 'forward', before=counted_forward)
                hooks.wrap(scheduler, 'step', after=lambda value:
                           result.update(solver_steps=result['solver_steps'] + 1))
                def event(name, value):
                    result['pipeline_events'].append({'stage': name, 'value': geometry(value)})
                def first_value(args, kwargs):
                    return args[0] if args else next(iter(kwargs.values()))
                # Timing wrappers do not synchronize GPU work at substage boundaries.
                def host_stage(owner, name, label, before=None, after=None, call_context=None):
                    original = getattr(owner, name)
                    own, prior = name in vars(owner), vars(owner).get(name)
                    def restore():
                        if own: setattr(owner, name, prior)
                        else: delattr(owner, name)
                    hooks.stack.callback(restore)
                    @functools.wraps(original)
                    def measured(*args, **kwargs):
                        if before: before(args, kwargs)
                        start = clock()
                        try:
                            with call_context() if call_context else nullcontext():
                                value = original(*args, **kwargs)
                            if after: after(value)
                            return value
                        finally:
                            row = result['substage_host_wall'].setdefault(label, {'calls': 0, 'seconds': 0.0})
                            row['calls'] += 1
                            row['seconds'] += clock() - start
                    setattr(owner, name, measured)
                def prepared(value):
                    result['prepare_calls'] += 1
                host_stage(inference.pipe, '_get_data_batch_input', 'prepare', after=prepared)
                host_stage(model, 'generate_samples_from_batch', 'sample',
                           after=lambda v: event('sample_return', v))
                host_stage(model, 'decode', 'decode',
                           before=lambda a, k: event('decode_input', first_value(a, k)),
                           after=lambda v: event('decode_output', v), call_context=lambda: decode_policy(True))
                host_stage(inference_module.guardrail_presets, 'run_video_guardrail', 'video_guardrail',
                           before=lambda a, k: event('guardrail_input', first_value(a, k)),
                           after=lambda v: event('guardrail_output', v))
                host_stage(inference_module, 'save_img_or_video', 'write',
                           before=lambda a, k: event('save_input', first_value(a, k)))
                result['flags_before'] = backend_flags()
                phase_dir = output / (str(index).zfill(3) + '_' + kind)
                sync()
                start = clock()
                try:
                    paths = inference.generate([sample], output_dir=phase_dir)
                finally:
                    sync()
                    result['pipeline_wall_seconds'] = clock() - start
                expected = phase_dir / (sample.name + '.mp4')
                if paths != [str(expected)] or not expected.is_file() or not expected.stat().st_size:
                    raise ValueError('Light complete generation missing expected output artifact')
                result['sampling'] = {'requested_steps': sample.num_steps,
                    'actual_schedule_steps': len(scheduler.timesteps),
                    'timesteps': scheduler.timesteps.cpu().tolist(),
                    'worldcache_horizon': net.worldcache_num_steps,
                    'use_kerras_sigma': model.config.use_kerras_sigma_at_inference}
                if (result['solver_steps'] != 36 or result['CFG_calls'] != 72
                        or result['sampling']['actual_schedule_steps'] != 36
                        or net.worldcache_num_steps != 70 or not model.config.use_kerras_sigma_at_inference
                        or result['prepare_calls'] != 1
                        or [v['cache_counter_before'] for v in counts.trace] != list(range(70)) + [0, 1]
                        or not all(v['deep_executed'] for v in counts.trace[-2:])):
                    raise ValueError('Light complete36/72, fresh prepare or native70 tail differs')
                events = result['pipeline_events']
                if [v['stage'] for v in events] != ['sample_return', 'decode_input', 'decode_output',
                                                  'guardrail_input', 'guardrail_output', 'save_input']:
                    raise ValueError('Light ordinary pipeline order differs')
                frames, height, width = expected_video
                if (events[2]['value']['shape'] != [1, 3, frames, height, width]
                        or events[3]['value']['shape'] != [frames, height, width, 3]
                        or events[4]['value']['shape'] != [frames, height, width, 3]
                        or events[5]['value']['shape'] != [3, frames, height, width]):
                    raise ValueError('Light complete output geometry differs')
                result['artifacts'] = [{'name': expected.name, 'bytes': expected.stat().st_size,
                    'sha256': hashlib.sha256(expected.read_bytes()).hexdigest()}]
                result['flags_after'] = backend_flags()
                result['rng_after'] = RNGState().signatures()
                verify_shared_eval(net, mode_setup)
                current = list(net.parameters())
                if len(current) != len(parameters) or any(p is not old or p._version != version
                        for p, (old, version) in zip(current, parameters)):
                    raise ValueError('Light pair modified model parameters')
                result['status'] = 'COMPLETE36_CFG72_ORDINARY_RETURN_NO_QUALITY_ACCEPTANCE'
            except BaseException as exc:
                result.update(status='TECH_BLOCKED', error_type=type(exc).__name__, error=str(exc))
                state['status'] = 'TECH_BLOCKED_DENOMINATOR_PRESERVED'
                raise
            finally:
                if counts:
                    result.update(trace=counts.trace, block_counts=counts.result())
                try:
                    hooks.close()
                finally:
                    if counts: counts.close()
                    if adapter:
                        result['refresh_provenance'] = adapter.report()
                        adapter.close()
                    save()
        state['status'] = 'COMPLETE_LIGHT_PIPELINE_INTERFACE_REQUIRES_GPU_PARITY_AND_METRICS'
    finally:
        if own_forward: net.forward = prior_forward
        elif 'forward' in vars(net): delattr(net, 'forward')
        reset_buffers()
        save()
