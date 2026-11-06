"""The actual new full native-policy batch through the pinned ordinary pipeline."""
import copy
import json
from pathlib import Path
import types

import torch

from wcomr.cfg_ra_calibration_sampling import run_batch, verify_batch, audit_vectors, vector_file
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
    config = {'sample_names':['common','human'], 'run_id':'RA_CALIBRATION_BATCH_CPU',
        'logical_copy_cap_bytes':6*(1<<30), 'workspace_reserve_bytes':4*(1<<30),
        'paired_prefix_reserve_bytes':4*(1<<30), 'expected_components':50,
        'expected_shape':[1,2048,2,8,8]}
    contexts = [(config['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in config['sample_names']]
    checks = []
    try:
        for scenario in ('complete', 'last_vector_writer_failure'):
            output = Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario
            output.mkdir(parents=True, exist_ok=False)
            state = {}; error = None
            def save():
                temporary = output/'receipt.tmp'
                temporary.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')
                temporary.replace(output/'receipt.json')
            def writer(path,tensors):
                if scenario=='last_vector_writer_failure' and path.name=='human_COLLECT_ON.pt':
                    raise ValueError('Injected last complete parent tensor writer failure')
                return vector_file(path,tensors)
            try:
                run_batch(inference,samples,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,contexts=contexts,mode_setup=modes,runtime=runtime,
                    config=config,rf_module=rf,writer=writer)
            except BaseException as exc:
                error = str(exc)
            assert state['initial_state_restored'] and all(float(v)==0 for v in net.buffers())
            assert state['planned_parent_paths']==4 and state['planned_child_arms']==12
            assert len(state['requests'])==2 and all(len(r['paths'])==2 for r in state['requests'])
            if scenario=='complete':
                assert error is None,error
                verdict = verify_batch(state)
                raw = audit_vectors(state,output,tensor_loader,config['expected_shape'],
                    fingerprint_context='ACTUAL_GUARDED_BATCH_TOY_CPU',toy=True)
                assert raw['actual_parent_guided_tensors_reloaded']==144
                assert raw['actual_parent_latents_reloaded']==4 and raw['actual_child_tensors_reloaded']==48
                assert len(raw['files'])==16 and len(raw['table']['observed_rows'])==6
                refused = []
                for fault in ('missing_request','missing_parent','missing_origin','missing_child',
                              'wrong_dense_suffix','wrong_current_input','wrong_anchor','parent_tensor_binding'):
                    bad = copy.deepcopy(state); row = bad['requests'][0]['paths'][1]
                    if fault=='missing_request':bad['requests'].pop()
                    elif fault=='missing_parent':bad['requests'][0]['paths'].pop()
                    elif fault=='missing_origin':row['origins'].pop()
                    elif fault=='missing_child':row['origins'][0]['arms'].pop()
                    elif fault=='wrong_dense_suffix':row['origins'][0]['arms'][0]['suffix_history'][-1]['action']='CC'
                    elif fault=='wrong_current_input':row['origins'][0]['arms'][0]['current_input_sha256']='0'*64
                    elif fault=='wrong_anchor':row['origins'][0]['arms'][0]['shared_anchor']=1
                    elif fault=='parent_tensor_binding':row['vector_artifact']['tensor_sha256']['guided']='0'*64
                    try:verify_batch(bad)
                    except ValueError:refused.append(fault)
                    else:raise AssertionError('Malformed complete calibration accepted: '+fault)
                path = Path(state['requests'][-1]['paths'][1]['origins'][-1]['arms'][1]['artifact']['path'])
                original = path.read_bytes()
                try:
                    path.write_bytes(original[:-1])
                    try:audit_vectors(state,output,tensor_loader,config['expected_shape'],fingerprint_context='TOY',toy=True)
                    except ValueError as exc:assert 'Actual calibration vector bytes differ' in str(exc)
                    else:raise AssertionError('Truncated child tensor accepted')
                finally:path.write_bytes(original)
                checks.append({'kind':'RA_calibration_actual_guarded_batch','flow':flow,'scenario':scenario,
                    'status':'PASS','receipt':state,'verdict':verdict,'actual_tensor_audit':raw,
                    'semantic_mutation_refusals':refused,'actual_child_truncation_refused':True,
                    'condition_class_AST_SHA':class_sha})
            else:
                assert error and 'Injected last complete parent tensor writer failure' in error,error
                last = state['requests'][-1]['paths'][-1]
                assert last['status']=='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED'
                assert len(last['guided_sha256'])==len(last['solver_returns'])==36
                assert 'vector_artifact' not in last and len(list(output.rglob('*.pt')))==15
                assert len(list(output.rglob('*.mp4')))==4
                assert len(last['origins'])==3 and all(len(o['arms'])==2 for o in last['origins'])
                checks.append({'kind':'RA_calibration_actual_guarded_batch','flow':flow,'scenario':scenario,
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
    result['limits']='Actual new coarse-calibration guarded batch and pinned WC/RF/UniPC/pipeline; Toy CPU weights, attention, prepare/decode/write. All actual Toy guided tensors reloaded. No model weights, CUDA, real videos, policy benefit or latency claim.'
    return result
