"""Complete guarded WC / simple joint / calibrated RA development comparison.

Every method follows its own trajectory from the same prepared input and noise.
This diagnostic path saves full outputs and actual actions; its instrumented
wall time is not a clean speed measurement. No teacher runs inside any method.
"""
import copy
from dataclasses import asdict
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
from .cfg_ra_baseline import JointNativePairExecutor
from .cfg_ra_joint_control import Calibration, JointCDController, finite_nonnegative
from .cfg_ra_joint_execution import JointPolicyPairExecutor
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip, STATE_STEPS
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, synchronize
from .mid_coverage import WC_FIELDS, tree_digest
from .prepared_input import PreparedInputReplay, RNGState
from .rv0_causal import artifact, model_guardrail_missing, pipeline_hooks
from .rv0_fork import WC_CONFIGURATION, object_state
from .rv0_restore import capture_inventory, capture_gate


METHODS = ('WC','JOINT_NATIVE','RA')


def verify_batch(state):
    if (state.get('planned_paths') != 6 or state.get('planned_videos') != 6
            or len(state.get('requests', [])) != 2 or state.get('teacher_calls') != 0
            or not finite_nonnegative(state.get('RA_threshold'))):
        raise ValueError('Complete two-scene three-method development comparison required')
    for request in state['requests']:
        rows = request['paths']
        if len(rows) != 3 or [r['method'] for r in rows] != list(METHODS):
            raise ValueError('Complete WC/simple-joint/RA method matrix missing')
        for row in rows:
            if (row['status'] != 'COMPLETE_PATH' or len(row['guided_sha256']) != 36
                    or len(row['solver_returns']) != 36 or len(row['actions']) != 36
                    or len(row['block_visits']) != 36 or row['actions'][:7] != ['DD']*7
                    or row['actions'][-1] != 'DD'
                    or row['counters'] != list(range(0,70,2))+[0]
                    or [p['step'] for p in row['checkpoints']] != STATE_STEPS
                    or row['conditions_before'] != row['conditions_after']
                    or row['conditions_before'] != rows[0]['conditions_before']
                    or row['first_velocity_input_sha256'] != rows[0]['first_velocity_input_sha256']
                    or row['rng_after'] != rows[0]['rng_after']
                    or not row['parameter_versions_unchanged'] or not row['all_modules_eval']
                    or row['vector_artifact']['tensor_sha256']['guided'] != row['guided_list_sha256']
                    or row['vector_artifact']['tensor_sha256']['final_latent'] != row['final_latent_sha256']):
                raise ValueError('Complete full36 outputs, paired input or raw artifact binding differs')
            for action,visits in zip(row['actions'],row['block_visits']):
                if (action not in ('CC','CD','DC','DD')
                        or visits != [[1,1]+[int(a=='D')]*(row['layers']-2) for a in action]):
                    raise ValueError('Recorded action did not execute the complete actual blocks')
            if row['method'] == 'WC':
                if row['prefix_decisions'] or row['policy_history']:
                    raise ValueError('Original WC has an injected joint selector')
            else:
                if (any(a not in ('CC','DD') for a in row['actions'])
                        or len(row['policy_history']) != 36
                        or [h['step'] for h in row['policy_history']] != list(range(1,37))
                        or [h['action'] for h in row['policy_history']] != row['actions']
                        or [d['step'] for d in row['prefix_decisions']] != list(range(8,36))):
                    raise ValueError('Actual complete shared-controller history differs')
                for decision in row['prefix_decisions']:
                    packets = decision['paid_probes']
                    step = decision['step']
                    if ([(p['slot'],p['counter']) for p in packets]
                            != [(0,2*(step-1)),(1,2*(step-1)+1)]
                            or decision['prefix_visits_before_deep'] != [[1,1]+[0]*(row['layers']-2)]*2
                            or decision['action'] != row['actions'][step-1]):
                        raise ValueError('Both actual paid prefixes must precede deep work')
                    if row['method'] == 'JOINT_NATIVE':
                        expected = 'CC' if all(p['native_cache'] for p in packets) else 'DD'
                        if decision['action'] != expected:
                            raise ValueError('Simple joint-native control rule differs')
                if row['method'] == 'RA' and (row['RA_threshold'] != state['RA_threshold']
                        or row['calibration_fingerprint'] != state['calibration_fingerprint']):
                    raise ValueError('Current RA prior or initial threshold changed within batch')
        prepared = request['prepared_input_calls']
        if len(prepared) != 3 or any(p['prepared'] != prepared[0]['prepared'] for p in prepared):
            raise ValueError('All methods must use the same complete prepared input')
    return {'complete_paths':6,'complete_videos':6,'solver_updates':216,'net_calls':432,
        'teacher_calls':0,'all_three_methods_complete_and_actual_deep_visits_verified':True,
        'method_outputs_not_required_equal':True,'instrumented_time_not_clean_latency':True,
        'endpoint_quality_requires_matching_reference_scoring':True}


