"""Full two-parent/four-swap placement core with all eight suffix controls.

Offline frozen masks diagnose allocation at equal separate CFG refresh counts.
No online method, equal runtime claim or single-action training label.
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
from .rv0_fixed_mask_v2 import FixedMaskRouterV2 as FixedMaskRouter, FixedMaskSuffixControlV2 as FixedMaskSuffixControl
from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts
from .rv0_placement_scope import LABELS, ENCODED
from .rv0_placement_v2_evaluation import validate_frozen_scope, validate_fixture_scope, verify_placement_row
from .rv0_causal import TRACE_KEYS, artifact, model_guardrail_missing, original_decode_tails, pipeline_hooks
from .rv0_fork import WC_CONFIGURATION, official_suffix
from .rv0_restore import capture_inventory, capture_gate, cuda_memory_observation


class PlacementSuffixControl(FixedMaskSuffixControl):
    def run_off(self, label):
        # OFF never arms a FixedMaskPlan: native adaptive decisions evolve normally.
        def before():
            if (self.router.plan is not None or self.router.pending is not None
                    or self.router.calls != 44 or len(self.router.events) != 44):
                raise ValueError('Original adaptive OFF requires the unarmed step22 state')
        def after():
            router = self.router
            if (router.plan is not None or router.pending is not None
                    or router.calls != 72 or len(router.events) != 72):
                raise ValueError('Original adaptive OFF complete coverage differs')
            actions = [e['actual_action'] for e in router.events]
            return {'action_report': {'actual_actions': actions,
                'suffix_events': copy.deepcopy(router.events[44:]),
                'per_CFG_full_counts': list(cfg_full_counts(actions)),
                'quota_matched_per_CFG': False, 'remaining_policy': 'ORIGINAL_WC_ADAPTIVE',
                'equal_runtime': False, 'online_policy': False, 'single_step_RV_label': False}}
        return self._execute_suffix(label, before=before, after=after,
            metadata={'counterfactual_label': False, 'current_action_intervention': False,
                      'protocol': 'ORIGINAL_ADAPTIVE_COMPLETE_PLACEMENT_OFF_CONTROL'},
            status='ORIGINAL_ADAPTIVE_PLACEMENT_OFF_COMPLETE_NOT_METHOD_RESULT')


def run_placement_causal_batch(inference, samples, wc, settings, *, state, save, output,
                           inference_module, contexts, mode_setup, runtime, config,
                           require_historical_bridge=True):
    scope = config['scope']
    run_id = scope['run_id']
    scenes = scope['scenes']
    if (len(samples) != 2 or [s.name for s in samples] != [r['scene'] for r in scenes]
            or len(contexts) != 2 or state.get('requests') or any(s.num_steps != 35 for s in samples)
            or inference.pipe.offload_diffusion_model or not inference.rank0
            or model_guardrail_missing(inference) or scope['maximum_age_solver_steps'] != 33):
        raise ValueError('Independent complete placement guarded scope differs')
    if require_historical_bridge is True:
        validate_frozen_scope(scope)
    else:
        if torch.cuda.is_initialized() or not run_id.startswith('CPU_PLACEMENT:'):
            raise ValueError('Historical bridge bypass only for declared CPU Toy placement fixtures')
        validate_fixture_scope(scope)
    decode, write, tails = original_decode_tails(runtime, inference_module)
    suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    original_forward = net.forward
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1)); initial_sha = initial.fingerprint()
    original_config = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    original_keys = {k for k in WC_FIELDS if hasattr(net, k)}
    state.update(planned_parent_phases=2, planned_suffix_controls=16, planned_encoded_outputs=10,
                 requests=[], source_derived_tails=tails, GPU_RV_labels=0,
                 policy='OFFLINE_FIXED_PER_CFG_QUOTA_TWO_POSITION_PLACEMENT',
                 planned_per_CFG_quota_matching=True, per_CFG_quota_matched=False,
                 equal_runtime=False, online_policy=False, full_RV0_accepted=False, formal_RV_training_labels=False,
                 historical_bridge_required=require_historical_bridge)
    save()
    try:
        for sample, context, scene in zip(samples, contexts, scenes):
            if context[0] != run_id+':'+sample.name:
                raise ValueError('Placement independent request context differs')
            parent_mask = tuple(scene['parent_action_mask'])
            initial.restore(); verify_shared_eval(net, mode_setup)
            wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
            router = FixedMaskRouter(context)
            router.install(net, wc, runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py')
            row = {'sample_name': sample.name, 'context': list(context), 'parent_mask_sha256': scene['parent_mask_sha256'],
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
                            raise ValueError('Placement branch guardrail rejection')
                        child['status'] = 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                    except BaseException as error:
                        child.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error)); raise
                    finally:
                        synchronize(); child['decode_guardrail_encode_wall_seconds'] = time.perf_counter()-started
                        child['flags_after'] = backend_flags(); row['pipeline'] = prior_pipeline
                        fork.restore_parent(); save()
                    if child['flags_before'] != child['flags_after']:
                        raise ValueError('Placement child decode flags leaked')

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
                    fork = PlacementSuffixControl(model, latent, active['noise'], active['generator'],
                        active['velocity'], suffix, router=router, context=context)
                    row['condition_classes'] = [type(c).__module__+'.'+type(c).__name__ for c in fork.conditions]
                    row['snapshot_storage'] = fork.snapshot_storage()
                    active['inside'] = True
                    try:
                        for label in LABELS:
                            swap = () if label.startswith(('OFF', 'BASE')) else tuple(scene['swaps'][int(label[4])]['calls'])
                            plan = FixedMaskPlan(parent_mask, swap)
                            child = {'label': label, 'swap_calls': list(swap), 'status': 'STARTED',
                                     **{k: [] for k in TRACE_KEYS}}
                            row['children'].append(child); destination[0] = child; save()
                            try:
                                result = fork.run_off(label) if label.startswith('OFF') else fork.run_mask(label, plan)
                                child.update(record=copy.deepcopy(fork.records[-1]),
                                    status='COMPLETE_PLACEMENT_SUFFIX_NOT_RV_LABEL', final_latent_sha256=tree_digest(result))
                                if label in ENCODED:
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
                    raise ValueError('Placement complete parent pipeline coverage differs')
                verify_placement_row(row, scene, len(net.blocks)-settings['probe_depth'])
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
                row['status'] = 'PLACEMENT_ALL_REPEATS_QUOTAS_AND_DECODE_BRIDGES_PASS_NOT_QUALITY'; save()
            except BaseException as error:
                row.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error)); save(); raise
            finally:
                hooks.close()
                for handle in handles:
                    handle.remove()
                router.close()
        if (len(state['requests']) != 2 or sum(len(r['children']) for r in state['requests']) != 16
                or sum(1+len(r['decoded_children']) for r in state['requests']) != 10):
            raise ValueError('Placement two-parent/sixteen-suffix/ten-output coverage differs')
        state.update(status='PLACEMENT_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT',
                     per_CFG_quota_matched=True); save()
    finally:
        initial.restore(); net.forward = original_forward
        for key in set(WC_FIELDS)-original_keys:
            if hasattr(net, key):
                delattr(net, key)
        for key, value in original_config.items():
            setattr(net, key, value)
        assert initial.fingerprint() == initial_sha
