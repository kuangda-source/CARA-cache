"""Complete guarded original/native-paired sampling, with diagnostic artifacts.

Two requests, two orders, two observer settings and two strict repetitions are
inseparable. Every path finishes the ordinary pipeline. This verifies an
interface, not a new scheduling policy, endpoint improvement or clean latency.
"""
import copy
import hashlib
import inspect
from pathlib import Path
import time
import types

import torch

from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor, NATIVE_POLICY_COMPILER_PROOF
from .cfg_paired_probe_production import compile_production
from .cfg_paired_probe_velocity import compile_velocity
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip, STATE_STEPS
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, synchronize
from .mid_coverage import WC_FIELDS, tree_digest
from .prepared_input import PreparedInputReplay, RNGState, input_signatures
from .rv0_causal import artifact, model_guardrail_missing, pipeline_hooks
from .rv0_fork import WC_CONFIGURATION, object_state
from .rv0_restore import capture_inventory, capture_gate


PARITY_FIELDS = ('guided_sha256', 'guided_list_tensor_sha256', 'solver_returns', 'actions', 'block_visits', 'counters',
    'checkpoints', 'final_components', 'final_latent_sha256', 'final_solver_sha256',
    'conditions_before', 'conditions_after', 'rng_after', 'sample_return_sha256',
    'flags_before', 'flags_after', 'pipeline')
PATH_KEYS = {(order, obs, rep) for order in ('ORIGINAL', 'PAIRED')
             for obs in (False, True) for rep in ('first', 'second')}


def observer_by_call(events):
    """Preserve event chronology; compare payloads at the same call and phase."""
    return sorted(events, key=lambda e: (e['call'], e['kind']))


def vector_file(path, tensors):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('Existing complete-path tensor artifact')
    torch.save(tensors, path)
    return {**artifact(path), 'tensor_sha256': {k: tree_digest(v) for k, v in tensors.items()}}


def verify_batch(state):
    if (state.get('planned_paths') != 16 or state.get('planned_videos') != 16
            or len(state.get('requests', [])) != 2):
        raise ValueError('Complete two-request/sixteen-path scope required')
    for request in state['requests']:
        rows = request.get('paths', [])
        if len(rows) != 8 or {(r['order'], r['observers'], r['repetition']) for r in rows} != PATH_KEYS:
            raise ValueError('Complete order/observer/repetition matrix missing')
        baseline = rows[0]
        for row in rows:
            if (row['status'] != 'COMPLETE_PATH' or len(row['guided_sha256']) != 36
                    or len(row['solver_returns']) != 36 or len(row['actions']) != 36
                    or len(row['block_visits']) != 36
                    or row['counters'] != list(range(0, 70, 2)) + [0]
                    or [c['step'] for c in row['checkpoints']] != STATE_STEPS
                    or not row['parameter_versions_unchanged'] or not row['all_modules_eval']
                    or row['conditions_before'] != row['conditions_after']
                    or set(row['vector_artifact']['tensor_sha256']) != {'guided', 'final_latent'}
                    or row['vector_artifact']['tensor_sha256']['guided'] != row['guided_list_tensor_sha256']):
                raise ValueError('Full36 state/output artifact record missing or changed')
            if any(row[k] != baseline[k] for k in PARITY_FIELDS):
                raise ValueError('Complete native policy parity differs: '+row['label'])
            if row['video_artifact']['sha256'] != baseline['video_artifact']['sha256']:
                raise ValueError('Full encoded video parity differs')
            if row['vector_artifact']['tensor_sha256']['final_latent'] != row['final_latent_sha256']:
                raise ValueError('Final latent artifact binding differs')
            events = row['net_events']
            if row['observers']:
                if (len(events) != 144 or {(e['kind'], e['call']) for e in events}
                        != {(k, c) for k in ('before', 'after') for c in range(72)}):
                    raise ValueError('Complete explicit observer events missing')
                reference = next(r for r in rows if r['observers'])
                if observer_by_call(events) != observer_by_call(reference['net_events']):
                    raise ValueError('Observer order/repeat parity differs')
            elif events:
                raise ValueError('OFF has explicit net observer events')
            if row['order'] == 'PAIRED':
                decisions = row['prefix_decisions']
                if (len(decisions) != 28 or [d['step'] for d in decisions] != list(range(8, 36))
                        or decisions[-1]['paid_counters'] != [68, 69]
                        or not row['native_policy_compiler']['inverse_AST_equal']):
                    raise ValueError('Complete paired tail/native-policy proof missing')
                for decision in decisions:
                    if (decision['paid_slots'] != [0, 1] or decision['action'] != row['actions'][decision['step']-1]
                            or decision['prefix_visits_before_deep'] != [[1, 1]+[0]*(row['layers']-2)]*2):
                        raise ValueError('Two paid prefixes did not precede deep continuation')
        prepared = request['prepared_input_calls']
        if len(prepared) != 8 or any(p['prepared'] != prepared[0]['prepared'] for p in prepared):
            raise ValueError('Full matrix prepared input differs')
    return {'complete_paths': 16, 'complete_videos': 16, 'solver_updates': 576,
            'net_calls': 1152, 'guided_outputs': 576, 'order_comparisons': 8,
            'full_native_policy_hash_and_state_parity': True,
            'raw_tensor_direct_equality_requires_actual_reload': True,
            'new_policy_or_clean_latency_claim': False}


