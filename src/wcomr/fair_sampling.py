"""Complete official Native/short Native/tuned WC/stage sampling, no shadow hashes."""
import hashlib
import math
import time
import types

import torch

from .decoder_policy import backend_flags, decode_policy
from .fair_workpoints import validate_workpoints
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, geometry, synchronize
from .measurement import BlockCounts
from .mid_scope import request_wc_gate
from .prepared_input import RNGState
from .stage_refresh import StageRefreshAdapter
from .stage_refresh_policy import StageRefreshPolicy


NATIVE_FORWARD = 'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'


def native_forward(net):
    # The class method survives an instance-level WorldCache patch. Setting
    # only pipe.worldcache_enabled=False would keep executing that patch.
    function = type(net).forward
    identity = function.__module__ + '.' + function.__qualname__
    if identity != NATIVE_FORWARD:
        raise ValueError('Pinned official Native LVG class forward identity differs')
    return types.MethodType(function, net)


def run_fair_request(inference, sample, wc, settings, points, policy, *, state,
                     save, output, inference_module, context, mode_setup,
                     fallback=(6, 23, 27), kernel=None, expected_video=(93, 432, 768),
                     expected_WC_sha256=None, sync=synchronize, clock=time.perf_counter):
    validate_workpoints(points)
    if (sample.num_steps != 35 or type(policy) is not StageRefreshPolicy
            or (policy.every, policy.first_solver_step, policy.last_solver_step) != (1, 23, 27)
            or type(context) is not tuple or len(context) != 3
            or any(type(v) is not str or not v for v in context)
            or len(expected_video) != 3 or expected_video[0] != 93
            or any(type(v) is not int or v <= 0 for v in expected_video)
            or state.get('phases')
            or not callable(getattr(sample, 'model_copy', None))):
        raise ValueError('Explicit fresh complete fair request scope differs')
    if expected_WC_sha256 is not None and (type(expected_WC_sha256) is not str
            or len(expected_WC_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_WC_sha256)):
        raise ValueError('Historical WC006 bridge SHA differs')
    model, net = inference.pipe.model, inference.pipe.model.net
    original_native = native_forward(net)
    verify_shared_eval(net, mode_setup)
    group = tuple(v for v in range(settings['probe_depth'], len(net.blocks)) if v not in fallback)
    if group != policy.sparse_layers or settings['worldcache_rel_l1_thresh'] != .06:
        raise ValueError('Stage group or common WC006 settings differ')
    scheduler, rng = model.sample_scheduler, RNGState()
    own_forward, prior_forward = 'forward' in vars(net), vars(net).get('forward')
    pipe_enabled = inference.pipe.worldcache_enabled
    missing = object()
    configuration = {name: getattr(net,name,missing) for name in
                     set(settings) | {'worldcache_enabled'}}
    parameters = [(p, p._version) for p in net.parameters()]
    buffers = {n: (b, b.detach().clone()) for n, b in net.named_buffers()}
    state.update(planned_phases=6, planned_outputs=6, phases=[],
                 workpoints=[p.to_dict() for p in points], context=list(context),
                 native_forward_identity=NATIVE_FORWARD,
                 fresh_prepare_per_phase=True, checkpoint_restore=False,
                 diagnostic_observers=False, per_forward_tensor_diagnostic_hashes=False,
                 refresh_ledger_and_kernel_checks_counted_in_wall=True,
                 timing_wrappers_CUDA_boundary_sync_only=True,
                 expected_video=list(expected_video), quality_acceptance=False,
                 clean_E2E_speed_claim=False)
    save()

    def reset_buffers():
        current = dict(net.named_buffers())
        if set(current) != set(buffers):
            raise ValueError('Fair initial buffer topology changed')
        with torch.no_grad():
            for name, (original, saved) in buffers.items():
                target = current[name]
                if target is not original or (target.shape, target.dtype, target.device) != (saved.shape, saved.dtype, saved.device):
                    raise ValueError('Fair initial buffer contract changed')
                target.copy_(saved)

    try:
        for index, point in enumerate(points):
            result = {'index': index, 'workpoint': point.to_dict(), 'status': 'STARTED',
                      'solver_steps': 0, 'CFG_calls': 0, 'prepare_calls': 0,
                      'pipeline_events': [], 'substage_host_wall': {},
                      'substage_cuda_isolated': False}
            state['phases'].append(result); save()
            hooks, counts, adapter = Hooks(), None, None
            try:
                verify_shared_eval(net, mode_setup)
                rng.restore(); reset_buffers()
                effective = sample.model_copy(update={'num_steps': point.requested_steps})
                if effective is sample or sample.num_steps != 35 or effective.num_steps != point.requested_steps:
                    raise ValueError('Fair workpoint sample copy mutated base request')
                phase_settings = dict(settings)
                if point.mode != 'native':
                    phase_settings['worldcache_rel_l1_thresh'] = point.threshold
                # Apply only as a common state reset before Native; immediately
                # replace its patched forward with the exact official class body.
                # No Native forward can execute WorldCache, probe, Gamma or warp.
                wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in phase_settings.items()})
                enabled = point.mode != 'native'
                inference.pipe.worldcache_enabled = enabled
                if not enabled:
                    net.worldcache_enabled = False
                    net.forward = original_native
                elif point.mode == 'stage':
                    if expected_WC_sha256 is not None and state['phases'][3]['artifacts'][0]['sha256'] != expected_WC_sha256:
                        raise ValueError('Historical WC006 output failed before stage candidate')
                    adapter = StageRefreshAdapter(context, policy, sparse=True,
                                                  fallback_layers=fallback, kernel=kernel)
                    adapter.install(net, wc)
                result['worldcache_enabled'] = enabled
                result['base_forward_identity'] = (NATIVE_FORWARD if not enabled else
                    wc.worldcache_mini_train_dit_forward.__module__ + '.' + wc.worldcache_mini_train_dit_forward.__qualname__)
                counts = BlockCounts(net.blocks, cache_model=net)
                def before_forward(args, kwargs):
                    result['CFG_calls'] += 1
                    if result['CFG_calls'] == 1 and enabled:
                        request_wc_gate(net, effective.num_steps, settings['probe_depth'])
                        if net.worldcache_rel_l1_thresh != point.threshold:
                            raise ValueError('Actual fair WC threshold differs from declared intervention')
                hooks.wrap(net, 'forward', before=before_forward)
                hooks.wrap(scheduler, 'step', after=lambda value:
                           result.update(solver_steps=result['solver_steps'] + 1))
                def event(name, value):
                    result['pipeline_events'].append({'stage': name, 'value': geometry(value)})
                def first(args, kwargs):
                    return args[0] if args else next(iter(kwargs.values()))
                def host_stage(owner, name, label, before=None, after=None, call_context=None):
                    def start(args, kwargs):
                        if before: before(args, kwargs)
                        stamps.append(clock())
                    stamps = []
                    def finish(value):
                        started = stamps.pop()
                        row = result['substage_host_wall'].setdefault(label, {'calls': 0, 'seconds': 0.0})
                        row['calls'] += 1; row['seconds'] += clock() - started
                        if after: after(value)
                    hooks.wrap(owner, name, before=start, after=finish, context=call_context)
                host_stage(inference.pipe, '_get_data_batch_input', 'prepare',
                           after=lambda value: result.update(prepare_calls=result['prepare_calls'] + 1))
                host_stage(model, 'generate_samples_from_batch', 'sample', after=lambda value: event('sample_return', value))
                host_stage(model, 'decode', 'decode', before=lambda a,k: event('decode_input', first(a,k)),
                           after=lambda value: event('decode_output', value), call_context=lambda: decode_policy(True))
                host_stage(inference_module.guardrail_presets, 'run_video_guardrail', 'video_guardrail',
                           before=lambda a,k: event('guardrail_input', first(a,k)),
                           after=lambda value: event('guardrail_output', value))
                host_stage(inference_module, 'save_img_or_video', 'write', before=lambda a,k: event('save_input', first(a,k)))
                result['flags_before'] = backend_flags()
                phase_dir = output / (str(index).zfill(3) + '_' + point.name)
                sync(); started = clock()
                try:
                    paths = inference.generate([effective], output_dir=phase_dir)
                finally:
                    sync(); result['pipeline_wall_seconds'] = clock() - started
                expected = phase_dir / (sample.name + '.mp4')
                if paths != [str(expected)] or not expected.is_file() or not expected.stat().st_size:
                    raise ValueError('Fair complete generation missing expected output artifact')
                updates = point.requested_steps + 1
                result['sampling'] = {'requested_steps': effective.num_steps,
                    'actual_schedule_steps': len(scheduler.timesteps),
                    'timesteps': scheduler.timesteps.cpu().tolist(),
                    'worldcache_horizon': net.worldcache_num_steps if enabled else None,
                    'use_kerras_sigma': model.config.use_kerras_sigma_at_inference}
                if (result['solver_steps'] != updates or result['CFG_calls'] != 2 * updates
                        or len(scheduler.timesteps) != updates or result['prepare_calls'] != 1
                        or not model.config.use_kerras_sigma_at_inference):
                    raise ValueError('Fair complete schedule/CFG/fresh prepare differs')
                if enabled:
                    if (net.worldcache_num_steps != 70 or net.worldcache_rel_l1_thresh != point.threshold
                            or [v['cache_counter_before'] for v in counts.trace] != list(range(70)) + [0,1]
                            or not all(v['deep_executed'] for v in counts.trace[-2:])):
                        raise ValueError('Fair WC70 threshold or dense tail differs')
                elif counts.result()['full_calls'] != 2 * updates:
                    raise ValueError('Native did not execute all deep CFG calls')
                events = result['pipeline_events']
                if [e['stage'] for e in events] != ['sample_return','decode_input','decode_output',
                                                   'guardrail_input','guardrail_output','save_input']:
                    raise ValueError('Fair ordinary pipeline order differs')
                frames,height,width = expected_video
                shapes = [[1,3,frames,height,width],[frames,height,width,3],
                          [frames,height,width,3],[3,frames,height,width]]
                if [e['value']['shape'] for e in events[2:]] != shapes:
                    raise ValueError('Fair full93 output geometry differs')
                if not math.isfinite(result['pipeline_wall_seconds']) or result['pipeline_wall_seconds'] <= 0:
                    raise ValueError('Fair complete wall is nonfinite or nonpositive')
                result['artifacts'] = [{'name': expected.name, 'bytes': expected.stat().st_size,
                    'sha256': hashlib.sha256(expected.read_bytes()).hexdigest()}]
                if point.name == 'wc006' and expected_WC_sha256 is not None and result['artifacts'][0]['sha256'] != expected_WC_sha256:
                    raise ValueError('Historical WC006 output failed; no stage candidate')
                result['flags_after'] = backend_flags(); result['rng_after'] = RNGState().signatures()
                verify_shared_eval(net, mode_setup)
                current = list(net.parameters())
                if len(current) != len(parameters) or any(p is not old or p._version != version
                        for p,(old,version) in zip(current,parameters)):
                    raise ValueError('Fair workpoints modified model parameters')
                result['status'] = 'COMPLETE_FULL93_WORKPOINT_NOT_QUALITY_OR_SPEED_ACCEPTANCE'
            except BaseException as exc:
                result.update(status='TECH_BLOCKED', error_type=type(exc).__name__, error=str(exc))
                state['status'] = 'TECH_BLOCKED_FAIR_SIX_WORKPOINT_DENOMINATOR_PRESERVED'
                raise
            finally:
                if counts: result.update(trace=counts.trace, block_counts=counts.result())
                try: hooks.close()
                finally:
                    if counts: counts.close()
                    if adapter:
                        result['refresh_provenance'] = adapter.report(); adapter.close()
                    save()
        state['status'] = 'SIX_COMPLETE_NATIVE_FEWER_STEP_TUNED_WC_STAGE_OUTPUTS_REQUIRE_AUDIT_METRICS'
    finally:
        inference.pipe.worldcache_enabled = pipe_enabled
        if own_forward: net.forward = prior_forward
        elif 'forward' in vars(net): delattr(net,'forward')
        for name,value in configuration.items():
            if value is missing:
                if hasattr(net,name): delattr(net,name)
            else: setattr(net,name,value)
        reset_buffers(); save()
