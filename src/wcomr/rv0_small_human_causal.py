"""Independent missing-Human complement; frozen original two-parent core remains unchanged.

Only cardinality/identity differs. Full controls, state, paid-probe rules and
historical decode bridges use the exact original pipeline and row verifier.
"""
import copy
from pathlib import Path
import time

import torch

from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, synchronize
from .mid_coverage import WC_FIELDS, tree_digest
from .prepared_input import RNGState, input_signatures
from .rv0_actions import OneAction, OneActionRouter, OneActionSuffixControl
from .rv0_causal import LABELS, TRACE_KEYS, artifact, model_guardrail_missing, original_decode_tails, pipeline_hooks
from .rv0_fork import WC_CONFIGURATION, official_suffix
from .rv0_restore import capture_inventory, capture_gate, cuda_memory_observation


from .rv0_small_causal import verify_small_children


def run_small_human_complement_batch(inference, samples, wc, settings, *, state, save, output,
                           inference_module, contexts, mode_setup, runtime, config,
                           require_historical_bridge=True):
    if (len(samples) != 1 or [s.name for s in samples] != config['sample_names']
            or len(contexts) != 1 or state.get('requests') or any(s.num_steps != 35 for s in samples)
            or inference.pipe.offload_diffusion_model or not inference.rank0
            or model_guardrail_missing(inference)
            or config['target_calls'] != [46] or config['maximum_age_solver_steps'] != 32):
        raise ValueError('Independent small single-process guarded C/D scope differs')
    if require_historical_bridge is not True:
        if torch.cuda.is_initialized() or not config['run_id'].startswith('CPU_SMALL_HUMAN:'):
            raise ValueError('Historical bridge bypass is only for explicitly labeled CPU Toy fixtures')
    decode, write, tails = original_decode_tails(runtime, inference_module)
    suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    original_forward = net.forward
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1)); initial_sha = initial.fingerprint()
    original_config = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    original_keys = {k for k in WC_FIELDS if hasattr(net, k)}
    state.update(planned_parent_phases=1, planned_suffix_controls=6, planned_encoded_outputs=4,
                 requests=[], source_derived_tails=tails, GPU_RV_labels=0,
                 policy='ONE_HUMAN_COMPLEMENT_ADAPTIVE_DIAGNOSTIC_WITH_HISTORICAL_REFERENCE',
                 budget_matched=False, full_RV0_accepted=False, formal_RV_training_labels=False,
                 historical_bridge_required=require_historical_bridge)
    save()
    try:
        for sample, context, target in zip(samples, contexts, config['target_calls']):
            if context[0] != config['run_id']+':'+sample.name:
                raise ValueError('Small independent request context differs')
            slot = (target-1) % 2
            initial.restore(); verify_shared_eval(net, mode_setup)
            wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
            router = OneActionRouter(context)
            router.install(net, wc, runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py')
            row = {'sample_name': sample.name, 'context': list(context), 'slot': slot, 'target_call': target,
                   'status': 'STARTED', **{k: [] for k in TRACE_KEYS}, 'children': [], 'decoded_children': [],
                   'prepare_calls': 0, 'flags_before': backend_flags(), 'memory_before': cuda_memory_observation()}
            state['requests'].append(row); save()
            hooks, handles = Hooks(), []
            active = {'inside': False}; destination = [row]; count = [0]
            try:
                pipeline_hooks(hooks, model, inference_module, row)
                hooks.wrap(inference.pipe, '_get_data_batch_input', after=lambda v: row.update(prepare_calls=row['prepare_calls']+1))
                hooks.wrap(model, 'get_velocity_fn_from_batch', after=lambda v: active.update(velocity=v))
                hooks.wrap(model, 'denoise', before=lambda a, k: active.update(noise=a[0]))
                for block in list(net.blocks)[settings['probe_depth']:]:
                    handles.append(block.register_forward_hook(lambda *a: count.__setitem__(0, count[0]+1)))
                hooks.wrap(net, 'forward', before=lambda a, k: (destination[0]['inputs'].append(input_signatures(a, k)), count.__setitem__(0, 0)),
                    after=lambda v: (destination[0]['outputs'].append(tree_digest(v)), destination[0]['deep'].append(count[0]),
                        destination[0]['banks'].append(tree_digest({k: getattr(net, k) for k in WC_FIELDS if hasattr(net, k)}))))

                def decode_child(result, label, fork):
                    target_dir = output/sample.name/('child_'+label); target_dir.mkdir(parents=True, exist_ok=False)
                    child = {'label': label, 'status': 'STARTED', 'flags_before': backend_flags()}
                    row['decoded_children'].append(child); save()
                    prior_pipeline = row['pipeline'].copy(); started = time.perf_counter()
                    try:
                        video = decode(inference.pipe, result)
                        path = write(inference, video, target_dir/sample.name)
                        child['pipeline'] = row['pipeline'][len(prior_pipeline):]
                        child['artifact'] = artifact(path) if path is not None else None
                        if child['artifact'] is None:
                            raise ValueError('Small branch guardrail rejection')
                        child['status'] = 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                    except BaseException as error:
                        child.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error)); raise
                    finally:
                        synchronize(); child['decode_guardrail_encode_wall_seconds'] = time.perf_counter()-started
                        child['flags_after'] = backend_flags(); row['pipeline'] = prior_pipeline
                        fork.restore_parent(); save()
                    if child['flags_before'] != child['flags_after']:
                        raise ValueError('Small child decode flags leaked')

                def after_step(value):
                    destination[0]['solver_outputs'].append(tree_digest(value))
                    if active['inside']:
                        return
                    latent = value[0].squeeze(0)
                    if scheduler._step_index == 36:
                        snapshot = CompleteStateRoundtrip(net, scheduler, latent, [active['generator']])
                        row.update(final_latent_sha256=tree_digest(latent), final_components=snapshot.components())
                    if scheduler._step_index != 22:
                        return
                    inventory = capture_inventory(net, scheduler, latent, active['noise'], active['velocity'])
                    row['capture_gate'] = capture_gate(inventory, logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                        transient_copy_factor=2, workspace_reserve_bytes=config['workspace_reserve_bytes'],
                        available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
                    fork = OneActionSuffixControl(model, latent, active['noise'], active['generator'],
                        active['velocity'], suffix, router=router, context=context)
                    row['condition_classes'] = [type(c).__module__+'.'+type(c).__name__ for c in fork.conditions]
                    row['snapshot_storage'] = fork.snapshot_storage()
                    active['inside'] = True
                    try:
                        for action, label in LABELS:
                            child = {'slot': slot, 'label': label, 'action': action, 'status': 'STARTED',
                                     **{k: [] for k in TRACE_KEYS}}
                            row['children'].append(child); destination[0] = child; save()
                            try:
                                result = fork.run_action(label, OneAction(action, target, slot, 32))
                                child.update(record=copy.deepcopy(fork.records[-1]),
                                    status='COMPLETE_SUFFIX_NOT_RV_LABEL', final_latent_sha256=tree_digest(result))
                                if label in ('OFF1', 'C_first', 'D_first'):
                                    decode_child(result, label, fork)
                                del result
                            except BaseException as error:
                                child.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error))
                                if fork.records:
                                    child['record'] = copy.deepcopy(fork.records[-1])
                                raise
                            finally:
                                save()
                    finally:
                        destination[0] = row; active['inside'] = False; fork.restore_parent()
                hooks.wrap(scheduler, 'step', before=lambda a, k: active.update(generator=k['generator']), after=after_step)
                hooks.wrap(model, 'generate_samples_from_batch', after=lambda v: row.update(sample_return_sha256=tree_digest(v)))
                synchronize(); started = time.perf_counter()
                paths = inference.generate([sample], output_dir=output/sample.name/'WC_ROUTER_OFF_WITH_SHADOWS')
                synchronize(); row['inclusive_parent_wall_seconds'] = time.perf_counter()-started
                row.update(flags_after=backend_flags(), RNG_after=RNGState().signatures(),
                           artifact=artifact(paths[0]) if len(paths) == 1 else None)
                if (row['artifact'] is None or len(row['inputs']) != 72 or len(row['solver_outputs']) != 36
                        or row['prepare_calls'] != 1 or row['sample_return_sha256'] != row['final_latent_sha256']
                        or row['flags_before'] != row['flags_after'] or net.cnt != 2):
                    raise ValueError('Small complete parent pipeline coverage differs')
                verify_small_children(row, slot, len(net.blocks)-settings['probe_depth'])
                if require_historical_bridge:
                    reference = config['references'][sample.name]
                    if (list(context[1:]) != reference['model_and_condition_context']
                            or settings != config['historical_wc_settings']
                            or [int(t) for t in scheduler.timesteps] != reference['timesteps']
                            or row['artifact']['sha256'] != reference['official_WC']['sha256']):
                        raise ValueError('Current WC/historical Native reference provenance or encoded bridge differs')
                    row['historical_WC_encoded_bridge_pass'] = True
                else:
                    row['historical_WC_encoded_bridge_pass'] = 'CPU_TOY_NOT_REAL_REFERENCE'
                row['status'] = 'SMALL_SELECTED_CD_ALL_REPEATS_AND_DECODE_BRIDGE_PASS_NOT_QUALITY'; save()
            except BaseException as error:
                row.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error)); save(); raise
            finally:
                hooks.close()
                for handle in handles:
                    handle.remove()
                router.close()
        if (len(state['requests']) != 1 or sum(len(r['children']) for r in state['requests']) != 6
                or sum(1+len(r['decoded_children']) for r in state['requests']) != 4):
            raise ValueError('Human complement one-parent/six-suffix/four-output coverage differs')
        state['status'] = 'HUMAN_COMPLEMENT_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'; save()
    finally:
        initial.restore(); net.forward = original_forward
        for key in set(WC_FIELDS)-original_keys:
            if hasattr(net, key):
                delattr(net, key)
        for key, value in original_config.items():
            setattr(net, key, value)
        assert initial.fingerprint() == initial_sha