def audit_vectors(state, root, loader, expected_shape):
    """Actually reload every full-path FP32 output; hashes are not a substitute."""
    verify_batch(state)
    root = Path(root).resolve()
    files = []
    for request in state['requests']:
        baseline = None
        for row in request['paths']:
            art = row['vector_artifact'];path = Path(art['path']).resolve()
            if not path.is_relative_to(root) or path.suffix != '.pt':
                raise ValueError('Complete vector artifact outside registered output')
            raw = path.read_bytes()
            if len(raw) != art['bytes'] or hashlib.sha256(raw).hexdigest() != art['sha256']:
                raise ValueError('Actual vector artifact bytes differ')
            values = loader(path, weights_only=True, map_location='cpu')
            if set(values) != {'guided', 'final_latent'} or len(values['guided']) != 36:
                raise ValueError('Complete actual tensor list missing')
            all_tensors = values['guided'] + [values['final_latent']]
            if any(t.dtype != torch.float32 or list(t.shape) != expected_shape
                   or not bool(torch.isfinite(t).all()) for t in all_tensors):
                raise ValueError('Actual complete FP32 output geometry differs')
            if ([tree_digest(t) for t in values['guided']] != row['guided_sha256']
                    or tree_digest(values['guided']) != art['tensor_sha256']['guided']
                    or tree_digest(values['final_latent']) != row['final_latent_sha256']):
                raise ValueError('Actual output tensor signatures differ')
            if baseline is None:
                baseline = values
            elif (not all(torch.equal(a, b) for a, b in zip(baseline['guided'], values['guided']))
                    or not torch.equal(baseline['final_latent'], values['final_latent'])):
                raise ValueError('Actual full native-policy tensors differ across matrix')
            files.append({'label': row['label'], 'path': str(path), 'bytes': art['bytes'], 'sha256': art['sha256']})
    if {str(p.resolve()) for p in root.rglob('*.pt')} != {f['path'] for f in files}:
        raise ValueError('Unexpected or missing complete vector artifact')
    return {'files': files, 'actual_guided_tensors_reloaded': 576,
            'actual_final_latents_reloaded': 16, 'all_direct_equal': True}