def audit_vectors(state,root,loader,expected_shape):
    verify_batch(state)
    root = Path(root).resolve()
    files = []
    for request in state['requests']:
        reference = None
        for row in request['paths']:
            art = row['vector_artifact']
            path = Path(art['path']).resolve()
            if not path.is_relative_to(root) or path.suffix != '.pt':
                raise ValueError('Actual method vector path outside registered output')
            raw = path.read_bytes()
            if len(raw) != art['bytes'] or hashlib.sha256(raw).hexdigest() != art['sha256']:
                raise ValueError('Actual method vector file changed')
            values = loader(path,weights_only=True,map_location='cpu')
            if (set(values) != {'guided','final_latent'} or len(values['guided']) != 36
                    or any(v.dtype != torch.float32 or list(v.shape) != expected_shape
                        or not bool(torch.isfinite(v).all())
                        for v in values['guided']+[values['final_latent']])
                    or {k:tree_digest(v) for k,v in values.items()} != art['tensor_sha256']
                    or [tree_digest(v) for v in values['guided']] != row['guided_sha256']):
                raise ValueError('Complete actual method FP32 tensors differ from receipt')
            if reference is None:
                reference = values
            elif not all(torch.equal(a,b) for a,b in zip(reference['guided'][:7],values['guided'][:7])):
                raise ValueError('Methods diverged before any eligible policy decision')
            files.append({'label':row['label'],'method':row['method'],'path':str(path),
                'bytes':art['bytes'],'sha256':art['sha256']})
    if len(files) != 6 or {str(p.resolve()) for p in root.rglob('*.pt')} != {f['path'] for f in files}:
        raise ValueError('Complete six method vector files missing or extra')
    return {'files':files,'actual_guided_tensors_reloaded':216,'actual_final_latents_reloaded':6,
        'actual_initial_7_DD_guided_direct_equal':True,'quality_or_speed_result':False}


