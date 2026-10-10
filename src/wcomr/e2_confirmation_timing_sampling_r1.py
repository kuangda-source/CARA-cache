"""Frozen E2 40 confirmation paths, 32 timing paths and four parity controls.

The existing WC/RF compilers, RA controller and phase A readout stay unchanged.
TIMING removes only outer content hashing, guided CPU copies and research
checkpoints. AUDIT retains full36 guided evidence. Native guardrail rejection
and method rejection keep their original slots rather than replacing inputs.
This module supplies no GPU admission, cost forecast or scientific acceptance.
"""
import copy
from dataclasses import asdict
import inspect
import hashlib
import math
from pathlib import Path
import time
import types

import torch

from .cfg_guided_w1_deployment_sampling import _compile_A, _attach_A, _condition_fields, _condition_masks
from .cfg_guided_w1_deployment import alpha_at
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .cfg_paired_probe_velocity import compile_velocity
from .cfg_ra_joint_control import Calibration, JointCDController
from .cfg_ra_joint_execution import JointPolicyPairExecutor
from .decoder_policy import backend_flags, decode_policy
from .full_sampling import CompleteStateRoundtrip
from .guardrail_observation import GuardrailObservation
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, geometry, synchronize
from .measurement import BlockCounts
from .mid_coverage import tree_digest
from .prepared_input import PreparedInputReplay, RNGState
from .rv0_causal import artifact, model_guardrail_missing
from .rv0_cfg_factorial_evaluation import solver_configuration
from .rv0_fork import object_state
from .cfg_mf00_interface_sampling import vector_file
from .w1_native_reference_sampling import run_native_request


METHODS = ('WC', 'RA', 'W1_ONE_PHASE', 'BETA1_ONE_PHASE')
A_METHODS = METHODS[2:]
NATIVE = 'NATIVE'


def _host_stage(hooks, owner, name, label, row, *, before=None, after=None, context=None):
    """Host substage times do not synchronize; pipeline boundaries do."""
    original = getattr(owner, name)
    own, prior = name in vars(owner), vars(owner).get(name)

    def restore():
        if own:
            setattr(owner, name, prior)
        else:
            delattr(owner, name)

    hooks.stack.callback(restore)

    def measured(*args, **kwargs):
        if before:
            before(args, kwargs)
        start = time.perf_counter()
        try:
            if context:
                with context():
                    value = original(*args, **kwargs)
            else:
                value = original(*args, **kwargs)
            if after:
                after(value)
            return value
        finally:
            record = row['host_substages'].setdefault(label, {'calls': 0, 'seconds': 0.0})
            record['calls'] += 1
            record['seconds'] += time.perf_counter()-start

    setattr(owner, name, measured)


