"""Complete guarded shared-D6 parent generation and coarse RA collection.

OFF/ON refers to counterfactual collection, with the same parent policy. This
collects latent calibration, not video-quality labels or a deployed RA method.
"""
import copy
import hashlib
import inspect
from pathlib import Path
import time
import types

import torch

from .cfg_mf00_interface_sampling import vector_file
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .cfg_paired_probe_production import compile_production
from .cfg_paired_probe_velocity import compile_velocity
from .cfg_ra_calibration import (SharedSchedulePairExecutor, CoarseCalibrationFork,
    DENSE_STEPS, TARGET_STEPS, ORIGIN_ANCHORS)
from .cfg_ra_calibration_table import statistics, fit_table
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, synchronize
from .mid_coverage import WC_FIELDS, tree_digest
from .prepared_input import PreparedInputReplay, RNGState
from .rv0_causal import artifact, model_guardrail_missing, pipeline_hooks
from .rv0_fork import WC_CONFIGURATION, object_state, official_suffix
from .rv0_restore import capture_inventory, capture_gate


STATE_STEPS = (12, 22, 32, 36)
PARITY = ('guided_sha256','guided_list_sha256','solver_returns','actions','counters','checkpoints',
    'conditions_before','conditions_after','rng_after','flags_before','flags_after','own_history',
    'own_fingerprint','final_latent_sha256','pipeline','sample_return_sha256')


def verify_batch(state):
    if state.get('planned_parent_paths') != 4 or len(state.get('requests', [])) != 2:
        raise ValueError('Complete two-scene four-parent calibration batch required')
    origins, children = 0, 0
    for request in state['requests']:
        rows = request['paths']
        if len(rows) != 2 or [r['collect'] for r in rows] != [False, True]:
            raise ValueError('Complete same-parent collection OFF/ON required')
        for row in rows:
            if (row['status'] != 'COMPLETE_PARENT_PATH'
                    or len(row['guided_sha256']) != 36 or len(row['solver_returns']) != 36
                    or row['actions'] != ['DD' if t in DENSE_STEPS else 'CC' for t in range(1, 37)]
                    or row['counters'] != list(range(0, 70, 2))+[0]
                    or row['vector_artifact']['tensor_sha256']['guided'] != row['guided_list_sha256']
                    or row['vector_artifact']['tensor_sha256']['final_latent'] != row['final_latent_sha256']
                    or [c['step'] for c in row['checkpoints']] != list(STATE_STEPS)
                    or row['conditions_before'] != row['conditions_after']
                    or not row['parameter_versions_unchanged'] or not row['all_modules_eval']
                    or any(row[k] != rows[0][k] for k in PARITY)
                    or row['video_artifact']['sha256'] != rows[0]['video_artifact']['sha256']):
                raise ValueError('Complete collection OFF/ON parent parity differs')
            if [o['target_step'] for o in row['origins']] != (list(TARGET_STEPS) if row['collect'] else []):
                raise ValueError('Registered three calibration origins missing')
            for origin in row['origins']:
                t = origin['target_step']
                arms = origin['arms']
                if len(arms) != 2 or [a['mode'] for a in arms] != ['CC', 'DD']:
                    raise ValueError('Complete current-action two-arm calibration missing')
                for a in arms:
                    if (a['status'] != 'COMPLETE_SAME_STATE_DENSE_SUFFIX_CALIBRATION'
                            or a['target_step'] != t or a['shared_anchor'] != ORIGIN_ANCHORS[t]
                            or not a['parent_restored'] or not a['own_shared_history_restored']
                            or not a['first_velocity_reused_without_extra_net_pair']
                            or a['actual_suffix_solver_updates'] != 37-t
                            or a['actual_suffix_net_pairs'] != 37-t
                            or [h['step'] for h in a['suffix_history']] != list(range(t, 37))
                            or [h['action'] for h in a['suffix_history']] != [a['mode']]+['DD']*(36-t)
                            or any(a[k] != arms[0][k] for k in ('origin_components','origin_fingerprint',
                                'origin_own_fingerprint','origin_own_history','current_input_sha256'))):
                        raise ValueError('Actual same-state complete dense suffix differs')
                origins += 1
                children += 2
        prepared = request['prepared_input_calls']
        if len(prepared) != 2 or prepared[0]['prepared'] != prepared[1]['prepared']:
            raise ValueError('Parent preparation differs across collection switch')
    if origins != 6 or children != 12:
        raise ValueError('Full six-origin/twelve-child calibration scope missing')
    return {'complete_parent_paths': 4,'complete_child_arms': 12,'same_state_origins': 6,
        'solver_updates': 312,'net_calls': 624,'full36_parent_OFF_ON_comparisons': 2,
        'raw_tensor_reload_and_full_video_decode_still_required': True,
        'policy_quality_or_clean_speed_claim': False}


