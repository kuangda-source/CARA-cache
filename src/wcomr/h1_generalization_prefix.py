"""Production early/late H1 paired-prefix execution; no changes to sealed r1 core."""
import time

import torch

from .h0_mode import verify_shared_eval
from .h1_lifetime import build_h1_forward
from .h1_generalization import H1GeneralizationProbe, select_sources
from .measurement import BlockCounts
from .mid_coverage import StateRoundtrip, PrefixComplete, tree_digest, compare_prefix
from .mid_prefix_audit import state_components
from .mid_scope import request_wc_gate
from .prepared_input import RNGState, PreparedInputReplay, input_signatures

PARITY_KEYS = ('input_hashes', 'output_hashes', 'trace', 'block_counts',
               'state_fingerprints', 'sampling', 'named_inputs', 'conditions',
               'field_signatures')


def run_h1_generalization_batch(inference, samples, wc, settings, config, *, state,
                                save, output, contexts, mode_setup, kernel=None):
    """One loaded model, two requests; every planned slot remains on failure."""
    if (len(samples) != 2 or [sample.name for sample in samples] != config['sample_names']
            or len(contexts) != 2 or any(len(context) != 3 for context in contexts)
            or [context[0] for context in contexts] != [config['run_id'] + ':' + name
                                                       for name in config['sample_names']]
            or contexts[0][1] != contexts[1][1]
            or any(not isinstance(value, str) or not value for context in contexts for value in context)):
        raise ValueError('Two-request sample/model/condition identities differ')
    if (state['planned_source_denominator'] != 24 or state['planned_lifetime_denominator'] != 72
            or state['planned_raw_files'] != 120):
        raise ValueError('Complete batch denominators changed before first request')
    state['requests'] = []
    for sample, context in zip(samples, contexts):
        request = {'sample_name': sample.name, 'status': 'STARTED', 'phases': [],
                   'reference_context': list(context), 'planned_source_denominator': 12,
                   'planned_lifetime_denominator': 36, 'planned_raw_files': 60}
        state['requests'].append(request)
        state['status'] = 'RUNNING_REQUEST_' + sample.name
        save()
        try:
            run_h1_generalization_prefixes(inference, sample, wc, settings, config,
                state=request, save=save, output=output / sample.name,
                context=context, mode_setup=mode_setup, kernel=kernel)
            request['status'] = 'H1_REGIONS_SOURCE12_LOCAL36_NINE_GATE_PASS_REQUIRES_AUDIT'
        except BaseException as error:
            request.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error))
            raise
        finally:
            save()
    coverage = [request['h1_coverage'] for request in state['requests']]
    if any(row['source_arms'] != 12 or row['future_source_age_cells'] != 36 for row in coverage):
        raise ValueError('Incomplete two-request matrix; no replacement or reduction')
    state['h1_coverage'] = {'requests': 2, 'source_arms': 24, 'future_source_age_cells': 72,
                            'all_held_references_immutable': True}
    save()