def execute_path(inference, sample, wc, settings, *, row, save, output,
                 inference_module, context, mode_setup, runtime, config, rf_module,
                 calibration, threshold, sampling_policy, mode, writer=vector_file):
    """One ordinary guarded path. Reset/restore belongs to the caller.

    The final timing tensor is retained as a view and copied after the timed
    pipeline, with a version check against decoder-side mutation. Only AUDIT
    installs PreparedInputReplay or copies/hash-checks full guided tensors.
    Setup and method cleanup are reported, never silently called zero cost.
    """
    method = row['method']
    if (method not in (NATIVE,)+METHODS or mode not in ('AUDIT', 'TIMING')
            or method == NATIVE and mode != 'AUDIT'
            or row.get('status') != 'NOT_STARTED' or Path(output).exists()
            or sample.num_steps != 35 or not isinstance(calibration, Calibration)
            or type(context) is not tuple or len(context) != 3
            or model_guardrail_missing(inference) or not inference.rank0
            or inference.pipe.offload_diffusion_model):
        raise ValueError('Fresh frozen E2 method, mode, request and guarded pipeline required')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    verify_shared_eval(net, mode_setup)
    flags = backend_flags()
    parameters = [(p, p._version) for p in net.parameters()]
    row.update(status='STARTED', mode=mode, sample_name=sample.name,
        request=sample.model_dump(mode='json'), solver_steps=0, guided_pairs=0,
        actions=[], counters=[], host_substages={}, pipeline_events=[],
        full_guided_CPU_copy_in_timed_pipeline=mode == 'AUDIT',
        full_content_hash_in_timed_pipeline=mode == 'AUDIT',
        research_checkpoints_in_timed_pipeline=False, teacher_calls=0,
        flags_before=flags, source_or_clean_latency_acceptance=False)
    save()
    hooks, guards, counts = Hooks(), None, None
    capture, values, conditions = {}, [], []
    executor, readout = None, None
    original_factory = model.get_velocity_fn_from_batch
    synchronize(); setup_start = time.perf_counter()
    try:
        wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
        factory = original_factory.__func__
        if method in METHODS[1:]:
            _, denoise, core, readout = _compile_A(runtime, wc, rf_module, method, context, model)
            base = NativePolicyPairedExecutor(model, denoise, torch,
                wc_forward=wc.worldcache_mini_train_dit_forward,
                rf_denoise=rf_module.Video2WorldModelRectifiedFlow.denoise)
            executor = JointPolicyPairExecutor(base, JointCDController(calibration, threshold))
            executor = _attach_A(executor, readout)
            factory, velocity_proof = compile_velocity(runtime, rf_module, executor, executor.choose)
            row.update(core_compiler=dict(core), velocity_compiler=dict(velocity_proof),
                       RA_threshold=threshold, calibration_fingerprint=calibration.fingerprint)

        def velocity_factory(bound_model, *args, **kwargs):
            velocity = factory(bound_model, *args, **kwargs)
            cells = inspect.getclosurevars(velocity).nonlocals
            if (set(cells) != {'self', 'condition', 'uncondition', 'guidance'}
                    or cells['self'] is not model or cells['guidance'] != 7):
                raise ValueError('Original E2 RF condition/CFG closure differs')
            conditions.extend((cells['condition'], cells['uncondition']))
            if mode == 'AUDIT':
                row['condition_fields_before'] = _condition_fields(conditions)
                row['actual_condition_masks'] = _condition_masks(conditions)
                row['conditions_before'] = tree_digest([object_state(c) for c in conditions])

            def observed(noise, latent, timestep):
                counter = int(net.cnt) if method != NATIVE else None
                trace_start = len(counts.trace) if counts else 0
                if mode == 'AUDIT' and not values:
                    row['first_velocity_input_sha256'] = tree_digest((noise, latent, timestep))
                value = velocity(noise, latent, timestep)
                if (value.dtype != torch.float32 or list(value.shape) != config['expected_shape']):
                    raise ValueError('E2 guided output dtype or geometry differs')
                row['guided_pairs'] += 1
                if method != NATIVE:
                    trace = counts.trace[trace_start:]
                    if len(trace) != 2:
                        raise ValueError('Both actual E2 CFG block groups must execute')
                    action = ''.join('D' if call['deep_executed'] else 'C' for call in trace)
                    if int(net.cnt) != (counter+2)%70 or executor and executor.last['action'] != action:
                        raise ValueError('Actual E2 action or native70 continuation differs')
                    row['actions'].append(action); row['counters'].append(counter)
                if mode == 'AUDIT':
                    values.append(value.detach().cpu().clone())
                return value

            return observed

        hooks.stack.callback(setattr, model, 'get_velocity_fn_from_batch', original_factory)
        model.get_velocity_fn_from_batch = types.MethodType(velocity_factory, model)
        prepared = None
        if mode == 'AUDIT':
            prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            hooks.stack.callback(setattr, inference.pipe, '_get_data_batch_input', inference.pipe._get_data_batch_input)
            inference.pipe._get_data_batch_input = prepared

        def after_step(value):
            row['solver_steps'] += 1
            if scheduler._step_index != row['solver_steps']:
                raise ValueError('E2 actual solver update index differs')
            if row['solver_steps'] == 36:
                final = value[0].squeeze(0).detach()
                capture['final'] = final
                capture['final_version'] = None if torch.is_inference(final) else final._version
                if mode == 'AUDIT':
                    capture['final_CPU'] = final.cpu().clone()

        hooks.wrap(scheduler, 'step', after=after_step)
        counts = BlockCounts(net.blocks, cache_model=net)
        if method == NATIVE:
            row['method_setup_seconds'] = time.perf_counter()-setup_start
            # Native retains the accepted origin, all-block and rejection code.
            # Its clock is audit-only; it is not one of the 32 timing paths.
            native = {'status': 'STARTED'}
            row['native'] = native
            run_native_request(inference, sample, state=native, save=save, output=Path(output),
                inference_module=inference_module, sampling_policy=sampling_policy,
                expected_flags=flags, synchronize=synchronize)
            row['outcome'] = native['outcome']
            row['pipeline_wall_seconds'] = native['pipeline_wall_seconds']
            row['video_artifact'] = native['artifact']
        else:
            guards = GuardrailObservation(inference_module.guardrail_presets)

            def first(args, kwargs):
                return args[0] if args else next(iter(kwargs.values()))

            def event(stage, value):
                row['pipeline_events'].append({'stage': stage, 'geometry': geometry(value)})

            _host_stage(hooks, inference.pipe, '_get_data_batch_input', 'prepare', row)
            _host_stage(hooks, model, 'generate_samples_from_batch', 'sample', row,
                        after=lambda value: event('sample_return', value))
            _host_stage(hooks, model, 'decode', 'decode', row,
                        before=lambda a, k: event('decode_input', first(a, k)),
                        after=lambda value: event('decode_output', value), context=lambda: decode_policy(True))
            _host_stage(hooks, inference_module.guardrail_presets, 'run_video_guardrail', 'video_guardrail', row,
                        before=lambda a, k: event('guardrail_input', first(a, k)),
                        after=lambda value: event('guardrail_output', value))
            _host_stage(hooks, inference_module, 'save_img_or_video', 'write', row,
                        before=lambda a, k: event('save_input', first(a, k)))
            synchronize(); row['method_setup_seconds'] = time.perf_counter()-setup_start
            start = time.perf_counter()
            try:
                paths = inference.generate([sample], output_dir=Path(output))
            finally:
                synchronize(); row['pipeline_wall_seconds'] = time.perf_counter()-start
            row['outcome'] = guards.classify(paths)
            row['guardrail_events'] = list(guards.events)
            expected = Path(output)/(sample.name+'.mp4')
            if (row['outcome'] == 'ACCEPTED' and paths != [str(expected)]
                    or row['outcome'] != 'ACCEPTED' and (paths or expected.exists())):
                raise ValueError('E2 accepted/rejected artifact path differs')
            row['video_artifact'] = artifact(paths[0]) if paths else None

        post_start = time.perf_counter()
        hooks.close()
        counts.close()
        if guards:
            guards.close()
        row['method_hook_cleanup_seconds'] = time.perf_counter()-post_start
        # All content inspection and final artifact copies below are outside
        # the timing interval, but their GPU residency/wall is still billed.
        row.update(flags_after=backend_flags(), rng_after=RNGState().signatures(),
                   block_counts=counts.result(), trace=copy.deepcopy(counts.trace),
                   actual_raw_solver_configuration=solver_configuration(scheduler))
        if row['outcome'] == 'TEXT_REJECTED':
            if row['solver_steps'] or row['guided_pairs'] or counts.first:
                raise ValueError('E2 text rejection entered model execution')
            row.update(status='TEXT_REJECTED', vector_artifact=None, A_readout=None)
            row['method_state_release_seconds'] = 0.0
            row['online_setup_pipeline_cleanup_seconds'] = sum(row[k] for k in
                ('method_setup_seconds', 'pipeline_wall_seconds', 'method_hook_cleanup_seconds'))
            save(); return
        if (row['solver_steps'], row['guided_pairs'], counts.first) != (36, 36, 72):
            raise ValueError('Complete E2 full36/72 execution missing')
        if method != NATIVE:
            events = row['pipeline_events']
            labels = ['sample_return','decode_input','decode_output','guardrail_input','guardrail_output']
            if row['outcome'] == 'ACCEPTED':
                labels.append('save_input')
            if ([e['stage'] for e in events] != labels
                    or events[2]['geometry']['shape'] != [1,3,93,432,768]
                    or events[3]['geometry']['shape'] != [93,432,768,3]
                    or row['outcome'] == 'ACCEPTED' and
                       (events[4]['geometry']['shape'] != [93,432,768,3]
                        or events[5]['geometry']['shape'] != [3,93,432,768])):
                raise ValueError('E2 complete guarded output order or geometry differs')
        if method != NATIVE and (row['counters'] != list(range(0,70,2))+[0]
                or row['actions'][:7] != ['DD']*7 or row['actions'][-1] != 'DD'):
            raise ValueError('E2 protected prefix or last native-cycle update differs')
        if executor:
            row['policy_history'] = [asdict(d) for d in executor.controller.history]
            if [d['action'] for d in row['policy_history']] != row['actions']:
                raise ValueError('Actual E2 RA controller actions differ')
        row['A_readout'] = readout.finish() if readout else None
        final = capture['final']
        if not torch.is_inference(final) and final._version != capture['final_version']:
            raise ValueError('Decoder changed deferred E2 final latent')
        final_CPU = capture.get('final_CPU')
        if final_CPU is None:
            final_CPU = final.cpu().clone()
        if not bool(torch.isfinite(final_CPU).all()):
            raise ValueError('E2 final latent is nonfinite')
        if mode == 'AUDIT':
            row.update(condition_fields_after=_condition_fields(conditions),
                conditions_after=tree_digest([object_state(c) for c in conditions]),
                prepared_input_calls=prepared.calls,
                guided_sha256=[tree_digest(value) for value in values])
            if row['condition_fields_before'] != row['condition_fields_after']:
                raise ValueError('E2 audit conditions changed')
            payload = {'guided': values, 'final_latent': final_CPU}
        else:
            payload = {'final_latent': final_CPU}
        row['final_latent_sha256'] = tree_digest(final_CPU)
        row['vector_artifact'] = writer(Path(output).parent/'vectors'/(Path(output).name+'.pt'), payload)
        if backend_flags() != flags or any(p._version != version for p, version in parameters):
            raise ValueError('E2 method changed parameters or backend flags')
        row['status'] = 'COMPLETE_PATH' if row['outcome'] == 'ACCEPTED' else 'VIDEO_REJECTED'
        release_start = time.perf_counter()
        if readout:
            # Its source-generated helpers form callback cycles. Clear only
            # completed-request anchors after the receipt and outputs exist.
            # This is method lifecycle work, so timing includes its cost.
            for calibrator in readout.calibrators:
                calibrator.reset(context)
            readout.warp = readout.to_velocity = None
        synchronize()
        row['method_state_release_seconds'] = time.perf_counter()-release_start
        row['online_setup_pipeline_cleanup_seconds'] = sum(row[k] for k in
            ('method_setup_seconds', 'pipeline_wall_seconds', 'method_hook_cleanup_seconds',
             'method_state_release_seconds'))
        save()
    except BaseException as error:
        row.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error))
        if counts:
            row.update(block_counts=counts.result(), trace=copy.deepcopy(counts.trace))
        if guards:
            row['guardrail_events'] = list(guards.events)
        save(); raise
    finally:
        if readout:
            for calibrator in readout.calibrators:
                calibrator.reset(context)
            readout.warp = readout.to_velocity = None
        hooks.close()
        if counts:
            counts.close()
        if guards:
            guards.close()
        values.clear()


