"""Actual guarded three-policy full36 batch using the accepted Toy calibration."""
import copy
import json
from pathlib import Path
import types

import torch

from wcomr.cfg_ra_baseline import threshold_from_collection
from wcomr.cfg_ra_baseline_sampling import run_batch,verify_batch,audit_vectors,vector_file
from wcomr.cfg_ra_calibration_table import load_table
from wcomr.h0_mode import establish_shared_eval


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exercise(*,inference,samples,settings,inference_module,flow,runtime,tensor_loader,
             artifact_root,calibration_cpu_result,**unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    prior=[r for r in calibration_cpu_result['checks'] if r['status']=='PASS' and r['flow']==flow]
    assert len(prior)==1
    prior=prior[0]
    calibration=load_table(prior['actual_tensor_audit']['table'],permit_toy=True)
    initialized=threshold_from_collection(prior['receipt'],calibration)
    assert len(initialized['observed_intervals'])==8 and initialized['threshold']>0
    assert not initialized['endpoint_quality_used_to_choose_threshold']
    model,net=inference.pipe.model,inference.pipe.model.net
    saved=(net.prepare_embedded_sequence,model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition)
    original_conditioner=model.conditioner.get_condition_with_negative_prompt
    config_before=copy.deepcopy(vars(model.config))
    cls,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    def conditions(batch):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+slot),fps=batch['fps'],
            use_video_condition=torch.tensor([True])).set_video_condition(torch.zeros(1,2048,2,8,8),0,0,
                num_conditional_frames=1) for slot in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,2048,2,8,8),None)
    for name in ('denoise','get_velocity_fn_from_batch'):
        setattr(model,name,types.MethodType(getattr(rf.Video2WorldModelRectifiedFlow,name),model))
    model.config.conditional_frame_timestep=-1
    model.config.denoise_replace_gt_frames=True
    model.config.min_num_conditional_frames=model.config.max_num_conditional_frames=0
    model.config.conditional_frames_probs=None
    modes=establish_shared_eval(net)
    settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    config={'sample_names':['common','human'],'run_id':'RA_BASELINE_BATCH_CPU',
        'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),
        'paired_prefix_reserve_bytes':4*(1<<30),'expected_components':50,'expected_shape':[1,2048,2,8,8]}
    contexts=[(config['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in config['sample_names']]
    checks=[]
    try:
        for scenario in ('complete','last_vector_writer_failure'):
            output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario
            output.mkdir(parents=True,exist_ok=False)
            state={}
            error=None
            def save():
                temporary=output/'receipt.tmp'
                temporary.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')
                temporary.replace(output/'receipt.json')
            def writer(path,tensors):
                if scenario=='last_vector_writer_failure' and path.name=='human_RA.pt':
                    raise ValueError('Injected last complete RA method vector writer failure')
                return vector_file(path,tensors)
            try:
                run_batch(inference,samples,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,contexts=contexts,mode_setup=modes,runtime=runtime,
                    config=config,rf_module=rf,writer=writer,calibration=calibration,
                    threshold=initialized['threshold'])
            except BaseException as exc:
                error=str(exc)
            assert state['initial_state_restored'] and all(float(v)==0 for v in net.buffers())
            assert state['planned_paths']==state['planned_videos']==6
            assert len(state['requests'])==2 and all(len(r['paths'])==3 for r in state['requests'])
            if scenario=='complete':
                assert error is None,error
                verdict=verify_batch(state)
                raw=audit_vectors(state,output,tensor_loader,config['expected_shape'])
                assert raw['actual_guided_tensors_reloaded']==216 and raw['actual_final_latents_reloaded']==6
                assert raw['actual_initial_7_DD_guided_direct_equal'] and len(raw['files'])==6
                refused=[]
                for fault in ('missing_method','wrong_prior','wrong_initial_noise','unpaid_prefix','wrong_deep_visits','incomplete_RA_history'):
                    bad=copy.deepcopy(state)
                    row=bad['requests'][0]['paths'][2]
                    if fault=='missing_method':bad['requests'][0]['paths'].pop()
                    elif fault=='wrong_prior':row['calibration_fingerprint']='unbound'
                    elif fault=='wrong_initial_noise':row['first_velocity_input_sha256']='0'*64
                    elif fault=='unpaid_prefix':row['prefix_decisions'][0]['prefix_visits_before_deep'][0][-1]=1
                    elif fault=='wrong_deep_visits':row['block_visits'][0][0][-1]=0
                    elif fault=='incomplete_RA_history':row['policy_history'].pop()
                    try:verify_batch(bad)
                    except ValueError:refused.append(fault)
                    else:raise AssertionError('Malformed three-method comparison accepted: '+fault)
                path=Path(state['requests'][-1]['paths'][-1]['vector_artifact']['path'])
                original=path.read_bytes()
                try:
                    path.write_bytes(original[:-1])
                    try:audit_vectors(state,output,tensor_loader,config['expected_shape'])
                    except ValueError as exc:assert 'Actual method vector file changed' in str(exc)
                    else:raise AssertionError('Truncated actual method vector accepted')
                finally:
                    path.write_bytes(original)
                checks.append({'kind':'RA_three_method_actual_guarded_batch','flow':flow,'scenario':scenario,
                    'status':'PASS','receipt':state,'verdict':verdict,'actual_tensor_audit':raw,
                    'threshold_initialization':initialized,'semantic_mutation_refusals':refused,
                    'actual_final_method_truncation_refused':True,'condition_class_AST_SHA':class_sha})
            else:
                assert error and 'Injected last complete RA method vector writer failure' in error,error
                last=state['requests'][-1]['paths'][-1]
                assert last['status']=='METHOD_FAILED_COMPLETE_SCOPE_RETAINED'
                assert len(last['guided_sha256'])==len(last['solver_returns'])==36
                assert len(last['policy_history'])==36
                assert 'vector_artifact' not in last and len(list(output.rglob('*.pt')))==5
                assert len(list(output.rglob('*.mp4')))==6
                try:verify_batch(state)
                except ValueError:pass
                else:raise AssertionError('Last failed method was accepted as a complete batch')
                checks.append({'kind':'RA_three_method_actual_guarded_batch','flow':flow,'scenario':scenario,
                    'status':'EXPECTED_FAILURE','error':error,'receipt':state,
                    'complete_scope_retained':True,'initial_full_state_restored':True})
        return checks
    finally:
        net.prepare_embedded_sequence=saved[0]
        model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition=saved[1:]
        model.conditioner.get_condition_with_negative_prompt=original_conditioner
        vars(model.config).clear()
        vars(model.config).update(config_before)


def run(runtime,tensor_loader,artifact_root,calibration_cpu_result):
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,
        calibration_cpu_result=calibration_cpu_result,**kw))
    assert len(result['checks'])==4
    result['limits']='Actual three-method guarded pipeline and pinned WC/RF/UniPC; Toy weights, attention, prepare/decode/write and previously accepted actual Toy calibration. Full36/paid prefixes/actual blocks/initial input/conditions/RNG/raw artifacts checked. No CUDA, real videos, quality or clean timing.'
    return result
