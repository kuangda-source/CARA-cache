"""Two ordinary parents and four unchanged suffix controls, not full RV0.

Each parent continues after its two restored shadows. Encoded output bridges
and all suffix tensors/state are checked; no action, label or speed claim.
"""
import copy
import hashlib
import inspect
import time
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import torch

from .full_sampling import CompleteStateRoundtrip
from .decoder_policy import backend_flags, decode_policy
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, geometry, synchronize
from .mid_coverage import WC_FIELDS, tree_digest
from .prepared_input import input_signatures
from .rv0_fork import SamplerSuffixControl, object_state, official_suffix


def cuda_memory_observation():
    """Observe the existing CUDA context; never initialize CUDA for CPU tests."""
    if not torch.cuda.is_initialized():
        return {'status': 'CUDA_NOT_INITIALIZED', 'GPU_measurement': False}
    free, total = torch.cuda.mem_get_info()
    return {'status': 'EXISTING_CUDA_CONTEXT_OBSERVED', 'GPU_measurement': True,
            'device': torch.cuda.current_device(), 'free_bytes': free, 'total_bytes': total,
            'allocated_bytes': torch.cuda.memory_allocated(),
            'reserved_bytes': torch.cuda.memory_reserved(),
            'max_allocated_bytes': torch.cuda.max_memory_allocated(),
            'max_reserved_bytes': torch.cuda.max_memory_reserved(),
            'scope': 'PYTORCH_CONTEXT_STATS_NOT_ALL_PROCESS_ALLOCATIONS'}


def capture_inventory(net, scheduler, output, noise, velocity):
    """Metadata of values to copy; logical bytes safely overcount aliases.

    No clone, content hash, CPU transfer or model parameter traversal. This is
    a capture estimate, not the total peak or a GPU performance measurement.
    """
    cells = inspect.getclosurevars(velocity).nonlocals
    if set(cells) != {'self', 'condition', 'uncondition', 'guidance'}:
        raise ValueError('Restore inventory requires the pinned velocity closure')
    values = {
        'WC': {k: getattr(net, k) for k in WC_FIELDS if hasattr(net, k)},
        'solver': object_state(scheduler), 'output': output, 'noise': noise,
        'conditions': [object_state(cells[k]) for k in ('condition', 'uncondition')],
        'buffers': dict(net.named_buffers()),
    }
    totals, rows = {}, []
    def walk(value, path):
        if isinstance(value, torch.Tensor):
            n = value.numel() * value.element_size(); device = str(value.device)
            totals[device] = totals.get(device, 0) + n
            rows.append({'path': path, 'shape': list(value.shape), 'dtype': str(value.dtype),
                         'device': device, 'logical_bytes': n})
        elif isinstance(value, np.ndarray):
            totals['numpy'] = totals.get('numpy', 0) + value.nbytes
        elif isinstance(value, Mapping):
            for k, v in value.items(): walk(v, path + '.' + str(k))
        elif isinstance(value, (tuple, list)):
            for i, v in enumerate(value): walk(v, path + '.' + str(i))
    walk(values, 'capture')
    return {'logical_copy_bytes_by_device': totals, 'tensor_metadata': rows,
            'aliases_not_deduplicated': True, 'clone_or_transfer_performed': False,
            'weights_and_total_peak_included': False}


def capture_gate(inventory, *, logical_copy_cap_bytes, transient_copy_factor,
                 workspace_reserve_bytes, available_gpu_bytes=None):
    if (type(logical_copy_cap_bytes) is not int or logical_copy_cap_bytes <= 0
            or transient_copy_factor != 2 or type(workspace_reserve_bytes) is not int
            or workspace_reserve_bytes <= 0):
        raise ValueError('Explicit capture cap/two-copy/reserve contract required')
    totals = inventory['logical_copy_bytes_by_device']
    gpu = sum(v for k, v in totals.items() if k.startswith('cuda:'))
    all_tensor = sum(v for k, v in totals.items() if k != 'numpy')
    if all_tensor > logical_copy_cap_bytes:
        raise ValueError('Capture logical tensor copies exceed the frozen cap')
    required = transient_copy_factor * gpu + workspace_reserve_bytes
    if gpu and (type(available_gpu_bytes) is not int or available_gpu_bytes < required):
        raise ValueError('Insufficient live GPU headroom before any snapshot copies')
    return {'logical_tensor_copy_bytes': all_tensor, 'GPU_logical_copy_bytes': gpu,
            'GPU_free_bytes': available_gpu_bytes, 'required_GPU_headroom_bytes': required,
            'transient_copy_factor': transient_copy_factor,
            'workspace_reserve_bytes': workspace_reserve_bytes,
            'scope': 'CAPTURE_ADMISSION_NOT_TOTAL_PEAK_OR_COMPLETE_COST_BOUND'}


