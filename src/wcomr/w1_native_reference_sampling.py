"""Five complete ordinary Native references; no cache forward or replay.

Accepted/rejected outputs remain separate. Full video decode and LPIPS belong
to the CPU phase after GPU release. The independent GPU supervisor is pending.
"""
import hashlib
import json
from pathlib import Path
import time
import types


NATIVE_FORWARD = 'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward'


def official_native_forward(net):
    function = type(net).forward
    if function.__module__ + '.' + function.__qualname__ != NATIVE_FORWARD:
        raise ValueError('Official Native class method identity differs')
    return types.MethodType(function, net)


def run_native_request(inference, sample, *, state, save, output,
                       inference_module, sampling_policy, expected_flags,
                       synchronize, clock=time.perf_counter):
    from .decoder_policy import backend_flags, decode_policy
    from .guardrail_observation import GuardrailObservation
    from .light_sampling import Hooks, geometry
    from .measurement import BlockCounts
    from .protocol import validate_schedule
    net, model = inference.pipe.model.net, inference.pipe.model
    if (state.get('status') != 'STARTED' or output.exists() or sample.num_steps != 35
            or any(module.training for module in net.modules()) or backend_flags() != expected_flags):
        raise ValueError('Fresh complete35 Native reference/eval/backend identity differs')
    native = official_native_forward(net)
    own, prior = 'forward' in vars(net), vars(net).get('forward')
    missing = object()
    prior_enabled = getattr(net, 'worldcache_enabled', missing)
    pipe_enabled = inference.pipe.worldcache_enabled
    parameters = [(p, p._version) for p in net.parameters()]
    hooks, guards, counts = Hooks(), None, None
    state.update(CFG_calls=0, solver_steps=0, prepare_calls=0, pipeline_events=[],
                 official_forward_identity=NATIVE_FORWARD, worldcache_enabled=False,
                 fresh_prepare=True, checkpoint_restore=False, artifact=None,
                 full_frame_decode_status='PENDING_CPU_AFTER_GPU_RELEASE',
                 clean_speed_measurement=False, flags_before=backend_flags())
    save()
    try:
        # An old instance patch must never survive into the Native branch.
        inference.pipe.worldcache_enabled = False
        net.worldcache_enabled = False
        net.forward = native
        counts = BlockCounts(net.blocks, cache_model=net)
        guards = GuardrailObservation(inference_module.guardrail_presets)
        def before_forward(args, kwargs):
            if inference.pipe.worldcache_enabled or net.worldcache_enabled:
                raise ValueError('Native reference unexpectedly enabled cache')
            state['CFG_calls'] += 1
        hooks.wrap(net, 'forward', before=before_forward)
        hooks.wrap(model.sample_scheduler, 'step', after=lambda value:
                   state.update(solver_steps=state['solver_steps'] + 1))
        hooks.wrap(inference.pipe, '_get_data_batch_input', after=lambda value:
                   state.update(prepare_calls=state['prepare_calls'] + 1))
        def first(args, kwargs): return args[0] if args else next(iter(kwargs.values()))
        def event(name, value): state['pipeline_events'].append({'stage': name, 'value': geometry(value)})
        hooks.wrap(model, 'generate_samples_from_batch', after=lambda value: event('sample_return', value))
        hooks.wrap(model, 'decode', before=lambda a, k: event('decode_input', first(a, k)),
                   after=lambda value: event('decode_output', value), context=lambda: decode_policy(True))
        hooks.wrap(inference_module.guardrail_presets, 'run_video_guardrail',
                   before=lambda a, k: event('guardrail_input', first(a, k)),
                   after=lambda value: event('guardrail_output', value))
        hooks.wrap(inference_module, 'save_img_or_video', before=lambda a, k: event('save_input', first(a, k)))
        synchronize(); started = clock()
        try: paths = inference.generate([sample], output_dir=output)
        finally:
            synchronize(); state['pipeline_wall_seconds'] = clock() - started
        outcome = guards.classify(paths)
        state.update(outcome=outcome, guardrail_events=list(guards.events),
                     block_counts=counts.result(), trace=list(counts.trace), flags_after=backend_flags())
        save()  # Durable raw observation before a contract failure.
        if outcome == 'TEXT_REJECTED':
            if state['CFG_calls'] or state['solver_steps'] or state['prepare_calls'] or state['pipeline_events']:
                raise ValueError('Text rejection unexpectedly entered generation')
        else:
            scheduler = model.sample_scheduler
            state['sampling'] = {
                'scheduler_class': type(scheduler).__name__, 'requested_steps': sample.num_steps,
                'actual_schedule_steps': len(scheduler.timesteps),
                'timesteps': scheduler.timesteps.detach().cpu().tolist(),
                'use_kerras_sigma': model.config.use_kerras_sigma_at_inference,
                'worldcache_horizon': None,
            }
            validate_schedule(state['sampling'], state['block_counts'], sampling_policy, 'native')
            if ((state['CFG_calls'], state['solver_steps'], state['prepare_calls']) != (72, 36, 1)
                    or state['block_counts']['full_calls'] != 72
                    or not all(e['deep_executed'] for e in state['trace'])):
                raise ValueError('Native reference must execute every complete block group')
            labels = [e['stage'] for e in state['pipeline_events']]
            expected = ['sample_return', 'decode_input', 'decode_output', 'guardrail_input', 'guardrail_output']
            if outcome == 'ACCEPTED': expected.append('save_input')
            if labels != expected:
                raise ValueError('Native output pipeline order differs')
            events = state['pipeline_events']
            if (events[2]['value']['shape'] != [1, 3, 93, 432, 768]
                    or events[3]['value']['shape'] != [93, 432, 768, 3]
                    or (outcome == 'ACCEPTED' and
                        (events[4]['value']['shape'] != [93, 432, 768, 3]
                         or events[5]['value']['shape'] != [3, 93, 432, 768]))):
                raise ValueError('Complete Native output geometry differs')
        expected_path = output / (sample.name + '.mp4')
        if outcome == 'ACCEPTED':
            if paths != [str(expected_path)] or not expected_path.is_file() or not expected_path.stat().st_size:
                raise ValueError('Native accepted output artifact missing or replaced')
            state['artifact'] = {'path': str(expected_path), 'bytes': expected_path.stat().st_size,
                                 'sha256': hashlib.sha256(expected_path.read_bytes()).hexdigest()}
        elif paths or expected_path.exists():
            raise ValueError('Rejected Native reference was saved or substituted')
        if backend_flags() != expected_flags or any(p._version != version for p, version in parameters):
            raise ValueError('Native reference changed parameters or leaked backend flags')
        state['status'] = 'ACCEPTED_REQUIRES_CPU_FULL_DECODE' if outcome == 'ACCEPTED' else outcome
        save()
    except BaseException as exc:
        state.update(status='TECH_BLOCKED_NATIVE_REFERENCE', error_type=type(exc).__name__, error=str(exc))
        if counts is not None: state.update(block_counts=counts.result(), trace=list(counts.trace))
        if guards is not None: state['guardrail_events'] = list(guards.events)
        save(); raise
    finally:
        hooks.close()
        if guards is not None: guards.close()
        if counts is not None: counts.close()
        if own: net.forward = prior
        else: delattr(net, 'forward')
        inference.pipe.worldcache_enabled = pipe_enabled
        if prior_enabled is missing: delattr(net, 'worldcache_enabled')
        else: net.worldcache_enabled = prior_enabled
        save()


