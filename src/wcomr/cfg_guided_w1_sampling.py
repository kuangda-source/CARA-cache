"""Full guarded four-scene same-state W1 collection on an unchanged D6 parent.

Collection OFF/ON has the same full36 parent route and ordinary pipeline. Eight
origins use score-only deep teachers; this is CAL, not an online teacher or a
new policy-benefit claim. Source-derived sampler/condition helpers are reused.
"""
import copy
import hashlib
import inspect
import math
from pathlib import Path
import time
import types
import torch

from .cfg_mf00_interface_sampling import vector_file
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .cfg_paired_probe_production import compile_production
from .cfg_paired_probe_velocity import compile_velocity
from .cfg_ra_calibration import SharedSchedulePairExecutor,DENSE_STEPS
from .cfg_guided_w1_forward import compile_collection
from .cfg_guided_w1_collection import GuidedW1Collector,CollectedSchedulePairExecutor,SELECTED_STEPS
from .cfg_guided_w1_collection import tensor_sha
from .cfg_guided_w1_outputs import guided_velocity_moments
from .cfg_guided_w1_grid import select_shared_alpha
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks,synchronize
from .mid_coverage import WC_FIELDS,tree_digest
from .prepared_input import PreparedInputReplay,RNGState
from .rv0_causal import artifact,model_guardrail_missing,pipeline_hooks
from .rv0_fork import WC_CONFIGURATION,object_state
from .rv0_restore import capture_inventory,capture_gate
from .rv0_cfg_factorial_evaluation import solver_configuration

STATE_STEPS=(12,30,35,36)
PARITY=('guided_sha256','guided_list_sha256','solver_returns','actions','counters','checkpoints',
    'conditions_before','conditions_after','rng_after','flags_before','flags_after','own_history',
    'own_fingerprint','final_latent_sha256','pipeline','sample_return_sha256',
    'condition_fields_before','condition_fields_after','actual_condition_masks','actual_raw_solver_configuration')


def verify_batch(state):
    if (state.get('planned_parent_paths')!=8 or state.get('planned_origins')!=8
            or state.get('planned_post_RF_branch_tensors')!=64 or len(state.get('requests',[]))!=4):
        raise ValueError('Complete four-scene eight-parent and eight-origin scope required')
    count=0
    for request in state['requests']:
        rows=request['paths']
        if len(rows)!=2 or [r['collect'] for r in rows]!=[False,True]:
            raise ValueError('Complete collection OFF/ON required for every scene')
        for row in rows:
            if (row['status']!='COMPLETE_PARENT_PATH' or len(row['guided_sha256'])!=36
                    or len(row['solver_returns'])!=36 or row['actions']!=['DD' if t in DENSE_STEPS else 'CC' for t in range(1,37)]
                    or row['counters']!=list(range(0,70,2))+[0]
                    or [c['step'] for c in row['checkpoints']]!=list(STATE_STEPS)
                    or any(row[k]!=rows[0][k] for k in PARITY)
                    or row['video_artifact']['sha256']!=rows[0]['video_artifact']['sha256']
                    or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                    or row['conditions_before']!=row['conditions_after']
                    or row['vector_artifact']['tensor_sha256']['guided']!=row['guided_list_sha256']
                    or row['vector_artifact']['tensor_sha256']['final_latent']!=row['final_latent_sha256']):
                raise ValueError('Full36 parent route, physical state, tensors or complete output parity differs')
            if [r['step'] for r in row['origins']]!=(list(SELECTED_STEPS) if row['collect'] else []):
                raise ValueError('Two preregistered actual CC origins missing')
            for origin in row['origins']:
                if (origin['scene']!=request['sample_name'] or origin['action']!='CC'
                        or not origin['actual_post_RF_original_direct_equal'] or origin['teacher_updates_deployment_anchor']
                        or list(origin['velocity_sha256'])!=['ORIGINAL','BETA1','W1','DENSE']
                        or any(len(v)!=2 for v in origin['velocity_sha256'].values())):
                    raise ValueError('Actual same-state four-method two-branch velocity scope differs')
                expected=[6,7] if origin['step']==12 else [19,25]
                if any(h['anchor_steps']!=expected for h in origin['past_D_history']):
                    raise ValueError('Candidate does not use strictly past actual D history')
                count+=1
        if len(request['prepared_input_calls'])!=2 or request['prepared_input_calls'][0]['prepared']!=request['prepared_input_calls'][1]['prepared']:
            raise ValueError('Actual prepared input differs across collection switch')
    if count!=8:raise ValueError('Full eight-origin supervision missing')
    return {'complete_parent_paths':8,'same_state_origins':8,'post_RF_branch_tensors':64,
        'parent_solver_updates':288,'parent_net_calls':576,'score_only_deep_branch_calls':16,
        'complete_guarded_OFF_ON_parent_pairs':4,'raw_tensor_reload_and_video_decode_required':True,
        'quality_or_clean_speed_or_independent_confirmation_claim':False}


