"""The actual new full native-policy batch through the pinned ordinary pipeline."""
import copy
import json
from pathlib import Path
import types

import torch

from wcomr.cfg_mf00_interface_sampling import run_batch, verify_batch, audit_vectors, vector_file
from wcomr.h0_mode import establish_shared_eval


def load(name):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = module_from_spec(spec);spec.loader.exec_module(module);return module


def exercise(*, inference, samples, settings, inference_module, flow, runtime, tensor_loader,
             artifact_root, **unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    model = inference.pipe.model;net = model.net
    names = ('prepare_embedded_sequence', 'get_velocity_fn_from_batch', 'denoise', 'get_data_and_condition')
    saved = (net.prepare_embedded_sequence, model.get_velocity_fn_from_batch, model.denoise, model.get_data_and_condition)
    original_conditioner = model.conditioner.get_condition_with_negative_prompt
    config_before = copy.deepcopy(vars(model.config))
    cls, class_sha = load('check_rv0_video_actions_cpu').pinned_video_condition(runtime, wc.DataType)
    net.prepare_embedded_sequence = lambda x, **kw: (x[:, :2048].movedim(1, -1).contiguous(), None, None)
    def conditions(batch):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+slot), fps=batch['fps'],
            use_video_condition=torch.tensor([True])).set_video_condition(torch.zeros(1,2048,2,8,8),0,0,
                num_conditional_frames=1) for slot in (0,1))
    model.conditioner.get_condition_with_negative_prompt = conditions
    model.get_data_and_condition = lambda b: (None, torch.zeros(1,2048,2,8,8), None)
    for name in ('denoise', 'get_velocity_fn_from_batch'):
        setattr(model, name, types.MethodType(getattr(rf.Video2WorldModelRectifiedFlow,name),model))
    model.config.conditional_frame_timestep = -1;model.config.denoise_replace_gt_frames = True
    model.config.min_num_conditional_frames = model.config.max_num_conditional_frames = 0
    model.config.conditional_frames_probs = None
    modes = establish_shared_eval(net)
    settings = {**settings, 'probe_depth':2, 'worldcache_rel_l1_thresh':.06}
    config = {'sample_names':['common','human'], 'run_id':'MF00_INTERFACE_CPU',
        'logical_copy_cap_bytes':6*(1<<30), 'workspace_reserve_bytes':4*(1<<30),
        'paired_prefix_reserve_bytes':4*(1<<30), 'expected_components':50,
        'expected_shape':[1,2048,2,8,8]}
    contexts = [(config['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in config['sample_names']]
    checks = []
    try:
        for scenario in ('complete', 'last_vector_writer_failure'):
            output = Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario
            output.mkdir(parents=True, exist_ok=False)
            state = {};error = None
            def save():
                temporary=output/'receipt.tmp'
                temporary.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')
                temporary.replace(output/'receipt.json')
            def writer(path, tensors):
                if scenario == 'last_vector_writer_failure' and path.name == 'human_OBS_OFF_first_PAIRED.pt':
                    raise ValueError('Injected final complete-path tensor writer failure')
                return vector_file(path, tensors)
            try:
                run_batch(inference,samples,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,contexts=contexts,mode_setup=modes,runtime=runtime,
                    config=config,rf_module=rf,writer=writer)
            except BaseException as exc:
                error = str(exc)
            assert state['planned_paths']==state['planned_videos']==4
            assert state['initial_state_restored'] and all(float(v)==0 for v in net.buffers())
            assert not any(m.training for m in net.modules())
            assert len(state['requests'])==2 and all(len(r['paths'])==2 for r in state['requests'])
            if scenario == 'complete':
                assert error is None, error
                verdict = verify_batch(state)
                raw = audit_vectors(state, output, tensor_loader, config['expected_shape'])
                assert raw['actual_guided_tensors_reloaded']==144 and raw['actual_final_latents_reloaded']==4
                refused = []
                for fault in ('missing_request','missing_path','wrong_observer','wrong_order','wrong_repeat',
                              'missing_guided','wrong_action','wrong_state','wrong_video','wrong_tensor_binding',
                              'unexpected_OFF_observer_event','missing_tail_prefix'):
                    bad = copy.deepcopy(state);row = bad['requests'][0]['paths'][1]
                    if fault=='missing_request':bad['requests'].pop()
                    elif fault=='missing_path':bad['requests'][0]['paths'].pop()
                    elif fault=='wrong_observer':row['observers']=True
                    elif fault=='wrong_order':row['order']='ORIGINAL'
                    elif fault=='wrong_repeat':row['repetition']='INVALID'
                    elif fault=='missing_guided':row['guided_sha256'].pop()
                    elif fault=='wrong_action':row['actions'][34]='DD'
                    elif fault=='wrong_state':row['checkpoints'][-1]['components']['output']='0'*64
                    elif fault=='wrong_video':row['video_artifact']['sha256']='0'*64
                    elif fault=='wrong_tensor_binding':row['vector_artifact']['tensor_sha256']['guided']='0'*64
                    elif fault=='unexpected_OFF_observer_event':row['net_events'].append({'kind':'unexpected'})
                    elif fault=='missing_tail_prefix':row['prefix_decisions'].pop()
                    try:verify_batch(bad)
                    except ValueError:refused.append(fault)
                    else:raise AssertionError('Incomplete/mutated full native batch accepted: '+fault)
                path = Path(state['requests'][-1]['paths'][-1]['vector_artifact']['path'])
                original = path.read_bytes()
                try:
                    path.write_bytes(original[:-1])
                    try:audit_vectors(state,output,tensor_loader,config['expected_shape'])
                    except ValueError as exc:assert 'Actual vector artifact bytes differ' in str(exc)
                    else:raise AssertionError('Truncated actual tensor file accepted')
                finally:path.write_bytes(original)
                checks.append({'kind':'complete_native_policy_actual_batch','flow':flow,'scenario':scenario,
                    'status':'PASS','receipt':state,'verdict':verdict,'actual_tensor_audit':raw,
                    'semantic_mutation_refusals':refused,'actual_artifact_truncation_refused':True,
                    'condition_class_AST_SHA':class_sha})
            else:
                assert error and 'Injected final complete-path tensor writer failure' in error, error
                last = state['requests'][-1]['paths'][-1]
                assert last['status']=='TECH_BLOCKED_COMPLETE_SCOPE_RETAINED'
                assert len(last['guided_sha256'])==len(last['solver_returns'])==36
                assert 'vector_artifact' not in last and len(list(output.rglob('*.pt')))==3
                assert len(list(output.rglob('*.mp4')))==4
                checks.append({'kind':'complete_native_policy_actual_batch','flow':flow,'scenario':scenario,
                    'status':'EXPECTED_FAILURE','error':error,'receipt':state,
                    'complete_scope_retained':True,'initial_full_state_restored':True})
        return checks
    finally:
        net.prepare_embedded_sequence = saved[0]
        model.get_velocity_fn_from_batch, model.denoise, model.get_data_and_condition = saved[1:]
        model.conditioner.get_condition_with_negative_prompt = original_conditioner
        vars(model.config).clear();vars(model.config).update(config_before)


def run(runtime, tensor_loader, artifact_root):
    result = load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert len(result['checks'])==4
    result['limits']='Actual new full guarded batch and pinned WC/RF/UniPC/pipeline; Toy CPU weights, attention, prepare/decode/write. All actual Toy guided tensors reloaded. No model weights, CUDA, real videos, policy benefit or latency claim.'
    return result