def expected_matrix(inputs):
    """Four diagnostic slots are additional to all72 scientific slots."""
    if (inputs['complete_scope']['complete_paths'] != 72
            or len(inputs['confirmation_slots']) != 40 or len(inputs['timing_slots']) != 32
            or inputs['co_primary_comparisons'] != [['W1_ONE_PHASE','RA'],['BETA1_ONE_PHASE','RA']]):
        raise ValueError('Original E2 complete72 input identity required')
    requests = inputs['requests']
    if (len(requests) != 8 or len({r['name'] for r in requests}) != 8
            or [r['seed'] for r in requests] != [17]*4+[43]*4
            or any(r['num_steps'] != 35 or r['guidance'] != 7
                   or r['num_output_frames'] != 93 or r['resolution'] != '432,768'
                   for r in requests)):
        raise ValueError('Frozen four prompts, two seeds and complete geometry required')
    expected_confirmation = [{'slot': index*5+j, 'request_name': r['name'],
                              'method': method, 'seed': r['seed']}
        for index, r in enumerate(requests) for j, method in enumerate((NATIVE,)+METHODS)]
    orders = [('WC','RA','BETA1_ONE_PHASE','W1_ONE_PHASE'),
              ('RA','W1_ONE_PHASE','WC','BETA1_ONE_PHASE'),
              ('W1_ONE_PHASE','BETA1_ONE_PHASE','RA','WC'),
              ('BETA1_ONE_PHASE','WC','W1_ONE_PHASE','RA')]
    names = ['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632',
             'av_51b45829-502e-4143-9c32-c026bd6ab191']
    expected_timing = [{'slot': 40+i*16+round_index*4+j, 'CAL_name': name,
                       'seed': 0, 'round': round_index+1, 'position': j+1, 'method': method}
        for i, name in enumerate(names) for round_index, order in enumerate(orders)
        for j, method in enumerate(order)]
    if (inputs['confirmation_slots'] != expected_confirmation
            or inputs['timing_slots'] != expected_timing):
        raise ValueError('Original E2 full40 and balanced32 positions changed')
    controls = [{'id': 'parity_'+method, 'section': 'PARITY',
                 'request_name': inputs['timing_slots'][0]['CAL_name'],
                 'method': method, 'mode': 'AUDIT'} for method in METHODS]
    confirmation = [{'id': 'confirmation_'+str(s['slot']).zfill(2), 'section': 'CONFIRMATION',
                     'request_name': s['request_name'], 'method': s['method'], 'mode': 'AUDIT',
                     'scientific_slot': s['slot']} for s in inputs['confirmation_slots']]
    timing = [{'id': 'timing_'+str(s['slot']).zfill(2), 'section': 'TIMING',
               'request_name': s['CAL_name'], 'method': s['method'], 'mode': 'TIMING',
               'scientific_slot': s['slot'], 'round': s['round'], 'position': s['position']}
              for s in inputs['timing_slots']]
    return controls+confirmation+timing