def run_batch(inference, samples, wc, settings, *, state, save, output, inference_module,
              contexts, mode_setup, runtime, config, rf_module, writer=vector_file):
    if (len(samples) != 4 or len(contexts) != 4 or [s.name for s in samples] != config['sample_names']
            or state.get('requests') or any(s.num_steps != 35 for s in samples)
            or any(c[0] != config['run_id']+':'+s.name for c,s in zip(contexts,samples))
            or any(type(c) is not tuple or len(c) != 3 or any(type(v) is not str or not v for v in c) for c in contexts)
            or inference.pipe.offload_diffusion_model or not inference.rank0 or model_guardrail_missing(inference)):
        raise ValueError('Complete guarded four-request guided-W1 calibration batch required')
    model, net = inference.pipe.model, inference.pipe.model.net
    scheduler = model.sample_scheduler
    initial = CompleteStateRoundtrip(net,scheduler,torch.zeros(1))
    initial_sha = initial.fingerprint()
    previous_forward = net.forward
    previous_config = {k:copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    previous_keys = {k for k in WC_FIELDS if hasattr(net,k)}
    parameters = [(p,p._version) for p in net.parameters()]
    state.update(planned_parent_paths=8,planned_origins=8,planned_post_RF_branch_tensors=64,requests=[],
        calibration_collection_policy='UNIFORM_SHARED_D6',selected_steps=list(SELECTED_STEPS),video_quality_labels=0,future_time_labels=0)
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
                def origin_writer(scene,step,values):
                    return writer(output/sample.name/'origins'/('step'+str(step)+'.pt'),values)
                collector = GuidedW1Collector(model,scene=sample.name,context=context,
                    enabled=collect,writer=origin_writer)
                if collect:
                    _,denoise,core = compile_collection(runtime,wc,rf_module,collector)
                else:
                    _,denoise,core = compile_production(runtime,wc,rf_module)
                base = NativePolicyPairedExecutor(model,denoise,torch,
                    wc_forward=wc.worldcache_mini_train_dit_forward,
                    rf_denoise=rf_module.Video2WorldModelRectifiedFlow.denoise)
                executor = SharedSchedulePairExecutor(base)
                collected = CollectedSchedulePairExecutor(executor,collector)
                factory,proof = compile_velocity(runtime,rf_module,collected,collected.choose)
                row['origins'] = collector.records
                row.update(core_compiler=dict(core),velocity_compiler=dict(proof))
                original_factory = model.get_velocity_fn_from_batch
                def velocity_factory(m,*args,**kwargs):
                    velocity = factory(m,*args,**kwargs)
                    cells = inspect.getclosurevars(velocity).nonlocals
                    if set(cells) != {'self','condition','uncondition','guidance'} or cells['self'] is not m or cells['guidance'] != 7:
                        raise ValueError('Actual calibration CFG condition closure differs')
                    conditions.extend((cells['condition'],cells['uncondition']))
                    row['conditions_before'] = tree_digest([object_state(c) for c in conditions])
                    row['condition_fields_before'] = [{k:tree_digest(v) for k,v in object_state(c).items()} for c in conditions]
                    row['actual_condition_masks'] = [{'shape':list(c.condition_video_input_mask_B_C_T_H_W.shape),
                        'dtype':str(c.condition_video_input_mask_B_C_T_H_W.dtype),
                        'nonzero_elements':int(torch.count_nonzero(c.condition_video_input_mask_B_C_T_H_W)),
                        'finite':bool(torch.isfinite(c.condition_video_input_mask_B_C_T_H_W).all())} for c in conditions]
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
                    row['collection_complete'] = collector.finish()
                    row['condition_fields_after'] = [{k:tree_digest(v) for k,v in object_state(c).items()} for c in conditions]
                    row['actual_raw_solver_configuration'] = solver_configuration(scheduler)
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
        state.update(verdict=verify_batch(state),status='COMPLETE_GUIDED_W1_COLLECTION_BATCH_REQUIRES_RAW_CPU_AUDIT')
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


def audit_vectors(state,root,loader,expected_shape):
    """Actual full-parent parity and all64 branch outputs, not scalar receipts."""
    verify_batch(state); root=Path(root).resolve(); files=[]; W1=[]; BETA1=[]
    def read(art):
        p=Path(art['path']).resolve()
        if not p.is_relative_to(root) or p.suffix!='.pt':raise ValueError('Actual collection artifact outside output')
        raw=p.read_bytes()
        if len(raw)!=art['bytes'] or hashlib.sha256(raw).hexdigest()!=art['sha256']:
            raise ValueError('Actual collection artifact changed or truncated')
        value=loader(p,map_location='cpu',weights_only=True)
        if {k:tree_digest(v) for k,v in value.items()}!=art['tensor_sha256']:
            raise ValueError('Actual tensor contents differ from bound receipt')
        files.append({'path':str(p),'bytes':len(raw),'sha256':art['sha256']})
        return value
    def finite(v):
        return isinstance(v,torch.Tensor) and v.dtype==torch.float32 and list(v.shape)==expected_shape and bool(torch.isfinite(v).all())
    for request in state['requests']:
        parents=[]
        for row in request['paths']:
            values=read(row['vector_artifact'])
            if (set(values)!= {'guided','final_latent'} or len(values['guided'])!=36
                    or not all(finite(v) for v in values['guided']+[values['final_latent']])
                    or [tree_digest(v) for v in values['guided']]!=row['guided_sha256']):
                raise ValueError('Complete actual FP32 parent tensors required')
            parents.append(values)
            for record in row['origins']:
                bundle=read(record['artifact'])
                if list(bundle)!=['ORIGINAL','BETA1','W1','DENSE'] or any(type(p) is not tuple or len(p)!=2 or not all(finite(v) for v in p) for p in bundle.values()):
                    raise ValueError('Four actual two-branch post-RF methods required')
                if {k:[tensor_sha(v) for v in pair] for k,pair in bundle.items()}!=record['velocity_sha256']:
                    raise ValueError('Actual branch output identity differs from origin')
                c,u=bundle['ORIGINAL']; actual_guided=c+7*(c-u)
                if not torch.equal(actual_guided,values['guided'][record['step']-1]):
                    raise ValueError('Collected original branches do not recover actual source CFG output order')
                for name,target in [('BETA1',BETA1),('W1',W1)]:
                    row_moments=guided_velocity_moments(scene=record['scene'],state='step'+str(record['step']),
                        original=bundle['ORIGINAL'],proposed=bundle[name],dense=bundle['DENSE'])
                    def same(x,y):
                        if isinstance(x,dict):return x.keys()==y.keys() and all(same(x[k],y[k]) for k in x)
                        if isinstance(x,list):return len(x)==len(y) and all(same(a,b) for a,b in zip(x,y))
                        if type(x) is float:return type(y) in (int,float) and math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12)
                        return x==y
                    if not same(row_moments,record['moments'][name]):raise ValueError('Actual direct guided moments differ from receipt')
                    target.append(row_moments)
        if not all(torch.equal(x,y) for x,y in zip(parents[0]['guided']+[parents[0]['final_latent']],parents[1]['guided']+[parents[1]['final_latent']])):
            raise ValueError('Actual complete OFF/ON parent outputs differ')
    if (len(files)!=16 or {str(p.resolve()) for p in root.rglob('*.pt')}!={f['path'] for f in files}
            or len(W1)!=8 or len(BETA1)!=8):
        raise ValueError('Complete parent/origin artifacts or full-scene moments missing')
    return {'actual_parent_guided_reloaded':288,'actual_parent_latents_reloaded':8,
        'actual_post_RF_branch_tensors_reloaded':64,'actual_full36_OFF_ON_direct_equal':True,
        'actual_original_branch_recovery_source_CFG_order_equal':True,
        'files':files,'W1_shared_alpha_selection':select_shared_alpha(W1),
        'BETA1_shared_alpha_selection':select_shared_alpha(BETA1),
        'online_teacher_or_quality_or_clean_latency_claim':False}