def run_native_batch(inference, samples, rows, *, state, save, output,
                     inference_module, sampling_policy, expected_flags, synchronize):
    from .w1_native_reference_scope import INDICES, NAMES
    if (tuple(r['original_CAL_index'] for r in rows) != INDICES
            or tuple(s.name for s in samples) != NAMES or tuple(r['scene'] for r in rows) != NAMES
            or state.get('cases') or output.exists()):
        raise ValueError('Exactly five fresh original missing Native references required')
    for sample, row in zip(samples, rows):
        if json.loads(sample.model_dump_json()) != row['request']:
            raise ValueError('Parsed request differs from original W1 request')
    state.update(planned_references=5, original_denominator=[8, 7, 1], cases=[],
                 original_rejected_sample_replaced=False, independent_confirmation=False,
                 GPU_scoring=False, status='GENERATING_NATIVE_REFERENCES')
    save()
    try:
        for sample, row in zip(samples, rows):
            case = {'sample_name': sample.name, 'original_CAL_index': row['original_CAL_index'],
                    'request': row['request'], 'status': 'STARTED'}
            state['cases'].append(case); save()
            run_native_request(inference, sample, state=case, save=save,
                output=output / sample.name, inference_module=inference_module,
                sampling_policy=sampling_policy, expected_flags=expected_flags,
                synchronize=synchronize)
        state.update(status='FIVE_REFERENCES_ATTEMPTED_REQUIRES_TERMINAL_AND_CPU_VIDEO_AUDIT',
                     accepted_references=sum(c['outcome'] == 'ACCEPTED' for c in state['cases']),
                     rejected_references=sum(c['outcome'] != 'ACCEPTED' for c in state['cases']))
        save()
    except BaseException as exc:
        state.update(status='TECH_BLOCKED_FIVE_REFERENCE_DENOMINATOR_PRESERVED',
                     error_type=type(exc).__name__, error=str(exc)); save(); raise
