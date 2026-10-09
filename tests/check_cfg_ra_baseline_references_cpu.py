"""Full six-method/two-Native composition with explicit Toy Native body."""
import copy
import json
from pathlib import Path
import types

import torch

from wcomr.cfg_ra_baseline import threshold_from_collection
from wcomr.cfg_ra_baseline_with_references import run_comparison as run_batch, verify_comparison as verify_batch, audit_comparison_vectors as audit_vectors, vector_file
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
    # Explicit stand-in Native class body for the CPU composition test only.
    # It always executes all pinned WC deep blocks; the real Native class origin
    # and unchanged forward source must be checked separately before GPU use.
    original_class_forward=type(net).forward
    def dense_toy_native(self,*args,**kwargs):
        threshold=self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*args,**kwargs)
        finally:self.worldcache_rel_l1_thresh=threshold
    dense_toy_native.__module__='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit'
    dense_toy_native.__qualname__='MinimalV1LVGDiT.forward'
    type(net).forward=dense_toy_native
    private_scheduler=copy.deepcopy(model.sample_scheduler)
    private_scheduler.set_timesteps(35,use_kerras_sigma=model.config.use_kerras_sigma_at_inference,device='cpu')
    policy={'scheduler_class':type(private_scheduler).__name__,'requested_steps':35,
        'actual_steps':36,'cfg_calls':72,'use_kerras_sigma':model.config.use_kerras_sigma_at_inference,
        'timesteps':private_scheduler.timesteps.tolist()}
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
                if scenario=='last_vector_writer_failure' and path.name=='human_NATIVE.pt':
                    raise ValueError('Injected last complete Native reference vector writer failure')
                return vector_file(path,tensors)
            try:
                run_batch(inference,samples,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,contexts=contexts,mode_setup=modes,runtime=runtime,
                    config=config,rf_module=rf,writer=writer,calibration=calibration,
                    threshold=initialized['threshold'],sampling_policy=policy)
            except BaseException as exc:
                error=str(exc)
            assert state['batch']['initial_state_restored'] and state['reference_initial_state_restored'] and all(float(v)==0 for v in net.buffers())
            assert state['planned_paths']==8 and state['planned_method_paths']==6 and state['planned_reference_paths']==2
            assert len(state['batch']['requests'])==2 and all(len(r['paths'])==3 for r in state['batch']['requests'])
            assert len(state['references'])==2
            if scenario=='complete':
                assert error is None,error
                verdict=verify_batch(state)
                raw=audit_vectors(state,output,tensor_loader,config['expected_shape'])
                assert raw['actual_guided_tensors_reloaded']==216 and raw['actual_final_latents_reloaded']==6
                assert raw['actual_initial_7_DD_guided_direct_equal'] and len(raw['files'])==6
                assert raw['actual_reference_guided_reloaded']==72 and raw['actual_reference_latents_reloaded']==2
                assert raw['actual_reference_initial7_direct_equal']
                refused=[]
                for fault in ('missing_method','wrong_prior','wrong_initial_noise','unpaid_prefix','wrong_deep_visits','incomplete_RA_history','missing_reference','wrong_reference_noise'):
                    bad=copy.deepcopy(state)
                    row=bad['batch']['requests'][0]['paths'][2]
                    if fault=='missing_method':bad['batch']['requests'][0]['paths'].pop()
                    elif fault=='wrong_prior':row['calibration_fingerprint']='unbound'
                    elif fault=='wrong_initial_noise':row['first_velocity_input_sha256']='0'*64
                    elif fault=='unpaid_prefix':row['prefix_decisions'][0]['prefix_visits_before_deep'][0][-1]=1
                    elif fault=='wrong_deep_visits':row['block_visits'][0][0][-1]=0
                    elif fault=='incomplete_RA_history':row['policy_history'].pop()
                    elif fault=='missing_reference':bad['references'].pop()
                    elif fault=='wrong_reference_noise':bad['references'][0]['first_velocity_input_sha256']='0'*64
                    try:verify_batch(bad)
                    except ValueError:refused.append(fault)
                    else:raise AssertionError('Malformed three-method comparison accepted: '+fault)
                path=Path(state['references'][-1]['vector_artifact']['path'])
                original=path.read_bytes()
                try:
                    path.write_bytes(original[:-1])
                    try:audit_vectors(state,output,tensor_loader,config['expected_shape'])
                    except ValueError as exc:assert 'Matching Native vector file changed' in str(exc)
                    else:raise AssertionError('Truncated actual method vector accepted')
                finally:
                    path.write_bytes(original)
                checks.append({'kind':'RA_three_method_actual_guarded_batch','flow':flow,'scenario':scenario,
                    'status':'PASS','receipt':state,'verdict':verdict,'actual_tensor_audit':raw,
                    'threshold_initialization':initialized,'semantic_mutation_refusals':refused,
                    'actual_final_method_truncation_refused':True,'condition_class_AST_SHA':class_sha})
            else:
                assert error and 'Injected last complete Native reference vector writer failure' in error,error
                last=state['references'][-1]
                assert last['status']=='MATCHED_NATIVE_FAILED_COMPLETE_SCOPE_RETAINED'
                assert len(last['guided_sha256'])==len(last['solver_returns'])==36
                assert last['CFG_calls']==72 and last['solver_steps']==36
                assert 'vector_artifact' not in last and len(list(output.rglob('*.pt')))==7
                assert len(list(output.rglob('*.mp4')))==8
                try:verify_batch(state)
                except ValueError:pass
                else:raise AssertionError('Last failed method was accepted as a complete batch')
                checks.append({'kind':'RA_three_method_actual_guarded_batch','flow':flow,'scenario':scenario,
                    'status':'EXPECTED_FAILURE','error':error,'receipt':state,
                    'complete_scope_retained':True,'initial_full_state_restored':True})
        return checks
    finally:
        type(net).forward=original_class_forward
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
    result['limits']='Actual six-method/two-reference composition, pinned WC/RF/UniPC and audited Native request control; Toy weights/attention, dense-only WC numerical stand-in Native class body, prepare/decode/write and accepted Toy calibration. This does not execute the real 2B Native class body. Full36/paid prefixes/actual blocks/initial input/conditions/raw artifacts checked. No CUDA, real videos, quality or clean timing.'
    return result