def verify_matrix(state, inputs):
    """Reject incomplete, altered or selectively dropped E2 paths."""
    matrix = expected_matrix(inputs)
    if (state.get('status') != 'COMPLETE_E2_MATRIX_REQUIRES_ARTIFACT_AUDIT_AND_FULL_FRAME_CPU_SCORE'
            or (state.get('planned_scientific_paths'), state.get('planned_parity_paths'),
                state.get('planned_all_paths')) != (72,4,76)
            or len(state.get('slots', [])) != 76 or not state.get('initial_state_restored')
            or state.get('teacher_calls') != 0 or state.get('quality_or_confirmation_accepted')
            or state.get('clean_latency_accepted')):
        raise ValueError('Complete original E2 matrix and restored state required')
    accepted, rejected, guided, updates = 0, 0, 0, 0
    parity = {}
    for row, slot in zip(state['slots'], matrix):
        if any(row.get(k) != v for k,v in slot.items()):
            raise ValueError('E2 matrix slot identity differs')
        if (row['status'] not in ('COMPLETE_PATH','TEXT_REJECTED','VIDEO_REJECTED')
                or row['flags_before'] != row['flags_after'] or row['teacher_calls'] != 0
                or any(not math.isfinite(row[k]) or row[k] < 0 for k in
                    ('pipeline_wall_seconds','online_setup_pipeline_cleanup_seconds'))
                or row['online_setup_pipeline_cleanup_seconds'] < row['pipeline_wall_seconds']
                or row['research_checkpoints_in_timed_pipeline']
                or row['full_guided_CPU_copy_in_timed_pipeline'] != (row['mode']=='AUDIT')
                or row['full_content_hash_in_timed_pipeline'] != (row['mode']=='AUDIT')):
            raise ValueError('E2 completion, timing boundary or flags differ')
        if row['status'] == 'TEXT_REJECTED':
            if (row['outcome'] != 'TEXT_REJECTED' or row['solver_steps'] or row['guided_pairs']
                    or row['trace'] or row['vector_artifact'] or row['video_artifact']):
                raise ValueError('Rejected E2 text executed or produced a substituted artifact')
            rejected += 1
            continue
        updates += row['solver_steps']; guided += row['guided_pairs']
        if ((row['solver_steps'],row['guided_pairs'],row['block_counts']['denoiser_calls']) != (36,36,72)
                or len(row['trace']) != 72
                or [t['call'] for t in row['trace']] != list(range(1,73))
                or row['block_counts']['full_calls'] != sum(t['deep_executed'] for t in row['trace'])
                or not row['actual_raw_solver_configuration']['raw_values']
                or row['vector_artifact']['tensor_sha256']['final_latent'] != row['final_latent_sha256']):
            raise ValueError('Actual E2 full36/72 blocks, solver or endpoint binding differs')
        if row['status'] == 'COMPLETE_PATH':
            if row['outcome'] != 'ACCEPTED' or not row['video_artifact']:
                raise ValueError('Accepted E2 video unavailable')
            accepted += 1
        else:
            if row['outcome'] != 'VIDEO_REJECTED' or row['video_artifact']:
                raise ValueError('Rejected E2 video was saved or substituted')
            rejected += 1
        method = row['method']
        if method == NATIVE:
            if row['block_counts']['full_calls'] != 72 or row['actions'] or row['A_readout']:
                raise ValueError('Original E2 Native reference was cached or altered')
        else:
            actions = [''.join('D' if t['deep_executed'] else 'C' for t in row['trace'][i:i+2])
                       for i in range(0,72,2)]
            if (actions != row['actions'] or actions[:7] != ['DD']*7 or actions[-1] != 'DD'
                    or row['counters'] != list(range(0,70,2))+[0]):
                raise ValueError('Actual E2 actions or native70 continuation differs')
            if method != 'WC':
                if ([h['step'] for h in row['policy_history']] != list(range(1,37))
                        or [h['action'] for h in row['policy_history']] != actions
                        or any(a not in ('CC','DD') for a in actions)):
                    raise ValueError('Actual E2 RA controller history differs')
        readout = row['A_readout']
        if method not in A_METHODS:
            if readout is not None:
                raise ValueError('A installed in original E2 baseline')
        else:
            if (readout['method'] != method or readout['completed_pairs'] != 36
                    or len(readout['history']) != 36 or readout['teacher_calls'] != 0
                    or readout['extra_candidate_deep_blocks'] != 0
                    or readout['candidate_original_head_elision_implemented']):
                raise ValueError('E2 complete original A computation differs')
            actual_D = []
            for step,(h,action) in enumerate(zip(readout['history'],row['actions']),1):
                if action == 'DD': actual_D.append(step)
                statuses = h['branch_status']
                if (h['step'] != step or h['action'] != action
                        or h['shared_alpha'] != alpha_at(method,step)
                        or h['past_D_steps'] != [actual_D[-2:]]*2
                        or h['teacher_calls'] or h['extra_deep_blocks']
                        or not h['post_RF_fusion'] or h['C_readout_updates_D_anchor']
                        or len(statuses) != 2
                        or action == 'DD' and statuses != ['ACTUAL_D_ONLY_ANCHOR']*2
                        or action == 'CC' and method.startswith('BETA1') and statuses != ['BETA1']*2
                        or action == 'CC' and method.startswith('W1') and any(s not in
                           ('scalar','small_denominator','insufficient_anchors','nonfinite_beta','nonfinite_prediction') for s in statuses)
                        or h['extra_heads'] != sum(s in ('scalar','BETA1') for s in statuses)):
                    raise ValueError('E2 A strength, trueD history or paid heads differ')
            if (any(c['anchor_steps'] != actual_D[-2:] for c in readout['D_only_final_history'])
                    or readout['extra_candidate_heads'] != sum(h['extra_heads'] for h in readout['history'])):
                raise ValueError('E2 A final anchors or total paid heads differ')
        if row['mode'] == 'AUDIT':
            if (len(row['guided_sha256']) != 36
                    or row['condition_fields_before'] != row['condition_fields_after']
                    or len(row['prepared_input_calls']) != 1):
                raise ValueError('E2 audit input or complete guided evidence differs')
        if row['section'] == 'PARITY':
            parity[method] = row
        if row['section']=='TIMING' and row['request_name']==matrix[0]['request_name']:
            ref=parity[method]
            if (not row.get('actual_audit_timing_endpoint_and_action_parity')
                    or row['actions'] != ref['actions']
                    or row['final_latent_sha256'] != ref['final_latent_sha256']
                    or row['video_artifact']['sha256'] != ref['video_artifact']['sha256']):
                raise ValueError('Actual E2 AUDIT/TIMING parity missing or changed')
    return {'complete_scope':76,'scientific_slots':72,'parity_slots':4,
            'accepted':accepted,'rejected':rejected,'solver_updates':updates,
            'guided_outputs':guided,'CFG_calls':guided*2,'quality_or_speed_claim':False}