def run_batch(inference, samples, wc, settings, *, state, save, output, inference_module,
              contexts, mode_setup, runtime, config, rf_module, writer=vector_file):
    if (len(samples) != 2 or len(contexts) != 2 or [s.name for s in samples] != config['sample_names']
            or state.get('requests') or any(s.num_steps != 35 for s in samples)
            or any(c[0] != config['run_id']+':'+s.name for c,s in zip(contexts,samples))
            or any(type(c) is not tuple or len(c) != 3 or any(type(v) is not str or not v for v in c) for c in contexts)
            or inference.pipe.offload_diffusion_model or not inference.rank0 or model_guardrail_missing(inference)):
        raise ValueError('Complete guarded two-request RA calibration batch required')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    initial = CompleteStateRoundtrip(net,scheduler,torch.zeros(1))
    initial_sha = initial.fingerprint()
    previous_forward = net.forward
    previous_config = {k:copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    previous_keys = {k for k in WC_FIELDS if hasattr(net,k)}
    parameters = [(p,p._version) for p in net.parameters()]
    suffix = official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    state.update(planned_parent_paths=4,planned_child_arms=12,requests=[],
        calibration_collection_policy='UNIFORM_SHARED_D6',video_quality_labels=0,future_time_labels=0)
    save()
    try:
        for sample,context in zip(samples,contexts):
            request = {'sample_name':sample.name,'context':list(context),'paths':[],'status':'STARTED'}
            state['requests'].append(request)
            prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            for collect in (False,True):
                initial.restore()
                verify_shared_eval(net,mode_setup)
                wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
                label = sample.name+('_COLLECT_ON' if collect else '_COLLECT_OFF')
                row = {'label':label,'collect':collect,'status':'STARTED','guided_sha256':[],
                    'solver_returns':[],'actions':[],'counters':[],'checkpoints':[],'origins':[],
                    'flags_before':backend_flags()}
                request['paths'].append(row)
                save()
                hooks, capture, tensors, conditions = Hooks(),{'in_fork':False},[],[]
                _,denoise,core = compile_production(runtime,wc,rf_module)
                base = NativePolicyPairedExecutor(model,denoise,torch,
                    wc_forward=wc.worldcache_mini_train_dit_forward,
                    rf_denoise=rf_module.Video2WorldModelRectifiedFlow.denoise)
                executor = SharedSchedulePairExecutor(base)
                factory,proof = compile_velocity(runtime,rf_module,executor,executor.choose)
                row.update(core_compiler=dict(core),velocity_compiler=dict(proof))
                original_factory = model.get_velocity_fn_from_batch
                def velocity_factory(m,*args,**kwargs):
                    velocity = factory(m,*args,**kwargs)
                    cells = inspect.getclosurevars(velocity).nonlocals
                    if set(cells) != {'self','condition','uncondition','guidance'} or cells['self'] is not m or cells['guidance'] != 7:
                        raise ValueError('Actual calibration CFG condition closure differs')
                    conditions.extend((cells['condition'],cells['uncondition']))
                    row['conditions_before'] = tree_digest([object_state(c) for c in conditions])
                    capture['velocity'] = velocity
                    def measured(noise,latent,timestep):
                        counter = int(net.cnt)
                        capture['noise'] = noise
                        value = velocity(noise,latent,timestep)
                        if value.dtype != torch.float32 or list(value.shape) != config['expected_shape']:
                            raise ValueError('Actual parent guided output geometry differs')
                        tensors.append(value.detach().cpu().clone())
                        row['guided_sha256'].append(tree_digest(tensors[-1]))
                        row['actions'].append(executor.history[-1]['action'])
                        row['counters'].append(counter)
                        return value
                    return measured
                def after_step(value):
                    if capture['in_fork']:
                        return
                    row['solver_returns'].append(tree_digest(value))
                    step = len(row['solver_returns'])
                    latent = value[0].squeeze(0)
                    if scheduler._step_index != step or len(executor.history) != step:
                        raise ValueError('Actual parent solver/shared history differs')
                    if step in STATE_STEPS:
                        inventory = capture_inventory(net,scheduler,latent,capture['noise'],capture['velocity'])
                        gate = capture_gate(inventory,logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                            transient_copy_factor=2,workspace_reserve_bytes=config['workspace_reserve_bytes']+config['paired_prefix_reserve_bytes'],
                            available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
                        snapshot = CompleteStateRoundtrip(net,scheduler,latent,[capture['generator']])
                        components = snapshot.components()
                        if len(components) != config['expected_components']:
                            raise ValueError('Actual parent complete-state component count differs')
                        row['checkpoints'].append({'step':step,'components':components,
                            'own_history':copy.deepcopy(executor.history),'own_fingerprint':executor.fingerprint()})
                        row.setdefault('capture_gates',[]).append({'step':step,**gate})
                        if step == 36:
                            capture['final_latent'] = latent.detach().cpu().clone()
                    if collect and step+1 in TARGET_STEPS:
                        capture['in_fork'] = True
                        try:
                            fork = CoarseCalibrationFork(model,latent,capture['noise'],capture['generator'],
                                capture['velocity'],suffix,context=context,executor=executor)
                            origin = {'target_step':step+1,'arms':fork.records}
                            row['origins'].append(origin)
                            for mode in ('CC','DD'):
                                def child_writer(child_label,values):
                                    return writer(output/sample.name/'calibration'/(child_label+'.pt'),values)
                                fork.measure(mode,writer=child_writer,label='step'+str(step+1)+'_'+mode,save=save)
                        finally:
                            capture['in_fork'] = False
                try:
                    pipeline_hooks(hooks,model,inference_module,row)
                    hooks.stack.callback(setattr,inference.pipe,'_get_data_batch_input',inference.pipe._get_data_batch_input)
                    inference.pipe._get_data_batch_input = prepared
                    hooks.stack.callback(setattr,model,'get_velocity_fn_from_batch',original_factory)
                    model.get_velocity_fn_from_batch = types.MethodType(velocity_factory,model)
                    hooks.wrap(scheduler,'step',before=lambda a,k:capture.update(generator=k['generator']),after=after_step)
                    hooks.wrap(model,'generate_samples_from_batch',after=lambda v:row.update(sample_return_sha256=tree_digest(v)))
                    synchronize()
                    start = time.perf_counter()
                    paths = inference.generate([sample],output_dir=output/sample.name/label)
                    synchronize()
                    row['instrumented_parent_pipeline_wall_seconds'] = time.perf_counter()-start
                    if len(paths) != 1 or len(tensors) != 36 or len(row['solver_returns']) != 36:
                        raise ValueError('Complete ordinary guarded calibration parent output missing')
                    row.update(conditions_after=tree_digest([object_state(c) for c in conditions]),
                        flags_after=backend_flags(),rng_after=RNGState().signatures(),
                        own_history=copy.deepcopy(executor.history),own_fingerprint=executor.fingerprint(),
                        video_artifact=artifact(paths[0]),guided_list_sha256=tree_digest(tensors),
                        final_latent_sha256=tree_digest(capture['final_latent']))
                    row['vector_artifact'] = writer(output/sample.name/'vectors'/(label+'.pt'),
                        {'guided':tensors,'final_latent':capture['final_latent']})
                    row.update(parameter_versions_unchanged=all(p is old and p._version == version for p,(old,version) in zip(net.parameters(),parameters)),
                        all_modules_eval=not any(m.training for m in net.modules()),status='COMPLETE_PARENT_PATH')
                    save()
                except BaseException as error:
                    row.update(status='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED',error=str(error),error_type=type(error).__name__)
                    save()
                    raise
                finally:
                    hooks.close()
                    tensors.clear()
            request.update(status='COMPLETE_REQUEST',prepared_input_calls=prepared.calls)
            save()
        state.update(verdict=verify_batch(state),status='COMPLETE_RA_CALIBRATION_BATCH_REQUIRES_RAW_CPU_AUDIT')
        save()
    finally:
        initial.restore()
        net.forward = previous_forward
        for k in set(WC_FIELDS)-previous_keys:
            if hasattr(net,k):delattr(net,k)
        for k,v in previous_config.items():setattr(net,k,v)
        if initial.fingerprint() != initial_sha:
            raise ValueError('Calibration initial physical state restoration differs')
        state['initial_state_restored'] = True
        save()


def audit_vectors(state,root,loader,expected_shape,*,fingerprint_context,toy=False):
    verify_batch(state)
    root = Path(root).resolve()
    rows, files = [], []
    def read(art):
        path = Path(art['path']).resolve()
        if not path.is_relative_to(root) or path.suffix != '.pt':
            raise ValueError('Actual calibration vector path outside output')
        raw = path.read_bytes()
        if len(raw) != art['bytes'] or hashlib.sha256(raw).hexdigest() != art['sha256']:
            raise ValueError('Actual calibration vector bytes differ')
        values = loader(path,weights_only=True,map_location='cpu')
        if {k:tree_digest(v) for k,v in values.items()} != art['tensor_sha256']:
            raise ValueError('Actual calibration raw tensor signature differs')
        files.append({'path':str(path),'bytes':art['bytes'],'sha256':art['sha256']})
        return values
    for request in state['requests']:
        parents = [read(p['vector_artifact']) for p in request['paths']]
        for parent,record in zip(parents,request['paths']):
            if set(parent) != {'guided','final_latent'} or len(parent['guided']) != 36:
                raise ValueError('Actual complete parent tensor matrix missing')
            if any(v.dtype != torch.float32 or list(v.shape) != expected_shape
                    or not bool(torch.isfinite(v).all()) for v in parent['guided']+[parent['final_latent']]):
                raise ValueError('Actual parent FP32 tensor geometry differs')
            if [tree_digest(v) for v in parent['guided']] != record['guided_sha256']:
                raise ValueError('Actual parent guided trace binding differs')
        if (not all(torch.equal(a,b) for a,b in zip(parents[0]['guided'],parents[1]['guided']))
                or not torch.equal(parents[0]['final_latent'],parents[1]['final_latent'])):
            raise ValueError('Actual full36 collection parent tensors differ')
        for origin in request['paths'][1]['origins']:
            cc,dd = [read(a['artifact']) for a in origin['arms']]
            if any(list(v.shape) != expected_shape for values in (cc,dd) for v in values.values()):
                raise ValueError('Actual child raw vector geometry differs')
            t = origin['target_step']
            rows.append({'sample_name':request['sample_name'],'target_step':t,
                'shared_anchor':ORIGIN_ANCHORS[t],'reuse_age':t-ORIGIN_ANCHORS[t],
                'raw_artifacts_independently_reloaded':True,'statistics':statistics(cc,dd)})
    if {str(p.resolve()) for p in root.rglob('*.pt')} != {f['path'] for f in files} or len(files) != 16:
        raise ValueError('Actual complete sixteen vector artifacts missing or extra')
    calibration, table = fit_table(rows,sample_names=[r['sample_name'] for r in state['requests']],
        fingerprint_context=fingerprint_context,toy=toy)
    return {'files':files,'actual_parent_guided_tensors_reloaded':144,'actual_parent_latents_reloaded':4,
        'actual_child_tensors_reloaded':48,'full36_parent_OFF_ON_direct_equal':True,
        'table':table,'calibration_fingerprint':calibration.fingerprint,
        'quality_or_speed_result':False}