def run_batch(inference,samples,wc,settings,*,state,save,output,inference_module,
              contexts,mode_setup,runtime,config,rf_module,calibration,threshold,writer=vector_file):
    if (not isinstance(calibration,Calibration) or not finite_nonnegative(threshold)
            or len(samples) != 2 or len(contexts) != 2
            or [s.name for s in samples] != config['sample_names'] or state.get('requests')
            or any(s.num_steps != 35 for s in samples)
            or any(type(c) is not tuple or len(c) != 3
                or any(type(v) is not str or not v for v in c)
                or c[0] != config['run_id']+':'+s.name for c,s in zip(contexts,samples))
            or inference.pipe.offload_diffusion_model or not inference.rank0
            or model_guardrail_missing(inference)):
        raise ValueError('Complete guarded two-request calibrated RA development batch required')
    model,net = inference.pipe.model,inference.pipe.model.net
    scheduler = model.sample_scheduler
    initial = CompleteStateRoundtrip(net,scheduler,torch.zeros(1))
    initial_sha = initial.fingerprint()
    prior_forward = net.forward
    old_config = {k:copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    old_keys = {k for k in WC_FIELDS if hasattr(net,k)}
    parameters = [(p,p._version) for p in net.parameters()]
    state.update(planned_paths=6,planned_videos=6,requests=[],teacher_calls=0,
        RA_threshold=threshold,calibration_fingerprint=calibration.fingerprint,
        clean_latency_claim=False,independent_confirmation_claim=False)
    save()
    try:
        for sample,context in zip(samples,contexts):
            request = {'sample_name':sample.name,'context':list(context),'paths':[],'status':'STARTED'}
            state['requests'].append(request)
            prepared = PreparedInputReplay(inference.pipe._get_data_batch_input)
            for method in METHODS:
                initial.restore()
                verify_shared_eval(net,mode_setup)
                wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
                label = sample.name+'_'+method
                row = {'label':label,'method':method,'status':'STARTED','layers':len(net.blocks),
                    'guided_sha256':[],'solver_returns':[],'actions':[],'counters':[],
                    'block_visits':[],'checkpoints':[],'prefix_decisions':[],'policy_history':[],
                    'flags_before':backend_flags()}
                request['paths'].append(row)
                save()
                hooks,handles,capture,tensors,conditions = Hooks(),[],{},[],[]
                def block_after(index):
                    def count(*unused):
                        capture['visits'][int(net.cnt)%2][index] += 1
                    return count
                for index,block in enumerate(net.blocks):
                    handles.append(block.register_forward_hook(block_after(index)))
                def record_selection(packets,action):
                    visits = copy.deepcopy(capture['visits'])
                    if visits != [[1,1]+[0]*(len(net.blocks)-2)]*2:
                        raise ValueError('Joint policy accessed deep blocks before both paid probes')
                    row['prefix_decisions'].append({'step':len(tensors)+1,'action':action,
                        'paid_probes':[asdict(p) for p in packets],'prefix_visits_before_deep':visits})
                    return action
                original_factory = model.get_velocity_fn_from_batch
                if method == 'WC':
                    executor = None
                    factory = original_factory.__func__
                else:
                    _,denoise,core = compile_production(runtime,wc,rf_module)
                    base = NativePolicyPairedExecutor(model,denoise,torch,
                        wc_forward=wc.worldcache_mini_train_dit_forward,
                        rf_denoise=rf_module.Video2WorldModelRectifiedFlow.denoise)
                    if method == 'JOINT_NATIVE':
                        class ObservedNative(JointNativePairExecutor):
                            def _select(self,packets):
                                return record_selection(packets,super()._select(packets))
                        executor = ObservedNative(base)
                    else:
                        class ObservedRA(JointPolicyPairExecutor):
                            def _select(self,packets):
                                return record_selection(packets,super()._select(packets))
                        executor = ObservedRA(base,JointCDController(calibration,threshold))
                        row.update(RA_threshold=threshold,calibration_fingerprint=calibration.fingerprint)
                    factory,proof = compile_velocity(runtime,rf_module,executor,executor.choose)
                    row.update(core_compiler=dict(core),velocity_compiler=dict(proof))
                def velocity_factory(m,*args,**kwargs):
                    velocity = factory(m,*args,**kwargs)
                    cells = inspect.getclosurevars(velocity).nonlocals
                    if set(cells) != {'self','condition','uncondition','guidance'} or cells['self'] is not m or cells['guidance'] != 7:
                        raise ValueError('Actual method RF/condition/CFG closure differs')
                    conditions.extend((cells['condition'],cells['uncondition']))
                    row['conditions_before'] = tree_digest([object_state(c) for c in conditions])
                    capture['velocity'] = velocity
                    def measured(noise,latent,timestep):
                        counter = int(net.cnt)
                        capture.update(noise=noise,visits=[[0]*len(net.blocks) for _ in (0,1)])
                        if not tensors:
                            row['first_velocity_input_sha256'] = tree_digest((noise,latent,timestep))
                        value = velocity(noise,latent,timestep)
                        visits = capture['visits']
                        action = ''.join('D' if v[2:] == [1]*(len(net.blocks)-2) else 'C' for v in visits)
                        if (visits != [[1,1]+[int(a=='D')]*(len(net.blocks)-2) for a in action]
                                or int(net.cnt) != (counter+2)%70
                                or executor is not None and executor.last['action'] != action
                                or value.dtype != torch.float32 or list(value.shape) != config['expected_shape']):
                            raise ValueError('Actual method action/visits/counter/geometry differs')
                        tensors.append(value.detach().cpu().clone())
                        row['guided_sha256'].append(tree_digest(tensors[-1]))
                        row['actions'].append(action)
                        row['counters'].append(counter)
                        row['block_visits'].append(copy.deepcopy(visits))
                        return value
                    return measured
                def after_step(value):
                    row['solver_returns'].append(tree_digest(value))
                    step = len(row['solver_returns'])
                    latent = value[0].squeeze(0)
                    if scheduler._step_index != step:
                        raise ValueError('Full method solver execution step differs')
                    if step in STATE_STEPS:
                        inventory = capture_inventory(net,scheduler,latent,capture['noise'],capture['velocity'])
                        gate = capture_gate(inventory,logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                            transient_copy_factor=2,workspace_reserve_bytes=config['workspace_reserve_bytes']+config['paired_prefix_reserve_bytes'],
                            available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
                        snapshot = CompleteStateRoundtrip(net,scheduler,latent,[capture['generator']])
                        components = snapshot.components()
                        if len(components) != config['expected_components']:
                            raise ValueError('Full method state component count differs')
                        row['checkpoints'].append({'step':step,'components':components})
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
                    row['instrumented_pipeline_wall_seconds'] = time.perf_counter()-start
                    if len(paths) != 1 or len(tensors) != 36 or len(row['solver_returns']) != 36:
                        raise ValueError('Complete ordinary guarded method video missing')
                    if executor is not None:
                        row['policy_history'] = (copy.deepcopy(executor.history) if method == 'JOINT_NATIVE'
                            else [asdict(d) for d in executor.controller.history])
                    row.update(conditions_after=tree_digest([object_state(c) for c in conditions]),
                        flags_after=backend_flags(),rng_after=RNGState().signatures(),video_artifact=artifact(paths[0]),
                        guided_list_sha256=tree_digest(tensors),final_latent_sha256=tree_digest(capture['final_latent']))
                    row['vector_artifact'] = writer(output/sample.name/'vectors'/(label+'.pt'),
                        {'guided':tensors,'final_latent':capture['final_latent']})
                    row.update(parameter_versions_unchanged=all(p is old and p._version == version
                        for p,(old,version) in zip(net.parameters(),parameters)),
                        all_modules_eval=not any(m.training for m in net.modules()),status='COMPLETE_PATH')
                    save()
                except BaseException as error:
                    row.update(status='METHOD_FAILED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error))
                    save()
                    raise
                finally:
                    hooks.close()
                    for handle in handles:
                        handle.remove()
                    tensors.clear()
            request.update(status='COMPLETE_REQUEST',prepared_input_calls=prepared.calls)
            save()
        state.update(verdict=verify_batch(state),status='COMPLETE_RA_BASELINE_BATCH_REQUIRES_RAW_CPU_AUDIT')
        save()
    finally:
        initial.restore()
        net.forward = prior_forward
        for key in set(WC_FIELDS)-old_keys:
            if hasattr(net,key):
                delattr(net,key)
        for key,value in old_config.items():
            setattr(net,key,value)
        if initial.fingerprint() != initial_sha:
            raise ValueError('Full method comparison initial physical restoration differs')
        state['initial_state_restored'] = True
        save()
