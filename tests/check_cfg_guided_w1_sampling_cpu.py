"""Actual full UniPC/guarded pipeline with a four-scene collection batch.

Toy CPU weights/attention/prepare/decode/writer remain explicit stand-ins. The
new batch, pinned WC/RF/condition class, full sampler and complete vector reload
are executed. Neither its fitting values nor mock files are real CAL/video.
"""
import copy
import json
from pathlib import Path
import types

import torch

from wcomr.cfg_guided_w1_sampling import run_batch,verify_batch,audit_vectors
from wcomr.cfg_mf00_interface_sampling import vector_file
from wcomr.h0_mode import establish_shared_eval


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m


def exercise(*,inference,samples,settings,inference_module,flow,runtime,tensor_loader,artifact_root,**unused):
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    model=inference.pipe.model;net=model.net
    saved=(net.prepare_embedded_sequence,model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition)
    conditioner=model.conditioner.get_condition_with_negative_prompt;cfg=copy.deepcopy(vars(model.config))
    cls,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    def conditions(batch):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True]))
            .set_video_condition(torch.zeros(1,2048,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,2048,2,8,8),None)
    for name in ('denoise','get_velocity_fn_from_batch'):
        setattr(model,name,types.MethodType(getattr(rf.Video2WorldModelRectifiedFlow,name),model))
    model.config.conditional_frame_timestep=-1;model.config.denoise_replace_gt_frames=True
    model.config.min_num_conditional_frames=model.config.max_num_conditional_frames=0;model.config.conditional_frames_probs=None
    mode=establish_shared_eval(net); settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    names=['AV28_CPU','Human_CPU','misc_CPU','AV51_CPU']; selected=[type(samples[0])(n) for n in names]
    config={'sample_names':names,'run_id':'GUIDED_W1_FULL_BATCH_CPU','logical_copy_cap_bytes':6*(1<<30),
        'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30),
        'expected_components':50,'expected_shape':[1,2048,2,8,8]}
    contexts=[(config['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in names]
    results=[]
    try:
        for scenario in (('complete','last_parent_writer_failure') if flow else ('complete',)):
            output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario;output.mkdir(parents=True,exist_ok=False)
            state={};error=None
            def save():
                p=output/'receipt.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(p)
            def writer(path,values):
                if scenario=='last_parent_writer_failure' and path.name=='AV51_CPU_COLLECT_ON.pt':
                    raise ValueError('Injected final full-parent vector writer failure')
                return vector_file(path,values)
            try:
                run_batch(inference,selected,wc,settings,state=state,save=save,output=output,inference_module=inference_module,
                    contexts=contexts,mode_setup=mode,runtime=runtime,config=config,rf_module=rf,writer=writer)
            except BaseException as exc:error=str(exc)
            assert state['planned_parent_paths']==8 and state['planned_origins']==8 and len(state['requests'])==4
            assert state['initial_state_restored'] and all(float(b)==0 for b in net.buffers())
            assert not any(m.training for m in net.modules())
            if scenario=='complete':
                assert error is None,error
                verdict=verify_batch(state);raw=audit_vectors(state,output,tensor_loader,config['expected_shape'])
                assert raw['actual_parent_guided_reloaded']==288 and raw['actual_parent_latents_reloaded']==8
                assert raw['actual_post_RF_branch_tensors_reloaded']==64 and raw['W1_shared_alpha_selection']['scenes']==4
                assert len(raw['files'])==16
                for r in state['requests']:
                    for row in r['paths']:
                        assert row['condition_fields_before']==row['condition_fields_after']
                        assert all(m['finite'] and m['nonzero_elements']==0 for m in row['actual_condition_masks'])
                        assert row['actual_raw_solver_configuration']['raw_values']
                refused=[]
                for fault in ('missing_scene','missing_origin','teacher_anchor_contamination','wrong_complete_route','modified_condition_field'):
                    bad=copy.deepcopy(state);row=bad['requests'][-1]['paths'][1]
                    if fault=='missing_scene':bad['requests'].pop()
                    elif fault=='missing_origin':row['origins'].pop()
                    elif fault=='teacher_anchor_contamination':row['origins'][0]['teacher_updates_deployment_anchor']=True
                    elif fault=='wrong_complete_route':row['actions'][11]='DD'
                    else:row['condition_fields_before'][0]['fps']='0'*64
                    try:verify_batch(bad)
                    except ValueError:refused.append(fault)
                    else:raise AssertionError('Incomplete or contaminated full batch accepted: '+fault)
                p=Path(raw['files'][-1]['path']);saved_bytes=p.read_bytes()
                try:
                    p.write_bytes(saved_bytes[:-1])
                    try:audit_vectors(state,output,tensor_loader,config['expected_shape'])
                    except ValueError as exc:assert 'changed or truncated' in str(exc)
                    else:raise AssertionError('Truncated actual tensor artifact accepted')
                finally:p.write_bytes(saved_bytes)
                results.append({'flow':flow,'scenario':scenario,'status':'PASS','verdict':verdict,
                    'actual_tensor_audit':raw,'receipt':state,'mutation_refusals':refused,
                    'actual_artifact_truncation_refused':True,'condition_class_AST_SHA':class_sha})
            else:
                assert error=='Injected final full-parent vector writer failure',error
                row=state['requests'][-1]['paths'][-1]
                assert row['status']=='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED' and len(row['guided_sha256'])==36
                assert len(row['origins'])==2 and 'vector_artifact' not in row
                assert len(list(output.rglob('*.pt')))==15 and len(list(output.rglob('*.mp4')))==8
                results.append({'flow':flow,'scenario':scenario,'status':'EXPECTED_FAILURE','error':error,
                    'complete_scope_retained':True,'receipt':state,'initial_full_state_restored':True})
        return results
    finally:
        net.prepare_embedded_sequence=saved[0]
        model.get_velocity_fn_from_batch,model.denoise,model.get_data_and_condition=saved[1:]
        model.conditioner.get_condition_with_negative_prompt=conditioner
        vars(model.config).clear();vars(model.config).update(cfg)


def run(runtime,tensor_loader,artifact_root):
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(runtime=Path(runtime),
        tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert len(result['checks'])==3
    result['limits']='Actual new four-scene batch, full pinned WC/RF/condition/UniPC/ordinary guarded pipeline; Toy CPU weights, attention, prepare/decode/mock writer. All288+8+64 tensors reloaded per flow. No actual Cosmos CAL, video, quality, CUDA or clean latency.'
    return result