def audit_vectors(state, inputs, root, loader, expected_shape):
    """Reload every produced tensor file, including unscored rejected videos."""
    verify_matrix(state,inputs)
    root=Path(root).resolve();files=[];guided_count=0;prefix={}
    for row in state['slots']:
        if row['status']=='TEXT_REJECTED': continue
        art=row['vector_artifact'];path=Path(art['path']).resolve()
        if not path.is_relative_to(root) or path.suffix != '.pt':
            raise ValueError('E2 vector outside complete registered output')
        raw=path.read_bytes()
        if len(raw)!=art['bytes'] or hashlib.sha256(raw).hexdigest()!=art['sha256']:
            raise ValueError('Actual E2 vector bytes changed')
        values=loader(path,weights_only=True,map_location='cpu')
        expected={'guided','final_latent'} if row['mode']=='AUDIT' else {'final_latent'}
        tensors=values.get('guided',[])+[values['final_latent']]
        if (set(values)!=expected or row['mode']=='AUDIT' and len(values['guided'])!=36
                or any(v.dtype!=torch.float32 or list(v.shape)!=expected_shape
                       or not bool(torch.isfinite(v).all()) for v in tensors)
                or {k:tree_digest(v) for k,v in values.items()} != art['tensor_sha256']):
            raise ValueError('Actual E2 complete FP32 tensors differ')
        if row['mode']=='AUDIT':
            guided_count+=36
            if [tree_digest(v) for v in values['guided']]!=row['guided_sha256']:
                raise ValueError('Actual E2 guided sequence differs')
            name=row['request_name']
            if name in prefix:
                if not all(torch.equal(a,b) for a,b in zip(prefix[name],values['guided'][:7])):
                    raise ValueError('E2 same-input protected prefix differs')
            else:prefix[name]=[v.clone() for v in values['guided'][:7]]
        files.append({'id':row['id'],'path':str(path),'sha256':art['sha256']})
    if {str(p.resolve()) for p in root.rglob('*.pt')} != {f['path'] for f in files}:
        raise ValueError('Missing or extra E2 complete tensor files')
    return {'files':files,'actual_guided_reloaded':guided_count,
            'actual_final_latents_reloaded':len(files),'all_protected_prefixes_equal':True,
            'quality_or_speed_claim':False}


