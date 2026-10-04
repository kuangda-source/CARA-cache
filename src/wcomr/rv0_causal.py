"""Full Native/cache-off/WC/OFF and one-action suffix diagnostic core.

This executes ordinary parent generation and original source-derived decode
tails. It is not a budget-matched policy or an RV training-label collector.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import time

import torch

from .decoder_policy import backend_flags, decode_policy
from .fair_sampling import native_forward
from .full_sampling import CompleteStateRoundtrip
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, synchronize
from .mid_coverage import WC_FIELDS, tree_digest
from .prepared_input import PreparedInputReplay, RNGState, input_signatures
from .rv0_actions import OneAction, OneActionRouter, OneActionSuffixControl
from .rv0_fork import WC_CONFIGURATION, official_suffix
from .rv0_restore import capture_inventory, capture_gate, cuda_memory_observation

LABELS = [('OFF', 'OFF1'), ('OFF', 'OFF2'), ('C', 'C_first'),
          ('D', 'D_second'), ('D', 'D_first'), ('C', 'C_second')]
MODES = ['NATIVE_ORIGINAL', 'CACHE_OFF_NATIVE_PATH',
         'WC_ORIGINAL_ROUTER_ABSENT', 'WC_ROUTER_OFF_WITH_SHADOWS']
TRACE_KEYS = ['inputs', 'outputs', 'deep', 'banks', 'solver_outputs']


def original_decode_tails(runtime, inference_module):
    """Keep the complete two official post-sampling bodies verbatim."""
    pipe_source = runtime/'cosmos_predict2/_src/predict2/inference/video2world.py'
    infer_source = runtime/'cosmos_predict2/inference.py'
    assert hashlib.sha256(pipe_source.read_bytes()).hexdigest() == '59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95'
    assert hashlib.sha256(infer_source.read_bytes()).hexdigest() == '0db96c49f0b3f18a971bc989e0727132dafc27ef621145a2d25a3da62a7a1975'
    pipe = next(n for n in ast.walk(ast.parse(pipe_source.read_text()))
                if isinstance(n, ast.FunctionDef) and n.name == 'generate_vid2world')
    starts = [i for i, n in enumerate(pipe.body) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'sample' for t in n.targets)]
    assert len(starts) == 1
    decode_body = copy.deepcopy(pipe.body[starts[0]+1:])
    infer = next(n for n in ast.walk(ast.parse(infer_source.read_text()))
                 if isinstance(n, ast.FunctionDef) and n.name == '_generate_sample')
    write_body = copy.deepcopy(infer.body[-2:])
    assert isinstance(write_body[0], ast.If) and ast.dump(write_body[0].test) == ast.dump(ast.parse('self.rank0', mode='eval').body)
    assert isinstance(write_body[1], ast.Return)
    namespace = dict(vars(inference_module))
    # Resolve the writer at call time: parent observers and failure adapters
    # are installed after these source-derived tails are compiled.
    def current_writer(*args, **kwargs):
        return inference_module.save_img_or_video(*args, **kwargs)
    namespace['save_img_or_video'] = current_writer
    functions = []
    for name, args, body in [('decode_tail', ['self', 'sample'], decode_body),
                             ('write_tail', ['self', 'video', 'output_path'], write_body)]:
        functions.append(ast.FunctionDef(name=name, args=ast.arguments(posonlyargs=[],
            args=[ast.arg(arg=a) for a in args], vararg=None, kwonlyargs=[], kw_defaults=[],
            kwarg=None, defaults=[]), body=body, decorator_list=[]))
    module = ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[]))
    exec(compile(module, '<rv0-original-decoder-writer-tails>', 'exec'), namespace)
    return namespace['decode_tail'], namespace['write_tail'], {
        'decode_tail_AST_sha256': hashlib.sha256(ast.dump(ast.Module(body=decode_body, type_ignores=[]), include_attributes=False).encode()).hexdigest(),
        'write_tail_AST_sha256': hashlib.sha256(ast.dump(ast.Module(body=write_body, type_ignores=[]), include_attributes=False).encode()).hexdigest(),
        'writer_namespace_binding': 'CALL_TIME_INFERENCE_MODULE_SAVE_IMG_OR_VIDEO'}


def artifact(path):
    path = Path(path)
    if not path.is_file() or not path.stat().st_size:
        raise ValueError('Complete encoded output missing')
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def pipeline_hooks(hooks, model, inference_module, row):
    row['pipeline'] = []
    def first(a, k): return a[0] if a else next(iter(k.values()))
    def event(stage, value): row['pipeline'].append({'stage': stage, 'sha256': tree_digest(value)})
    hooks.wrap(model, 'decode', before=lambda a, k: event('decode_input', first(a, k)),
               after=lambda v: event('decode_output', v), context=lambda: decode_policy(True))
    hooks.wrap(inference_module.guardrail_presets, 'run_video_guardrail',
               before=lambda a, k: event('guardrail_input', first(a, k)),
               after=lambda v: event('guardrail_output', v))
    hooks.wrap(inference_module, 'save_img_or_video',
               before=lambda a, k: event('save_input', first(a, k)))


def run_causal_batch(inference, samples, wc, settings, *, state, save, output,
                     inference_module, contexts, mode_setup, runtime, config):
    """All eight parents, 24 complete suffixes and 18 encoded outputs, or fail."""
    names = [s.name for s in samples]
    if (len(samples) != 2 or names != config['sample_names'] or len(contexts) != 2
            or state.get('requests') or any(s.num_steps != 35 for s in samples)
            or any(c[0] != config['run_id']+':'+n for c, n in zip(contexts, names))
            or any(type(c) is not tuple or len(c) != 3 or any(type(v) is not str or not v for v in c) for c in contexts)
            or inference.pipe.offload_diffusion_model or not inference.rank0
            or model_guardrail_missing(inference)):
        raise ValueError('Full single-process guarded causal scope differs')
    decode, write, tails = original_decode_tails(runtime, inference_module)
    suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    original_forward, enabled = net.forward, inference.pipe.worldcache_enabled
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1)); initial_sha = initial.fingerprint()
    original_config = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    original_keys = {k for k in WC_FIELDS if hasattr(net, k)}
    state.update(planned_parent_phases=8, planned_suffix_controls=24, planned_encoded_outputs=18,
                 requests=[], source_derived_tails=tails, GPU_RV_labels=0,
                 policy='ONE_ACTION_ADAPTIVE_DIAGNOSTIC', budget_matched=False,
                 full_RV0_accepted=False, formal_RV_training_labels=False)
    save()
    try:
        for sample, context in zip(samples, contexts):
            request = {'sample_name': sample.name, 'context': list(context), 'status': 'STARTED', 'parents': []}
            state['requests'].append(request); save()
            entry = RNGState(); prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            original_prepare = inference.pipe._get_data_batch_input
            inference.pipe._get_data_batch_input = prepared
            try:
                for mode in MODES:
                    initial.restore(); entry.restore(); verify_shared_eval(net, mode_setup)
                    wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
                    native = mode in MODES[:2]
                    inference.pipe.worldcache_enabled = not native
                    if native:
                        net.worldcache_enabled = False; net.forward = native_forward(net)
                    router = OneActionRouter(context) if mode == MODES[-1] else None
                    if router: router.install(net, wc, runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py')
                    row = {'mode': mode, 'status': 'STARTED', 'inputs': [], 'outputs': [], 'deep': [],
                           'banks': [], 'solver_outputs': [], 'children': [], 'decoded_children': [],
                           'prepare_calls': 0, 'flags_before': backend_flags(),
                           'memory_before': cuda_memory_observation()}
                    request['parents'].append(row); save()
                    hooks, handles = Hooks(), []
                    active = {'inside': False}; destination = [row]; count = [0]
                    try:
                        pipeline_hooks(hooks, model, inference_module, row)
                        hooks.wrap(inference.pipe, '_get_data_batch_input',
                                   after=lambda v: row.update(prepare_calls=row['prepare_calls']+1))
                        hooks.wrap(model, 'get_velocity_fn_from_batch', after=lambda v: active.update(velocity=v))
                        hooks.wrap(model, 'denoise', before=lambda a, k: active.update(noise=a[0]))
                        for block in list(net.blocks)[settings['probe_depth']:]:
                            handles.append(block.register_forward_hook(lambda *a: count.__setitem__(0, count[0]+1)))
                        hooks.wrap(net, 'forward', before=lambda a, k: (destination[0]['inputs'].append(input_signatures(a, k)), count.__setitem__(0, 0)),
                            after=lambda v: (destination[0]['outputs'].append(tree_digest(v)),
                                destination[0]['deep'].append(count[0]), destination[0]['banks'].append(
                                    tree_digest({k: getattr(net, k) for k in WC_FIELDS if hasattr(net, k)}))))

                        def decode_child(result, label, fork):
                            target = output/sample.name/('child_'+label); target.mkdir(parents=True, exist_ok=False)
                            child = {'label': label, 'status': 'STARTED', 'flags_before': backend_flags()}
                            row['decoded_children'].append(child); save()
                            started = time.perf_counter()
                            # Parent observers are active during the tail too;
                            # restore their event list after collecting this tail.
                            original_pipeline = row['pipeline'].copy()
                            try:
                                video = decode(inference.pipe, result)
                                path = write(inference, video, target/sample.name)
                                child['pipeline'] = row['pipeline'][len(original_pipeline):]
                                child['artifact'] = artifact(path) if path is not None else None
                                if child['artifact'] is None: raise ValueError('Branch guardrail rejection')
                                child['status'] = 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                            except BaseException as error:
                                child.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error)); raise
                            finally:
                                synchronize(); child['decode_guardrail_encode_wall_seconds'] = time.perf_counter()-started
                                child['flags_after'] = backend_flags(); row['pipeline'] = original_pipeline
                                fork.restore_parent(); save()
                            if child['flags_before'] != child['flags_after']:
                                raise ValueError('Child decode backend flags leaked')

                        def after_step(value):
                            destination[0]['solver_outputs'].append(tree_digest(value))
                            if active['inside']: return
                            latent = value[0].squeeze(0)
                            if scheduler._step_index == 36:
                                snapshot = CompleteStateRoundtrip(net, scheduler, latent, [active['generator']])
                                row.update(final_latent_sha256=tree_digest(latent), final_components=snapshot.components())
                            if not router or scheduler._step_index != 22: return
                            inventory = capture_inventory(net, scheduler, latent, active['noise'], active['velocity'])
                            row['capture_gate'] = capture_gate(inventory, logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                                transient_copy_factor=2, workspace_reserve_bytes=config['workspace_reserve_bytes'],
                                available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
                            fork = OneActionSuffixControl(model, latent, active['noise'], active['generator'],
                                active['velocity'], suffix, router=router, context=context)
                            row['condition_classes'] = [type(c).__module__+'.'+type(c).__name__ for c in fork.conditions]
                            active['inside'] = True
                            try:
                                for slot in (0, 1):
                                    for action, label in LABELS:
                                        child = {'slot': slot, 'label': label, 'action': action, 'status': 'STARTED',
                                                 **{k: [] for k in TRACE_KEYS}}
                                        row['children'].append(child); destination[0] = child; save()
                                        try:
                                            result = fork.run_action(f'{slot}_{label}', OneAction(action, 45+slot, slot, 32))
                                            child['record'] = copy.deepcopy(fork.records[-1]); child['status'] = 'COMPLETE_SUFFIX_NOT_RV_LABEL'
                                            child['final_latent_sha256'] = tree_digest(result)
                                            if (slot == 0 and label == 'OFF1') or label in ('C_first', 'D_first'):
                                                decode_child(result, f'{slot}_{label}', fork)
                                            del result
                                        except BaseException as error:
                                            child.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error))
                                            if fork.records: child['record'] = copy.deepcopy(fork.records[-1])
                                            raise
                                        finally: save()
                            finally:
                                destination[0] = row; active['inside'] = False; fork.restore_parent()
                        hooks.wrap(scheduler, 'step', before=lambda a, k: active.update(generator=k['generator']), after=after_step)
                        hooks.wrap(model, 'generate_samples_from_batch', after=lambda v: row.update(sample_return_sha256=tree_digest(v)))
                        synchronize(); started = time.perf_counter()
                        paths = inference.generate([sample], output_dir=output/sample.name/mode)
                        synchronize(); row['inclusive_parent_wall_seconds'] = time.perf_counter()-started
                        row['flags_after'] = backend_flags(); row['RNG_after'] = RNGState().signatures()
                        row['artifact'] = artifact(paths[0]) if len(paths) == 1 else None
                        if (row['artifact'] is None or len(row['inputs']) != 72 or len(row['solver_outputs']) != 36
                                or row['prepare_calls'] != 1 or row['sample_return_sha256'] != row['final_latent_sha256']
                                or row['flags_before'] != row['flags_after']):
                            raise ValueError('Complete parent/pipeline/source flags coverage differs')
                        if native and (net.cnt != 0 or not all(n == len(net.blocks)-settings['probe_depth'] for n in row['deep'])):
                            raise ValueError('Native cache-off path executed WC')
                        if router: verify_children(row, len(net.blocks)-settings['probe_depth'])
                        row['status'] = 'FULL_PARENT_AND_PLANNED_CONTROLS_COMPLETE'; save()
                    except BaseException as error:
                        row.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error)); save(); raise
                    finally:
                        hooks.close()
                        for handle in handles: handle.remove()
                        if router: router.close()
                left, right, wc_row, off_row = request['parents']
                for a, b in [(left, right), (wc_row, off_row)]:
                    for key in TRACE_KEYS+['final_latent_sha256', 'final_components', 'pipeline', 'RNG_after']:
                        if a[key] != b[key]: raise ValueError('Original/cache-off or WC/OFF mismatch: '+key)
                    if a['artifact']['sha256'] != b['artifact']['sha256']:
                        raise ValueError('Original/cache-off or WC/OFF encoded video differs')
                request.update(status='NATIVE_COMPAT_OFF_CD_REPEATS_AND_DECODE_BRIDGE_PASS_NOT_QUALITY',
                               Native_compatibility=True, router_OFF_equal=True); save()
            except BaseException as error:
                request.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error)); save(); raise
            finally: inference.pipe._get_data_batch_input = original_prepare
        state['status'] = 'FULL_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'; save()
    finally:
        initial.restore(); net.forward = original_forward; inference.pipe.worldcache_enabled = enabled
        for k in set(WC_FIELDS)-original_keys:
            if hasattr(net, k): delattr(net, k)
        for k, v in original_config.items(): setattr(net, k, v)
        assert initial.fingerprint() == initial_sha


def model_guardrail_missing(inference):
    return inference.text_guardrail_runner is None or inference.video_guardrail_runner is None


def verify_children(row, deep_count):
    by = {(c['slot'], c['label']): c for c in row['children']}
    if len(by) != 12 or len(row['decoded_children']) != 5: raise ValueError('Full branch/video denominator differs')
    for slot in (0, 1):
        off = by[slot, 'OFF1']
        for key in TRACE_KEYS:
            tail = 22 if key == 'solver_outputs' else 44
            if off[key] != row[key][tail:]: raise ValueError('OFF continuation differs: '+key)
        if off['final_latent_sha256'] != row['final_latent_sha256'] or off['record']['final_state_components'] != row['final_components']:
            raise ValueError('OFF final state differs')
        for first, second in [('OFF1', 'OFF2'), ('C_first', 'C_second'), ('D_first', 'D_second')]:
            a, b = by[slot, first], by[slot, second]
            for key in TRACE_KEYS+['final_latent_sha256']:
                if a[key] != b[key]: raise ValueError('Repeated/swapped child differs: '+key)
            if a['record']['final_state_components'] != b['record']['final_state_components']:
                raise ValueError('Repeated/swapped final child state differs')
        c, d = by[slot, 'C_first'], by[slot, 'D_first']
        if c['inputs'][:slot+1] != d['inputs'][:slot+1] or c['deep'][slot] != 0 or d['deep'][slot] != deep_count:
            raise ValueError('Same-state current action/deep execution differs')
        for child in [by[slot, label] for _, label in LABELS]:
            record = child['record']; report = record['action_report']
            if (not record['parent_restored'] or len(child['solver_outputs']) != 14 or len(child['inputs']) != 28
                    or len(report['suffix_events']) != 28 or report['budget_matched']
                    or report['decision_interventions'] != int(child['action'] != 'OFF')):
                raise ValueError('Suffix completion/action restoration differs')
    bridge = next(c for c in row['decoded_children'] if c['label'] == '0_OFF1')
    if bridge['pipeline'] != row['pipeline'] or bridge['artifact']['sha256'] != row['artifact']['sha256']:
        raise ValueError('Source-derived decode tail differs from full parent video pipeline: '+json.dumps({
            'child': bridge['pipeline'], 'parent': row['pipeline'],
            'child_video_sha256': bridge['artifact']['sha256'], 'parent_video_sha256': row['artifact']['sha256']}))