def run_h1_generalization_prefixes(inference, sample, wc, settings, config, *, state, save,
                    output, context, mode_setup, kernel=None):
    """The only deployed path is unchanged official WC; candidates are shadows.

    CPU controls inject a synthetic attention kernel and stand-in Inference.
    The production CLI has no override for either of those objects.
    """
    if (config['phases'] != ['baseline_prefix', 'observed_prefix']
            or config['stop_after_solver_steps'] != 33 or config['state_steps'] != [13, 21, 33]):
        raise ValueError('Generalization prefix and complete checkpoint scope changed')
    model, net = inference.pipe.model, inference.pipe.model.net
    common_rng = RNGState()
    prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
    prepare_owned = '_get_data_batch_input' in vars(inference.pipe)
    prepare_prior = vars(inference.pipe).get('_get_data_batch_input')
    forward_owned = 'forward' in vars(net)
    forward_prior = vars(net).get('forward')
    inference.pipe._get_data_batch_input = prepared
    official_forward = wc.worldcache_mini_train_dit_forward
    diagnostic = None

    def sync():
        if torch.cuda.is_initialized():
            torch.cuda.synchronize()

    def retain_diagnostic():
        state['h1_source_records'] = diagnostic.source_records if diagnostic else []
        state['h1_source_attempts'] = diagnostic.source_attempts if diagnostic else []
        state['h1_records'] = diagnostic.records if diagnostic else []
        state['h1_attempts'] = diagnostic.attempts if diagnostic else []

    try:
        for phase in config['phases']:
            verify_shared_eval(net, mode_setup)
            if phase == 'observed_prefix':
                state['source_selection'] = select_sources(state['phases'][0]['trace'], config['source_regions'])
                save()  # Selection is durable before any candidate or current teacher.
                private_config = dict(config, _baseline_trace=state['phases'][0]['trace'])
                diagnostic = H1GeneralizationProbe(private_config, selection=state['source_selection'],
                    context=context, kernel=kernel, raw_output=output / 'raw-h1')
                wc.worldcache_mini_train_dit_forward = build_h1_forward(official_forward, diagnostic)
            else:
                wc.worldcache_mini_train_dit_forward = official_forward
            common_rng.restore()
            wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
            result = {'phase': phase, 'output_hashes': [], 'input_hashes': [],
                'state_fingerprints': [], 'roundtrips': [], 'field_signatures': [],
                'named_inputs': [], 'conditions': [], 'solver_steps': 0,
                'status': 'GENERATING_PREFIX'}
            state['phases'].append(result)
            state['status'] = phase.upper()
            save()
            counts = BlockCounts(net.blocks, cache_model=net)
            call = step = 0
            restores = []

            def replace(owner, name, value):
                owned, prior = name in vars(owner), vars(owner).get(name)
                def restore():
                    if owned:
                        setattr(owner, name, prior)
                    else:
                        delattr(owner, name)
                restores.append(restore)
                setattr(owner, name, value)

            original_forward = net.forward
            def forward(*args, **kwargs):
                nonlocal call
                call += 1
                if call == 1:
                    request_wc_gate(net, sample.num_steps, settings['probe_depth'])
                result['named_inputs'].append(input_signatures(args, kwargs))
                result['input_hashes'].append(tree_digest([
                    x for x in list(args) + list(kwargs.values()) if isinstance(x, torch.Tensor)]))
                value = original_forward(*args, **kwargs)
                result['output_hashes'].append(tree_digest(value))
                return value
            replace(net, 'forward', forward)

            original_denoise = model.denoise
            def denoise(*args, **kwargs):
                condition = kwargs.get('condition', args[3] if len(args) > 3 else None)
                if condition is None:
                    raise ValueError('Condition identity missing')
                result['conditions'].append(input_signatures((), condition.to_dict(skip_underscore=False)))
                return original_denoise(*args, **kwargs)
            replace(model, 'denoise', denoise)

            scheduler = model.sample_scheduler
            original_step = scheduler.step
            def solver_step(*args, **kwargs):
                nonlocal step
                value = original_step(*args, **kwargs)
                step += 1
                result['solver_steps'] = step
                if step in config['state_steps']:
                    latent = value[0] if isinstance(value, tuple) else value.prev_sample
                    generator = kwargs.get('generator')
                    snapshot = StateRoundtrip(net, scheduler, latent,
                        generators=[generator] if generator is not None else [])
                    before = snapshot.fingerprint()
                    result['field_signatures'].append({'solver_step': step, 'call': call,
                        'components': state_components(snapshot)})
                    if phase == 'observed_prefix':
                        restored = snapshot.restore()
                        if snapshot.fingerprint() != before or tree_digest(restored) != tree_digest(latent):
                            raise ValueError('State roundtrip drift')
                        result['roundtrips'].append({'solver_step': step, 'call': call,
                            'net_keys': snapshot.keys, 'solver_keys': sorted(vars(scheduler)),
                            'fingerprint': before, 'status': 'ROUNDTRIP_PASS'})
                    result['state_fingerprints'].append({'solver_step': step, 'call': call, 'sha256': before})
                    del snapshot
                if step == config['stop_after_solver_steps']:
                    raise PrefixComplete()
                return value
            replace(scheduler, 'step', solver_step)
            if phase == 'observed_prefix':
                diagnostic.install_operators(net)
            begin = time.perf_counter()
            try:
                inference.generate([sample], output_dir=output / phase)
                raise ValueError('Expected controlled prefix completion absent')
            except PrefixComplete:
                sync()
                result.update(status='EXPECTED_PREFIX_COMPLETE_NOT_VIDEO',
                    wall_seconds=time.perf_counter() - begin, trace=counts.trace,
                    block_counts=counts.result())
                result['sampling'] = {'scheduler_class': type(scheduler).__name__,
                    'requested_steps': sample.num_steps, 'actual_schedule_steps': len(scheduler.timesteps),
                    'timesteps': scheduler.timesteps.cpu().tolist(),
                    'worldcache_horizon': net.worldcache_num_steps,
                    'use_kerras_sigma': model.config.use_kerras_sigma_at_inference}
                if call != 66 or len(counts.trace) != 66 or step != 33:
                    raise ValueError('Frozen generalization H1 prefix33/66 coverage differs')
                if len(scheduler.timesteps) != 36 or not model.config.use_kerras_sigma_at_inference:
                    raise ValueError('Frozen solver grid differs')
                retain_diagnostic()
                save()
            finally:
                result['actual_cfg_calls_entered'] = call
                result['trace'] = counts.trace
                result['block_counts'] = counts.result()
                for restore in reversed(restores):
                    restore()
                counts.close()
                if diagnostic is not None:
                    diagnostic.close()
                wc.worldcache_mini_train_dit_forward = official_forward
        verify_shared_eval(net, mode_setup)
        state['shared_eval_through_both_phases'] = True
        state['prepared_input_calls'] = prepared.calls
        left, right = state['phases']
        state['all_gate_checks'] = {key: left[key] == right[key] for key in PARITY_KEYS}
        if len(prepared.calls) != 2 or prepared.calls[0]['prepared'] != prepared.calls[1]['prepared']:
            raise ValueError('Shared official preparation contract differs')
        state['parity'] = compare_prefix(left, right)
        if not all(state['all_gate_checks'].values()):
            raise ValueError('H1 generalization full66 fieldwise/input/condition gate differs')
        state['h1_coverage'] = diagnostic.coverage()
    finally:
        state['prepared_input_calls'] = prepared.calls
        retain_diagnostic()
        if diagnostic is not None:
            diagnostic.close()
        wc.worldcache_mini_train_dit_forward = official_forward
        if forward_owned:
            setattr(net, 'forward', forward_prior)
        else:
            delattr(net, 'forward')
        if prepare_owned:
            setattr(inference.pipe, '_get_data_batch_input', prepare_prior)
        else:
            delattr(inference.pipe, '_get_data_batch_input')