def run_matrix(inference, samples_by_name, wc, settings, *, state, save, output,
               inference_module, mode_setup, runtime, config, rf_module,
               calibration, threshold, sampling_policy, inputs, writer=vector_file):
    matrix = expected_matrix(inputs)
    if state or set(samples_by_name) != {s['request_name'] for s in matrix}:
        raise ValueError('Fresh complete E2 72+4 matrix and exact ten requests required')
    state.update(planned_scientific_paths=72, planned_parity_paths=4, planned_all_paths=76,
        slots=[dict(slot, status='NOT_STARTED') for slot in matrix],
        status='RUNNING_COMPLETE_E2_MATRIX', clean_latency_accepted=False,
        quality_or_confirmation_accepted=False, teacher_calls=0)
    save()
    model, net = inference.pipe.model, inference.pipe.model.net
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    fingerprint = initial.fingerprint()
    own_forward, prior_forward = 'forward' in vars(net), vars(net).get('forward')
    parity = {}
    try:
        for row in state['slots']:
            initial.restore()
            sample = samples_by_name[row['request_name']]
            context = (config['run_id']+':'+sample.name, config['model_context'], tree_digest(sample.model_dump(mode='json')))
            execute_path(inference, sample, wc, settings, row=row, save=save,
                output=Path(output)/row['id'], inference_module=inference_module,
                context=context, mode_setup=mode_setup, runtime=runtime, config=config,
                rf_module=rf_module, calibration=calibration, threshold=threshold,
                sampling_policy=sampling_policy, mode=row['mode'], writer=writer)
            if row['section'] == 'PARITY':
                if row['status'] != 'COMPLETE_PATH':
                    raise ValueError('Actual E2 representative parity control unavailable')
                parity[row['method']] = row
            if row['section'] == 'TIMING' and row['request_name'] == matrix[0]['request_name']:
                reference = parity[row['method']]
                if (row['status'] != 'COMPLETE_PATH' or row['actions'] != reference['actions']
                        or row['final_latent_sha256'] != reference['final_latent_sha256']
                        or row['video_artifact']['sha256'] != reference['video_artifact']['sha256']):
                    raise ValueError('Actual E2 audit/timing action, final tensor or video parity differs')
                row['actual_audit_timing_endpoint_and_action_parity'] = True
                save()
        state['status'] = 'COMPLETE_E2_MATRIX_REQUIRES_ARTIFACT_AUDIT_AND_FULL_FRAME_CPU_SCORE'
        state['initial_state_restored'] = False
        save()
    except BaseException as error:
        state.update(status='E2_TECH_BLOCKED_ALL76_SLOTS_RETAINED', error_type=type(error).__name__, error=str(error))
        save(); raise
    finally:
        initial.restore()
        if own_forward:
            net.forward = prior_forward
        elif 'forward' in vars(net):
            delattr(net, 'forward')
        if initial.fingerprint() != fingerprint:
            raise ValueError('E2 matrix leaked initial physical state')
        state['initial_state_restored'] = True
        save()