def run_restore_controls(inference, samples, wc, settings, *, state, save, output,
                         contexts, mode_setup, sampler_source, config):
    names = [s.name for s in samples]
    if (len(samples) != 2 or names != config['sample_names'] or len(contexts) != 2
            or any(s.num_steps != 35 or s.seed != 0 for s in samples)
            or config['snapshot_step'] != 22 or config['suffix_labels'] != ['A', 'B']
            or state.get('requests')):
        raise ValueError('Explicit two-parent/four-unchanged-suffix scope differs')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    verify_shared_eval(net, mode_setup)
    suffix = official_suffix(sampler_source)
    state.update(planned_parent_phases=2, planned_suffix_controls=4,
                 planned_parent_outputs=2, requests=[], RV_labels=0,
                 action_interventions=0, complete_RV0_acceptance=False,
                 clean_speed_measurement=False)
    save()
    for sample, context in zip(samples, contexts):
        if context[0] != config['run_id'] + ':' + sample.name:
            raise ValueError('Restore request identity differs')
        row = {'sample_name': sample.name, 'context': list(context), 'status': 'STARTED',
               'inputs': [], 'outputs': [], 'deep': [], 'solver_outputs': [],
               'controls': [], 'prepare_calls': 0, 'flags_before': backend_flags(),
               'memory_before_parent': cuda_memory_observation()}
        state['requests'].append(row); save()
        hooks, handles = Hooks(), []
        prior_forward = net.forward
        try:
            verify_shared_eval(net, mode_setup)
            wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
            active = {'inside': False}; deep = [0]
            destination = [row]
            hooks.wrap(inference.pipe, '_get_data_batch_input',
                       after=lambda v: row.update(prepare_calls=row['prepare_calls'] + 1))
            hooks.wrap(model, 'get_velocity_fn_from_batch', after=lambda v: active.update(velocity=v))
            hooks.wrap(model, 'denoise', before=lambda a, k: active.update(noise=a[0]))
            # The historical encoded WC bridge used this scoped decode policy.
            # Keep it identical here; do not change sampling backend flags.
            hooks.wrap(model, 'decode', context=lambda: decode_policy(True))
            row['decode_policy'] = 'SCOPED_CUDNN_BENCHMARK_FALSE_DETERMINISTIC_TRUE'
            for block in list(net.blocks)[settings['probe_depth']:]:
                handles.append(block.register_forward_hook(lambda *a: deep.__setitem__(0, deep[0]+1)))
            def before_forward(args, kwargs):
                destination[0]['inputs'].append(input_signatures(args, kwargs)); deep[0] = 0
            def after_forward(value):
                destination[0]['outputs'].append(tree_digest(value))
                destination[0]['deep'].append(deep[0])
            hooks.wrap(net, 'forward', before=before_forward, after=after_forward)
            def after_step(value):
                destination[0]['solver_outputs'].append(tree_digest(value))
                if active['inside']: return
                latents = value[0].squeeze(0)
                if scheduler._step_index == 36:
                    final = CompleteStateRoundtrip(net, scheduler, latents, [active['generator']])
                    row['final_latent_sha256'] = tree_digest(latents)
                    row['final_components'] = final.components()
                    row['final_state_sha256'] = final.fingerprint()
                if scheduler._step_index != config['snapshot_step']: return
                synchronize(); start = time.perf_counter()
                inventory = capture_inventory(net, scheduler, latents, active['noise'], active['velocity'])
                gpu_free = torch.cuda.mem_get_info()[0] if latents.is_cuda else None
                row['capture_inventory'] = inventory
                row['memory_before_snapshot'] = cuda_memory_observation()
                cells = inspect.getclosurevars(active['velocity']).nonlocals
                row['condition_classes'] = {
                    name: {'class': type(cells[name]).__module__ + '.' + type(cells[name]).__qualname__,
                           'frozen_dataclass': bool(getattr(type(cells[name]), '__dataclass_params__', None)
                                                    and type(cells[name]).__dataclass_params__.frozen)}
                    for name in ('condition', 'uncondition')}
                row['capture_gate'] = capture_gate(inventory,
                    logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                    transient_copy_factor=config['transient_copy_factor'],
                    workspace_reserve_bytes=config['workspace_reserve_bytes'], available_gpu_bytes=gpu_free)
                fork = SamplerSuffixControl(model, latents, active['noise'], active['generator'],
                                            active['velocity'], suffix, context=context)
                row['snapshot_storage'] = fork.snapshot_storage()
                synchronize(); row['snapshot_and_validation_wall_seconds'] = time.perf_counter()-start
                row['memory_after_snapshot'] = cuda_memory_observation()
                save(); active['inside'] = True
                try:
                    for label in config['suffix_labels']:
                        child = {'label': label, 'status': 'STARTED', 'inputs': [], 'outputs': [],
                                 'deep': [], 'solver_outputs': []}
                        row['controls'].append(child); destination[0] = child; save()
                        synchronize(); started = time.perf_counter()
                        try:
                            result = fork.repeat(label)
                            child['final_latent_sha256'] = tree_digest(result)
                            child['record'] = copy.deepcopy(fork.records[-1])
                            del result
                            child['status'] = 'UNCHANGED_SUFFIX_COMPLETE_NOT_ACTION_LABEL'
                        except BaseException:
                            child['record'] = copy.deepcopy(fork.records[-1]) if fork.records else None
                            child['status'] = 'TECH_BLOCKED'; raise
                        finally:
                            synchronize(); child['inclusive_wall_seconds'] = time.perf_counter()-started
                            child['memory_after_suffix_and_restore'] = cuda_memory_observation()
                            save()
                finally:
                    destination[0] = row; active['inside'] = False
                del fork
            hooks.wrap(scheduler, 'step', before=lambda a, k: active.update(generator=k['generator']), after=after_step)
            hooks.wrap(model, 'generate_samples_from_batch',
                       after=lambda v: row.update(sample_return_sha256=tree_digest(v), sample_geometry=geometry(v)))
            synchronize(); started = time.perf_counter()
            paths = inference.generate([sample], output_dir=output/sample.name)
            synchronize(); row['parent_pipeline_including_diagnostics_wall_seconds'] = time.perf_counter()-started
            row['memory_after_parent'] = cuda_memory_observation()
            row['flags_after'] = backend_flags()
            if row['flags_before'] != row['flags_after']:
                raise ValueError('Scoped decode policy leaked sampling backend flags')
            if (row['prepare_calls'] != 1 or len(row['inputs']) != 72
                    or len(row['solver_outputs']) != 36 or len(row['controls']) != 2
                    or scheduler._step_index != 36 or net.cnt != 2):
                raise ValueError('Ordinary parent/complete suffix coverage differs')
            for child in row['controls']:
                for key in ('inputs', 'outputs', 'deep'):
                    if child[key] != row[key][44:]:
                        raise ValueError('Restored suffix differs from live parent continuation: '+key)
                if (child['solver_outputs'] != row['solver_outputs'][22:]
                        or child['final_latent_sha256'] != row['final_latent_sha256']
                        or child['record']['final_state_components'] != row['final_components']
                        or child['record']['parent_restored'] is not True):
                    raise ValueError('Restored final solver/latent/state differs from live parent')
            if row['sample_return_sha256'] != row['final_latent_sha256']:
                raise ValueError('Ordinary sampler return differs from final solver latent')
            if len(paths) != 1 or not Path(paths[0]).is_file():
                raise ValueError('Ordinary complete parent output missing')
            path = Path(paths[0])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            row['artifact'] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}
            if digest != config['expected_parent_video_sha256'][sample.name]:
                raise ValueError('Parent complete encoded video differs from frozen official WC bridge')
            row.update(status='RESTORE_CONTROLS_AND_ORDINARY_PARENT_CONTINUATION_PASS',
                       all_suffix_inputs_outputs_solver_deep_latent_state_equal=True,
                       historical_official_video_bridge_equal=True)
            save()
        except BaseException as error:
            row.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error))
            save(); raise
        finally:
            hooks.close()
            for handle in handles: handle.remove()
            net.forward = prior_forward
    state['status'] = 'UNCHANGED_REAL_MODEL_RESTORE_CONTROLS_RETURNED_REQUIRES_INDEPENDENT_AUDIT'
    save()