def run_batch(inference, samples, wc, settings, *, state, save, output, inference_module,
              contexts, mode_setup, runtime, config, rf_module, writer=vector_file):
    if (len(samples) != 2 or len(contexts) != 2 or [s.name for s in samples] != config['sample_names']
            or state.get('requests') or any(s.num_steps != 35 for s in samples)
            or any(c[0] != config['run_id']+':'+s.name for c, s in zip(contexts, samples))
            or any(len(c) != 3 or any(type(v) is not str or not v for v in c) for c in contexts)
            or inference.pipe.offload_diffusion_model or not inference.rank0 or model_guardrail_missing(inference)):
        raise ValueError('Complete guarded two-request native-policy batch required')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1));initial_sha = initial.fingerprint()
    prior_forward = net.forward
    old_config = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    old_keys = {k for k in WC_FIELDS if hasattr(net, k)}
    parameters = [(p, p._version) for p in net.parameters()]
    state.update(planned_paths=16, planned_videos=16, requests=[], endpoint_labels=0,
                 new_policy_or_clean_latency_claim=False)
    save()
    try:
        for sample, context in zip(samples, contexts):
            request = {'sample_name': sample.name, 'context': list(context), 'paths': [], 'status': 'STARTED'}
            state['requests'].append(request)
            prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            for observers in (False, True):
                for repetition in ('first', 'second'):
                    for order in ('ORIGINAL', 'PAIRED'):
                        initial.restore();verify_shared_eval(net, mode_setup)
                        wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
                        label = '_'.join((sample.name, 'OBS_ON' if observers else 'OBS_OFF', repetition, order))
                        row = {'label': label, 'order': order, 'observers': observers, 'repetition': repetition,
                            'status': 'STARTED', 'guided_sha256': [], 'solver_returns': [], 'actions': [],
                            'block_visits': [], 'counters': [], 'checkpoints': [], 'net_events': [],
                            'prefix_decisions': [], 'layers': len(net.blocks), 'flags_before': backend_flags()}
                        request['paths'].append(row);save()
                        hooks, handles, capture, tensors = Hooks(), [], {}, []
                        conditions = []
                        def before(n, slot, args, kwargs):
                            row['net_events'].append({'kind': 'before', 'call': 2*len(tensors)+slot,
                                'slot': slot, 'signature': input_signatures(args, kwargs)})
                        def after(n, slot, value):
                            row['net_events'].append({'kind': 'after', 'call': 2*len(tensors)+slot,
                                'slot': slot, 'output_sha256': tree_digest(value)})
                        def block_after(index):
                            def count(*unused):
                                capture['visits'][int(net.cnt)%2][index] += 1
                            return count
                        for i, block in enumerate(net.blocks):
                            handles.append(block.register_forward_hook(block_after(i)))
                        def select(packets):
                            visits = copy.deepcopy(capture['visits'])
                            if ([(p.slot, p.counter) for p in packets] != [(0, net.cnt), (1, net.cnt+1)]
                                    or visits != [[1, 1]+[0]*(len(net.blocks)-2)]*2):
                                raise ValueError('Both full native-policy prefixes must precede deep compute')
                            action = ''.join('C' if p.native_cache else 'D' for p in packets)
                            row['prefix_decisions'].append({'step': len(tensors)+1, 'action': action,
                                'paid_slots': [p.slot for p in packets], 'paid_counters': [p.counter for p in packets],
                                'prefix_visits_before_deep': visits})
                            return action
                        try:
                            pipeline_hooks(hooks, model, inference_module, row)
                            hooks.stack.callback(setattr, inference.pipe, '_get_data_batch_input', inference.pipe._get_data_batch_input)
                            inference.pipe._get_data_batch_input = prepared
                            original_factory = model.get_velocity_fn_from_batch
                            if order == 'PAIRED':
                                _, denoise, core = compile_production(runtime, wc, rf_module,
                                    before=before if observers else None, after=after if observers else None)
                                executor = NativePolicyPairedExecutor(model, denoise, torch,
                                    wc_forward=wc.worldcache_mini_train_dit_forward,
                                    rf_denoise=rf_module.Video2WorldModelRectifiedFlow.denoise)
                                factory, proof = compile_velocity(runtime, rf_module, executor, select)
                                row.update(core_compiler=dict(core), velocity_compiler=dict(proof),
                                           native_policy_compiler=dict(NATIVE_POLICY_COMPILER_PROOF))
                            else:
                                executor = None;factory = original_factory.__func__
                                if observers:
                                    original_forward = net.forward
                                    def observed_original(*args, **kwargs):
                                        slot = int(net.cnt)%2;before(net, slot, args, kwargs)
                                        value = original_forward(*args, **kwargs);after(net, slot, value)
                                        return value
                                    hooks.stack.callback(setattr, net, 'forward', original_forward)
                                    net.forward = observed_original
                            def velocity_factory(m, *args, **kwargs):
                                velocity = factory(m, *args, **kwargs)
                                cells = inspect.getclosurevars(velocity).nonlocals
                                if set(cells) != {'self', 'condition', 'uncondition', 'guidance'} or cells['self'] is not m or cells['guidance'] != 7:
                                    raise ValueError('Actual complete velocity condition/CFG closure differs')
                                conditions.extend([cells['condition'], cells['uncondition']])
                                row['conditions_before'] = tree_digest([object_state(c) for c in conditions])
                                capture['velocity'] = velocity
                                def measured(*a, **kw):
                                    counter = int(net.cnt);capture['visits'] = [[0]*len(net.blocks) for _ in (0, 1)]
                                    capture['noise'] = a[0]
                                    value = velocity(*a, **kw)
                                    visits = capture['visits']
                                    action = ''.join('D' if v[2:] == [1]*(len(net.blocks)-2) else 'C' for v in visits)
                                    if (any(v[:2] != [1, 1] or v[2:] not in ([0]*(len(net.blocks)-2), [1]*(len(net.blocks)-2)) for v in visits)
                                            or net.cnt != (counter+2)%70 or (executor is not None and executor.last['action'] != action)
                                            or value.dtype != torch.float32 or list(value.shape) != config['expected_shape']):
                                        raise ValueError('Complete actual velocity visits/counter/shape differ')
                                    tensors.append(value.detach().cpu().clone())
                                    row['guided_sha256'].append(tree_digest(tensors[-1]));row['actions'].append(action)
                                    row['counters'].append(counter);row['block_visits'].append(copy.deepcopy(visits))
                                    return value
                                return measured
                            hooks.stack.callback(setattr, model, 'get_velocity_fn_from_batch', original_factory)
                            model.get_velocity_fn_from_batch = types.MethodType(velocity_factory, model)
                            def after_step(value):
                                row['solver_returns'].append(tree_digest(value))
                                step = len(row['solver_returns']);latent = value[0].squeeze(0)
                                if step in STATE_STEPS:
                                    inventory = capture_inventory(net, scheduler, latent, capture['noise'], capture['velocity'])
                                    gate = capture_gate(inventory, logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                                        transient_copy_factor=2, workspace_reserve_bytes=config['workspace_reserve_bytes']+config['paired_prefix_reserve_bytes'],
                                        available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
                                    snapshot = CompleteStateRoundtrip(net, scheduler, latent, [capture['generator']])
                                    components = snapshot.components()
                                    if len(components) != config['expected_components']:
                                        raise ValueError('Complete actual state component count differs')
                                    row['checkpoints'].append({'step': step, 'components': components})
                                    row.setdefault('capture_gates', []).append({'step': step, **gate})
                                    if step == 36:
                                        row.update(final_components=components, final_latent_sha256=tree_digest(latent),
                                            final_solver_sha256=tree_digest({k: v for k, v in object_state(scheduler).items() if not callable(v)}))
                                        capture['final_latent'] = latent.detach().cpu().clone()
                            hooks.wrap(scheduler, 'step', before=lambda a, k: capture.update(generator=k['generator']), after=after_step)
                            hooks.wrap(model, 'generate_samples_from_batch', after=lambda v: row.update(sample_return_sha256=tree_digest(v)))
                            synchronize();started = time.perf_counter()
                            paths = inference.generate([sample], output_dir=output/sample.name/label)
                            synchronize();row['instrumented_pipeline_wall_seconds'] = time.perf_counter()-started
                            row['conditions_after'] = tree_digest([object_state(c) for c in conditions])
                            row.update(flags_after=backend_flags(), rng_after=RNGState().signatures())
                            if len(paths) != 1 or len(tensors) != 36 or len(row['solver_returns']) != 36:
                                raise ValueError('Complete ordinary generated output missing')
                            row['video_artifact'] = artifact(paths[0])
                            row['guided_list_tensor_sha256'] = tree_digest(tensors)
                            row['vector_artifact'] = writer(output/sample.name/'vectors'/(label+'.pt'),
                                {'guided': tensors, 'final_latent': capture['final_latent']})
                            row.update(parameter_versions_unchanged=all(p is original and p._version == version for p, (original, version) in zip(net.parameters(), parameters)),
                                all_modules_eval=not any(m.training for m in net.modules()), status='COMPLETE_PATH')
                            save()
                        except BaseException as error:
                            row.update(status='TECH_BLOCKED_COMPLETE_SCOPE_RETAINED', error=str(error), error_type=type(error).__name__)
                            save();raise
                        finally:
                            hooks.close()
                            for handle in handles:handle.remove()
                            tensors.clear()
                            save()
            request.update(prepared_input_calls=prepared.calls, status='COMPLETE_REQUEST');save()
        state.update(verdict=verify_batch(state), status='COMPLETE_NATIVE_POLICY_BATCH_REQUIRES_RAW_CPU_AUDIT');save()
    finally:
        initial.restore();net.forward = prior_forward
        for key in set(WC_FIELDS)-old_keys:
            if hasattr(net, key):delattr(net, key)
        for key, value in old_config.items():setattr(net, key, value)
        if initial.fingerprint() != initial_sha:
            raise ValueError('Complete batch initial state restoration drift')
        state['initial_state_restored'] = True;save()
